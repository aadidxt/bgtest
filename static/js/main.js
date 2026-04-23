const fileInput = document.getElementById("fileInput");
const processBtn = document.getElementById("processBtn");
const uploadPreview = document.getElementById("uploadPreview");
const result = document.getElementById("result");
const download = document.getElementById("download");
const statusEl = document.getElementById("status");
const todayUsageEl = document.getElementById("todayUsage");
const totalUsageEl = document.getElementById("totalUsage");
const remainingUsageEl = document.getElementById("remainingUsage");

fileInput?.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) {
    return;
  }
  uploadPreview.src = URL.createObjectURL(file);
  uploadPreview.style.display = "block";
});

processBtn?.addEventListener("click", async () => {
  if (!fileInput.files[0]) {
    statusEl.innerText = "Please select an image first.";
    return;
  }

  statusEl.innerText = "Processing...";
  const formData = new FormData();
  formData.append("image", fileInput.files[0]);

  try {
    const response = await fetch("/api/v1/remove-bg", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      statusEl.innerText = data.error || "Request failed.";
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    result.src = url;
    result.style.display = "block";
    download.href = url;
    download.style.display = "inline-block";

    todayUsageEl.innerText = response.headers.get("X-Usage-Used") || todayUsageEl.innerText;
    remainingUsageEl.innerText =
      response.headers.get("X-Remaining-Usage") || remainingUsageEl.innerText;
    totalUsageEl.innerText = String(Number(totalUsageEl.innerText || "0") + 1);

    statusEl.innerText = "Done";
  } catch (err) {
    statusEl.innerText = "Network or server error.";
  }
});
