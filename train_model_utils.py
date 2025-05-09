import time
import threading

# Khai báo biến lưu trạng thái training
training_states = {}


def get_training_status(model_id):
    if str(model_id) not in training_states:
        return {'status': 'not_found'}
    return training_states[str(model_id)]


def simulate_training_process(model_id, epochs):
    """Giả lập quá trình huấn luyện theo thời gian"""
    model_id = str(model_id)
    # Thời gian bắt đầu
    start_time = time.time()
    # Tổng thời gian huấn luyện (20 giây)
    total_training_time = 20.0

    # Đặt trạng thái ban đầu là training
    training_states[model_id]['status'] = 'training'

    # Vòng lặp giả lập quá trình huấn luyện
    while True:
        # Tính toán thời gian đã trôi qua
        elapsed_time = time.time() - start_time

        # Kiểm tra nếu quá trình đã hoàn thành hoặc bị hủy
        if training_states[model_id]['status'] == 'cancelled':
            break

        if elapsed_time >= total_training_time:
            # Huấn luyện hoàn tất
            training_states[model_id]['status'] = 'completed'
            training_states[model_id]['progress'] = 100
            training_states[model_id]['current_epoch'] = epochs
            training_states[model_id]['metrics'] = {
                'metrics/mAP50(B)': 0.85,
                'metrics/precision(B)': 0.82,
                'metrics/recall(B)': 0.87
            }
            training_states[model_id]['model_path'] = f"models/{model_id}/best.pt"
            training_states[model_id]['duration'] = int(elapsed_time)
            break
        else:
            # Tính toán tiến trình huấn luyện
            progress = (elapsed_time / total_training_time) * 100
            current_epoch = int((epochs * progress) / 100)

            # Cập nhật trạng thái
            training_states[model_id]['progress'] = progress
            training_states[model_id]['current_epoch'] = max(1, current_epoch)
            training_states[model_id]['loss'] = 1.0 - (progress / 100) * 0.9
            training_states[model_id]['metrics']['metrics/mAP50(B)'] = (
                progress / 100) * 0.85

            # Ngủ một chút để không tiêu tốn tài nguyên
            time.sleep(0.5)


def train_yolo_model(model_id, model_name, model_type, version, epochs, batch_size, image_size, learning_rate, template_ids):
    model_id = str(model_id)
    # Khởi tạo trạng thái huấn luyện
    training_states[model_id] = {
        'status': 'initializing',
        'progress': 0,
        'model_name': model_name,
        'model_type': model_type,
        'version': version,
        'current_epoch': 0,
        'total_epochs': epochs,
        'batch_size': batch_size,
        'learning_rate': learning_rate,
        'template_ids': template_ids,
        'metrics': {'metrics/mAP50(B)': 0},
        'epoch_metrics': {},
        'loss': 1.0
    }

    # Bắt đầu một thread mới để giả lập quá trình huấn luyện
    training_thread = threading.Thread(
        target=simulate_training_process, args=(model_id, epochs))
    training_thread.daemon = True
    training_thread.start()

    return {'success': True, 'message': 'Huấn luyện bắt đầu thành công'}


def cancel_training(model_id):
    model_id = str(model_id)
    if model_id in training_states:
        training_states[model_id]['status'] = 'cancelled'
        return True
    return False


def cleanup_training_data(model_id, keep_model=True):
    model_id = str(model_id)
    if model_id in training_states and not keep_model:
        del training_states[model_id]
    return True
