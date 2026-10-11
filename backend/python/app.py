import base64
import binascii
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from flask import Flask, jsonify, request, send_from_directory

# Configure App 

FRONTEND_PATH = Path(__file__).resolve().parent.parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_PATH), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# Get File Paths

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model/model.tflite"
LABELS_PATH = BASE_DIR / "model/labels.txt"
DB_PATH = BASE_DIR / "model/predictions.db"


# Load the Model
interpreter = tf.lite.Interpreter(model_path=str(MODEL_PATH))
interpreter.allocate_tensors()

# Load Model Input and Output dimensions

input_details = interpreter.get_input_details()[0]
output_details = interpreter.get_output_details()[0]

# Load Labels

with open(LABELS_PATH, encoding="utf-8") as f:
    labels = [line.strip() for line in f if line.strip()]

# Initialize Database

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


init_db()

# Step 1: Convert Data URL to Image

def decode_data_url(data_url):
    """Decode a base64 image Data URL into a PIL image."""
    if not isinstance(data_url, str):
        raise ValueError("Image data must be a string.")

    header, separator, encoded = data_url.partition(",")

    if not separator or not header.startswith("data:image/"):
        raise ValueError("Expected an image Data URL.")

    if ";base64" not in header.lower():
        raise ValueError("Expected base64-encoded image data.")

    try:
        raw_bytes = base64.b64decode(encoded, validate=True)
        # Verify that the uploaded bytes represent an actual image.
        with Image.open(io.BytesIO(raw_bytes)) as image:
            image.verify()

        with Image.open(io.BytesIO(raw_bytes)) as image:
            return image.convert("RGB")

    except (binascii.Error, UnidentifiedImageError, OSError) as exc:
        raise ValueError("Invalid or unsupported image.") from exc

# Step 2: Preprocess Image for Model

def preprocess_image(image):
    """Prepare RGB pixels for the model's NHWC input."""
    shape = input_details["shape"]
    height, width = int(shape[1]), int(shape[2])
    dtype = input_details["dtype"]

    image = image.resize((width, height))
    pixels = np.asarray(image, dtype=np.float32)
    batch = np.expand_dims(pixels, axis=0)

    batch = batch / 255.0

    return batch.astype(dtype)

# Step 3: Classify Image

def classify(image):
    batch = preprocess_image(image)

    interpreter.set_tensor(input_details["index"], batch)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details["index"])
    scores = np.asarray(output[0], dtype=np.float32).reshape(-1)

    if not np.all(np.isfinite(scores)):
        raise ValueError("Model returned invalid scores.")

    if len(scores) != len(labels):
        raise ValueError("Model output size does not match labels.txt.")

    index = int(np.argmax(scores))
    confidence = float(scores[index])

    return labels[index], confidence


# Configure Front-end from Back-end

@app.get("/")
def home():
    return send_from_directory(str(FRONTEND_PATH), "index.html")

# Post predict request

@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    data_url = payload.get("image")

    if not data_url:
        return jsonify({"error": "Missing image field."}), 400

    try:
        image = decode_data_url(data_url)
        label, confidence = classify(image)

        created_at = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                INSERT INTO predictions (label, confidence, created_at)
                VALUES (?, ?, ?)
                """,
                (label, confidence, created_at),
            )
            prediction_id = cursor.lastrowid

        return jsonify({
            "id": prediction_id,
            "label": label,
            "confidence": confidence,
            "created_at": created_at,
        }), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/predictions")
def get_predictions():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, label, confidence, created_at
            FROM predictions
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()

    return jsonify([dict(row) for row in rows])


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "Image exceeds the 10 MB limit."}), 413


if __name__ == "__main__":
    app.run(debug=True, port=5000)