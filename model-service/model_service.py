from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import requests
from datetime import datetime

from dao.model_dao import ModelDAO
from dao.training_data_dao import TrainingDataDAO
from models.model import Model
from models.train_info import TrainInfo
from models.training_data import TrainingData
from config import Config

app = FastAPI(title="Model Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_dao = ModelDAO()
training_data_dao = TrainingDataDAO()


class ModelCreateRequest(BaseModel):
    model_name: str
    model_type: str = "FraudDetection"
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
    try:
        models = model_dao.get_all()
        return [ModelResponse(**model.to_dict()) for model in models]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models")
async def create_model(model_request: ModelCreateRequest):
    try:
        existing_model = model_dao.get_by_name_and_version(
            model_request.model_name,
            model_request.version
        )

        if existing_model:
            raise HTTPException(
                status_code=400,
                detail=f"Model with name '{model_request.model_name}' and version '{model_request.version}'"
            )

        # Tạo train info
        train_info = TrainInfo(
            epoch=model_request.epochs,
            learningRate=model_request.learning_rate,
            batchSize=model_request.batch_size,
            accuracy=model_request.accuracy,
            timeTrain=datetime.now()
        )

        # Tạo model
        model = Model(
            modelName=model_request.model_name,
            modelType=model_request.model_type,
            version=model_request.version,
            description=model_request.description,
            trainInfo=train_info
        )

        model_id = model_dao.create(model)

        # Tạo training data cho các templates
        for template_id in model_request.template_ids:
            training_data = TrainingData(
                modelId=model_id,
                fraudTemplateId=template_id,
                description=f"Training data for {model_request.model_name}"
            )
            training_data_dao.create(training_data)

        return {"success": True, "model_id": model_id, "message": "Model created successfully"}

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        if "Duplicate entry" in error_message and "UNIQUE_MODEL_NAME_VERSION" in error_message:
            raise HTTPException(
                status_code=400,
                detail=f"Model with name '{model_request.model_name}' and version '{model_request.version}' already exists. Please use a different name or version."
            )
        else:
            raise HTTPException(
                status_code=500, detail=f"Database error: {error_message}")


@app.get("/check-model-exists/{model_name}/{version}")
async def check_model_exists(model_name: str, version: str):
    try:
        existing_model = model_dao.get_by_name_and_version(model_name, version)
        return {
            "exists": existing_model is not None,
            "model_id": existing_model.idModel if existing_model else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model-types")
async def get_model_types():
    return {"model_types": ["HumanDetection", "FraudDetection"]}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "model-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
