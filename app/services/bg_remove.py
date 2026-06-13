from app.services.birefnet_model import remove_background_advanced, remove_background_standard


def remove_background(image_bytes: bytes, resolution: str = "hd", **kwargs) -> bytes:
    mode = kwargs.pop("processing_mode", "object_detection")
    if mode == "text_graphic":
        kwargs["enable_ocr"] = True
        return remove_background_advanced(image_bytes, resolution=resolution, **kwargs)
    return remove_background_standard(image_bytes, resolution=resolution)
