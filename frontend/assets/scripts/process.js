const processImage = async (link) => {
  loadingContainer.style.display = "flex";

  try {
    const result = await classifyImage(link);

    loadingContainer.style.display = "none";

    if (result.label == "dog") {
      resultsEmoji.innerHTML = "🐶";
    } else {
      resultsEmoji.innerHTML = "🐱";
    }

    resultsLabel.innerHTML = result.label;
    resultsConf.innerHTML = (result.confidence * 100).toFixed(1);

    resultsContainer.style.display = "flex";
  } catch (error) {
    loadingContainer.style.display = "none";
    errorContainer.style.display = "flex";
  }
};

const classifyImage = async (link) => {
  const response = await fetch("/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image: link,
    }),
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.error || "Classification failed");
  }

  return result;
};
