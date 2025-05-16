import sys
from models.training_lost import TrainingLost
from models.model import Model
from models.training_data import TrainingData
from models.train_info import TrainInfo
from utils.enums import ModelType
from dao.training_lost_dao import TrainingLostDAO
from dao.bounding_box_dao import BoundingBoxDAO
from dao.fraud_label_dao import FraudLabelDAO
from dao.fraud_template_dao import FraudTemplateDAO
from dao.training_data_dao import TrainingDataDAO
from dao.train_info_dao import TrainInfoDAO
from dao.model_dao import ModelDAO
import os
import json
import threading
from flask import Flask, redirect, request, url_for, jsonify, render_template, flash
from config.config import Config
from datetime import datetime
import logging
from dotenv import load_dotenv

# Import train_model module
from train_model import train_yolo_model, get_training_status, cancel_training, find_model_file

load_dotenv()

# Khởi tạo Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv(
    "SECRET_KEY", "8f42a73054b92c79c07935be5a17aa0ca383b783e4e321f3")

# Khởi tạo các DAO
model_dao = ModelDAO()
train_info_dao = TrainInfoDAO()
training_data_dao = TrainingDataDAO()
fraud_template_dao = FraudTemplateDAO()
fraud_label_dao = FraudLabelDAO()
bounding_box_dao = BoundingBoxDAO()
training_lost_dao = TrainingLostDAO()

# Đảm bảo thư mục cần thiết tồn tại
os.makedirs("model_train_logs", exist_ok=True)


@app.template_filter('fix_image_path')
def fix_image_path(path):
    """Chuyển đổi backslash thành forward slash trong đường dẫn"""
    if path:
        if '\\' in path:
            path = path.replace('\\', '/')

        if path.startswith('static/'):
            path = '/' + path
        elif not path.startswith('/static/') and 'static/' in path:
            idx = path.find('static/')
            path = '/' + path[idx:]

        return path
    return path


@app.route('/')
def index():
    return redirect("/model-management")


@app.route('/model-management')
def model_management():
    """Trang quản lý mô hình."""
    model_list = model_dao.get_all()
    model_dict = []
    for i in range(len(model_list)-1, -1, -1):
        model_dict.append(model_list[i].to_dict())
    return render_template('model_management.html', models=model_dict, active_page='model_management')


@app.route('/add-model', methods=['GET', 'POST'])
def route_add_model():
    if request.method == 'GET':
        templates = fraud_template_dao.get_all()
        templates_dict = []
        for template in templates:
            template_dict = template.to_dict()
            templates_dict.append(template_dict)
        model_types = ModelType.get_all_values()
        models = model_dao.get_all()
        model_id = 1000
        if models and len(models) > 0:
            model_id = max([m.idModel for m in models]) + 1
        return render_template('add_model.html', sample_images=templates_dict, model_types=model_types, model_id=model_id, active_page='model_management')
    else:
        try:
            data = request.json

            model_id = data.get('model_id')

            if not model_id:
                return jsonify({'success': False, 'message': 'Không tìm thấy thông tin ID mô hình'})

            training_status = get_training_status(model_id)
            if training_status.get('status') != 'completed':
                return jsonify({'success': False, 'message': f'Huấn luyện chưa hoàn thành (trạng thái: {training_status.get("status")})'})

            model_name = data.get('model_name', '')
            model_type = data.get('model_type', '')
            version = data.get('version', '')
            description = data.get('description', '')

            print(
                f"Saving model: {model_name}, type: {model_type}, version: {version}")

            # Kiểm tra mô hình đã tồn tại
            existing_models = model_dao.get_all()
            for existing_model in existing_models:
                if existing_model.modelName == model_name and existing_model.version == version:
                    return jsonify({'success': False, 'message': f'Mô hình {model_name} phiên bản {version} đã tồn tại.'})

            # Tạo TrainInfo object
            train_info = TrainInfo(
                epoch=int(
                    data.get('epochs', training_status.get('total_epochs', 100))),
                learningRate=float(data.get('learning_rate', 0.001)),
                batchSize=int(data.get('batch_size', 16)),
                accuracy=float(training_status.get(
                    'final_metrics', {}).get('accuracy', 0.85)),
                timeTrain=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            # Lưu TrainInfo
            train_info_id = train_info_dao.create(train_info)
            train_info.idInfo = train_info_id

            # Tạo Model và lưu vào database
            model = Model(
                modelName=model_name,
                modelType=model_type,
                version=version,
                description=description or f"Model huấn luyện YOLOv8 ngày {datetime.now().strftime('%Y-%m-%d')}",
                lastUpdate=datetime.now()
            )

            model.trainInfo = train_info
            model_id_db = model_dao.create(model)

            print(f"Model created with database ID: {model_id_db}")

            # Lưu dữ liệu huấn luyện (template ID)
            template_ids = data.get('template_ids', [])
            processed_templates = 0

            for template_id in template_ids:
                template = fraud_template_dao.get_by_id(int(template_id))
                if template:
                    training_data = TrainingData(
                        modelId=model_id_db,
                        fraudTemplateId=template.idTemplate,
                        description=f"Training data for {model_name}",
                        timeUpdate=datetime.now()
                    )
                    training_data_dao.create(training_data)
                    processed_templates += 1

            print(f"Processed {processed_templates} templates for model")

            # Trả về kết quả thành công dưới dạng JSON
            return jsonify({'success': True,
                            'message': f'Mô hình {model_name} đã được lưu thành công!'})

        except Exception as e:
            print(f"Error saving model: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi khi lưu mô hình: {str(e)}'})


def run_training_in_thread(model_id, model_name, model_type, version, template_ids, epochs, batch_size, image_size, learning_rate):
    try:
        result = train_yolo_model(model_id, model_name, model_type, version,
                                  epochs, batch_size, image_size, learning_rate, template_ids)
        if result['success']:
            print("train success")
        else:
            print("train failed", result['message'])
    except Exception as e:
        print(e)


@app.route('/api/train-model', methods=['POST'])
def api_train_model():
    try:
        data = request.json
        model_name = data.get('model_name')
        model_type = data.get('model_type', 'FraudDetection')
        version = data.get('version', 'v1.0.0')
        template_ids = data.get('template_ids', [])
        epochs = int(data.get('epochs', 100))
        batch_size = int(data.get('batch_size', 16))
        image_size = int(data.get('image_size', 640))
        learning_rate = float(data.get('learning_rate', 0.001))

        if not model_name or not template_ids:
            return jsonify({'success': False, 'message': 'Thiếu thông tin cần thiết'})

        # Lấy model ID mới
        models = model_dao.get_all()
        model_id = 1000
        if models and len(models) > 0:
            model_id = max([m.idModel for m in models]) + 1

        training_thread = threading.Thread(
            target=run_training_in_thread,
            args=(model_id, model_name, model_type, version, template_ids, epochs,
                  batch_size, image_size, learning_rate)
        )
        training_thread.daemon = True
        training_thread.start()

        return jsonify({
            'success': True,
            'model_id': model_id,
            'message': 'Đã bắt đầu huấn luyện'
        })
    except Exception as e:
        print(e)
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })


