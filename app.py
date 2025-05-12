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

# Load environment variables
load_dotenv()

# Khởi tạo Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv("SECRET_KEY", "8f42a73054b92c79c07935be5a17aa0ca383b783e4e321f3")

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app")

# Import các DAOs
from dao.model_dao import ModelDAO
from dao.train_info_dao import TrainInfoDAO
from dao.training_data_dao import TrainingDataDAO
from dao.fraud_template_dao import FraudTemplateDAO
from dao.fraud_label_dao import FraudLabelDAO
from dao.bounding_box_dao import BoundingBoxDAO
from dao.training_lost_dao import TrainingLostDAO
from utils.enums import ModelType
from models.train_info import TrainInfo
from models.training_data import TrainingData
from models.model import Model
from models.training_lost import TrainingLost

# Khởi tạo các DAO
model_dao = ModelDAO()
train_info_dao = TrainInfoDAO()
training_data_dao = TrainingDataDAO()
fraud_template_dao = FraudTemplateDAO()
fraud_label_dao = FraudLabelDAO()
bounding_box_dao = BoundingBoxDAO()
training_lost_dao = TrainingLostDAO()

# Đảm bảo thư mục cần thiết tồn tại
os.makedirs("models", exist_ok=True)


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
    """Trang thêm mô hình mới."""
    if request.method == 'GET':
        templates = fraud_template_dao.get_all()
        templates_dict = []
        for template in templates:
            template_dict = template.to_dict()
            templates_dict.append(template_dict)
        model_types = ModelType.get_all_values()
        return render_template('add_model.html', sample_images=templates_dict, model_types=model_types, active_page='model_management')
    else:
        # Xử lý POST request để lưu mô hình đã train vào database
        model_id = request.form.get('model_id')
        if not model_id:
            flash('Không tìm thấy thông tin ID mô hình', 'danger')
            return redirect(url_for('model_management'))
            
        # Lấy trạng thái huấn luyện
        training_status = get_training_status(model_id)
        if training_status.get('status') != 'completed':
            flash(f'Huấn luyện chưa hoàn thành (trạng thái: {training_status.get("status")})', 'warning')
            return redirect(url_for('add_model'))
            
        # Lấy thông tin từ form
        model_name = request.form.get('model_name', '')
        model_type = request.form.get('model_type', '')
        version = request.form.get('version', '')
        description = request.form.get('description', '')
        
        # Kiểm tra mô hình đã tồn tại
        existing_models = model_dao.get_all()
        for existing_model in existing_models:
            if existing_model.modelName == model_name and existing_model.version == version:
                flash(f'Mô hình {model_name} phiên bản {version} đã tồn tại.', 'danger')
                return redirect(url_for('add_model'))
        
        # Tạo TrainInfo object
        train_info = TrainInfo(
            epoch=int(training_status.get('total_epochs', 100)),
            learningRate=float(0.01),  # Default value
            batchSize=int(16),  # Default value
            accuracy=float(0.85),  # Default value
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
        
        # Lưu dữ liệu huấn luyện (template ID)
        template_ids = training_status.get("template_ids", [])
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
        
        flash(f'Mô hình {model_name} đã được lưu thành công!', 'success')
        return redirect(url_for('model_management'))


def run_training_in_thread(model_id, model_name, template_ids, epochs):
    """
    Chạy huấn luyện trong thread riêng biệt để không block server
    """
    try:
        logger.info(f"Bắt đầu huấn luyện model {model_name} (ID: {model_id}) trong thread riêng")
        train_yolo_model(model_id, model_name, template_ids, epochs)
        logger.info(f"Hoàn thành huấn luyện model {model_id}")
    except Exception as e:
        logger.error(f"Lỗi khi huấn luyện model {model_id} trong thread: {e}")


@app.route('/api/train-model', methods=['POST'])
def api_train_model():
    """API bắt đầu huấn luyện mô hình."""
    try:
        data = request.json
        model_name = data.get('model_name')
        model_type = data.get('model_type', 'FraudDetection')  # Giá trị mặc định
        template_ids = data.get('template_ids', [])
        epochs = int(data.get('epochs', 100))
        
        if not model_name or not template_ids:
            logger.warning("Thiếu thông tin cần thiết cho huấn luyện")
            return jsonify({'success': False, 'message': 'Thiếu thông tin cần thiết'})
        
        # Lấy model ID mới
        models = model_dao.get_all()
        model_id = 1000  # Default
        if models and len(models) > 0:
            model_id = max([m.idModel for m in models]) + 1
            
        logger.info(f"Tạo model mới với ID: {model_id}, tên: {model_name}")
        
        # Bắt đầu huấn luyện trong thread riêng để không block server
        training_thread = threading.Thread(
            target=run_training_in_thread,
            args=(model_id, model_name, template_ids, epochs)
        )
        training_thread.daemon = True
        training_thread.start()
        
        logger.info(f"Đã bắt đầu thread huấn luyện cho model ID: {model_id}")
        
        return jsonify({
            'success': True,
            'model_id': model_id,
            'message': 'Đã bắt đầu huấn luyện'
        })
    except Exception as e:
        logger.error(f"Lỗi API train model: {e}")
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
        logger.debug(f"Lấy trạng thái model {model_id}: {status.get('status')}")
        return jsonify(status)
    except Exception as e:
        logger.error(f"Lỗi khi lấy trạng thái huấn luyện: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })


@app.route('/api/cancel-training/<model_id>', methods=['POST'])
def api_cancel_training(model_id):
    """API hủy huấn luyện."""
    try:
        logger.info(f"Nhận yêu cầu hủy huấn luyện cho model {model_id}")
        result = cancel_training(model_id)
        
        if result:
            logger.info(f"Đã hủy thành công quá trình huấn luyện cho model {model_id}")
            return jsonify({'success': True, 'message': 'Đã hủy quá trình huấn luyện'})
        else:
            logger.warning(f"Không thể hủy quá trình huấn luyện cho model {model_id}")
            return jsonify({'success': False, 'message': 'Không tìm thấy quá trình huấn luyện'})
    except Exception as e:
        logger.error(f"Lỗi khi hủy huấn luyện model {model_id}: {e}")
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


# Tắt debug nếu ở môi trường production
if not Config.DEBUG:
    # Tắt watchdog/reloading để tránh các vấn đề với thread
    # Khi tắt debug, watchdog sẽ không theo dõi các file thư viện
    app.config['USE_RELOADER'] = False
# Đảm bảo stdout và stderr có thể xử lý Unicode
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

if __name__ == '__main__':
    # Kiểm tra và tạo thư mục models nếu cần
    os.makedirs('models', exist_ok=True)
    
    # Khởi động server
    app.run(
        debug=Config.DEBUG, 
        host='0.0.0.0', 
        port=5000,
        use_reloader=Config.DEBUG  # Chỉ sử dụng reloader trong môi trường dev
    )