# Using your train_model.py instead
import os
import time
import json
from train_model import train_yolo_model

def run_test_with_app_code():
    # Create a unique model ID
    model_id = 100  # Or use an available ID in your system
    model_name = "Test_Model"
    model_type = "Human Detection"
    version = "v1.0.0"
    
    # Template IDs to use
    template_ids = [1, 2, 3]
    
    # Training parameters
    epochs = 5  # Smaller number for testing
    batch_size = 8
    image_size = 320
    learning_rate = 0.001
    
    print(f"Starting training with template IDs: {template_ids}")
    
    # Call your training function
    result = train_yolo_model(
        model_id, 
        model_name, 
        model_type, 
        version, 
        epochs, 
        batch_size, 
        image_size, 
        learning_rate, 
        template_ids
    )
    
    # Print result
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_test_with_app_code()