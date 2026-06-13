const fileInput = document.getElementById("fileInput");
const processBtn = document.getElementById("processBtn");
const uploadPreview = document.getElementById("uploadPreview");
const result = document.getElementById("result");
const download = document.getElementById("download");
const statusEl = document.getElementById("status");
const todayUsageEl = document.getElementById("todayUsage");
const totalUsageEl = document.getElementById("totalUsage");
const remainingUsageEl = document.getElementById("remainingUsage");
const singleDropZone = document.getElementById("singleDropZone");
const pipelineStages = document.getElementById("pipelineStages");
const originalPlaceholder = document.getElementById("originalPlaceholder");
const processedPlaceholder = document.getElementById("processedPlaceholder");
const originalInfo = document.getElementById("originalInfo");
const processedInfo = document.getElementById("processedInfo");

const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;
const MAX_FILES = 20;

/* ───────── Processing Mode ───────── */

let currentMode = "object_detection";

const STAGES = {
  object_detection: [
    { id: "upload", label: "Uploading" },
    { id: "detection", label: "Removing Background" },
    { id: "rendering", label: "Generating PNG" },
  ],
  text_graphic: [
    { id: "upload", label: "Uploading" },
    { id: "tiling", label: "Generating Tiles" },
    { id: "detection", label: "Detecting Text" },
    { id: "graphics", label: "Detecting Graphics" },
    { id: "merging", label: "Merging Masks" },
    { id: "refining", label: "Refining Edges" },
    { id: "rendering", label: "Generating PNG" },
  ],
};

function getCurrentStages() {
  return STAGES[currentMode] || STAGES.object_detection;
}

document.querySelectorAll(".segmented-option").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".segmented-option").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentMode = btn.dataset.mode;
    resetPipeline();
  });
});

/* ───────── Pipeline Stage UI ───────── */

function buildStages() {
  if (!pipelineStages) return;
  pipelineStages.innerHTML = "";
  const stages = getCurrentStages();
  stages.forEach((s) => {
    const div = document.createElement("div");
    div.className = "stage";
    div.dataset.stageId = s.id;
    div.innerHTML =
      `<span class="stage-icon">&#9654;</span>` +
      `<span class="stage-label">${s.label}</span>` +
      `<span class="stage-status"></span>`;
    pipelineStages.appendChild(div);
  });
}

function resetPipeline() {
  if (!pipelineStages) return;
  pipelineStages.style.display = "none";
  pipelineStages.querySelectorAll(".stage").forEach((el) => {
    el.classList.remove("active", "done");
    const icon = el.querySelector(".stage-icon");
    if (icon) icon.textContent = "\u25B6";
    const st = el.querySelector(".stage-status");
    if (st) st.textContent = "";
  });
  statusEl.innerText = "";
}

function showStage(stageId) {
  if (!pipelineStages) return;
  pipelineStages.style.display = "flex";
  const stages = getCurrentStages();
  let activeFound = false;
  stages.forEach((s) => {
    const el = pipelineStages.querySelector(`[data-stage-id="${s.id}"]`);
    if (!el) return;
    if (s.id === stageId) {
      el.classList.add("active");
      el.classList.remove("done");
      el.querySelector(".stage-icon").textContent = "\u25B6";
      el.querySelector(".stage-status").textContent = "In progress\u2026";
      activeFound = true;
    } else if (!activeFound) {
      el.classList.remove("active");
      el.classList.add("done");
      el.querySelector(".stage-icon").textContent = "\u2713";
      el.querySelector(".stage-status").textContent = "Done";
    } else {
      el.classList.remove("active", "done");
      el.querySelector(".stage-icon").textContent = "\u25B6";
      el.querySelector(".stage-status").textContent = "";
    }
  });
}

function finishStages() {
  if (!pipelineStages) return;
  pipelineStages.querySelectorAll(".stage").forEach((el) => {
    el.classList.remove("active");
    el.classList.add("done");
    el.querySelector(".stage-icon").textContent = "\u2713";
    el.querySelector(".stage-status").textContent = "Done";
  });
}

/* ───────── Stage Simulation ───────── */

let stageTimer = null;
let stageIndex = 0;

function startStageSimulation() {
  resetPipeline();
  buildStages();
  stageIndex = 0;
  const stages = getCurrentStages();
  if (stages.length > 0) showStage(stages[0].id);
  const stageDuration = 800;

  if (stageTimer) clearInterval(stageTimer);
  stageTimer = setInterval(() => {
    stageIndex++;
    const stages = getCurrentStages();
    if (stageIndex < stages.length) {
      showStage(stages[stageIndex].id);
    } else {
      clearInterval(stageTimer);
      stageTimer = null;
    }
  }, stageDuration);
}

