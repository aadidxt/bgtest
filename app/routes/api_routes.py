import io
import shutil
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, send_file

from app.services.bg_remove import remove_background
from app.utils.decorators import auth_required, rate_limit_per_user

api_bp = Blueprint("api", __name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_BULK_FILES = 20

_batches = {}
_batch_lock = threading.Lock()


@api_bp.route("/v1/remove-bg", methods=["POST"])
@auth_required(api_mode=True, enforce_usage=True)
@rate_limit_per_user
def remove_bg():
    from flask import request

    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    resolution = request.form.get("resolution", "hd")
    if resolution not in ("hd", "standard"):
        resolution = "hd"

    processing_mode = request.form.get("processing_mode", "object_detection")

    cfg = current_app.config
    pipeline_kwargs = {
        "processing_mode": processing_mode,
        "tile_size": int(request.form.get("tile_size", cfg.get("TILE_SIZE", "1024"))),
        "overlap": int(request.form.get("overlap", cfg.get("TILE_OVERLAP", "64"))),
        "enable_ocr": True,
        "ocr_conf": float(request.form.get("ocr_conf", cfg.get("OCR_CONFIDENCE_THRESHOLD", "0.5"))),
        "fusion_strategy": request.form.get("fusion_strategy", cfg.get("MASK_FUSION_STRATEGY", "or")),
    }

    try:
        output = remove_background(file.read(), resolution=resolution, **pipeline_kwargs)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        print("ERROR:", repr(exc))
        return jsonify({"error": f"Background removal failed: {exc}"}), 500

    return send_file(io.BytesIO(output), mimetype="image/png")


def _cleanup_stale_batches():
    now = time.time()
    with _batch_lock:
        stale = [bid for bid, info in _batches.items()
                 if now - info["created_at"] > 3600]
        for bid in stale:
            info = _batches[bid]
            shutil.rmtree(info["temp_dir"], ignore_errors=True)
            del _batches[bid]


def _process_batch(batch_id):
    info = _batches.get(batch_id)
    if not info:
        return
    files = info["files"]
    resolution = info["resolution"]
    temp_dir = Path(info["temp_dir"])
    pipeline_kwargs = info.get("pipeline_kwargs", {})
    total = len(files)
    completed = 0
    failed = 0

    for filename, data in files:
        try:
            result_bytes = remove_background(data, resolution=resolution, **pipeline_kwargs)
            stem = Path(filename).stem
            out_name = f"{stem}_processed.png"
            (temp_dir / out_name).write_bytes(result_bytes)
            completed += 1
        except Exception as e:
            print(f"[Bulk] Failed to process {filename}: {e}")
            failed += 1

        with _batch_lock:
            current = _batches.get(batch_id)
            if current:
                current["completed"] = completed
                current["failed"] = failed
                current["pending"] = total - completed - failed

    with _batch_lock:
        current = _batches.get(batch_id)
        if current:
            current["status"] = "completed"


@api_bp.route("/v1/remove-bg/bulk", methods=["POST"])
@auth_required(api_mode=True, enforce_usage=True)
@rate_limit_per_user
def remove_bg_bulk():
    from flask import request

    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "No image files provided."}), 400

    if len(files) > MAX_BULK_FILES:
        return jsonify({"error": f"Maximum {MAX_BULK_FILES} files per batch."}), 400

    resolution = request.form.get("resolution", "hd")
    if resolution not in ("hd", "standard"):
        resolution = "hd"

    validated = []
    for f in files:
        if not f.filename:
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"error": f"Unsupported file type: {f.filename}"}), 400
        data = f.read()
        if len(data) > MAX_FILE_SIZE:
            return jsonify({"error": f"File too large: {f.filename} (max 10MB)"}), 400
        validated.append((f.filename, data))

    if not validated:
        return jsonify({"error": "No valid image files provided."}), 400

    processing_mode = request.form.get("processing_mode", "object_detection")

    cfg = current_app.config
    pipeline_kwargs = {
        "processing_mode": processing_mode,
        "tile_size": int(cfg.get("TILE_SIZE", "1024")),
        "overlap": int(cfg.get("TILE_OVERLAP", "64")),
        "enable_ocr": True,
        "ocr_conf": float(cfg.get("OCR_CONFIDENCE_THRESHOLD", "0.5")),
        "fusion_strategy": cfg.get("MASK_FUSION_STRATEGY", "or"),
    }

    batch_id = uuid.uuid4().hex
    temp_dir = Path(tempfile.mkdtemp(prefix=f"bulk_{batch_id}_"))

    info = {
        "batch_id": batch_id,
        "files": validated,
        "resolution": resolution,
        "temp_dir": str(temp_dir),
        "status": "processing",
        "total": len(validated),
        "completed": 0,
        "failed": 0,
        "pending": len(validated),
        "created_at": time.time(),
        "pipeline_kwargs": pipeline_kwargs,
    }

    with _batch_lock:
        _batches[batch_id] = info

    _cleanup_stale_batches()

    thread = threading.Thread(target=_process_batch, args=(batch_id,), daemon=True)
    thread.start()

    return jsonify({"batch_id": batch_id, "total": len(validated)})


@api_bp.route("/v1/remove-bg/bulk/<batch_id>/status", methods=["GET"])
def bulk_status(batch_id):
    with _batch_lock:
        info = _batches.get(batch_id)
    if not info:
        return jsonify({"error": "Batch not found"}), 404
    return jsonify({
        "status": info["status"],
        "total": info["total"],
        "completed": info["completed"],
        "failed": info["failed"],
        "pending": info["pending"],
    })


@api_bp.route("/v1/remove-bg/bulk/<batch_id>/download", methods=["GET"])
def bulk_download(batch_id):
    with _batch_lock:
        info = _batches.get(batch_id)
    if not info:
        return jsonify({"error": "Batch not found"}), 404
    if info["status"] != "completed":
        return jsonify({"error": "Batch not yet completed"}), 400

    temp_dir = Path(info["temp_dir"])
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for png_file in sorted(temp_dir.iterdir()):
            if png_file.suffix == ".png":
                zf.write(png_file, png_file.name)

    zip_buf.seek(0)

    shutil.rmtree(temp_dir, ignore_errors=True)
    with _batch_lock:
        _batches.pop(batch_id, None)

    return send_file(
        zip_buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name="processed_images.zip",
    )
