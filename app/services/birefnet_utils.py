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
    """Resize, normalize, and batch an RGB PIL image for BiRefNet."""
    transform = transforms.Compose([
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return transform(image).unsqueeze(0)  # [1, 3, H, W]


def postprocess_image(original_image: Image.Image, mask_tensor: torch.Tensor) -> Image.Image:
    """
    Convert the raw sigmoid mask tensor back to a full-resolution RGBA image.
    mask_tensor: any shape with [H, W] as the last two dims (e.g. [1,1,H,W]).
    """
    mask = mask_tensor.detach().cpu().float()

    # Collapse leading batch/channel dims → [H, W]
    while mask.dim() > 2:
        mask = mask.squeeze(0)

    # Sanitize and clamp
    mask = torch.nan_to_num(mask, nan=0.0, posinf=1.0, neginf=0.0).clamp(0, 1)

    # Resize mask to the original image resolution
    mask = F.interpolate(
        mask.unsqueeze(0).unsqueeze(0),
        size=(original_image.height, original_image.width),
        mode="bilinear",
        align_corners=False,
    ).squeeze()

    # Build RGBA image using the mask as the alpha channel
    alpha = Image.fromarray(np.uint8(mask.numpy() * 255), mode="L")
    result = original_image.convert("RGBA")
    result.putalpha(alpha)
    return result
