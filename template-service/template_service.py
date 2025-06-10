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

IMAGES_DIR = "images"

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

template_dao = FraudTemplateDAO()


class TemplateResponse(BaseModel):
    idTemplate: int
    description: Optional[str]
    imageUrl: str
    timeUpdate: str
    labels: List[dict] = []
    boundingBox: List[dict] = []


# @app.get("/images/{filename}")
# async def get_image(filename: str):
#     try:
#         file_path = os.path.join(IMAGES_DIR, filename)

#         if not os.path.exists(file_path):
#             # Return placeholder image thay vì 404
#             placeholder_path = os.path.join(IMAGES_DIR, "placeholder.jpg")
#             if os.path.exists(placeholder_path):
#                 return FileResponse(placeholder_path)
#             else:
#                 raise HTTPException(status_code=404, detail="Image not found")

#         return FileResponse(file_path)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "template-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
