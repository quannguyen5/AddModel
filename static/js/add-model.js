document.addEventListener("DOMContentLoaded", function () {
  const sampleCheckboxes = document.querySelectorAll(".sample-checkbox");
  const trainModelBtn = document.getElementById("trainModelBtn");
  const saveModelBtn = document.getElementById("saveModelBtn");
  const modelNameInput = document.getElementById("model_name");
  const modelTypeSelect = document.getElementById("model_type");
  const versionInput = document.getElementById("version");
  const trainingModal = document.getElementById("trainingModal");

  // Progress monitoring
  let trainingTimer;
  let modelId;

  // Kiểm tra khi checkbox thay đổi
  sampleCheckboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", checkTrainButtonState);
  });

  // Kiểm tra khi tên model thay đổi
  if (modelNameInput) {
    modelNameInput.addEventListener("input", checkTrainButtonState);
  }

  // Kiểm tra khi loại model thay đổi
  if (modelTypeSelect) {
    modelTypeSelect.addEventListener("change", checkTrainButtonState);
  }

  // Kiểm tra khi version thay đổi
  if (versionInput) {
    versionInput.addEventListener("input", checkTrainButtonState);
  }

  // Kiểm tra trạng thái nút Train
  function checkTrainButtonState() {
    const anyChecked = Array.from(sampleCheckboxes).some((cb) => cb.checked);
    const hasModelName = modelNameInput && modelNameInput.value.trim() !== "";
    const hasModelType = modelTypeSelect && modelTypeSelect.value !== "";
    const hasVersion = versionInput && versionInput.value.trim() !== "";

    if (trainModelBtn) {
      trainModelBtn.disabled = !(
        anyChecked &&
        hasModelName &&
        hasModelType &&
        hasVersion
      );
    }
  }

  // Kích hoạt ngay khi trang tải xong
  checkTrainButtonState();

  // Xử lý sự kiện nút Train
  if (trainModelBtn) {
    trainModelBtn.addEventListener("click", function () {
      startTraining();
    });
  }

  // Xử lý sự kiện nút Cancel Training
  const cancelTrainingBtn = document.getElementById("cancelTrainingBtn");
  if (cancelTrainingBtn) {
    cancelTrainingBtn.addEventListener("click", function () {
      // Check if training is completed or failed
      const currentStatus =
        document.getElementById("trainingStatus").textContent;
      if (
        currentStatus.includes("hoàn thành") ||
        currentStatus.includes("thất bại") ||
        currentStatus.includes("hủy")
      ) {
        // Just close the modal
        const modalInstance = bootstrap.Modal.getInstance(trainingModal);
        if (modalInstance) {
          modalInstance.hide();
        }
      } else {
        // Try to cancel training
        cancelTraining();
      }
    });
  }
  if (saveModelBtn) {
    saveModelBtn.addEventListener("click", function () {
      // Disable button
      saveModelBtn.disabled = true;
      saveModelBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Đang lưu...';

      // Lấy các giá trị cần thiết
      const modelName = modelNameInput ? modelNameInput.value.trim() : "";
      const modelType = modelTypeSelect ? modelTypeSelect.value : "";
      const version = versionInput ? versionInput.value.trim() : "";
      const description = document.getElementById("description")
        ? document.getElementById("description").value.trim()
        : "";

      // Validation
      if (!modelName || !modelType || !version) {
        alert(
          "Vui lòng điền đầy đủ thông tin bắt buộc (tên mô hình, loại mô hình, version)"
        );
        saveModelBtn.disabled = false;
        saveModelBtn.innerHTML = '<i class="fas fa-save"></i> Lưu mô hình';
        return;
      }

      // Lấy danh sách template đã chọn
      const selectedTemplates = [];
      sampleCheckboxes.forEach((checkbox) => {
        if (checkbox.checked) {
          selectedTemplates.push(checkbox.dataset.id);
        }
      });

      // Sử dụng fetch API với mode redirect
      fetch("/add-model", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model_id: modelId,
          model_name: modelName,
          model_type: modelType,
          version: version,
          description: description,
          template_ids: selectedTemplates,
          epochs: document.getElementById("epochs")
            ? parseInt(document.getElementById("epochs").value)
            : 100,
          batch_size: document.getElementById("batch_size")
            ? parseInt(document.getElementById("batch_size").value)
            : 16,
          image_size: document.getElementById("image_size")
            ? parseInt(document.getElementById("image_size").value)
            : 640,
          learning_rate: document.getElementById("learning_rate")
            ? parseFloat(document.getElementById("learning_rate").value)
            : 0.001,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Chuyển hướng với tham số thông báo
            window.location.href = `/model-management?success=true&model=${encodeURIComponent(
              modelName
            )}`;
          } else {
            alert(data.message || "Có lỗi xảy ra khi lưu mô hình");
            saveModelBtn.disabled = false;
            saveModelBtn.innerHTML = '<i class="fas fa-save"></i> Lưu mô hình';
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("Đã xảy ra lỗi khi lưu mô hình. Vui lòng thử lại.");
          saveModelBtn.disabled = false;
          saveModelBtn.innerHTML = '<i class="fas fa-save"></i> Lưu mô hình';
        });
    });
  }

  // Xử lý sự kiện nút Finish (sau khi hoàn thành)
  const finishTrainingBtn = document.getElementById("finishTrainingBtn");
  if (finishTrainingBtn) {
    finishTrainingBtn.addEventListener("click", function () {
      // Hide modal using Bootstrap 5 modal instance
      const modalInstance = bootstrap.Modal.getInstance(trainingModal);
      if (modalInstance) {
        modalInstance.hide();
      }

      // Hiển thị nút Save và form lưu model
      if (saveModelBtn) {
        saveModelBtn.classList.remove("fade");
        saveModelBtn.classList.add("show");
      }

      // Thêm model_id vào form
      const modelIdInput = document.getElementById("model_id");
      if (modelIdInput) {
        modelIdInput.value = modelId;
      }

      // Cập nhật trạng thái huấn luyện
      const trainedInput = document.getElementById("trained");
      const trainingSuccessInput = document.getElementById("training_success");
      const accuracyInput = document.getElementById("accuracy"); // Thêm input accuracy

      if (trainedInput) trainedInput.value = "true";
      if (trainingSuccessInput) trainingSuccessInput.value = "true";

      // Cập nhật giá trị accuracy nếu có
      if (accuracyInput) {
        const accuracyElem = document.getElementById("metricAccuracy");
        const map50Elem = document.getElementById("metricMap50");

        // Ưu tiên sử dụng accuracy nếu có
        if (
          accuracyElem &&
          accuracyElem.textContent &&
          accuracyElem.textContent !== "-"
        ) {
          const accuracy =
            parseFloat(accuracyElem.textContent.replace("%", "")) / 100;
          accuracyInput.value = accuracy.toString();
        }
        // Nếu không có accuracy, dùng mAP50
        else if (
          map50Elem &&
          map50Elem.textContent &&
          map50Elem.textContent !== "-"
        ) {
          const accuracy =
            parseFloat(map50Elem.textContent.replace("%", "")) / 100;
          accuracyInput.value = accuracy.toString();
        } else {
          // Giá trị mặc định nếu không có thông số
          accuracyInput.value = "0.75";
        }
      }
    });
  }

  // Hàm bắt đầu huấn luyện
  function startTraining() {
    // Lấy các thông số huấn luyện
    const modelName = modelNameInput ? modelNameInput.value : "";
    const modelType = modelTypeSelect ? modelTypeSelect.value : "";
    const version = versionInput ? versionInput.value : "";
    const epochs = document.getElementById("epochs")
      ? parseInt(document.getElementById("epochs").value)
      : 100;
    const batchSize = document.getElementById("batch_size")
      ? parseInt(document.getElementById("batch_size").value)
      : 16;
    const imageSize = document.getElementById("image_size")
      ? parseInt(document.getElementById("image_size").value)
      : 640;
    const learningRate = document.getElementById("learning_rate")
      ? parseFloat(document.getElementById("learning_rate").value)
      : 0.001;

    // Lấy danh sách template đã chọn
    const selectedTemplates = [];
    sampleCheckboxes.forEach((checkbox) => {
      if (checkbox.checked) {
        selectedTemplates.push(checkbox.dataset.id);
      }
    });

    // Hiển thị modal huấn luyện using Bootstrap 5
    const bsTrainingModal = new bootstrap.Modal(trainingModal);
    bsTrainingModal.show();

    document.getElementById("trainingStatus").textContent = "Đang khởi tạo...";
    document.getElementById("trainingProgress").style.width = "0%";
    document.getElementById("trainingProgress").textContent = "0%";

    // Show spinner and hide result
    const spinner = document.getElementById("trainingSpinner");
    const resultSection = document.getElementById("trainingResult");
    if (spinner) spinner.style.display = "inline-block";
    if (resultSection) resultSection.style.display = "none";

    // Change button text back
    if (cancelTrainingBtn) {
      cancelTrainingBtn.textContent = "Hủy huấn luyện";
      cancelTrainingBtn.style.display = "block";
    }
    if (finishTrainingBtn) {
      finishTrainingBtn.style.display = "none";
    }

    // Gửi request tới API để bắt đầu huấn luyện
    fetch("/api/train-model", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model_name: modelName,
        model_type: modelType,
        version: version,
        template_ids: selectedTemplates,
        epochs: epochs,
        batch_size: batchSize,
        image_size: imageSize,
        learning_rate: learningRate,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          // Lưu model ID cho việc theo dõi
          modelId = data.model_id;

          // Bắt đầu kiểm tra trạng thái
          startStatusMonitoring(modelId);
        } else {
          alert("Lỗi khi bắt đầu huấn luyện: " + data.message);
          const modalInstance = bootstrap.Modal.getInstance(trainingModal);
          if (modalInstance) {
            modalInstance.hide();
          }
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Đã xảy ra lỗi khi gửi yêu cầu huấn luyện.");
        const modalInstance = bootstrap.Modal.getInstance(trainingModal);
        if (modalInstance) {
          modalInstance.hide();
        }
      });
  }

  // Hàm theo dõi trạng thái huấn luyện
  function startStatusMonitoring(modelId) {
    // Hủy timer cũ nếu có
    if (trainingTimer) {
      clearInterval(trainingTimer);
    }

    // Tạo timer mới để kiểm tra trạng thái
    trainingTimer = setInterval(() => {
      checkTrainingStatus(modelId);
    }, 2000); // Kiểm tra mỗi 2 giây
  }

  // Hàm kiểm tra trạng thái huấn luyện - Đơn giản hóa
  function checkTrainingStatus(modelId) {
    fetch(`/api/training-status/${modelId}`)
      .then((response) => response.json())
      .then((data) => {
        console.log("Training status update:", data);

        // Cập nhật tiến trình
        updateProgressBar(data);

        // Kiểm tra trạng thái huấn luyện
        if (data.status === "completed") {
          clearInterval(trainingTimer);
          // Hiển thị kết quả huấn luyện
          showTrainingCompleted(data);
        } else if (data.status === "failed") {
          clearInterval(trainingTimer);
          showTrainingFailed(data);
        } else if (data.status === "cancelled") {
          clearInterval(trainingTimer);
          showTrainingCancelled();
        }
      })
      .catch((error) => {
        console.error("Error checking training status:", error);
      });
  }

  // Cập nhật thanh tiến trình
  function updateProgressBar(data) {
    // Cập nhật tiêu đề trạng thái
    let statusText;
    switch (data.status) {
      case "initializing":
        statusText = "Đang khởi tạo...";
        break;
      case "preparing_data":
        statusText = "Đang chuẩn bị dữ liệu...";
        break;
      case "running":
        statusText =
          data.current_epoch > 0
            ? `Đang huấn luyện: Epoch ${data.current_epoch}/${data.total_epochs}`
            : "Đang khởi động huấn luyện...";
        break;
      case "completed":
        statusText = "Huấn luyện đã hoàn thành!";
        break;
      case "failed":
        statusText =
          "Huấn luyện thất bại: " + (data.error || "Lỗi không xác định");
        break;
      case "cancelled":
        statusText = "Huấn luyện đã bị hủy";
        break;
      default:
        statusText = `Trạng thái: ${data.status}`;
    }
    document.getElementById("trainingStatus").textContent = statusText;

    // Cập nhật thanh tiến trình
    if (data.total_epochs > 0) {
      let progress = 0;
      if (data.current_epoch > 0) {
        progress = (data.current_epoch / data.total_epochs) * 100;
      } else if (data.status === "running") {
        progress = 10; // Giá trị mặc định khi đang chạy nhưng chưa có epoch
      }

      document.getElementById("trainingProgress").style.width = `${progress}%`;
      document.getElementById("trainingProgress").textContent = `${Math.round(
        progress
      )}%`;
    }
  }

  // Hiển thị khi huấn luyện hoàn thành
  function showTrainingCompleted(data) {
    // Ẩn spinner
    const spinner = document.getElementById("trainingSpinner");
    if (spinner) spinner.style.display = "none";

    // Cập nhật trạng thái
    document.getElementById("trainingStatus").textContent =
      "Huấn luyện đã hoàn thành!";
    document.getElementById("trainingProgress").style.width = "100%";
    document.getElementById("trainingProgress").textContent = "100%";

    // Hiển thị kết quả
    const resultSection = document.getElementById("trainingResult");
    if (resultSection) {
      resultSection.style.display = "block";

      // Hiệu suất mô hình
      updateMetrics(data);
    }

    // Cập nhật trạng thái nút
    document.getElementById("cancelTrainingBtn").style.display = "none";
    document.getElementById("finishTrainingBtn").style.display = "block";

    // Cập nhật giá trị cho form
    document.getElementById("model_path").value = data.model_path || "";
  }

  // Cập nhật tất cả các thông số
  function updateMetrics(data) {
    console.log("Updating metrics with data:", data);

    // Đường dẫn mô hình
    const modelPathElement = document.getElementById("modelPath");
    if (modelPathElement && data.model_path) {
      modelPathElement.textContent = data.model_path;
    }

    // Lấy metrics từ final_metrics nếu có
    let metrics = data.final_metrics || {};

    // Hiển thị các chỉ số
    if (metrics) {
      if (metrics.map50 !== undefined) {
        setElementText("metricMap50", (metrics.map50 * 100).toFixed(2) + "%");
      }

      if (metrics.map50_95 !== undefined) {
        setElementText(
          "metricMap5095",
          (metrics.map50_95 * 100).toFixed(2) + "%"
        );
      }

      if (metrics.precision !== undefined) {
        setElementText(
          "metricPrecision",
          (metrics.precision * 100).toFixed(2) + "%"
        );
      }

      if (metrics.recall !== undefined) {
        setElementText("metricRecall", (metrics.recall * 100).toFixed(2) + "%");
      }

      if (metrics.accuracy !== undefined) {
        setElementText(
          "metricAccuracy",
          (metrics.accuracy * 100).toFixed(2) + "%"
        );
      }

      if (metrics.f1_score !== undefined) {
        setElementText(
          "metricF1Score",
          (metrics.f1_score * 100).toFixed(2) + "%"
        );
      }
    }

    // Hiển thị thông tin dataset
    const datasetInfo = data.dataset_info || {};
    setElementText("datasetTotalImages", datasetInfo.total_images || "-");
    setElementText("datasetTrainImages", datasetInfo.train_images || "-");
    setElementText("datasetValImages", datasetInfo.val_images || "-");

    // Tính thời gian huấn luyện
    let duration = "-";
    if (data.start_time && data.end_time) {
      try {
        const startTime = new Date(data.start_time);
        const endTime = new Date(data.end_time);
        const durationMs = endTime - startTime;

        // Format thời gian
        const minutes = Math.floor(durationMs / (1000 * 60));
        const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);
        duration = `${minutes} phút ${seconds} giây`;
      } catch (error) {
        console.error("Error calculating duration:", error);
        duration = "Không xác định";
      }
    }

    setElementText("trainingDuration", duration);
  }

  // Tiện ích để cập nhật nội dung
  function setElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) element.textContent = text;
  }

  // Hiển thị khi huấn luyện thất bại
  function showTrainingFailed(data) {
    // Ẩn spinner
    const spinner = document.getElementById("trainingSpinner");
    if (spinner) spinner.style.display = "none";

    // Cập nhật trạng thái
    document.getElementById("trainingStatus").textContent =
      "Huấn luyện thất bại: " + (data.error || "Lỗi không xác định");

    // Cập nhật nút
    document.getElementById("cancelTrainingBtn").textContent = "Đóng";
  }

  // Hiển thị khi huấn luyện bị hủy
  function showTrainingCancelled() {
    // Ẩn spinner
    const spinner = document.getElementById("trainingSpinner");
    if (spinner) spinner.style.display = "none";

    // Cập nhật trạng thái
    document.getElementById("trainingStatus").textContent =
      "Huấn luyện đã bị hủy";

    // Cập nhật nút
    document.getElementById("cancelTrainingBtn").textContent = "Đóng";
  }

  // Hàm hủy huấn luyện
  function cancelTraining() {
    if (!modelId) return;

    // Disable cancel button to prevent multiple clicks
    const cancelBtn = document.getElementById("cancelTrainingBtn");
    if (cancelBtn) {
      cancelBtn.disabled = true;
      cancelBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Đang hủy...';
    }

    fetch(`/api/cancel-training/${modelId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          document.getElementById("trainingStatus").textContent =
            "Đang hủy huấn luyện...";

          // Re-enable button after 3 seconds
          setTimeout(() => {
            if (cancelBtn) {
              cancelBtn.disabled = false;
              cancelBtn.innerHTML = "Hủy huấn luyện";
            }
          }, 3000);
        } else {
          alert("Không thể hủy huấn luyện: " + data.message);
          if (cancelBtn) {
            cancelBtn.disabled = false;
            cancelBtn.innerHTML = "Hủy huấn luyện";
          }
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("Đã xảy ra lỗi khi hủy huấn luyện.");
        if (cancelBtn) {
          cancelBtn.disabled = false;
          cancelBtn.innerHTML = "Hủy huấn luyện";
        }
      });
  }
});
