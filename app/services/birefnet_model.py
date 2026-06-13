import io
import os
# pyrefly: ignore [missing-import]
import torch
from PIL import Image
import numpy as np
from transformers import AutoModelForImageSegmentation
from app.services.birefnet_utils import (
    RESOLUTIONS,
    preprocess_image,
    postprocess_mask,
    create_tile_grid,
    merge_tile_masks,
    detect_text_mask,
    fuse_masks,
)

_birefnet_model = None
_device = None


def _get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_model():
    global _birefnet_model, _device
    if _birefnet_model is None:
        _device = _get_device()
        print(f"[BiRefNet] Loading model on {_device}...")
        model = AutoModelForImageSegmentation.from_pretrained(
            "ZhengPeng7/BiRefNet",
            trust_remote_code=True,
        )
        model.to(_device)
        model.float()
        model.eval()
        _birefnet_model = model
        print("[BiRefNet] Model ready.")
    return _birefnet_model, _device


def _run_inference(model, device, input_tensor):
    with torch.no_grad():
        outputs = model(input_tensor)
    preds = outputs[0] if isinstance(outputs, (list, tuple)) else outputs
    preds = preds[0] if isinstance(preds, (list, tuple)) else preds
    return torch.sigmoid(preds).cpu().float()


def remove_background_standard(
    image_bytes: bytes,
    resolution: str = "hd",
) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    model, device = _load_model()
    model_size = RESOLUTIONS.get(resolution, RESOLUTIONS["hd"])

    input_tensor = preprocess_image(image, size=model_size).to(device)
    preds = _run_inference(model, device, input_tensor)
    birefnet_mask = postprocess_mask(preds, (image.height, image.width))

    alpha = Image.fromarray(np.uint8(np.clip(birefnet_mask * 255, 0, 255)), mode="L")
    result = image.convert("RGBA")
    result.putalpha(alpha)

    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


def remove_background_advanced(
    image_bytes: bytes,
    resolution: str = "hd",
    **kwargs,
) -> bytes:
    try:
        tile_size = int(kwargs.get("tile_size", os.getenv("TILE_SIZE", "1024")))
        overlap = int(kwargs.get("overlap", os.getenv("TILE_OVERLAP", "64")))
        enable_ocr = kwargs.get(
            "enable_ocr",
            os.getenv("OCR_ENABLED", "true").lower() == "true",
        )
        ocr_conf = float(kwargs.get("ocr_conf", os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.5")))
        fusion_strategy = kwargs.get(
            "fusion_strategy",
            os.getenv("MASK_FUSION_STRATEGY", "or"),
        )
        max_res = int(kwargs.get("max_resolution", os.getenv("MAX_IMAGE_RESOLUTION", "4096")))

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        model, device = _load_model()

        model_size = RESOLUTIONS.get(resolution, RESOLUTIONS["hd"])
        actual_tile_size = min(tile_size, model_size[0])
        actual_overlap = min(overlap, actual_tile_size // 2)

        orig_w, orig_h = image.size
        needs_tiling = (
            (orig_w > actual_tile_size or orig_h > actual_tile_size)
            and max(orig_w, orig_h) <= max_res
        )

        if not needs_tiling:
            input_tensor = preprocess_image(image, size=model_size).to(device)
            preds = _run_inference(model, device, input_tensor)
            birefnet_mask = postprocess_mask(preds, (orig_h, orig_w))
        else:
            tiles = create_tile_grid(orig_w, orig_h, actual_tile_size, actual_overlap)
            tile_results = []
            for grid in tiles:
                tile = image.crop((
                    grid["x"],
                    grid["y"],
                    grid["x"] + grid["w"],
                    grid["y"] + grid["h"],
                ))
                input_tensor = preprocess_image(tile, size=model_size).to(device)
                preds = _run_inference(model, device, input_tensor)
                tile_mask = postprocess_mask(preds, (tile.height, tile.width))
                tile_results.append({"grid": grid, "mask": tile_mask})

            birefnet_mask = merge_tile_masks(
                tile_results, (orig_w, orig_h), actual_tile_size, actual_overlap,
            )

        ocr_mask = None
        if enable_ocr:
            ocr_mask = detect_text_mask(image, conf_threshold=ocr_conf)

        fused = fuse_masks(birefnet_mask, ocr_mask, fusion_strategy)

        alpha = Image.fromarray(np.uint8(np.clip(fused * 255, 0, 255)), mode="L")
        result = image.convert("RGBA")
        result.putalpha(alpha)

        buf = io.BytesIO()
        result.save(buf, format="PNG")
        return buf.getvalue()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR:", repr(e))
        raise
