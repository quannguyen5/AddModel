from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

# Import existing DAOs
from dao.model_dao import ModelDAO
from dao.train_info_dao import TrainInfoDAO
from dao.fraud_template_dao import FraudTemplateDAO
from dao.training_data_dao import TrainingDataDAO
from models.model import Model
from models.train_info import TrainInfo
from models.training_data import TrainingData
from utils.enums import ModelType

app = FastAPI(title="Model Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DAOs
model_dao = ModelDAO()
train_info_dao = TrainInfoDAO()
fraud_template_dao = FraudTemplateDAO()
training_data_dao = TrainingDataDAO()

# Pydantic models


class ModelCreateRequest(BaseModel):
    model_name: str
    model_type: str
    version: str
    description: Optional[str] = ""
    template_ids: List[int]
    epochs: int = 100
    batch_size: int = 16
    learning_rate: float = 0.001
    accuracy: float = 0.85


class ModelResponse(BaseModel):
    idModel: int
    modelName: str
    modelType: str
    version: str
    description: Optional[str]
    lastUpdate: str
    accuracy: float


class TemplateResponse(BaseModel):
    idTemplate: int
    description: Optional[str]
    imageUrl: str
    timeUpdate: str
    labels: List[dict] = []
    boundingBox: List[dict] = []


@app.get("/")
async def root():
    return {"message": "Model Service is running"}


@app.get("/models", response_model=List[ModelResponse])
async def get_all_models():
    """Lấy danh sách tất cả models"""
    try:
        models = model_dao.get_all()
        model_list = []
        for model in models:
            model_dict = model.to_dict()
            model_response = ModelResponse(
                idModel=model_dict["idModel"],
                modelName=model_dict["modelName"],
                modelType=model_dict["modelType"],
                version=model_dict["version"],
                description=model_dict.get("description", ""),
                lastUpdate=model_dict["lastUpdate"],
                accuracy=model_dict.get("accuracy", 0.0)
            )
            model_list.append(model_response)
        return model_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_id}")
async def get_model(model_id: int):
    """Lấy thông tin chi tiết một model"""
    try:
        model = model_dao.get_by_id(model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models")
async def create_model(model_request: ModelCreateRequest):
    """Tạo model mới"""
    try:
        # Kiểm tra model đã tồn tại
        existing_models = model_dao.get_all()
        for existing_model in existing_models:
            if (existing_model.modelName == model_request.model_name and
                    existing_model.version == model_request.version):
                raise HTTPException(
                    status_code=400,
                    detail=f"Model {model_request.model_name} version {model_request.version} already exists"
                )

        # Tạo TrainInfo
        train_info = TrainInfo(
            epoch=model_request.epochs,
            learningRate=model_request.learning_rate,
            batchSize=model_request.batch_size,
            accuracy=model_request.accuracy,
            timeTrain=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        train_info_id = train_info_dao.create(train_info)
        train_info.idInfo = train_info_id

        # Tạo Model
        model = Model(
            modelName=model_request.model_name,
            modelType=model_request.model_type,
            version=model_request.version,
            description=model_request.description,
            lastUpdate=datetime.now()
        )
        model.trainInfo = train_info
        model_id = model_dao.create(model)

        # Tạo TrainingData cho các templates
        for template_id in model_request.template_ids:
            template = fraud_template_dao.get_by_id(template_id)
            if template:
                training_data = TrainingData(
                    modelId=model_id,
                    fraudTemplateId=template.idTemplate,
                    description=f"Training data for {model_request.model_name}",
                    timeUpdate=datetime.now()
                )
                training_data_dao.create(training_data)

        return {"success": True, "model_id": model_id, "message": "Model created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/models/{model_id}")
async def delete_model(model_id: int):
    """Xóa model"""
    try:
        success = model_dao.delete(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="Model not found")
        return {"success": True, "message": "Model deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/templates", response_model=List[TemplateResponse])
async def get_all_templates():
    """Lấy danh sách tất cả fraud templates"""
    try:
        templates = fraud_template_dao.get_all()
        template_list = []
        for template in templates:
            template_dict = template.to_dict()
            template_response = TemplateResponse(
                idTemplate=template_dict["idTemplate"],
                description=template_dict.get("description", ""),
                imageUrl=template_dict["imageUrl"],
                timeUpdate=template_dict["timeUpdate"],
                labels=template_dict.get("labels", []),
                boundingBox=template_dict.get("boundingBox", [])
            )
            template_list.append(template_response)
        return template_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model-types")
async def get_model_types():
    """Lấy danh sách các loại model"""
    return {"model_types": ModelType.get_all_values()}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "model-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
