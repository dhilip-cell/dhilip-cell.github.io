const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatLog = document.getElementById("chat-log");
const uploadForm = document.getElementById("upload-form");
const uploadStatus = document.getElementById("upload-status");

function appendMessage(text, type = "bot") {
  const bubble = document.createElement("div");
  bubble.className = message ;
  bubble.textContent = text;
  chatLog.appendChild(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function sendChatMessage(message) {
  appendMessage(message, "user");
  chatInput.value = "";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const errorBody = await response.json();
      const errMsg = errorBody.reply || errorBody.error || "Unable to process your request.";
      appendMessage(errMsg, "bot");
      return;
    }

    const data = await response.json();
    let replyText = data.reply || "I'm here to help!";
    let messageType = "bot";
    if (data.source === "dataset") {
      replyText = Dataset insight:\n;
      messageType = "bot dataset";
    } else if (typeof data.confidence === "number" && data.confidence > 0) {
      replyText = ${replyText}\n(confidence: %);
    }
    appendMessage(replyText, messageType);
  } catch (error) {
    appendMessage("Network error. Please try again.", "bot");
    console.error(error);
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (message) {
    sendChatMessage(message);
  }
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(uploadForm);
  uploadStatus.textContent = "Uploading...";

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      uploadStatus.textContent = data.error || "Upload failed.";
      uploadStatus.style.color = "#dc2626";
      return;
    }
    uploadStatus.textContent = data.message;
    uploadStatus.style.color = "#1d4ed8";
    if (data.summary) {
      appendMessage(Dataset summary:\n, "bot");
    }
  } catch (error) {
    uploadStatus.textContent = "Network error during upload.";
    uploadStatus.style.color = "#dc2626";
    console.error(error);
  }
});

