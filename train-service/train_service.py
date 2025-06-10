from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import threading
import requests

from train_model import (train_yolo_model, get_training_status, cancel_training,
                         delete_training_folder, cleanup_failed_training)
from config import Config

app = FastAPI(title="Train Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TrainRequest(BaseModel):
    model_name: str
    model_type: str = "FraudDetection"
    version: str = "v1.0.0"
    template_ids: List[int]
    epochs: int = 100
    batch_size: int = 16
    image_size: int = 640
    learning_rate: float = 0.001


class TrainResponse(BaseModel):
    success: bool
    model_id: Optional[str] = None
    message: str


class StatusResponse(BaseModel):
    status: str
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    current_epoch: int = 0
    total_epochs: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None
    final_metrics: Optional[Dict[str, Any]] = None
    dataset_info: Optional[Dict[str, Any]] = None


class DeleteResponse(BaseModel):
    success: bool
    message: str


def run_training_async(model_id, model_name, model_type, version, template_ids,
                       epochs, batch_size, image_size, learning_rate):
    try:
        result = train_yolo_model(
            model_id, model_name, model_type, version,
            epochs, batch_size, image_size, learning_rate, template_ids
        )
    except Exception as e:
        print(e)


@app.post("/train", response_model=TrainResponse)
async def start_training(train_request: TrainRequest):
    try:
        if not train_request.model_name or not train_request.template_ids:
            raise HTTPException(
                status_code=400, detail="Missing required information")

        model_id = hash(
            f"{train_request.model_name}_{train_request.version}") % 10000 + 1000

        model_id = str(model_id)

        training_thread = threading.Thread(
            target=run_training_async,
            args=(model_id, train_request.model_name, train_request.model_type,
                  train_request.version, train_request.template_ids,
                  train_request.epochs, train_request.batch_size,
                  train_request.image_size, train_request.learning_rate)
        )
        training_thread.daemon = True
        training_thread.start()

        return TrainResponse(
            success=True,
            model_id=model_id,
            message="Training started successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{model_id}", response_model=StatusResponse)
async def get_training_status_api(model_id: str):
    try:
        status = get_training_status(model_id)

        return StatusResponse(
            status=status.get('status', 'unknown'),
            model_id=status.get('model_id'),
            model_name=status.get('model_name'),
            current_epoch=status.get('current_epoch', 0),
            total_epochs=status.get('total_epochs', 0),
            start_time=status.get('start_time'),
            end_time=status.get('end_time'),
            error=status.get('error'),
            final_metrics=status.get('final_metrics'),
            dataset_info=status.get('dataset_info')
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cancel/{model_id}")
async def cancel_training_api(model_id: str):
    try:
        success = cancel_training(model_id)

        if success:
            return {"success": True, "message": "Training cancelled"}
        else:
            return {"success": False, "message": "Could not cancel training"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete-training/{model_id}", response_model=DeleteResponse)
async def delete_training_folder_api(model_id: str):
    try:
        success = delete_training_folder(model_id)

        if success:
            return DeleteResponse(
                success=True,
                message=f"Training folder deleted successfully"
            )
        else:
            return DeleteResponse(
                success=False,
                message=f"Training folder not found"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e))


@app.post("/cleanup/{model_id}")
async def cleanup_failed_training_api(model_id: str):
    try:
        success = cleanup_failed_training(model_id)

        if success:
            return {"success": True, "message": f"Cleaned up failed training"}
        else:
            return {"success": False, "message": f"No cleanup"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "train-service"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
