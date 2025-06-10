import os
import json
import time
import threading
import traceback
import requests
import shutil
from datetime import datetime
import random
from config import Config

# Khởi tạo thư mục
Config.init_directories()


def ensure_dir(directory):
    """Tạo thư mục nếu chưa tồn tại"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_template_image(template_id, save_dir):
    """Tải ảnh từ template service về shared_model"""
    try:
        # Lấy thông tin template
        template_url = f"{Config.TEMPLATE_SERVICE_URL}/templates/{template_id}"
        response = requests.get(template_url, timeout=30)
        response.raise_for_status()

        template_data = response.json()
        image_url = template_data.get('imageUrl', '')

        if not image_url:
            return None, None

        # Tải ảnh từ /images/ endpoint
        if image_url.startswith('/images/'):
            # URL dạng /images/filename.jpg
            full_url = f"{Config.TEMPLATE_SERVICE_URL}{image_url}"
        elif image_url.startswith('http'):
            # URL đầy đủ
            full_url = image_url
        else:
            # Fallback
            full_url = f"{Config.TEMPLATE_SERVICE_URL}/images/{image_url}"

        print(f"Downloading image from: {full_url}")
        image_response = requests.get(full_url, timeout=30)
        image_response.raise_for_status()

        # Lưu ảnh
        filename = f"template_{template_id}.jpg"
        image_path = os.path.join(save_dir, filename)

        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        print(f"Downloaded: {image_path}")
        return image_path, template_data

    except Exception as e:
        print(f"Error downloading template {template_id}: {e}")
        return None, None


def train_yolo_model(model_id, model_name, model_type, version, epochs=100,
                     batch_size=16, image_size=640, learning_rate=0.001, template_ids=None):
    """Huấn luyện YOLO model với ảnh tải về shared_model"""

    model_id = str(model_id)
    print(f"Bắt đầu huấn luyện model {model_name} (ID: {model_id})")

    # Tạo thư mục trong shared_model
    model_dir = os.path.join(Config.SHARED_MODEL_DIR, f"model_{model_id}")
    dataset_dir = os.path.join(model_dir, "dataset")
    images_dir = os.path.join(model_dir, "images")

    ensure_dir(model_dir)
    ensure_dir(dataset_dir)
    ensure_dir(images_dir)

    # Tạo cấu trúc dataset
    train_images = os.path.join(dataset_dir, "train", "images")
    train_labels = os.path.join(dataset_dir, "train", "labels")
    val_images = os.path.join(dataset_dir, "val", "images")
    val_labels = os.path.join(dataset_dir, "val", "labels")

    for path in [train_images, train_labels, val_images, val_labels]:
        ensure_dir(path)

    # File trạng thái
    status_file = os.path.join(model_dir, 'status.json')
    status = {
        "status": "preparing_data",
        "model_id": model_id,
        "model_name": model_name,
        "current_epoch": 0,
        "total_epochs": epochs,
        "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "template_ids": template_ids or []
    }

    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

    try:
        processed_images = []

        # Tải và xử lý từng template
        for template_id in template_ids:
            print(f"Processing template {template_id}")

            # Tải ảnh và dữ liệu
            image_path, template_data = download_template_image(
                template_id, images_dir)
            if not image_path or not template_data:
                continue

            # Copy ảnh vào train
            img_filename = f"img_{template_id}.jpg"
            train_img_path = os.path.join(train_images, img_filename)
            shutil.copy2(image_path, train_img_path)

            # Tạo file label
            label_filename = f"img_{template_id}.txt"
            train_label_path = os.path.join(train_labels, label_filename)

            with open(train_label_path, 'w') as f:
                for box in template_data.get('boundingBox', []):
                    # Đơn giản hóa: tất cả class_id = 0
                    f.write(
                        f"0 {box['xCenter']} {box['yCenter']} {box['width']} {box['height']}\n")

            processed_images.append(img_filename)

        if not processed_images:
            status["status"] = "failed"
            status["error"] = "Không có ảnh nào được xử lý"
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)
            return {'success': False, 'message': 'Không có ảnh được tải'}

        # Tạo validation set (copy 1 ảnh)
        if processed_images:
            val_img = processed_images[0]
            shutil.copy2(
                os.path.join(train_images, val_img),
                os.path.join(val_images, val_img)
            )
            shutil.copy2(
                os.path.join(train_labels, val_img.replace('.jpg', '.txt')),
                os.path.join(val_labels, val_img.replace('.jpg', '.txt'))
            )

        # Tạo dataset.yaml
        yaml_content = f"""
path: {os.path.abspath(dataset_dir)}
train: train/images
val: val/images
names:
  0: object
"""
        with open(os.path.join(dataset_dir, 'dataset.yaml'), 'w') as f:
            f.write(yaml_content)

        # Bắt đầu huấn luyện
        status["status"] = "running"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)

        def train_thread():
            try:
                from ultralytics import YOLO

                model = YOLO('yolov8n.pt')

                # Huấn luyện
                results = model.train(
                    data=os.path.join(dataset_dir, 'dataset.yaml'),
                    epochs=epochs,
                    batch=batch_size,
                    project=model_dir,
                    name='train',
                    exist_ok=True
                )

                # Cập nhật trạng thái hoàn thành
                status["status"] = "completed"
                status["end_time"] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
                status["current_epoch"] = epochs

                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(status, f, indent=2)

                print(f"Hoàn thành huấn luyện model {model_id}")

            except Exception as e:
                status["status"] = "failed"
                status["error"] = str(e)
                status["end_time"] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')

                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(status, f, indent=2)

                print(f"Lỗi huấn luyện: {e}")

        # Chạy trong thread
        thread = threading.Thread(target=train_thread)
        thread.daemon = True
        thread.start()

        return {'success': True, 'model_id': model_id}

    except Exception as e:
        status["status"] = "failed"
        status["error"] = str(e)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        return {'success': False, 'message': str(e)}


def get_training_status(model_id):
    """Lấy trạng thái huấn luyện"""
    status_file = os.path.join(
        Config.SHARED_MODEL_DIR, f"model_{model_id}", 'status.json')

    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    return {'status': 'not_found', 'message': 'Không tìm thấy thông tin huấn luyện'}


def cancel_training(model_id):
    """Hủy huấn luyện"""
    status_file = os.path.join(
        Config.SHARED_MODEL_DIR, f"model_{model_id}", 'status.json')

    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)

            status['status'] = 'cancelled'
            status['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2)

            return True
        except:
            pass

    return False
