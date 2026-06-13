import math
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image

RESOLUTIONS = {
    "hd": (1024, 1024),
    "standard": (512, 512),
}


def preprocess_image(image: Image.Image, size: tuple = (1024, 1024)) -> torch.Tensor:
    transform = transforms.Compose([
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return transform(image).unsqueeze(0)


def postprocess_image(original_image: Image.Image, mask_tensor: torch.Tensor) -> Image.Image:
    mask = mask_tensor.detach().cpu().float()
    while mask.dim() > 2:
        mask = mask.squeeze(0)
    mask = torch.nan_to_num(mask, nan=0.0, posinf=1.0, neginf=0.0).clamp(0, 1)
    mask = F.interpolate(
        mask.unsqueeze(0).unsqueeze(0),
        size=(original_image.height, original_image.width),
        mode="bilinear",
        align_corners=False,
    ).squeeze()
    alpha = Image.fromarray(np.uint8(mask.numpy() * 255), mode="L")
    result = original_image.convert("RGBA")
    result.putalpha(alpha)
    return result


def postprocess_mask(mask_tensor: torch.Tensor, target_size: tuple) -> np.ndarray:
    mask = mask_tensor.detach().cpu().float()
    while mask.dim() > 2:
        mask = mask.squeeze(0)
    mask = torch.nan_to_num(mask, nan=0.0, posinf=1.0, neginf=0.0).clamp(0, 1)
    mask = F.interpolate(
        mask.unsqueeze(0).unsqueeze(0),
        size=target_size,
        mode="bilinear",
        align_corners=False,
    ).squeeze()
    return mask.numpy()


# ── Image Tiling ──

def create_tile_grid(width: int, height: int, tile_size: int, overlap: int) -> list:
    if width <= tile_size and height <= tile_size:
        return [{'x': 0, 'y': 0, 'w': tile_size, 'h': tile_size, 'ix': 0, 'iy': 0, 'nx': 1, 'ny': 1}]

    stride = max(1, tile_size - overlap)

    x_starts = _compute_1d_starts(width, tile_size, stride)
    y_starts = _compute_1d_starts(height, tile_size, stride)

    tiles = []
    for iy, y in enumerate(y_starts):
        for ix, x in enumerate(x_starts):
            tiles.append({
                'x': x, 'y': y,
                'w': tile_size, 'h': tile_size,
                'ix': ix, 'iy': iy,
                'nx': len(x_starts), 'ny': len(y_starts),
            })
    return tiles


def _compute_1d_starts(length: int, tile_size: int, max_stride: int) -> list:
    if length <= tile_size:
        return [0]
    num_tiles = max(2, math.ceil((length - tile_size) / max_stride) + 1)
    actual_stride = (length - tile_size) / (num_tiles - 1)
    starts = [round(i * actual_stride) for i in range(num_tiles)]
    starts[-1] = length - tile_size
    return starts


def create_weight_map(tile_size: int, overlap: int) -> np.ndarray:
    wx = np.ones(tile_size, dtype=np.float64)
    wy = np.ones(tile_size, dtype=np.float64)
    ramp = min(overlap, tile_size // 2)
    if ramp > 0:
        for i in range(ramp):
            t = (i + 1) / (ramp + 1)
            wx[i] = t
            wx[-(i + 1)] = t
            wy[i] = t
            wy[-(i + 1)] = t
    return np.outer(wy, wx)


def merge_tile_masks(tile_results: list, original_size: tuple, tile_size: int, overlap: int) -> np.ndarray:
    width, height = original_size
    weight_sum = np.zeros((height, width), dtype=np.float64)
    mask_sum = np.zeros((height, width), dtype=np.float64)
    weight = create_weight_map(tile_size, overlap)

    for tr in tile_results:
        g = tr['grid']
        x, y = g['x'], g['y']
        tile_mask = tr['mask']
        th, tw = tile_mask.shape[:2]
        w_slice = weight[:th, :tw]
        mask_sum[y:y + th, x:x + tw] += tile_mask * w_slice
        weight_sum[y:y + th, x:x + tw] += w_slice

    merged = np.divide(mask_sum, weight_sum, where=weight_sum > 0)
    merged = np.clip(merged, 0, 1)
    return merged


# ── PaddleOCR Text Detection ──

_ocr_instance = None


def get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_instance = PaddleOCR(use_angle_cls=True, lang='en')
        except ImportError:
            print("[OCR] PaddleOCR not installed. Text detection disabled.")
            _ocr_instance = False
        except Exception as e:
            print(f"[OCR] Failed to initialize: {e}")
            _ocr_instance = False
    return _ocr_instance


def detect_text_mask(image: Image.Image, conf_threshold: float = 0.5) -> np.ndarray:
    ocr = get_ocr()
    if ocr is False:
        return None
    try:
        img_array = np.array(image.convert("RGB"))
        raw = ocr.ocr(img_array)
        if not raw or not raw[0]:
            return None
        result = [(bbox, text, conf) for bbox, (text, conf) in raw[0]]
        mask = np.zeros((image.height, image.width), dtype=np.uint8)
        try:
            import cv2
            for bbox, text, conf in result:
                if conf >= conf_threshold:
                    pts = np.array(bbox, dtype=np.int32)
                    cv2.fillPoly(mask, [pts], 1)
        except ImportError:
            from PIL import ImageDraw
            for bbox, text, conf in result:
                if conf >= conf_threshold:
                    pts = [tuple(p) for p in bbox]
                    poly_img = Image.new("L", (image.width, image.height), 0)
                    ImageDraw.Draw(poly_img).polygon(pts, fill=1)
                    mask = np.maximum(mask, np.array(poly_img))
        return mask
    except Exception as e:
        print(f"[OCR] Detection error: {e}")
        return None


# ── Mask Fusion ──

def fuse_masks(birefnet_mask: np.ndarray, ocr_mask: np.ndarray, strategy: str = "or") -> np.ndarray:
    if ocr_mask is None:
        return birefnet_mask
    ocr_float = ocr_mask.astype(np.float64)
    if ocr_float.max() > 1:
        ocr_float = ocr_float / 255.0
    if strategy == "or":
        return np.clip(birefnet_mask + ocr_float, 0, 1)
    elif strategy == "add":
        return np.clip(birefnet_mask + ocr_float * 0.5, 0, 1)
    elif strategy == "birefnet":
        return birefnet_mask
    else:
        return np.clip(birefnet_mask + ocr_float, 0, 1)