@app.route('/api/training-status/<model_id>', methods=['GET'])
def api_training_status(model_id):
    """API lấy trạng thái huấn luyện."""
    try:
        status = get_training_status(model_id)
        print(status)
        return jsonify(status)
    except Exception as e:
        print(e)
        return jsonify({
            'status': 'error',
            'error': str(e)
        })


@app.route('/api/cancel-training/<model_id>', methods=['POST'])
def api_cancel_training(model_id):
    try:
        model_id = str(model_id)
        print(f"Nhận yêu cầu hủy huấn luyện cho model ID: {model_id}")
        status_file = os.path.join('model_train_logs', model_id, 'status.json')
        if not os.path.exists(status_file):
            print(f"Không tìm thấy file status cho model {model_id}")
            return jsonify({
                'success': False,
                'message': 'Không tìm thấy thông tin huấn luyện'
            })

        # Cập nhật trạng thái trong file
        with open(status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)

        # Nếu đã hoàn thành/hủy/lỗi rồi thì không cần làm gì thêm
        if status.get('status') in ['cancelled', 'completed', 'failed']:
            print(
                f"Model {model_id} đã ở trạng thái {status.get('status')}, không cần hủy")
            return jsonify({
                'success': True,
                'message': f"Model đã ở trạng thái {status.get('status')}"
            })

        # Đổi trạng thái thành cancelled
        status['status'] = 'cancelled'
        status['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)

        # Sử dụng hàm có sẵn từ train_model.py
        from train_model import cancel_training
        cancel_success = cancel_training(model_id)

        if cancel_success:
            print(
                f"Đã hủy thành công quá trình huấn luyện model {model_id}")
            return jsonify({
                'success': True,
                'message': 'Đã hủy quá trình huấn luyện'
            })
        else:
            print(
                f"Không tìm thấy process huấn luyện để hủy cho model {model_id}")
            return jsonify({
                'success': True,
                'message': 'Đã cập nhật trạng thái hủy, nhưng không tìm thấy process để kết thúc'
            })

    except Exception as e:
        print(f"Lỗi khi hủy huấn luyện: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })


@app.after_request
def add_header(response):
    """Thêm header để vô hiệu hóa cache."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


# Đảm bảo stdout và stderr có thể xử lý Unicode
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

if __name__ == '__main__':
    # Make sure to disable reloader
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000, use_reloader=False)
