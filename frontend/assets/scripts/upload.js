const triggerImageUpload = () => {
  imageInput.click();
};

const handleImageUpload = (event) => {
  const file = event.target.files[0];

  if (!file) return;

  startMenu.style.display = "none";

  const img = new Image();

  img.onload = () => {
    // Determine image size
    const size = Math.min(img.width, img.height);

    // Determine image center
    const sx = (img.width - size) / 2;
    const sy = (img.height - size) / 2;

    // Set canvas size to image size
    canvas.width = size;
    canvas.height = size;

    const context = canvas.getContext("2d");

    // Draw image (centered)
    context.drawImage(img, sx, sy, size, size, 0, 0, size, size);

    // Convert to dataURL
    const dataURL = canvas.toDataURL("image/jpeg", 0.9);

    // Attach the image to preview image
    updatePreview(dataURL);
    processImage(dataURL);

    URL.revokeObjectURL(img.src);
  };

  img.src = URL.createObjectURL(file);
};
