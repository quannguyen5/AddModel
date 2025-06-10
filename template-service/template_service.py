from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os

from dao.fraud_template_dao import FraudTemplateDAO

app = FastAPI(title="Template Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = "static"
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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


@app.get("/images/{filename}")
async def get_image(filename: str):
    try:
        # Tìm file trong static directory
        file_path = os.path.join(STATIC_DIR, filename)

        if os.path.exists(file_path):
            return FileResponse(file_path)

        # Placeholder nếu không tìm thấy
        return {"error": "Image not found"}
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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "template-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
