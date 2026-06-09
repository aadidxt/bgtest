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

  // statusEl.innerText = "Processing...";

  const startTime = Date.now();

  statusEl.innerText = "Processing... 0.0s";

  const timer = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    statusEl.innerText = `Processing... ${elapsed}s`;
  }, 100);


  const resolutionToggle = document.getElementById("resolutionToggle");
  const resolution = resolutionToggle?.checked ? "hd" : "standard";

  const formData = new FormData();
  formData.append("image", fileInput.files[0]);
  formData.append("resolution", resolution);

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

    // statusEl.innerText = "Done";
    clearInterval(timer);

    const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
    statusEl.innerText = `✅ Done in ${totalTime} seconds`;
  } catch (err) {
    clearInterval(timer);
    statusEl.innerText = "Network or server error.";
  }
});

/* ───────── Bulk Upload ───────── */

const dropZone = document.getElementById("dropZone");
const bulkFileInput = document.getElementById("bulkFileInput");
const bulkFileList = document.getElementById("bulkFileList");
const bulkProcessBtn = document.getElementById("bulkProcessBtn");
const bulkProgress = document.getElementById("bulkProgress");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const bulkSummary = document.getElementById("bulkSummary");
const bulkDownloadBtn = document.getElementById("bulkDownloadBtn");

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;
const MAX_FILES = 20;

let selectedFiles = [];
let batchId = null;
let pollTimer = null;
let bulkTimer = null;
let bulkStartTime = null;

/* ── Drag / drop / click ── */

dropZone?.addEventListener("click", () => bulkFileInput?.click());

dropZone?.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone?.addEventListener("dragleave", () => {
  dropZone.classList.remove("drag-over");
});

dropZone?.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
});

bulkFileInput?.addEventListener("change", () => {
  if (bulkFileInput.files.length) addFiles(bulkFileInput.files);
  bulkFileInput.value = "";
});

/* ── File validation & list ── */

function addFiles(fileList) {
  const newFiles = [];
  for (const file of fileList) {
    if (!ALLOWED_TYPES.includes(file.type)) {
      alert(`"${file.name}" is not a supported image type.`);
      continue;
    }
    if (file.size > MAX_FILE_SIZE) {
      alert(`"${file.name}" exceeds the 10 MB limit.`);
      continue;
    }
    newFiles.push(file);
  }
  if (selectedFiles.length + newFiles.length > MAX_FILES) {
    alert(`Maximum ${MAX_FILES} files allowed.`);
    return;
  }
  selectedFiles = selectedFiles.concat(newFiles);
  renderFileList();
}

function renderFileList() {
  bulkFileList.innerHTML = selectedFiles
    .map(
      (f, i) =>
        `<div class="bulk-file-item">
          <span class="file-name">${escapeHtml(f.name)}</span>
          <span class="file-size">${(f.size / 1024).toFixed(1)} KB</span>
          <button class="file-remove" data-index="${i}">&times;</button>
        </div>`
    )
    .join("");

  bulkFileList.querySelectorAll(".file-remove").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedFiles.splice(parseInt(btn.dataset.index, 10), 1);
      renderFileList();
    });
  });

  bulkProcessBtn.disabled = selectedFiles.length === 0;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

/* ── Process All ── */

bulkProcessBtn?.addEventListener("click", async () => {
  if (selectedFiles.length === 0) return;

  const resolutionToggle = document.getElementById("resolutionToggle");
  const resolution = resolutionToggle?.checked ? "hd" : "standard";

  const formData = new FormData();
  for (const file of selectedFiles) formData.append("images", file);
  formData.append("resolution", resolution);

  bulkProcessBtn.disabled = true;
  bulkProgress.style.display = "block";
  bulkSummary.style.display = "none";
  bulkDownloadBtn.style.display = "none";
  progressFill.style.width = "0%";
  progressText.innerText = `Uploading ${selectedFiles.length} file(s)...`;

  bulkStartTime = Date.now();
  bulkTimer = setInterval(() => {
    if (bulkStartTime) {
      const elapsed = ((Date.now() - bulkStartTime) / 1000).toFixed(1);
      progressText.innerText = progressText.innerText.replace(/\s+\([\d.]+s\)$/, "") + ` (${elapsed}s)`;
    }
  }, 100);

  try {
    const resp = await fetch("/api/v1/remove-bg/bulk", { method: "POST", body: formData });
    if (!resp.ok) {
      clearInterval(bulkTimer);
      const data = await resp.json().catch(() => ({}));
      alert(data.error || "Bulk processing failed.");
      bulkProcessBtn.disabled = false;
      bulkProgress.style.display = "none";
      return;
    }

    const { batch_id, total } = await resp.json();
    batchId = batch_id;

    progressText.innerText = `Processing 0 / ${total} (0.0s)`;

    pollTimer = setInterval(async () => {
      try {
        const sr = await fetch(`/api/v1/remove-bg/bulk/${batchId}/status`);
        if (!sr.ok) { clearInterval(pollTimer); clearInterval(bulkTimer); return; }
        const s = await sr.json();
        const elapsed = bulkStartTime ? ((Date.now() - bulkStartTime) / 1000).toFixed(1) : "?";

        const pct = s.total > 0 ? Math.round(((s.completed + s.failed) / s.total) * 100) : 0;
        progressFill.style.width = `${pct}%`;
        progressText.innerText =
          `Completed: ${s.completed}  |  Failed: ${s.failed}  |  Pending: ${s.pending} (${elapsed}s)`;

        if (s.status === "completed") {
          clearInterval(pollTimer);
          clearInterval(bulkTimer);
          finishBulk(s);
        }
      } catch (_) { /* ignore polling errors */ }
    }, 1000);
  } catch (err) {
    clearInterval(pollTimer);
    clearInterval(bulkTimer);
    alert("Network or server error.");
    bulkProcessBtn.disabled = false;
    bulkProgress.style.display = "none";
  }
});

function finishBulk(status) {
  const totalTime = bulkStartTime ? ((Date.now() - bulkStartTime) / 1000).toFixed(2) : "?";
  bulkSummary.style.display = "block";
  let html = `<p class="summary-line success">${status.completed} processed successfully</p>`;
  if (status.failed > 0) {
    html += `<p class="summary-line fail">${status.failed} failed</p>`;
  }
  html += `<p class="summary-line total-time">Done in ${totalTime}s</p>`;
  bulkSummary.innerHTML = html;

  if (status.completed > 0) {
    bulkDownloadBtn.style.display = "inline-block";
    bulkDownloadBtn.href = `/api/v1/remove-bg/bulk/${batchId}/download`;
  }

  bulkProcessBtn.disabled = false;
}

/* ── Download ZIP ── */

bulkDownloadBtn?.addEventListener("click", () => {
  setTimeout(() => {
    selectedFiles = [];
    batchId = null;
    bulkTimer = null;
    bulkStartTime = null;
    renderFileList();
    bulkProgress.style.display = "none";
    bulkSummary.style.display = "none";
    bulkDownloadBtn.style.display = "none";
    progressFill.style.width = "0%";
  }, 2000);
});
