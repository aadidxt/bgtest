from app.services.birefnet_model import remove_background_birefnet


def remove_background(image_bytes: bytes, resolution: str = "hd") -> bytes:
    return remove_background_birefnet(image_bytes, resolution=resolution)