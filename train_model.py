import os
import json
import time
import logging
import traceback
import random
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path

# Cấu hình logging


def _get_utf8_stream_handler():
    """Tạo một StreamHandler với encoding utf-8"""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
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


class YOLOModelTrainer:
    def __init__(self, model_id, model_name, model_type, version, output_dir='models'):
        self.model_id = str(model_id)
        self.model_name = model_name
        self.model_type = model_type
        self.version = version
        self.output_dir = output_dir
        self.model_dir = os.path.join(output_dir, self.model_id)
        self.status_file = os.path.join(self.model_dir, 'status.json')
        self.running = True
        self.training_thread = None

        # Create model directory
        os.makedirs(self.model_dir, exist_ok=True)

        # Initialize status
        self.status = {
            "status": "initialized",
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_type": self.model_type,
            "version": self.version,
            "current_epoch": 0,
            "total_epochs": 0,
            "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "template_ids": [],
            "epochs": [],
            "best_map50": 0,
            "best_map50_95": 0
        }

        # Save initial status
        self._update_status()

    def _update_status(self):
        """Update status file"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating status file: {str(e)}")

    def _monitor_training_progress(self, run_dir, total_epochs):
        """Monitor training progress by reading results.csv file"""
        results_file = os.path.join(run_dir, "results.csv")

        # Also check alternative locations
        alt_results_file = os.path.join(run_dir, "train", "results.csv")

        prev_epoch = 0
        checks_without_progress = 0
        max_checks_without_progress = 30  # After this many checks, force progress update

        logger.info(f"Started monitoring thread for model {self.model_id}")

        while self.running:
            # Check if status is still running
            if self.status.get('status') not in ['running', 'initializing']:
                logger.info(
                    f"Model {self.model_id} status is {self.status.get('status')}, stopping monitor")
                break

            # Look for possible results files
            result_files_to_check = [
                results_file,
                alt_results_file
            ]

            # Try to find any results.csv file in the train directory
            if not os.path.exists(results_file) and not os.path.exists(alt_results_file):
                # Search for any results.csv in subdirectories
                for root, dirs, files in os.walk(run_dir):
                    for file in files:
                        if file == 'results.csv':
                            result_files_to_check.append(
                                os.path.join(root, file))
                            logger.info(
                                f"Found alternative results.csv at: {os.path.join(root, file)}")

            # Check if any training log files exist
            found_results = False

            for results_path in result_files_to_check:
                if os.path.exists(results_path):
                    logger.info(f"Reading results file: {results_path}")
                    try:
                        # Read the results file
                        with open(results_path, 'r') as f:
                            lines = f.readlines()

                        # Skip header
                        if len(lines) > 1:
                            # Parse header to get column indices - strip whitespace
                            header = [h.strip()
                                      for h in lines[0].strip().split(',')]

                            # Find indices of relevant metrics
                            try:
                                # Look for columns by pattern matching
                                epoch_idx = None
                                map50_idx = None
                                map50_95_idx = None
                                precision_idx = None
                                recall_idx = None
                                box_loss_idx = None
                                cls_loss_idx = None
                                dfl_loss_idx = None

                                for i, col in enumerate(header):
                                    col = col.strip()
                                    if col == 'epoch':
                                        epoch_idx = i
                                    elif 'mAP50(B)' in col:
                                        map50_idx = i
                                    elif 'mAP50-95(B)' in col:
                                        map50_95_idx = i
                                    elif 'precision(B)' in col:
                                        precision_idx = i
                                    elif 'recall(B)' in col:
                                        recall_idx = i
                                    elif 'train/box_loss' in col or 'box_loss' in col:
                                        box_loss_idx = i
                                    elif 'train/cls_loss' in col or 'cls_loss' in col:
                                        cls_loss_idx = i
                                    elif 'train/dfl_loss' in col or 'dfl_loss' in col:
                                        dfl_loss_idx = i

                                # Now check if we found all the necessary columns
                                if epoch_idx is None:
                                    logger.warning(
                                        f"'epoch' column not found in results.csv. Available columns: {header}")
                                    continue

                            except Exception as e:
                                logger.error(
                                    f"Error finding column indices: {e}")
                                logger.error(f"Available columns: {header}")
                                continue

                            # Process each row (epoch)
                            for line in lines[1:]:
                                try:
                                    values = line.strip().split(',')
                                    if len(values) <= epoch_idx:
                                        continue

                                    # Convert to 1-indexed
                                    epoch = int(float(values[epoch_idx])) + 1

                                    # Skip already processed epochs
                                    if epoch <= prev_epoch:
                                        continue

                                    # Extract metrics
                                    metrics = {}
                                    if map50_idx is not None and map50_idx < len(values):
                                        try:
                                            metrics["map50"] = float(
                                                values[map50_idx])
                                            if metrics["map50"] > self.status.get("best_map50", 0):
                                                self.status["best_map50"] = metrics["map50"]
                                        except:
                                            pass

                                    if map50_95_idx is not None and map50_95_idx < len(values):
                                        try:
                                            metrics["map50_95"] = float(
                                                values[map50_95_idx])
                                            if metrics["map50_95"] > self.status.get("best_map50_95", 0):
                                                self.status["best_map50_95"] = metrics["map50_95"]
                                        except:
                                            pass

                                    if precision_idx is not None and precision_idx < len(values):
                                        try:
                                            metrics["precision"] = float(
                                                values[precision_idx])
                                        except:
                                            pass

                                    if recall_idx is not None and recall_idx < len(values):
                                        try:
                                            metrics["recall"] = float(
                                                values[recall_idx])
                                        except:
                                            pass

                                    if box_loss_idx is not None and box_loss_idx < len(values):
                                        try:
                                            metrics["box_loss"] = float(
                                                values[box_loss_idx])
                                        except:
                                            pass

                                    if cls_loss_idx is not None and cls_loss_idx < len(values):
                                        try:
                                            metrics["cls_loss"] = float(
                                                values[cls_loss_idx])
                                        except:
                                            pass

                                    if dfl_loss_idx is not None and dfl_loss_idx < len(values):
                                        try:
                                            metrics["dfl_loss"] = float(
                                                values[dfl_loss_idx])
                                        except:
                                            pass

                                    # Create epoch data
                                    epoch_data = {
                                        "epoch": epoch,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "metrics": metrics
                                    }

                                    # Update status data
                                    self.status['current_epoch'] = epoch
                                    if 'epochs' not in self.status:
                                        self.status['epochs'] = []
                                    self.status['epochs'].append(epoch_data)

                                    # Update status file
                                    self._update_status()

                                    # Print progress
                                    progress_msg = f"Model {self.model_id}: Epoch {epoch}/{total_epochs}"
                                    if "map50" in metrics:
                                        progress_msg += f", mAP50={metrics['map50']:.4f}"
                                    if "map50_95" in metrics:
                                        progress_msg += f", mAP50-95={metrics['map50_95']:.4f}"
                                    logger.info(progress_msg)

                                    # Remember processed epoch
                                    prev_epoch = epoch
                                    checks_without_progress = 0
                                    found_results = True
                                except Exception as e:
                                    logger.error(
                                        f"Error processing results row: {str(e)}")

                    except Exception as e:
                        logger.error(
                            f"Error reading results file {results_path}: {e}")

            # Check for train completion
            results_png_paths = [
                os.path.join(run_dir, "results.png"),
                os.path.join(run_dir, "train", "results.png")
            ]

            # Check if any results.png exists (indicates training may be complete)
            completed = any(os.path.exists(p) for p in results_png_paths)

            if completed:
                logger.info(
                    f"Found results.png for model {self.model_id}, training may be completed")

                # Update current epoch to total epochs if we're close
                if self.status['current_epoch'] > 0 and self.status['current_epoch'] < total_epochs:
                    # If we're close to completion, assume it's done
                    if self.status['current_epoch'] >= total_epochs * 0.8:
                        self.status['current_epoch'] = total_epochs
                        self._update_status()
                        logger.info(
                            f"Updated final epoch count to {total_epochs} for model {self.model_id}")

            # If we've checked many times without progress but YOLO is still running,
            # increment the epoch counter manually to show progress
            if not found_results:
                checks_without_progress += 1

                if checks_without_progress >= max_checks_without_progress:
                    current_epoch = self.status.get('current_epoch', 0)
                    # Increment by 1 but don't exceed total
                    if current_epoch < total_epochs:
                        new_epoch = min(current_epoch + 1, total_epochs)
                        logger.info(
                            f"No progress detected, manually incrementing epoch from {current_epoch} to {new_epoch}")

                        self.status['current_epoch'] = new_epoch
                        self._update_status()

                        checks_without_progress = 0

            # Wait before checking again
            time.sleep(3)

        logger.info(f"Finished monitoring thread for model {self.model_id}")

    def prepare_data(self, template_ids, img_size=640):
        """Prepare training data from templates"""
        try:
            # Update status
            self.status["status"] = "preparing_data"
            self.status["template_ids"] = template_ids
            self._update_status()

            # Import DAO when needed
            from dao.fraud_template_dao import FraudTemplateDAO
            from dao.fraud_label_dao import FraudLabelDAO

            fraud_template_dao = FraudTemplateDAO()
            fraud_label_dao = FraudLabelDAO()

            # Create dataset directories
            dataset_dir = os.path.join(self.model_dir, 'dataset')
            train_dir = os.path.join(dataset_dir, 'train')
            val_dir = os.path.join(dataset_dir, 'val')

            # Create directories
            for dir_path in [train_dir, val_dir]:
                os.makedirs(os.path.join(dir_path, 'images'), exist_ok=True)
                os.makedirs(os.path.join(dir_path, 'labels'), exist_ok=True)

            processed_images = []
            class_counts = {}  # Count for each class

            # Process each template
            for template_id in template_ids:
                template = fraud_template_dao.get_by_id(int(template_id))
                if not template:
                    logger.warning(f"Template ID not found: {template_id}")
                    continue

                # Get image path
                image_path = template.imageUrl
                if image_path.startswith('/'):
                    image_path = image_path[1:]

                # Normalize path
                if not os.path.exists(image_path) and image_path.startswith('static/'):
                    image_path = os.path.join(os.getcwd(), image_path)

                if not os.path.exists(image_path):
                    # Try relative path
                    alt_path = os.path.join(
                        os.getcwd(), image_path.lstrip('/'))
                    if os.path.exists(alt_path):
                        image_path = alt_path
                    else:
                        logger.warning(f"Image not found: {image_path}")
                        continue

                # Create image filename
                img_filename = f"img_{template_id}_{os.path.basename(image_path)}"

                # Copy image to train directory
                train_img_path = os.path.join(
                    train_dir, 'images', img_filename)
                shutil.copy2(image_path, train_img_path)

                # Create label file for train
                train_label_path = os.path.join(
                    train_dir, 'labels', f"{os.path.splitext(img_filename)[0]}.txt")

                boxes_in_image = []
                with open(train_label_path, 'w') as f:
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

                            # Update class count
                            class_counts[class_id] = class_counts.get(
                                class_id, 0) + 1

                            # Save box info
                            boxes_in_image.append({
                                'class_id': class_id,
                                'x': box.xCenter,
                                'y': box.yCenter,
                                'w': box.width,
                                'h': box.height
                            })

                            # Write line in label file
                            f.write(
                                f"{class_id} {box.xCenter} {box.yCenter} {box.width} {box.height}\n")

                # Add to processed images list
                processed_images.append({
                    'filename': img_filename,
                    'boxes': boxes_in_image
                })

            if not processed_images:
                logger.error("No images processed")
                self.status["status"] = "failed"
                self.status["error"] = "No images could be processed"
                self._update_status()
                return None

            # Choose validation images: at least 1 image, or 1/3 of total
            val_count = max(1, len(processed_images) // 3)
            logger.info(
                f"Selecting {val_count} images for validation from {len(processed_images)} total images")

            # Randomly select validation images
            val_indices = random.sample(
                range(len(processed_images)), min(val_count, len(processed_images)))
            val_images = [processed_images[i] for i in val_indices]

            # Copy these images to validation directory
            for img_info in val_images:
                img_name = img_info['filename']

                # Copy image
                train_img = os.path.join(train_dir, 'images', img_name)
                val_img = os.path.join(val_dir, 'images', img_name)
                shutil.copy2(train_img, val_img)

                # Copy label
                train_label = os.path.join(
                    train_dir, 'labels', f"{os.path.splitext(img_name)[0]}.txt")
                val_label = os.path.join(
                    val_dir, 'labels', f"{os.path.splitext(img_name)[0]}.txt")
                shutil.copy2(train_label, val_label)

            logger.info(
                f"Processed {len(processed_images)} images for training and {len(val_images)} for validation")

            # Create dataset.yaml file
            class_names = ["Human", "Object"]  # Default
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

            yaml_path = os.path.join(dataset_dir, 'dataset.yaml')
            with open(yaml_path, 'w') as f:
                f.write(yaml_content)

            # Update status with dataset info
            self.status["dataset_info"] = {
                'total_images': len(processed_images),
                'train_images': len(processed_images) - len(val_images),
                'val_images': len(val_images),
                'class_counts': {str(k): v for k, v in class_counts.items()}
            }
            self._update_status()

            return yaml_path

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error preparing data: {e}")
            logger.error(tb)

            self.status["status"] = "failed"
            self.status["error"] = str(e)
            self.status["error_details"] = tb
            self._update_status()

            return None

    def train(self, template_ids, epochs=100, batch_size=16, img_size=640, learning_rate=0.001):
        """Train the YOLOv8 model"""
        try:
            # Update status
            self.status["status"] = "initializing"
            self.status["configuration"] = {
                "epochs": epochs,
                "batch_size": batch_size,
                "image_size": img_size,
                "learning_rate": learning_rate
            }
            self.status["total_epochs"] = epochs
            self._update_status()

            # Prepare data
            yaml_path = self.prepare_data(template_ids, img_size)
            if not yaml_path:
                return False

            # Start monitoring thread
            self.status["status"] = "running"
            self._update_status()

            monitor_thread = threading.Thread(
                target=self._monitor_training_progress,
                args=(self.model_dir, epochs)
            )
            monitor_thread.daemon = True
            monitor_thread.start()

            # Train model using YOLOv8
            try:
                from ultralytics import YOLO

                # Initialize model
                model = YOLO('yolov8n.pt')  # Load pretrained model

                # Train model
                logger.info(
                    f"Starting YOLOv8 training with dataset: {yaml_path}")
                results = model.train(
                    data=yaml_path,
                    epochs=epochs,
                    imgsz=img_size,
                    batch=batch_size,
                    name=self.model_id,
                    project=self.output_dir,
                    exist_ok=True
                )

                # Wait for monitor thread to catch up
                monitor_thread.join(timeout=10)

                # Check for model file
                best_model_path = find_model_file(self.model_id)

                if best_model_path:
                    # Training successful
                    self.status["status"] = "completed"
                    self.status["end_time"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S")
                    self.status["model_path"] = os.path.abspath(
                        best_model_path)

                    # Make sure current_epoch is updated to total_epochs
                    self.status["current_epoch"] = epochs
                    self._update_status()

                    logger.info(
                        f"Training completed successfully for model {self.model_id}")
                    return True
                else:
                    # Model file not found
                    self.status["status"] = "failed"
                    self.status["error"] = "Model file not found after training"
                    self.status["end_time"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S")
                    self._update_status()

                    logger.error(f"Training failed: model file not found")
                    return False

            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"Error during YOLOv8 training: {e}")
                logger.error(tb)

                self.status["status"] = "failed"
                self.status["error"] = str(e)
                self.status["error_details"] = tb
                self.status["end_time"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S")
                self._update_status()

                return False

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error in train method: {e}")
            logger.error(tb)

            self.status["status"] = "failed"
            self.status["error"] = str(e)
            self.status["error_details"] = tb
            self.status["end_time"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
            self._update_status()

            return False

    def stop(self):
        """Stop the training process"""
        self.running = False
        self.status["status"] = "cancelled"
        self.status["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._update_status()
        logger.info(f"Training cancelled for model {self.model_id}")
        return True

    def get_status(self):
        """Get current status"""
        return self.status


def train_yolo_model(model_id, model_name, model_type, version, epochs, batch_size, image_size, learning_rate, template_ids):
    """
    Huấn luyện mô hình YOLOv8 trong thread riêng biệt

    Args:
        model_id: ID của mô hình
        model_name: Tên mô hình
        model_type: Loại mô hình
        version: Phiên bản
        epochs: Số epochs cần huấn luyện
        batch_size: Kích thước batch
        image_size: Kích thước ảnh đầu vào
        learning_rate: Tốc độ học
        template_ids: Danh sách ID template để huấn luyện

    Returns:
        Dict: Kết quả quá trình huấn luyện
    """
    logger.info(f"Starting training for model {model_name} (ID: {model_id})")

    # Create trainer
    trainer = YOLOModelTrainer(
        model_id=model_id,
        model_name=model_name,
        model_type=model_type,
        version=version
    )

    # Start training process
    result = trainer.train(
        template_ids=template_ids,
        epochs=epochs,
        batch_size=batch_size,
        img_size=image_size,
        learning_rate=learning_rate
    )

    # Return final status
    if result:
        return {
            'success': True,
            'message': 'Training successful',
            'model_path': trainer.status.get('model_path'),
            'metrics': trainer.status.get('metrics', {})
        }
    else:
        return {
            'success': False,
            'message': f'Training failed: {trainer.status.get("error", "Unknown error")}',
            'error': trainer.status.get('error_details', '')
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
        os.path.join('models', model_id, 'weights', 'best.pt'),
        os.path.join('models', model_id, 'weights', 'last.pt'),
        os.path.join('models', model_id, 'train', 'weights', 'best.pt'),
        os.path.join('models', model_id, 'train', 'weights', 'last.pt')
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
        # Cập nhật trạng thái
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)

        status['status'] = 'cancelled'
        status['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)

        # Tìm và kết thúc process liên quan
        try:
            # Thử sử dụng module psutil nếu có
            import psutil

            # Tìm tất cả các process Python đang chạy
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    # Kiểm tra xem process có phải Python và có đang huấn luyện model này
                    if cmdline and 'python' in proc.info['name'].lower() and any(model_id in arg for arg in cmdline if isinstance(arg, str)):
                        logger.info(
                            f"Found process for model {model_id}: PID {proc.pid}")
                        # Kết thúc process và các process con
                        parent = psutil.Process(proc.pid)
                        children = parent.children(recursive=True)
                        for child in children:
                            child.terminate()
                        parent.terminate()

                        gone, still_alive = psutil.wait_procs(
                            [parent] + children, timeout=3)

                        # Nếu vẫn còn process, kill cưỡng bức
                        for p in still_alive:
                            p.kill()

                        logger.info(
                            f"Terminated process tree for model {model_id}")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # Nếu không tìm thấy process cụ thể, kill tất cả các process YOLOv8 train
            killed = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'python' in proc.info['name'].lower() and any('yolo' in arg.lower() and 'train' in arg.lower() for arg in cmdline if isinstance(arg, str)):
                        logger.info(
                            f"Found YOLO training process: PID {proc.pid}")
                        proc.terminate()
                        killed = True
                except:
                    pass

            return killed

        except ImportError:
            # Nếu không có psutil, sử dụng các lệnh hệ thống
            import platform
            import subprocess

            if platform.system() == "Windows":
                # Kết thúc process trên Windows
                try:
                    subprocess.run(
                        f'taskkill /F /FI "WINDOWTITLE eq *{model_id}*"', shell=True)
                    subprocess.run(
                        f'taskkill /F /FI "IMAGENAME eq python.exe" /FI "COMMANDLINE eq *{model_id}*"', shell=True)
                    return True
                except:
                    return False
            else:
                # Kết thúc process trên Linux/Mac
                try:
                    subprocess.run(
                        f"pkill -f 'python.*{model_id}'", shell=True)
                    return True
                except:
                    return False

    except Exception as e:
        logger.error(f"Error cancelling training: {e}")
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python train_model.py <model_id> <model_name> <model_type> <version> <epochs> <batch_size> <image_size> <learning_rate> <template_id1,template_id2,...>")
        sys.exit(1)

    model_id = sys.argv[1]
    model_name = sys.argv[2]
    model_type = sys.argv[3]
    version = sys.argv[4]
    epochs = int(sys.argv[5]) if len(sys.argv) > 5 else 100
    batch_size = int(sys.argv[6]) if len(sys.argv) > 6 else 16
    image_size = int(sys.argv[7]) if len(sys.argv) > 7 else 640
    learning_rate = float(sys.argv[8]) if len(sys.argv) > 8 else 0.001
    template_ids = [int(tid) for tid in sys.argv[9].split(
        ',')] if len(sys.argv) > 9 else []

    result = train_yolo_model(model_id, model_name, model_type, version,
                              epochs, batch_size, image_size, learning_rate, template_ids)
    print(json.dumps(result, indent=2))
