let stream;

const triggerWebcam = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: false,
      aspectRatio: 1,
    });

    togglePreview(false);
    startMenu.style.display = "none";

    // Add stream to video element, unhide video
    video.srcObject = stream;
    video.hidden = false;

    imageContainer.style.display = "flex";

    // Display snap photo button
    snapButton.style.display = "flex";
  } catch (error) {
    console.error("Could not access webcam:", error);
  }
};

const snapPhoto = () => {
  const size = Math.min(video.videoWidth, video.videoHeight);

  //   Determine video center
  const sx = (video.videoWidth - size) / 2;
  const sy = (video.videoHeight - size) / 2;

  //   Set canvas size to image size
  canvas.width = size;
  canvas.height = size;

  const context = canvas.getContext("2d");

  //   Draw image (centered)
  context.drawImage(video, sx, sy, size, size, 0, 0, size, size);

  // Attach the image to image preview
  const dataURL = canvas.toDataURL("image/jpeg", 0.9);

  updatePreview(dataURL);
  processImage(dataURL);

  //   Turn off webcam and reset stream
  stream.getTracks().forEach((track) => track.stop());
  video.srcObject = null;
  video.hidden = true;
  snapButton.style.display = "none";
};
