from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import shutil

from dao.fraud_template_dao import FraudTemplateDAO

app = FastAPI(title="Template Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chỉ dùng thư mục images
IMAGES_DIR = "images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)
    print(f"Created directory: {IMAGES_DIR}")

# Mount images folder
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# DAO
template_dao = FraudTemplateDAO()


class TemplateResponse(BaseModel):
    idTemplate: int
    description: Optional[str]
    imageUrl: str
    timeUpdate: str
    labels: List[dict] = []
    boundingBox: List[dict] = []


@app.get("/")
async def root():
    return {"message": "Template Service is running"}


@app.get("/templates", response_model=List[TemplateResponse])
async def get_all_templates():
    try:
        templates = template_dao.get_all()
        return [TemplateResponse(**template.to_dict()) for template in templates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates/{template_id}")
async def get_template(template_id: int):
    try:
        template = template_dao.get_by_id(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload ảnh mới vào images folder"""
    try:
        # Kiểm tra file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, detail="File must be an image")

        # Lưu file vào images folder
        file_path = os.path.join(IMAGES_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return URL
        image_url = f"/images/{file.filename}"
        return {"success": True, "imageUrl": image_url, "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/templates/{template_id}")
async def delete_template(template_id: int):
    try:
        success = template_dao.delete(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"success": True, "message": "Template deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/list-images")
async def list_images():
    """List tất cả images trong folder images"""
    try:
        images = []

        for filename in os.listdir(IMAGES_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                images.append({
                    "filename": filename,
                    "url": f"/images/{filename}"
                })

        return {"images": images, "count": len(images)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "template-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
