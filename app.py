import train_model_utils
from flask import Flask, redirect, request, url_for, jsonify
from config.config import Config
from flask import render_template
from datetime import datetime
import time
# Import các DAOs
from dao.model_dao import ModelDAO
from dao.train_info_dao import TrainInfoDAO
from dao.training_data_dao import TrainingDataDAO
from dao.fraud_template_dao import FraudTemplateDAO
from dao.fraud_label_dao import FraudLabelDAO
from dao.bounding_box_dao import BoundingBoxDAO
from dao.training_lost_dao import TrainingLostDAO
from dao.phase_detection_dao import PhaseDetectionDAO
from dao.detect_result_dao import DetectResultDAO
from utils.enums import ModelType
from models.train_info import TrainInfo
from models.training_data import TrainingData
from models.model import Model
# Khởi tạo Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "8f42a73054b92c79c07935be5a17aa0ca383b783e4e321f3"

# Khởi tạo các DAO
model_dao = ModelDAO()
train_info_dao = TrainInfoDAO()
training_data_dao = TrainingDataDAO()
fraud_template_dao = FraudTemplateDAO()
fraud_label_dao = FraudLabelDAO()
bounding_box_dao = BoundingBoxDAO()
training_lost_dao = TrainingLostDAO()
phase_detection_dao = PhaseDetectionDAO()
detect_result_dao = DetectResultDAO()


@app.template_filter('fix_image_path')
def fix_image_path(path):
    """Chuyển đổi backslash thành forward slash trong đường dẫn"""
    if path:
        # Xử lý các trường hợp đặc biệt
        if '\\' in path:
            path = path.replace('\\', '/')

        # Đảm bảo path bắt đầu bằng /static nếu là đường dẫn tương đối
        if path.startswith('static/'):
            path = '/' + path
        elif not path.startswith('/static/') and 'static/' in path:
            # Nếu path chứa static/ nhưng không bắt đầu bằng nó
            idx = path.find('static/')
            path = '/' + path[idx:]

        return path
    return path


@app.route('/')
def index():
    return redirect("/model-management")


@app.route('/model-management')
def model_management():
    model_list = model_dao.get_all()
    model_dict = []
    for i in range(len(model_list)-1, -1, -1):
        model_dict.append(model_list[i].to_dict())
    return render_template('model_management.html', models=model_dict)


@app.route('/add-model', methods=['GET', 'POST'])
def route_add_model():
    if request.method == 'GET':
        templates = fraud_template_dao.get_all()
        templates_dict = []
        for template in templates:
            template_dict = template.to_dict()
            templates_dict.append(template_dict)
        model_types = ModelType.get_all_values()
        return render_template('add_model.html', sample_images=templates_dict, model_types=model_types)
    else:
        pass


@app.route('/api/train-model', methods=['POST'])
def train_model():
    data = request.json
    model_name = data.get('model_name')
    model_type = data.get('model_type')
    version = data.get('version')

    if not model_name or not model_type or not version:
        return jsonify({'success': False, 'message': 'Thiếu thông tin mô hình'})

    template_ids = data.get('template_ids', [])
    if not template_ids:
        return jsonify({'success': False, 'message': 'Vui lòng chọn ít nhất một template'})
    models = model_dao.get_all()
    model_id = models[0].idModel + 1
    epochs = int(data.get('epochs', 100))
    batch_size = int(data.get('batch_size', 16))
    learning_rate = float(data.get('learning_rate', 0.001))
    image_size = int(data.get('image_size', 640))
    result = train_model_utils.train_yolo_model(
        model_id=model_id,
        model_name=model_name,
        model_type=model_type,
        version=version,
        epochs=epochs,
        batch_size=batch_size,
        image_size=image_size,
        learning_rate=learning_rate,
        template_ids=template_ids
    )
    return jsonify({
        'success': True,
        'model_id': model_id,
        'message': result['message']
    })


@app.route('/api/training_status/<string:model_id>', methods=['GET'])
def api_training_status(model_id):
    try:
        status = train_model_utils.get_training_status(model_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'status': 'training',
            'progress': 50,
            'current_epoch': 6,
            'total_epochs': 10,
            'loss': 0.5,
            'metrics': {
                'metrics/mAP50(B)': 0.5
            },
            'error_info': str(e)
        })


@app.route('/api/cancel_training/<int:model_id>', methods=['POST'])
def cancel_training(model_id):
    result = train_model_utils.cancel_training(model_id)
    if result:
        return jsonify({'success': True, 'message': 'Đã hủy quá trình huấn luyện'})
    else:
        return jsonify({'success': False, 'message': 'Không tìm thấy quá trình huấn luyện'})
    pass


@app.route('/api/save_trained_model/<int:model_id>', methods=['POST'])
def save_trained_model(model_id):
    status = train_model_utils.get_training_status(model_id)
    model_name = status.get('model_name', '')
    model_type = status.get('model_type', '')
    version = status.get('version', '')

    existing_models = model_dao.get_all()

    for existing_model in existing_models:
        if existing_model.modelName == model_name and existing_model.version == version:
            return jsonify({
                'success': False,
                'message': f'Mô hình {model_name} phiên bản {version} đã tồn tại. Vui lòng thử lại.'
            })

    train_info = TrainInfo(
        epoch=status.get('total_epochs', 0),
        learningRate=status.get('learning_rate', 0.001),
        batchSize=status.get('batch_size', 16),
        mae=status.get('mae', 0.0),
        mse=status.get('mse', 0.0),
        accuracy=status.get('accuracy', 0.85),
        trainDuration=int(status.get('duration', 0)),
        timeTrain=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    train_info_id = train_info_dao.create(train_info)
    train_info.idInfo = train_info_id
    epoch_metrics = status.get('epoch_metrics', {})

    saved_epochs = 0
    for epoch_key, metrics in epoch_metrics.items():
        if isinstance(epoch_key, str) and epoch_key.startswith('epoch_'):
            try:
                epoch_num = int(epoch_key.replace('epoch_', ''))
                loss_value = metrics.get('loss', 0.0)

                training_lost = TrainingLost(
                    epoch=epoch_num,
                    lost=loss_value,
                    trainInfoId=train_info_id
                )

                training_lost_dao.create(training_lost)
                saved_epochs += 1
            except Exception as e:
                logging.error(
                    f"[SAVE_MODEL] Error creating TrainingLost for {epoch_key}: {str(e)}")

    model = Model(
        modelName=model_name,
        modelType=model_type,
        version=version,
        description=f"Model huấn luyện YOLOv8 ngày {datetime.now().strftime('%Y-%m-%d')}",
        lastUpdate=datetime.now()
    )

    model.trainInfo = train_info
    model_id_db = model_dao.create(model)
    template_ids = status.get("template_ids")
    print(template_ids)
    for image_id in template_ids:
        print(image_id)
        template = fraud_template_dao.get_by_id(int(image_id))
        if template:
            training_data = TrainingData(
                modelId=model_id_db,
                fraudTemplateId=template.idTemplate,
                description=f"Training data for {model_name}",
                timeUpdate=datetime.now()
            )
            training_data_dao.create(training_data)
    train_model_utils.cleanup_training_data(model_id, keep_model=True)

    return jsonify({
        'success': True,
        'model_id': model_id_db,
        'message': 'Đã lưu thông tin mô hình thành công'
    })


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
