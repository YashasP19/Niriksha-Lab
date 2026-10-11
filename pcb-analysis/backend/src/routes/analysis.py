from fastapi import APIRouter, UploadFile, File, HTTPException

from ..analyzer import analyze_test_image, save_template, template_exists, load_template
from ..image_utils import image_to_base64

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/template")
async def upload_template(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    save_template(image_bytes)
    return {"status": "ok", "message": "Template uploaded successfully"}


@router.get("/template")
async def get_template_status():
    if not template_exists():
        return {"exists": False, "image": None}

    template_bytes = load_template()
    return {"exists": True, "image": image_to_base64(template_bytes)}


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    if not template_exists():
        raise HTTPException(status_code=400, detail="No template uploaded. Upload a template first.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = await analyze_test_image(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result.model_dump()
