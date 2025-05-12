# Cập nhật hàm main để phù hợp với tên đã import trong app.py
# Đổi tên hàm train_yolo_model -> train_model

import os
import json
import time
import logging
import subprocess
import traceback
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Cấu hình logging
# Sửa lỗi encoding trong Windows console
def _get_utf8_stream_handler():
    """Tạo một StreamHandler với encoding utf-8"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    return handler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("train_model.log", encoding='utf-8'),
        _get_utf8_stream_handler()
    ]
)
logger = logging.getLogger("train_model")

# Đổi tên hàm để phù hợp với import trong app.py
def train_model(model_id, model_name, template_ids, epochs=100):
    """
    Huấn luyện mô hình YOLOv8 đơn giản
    
    Args:
        model_id: ID của mô hình
        model_name: Tên mô hình
        template_ids: Danh sách ID template để huấn luyện
        epochs: Số epochs cần huấn luyện
    
    Returns:
        Dict: Kết quả quá trình huấn luyện
    """
    model_id = str(model_id)
    logger.info(f"Starting training for model {model_name} (ID: {model_id})")
    
    # Tạo thư mục cho model
    model_dir = os.path.join('models', model_id)
    os.makedirs(model_dir, exist_ok=True)
    
    # Tạo file trạng thái
    status_file = os.path.join(model_dir, 'status.json')
    status = {
        "status": "initializing",
        "model_id": model_id,
        "model_name": model_name,
        "current_epoch": 0,
        "total_epochs": epochs,
        "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "template_ids": template_ids
    }
    
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)
    
    try:
        # Chuẩn bị dữ liệu
        logger.info(f"Preparing data for model {model_id} with {len(template_ids)} templates")
        prepare_data_result = prepare_training_data(model_id, template_ids)
        if not prepare_data_result.get('success'):
            error_msg = prepare_data_result.get('message', 'Error preparing data')
            logger.error(f"Error preparing data: {error_msg}")
            
            # Cập nhật trạng thái
            status["status"] = "failed"
            status["error"] = error_msg
            status["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
                
            return {
                'success': False,
                'message': error_msg
            }
        
        # Cập nhật trạng thái
        status["status"] = "running"
        status["dataset_info"] = prepare_data_result.get('dataset_info', {})
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        
        # Lệnh huấn luyện YOLOv8
        dataset_path = prepare_data_result.get('dataset_path')
        logger.info(f"Starting training with dataset: {dataset_path}")
        
        yolo_cmd = [
            'yolo', 'task=detect', 'mode=train',
            f'model=yolov8n.pt',
            f'data={dataset_path}',
            f'epochs={epochs}',
            f'project=models/{model_id}',
            'name=train',
            'exist_ok=True'
        ]
        
        # Bắt đầu huấn luyện
        logger.info(f"Running command: {' '.join(yolo_cmd)}")
        process = subprocess.Popen(
            yolo_cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=True
        )
        
        # Lưu PID của process để có thể hủy sau này
        status["pid"] = process.pid
        status["command"] = " ".join(yolo_cmd)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Training process started with PID: {process.pid}")
        
        # Theo dõi quá trình huấn luyện
        for line in process.stdout:
            line = line.strip()
            logger.info(line)
            
            # Tìm thông tin epoch từ output
            if "Epoch" in line:
                try:
                    import re
                    epoch_match = re.search(r'Epoch\s+(\d+)/(\d+)', line)
                    if epoch_match:
                        current_epoch = int(epoch_match.group(1))
                        total_epochs = int(epoch_match.group(2))
                        
                        # Cập nhật trạng thái
                        status["current_epoch"] = current_epoch
                        status["total_epochs"] = total_epochs
                        status["status"] = "running"
                        
                        with open(status_file, 'w', encoding='utf-8') as f:
                            json.dump(status, f, indent=2)
                            
                        logger.info(f"Training progress: Epoch {current_epoch}/{total_epochs}")
                except Exception as e:
                    logger.error(f"Error processing output: {e}")
        
        # Đợi quá trình hoàn tất
        return_code = process.wait()
        logger.info(f"Training process finished with code: {return_code}")
        
        # Đọc stderr nếu có
        stderr_output = process.stderr.read() if process.stderr else None
        if stderr_output:
            logger.error(f"Stderr output: {stderr_output}")
        
        # Kiểm tra kết quả
        if return_code == 0:
            # Huấn luyện thành công
            status["status"] = "completed"
            status["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status["duration"] = (datetime.now() - datetime.strptime(status["start_time"], '%Y-%m-%d %H:%M:%S')).total_seconds()
            
            # Tìm file model
            best_model = find_model_file(model_id)
            if best_model:
                status["model_path"] = best_model
                logger.info(f"Found model at: {best_model}")
            else:
                logger.warning(f"No model file found after training")
            
            # Tìm metrics
            try:
                results_csv = os.path.join(model_dir, 'train', 'results.csv')
                if os.path.exists(results_csv):
                    import pandas as pd
                    df = pd.read_csv(results_csv)
                    if not df.empty:
                        last_row = df.iloc[-1].to_dict()
                        status["metrics"] = {
                            "precision": float(last_row.get('metrics/precision', 0)),
                            "recall": float(last_row.get('metrics/recall', 0)),
                            "mAP_50": float(last_row.get('metrics/mAP_0.5', 0)),
                            "box_loss": float(last_row.get('train/box_loss', 0))
                        }
                        logger.info(f"Final metrics: {status['metrics']}")
            except Exception as e:
                logger.error(f"Error reading metrics: {e}")
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
                
            logger.info(f"Training completed successfully for model {model_id}")
            return {
                'success': True,
                'message': 'Training successful',
                'model_path': best_model,
                'metrics': status.get('metrics', {})
            }
        else:
            # Huấn luyện thất bại
            error_msg = "Unknown error"
            
            if stderr_output:
                # Phân tích lỗi
                stderr_str = stderr_output if isinstance(stderr_output, str) else stderr_output.decode('utf-8', errors='ignore')
                
                # Lỗi thường gặp
                if "Error loading data from" in stderr_str and "val" in stderr_str:
                    error_msg = "Validation data error. No images found in validation folder."
                elif "AssertionError" in stderr_str:
                    # Tìm dòng AssertionError
                    for line in stderr_str.split('\n'):
                        if "AssertionError" in line:
                            error_msg = f"Assertion error: {line.strip()}"
                            break
                else:
                    # Lấy 3 dòng cuối cùng có thể là thông báo lỗi
                    error_lines = [line for line in stderr_str.split('\n') if line.strip()][-3:]
                    error_msg = '\n'.join(error_lines)
            
            # Cập nhật trạng thái
            status["status"] = "failed"
            status["error"] = error_msg
            status["error_code"] = return_code
            status["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
                
            logger.error(f"Training failed with code {return_code}: {error_msg}")
            return {
                'success': False,
                'message': f'Training failed: {error_msg}'
            }
    
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error during training: {e}")
        logger.error(tb)
        
        # Cập nhật trạng thái
        status["status"] = "failed"
        status["error"] = str(e)
        status["traceback"] = tb
        status["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
            
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }

def prepare_training_data(model_id, template_ids):
    """
    Chuẩn bị dữ liệu huấn luyện từ các template
    
    Args:
        model_id: ID của mô hình
        template_ids: Danh sách ID template
    
    Returns:
        Dict: Kết quả chuẩn bị dữ liệu
    """
    try:
        # Import DAO khi cần
        from dao.fraud_template_dao import FraudTemplateDAO
        from dao.fraud_label_dao import FraudLabelDAO
        
        fraud_template_dao = FraudTemplateDAO()
        fraud_label_dao = FraudLabelDAO()
        
        # Tạo thư mục dataset
        dataset_dir = os.path.join('models', model_id, 'dataset')
        train_dir = os.path.join(dataset_dir, 'train')
        val_dir = os.path.join(dataset_dir, 'val')
        
        # Tạo thư mục
        for dir_path in [train_dir, val_dir]:
            os.makedirs(os.path.join(dir_path, 'images'), exist_ok=True)
            os.makedirs(os.path.join(dir_path, 'labels'), exist_ok=True)
        
        processed_images = []
        class_counts = {}  # Đếm số lượng mỗi class
        
        # Xử lý từng template
        for template_id in template_ids:
            template = fraud_template_dao.get_by_id(int(template_id))
            if not template:
                logger.warning(f"Template ID not found: {template_id}")
                continue
            
            # Lấy đường dẫn ảnh
            image_path = template.imageUrl
            if image_path.startswith('/'):
                image_path = image_path[1:]
            
            # Chuẩn hóa đường dẫn
            if not os.path.exists(image_path) and image_path.startswith('static/'):
                image_path = os.path.join(os.getcwd(), image_path)
            
            if not os.path.exists(image_path):
                # Thử tìm với đường dẫn tương đối
                alt_path = os.path.join(os.getcwd(), image_path.lstrip('/'))
                if os.path.exists(alt_path):
                    image_path = alt_path
                else:
                    logger.warning(f"Image not found: {image_path}")
                    continue
            
            # Tạo tên file ảnh
            img_filename = f"img_{template_id}_{os.path.basename(image_path)}"
            
            # Copy ảnh sang thư mục train
            train_img_path = os.path.join(train_dir, 'images', img_filename)
            shutil.copy2(image_path, train_img_path)
            
            # Tạo file label cho train
            train_label_path = os.path.join(train_dir, 'labels', f"{os.path.splitext(img_filename)[0]}.txt")
            
            boxes_in_image = []
            with open(train_label_path, 'w') as f:
                if template.boundingBox and len(template.boundingBox) > 0:
                    for box in template.boundingBox:
                        # Lấy class id từ label
                        label = fraud_label_dao.get_by_id(box.fraudLabelId)
                        class_id = 0  # Default class
                        
                        if label and label.typeLabel:
                            type_label = label.typeLabel
                            if isinstance(type_label, str):
                                if type_label == "HumanDetect":
                                    class_id = 0
                                elif type_label == "literal":
                                    class_id = 1
                        
                        # Cập nhật đếm số lượng class
                        class_counts[class_id] = class_counts.get(class_id, 0) + 1
                        
                        # Lưu thông tin box
                        boxes_in_image.append({
                            'class_id': class_id,
                            'x': box.xCenter,
                            'y': box.yCenter,
                            'w': box.width,
                            'h': box.height
                        })
                        
                        # Viết dòng trong file label
                        f.write(f"{class_id} {box.xCenter} {box.yCenter} {box.width} {box.height}\n")
            
            # Thêm vào danh sách ảnh đã xử lý
            processed_images.append({
                'filename': img_filename,
                'boxes': boxes_in_image
            })
        
        if not processed_images:
            return {
                'success': False,
                'message': 'No images processed'
            }
        
        # QUAN TRỌNG: Copy một số ảnh sang thư mục validation
        # YOLOv8 yêu cầu phải có dữ liệu validation
        
        # Chọn số lượng validation: ít nhất 1 ảnh, hoặc 1/3 tổng số
        val_count = max(1, len(processed_images) // 3)
        logger.info(f"Selecting {val_count} images for validation from total {len(processed_images)} images")
        
        # Chọn ngẫu nhiên một số ảnh để làm validation
        val_indices = random.sample(range(len(processed_images)), min(val_count, len(processed_images)))
        val_images = [processed_images[i] for i in val_indices]
        
        # Copy các ảnh này sang thư mục validation
        for img_info in val_images:
            img_name = img_info['filename']
            
            # Copy ảnh
            train_img = os.path.join(train_dir, 'images', img_name)
            val_img = os.path.join(val_dir, 'images', img_name)
            shutil.copy2(train_img, val_img)
            
            # Copy label
            train_label = os.path.join(train_dir, 'labels', f"{os.path.splitext(img_name)[0]}.txt")
            val_label = os.path.join(val_dir, 'labels', f"{os.path.splitext(img_name)[0]}.txt")
            shutil.copy2(train_label, val_label)
        
        logger.info(f"Processed {len(processed_images)} images for training and {len(val_images)} for validation")
        
        # Tạo file dataset.yaml
        class_names = ["Human", "Object"]  # Mặc định
        yaml_content = f"""