function stopStageSimulation(completed) {
  if (stageTimer) {
    clearInterval(stageTimer);
    stageTimer = null;
  }
  if (completed) {
    finishStages();
  } else {
    resetPipeline();
  }
}

/* ───────── Single Image Upload ───────── */

function hasImage() {
  return fileInput?.files?.length > 0;
}

function updateProcessBtn() {
  processBtn.disabled = !hasImage();
}

function showOriginalImage(file) {
  const url = URL.createObjectURL(file);
  uploadPreview.src = url;
  uploadPreview.style.display = "block";
  if (originalPlaceholder) originalPlaceholder.style.display = "none";
  if (originalInfo) {
    const img = new Image();
    img.onload = () => {
      originalInfo.textContent = `${img.naturalWidth} x ${img.naturalHeight}`;
    };
    img.src = url;
  }
  updateProcessBtn();
  resetPipeline();
}

singleDropZone?.addEventListener("click", () => fileInput?.click());

singleDropZone?.addEventListener("dragover", (e) => {
  e.preventDefault();
  singleDropZone.classList.add("drag-over");
});

singleDropZone?.addEventListener("dragleave", () => {
  singleDropZone.classList.remove("drag-over");
});

singleDropZone?.addEventListener("drop", (e) => {
  e.preventDefault();
  singleDropZone.classList.remove("drag-over");
  if (e.dataTransfer.files.length) {
    const file = e.dataTransfer.files[0];
    if (!ALLOWED_TYPES.includes(file.type)) {
      alert(`"${file.name}" is not a supported image type.`);
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      alert(`"${file.name}" exceeds the 10 MB limit.`);
      return;
    }
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    showOriginalImage(file);
  }
});

fileInput?.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  if (!ALLOWED_TYPES.includes(file.type)) {
    alert(`"${file.name}" is not a supported image type.`);
    fileInput.value = "";
    updateProcessBtn();
    return;
  }
  if (file.size > MAX_FILE_SIZE) {
    alert(`"${file.name}" exceeds the 10 MB limit.`);
    fileInput.value = "";
    updateProcessBtn();
    return;
  }
  showOriginalImage(file);
});

/* ───────── Process Single Image ───────── */

processBtn?.addEventListener("click", async () => {
  if (!hasImage()) {
    statusEl.innerText = "Please select an image first.";
    return;
  }

  const startTime = Date.now();
  statusEl.innerText = "Processing... 0.0s";
  processBtn.disabled = true;

  const timer = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    statusEl.innerText = `Processing... ${elapsed}s`;
  }, 100);

  startStageSimulation();

  const resolutionToggle = document.getElementById("resolutionToggle");
  const resolution = resolutionToggle?.checked ? "hd" : "standard";

  const formData = new FormData();
  formData.append("image", fileInput.files[0]);
  formData.append("resolution", resolution);
  formData.append("processing_mode", currentMode);

  try {
    const response = await fetch("/api/v1/remove-bg", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      clearInterval(timer);
      const data = await response.json().catch(() => ({}));
      statusEl.innerText = data.error || "Request failed.";
      stopStageSimulation(false);
      processBtn.disabled = false;
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    result.src = url;
    result.style.display = "block";
    if (processedPlaceholder) processedPlaceholder.style.display = "none";
    download.href = url;
    download.style.display = "inline-block";

    if (processedInfo) {
      const img = new Image();
      img.onload = () => {
        processedInfo.textContent = `${img.naturalWidth} x ${img.naturalHeight}`;
      };
      img.src = url;
    }

    if (todayUsageEl) {
      todayUsageEl.innerText = response.headers.get("X-Usage-Used") || todayUsageEl.innerText;
      remainingUsageEl.innerText =
        response.headers.get("X-Remaining-Usage") || remainingUsageEl.innerText;
      totalUsageEl.innerText = String(Number(totalUsageEl.innerText || "0") + 1);
    }

    clearInterval(timer);
    stopStageSimulation(true);

    const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
    statusEl.innerText = `\u2705 Done in ${totalTime} seconds`;
  } catch (err) {
    clearInterval(timer);
    stopStageSimulation(false);
    statusEl.innerText = "Network or server error.";
  }
  processBtn.disabled = false;
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

let selectedFiles = [];
let batchId = null;
let pollTimer = null;
let bulkTimer = null;
let bulkStartTime = null;

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

bulkProcessBtn?.addEventListener("click", async () => {
  if (selectedFiles.length === 0) return;

  const resolutionToggle = document.getElementById("resolutionToggle");
  const resolution = resolutionToggle?.checked ? "hd" : "standard";

  const formData = new FormData();
  for (const file of selectedFiles) formData.append("images", file);
  formData.append("resolution", resolution);
  formData.append("processing_mode", currentMode);

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

/* ───────── Init ───────── */

buildStages();
updateProcessBtn();

if (!result.src || result.src === "") {
  result.style.display = "none";
}
