// Biến toàn cục
let isTraining = false;
let modelId = null;
let statusInterval = null;

// Chạy khi trang được load
document.addEventListener('DOMContentLoaded', function() {
    // Lắng nghe sự kiện cho các checkbox mẫu
    const sampleCheckboxes = document.querySelectorAll('.sample-checkbox');
    sampleCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateTrainButtonState);
    });
    
    // Thiết lập nút Train
    const trainButton = document.getElementById('trainModelBtn');
    if (trainButton) {
        trainButton.addEventListener('click', startTraining);
    }
    
    // Thiết lập nút Cancel
    const cancelButton = document.getElementById('cancelTrainingBtn');
    if (cancelButton) {
        cancelButton.addEventListener('click', cancelTraining);
    }
    
    // Thiết lập nút Finish
    const finishButton = document.getElementById('finishTrainingBtn');
    if (finishButton) {
        finishButton.addEventListener('click', finishTraining);
    }
    
    // Cập nhật trạng thái ban đầu
    updateTrainButtonState();
});

// Cập nhật trạng thái nút Train
function updateTrainButtonState() {
    const trainButton = document.getElementById('trainModelBtn');
    const checkedBoxes = document.querySelectorAll('.sample-checkbox:checked');
    
    if (checkedBoxes.length > 0 && !isTraining) {
        trainButton.disabled = false;
    } else {
        trainButton.disabled = true;
    }
}

