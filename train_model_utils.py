# train_model_utils.py
import os
import time
import json
import threading
from datetime import datetime
from simple_trainer import trainer  # Sử dụng simple trainer

# File lưu trữ trạng thái
TRAINING_STATES_FILE = "training_states.json"

# Khởi tạo trạng thái
training_states = {}

def load_training_states():
    """Load training states from file"""
    if os.path.exists(TRAINING_STATES_FILE):
        try:
            with open(TRAINING_STATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading training states: {e}")
            return {}
    return {}

def save_training_states(states):
    """Save training states to file"""
    try:
        with open(TRAINING_STATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(states, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving training states: {e}")

# Load states from file if exists
training_states = load_training_states()

def get_training_status(model_id):
    """Get training status for a model"""
    model_id = str(model_id)
    
    # Đọc trạng thái từ file
    status_file = os.path.join('models', model_id, 'status.json')
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            
            # Cập nhật status vào file lưu trữ chung
            training_states[model_id] = status
            save_training_states(training_states)
            
            return status
        except Exception as e:
            print(f"Error loading status file: {e}")
    
    # Nếu không có file, kiểm tra trong memory
    if model_id in training_states:
        return training_states[model_id]
    
    return {'status': 'not_found'}

def train_yolo_model(model_id, model_name, model_type, version, epochs, batch_size, image_size, learning_rate, template_ids):
    """Bắt đầu huấn luyện mô hình trên máy local sử dụng script riêng biệt"""
    model_id = str(model_id)
    print(f"Starting training for model ID: {model_id}, name: {model_name}")
    
    # Import DAOs for data preparation
    from dao.fraud_template_dao import FraudTemplateDAO
    from dao.fraud_label_dao import FraudLabelDAO
    from dao.bounding_box_dao import BoundingBoxDAO
    
    fraud_template_dao = FraudTemplateDAO()
    fraud_label_dao = FraudLabelDAO()
    bounding_box_dao = BoundingBoxDAO()
    
    # Collect images and labels
    template_images = []
    template_labels = []
    
    for template_id in template_ids:
        # Get template from database
        template = fraud_template_dao.get_by_id(int(template_id))
        
        if not template:
            print(f"Template ID not found: {template_id}")
            continue
        
        # Get image path
        image_path = template.imageUrl
        if image_path.startswith('/'):
            image_path = image_path[1:]  # Remove leading slash if present
            
        # Kiểm tra và chuyển đổi đường dẫn ảnh
        if image_path.startswith('static/'):
            image_path = os.path.join(os.getcwd(), image_path)
        
        # Debug log
        print(f"Processing image: {image_path}")
        
        # Check if image file exists
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            print(f"Trying alternative path...")
            
            # Thử tìm với đường dẫn tương đối
            alt_path = os.path.join(os.getcwd(), image_path.lstrip('/'))
            if os.path.exists(alt_path):
                print(f"Found at alternative path: {alt_path}")
                image_path = alt_path
            else:
                print(f"Alternative path not found either: {alt_path}")
                continue
        
        # Get bounding boxes for this template
        boxes = []
        if template.boundingBox and len(template.boundingBox) > 0:
            for box in template.boundingBox:
                # Get class id from label
                label = fraud_label_dao.get_by_id(box.fraudLabelId)
                class_id = 0  # Default class
                
                if label and label.typeLabel:
                    type_label = label.typeLabel
                    if isinstance(type_label, str):
                        if type_label == "HumanDetect":
                            class_id = 0
                        elif type_label == "literal":
                            class_id = 1
                
                boxes.append({
                    'class_id': class_id,
                    'x_center': box.xCenter,
                    'y_center': box.yCenter,
                    'width': box.width,
                    'height': box.height
                })
        
        # Add to lists
        template_images.append(image_path)
        template_labels.append(boxes)
    
    # Check if we have any valid images
    if not template_images:
        print("No valid images found for training!")
        return {
            'success': False, 
            'message': 'Không tìm thấy ảnh hợp lệ cho việc huấn luyện'
        }
    
    print(f"Starting training with {len(template_images)} images")
    
    # Chuẩn bị thông số
    model_dir = os.path.join('models', model_id)
    os.makedirs(model_dir, exist_ok=True)
    
    # Lưu labels vào file
    labels_file = os.path.join(model_dir, 'labels.json')
    with open(labels_file, 'w', encoding='utf-8') as f:
        json.dump(template_labels, f, indent=2, ensure_ascii=False)
    
    # Chuẩn bị trạng thái ban đầu
    status_file = os.path.join(model_dir, 'status.json')
    initial_status = {
        "status": "initializing",
        "progress": 0,
        "model_name": model_name,
        "model_type": model_type,
        "version": version,
        "current_epoch": 0,
        "total_epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "metrics": {},
        "epoch_metrics": {},
        "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "template_ids": template_ids
    }
    
    # Lưu trạng thái
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(initial_status, f, indent=2, ensure_ascii=False)
    
    # Cập nhật trạng thái lưu trữ
    training_states[model_id] = initial_status
    save_training_states(training_states)
    
    # Chuẩn bị danh sách ảnh cho command line
    images_param = ';'.join(template_images)
    
    # Chạy script huấn luyện
    cmd = f'python train_yolo.py --model_id={model_id} --model_name="{model_name}" --model_type="{model_type}" --version="{version}" --epochs={epochs} --batch_size={batch_size} --learning_rate={learning_rate} --image_size={image_size} --images="{images_param}" --labels="{labels_file}"'
    
    print(f"Starting training process with command: {cmd}")
    
    # Bắt đầu quá trình huấn luyện trong process riêng biệt
    import subprocess
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    
    return {
        "success": True,
        "message": "Đã bắt đầu huấn luyện trên máy local",
        "model_id": model_id
    }

def cancel_training(model_id):
    """Cancel a running training job"""
    model_id = str(model_id)
    print(f"Cancelling training for model ID: {model_id}")
    
    # Tìm và kết thúc process Python đang chạy script train_yolo.py với model_id này
    import subprocess
    import platform
    
    success = False
    
    try:
        if platform.system() == "Windows":
            # Tìm PID của process đang chạy
            cmd = f'wmic process where "commandline like \'%train_yolo.py%--model_id={model_id}%\'" get processid'
            result = subprocess.check_output(cmd, shell=True, text=True)
            
            # Lấy PID từ output
            lines = result.strip().split('\n')
            if len(lines) > 1:
                pid = lines[1].strip()
                if pid:
                    # Kết thúc process
                    subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                    success = True
        else:
            # Linux/Mac
            cmd = f"pkill -f 'train_yolo.py.*--model_id={model_id}'"
            subprocess.run(cmd, shell=True)
            success = True
    except Exception as e:
        print(f"Error cancelling training: {e}")
    
    # Cập nhật trạng thái
    if model_id in training_states:
        training_states[model_id]['status'] = 'cancelled'
        save_training_states(training_states)
    
    # Cập nhật file trạng thái
    status_file = os.path.join('models', model_id, 'status.json')
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            
            status['status'] = 'cancelled'
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error updating status file: {e}")
    
    return success

def download_trained_model(model_id, output_dir='models'):
    """Get trained model from output directory"""
    model_id = str(model_id)
    print(f"Getting model {model_id}")
    
    model_dir = os.path.join(output_dir, model_id)
    train_dir = os.path.join(model_dir, 'train')
    weights_dir = os.path.join(train_dir, 'weights')
    
    if not os.path.exists(weights_dir):
        return {'success': False, 'message': 'Model weights directory not found'}
    
    # Check for model files (best.pt or last.pt)
    best_model = os.path.join(weights_dir, 'best.pt')
    last_model = os.path.join(weights_dir, 'last.pt')
    
    model_path = None
    if os.path.exists(best_model):
        model_path = best_model
    elif os.path.exists(last_model):
        model_path = last_model
    
    if not model_path:
        return {'success': False, 'message': 'Model file not found'}
    
    # Update model path in state
    if model_id in training_states:
        training_states[model_id]['model_path'] = model_path
        save_training_states(training_states)
    
    return {
        'success': True,
        'message': 'Model found',
        'model_path': model_path
    }

def cleanup_training_data(model_id, keep_model=True):
    """Clean up training data after completion"""
    model_id = str(model_id)
    
    # Cleanup in trainer
    trainer.cleanup_training_data(model_id, keep_model)
    
    if not keep_model and model_id in training_states:
        del training_states[model_id]
        save_training_states(training_states)
    
    return True