import io
import torch
from PIL import Image
from transformers import AutoModelForImageSegmentation
from app.services.birefnet_utils import preprocess_image, postprocess_image

_birefnet_model = None
_device = None


def _get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_model():
    global _birefnet_model, _device

    if _birefnet_model is None:
        _device = _get_device()
        print(f"[BiRefNet] Loading model on {_device}...")

        import os

        model = AutoModelForImageSegmentation.from_pretrained(
        "ZhengPeng7/BiRefNet",
        trust_remote_code=True
    )

        model.to(_device)
        model.float()
        model.eval()

        _birefnet_model = model
        print("[BiRefNet] Model ready.")

    return _birefnet_model, _device



def remove_background_birefnet(image_bytes: bytes, resolution: str = "hd") -> bytes:
    try:
        
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        
        model, device = _load_model()

        
        from app.services.birefnet_utils import RESOLUTIONS
        size = RESOLUTIONS.get(resolution, RESOLUTIONS["hd"])
        input_tensor = preprocess_image(image, size=size).to(device)

        
        with torch.no_grad():
            outputs = model(input_tensor)

       
        preds = outputs[0] if isinstance(outputs, (list, tuple)) else outputs
        preds = preds[0] if isinstance(preds, (list, tuple)) else preds
        preds = torch.sigmoid(preds).cpu().float()

       
        result = postprocess_image(image, preds)

       
        buf = io.BytesIO()
        result.save(buf, format="PNG")

       
        return buf.getvalue()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR:", repr(e))
        raise


