# Dependency Audit Report

**Generated:** 2026-06-10
**Project:** Background Removal SaaS (BiRefNet)

---

## Summary

| Metric | Value |
|--------|-------|
| Python files scanned | 19 |
| Total distinct third-party imports | 14 |
| Packages in old `requirements.txt` | 15 |
| Packages in new `requirements.txt` | 15 |
| Packages removed | 3 |
| Packages added | 3 |
| Packages kept | 12 |

---

## Added Dependencies

| Package | Version | Reason |
|---------|---------|--------|
| `pymongo>=4.0,<5` | ≥4.0, <5 | Directly imported in `app/models/user_model.py` (lines 3-4) and `app/services/usage_service.py` (line 4). Previously only available transitively via `flask-pymongo`. |
| `paddleocr>=2.7.0` | ≥2.7 | Dynamically imported in `app/services/birefnet_utils.py` for OCR-based text detection mask. Replaces EasyOCR. Wrapped in `try/except ImportError`. |
| `paddlepaddle>=2.5.0` | ≥2.5.0 | Required backend for PaddleOCR. Provides GPU acceleration via PaddlePaddle's own CUDA support. |

---

## Removed Dependencies

| Package | Old Version | Reason |
|---------|-------------|--------|
| `einops` | (no pin) | Not imported in any application file. May be a transitive dependency of `transformers` or `timm`, but is not required directly. |
| `kornia` | (no pin) | Not imported in any application file. |
| `timm` | (no pin) | Not imported in any application file. May be used internally by the BiRefNet model loaded via `transformers`, but is not required directly. |

---

## Dependency Conflicts Found

None identified. All version ranges are compatible based on current installed packages:

| Package | New Constraint | Installed Version | Compatible |
|---------|---------------|-------------------|------------|
| `flask` | `==3.0.*` | 3.0.3 | ✅ |
| `flask-cors` | `==4.0.*` | 4.0.2 | ✅ |
| `flask-pymongo` | `==2.3.*` | 2.3.0 | ✅ |
| `bcrypt` | `==4.2.*` | 4.2.1 | ✅ |
| `pymongo` | `>=4.0,<5` | 4.17.0 | ✅ |
| `torch` | `>=2.0.0` | 2.12.0 | ✅ |
| `torchvision` | `>=0.15.0` | 0.27.0 | ✅ |
| `transformers` | `>=4.30.0` | 5.10.2 | ✅ |

`flask-pymongo==2.3.0` requires `pymongo>=3,<5`, which is satisfied by `pymongo>=4.0,<5`.

---

## Missing Modules Resolved

| Module | File | Line | Status |
|--------|------|------|--------|
| `pymongo` | `app/models/user_model.py` | 3-4 | Added |
| `pymongo` | `app/services/usage_service.py` | 4 | Added |
| `paddleocr` | `app/services/birefnet_utils.py` | OCR section | Replaced easyocr |
| `cv2` | `app/services/birefnet_utils.py` | 157 | Added |

---

## Compatibility Notes

1. **PaddleOCR installation:** `paddleocr` uses PaddlePaddle as its backend. It auto-detects GPU via `paddle.is_compiled_with_cuda()`.

2. **OpenCV:** `opencv-python` provides the `cv2` module. Consider using `opencv-python-headless` for server deployments to reduce size if GUI features are never needed.

3. **einops / kornia / timm:** These were removed because no application code imports them. If any of these are required internally by `transformers` for specific model architectures (e.g., BiRefNet), they will be installed automatically as transitive dependencies.

4. **Production deployment:** `gunicorn` is retained as it is referenced in `Procfile` for Heroku-style deployments, even though it is not a Python-level import.

5. **Python version:** The application targets Python 3.12+ (as specified in `Dockerfile`).

---

## Packages Requiring Manual Review

| Package | Concern |
|---------|---------|
| `paddleocr>=2.7.0` | First-time download of recognition models. GPU acceleration uses PaddlePaddle CUDA backend. |
| `opencv-python>=4.5.0` | On some platforms, `opencv-python` can conflict with other OpenCV installations. The code handles `ImportError` gracefully, but for full OCR functionality this package must be installed. |

---

## File-by-File Import Map

| File | Third-Party Imports |
|------|-------------------|
| `run.py` | flask |
| `config.py` | python-dotenv |
| `app/__init__.py` | flask, flask-cors, flask-pymongo, certifi |
| `app/models/user_model.py` | pymongo |
| `app/routes/api_routes.py` | flask |
| `app/routes/auth_routes.py` | flask |
| `app/routes/admin_routes.py` | flask |
| `app/routes/main_routes.py` | flask |
| `app/services/bg_remove.py` | (none; calls local module) |
| `app/services/birefnet_model.py` | torch, PIL, numpy, transformers |
| `app/services/birefnet_utils.py` | numpy, torch, torchvision, PIL, paddleocr*, paddlepaddle* |
| `app/services/usage_service.py` | flask, pymongo |
| `app/services/auth_service.py` | flask |
| `app/services/api_key_service.py` | (none; calls local module) |
| `app/utils/decorators.py` | flask |
| `app/utils/validators.py` | (none; stdlib only) |
| `app/utils/security.py` | bcrypt |

*\* Dynamic import wrapped in try/except*
