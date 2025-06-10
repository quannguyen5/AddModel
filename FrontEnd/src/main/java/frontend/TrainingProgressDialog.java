package frontend;

import frontend.modeldata.*;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Map;

public class TrainingProgressDialog extends JDialog {
    private ApiClient apiClient;
    private String modelId;
    private boolean modelSaved = false;
    private AddModelDialog parentDialog;
    private CreateModelRequest modelRequest;

    private JLabel statusLabel;
    private JProgressBar progressBar;
    private JTextArea logArea;
    private JButton cancelButton;
    private JButton saveButton;
    private JButton discardButton;
    private JButton closeButton;

    private JLabel map50Label;
    private JLabel map50_95Label;
    private JLabel precisionLabel;
    private JLabel recallLabel;
    private JLabel accuracyLabel;
    private JLabel f1ScoreLabel;

    private JLabel totalImagesLabel;
    private JLabel trainImagesLabel;
    private JLabel valImagesLabel;
    private JLabel durationLabel;

    private Timer statusUpdateTimer;

    public TrainingProgressDialog(Dialog parent, ApiClient apiClient, String modelId, AddModelDialog parentDialog) {
        super(parent, "Training Progress", true);
        this.apiClient = apiClient;
        this.modelId = modelId;
        this.parentDialog = parentDialog;

        initializeUI();
        startStatusUpdates();
    }

    private void initializeUI() {
        setLayout(new BorderLayout());
        setSize(600, 500);
        setLocationRelativeTo(getParent());
        setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);

        JPanel contentPanel = new JPanel(new BorderLayout());

        JPanel statusPanel = createStatusPanel();
        contentPanel.add(statusPanel, BorderLayout.NORTH);

        JTabbedPane tabbedPane = new JTabbedPane();

        JPanel metricsTabPanel = createMetricsPanel();
        tabbedPane.addTab("Metrics", metricsTabPanel);

        JPanel logPanel = createLogPanel();
        tabbedPane.addTab("Progress Log", logPanel);

        contentPanel.add(tabbedPane, BorderLayout.CENTER);

        JPanel buttonPanel = createButtonPanel();
        contentPanel.add(buttonPanel, BorderLayout.SOUTH);