# YOLOv8 dataset config
path: {os.path.abspath(dataset_dir)}
train: train/images
val: val/images

# Classes
names:
  0: {class_names[0]}
  1: {class_names[1]}
"""
        
        dataset_yaml = os.path.join(dataset_dir, 'dataset.yaml')
        with open(dataset_yaml, 'w') as f:
            f.write(yaml_content)
        
        # Thông tin về dataset để hiển thị
        dataset_info = {
            'total_images': len(processed_images),
            'train_images': len(processed_images),
            'val_images': len(val_images),
            'class_counts': class_counts
        }
        
        return {
            'success': True,
            'message': f'Processed {len(processed_images)} images, including {len(val_images)} for validation',
            'dataset_path': dataset_yaml,
            'dataset_info': dataset_info
        }
    
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error preparing data: {e}")
        logger.error(tb)
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'traceback': tb
        }

def find_model_file(model_id):
    """
    Tìm file model sau khi huấn luyện
    
    Args:
        model_id: ID của mô hình
    
    Returns:
        str: Đường dẫn đến file model (hoặc None nếu không tìm thấy)
    """
    # Các đường dẫn có thể có
    paths = [
        os.path.join('models', model_id, 'train', 'weights', 'best.pt'),
        os.path.join('models', model_id, 'train', 'weights', 'last.pt'),
        os.path.join('models', model_id, 'train', 'best.pt'),
        os.path.join('models', model_id, 'train', 'last.pt')
    ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None

def get_training_status(model_id):
    """
    Lấy trạng thái huấn luyện hiện tại
    
    Args:
        model_id: ID của mô hình
    
    Returns:
        Dict: Trạng thái huấn luyện
    """
    model_id = str(model_id)
    status_file = os.path.join('models', model_id, 'status.json')
    
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading status file: {e}")
    
    return {
        'status': 'not_found',
        'message': 'Training information not found'
    }

def cancel_training(model_id):
    """
    Hủy quá trình huấn luyện đang chạy
    
    Args:
        model_id: ID của mô hình cần hủy
    
    Returns:
        bool: True nếu hủy thành công, False nếu không
    """
    model_id = str(model_id)
    logger.info(f"Attempting to cancel training for model ID: {model_id}")
    
    # Đọc thông tin trạng thái
    status_file = os.path.join('models', model_id, 'status.json')
    if not os.path.exists(status_file):
        logger.error(f"Status file not found: {status_file}")
        return False
    
    try:
        # Đọc trạng thái hiện tại
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
        
        # Kiểm tra xem có PID không
        if 'pid' not in status:
            logger.error("PID information not found in status file")
            return False
        
        process_pid = status['pid']
        logger.info(f"Found PID: {process_pid}, attempting to terminate process")
        
        # Thử kết thúc process theo PID
        try:
            # Thử sử dụng module psutil nếu có
            try:
                import psutil
                if psutil.pid_exists(process_pid):
                    process = psutil.Process(process_pid)
                    logger.info(f"Found process with PID {process_pid}, terminating...")
                    
                    # Kết thúc process và cả các process con nếu có
                    for child in process.children(recursive=True):
                        child.terminate()
                    process.terminate()
                    
                    # Đợi tối đa 5 giây
                    killed = False
                    for _ in range(5):
                        if not psutil.pid_exists(process_pid):
                            killed = True
                            break
                        time.sleep(1)
                    
                    # Nếu vẫn chưa kết thúc, kill cưỡng bức
                    if not killed and psutil.pid_exists(process_pid):
                        logger.info(f"Process still active after 5 seconds, killing...")
                        for child in process.children(recursive=True):
                            try:
                                child.kill()
                            except:
                                pass
                        process.kill()
                    
                    logger.info(f"Terminated process with PID {process_pid}")
                else:
                    logger.warning(f"Process with PID {process_pid} not found")
                    return False
            except ImportError:
                # Nếu không có psutil, sử dụng phương pháp thông thường
                import platform
                import subprocess
                
                if platform.system() == "Windows":
                    logger.info(f"Using taskkill for PID {process_pid}")
                    subprocess.run(f'taskkill /F /PID {process_pid}', shell=True)
                    subprocess.run(f'taskkill /F /T /PID {process_pid}', shell=True)  # Kill tree
                else:
                    logger.info(f"Using kill for PID {process_pid}")
                    # Trong Linux, kill cả process group
                    subprocess.run(f'pkill -9 -P {process_pid}', shell=True)  # Kill children
                    subprocess.run(f'kill -9 {process_pid}', shell=True)  # Kill parent
        except Exception as e:
            logger.error(f"Error terminating process: {e}")
            return False
        
        # Cập nhật trạng thái
        status['status'] = 'cancelled'
        status['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Successfully cancelled training for model ID: {model_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error cancelling training: {e}")
        logger.error(traceback.format_exc())
        return False

# THÊM: Đổi tên để giống tên đã import trong app.py
train_yolo_model = train_model

# Hàm để sử dụng tương tác
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python train_model.py <model_id> <model_name> <template_id1,template_id2,...> [epochs]")
        sys.exit(1)
    
    model_id = sys.argv[1]
    model_name = sys.argv[2]
    template_ids = [int(tid) for tid in sys.argv[3].split(',')]
    epochs = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    
    result = train_model(model_id, model_name, template_ids, epochs)
    print(json.dumps(result, indent=2))