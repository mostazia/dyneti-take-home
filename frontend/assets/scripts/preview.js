const togglePreview = (bool) => {
  if (bool) {
    imagePreview.style.display = "block";
    imageContainer.style.display = "flex";
  } else {
    imagePreview.style.display = "none";
  }
};

const updatePreview = (link) => {
  togglePreview(false);

  imagePreview.src = link;

  togglePreview(true);
};

const toggleOptions = (bool) => {};
