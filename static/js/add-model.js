/**
 * JavaScript dành cho trang Thêm mô hình mới
 * Xử lý các tính năng huấn luyện, theo dõi training, tải và lưu mô hình
 */

document.addEventListener("DOMContentLoaded", function () {
  // Biến lưu trạng thái huấn luyện
  let modelId = null;
  let trainingActive = false;
  let checkStatusInterval = null;

  // Modal huấn luyện
  const trainingModal = new bootstrap.Modal(
    document.getElementById("trainingModal")
  );

  // ========== XỬ LÝ CHỌN TEMPLATES ==========

  // Kiểm tra checkbox mẫu để enable/disable nút huấn luyện
  function updateTrainButton() {
    const hasSelectedTemplates =
      document.querySelectorAll(".sample-checkbox:checked").length > 0;
    document.getElementById("trainModelBtn").disabled = !hasSelectedTemplates;
  }

  // Lắng nghe sự kiện thay đổi checkbox
  document.querySelectorAll(".sample-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", updateTrainButton);
  });

  // Kiểm tra ban đầu
  updateTrainButton();

  // ========== XỬ LÝ NÚT HUẤN LUYỆN ==========

  document
    .getElementById("trainModelBtn")
    .addEventListener("click", function () {
      // Reset trạng thái
      modelId = null;
      trainingActive = true;

      // Xóa interval cũ nếu có
      if (checkStatusInterval) {
        clearInterval(checkStatusInterval);
      }

      // Reset UI về trạng thái ban đầu
      resetTrainingUI();

      // Hiển thị modal huấn luyện
      trainingModal.show();

      // Lấy các tham số từ form
      const modelName = document.getElementById("model_name").value;
      const modelType = document.getElementById("model_type").value;
      const version = document.getElementById("version").value;
      const epochs = document.getElementById("epochs").value;
      const batchSize = document.getElementById("batch_size").value;
      const learningRate = document.getElementById("learning_rate").value;
      const imageSize = document.getElementById("image_size").value;

      // Lấy các template được chọn
      const selectedTemplates = [];
      document
        .querySelectorAll(".sample-checkbox:checked")
        .forEach((checkbox) => {
          selectedTemplates.push(checkbox.dataset.id);
        });

      // Kiểm tra thông tin cần thiết
      if (!modelName || !modelType || !version) {
        alert("Vui lòng nhập đầy đủ thông tin mô hình!");
        trainingModal.hide();
        return false;
      }

      if (selectedTemplates.length === 0) {
        alert("Vui lòng chọn ít nhất một mẫu dữ liệu huấn luyện!");
        trainingModal.hide();
        return false;
      }

      // Gửi yêu cầu huấn luyện đến API
      fetch("/api/train-model", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_name: modelName,
          model_type: modelType,
          version: version,
          epochs: parseInt(epochs),
          batch_size: parseInt(batchSize),
          learning_rate: parseFloat(learningRate),
          image_size: parseInt(imageSize),
          template_ids: selectedTemplates,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            modelId = data.model_id;
            console.log("Bắt đầu huấn luyện mô hình ID:", modelId);

            // Cập nhật trạng thái form
            document.getElementById("trained").value = "false";
            document.getElementById("training_success").value = "false";

            // Lưu model ID vào trường ẩn để sử dụng sau này
            if (document.getElementById("modelId")) {
              document.getElementById("modelId").value = modelId;
            }

            // Bắt đầu kiểm tra trạng thái ngay lập tức
            checkTrainingStatus();

            // Kiểm tra trạng thái mỗi 3 giây để hiển thị tiến trình
            checkStatusInterval = setInterval(checkTrainingStatus, 3000);
          } else {
            showTrainingError(data.message || "Lỗi khi bắt đầu huấn luyện");
            trainingActive = false;
          }
        })
        .catch((error) => {
          console.error("Lỗi khi gửi yêu cầu huấn luyện:", error);
          showTrainingError("Lỗi kết nối với máy chủ. Vui lòng thử lại sau.");
        });

      return true;
    });

  // ========== HÀM KIỂM TRA TRẠNG THÁI HUẤN LUYỆN ==========

  function checkTrainingStatus() {
    if (!modelId || !trainingActive) return;

    console.log("Kiểm tra trạng thái huấn luyện cho mô hình ID:", modelId);

    fetch(`/api/training_status/${modelId}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("Trạng thái huấn luyện:", data);

        // Cập nhật UI dựa trên trạng thái huấn luyện
        updateTrainingUI(data);

        // Kiểm tra nếu huấn luyện đã kết thúc
        if (
          data.status === "completed" ||
          data.status === "failed" ||
          data.status === "cancelled" ||
          data.status === "not_found" // Trường hợp không tìm thấy trạng thái huấn luyện
        ) {
          clearInterval(checkStatusInterval);
          checkStatusInterval = null;

          if (data.status === "completed") {
            handleTrainingCompleted(data);
          } else if (data.status === "failed") {
            handleTrainingFailed(data);
          } else if (data.status === "cancelled") {
            handleTrainingCancelled();
          } else if (data.status === "not_found") {
            // Xử lý trường hợp không tìm thấy trạng thái huấn luyện
            showTrainingError(
              "Không tìm thấy thông tin huấn luyện. Quá trình có thể đã kết thúc hoặc bị hủy."
            );
          }
        }
      })
      .catch((error) => {
        console.error("Lỗi khi kiểm tra trạng thái:", error);
        showTrainingError(
          "Lỗi khi kiểm tra trạng thái huấn luyện: " + error.message
        );
      });
  }

  // ========== CẬP NHẬT UI THEO TRẠNG THÁI HUẤN LUYỆN ==========

  // Reset UI về trạng thái ban đầu
  function resetTrainingUI() {
    // Khôi phục hiển thị spinner
    document.querySelector(".spinner-border").style.display = "";

    // Reset tiêu đề và thông báo
    document.querySelector(".modal-body h5").textContent = "Đang huấn luyện...";

    // Reset alert về trạng thái info ban đầu
    const alertElement = document.querySelector(".modal-body .alert");
    alertElement.className = "alert alert-info mt-3";
    alertElement.innerHTML =
      "Hệ thống đang huấn luyện mô hình. Quá trình này sẽ tự động diễn ra. Vui lòng không đóng trang cho đến khi hoàn tất.";

    // Xóa thông tin epoch cũ nếu có
    const existingEpochInfo = document.querySelector(".modal-body .epoch-info");
    if (existingEpochInfo) {
      existingEpochInfo.remove();
    }

    // Xóa bảng kết quả cũ nếu có
    const existingResults = document.querySelector(
      ".modal-body .training-results"
    );
    if (existingResults) {
      existingResults.remove();
    }

    // Reset trạng thái các nút
    document.getElementById("cancelTrainingBtn").textContent = "Hủy huấn luyện";
    document.getElementById("cancelTrainingBtn").style.display = "inline-block";
    document.getElementById("finishTrainingBtn").style.display = "none";

    // Reset trạng thái nút lưu mô hình
    document.getElementById("saveModelBtn").innerHTML =
      '<i class="fas fa-save"></i> Lưu mô hình';
    document.getElementById("saveModelBtn").classList.add("fade");
  }

  // Cập nhật UI dựa trên trạng thái huấn luyện
  function updateTrainingUI(data) {
    // Lấy thông tin trạng thái
    const status = data.status;
    const currentEpoch = data.current_epoch || 0;
    const totalEpochs = data.total_epochs || 0;
    const progress = data.progress || 0;

    // Cập nhật text trạng thái
    let statusText = "Đang huấn luyện...";
    if (status === "initializing") {
      statusText = "Đang khởi tạo...";
    } else if (status === "preparing_dataset") {
      statusText = "Đang chuẩn bị dữ liệu...";
    } else if (status === "dataset_created") {
      statusText = "Đã tạo dataset, đang chuẩn bị huấn luyện...";
    } else if (status === "training") {
      // Thêm thông tin metrics nếu có
      let metricsText = "";
      if (data.metrics && Object.keys(data.metrics).length > 0) {
        const mAP = (data.metrics["mAP50(B)"] || 0).toFixed(3);
        const loss = (data.metrics["loss"] || 0).toFixed(3);
        metricsText = ` (mAP: ${mAP}, Loss: ${loss})`;
      }

      statusText = `Đang huấn luyện... Epoch ${currentEpoch}/${totalEpochs}${metricsText}`;
    } else if (status === "exporting") {
      statusText = "Đang xuất mô hình...";
    } else if (status === "completed") {
      statusText = "Huấn luyện hoàn tất!";
    } else if (status === "not_found") {
      statusText = "Không tìm thấy thông tin huấn luyện";
    }

    // Hiển thị trạng thái
    document.querySelector(".modal-body h5").textContent = statusText;

    // Hiển thị thông tin epoch
    let epochInfo = document.querySelector(".modal-body .epoch-info");
    if (!epochInfo && totalEpochs > 0) {
      const epochHTML = `
                <div class="text-center mt-3 epoch-info">
                    <h5>Tiến trình huấn luyện</h5>
                    <div class="progress mb-3">
                        <div class="progress-bar bg-primary" role="progressbar" style="width: ${progress}%" 
                            aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100">
                            ${Math.round(progress)}%
                        </div>
                    </div>
                </div>
            `;
      document
        .querySelector(".modal-body .alert")
        .insertAdjacentHTML("beforebegin", epochHTML);
    } else if (epochInfo) {
      // Cập nhật thông tin epoch hiện có
      const progressBar = epochInfo.querySelector(".progress-bar");

      if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute("aria-valuenow", progress);
        progressBar.textContent = `${Math.round(progress)}%`;
      }
    }
  }

  // ========== XỬ LÝ KẾT QUẢ HUẤN LUYỆN ==========

  // Xử lý khi huấn luyện hoàn tất
  function handleTrainingCompleted(data) {
    // Đánh dấu là hoàn tất và dừng kiểm tra
    trainingActive = false;

    // Cập nhật trường hidden
    document.getElementById("trained").value = "true";
    document.getElementById("training_success").value = "true";

    // Nếu có model_path, cập nhật vào form
    if (data.model_path) {
      document.getElementById("model_path").value = data.model_path;
    }

    // Cập nhật accuracy nếu có
    if (data.accuracy || (data.metrics && data.metrics["mAP50(B)"])) {
      const accuracy = data.accuracy || data.metrics["mAP50(B)"];
      document.getElementById("accuracy").value = accuracy;
    }

    // Hiển thị nút hoàn tất
    document.getElementById("finishTrainingBtn").style.display = "inline-block";
    document.getElementById("cancelTrainingBtn").style.display = "none";

    // Cập nhật thông báo
    document.querySelector(".modal-body h5").textContent =
      "Huấn luyện đã hoàn tất!";
    document.querySelector(".alert-info").className =
      "alert alert-success mt-3";
    document.querySelector(".alert-success").innerHTML =
      '<i class="fas fa-check-circle"></i> Mô hình đã được huấn luyện thành công! Bạn có thể lưu mô hình này.';
    document.querySelector(".spinner-border").style.display = "none";

    // Hiển thị bảng thông số kết quả
    displayTrainingResults(data);

    // Cập nhật nút lưu mô hình
    document.getElementById("saveModelBtn").innerHTML =
      '<i class="fas fa-save"></i> Lưu mô hình đã huấn luyện';
    document.getElementById("saveModelBtn").classList.remove("fade");
  }

  // Hiển thị bảng kết quả chi tiết
  function displayTrainingResults(data) {
    // Lấy metrics từ dữ liệu
    const accuracy =
      data.accuracy || (data.metrics && data.metrics["mAP50(B)"]) || 0;
    const precision = (data.metrics && data.metrics["precision(B)"]) || 0;
    const recall = (data.metrics && data.metrics["recall(B)"]) || 0;

    // Tính duration từ start_time và end_time nếu có
    let duration = data.duration || 0;
    if (!duration && data.start_time && data.end_time) {
      const startTime = new Date(data.start_time);
      const endTime = new Date(data.end_time);
      duration = (endTime - startTime) / 1000; // Convert to seconds
    }

    const epochs = data.total_epochs || 0;

    const resultsHTML = `
            <div class="training-results mt-4">
                <h6>Kết quả huấn luyện:</h6>
                <table class="table table-sm table-bordered">
                    <tbody>
                        <tr>
                            <th>Độ chính xác (mAP50)</th>
                            <td>${(accuracy * 100).toFixed(2)}%</td>
                        </tr>
                        <tr>
                            <th>Precision</th>
                            <td>${(precision * 100).toFixed(2)}%</td>
                        </tr>
                        <tr>
                            <th>Recall</th>
                            <td>${(recall * 100).toFixed(2)}%</td>
                        </tr>
                        <tr>
                            <th>Thời gian huấn luyện</th>
                            <td>${Math.round(duration)} giây</td>
                        </tr>
                        <tr>
                            <th>Số epoch</th>
                            <td>${epochs}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;

    // Thêm bảng kết quả vào modal
    const existingResults = document.querySelector(
      ".modal-body .training-results"
    );
    if (!existingResults) {
      document
        .querySelector(".modal-body")
        .insertAdjacentHTML("beforeend", resultsHTML);
    }
  }

  // Xử lý khi huấn luyện thất bại
  function handleTrainingFailed(data) {
    // Đánh dấu là đã dừng
    trainingActive = false;

    // Hiển thị thông báo lỗi
    document.querySelector(".modal-body h5").textContent =
      "Huấn luyện thất bại!";

    const alertElement = document.querySelector(".modal-body .alert");
    alertElement.className = "alert alert-danger mt-3";

    // Hiển thị thông tin lỗi chi tiết nếu có
    let errorMessage = data.error || "Lỗi không xác định";
    if (data.traceback) {
      errorMessage += `<details>
        <summary>Chi tiết lỗi</summary>
        <pre class="text-start" style="max-height: 200px; overflow: auto;">${data.traceback}</pre>
      </details>`;
    }

    alertElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> Có lỗi xảy ra trong quá trình huấn luyện: ${errorMessage}`;
    document.querySelector(".spinner-border").style.display = "none";

    // Đổi nút hủy thành nút đóng
    document.getElementById("cancelTrainingBtn").textContent = "Đóng";
  }

  // Xử lý khi huấn luyện bị hủy
  function handleTrainingCancelled() {
    // Đánh dấu là đã dừng
    trainingActive = false;

    // Cập nhật UI
    document.querySelector(".modal-body h5").textContent =
      "Huấn luyện đã bị hủy!";

    const alertElement = document.querySelector(".modal-body .alert");
    alertElement.className = "alert alert-warning mt-3";
    alertElement.innerHTML =
      '<i class="fas fa-exclamation-triangle"></i> Quá trình huấn luyện đã bị hủy bỏ.';

    document.querySelector(".spinner-border").style.display = "none";

    // Đổi nút hủy thành nút đóng
    document.getElementById("cancelTrainingBtn").textContent = "Đóng";
  }

  // Hiển thị lỗi huấn luyện
  function showTrainingError(errorMessage) {
    document.querySelector(".modal-body h5").textContent =
      "Lỗi khởi tạo huấn luyện!";

    const alertElement = document.querySelector(".modal-body .alert");
    alertElement.className = "alert alert-danger mt-3";
    alertElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${errorMessage}`;

    document.querySelector(".spinner-border").style.display = "none";
    document.getElementById("cancelTrainingBtn").textContent = "Đóng";
  }

  // ========== XỬ LÝ CÁC NÚT THAO TÁC ==========

  // Xử lý nút hủy/đóng
  document
    .getElementById("cancelTrainingBtn")
    .addEventListener("click", function () {
      if (this.textContent === "Đóng") {
        trainingModal.hide();
        return;
      }

      if (confirm("Bạn có chắc chắn muốn hủy quá trình huấn luyện không?")) {
        // Đánh dấu là đang hủy
        trainingActive = false;

        // Gửi yêu cầu hủy và hiển thị thông báo đang hủy
        const alertElement = document.querySelector(".modal-body .alert");
        alertElement.className = "alert alert-warning mt-3";
        alertElement.innerHTML =
          '<i class="fas fa-spinner fa-spin"></i> Đang hủy quá trình huấn luyện...';

        fetch(`/api/cancel_training/${modelId}`, {
          method: "POST",
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              if (checkStatusInterval) {
                clearInterval(checkStatusInterval);
                checkStatusInterval = null;
              }
              handleTrainingCancelled();
            } else {
              alertElement.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${
                data.message || "Không thể hủy huấn luyện."
              }`;
            }
          })
          .catch((error) => {
            console.error("Lỗi khi hủy huấn luyện:", error);
            alertElement.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Lỗi khi hủy huấn luyện: ${error.message}`;
          });
      }
    });

  // Xử lý nút hoàn tất
  document
    .getElementById("finishTrainingBtn")
    .addEventListener("click", function () {
      trainingModal.hide();

      // Hiển thị nút lưu mô hình rõ ràng
      document.getElementById("saveModelBtn").classList.remove("fade");
    });

  // Xử lý nút lưu mô hình
  document
    .getElementById("saveModelBtn")
    .addEventListener("click", function (e) {
      // Chỉ xử lý đặc biệt nếu đã huấn luyện thành công
      if (
        document.getElementById("trained").value === "true" &&
        document.getElementById("training_success").value === "true"
      ) {
        e.preventDefault();

        // Hiển thị thông báo đang tải
        const saveAlert = document.createElement("div");
        saveAlert.classList.add("alert", "alert-info", "save-alert");
        saveAlert.innerHTML =
          '<i class="fas fa-spinner fa-spin"></i> Đang tải mô hình để lưu...';
        document.body.appendChild(saveAlert);

        // Lấy modelId từ trường ẩn
        const modelId = document.getElementById("modelId").value;

        // Lưu model vào database trực tiếp (không cần tải từ Kaggle nữa)
        fetch(`/api/save_trained_model/${modelId}`, {
          method: "POST",
        })
          .then((response) => response.json())
          .then((saveData) => {
            if (saveData.success) {
              // Thay đổi thông báo thành công
              saveAlert.classList.remove("alert-info");
              saveAlert.classList.add("alert-success");
              saveAlert.innerHTML =
                '<i class="fas fa-check-circle"></i> Đã lưu mô hình thành công! Đang chuyển hướng...';

              // Chuyển hướng đến trang quản lý mô hình
              setTimeout(() => {
                window.location.href = "/model-management?saved=true";
              }, 1500);
            } else {
              saveAlert.classList.remove("alert-info");
              saveAlert.classList.add("alert-danger");
              saveAlert.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${
                saveData.message || "Không thể lưu thông tin mô hình"
              }`;
              setTimeout(() => saveAlert.remove(), 5000);
            }
          })
          .catch((error) => {
            console.error("Lỗi:", error);
            saveAlert.classList.remove("alert-info");
            saveAlert.classList.add("alert-danger");
            saveAlert.innerHTML =
              '<i class="fas fa-exclamation-circle"></i> ' + error.message;
            setTimeout(() => saveAlert.remove(), 5000);
          });
      }
    });
});
