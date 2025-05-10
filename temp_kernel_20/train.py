
# YOLO Training Script with Progress Tracking
import os
import json
import time
import traceback
from ultralytics import YOLO

# Initialize model
model = YOLO('yolov8n.pt')  # Load pretrained model

# Training configuration
config = {"model_name": "M\u00f4 h\u00ecnh 2p2", "model_type": "Human Detection", "version": "v1.0.13", "epochs": 100, "batch_size": 16, "image_size": 640, "learning_rate": 0.001}

# Dataset path
dataset_path = "../input/yolo-fraud-detection-20-1746894200/dataset.yaml"

print(f"Starting training with dataset: {dataset_path}")
print(f"Configuration: {config}")

# Create progress tracking file
progress_data = {
    "status": "training",
    "total_epochs": config['epochs'],
    "current_epoch": 0,
    "metrics": {},
    "epoch_metrics": {},
    "start_time": time.time()
}

# Save initial progress
with open('progress.json', 'w') as f:
    json.dump(progress_data, f, indent=2)

# Custom callback to track progress
def on_train_epoch_end(trainer):
    progress_data["current_epoch"] = trainer.epoch + 1
    progress_data["metrics"] = {
        "mAP50(B)": trainer.metrics.get('metrics/mAP50(B)', 0),
        "precision(B)": trainer.metrics.get('metrics/precision(B)', 0),
        "recall(B)": trainer.metrics.get('metrics/recall(B)', 0),
        "loss": float(trainer.loss) if hasattr(trainer, 'loss') else 0
    }
    progress_data["epoch_metrics"][f"epoch_{trainer.epoch + 1}"] = progress_data["metrics"].copy()
    progress_data["progress"] = ((trainer.epoch + 1) / config['epochs']) * 100
    
    # Save progress data
    with open('progress.json', 'w') as f:
        json.dump(progress_data, f, indent=2)
    
    # Also save current model at each epoch
    if (trainer.epoch + 1) % 5 == 0 or (trainer.epoch + 1) == config['epochs']:
        os.makedirs('output', exist_ok=True)
        trainer.model.export(f"output/model_epoch_{trainer.epoch + 1}.onnx")

# Start training
try:
    results = model.train(
        data=dataset_path,
        epochs=config['epochs'],
        batch=config['batch_size'],
        imgsz=config['image_size'],
        patience=50,
        device=0,  # Use GPU
        callbacks=[on_train_epoch_end]  # Register progress tracking callback
    )

    # Update final progress
    progress_data["status"] = "completed"
    progress_data["current_epoch"] = config['epochs'] 
    progress_data["end_time"] = time.time()
    progress_data["duration"] = progress_data["end_time"] - progress_data["start_time"]

    # Save final metrics
    final_metrics = {}
    try:
        for k, v in results.results_dict.items():
            if isinstance(v, (int, float)):
                final_metrics[k] = v
        progress_data["metrics"] = final_metrics
        progress_data["accuracy"] = final_metrics.get('metrics/mAP50(B)', 0)
    except Exception as e:
        print(f"Error saving final metrics: {e}")

    # Save final progress
    with open('progress.json', 'w') as f:
        json.dump(progress_data, f, indent=2)

    # Save metrics in separate file too for compatibility
    with open('metrics.json', 'w') as f:
        json.dump(final_metrics, f, indent=2)

    # Export model in multiple formats
    os.makedirs('output', exist_ok=True)
    model.export(format='onnx', imgsz=config['image_size'])
    model.export(format='pytorch', imgsz=config['image_size'])

    print("Training completed!")
except Exception as e:
    # Log error and save to progress file
    error_msg = str(e)
    traceback_str = traceback.format_exc()
    print(f"Training error: {error_msg}")
    print(traceback_str)
    
    progress_data["status"] = "failed"
    progress_data["error"] = error_msg
    progress_data["traceback"] = traceback_str
    
    with open('progress.json', 'w') as f:
        json.dump(progress_data, f, indent=2)
