document.addEventListener("DOMContentLoaded", function () {
  // Kích hoạt nút Train khi chọn ít nhất một ảnh mẫu
  const sampleCheckboxes = document.querySelectorAll(".sample-checkbox");
  const trainModelBtn = document.getElementById("trainModelBtn");
  const saveModelBtn = document.getElementById("saveModelBtn");
  const modelNameInput = document.getElementById("model_name");
  const modelTypeSelect = document.getElementById("model_type");
  const versionInput = document.getElementById("version");
  const addModelForm = document.getElementById("addModelForm");
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
      if (trainedInput) trainedInput.value = "true";
      if (trainingSuccessInput) trainingSuccessInput.value = "true";
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

    // Show spinner and hide metrics
    const spinner = document.getElementById("trainingSpinner");
    if (spinner) spinner.style.display = "inline-block";

    // Remove old metrics if exists
    const metricsSection = document.getElementById("metricsSection");
    if (metricsSection) metricsSection.remove();

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
    }, 1000);
  }

  // Hàm kiểm tra trạng thái huấn luyện
  function checkTrainingStatus(modelId) {
    fetch(`/api/training-status/${modelId}`)
      .then((response) => response.json())
      .then((data) => {
        updateTrainingUI(data);

        // Kiểm tra trạng thái huấn luyện
        if (data.status === "completed") {
          clearInterval(trainingTimer);
          // Hide spinner
          const spinner = document.getElementById("trainingSpinner");
          if (spinner) spinner.style.display = "none";

          // Show completion message with metrics
          document.getElementById("trainingStatus").textContent =
            "Huấn luyện đã hoàn thành!";
          document.getElementById("trainingProgress").style.width = "100%";
          document.getElementById("trainingProgress").textContent = "100%";
          document.getElementById("cancelTrainingBtn").style.display = "none";
          document.getElementById("finishTrainingBtn").style.display = "block";

          // Show training metrics in a table
          displayTrainingMetrics(data);

          // Cập nhật trạng thái cho form
          document.getElementById("model_path").value = data.model_path || "";
        } else if (data.status === "failed") {
          clearInterval(trainingTimer);

          // Hide spinner
          const spinner = document.getElementById("trainingSpinner");
          if (spinner) spinner.style.display = "none";

          document.getElementById("trainingStatus").textContent =
            "Huấn luyện thất bại: " + (data.error || "Unknown error");
          document.getElementById("cancelTrainingBtn").textContent = "Đóng";
        } else if (data.status === "cancelled") {
          clearInterval(trainingTimer);

          // Hide spinner
          const spinner = document.getElementById("trainingSpinner");
          if (spinner) spinner.style.display = "none";

          document.getElementById("trainingStatus").textContent =
            "Huấn luyện đã bị hủy";
          document.getElementById("cancelTrainingBtn").textContent = "Đóng";
        }
      })
      .catch((error) => {
        console.error("Error checking training status:", error);
      });
  }

  // Hàm hiển thị metrics huấn luyện
  function displayTrainingMetrics(data) {
    // Remove old metrics section if exists
    const oldMetricsSection = document.getElementById("metricsSection");
    if (oldMetricsSection) oldMetricsSection.remove();

    // Create metrics section
    const metricsSection = document.createElement("div");
    metricsSection.id = "metricsSection";
    metricsSection.className = "mt-4";

    // Add title
    const title = document.createElement("h5");
    title.className = "text-start mb-3";
    title.innerHTML =
      '<i class="fas fa-chart-line me-2"></i>Kết quả huấn luyện:';
    metricsSection.appendChild(title);

    // Create table
    const table = document.createElement("table");
    table.id = "metricsTable";
    table.className = "table table-sm table-bordered table-striped";

    // Add headers
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    thead.className = "table-primary";

    const headers = ["Thông số", "Giá trị"];
    headers.forEach((headerText) => {
      const th = document.createElement("th");
      th.textContent = headerText;
      headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create table body
    const tbody = document.createElement("tbody");
    table.appendChild(tbody);

    // Add metrics rows
    // 1. General information
    addMetricsGroup(tbody, "Thông tin chung", [
      { name: "Kích thước tập dữ liệu", value: getDatasetSize(data) },
      { name: "Số epochs", value: data.total_epochs },
      { name: "Batch size", value: data.configuration?.batch_size || "N/A" },
      {
        name: "Learning rate",
        value: data.configuration?.learning_rate || "N/A",
      },
      {
        name: "Thời gian huấn luyện",
        value: getTrainingDuration(data.start_time, data.end_time),
      },
    ]);

    // 2. Performance metrics
    const performanceMetrics = [
      { name: "mAP50", value: formatDecimal(data.best_map50) },
      { name: "mAP50-95", value: formatDecimal(data.best_map50_95) },
    ];

    // Get latest epoch metrics
    if (data.epochs && data.epochs.length > 0) {
      const lastEpoch = data.epochs[data.epochs.length - 1];
      if (lastEpoch.metrics) {
        if (lastEpoch.metrics.precision !== undefined) {
          performanceMetrics.push({
            name: "Precision",
            value: formatDecimal(lastEpoch.metrics.precision),
          });
        }
        if (lastEpoch.metrics.recall !== undefined) {
          performanceMetrics.push({
            name: "Recall",
            value: formatDecimal(lastEpoch.metrics.recall),
          });
        }
        if (lastEpoch.metrics.box_loss !== undefined) {
          performanceMetrics.push({
            name: "Box Loss",
            value: lastEpoch.metrics.box_loss.toFixed(4),
          });
        }
        if (lastEpoch.metrics.cls_loss !== undefined) {
          performanceMetrics.push({
            name: "Class Loss",
            value: lastEpoch.metrics.cls_loss.toFixed(4),
          });
        }
      }
    }

    addMetricsGroup(tbody, "Hiệu suất mô hình", performanceMetrics);

    // 3. Model information
    addMetricsGroup(tbody, "Thông tin mô hình", [
      { name: "ID mô hình", value: data.model_id },
      { name: "Tên mô hình", value: data.model_name },
      { name: "Loại mô hình", value: data.model_type },
      { name: "Phiên bản", value: data.version },
      {
        name: "Đường dẫn mô hình",
        value: shortenPath(data.model_path) || "N/A",
      },
    ]);

    metricsSection.appendChild(table);

    // Add epoch progress chart if more than 2 epochs
    if (data.epochs && data.epochs.length > 2) {
      const chartContainer = document.createElement("div");
      chartContainer.className = "mt-4";
      chartContainer.style.height = "200px";

      const canvas = document.createElement("canvas");
      canvas.id = "metricsChart";
      chartContainer.appendChild(canvas);
      metricsSection.appendChild(chartContainer);

      // Create chart after appending to DOM
      setTimeout(() => createMetricsChart(data), 100);
    }

    // Add to modal
    const modalBody = document.querySelector(".modal-body");
    modalBody.appendChild(metricsSection);
  }

  // Helper function to add a group of metrics to the table
  function addMetricsGroup(tbody, groupName, metrics) {
    // Add group header
    const groupRow = document.createElement("tr");
    const groupCell = document.createElement("td");
    groupCell.colSpan = 2;
    groupCell.className = "table-secondary fw-bold";
    groupCell.textContent = groupName;
    groupRow.appendChild(groupCell);
    tbody.appendChild(groupRow);

    // Add metrics
    metrics.forEach((metric) => {
      const row = document.createElement("tr");

      const nameCell = document.createElement("td");
      nameCell.textContent = metric.name;
      nameCell.style.width = "40%";
      row.appendChild(nameCell);

      const valueCell = document.createElement("td");
      valueCell.textContent = metric.value;
      row.appendChild(valueCell);

      tbody.appendChild(row);
    });
  }

  // Helper function to create metrics chart
  function createMetricsChart(data) {
    if (!data.epochs || data.epochs.length < 2) return;

    const canvas = document.getElementById("metricsChart");
    if (!canvas) return;

    // Extract data
    const epochs = data.epochs.map((e) => e.epoch);
    const map50Values = data.epochs.map((e) => e.metrics?.map50 || 0);
    const map50_95Values = data.epochs.map((e) => e.metrics?.map50_95 || 0);

    // Create chart
    const ctx = canvas.getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: epochs,
        datasets: [
          {
            label: "mAP50",
            data: map50Values.map((v) => v * 100), // Convert to percentage
            borderColor: "rgb(54, 162, 235)",
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            tension: 0.1,
            fill: false,
          },
          {
            label: "mAP50-95",
            data: map50_95Values.map((v) => v * 100), // Convert to percentage
            borderColor: "rgb(255, 99, 132)",
            backgroundColor: "rgba(255, 99, 132, 0.2)",
            tension: 0.1,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Giá trị (%)",
            },
          },
          x: {
            title: {
              display: true,
              text: "Epoch",
            },
          },
        },
        plugins: {
          title: {
            display: true,
            text: "Tiến trình huấn luyện",
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `${context.dataset.label}: ${context.raw.toFixed(2)}%`;
              },
            },
          },
        },
      },
    });
  }

  // Helper function to get dataset size info
  function getDatasetSize(data) {
    if (!data.dataset_info) return "N/A";

    const total = data.dataset_info.total_images || 0;
    const train = data.dataset_info.train_images || 0;
    const val = data.dataset_info.val_images || 0;

    return `${total} ảnh (${train} train, ${val} validation)`;
  }

  // Format decimal to percentage
  function formatDecimal(value) {
    if (value === undefined || value === null) return "N/A";
    return (value * 100).toFixed(2) + "%";
  }

  // Shorten path for display
  function shortenPath(path) {
    if (!path) return "N/A";

    // If path is very long, show only the important parts
    if (path.length > 50) {
      const parts = path.split("\\");
      if (parts.length > 3) {
        return "..." + parts.slice(-3).join("\\");
      }
    }

    return path;
  }

  // Calculate training duration
  function getTrainingDuration(startTime, endTime) {
    if (!startTime || !endTime) return "N/A";

    const start = new Date(startTime);
    const end = new Date(endTime);
    const durationMs = end - start;

    // Format as minutes and seconds
    const minutes = Math.floor(durationMs / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);

    return `${minutes} phút ${seconds} giây`;
  }

  // Hàm cập nhật UI với trạng thái huấn luyện
  function updateTrainingUI(data) {
    // Cập nhật tiêu đề
    document.getElementById("trainingStatus").textContent = getStatusText(data);

    // Cập nhật thanh tiến trình
    if (data.total_epochs > 0) {
      let progress = 0;

      if (data.current_epoch > 0) {
        // If we have epoch data, use it
        progress = (data.current_epoch / data.total_epochs) * 100;
      } else {
        // If no epoch data but training is running, show indeterminate progress
        // Use elapsed time as a rough estimate (max 95%)
        if (data.status === "running" && data.start_time) {
          const startTime = new Date(data.start_time);
          const now = new Date();
          const elapsedMinutes = (now - startTime) / (1000 * 60);

          // Rough estimate: 5% progress per minute, max 95%
          progress = Math.min(95, elapsedMinutes * 5);
        }
      }

      document.getElementById("trainingProgress").style.width = `${progress}%`;
      document.getElementById("trainingProgress").textContent = `${Math.round(
        progress
      )}%`;

      // Hiển thị thông tin chi tiết
      if (data.current_epoch > 0) {
        // Hiển thị thêm thông tin metrics nếu có
        let statusText = `Epoch ${data.current_epoch}/${data.total_epochs}`;

        // Find the last epoch data
        let lastEpochData = null;
        if (data.epochs && data.epochs.length > 0) {
          lastEpochData = data.epochs[data.epochs.length - 1];
        }

        if (lastEpochData && lastEpochData.metrics) {
          const metrics = lastEpochData.metrics;
          if (metrics.map50) {
            statusText += `, mAP50: ${(metrics.map50 * 100).toFixed(2)}%`;
          }
          if (metrics.map50_95) {
            statusText += `, mAP50-95: ${(metrics.map50_95 * 100).toFixed(2)}%`;
          }
        }

        document.getElementById("trainingStatus").textContent = statusText;
      } else if (data.status === "running") {
        // Show a message when training is running but no epoch data yet
        const startTime = new Date(data.start_time);
        const now = new Date();
        const elapsedSeconds = Math.floor((now - startTime) / 1000);
        document.getElementById(
          "trainingStatus"
        ).textContent = `Đang huấn luyện... (${elapsedSeconds}s)`;
      }
    }
  }

  // Hàm lấy text hiển thị trạng thái
  function getStatusText(data) {
    switch (data.status) {
      case "initializing":
        return "Đang khởi tạo...";
      case "preparing_data":
        return "Đang chuẩn bị dữ liệu...";
      case "running":
        if (data.current_epoch > 0) {
          return `Đang huấn luyện: Epoch ${data.current_epoch}/${data.total_epochs}`;
        } else {
          return "Đang khởi động huấn luyện...";
        }
      case "completed":
        return "Huấn luyện đã hoàn thành!";
      case "failed":
        return "Huấn luyện thất bại: " + (data.error || "Unknown error");
      case "cancelled":
        return "Huấn luyện đã bị hủy";
      default:
        return `Trạng thái: ${data.status}`;
    }
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