        add(contentPanel);
    }

    private JPanel createStatusPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 10, 20));

        statusLabel = new JLabel("Init training...");
        statusLabel.setFont(statusLabel.getFont().deriveFont(Font.BOLD, 14f));
        panel.add(statusLabel, BorderLayout.NORTH);

        progressBar = new JProgressBar(0, 100);
        progressBar.setStringPainted(true);
        progressBar.setString("0%");
        panel.add(progressBar, BorderLayout.SOUTH);

        return panel;
    }

    private JPanel createMetricsPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JPanel modelMetricsPanel = new JPanel(new GridBagLayout());
        modelMetricsPanel.setBorder(BorderFactory.createTitledBorder("Model Performance"));
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;

        // mAP50
        gbc.gridx = 0; gbc.gridy = 0;
        modelMetricsPanel.add(new JLabel("mAP50:"), gbc);
        gbc.gridx = 1;
        map50Label = new JLabel("-");
        map50Label.setFont(map50Label.getFont().deriveFont(Font.BOLD));
        modelMetricsPanel.add(map50Label, gbc);

        // mAP50-95
        gbc.gridx = 0; gbc.gridy = 1;
        modelMetricsPanel.add(new JLabel("mAP50-95:"), gbc);
        gbc.gridx = 1;
        map50_95Label = new JLabel("-");
        map50_95Label.setFont(map50_95Label.getFont().deriveFont(Font.BOLD));
        modelMetricsPanel.add(map50_95Label, gbc);

        // Precision
        gbc.gridx = 0; gbc.gridy = 2;
        modelMetricsPanel.add(new JLabel("Precision:"), gbc);
        gbc.gridx = 1;
        precisionLabel = new JLabel("-");
        precisionLabel.setFont(precisionLabel.getFont().deriveFont(Font.BOLD));
        modelMetricsPanel.add(precisionLabel, gbc);

        // Recall
        gbc.gridx = 0; gbc.gridy = 3;
        modelMetricsPanel.add(new JLabel("Recall:"), gbc);
        gbc.gridx = 1;
        recallLabel = new JLabel("-");
        recallLabel.setFont(recallLabel.getFont().deriveFont(Font.BOLD));
        modelMetricsPanel.add(recallLabel, gbc);

        // Accuracy
        gbc.gridx = 0; gbc.gridy = 4;
        modelMetricsPanel.add(new JLabel("Accuracy:"), gbc);
        gbc.gridx = 1;
        accuracyLabel = new JLabel("-");
        accuracyLabel.setFont(accuracyLabel.getFont().deriveFont(Font.BOLD));
        modelMetricsPanel.add(accuracyLabel, gbc);

        // F1 Score
        gbc.gridx = 0; gbc.gridy = 5;
        modelMetricsPanel.add(new JLabel("F1 Score:"), gbc);
        gbc.gridx = 1;
        f1ScoreLabel = new JLabel("-");
        f1ScoreLabel.setFont(f1ScoreLabel.getFont().deriveFont(Font.BOLD));
        modelMetricsPanel.add(f1ScoreLabel, gbc);

        panel.add(modelMetricsPanel, BorderLayout.NORTH);

        // Dataset info
        JPanel datasetPanel = new JPanel(new GridBagLayout());
        datasetPanel.setBorder(BorderFactory.createTitledBorder("Dataset Information"));
        gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;

        // Total images
        gbc.gridx = 0; gbc.gridy = 0;
        datasetPanel.add(new JLabel("Total Images:"), gbc);
        gbc.gridx = 1;
        totalImagesLabel = new JLabel("-");
        totalImagesLabel.setFont(totalImagesLabel.getFont().deriveFont(Font.BOLD));
        datasetPanel.add(totalImagesLabel, gbc);

        // Train images
        gbc.gridx = 0; gbc.gridy = 1;
        datasetPanel.add(new JLabel("Train Images:"), gbc);
        gbc.gridx = 1;
        trainImagesLabel = new JLabel("-");
        trainImagesLabel.setFont(trainImagesLabel.getFont().deriveFont(Font.BOLD));
        datasetPanel.add(trainImagesLabel, gbc);

        // Val images
        gbc.gridx = 0; gbc.gridy = 2;
        datasetPanel.add(new JLabel("Validation Images:"), gbc);
        gbc.gridx = 1;
        valImagesLabel = new JLabel("-");
        valImagesLabel.setFont(valImagesLabel.getFont().deriveFont(Font.BOLD));
        datasetPanel.add(valImagesLabel, gbc);

        // Duration
        gbc.gridx = 0; gbc.gridy = 3;
        datasetPanel.add(new JLabel("Duration:"), gbc);
        gbc.gridx = 1;
        durationLabel = new JLabel("-");
        durationLabel.setFont(durationLabel.getFont().deriveFont(Font.BOLD));
        datasetPanel.add(durationLabel, gbc);

        panel.add(datasetPanel, BorderLayout.CENTER);

        return panel;
    }

    private JPanel createLogPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        logArea = new JTextArea();
        logArea.setEditable(false);
        logArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));

        JScrollPane scrollPane = new JScrollPane(logArea);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);

        panel.add(scrollPane, BorderLayout.CENTER);

        return panel;
    }

    private JPanel createButtonPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Cancel button - hiển thị khi đang training
        cancelButton = new JButton("Cancel Training");
        cancelButton.addActionListener(this::onCancelClicked);

        // Save button - hiển thị khi training hoàn thành
        saveButton = new JButton("Save Model");
        saveButton.addActionListener(this::onSaveClicked);
        saveButton.setVisible(false);
        saveButton.setBackground(new Color(34, 139, 34)); // Green
        saveButton.setForeground(Color.WHITE);

        // Discard button - hiển thị khi training hoàn thành
        discardButton = new JButton("Discard");
        discardButton.addActionListener(this::onDiscardClicked);
        discardButton.setVisible(false);
        discardButton.setBackground(new Color(220, 20, 60)); // Red
        discardButton.setForeground(Color.WHITE);

        // Close button - hiển thị khi training failed/cancelled
        closeButton = new JButton("Close");
        closeButton.addActionListener(e -> dispose());
        closeButton.setVisible(false);

        panel.add(cancelButton);
        panel.add(saveButton);
        panel.add(discardButton);
        panel.add(closeButton);

        return panel;
    }

    private void startStatusUpdates() {
        statusUpdateTimer = new Timer(2000, new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                updateTrainingStatus();
            }
        });
        statusUpdateTimer.start();
    }

    private void updateTrainingStatus() {
        SwingWorker<TrainingStatus, Void> worker = new SwingWorker<TrainingStatus, Void>() {
            @Override
            protected TrainingStatus doInBackground() throws Exception {
                return apiClient.getTrainingStatus(modelId);
            }

            @Override
            protected void done() {
                try {
                    TrainingStatus status = get();

                    appendLog("=== STATUS DEBUG ===");
                    appendLog("Status: " + status.getStatus());
                    appendLog("Current Epoch: " + status.getCurrent_epoch());
                    appendLog("Total Epochs: " + status.getTotal_epochs());
                    appendLog("Final Metrics: " + (status.getFinal_metrics() != null ? status.getFinal_metrics().toString() : "null"));
                    appendLog("Dataset Info: " + (status.getDataset_info() != null ? status.getDataset_info().toString() : "null"));
                    appendLog("==================");

                    updateUI(status);

                    String currentStatus = status.getStatus();
                    if ("completed".equals(currentStatus) || "failed".equals(currentStatus) || "cancelled".equals(currentStatus)) {
                        statusUpdateTimer.stop();
                        onTrainingFinished(status);
                    }

                } catch (Exception e) {
                    appendLog("Error training status: " + e.getMessage());
                    e.printStackTrace();
                }
            }
        };
        worker.execute();
    }

    private void updateUI(TrainingStatus status) {
        String statusText = getStatusText(status);
        statusLabel.setText(statusText);

        if (status.getTotal_epochs() > 0) {
            int progress = (int) ((double) status.getCurrent_epoch() / status.getTotal_epochs() * 100);
            progressBar.setValue(progress);
            progressBar.setString(progress + "%");
        }

        appendLog(String.format("[%s] %s",
                java.time.LocalTime.now().toString(), statusText));

        updateMetrics(status);

        updateDatasetInfo(status);
    }

    private String getStatusText(TrainingStatus status) {
        switch (status.getStatus()) {
            case "initializing":
                return "Initializing training...";
            case "preparing_data":
                return "Preparing training data...";
            case "running":
                if (status.getCurrent_epoch() > 0) {
                    return String.format("Training: Epoch %d/%d",
                            status.getCurrent_epoch(), status.getTotal_epochs());
                } else {
                    return "Starting training...";
                }
            case "completed":
                return "Training completed successfully!";
            case "failed":
                return "Training failed: " + (status.getError() != null ? status.getError() : "Unknown error");
            case "cancelled":
                return "Training was cancelled";
            default:
                return "Status: " + status.getStatus();
        }
    }

    private void updateMetrics(TrainingStatus status) {
        Map<String, Object> metrics = status.getFinal_metrics();

        if (metrics != null) {
            appendLog("Found metrics, updating display...");

            if (metrics.containsKey("map50")) {
                updateMetricLabel(map50Label, metrics.get("map50"));
            }
            if (metrics.containsKey("map50_95")) {
                updateMetricLabel(map50_95Label, metrics.get("map50_95"));
            }
            if (metrics.containsKey("precision")) {
                updateMetricLabel(precisionLabel, metrics.get("precision"));
            }
            if (metrics.containsKey("recall")) {
                updateMetricLabel(recallLabel, metrics.get("recall"));
            }
            if (metrics.containsKey("accuracy")) {
                updateMetricLabel(accuracyLabel, metrics.get("accuracy"));
            }
            if (metrics.containsKey("f1_score")) {
                updateMetricLabel(f1ScoreLabel, metrics.get("f1_score"));
            }
            SwingUtilities.invokeLater(() -> {
                revalidate();
                repaint();
            });
        }
    }

    private void updateMetricLabel(JLabel label, Object value) {
        if (value != null) {
            try {
                double val = 0.0;
                if (value instanceof Number) {
                    val = ((Number) value).doubleValue();
                } else {
                    val = Double.parseDouble(value.toString());
                }
                if (val <= 1.0) {
                    val = val * 100;
                }

                final String displayText = String.format("%.2f%%", val);
                SwingUtilities.invokeLater(() -> {
                    label.setText(displayText);
                    label.setForeground(new Color(34, 139, 34)); //xanh la cay
                });

            } catch (NumberFormatException e) {
                appendLog("Error parsing metric value: " + value);
            }
        }
    }

    private void updateDatasetInfo(TrainingStatus status) {
        Map<String, Object> datasetInfo = status.getDataset_info();
        if (datasetInfo != null) {
            updateDatasetLabel(totalImagesLabel, datasetInfo.get("total_images"));
            updateDatasetLabel(trainImagesLabel, datasetInfo.get("train_images"));
            updateDatasetLabel(valImagesLabel, datasetInfo.get("val_images"));
        }
        if (status.getStart_time() != null && status.getEnd_time() != null) {
            durationLabel.setText("Training completed");
        } else if (status.getStart_time() != null) {
            durationLabel.setText("In progress...");
        }
    }

    private void updateDatasetLabel(JLabel label, Object value) {
        if (value != null) {
            SwingUtilities.invokeLater(() -> {
                label.setText(value.toString());
                label.setForeground(Color.BLACK);
            });
        }
    }

    private void appendLog(String message) {
        SwingUtilities.invokeLater(() -> {
            logArea.append(message + "\n");
            logArea.setCaretPosition(logArea.getDocument().getLength());
        });
    }

    private void onCancelClicked(ActionEvent e) {
        int result = JOptionPane.showConfirmDialog(
                this,
                "Are you sure you want to cancel the training?",
                "Confirm Cancel",
                JOptionPane.YES_NO_OPTION
        );

        if (result == JOptionPane.YES_OPTION) {
            try {
                apiClient.cancelTraining(modelId);
                appendLog("Cancel request sent...");
                cancelButton.setEnabled(false);
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Error cancelling training: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
        }
    }

    private void onSaveClicked(ActionEvent e) {
        saveButton.setEnabled(false);
        discardButton.setEnabled(false);
        saveButton.setText("Saving...");

        SwingWorker<Void, Void> saveWorker = new SwingWorker<Void, Void>() {
            private String result = null;
            private Exception error = null;

            @Override
            protected Void doInBackground() throws Exception {
                try {
                    result = apiClient.createModel(modelRequest);
                } catch (Exception e) {
                    error = e;
                }
                return null;
            }

            @Override
            protected void done() {
                saveButton.setText("Save Model");
                saveButton.setEnabled(true);
                discardButton.setEnabled(true);

                if (error == null) {
                    modelSaved = true;
                    appendLog("Model saved successfully!");

                    JOptionPane.showMessageDialog(TrainingProgressDialog.this,
                            "Model saved successfully!\n" + result,
                            "Success",
                            JOptionPane.INFORMATION_MESSAGE);

                    dispose();
                } else {
                    JOptionPane.showMessageDialog(TrainingProgressDialog.this,
                            "Error saving model: " + error.getMessage(),
                            "Error",
                            JOptionPane.ERROR_MESSAGE);
                }
            }
        };
        saveWorker.execute();
    }

    private void onDiscardClicked(ActionEvent e) {
        int confirm = JOptionPane.showConfirmDialog(this,
                "Are you sure you want to discard this trained model?\nThis action cannot be undone.",
                "Confirm Discard",
                JOptionPane.YES_NO_OPTION,
                JOptionPane.WARNING_MESSAGE);

        if (confirm == JOptionPane.YES_OPTION) {
            discardButton.setEnabled(false);
            saveButton.setEnabled(false);
            discardButton.setText("Discarding...");

            SwingWorker<Void, Void> discardWorker = new SwingWorker<Void, Void>() {
                @Override
                protected Void doInBackground() throws Exception {
                    deleteTrainingFolder();
                    return null;
                }

                @Override
                protected void done() {
                    appendLog("Training data discarded.");

                    JOptionPane.showMessageDialog(TrainingProgressDialog.this,
                            "Model discarded. Training data has been removed.",
                            "Model Discarded",
                            JOptionPane.INFORMATION_MESSAGE);

                    dispose();
                }
            };
            discardWorker.execute();
        }
    }

    private void onTrainingFinished(TrainingStatus status) {
        if ("completed".equals(status.getStatus())) {
            if (parentDialog != null) {
                parentDialog.onTrainingCompleted();
            }
            showSaveDiscardButtons();
        } else {
            showCloseButton();
        }
    }

    private void showSaveDiscardButtons() {
        SwingUtilities.invokeLater(() -> {
            cancelButton.setVisible(false);
            saveButton.setVisible(true);
            discardButton.setVisible(true);

            appendLog("\n=== Training Completed ===");

            revalidate();
            repaint();
        });
    }

    private void showCloseButton() {
        SwingUtilities.invokeLater(() -> {
            cancelButton.setVisible(false);
            saveButton.setVisible(false);
            discardButton.setVisible(false);
            closeButton.setVisible(true);

            revalidate();
            repaint();
        });
    }

    private void deleteTrainingFolder() {
        try {
            DeleteResponse response = apiClient.deleteTrainingFolder(modelId);
            if (response.isSuccess()) {
                appendLog("Training folder deleted successfully: " + response.getMessage());
                System.out.println("Training folder deleted for model: " + modelId);
            } else {
                appendLog("Failed to delete training folder: " + response.getMessage());
                System.err.println("Failed to delete training folder: " + response.getMessage());
            }
        } catch (Exception e) {
            String errorMsg = "Error deleting training folder: " + e.getMessage();
            System.err.println(errorMsg);
            appendLog(errorMsg);
        }
    }

    public void setModelRequest(CreateModelRequest modelRequest) {
        this.modelRequest = modelRequest;
    }

    public boolean isModelSaved() {
        return modelSaved;
    }

    @Override
    public void dispose() {
        if (statusUpdateTimer != null) {
            statusUpdateTimer.stop();
        }
        super.dispose();
    }
}