// Bắt đầu huấn luyện mô hình
async function startTraining() {
    // Lấy thông tin từ form
    const modelName = document.getElementById('model_name').value;
    const modelType = document.getElementById('model_type').value;
    const epochs = document.getElementById('epochs').value;
    
    // Kiểm tra thông tin
    if (!modelName) {
        alert('Vui lòng nhập tên mô hình');
        return;
    }
    
    // Lấy danh sách template đã chọn
    const checkedBoxes = document.querySelectorAll('.sample-checkbox:checked');
    if (checkedBoxes.length === 0) {
        alert('Vui lòng chọn ít nhất một ảnh mẫu');
        return;
    }
    
    const templateIds = Array.from(checkedBoxes).map(cb => cb.dataset.id);
    
    // Hiển thị modal
    const trainingModal = new bootstrap.Modal(document.getElementById('trainingModal'));
    trainingModal.show();
    
    // Gửi request API
    try {
        // Hiển thị trạng thái đang chuẩn bị
        document.getElementById('trainingStatus').textContent = 'Đang chuẩn bị...';
        document.getElementById('trainingProgress').style.width = '0%';
        document.getElementById('trainingProgress').textContent = '0%';
        
        const response = await fetch('/api/train-model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_name: modelName,
                model_type: modelType,
                epochs: parseInt(epochs || 100),
                template_ids: templateIds
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Lưu model ID
            modelId = data.model_id;
            document.getElementById('model_id').value = modelId;
            
            // Đánh dấu đang huấn luyện
            isTraining = true;
            
            // Cập nhật UI
            document.getElementById('trainingStatus').textContent = 'Đang khởi tạo...';
            document.getElementById('cancelTrainingBtn').style.display = 'inline-block';
            document.getElementById('finishTrainingBtn').style.display = 'none';
            
            // Bắt đầu kiểm tra trạng thái
            startStatusCheck();
        } else {
            // Hiển thị lỗi
            document.getElementById('trainingStatus').textContent = 'Lỗi: ' + data.message;
            document.getElementById('cancelTrainingBtn').style.display = 'none';
            document.getElementById('finishTrainingBtn').style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Lỗi:', error);
        document.getElementById('trainingStatus').textContent = 'Đã xảy ra lỗi kết nối';
        document.getElementById('cancelTrainingBtn').style.display = 'none';
        document.getElementById('finishTrainingBtn').style.display = 'inline-block';
    }
}

// Bắt đầu kiểm tra trạng thái định kỳ
function startStatusCheck() {
    // Xóa interval cũ nếu có
    if (statusInterval) {
        clearInterval(statusInterval);
    }
    
    // Tạo interval mới
    statusInterval = setInterval(checkTrainingStatus, 2000);
}

// Kiểm tra trạng thái huấn luyện
async function checkTrainingStatus() {
    if (!modelId || !isTraining) {
        clearInterval(statusInterval);
        return;
    }
    
    try {
        const response = await fetch(`/api/training-status/${modelId}`);
        const status = await response.json();
        
        // Cập nhật UI
        updateTrainingUI(status);
        
        // Kiểm tra nếu đã hoàn thành
        if (['completed', 'failed', 'cancelled'].includes(status.status)) {
            isTraining = false;
            clearInterval(statusInterval);
            
            if (status.status === 'completed') {
                // Bật nút Save
                document.getElementById('trained').value = 'true';
                document.getElementById('saveModelBtn').classList.remove('fade');
                document.getElementById('saveModelBtn').classList.add('show');
            }
        }
    } catch (error) {
        console.error('Lỗi kiểm tra trạng thái:', error);
    }
}

// Cập nhật UI theo trạng thái
function updateTrainingUI(status) {
    const statusText = document.getElementById('trainingStatus');
    const progressBar = document.getElementById('trainingProgress');
    const cancelBtn = document.getElementById('cancelTrainingBtn');
    const finishBtn = document.getElementById('finishTrainingBtn');
    
    // Cập nhật text
    let statusMessage = 'Đang huấn luyện...';
    
    switch(status.status) {
        case 'initializing':
            statusMessage = 'Đang khởi tạo...';
            break;
        case 'running':
            statusMessage = `Epoch ${status.current_epoch || 0}/${status.total_epochs || 0}`;
            break;
        case 'completed':
            statusMessage = 'Huấn luyện hoàn tất!';
            break;
        case 'failed':
            statusMessage = 'Huấn luyện thất bại: ' + (status.error || '');
            break;
        case 'cancelled':
            statusMessage = 'Huấn luyện đã bị hủy';
            break;
    }
    
    statusText.textContent = statusMessage;
    
    // Cập nhật progress bar
    if (progressBar) {
        // Tính progress
        let progress = 0;
        if (status.current_epoch && status.total_epochs) {
            progress = Math.round((status.current_epoch / status.total_epochs) * 100);
        }
        
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
    }
    
    // Cập nhật nút nhấn
    if (['completed', 'failed', 'cancelled'].includes(status.status)) {
        if (cancelBtn) cancelBtn.style.display = 'none';
        if (finishBtn) finishBtn.style.display = 'inline-block';
    } else {
        if (cancelBtn) cancelBtn.style.display = 'inline-block';
        if (finishBtn) finishBtn.style.display = 'none';
    }
}

// Hủy quá trình huấn luyện
async function cancelTraining() {
    if (!modelId) {
        console.error('Không có model ID để hủy huấn luyện');
        return;
    }
    
    try {
        // Disable nút khi đang gửi request
        const cancelBtn = document.getElementById('cancelTrainingBtn');
        if (cancelBtn) {
            cancelBtn.disabled = true;
            cancelBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Đang hủy...';
        }
        
        const response = await fetch(`/api/cancel-training/${modelId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        // Re-enable nút
        if (cancelBtn) {
            cancelBtn.disabled = false;
            cancelBtn.innerHTML = 'Hủy huấn luyện';
        }
        
        if (data.success) {
            // Cập nhật UI
            document.getElementById('trainingStatus').textContent = 'Huấn luyện đã bị hủy';
            document.getElementById('cancelTrainingBtn').style.display = 'none';
            document.getElementById('finishTrainingBtn').style.display = 'inline-block';
            
            isTraining = false;
            clearInterval(statusInterval);
        } else {
            // Hiển thị thông báo lỗi trong UI
            const errorMsg = data.message || 'Không thể hủy huấn luyện';
            alert(`Lỗi: ${errorMsg}`);
            
            // Kiểm tra trạng thái lần nữa để cập nhật UI
            checkTrainingStatus();
        }
    } catch (error) {
        console.error('Lỗi khi gửi request hủy huấn luyện:', error);
        alert('Đã xảy ra lỗi khi hủy huấn luyện');
        
        // Re-enable nút
        const cancelBtn = document.getElementById('cancelTrainingBtn');
        if (cancelBtn) {
            cancelBtn.disabled = false;
            cancelBtn.innerHTML = 'Hủy huấn luyện';
        }
    }
}

// Hoàn tất và đóng modal
function finishTraining() {
    const trainingModal = bootstrap.Modal.getInstance(document.getElementById('trainingModal'));
    if (trainingModal) {
        trainingModal.hide();
    }
    
    // Cập nhật trạng thái nút
    updateTrainButtonState();
}