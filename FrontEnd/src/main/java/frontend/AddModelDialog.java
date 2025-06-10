package frontend;

import frontend.modeldata.*;
import frontend.uicustom.*;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.util.List;

public class AddModelDialog extends JDialog {
    private ApiClient apiClient;
    private boolean modelAdded = false;

    private JTextField modelNameField;
    private JComboBox<String> modelTypeCombo;
    private JTextField versionField;
    private JTextArea descriptionArea;
    private JSpinner epochsSpinner;
    private JSpinner batchSizeSpinner;
    private JSpinner imageSizeSpinner;
    private JSpinner learningRateSpinner;

    private JTable templateTable;
    private TemplateTableModel templateTableModel;
    private List<TemplateData> templates;

    private JButton trainButton;
    private JButton cancelButton;

    private String currentModelId;
    private TrainingProgressDialog trainingDialog;
    
    public AddModelDialog(Frame parent, ApiClient apiClient) {
        super(parent, "Add New Model", true);
        this.apiClient = apiClient;
        
        initializeUI();
        loadTemplates();
        loadModelTypes();
    }
    
    private void initializeUI() {
        setLayout(new BorderLayout());
        setSize(1200, 600);
        setLocationRelativeTo(getParent());

        JTabbedPane tabbedPane = new JTabbedPane();

        JPanel modelInfoPanel = createModelInfoPanel();
        tabbedPane.addTab("Thong tin", modelInfoPanel);

        JPanel trainingPanel = createTrainingParametersPanel();
        tabbedPane.addTab("Thong so train", trainingPanel);

        JPanel templatePanel = createTemplateSelectionPanel();
        tabbedPane.addTab("Cac mau huan luyen", templatePanel);
        
        add(tabbedPane, BorderLayout.CENTER);

        JPanel buttonPanel = createButtonPanel();
        add(buttonPanel, BorderLayout.SOUTH);
    }
    
    private JPanel createModelInfoPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        GridBagConstraints gbc = new GridBagConstraints();

        gbc.gridx = 0; gbc.gridy = 0;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.insets = new Insets(5, 5, 5, 5);
        panel.add(new JLabel("Model Name:*"), gbc);
        
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        modelNameField = new JTextField(20);
        panel.add(modelNameField, gbc);
        
        gbc.gridx = 0; gbc.gridy = 1;
        gbc.fill = GridBagConstraints.NONE;
        gbc.weightx = 0;
        panel.add(new JLabel("Model Type:*"), gbc);
        
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        modelTypeCombo = new JComboBox<>();
        panel.add(modelTypeCombo, gbc);
        
        gbc.gridx = 0; gbc.gridy = 2;
        gbc.fill = GridBagConstraints.NONE;
        gbc.weightx = 0;
        panel.add(new JLabel("Version:*"), gbc);
        
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        versionField = new JTextField("v1.0.0");
        panel.add(versionField, gbc);
        
        // Description
        gbc.gridx = 0; gbc.gridy = 3;
        gbc.fill = GridBagConstraints.NONE;
        gbc.weightx = 0;
        gbc.anchor = GridBagConstraints.NORTHWEST;
        panel.add(new JLabel("Description:"), gbc);
        
        gbc.gridx = 1; gbc.fill = GridBagConstraints.BOTH;
        gbc.weightx = 1.0; gbc.weighty = 1.0;
        descriptionArea = new JTextArea(5, 20);
        descriptionArea.setLineWrap(true);
        descriptionArea.setWrapStyleWord(true);
        JScrollPane descScrollPane = new JScrollPane(descriptionArea);
        panel.add(descScrollPane, gbc);
        
        return panel;
    }
    
    private JPanel createTrainingParametersPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        GridBagConstraints gbc = new GridBagConstraints();
        
        // Epochs
        gbc.gridx = 0; gbc.gridy = 0;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.insets = new Insets(5, 5, 5, 5);
        panel.add(new JLabel("Epochs:"), gbc);
        
        gbc.gridx = 1;
        epochsSpinner = new JSpinner(new SpinnerNumberModel(100, 1, 1000, 1));
        panel.add(epochsSpinner, gbc);
        
        // Batch Size
        gbc.gridx = 0; gbc.gridy = 1;
        panel.add(new JLabel("Batch Size:"), gbc);
        
        gbc.gridx = 1;
        batchSizeSpinner = new JSpinner(new SpinnerNumberModel(16, 1, 128, 1));
        panel.add(batchSizeSpinner, gbc);
        
        // Image Size
        gbc.gridx = 0; gbc.gridy = 2;
        panel.add(new JLabel("Image Size:"), gbc);
        
        gbc.gridx = 1;
        imageSizeSpinner = new JSpinner(new SpinnerNumberModel(640, 320, 1280, 32));
        panel.add(imageSizeSpinner, gbc);
        
        // Learning Rate
        gbc.gridx = 0; gbc.gridy = 3;
        panel.add(new JLabel("Learning Rate:"), gbc);
        
        gbc.gridx = 1;
        learningRateSpinner = new JSpinner(new SpinnerNumberModel(0.001, 0.0001, 0.1, 0.0001));
        JSpinner.NumberEditor editor = new JSpinner.NumberEditor(learningRateSpinner, "0.0000");
        learningRateSpinner.setEditor(editor);
        panel.add(learningRateSpinner, gbc);
        
        return panel;
    }
    
    private JPanel createTemplateSelectionPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JLabel infoLabel = new JLabel("Chon it nhat 1 mau de train");
        panel.add(infoLabel, BorderLayout.NORTH);

        templateTableModel = new TemplateTableModel();
        templateTableModel.setParentDialog(this);
        templateTable = new JTable(templateTableModel);

        templateTable.getColumnModel().getColumn(0).setCellEditor(new CheckboxCellEditor());
        templateTable.getColumnModel().getColumn(0).setCellRenderer(new CheckboxRenderer());
        
        // Set column widths - thêm cột Labels
        templateTable.getColumnModel().getColumn(0).setPreferredWidth(50);  // Checkbox
        templateTable.getColumnModel().getColumn(1).setPreferredWidth(50);  // ID
        templateTable.getColumnModel().getColumn(2).setPreferredWidth(100); // Image
        templateTable.getColumnModel().getColumn(3).setPreferredWidth(200); // Description
        templateTable.getColumnModel().getColumn(4).setPreferredWidth(150); // Labels
        templateTable.getColumnModel().getColumn(5).setPreferredWidth(120); // Time
        
        // Add image renderer for image column
        templateTable.getColumnModel().getColumn(2).setCellRenderer(new ImageRenderer(apiClient));
        templateTable.setRowHeight(80);
        
        JScrollPane scrollPane = new JScrollPane(templateTable);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createButtonPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        cancelButton = new JButton("Cancel");
        cancelButton.addActionListener(e -> dispose());
        
        trainButton = new JButton("Train Model");
        trainButton.addActionListener(this::onTrainClicked);
        trainButton.setEnabled(false);
        
        panel.add(cancelButton);
        panel.add(trainButton);

        modelNameField.getDocument().addDocumentListener(new SimpleDocumentListener(this::updateTrainButtonState));
        versionField.getDocument().addDocumentListener(new SimpleDocumentListener(this::updateTrainButtonState));
        
        return panel;
    }
    
    public void updateTrainButtonState() {
        boolean hasName = !modelNameField.getText().trim().isEmpty();
        boolean hasVersion = !versionField.getText().trim().isEmpty();
        boolean hasModelType = modelTypeCombo.getSelectedItem() != null;

        boolean hasSelectedTemplates = false;
        if (templateTableModel != null) {
            hasSelectedTemplates = templateTableModel.hasSelectedTemplates();
        }
        
        trainButton.setEnabled(hasName && hasVersion && hasModelType && hasSelectedTemplates);
    }
    
    private void onTrainClicked(ActionEvent e) {
        if (!validateInput()) return;
        
        try {
            TrainRequest request = createTrainRequest();
            TrainResponse response = apiClient.startTraining(request);
            
            if (response.isSuccess()) {
                currentModelId = response.getModel_id();
                trainingDialog = new TrainingProgressDialog(this, apiClient, currentModelId, this);
                trainingDialog.setVisible(true);
                if (trainingDialog.isModelSaved()) {
                    modelAdded = true;
                    dispose();
                }
            } else {
                JOptionPane.showMessageDialog(this, "Loi khi bat dau: " + response.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
            
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, "Loi khi bat dau: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
        }
    }
    
    public void onTrainingCompleted() {
        CreateModelRequest request = createModelRequest();
        if (trainingDialog != null) {
            trainingDialog.setModelRequest(request);
        }
    }
    
    private boolean validateInput() {
        if (modelNameField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Chua nhap ten", "Loi", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (versionField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Chua nhap version", "Loi", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (modelTypeCombo.getSelectedItem() == null) {
            JOptionPane.showMessageDialog(this, "Chua chon loai mo hinh", "Loi", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (templateTable.getColumnModel().getColumnCount() == 0) {
            JOptionPane.showMessageDialog(this, "Chon it nhat 1 mau", "Loi", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (!templateTableModel.hasSelectedTemplates()) {
            JOptionPane.showMessageDialog(this, "Chon it nhat 1 mau", "Loi", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        return true;
    }
    
    private TrainRequest createTrainRequest() {
        List<Integer> templateIds = templateTableModel.getSelectedTemplateIds();
        
        return new TrainRequest(
            modelNameField.getText().trim(),
            (String) modelTypeCombo.getSelectedItem(),
            versionField.getText().trim(),
            templateIds,
            (Integer) epochsSpinner.getValue(),
            (Integer) batchSizeSpinner.getValue(),
            (Integer) imageSizeSpinner.getValue(),
            (Double) learningRateSpinner.getValue()
        );
    }
    
    private CreateModelRequest createModelRequest() {
        List<Integer> templateIds = templateTableModel.getSelectedTemplateIds();
        
        return new CreateModelRequest(
            modelNameField.getText().trim(),
            (String) modelTypeCombo.getSelectedItem(),
            versionField.getText().trim(),
            descriptionArea.getText().trim(),
            templateIds,
            (Integer) epochsSpinner.getValue(),
            (Integer) batchSizeSpinner.getValue(),
            (Double) learningRateSpinner.getValue(),
            0.85
        );
    }
    
    private void loadTemplates() {
        SwingWorker<List<TemplateData>, Void> worker = new SwingWorker<List<TemplateData>, Void>() {
            @Override
            protected List<TemplateData> doInBackground() throws Exception {
                return apiClient.getAllTemplates();
            }
            
            @Override
            protected void done() {
                try {
                    templates = get();
                    templateTableModel.setTemplates(templates);

                    if (templates != null && !templates.isEmpty()) {
                        String firstImageUrl = templates.get(0).getImageUrl();
                        if (firstImageUrl != null) {
                            String filename = apiClient.extractFilename(firstImageUrl);
                        }
                    }
                    
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        };
        worker.execute();
    }
    
    private void loadModelTypes() {
        SwingWorker<List<String>, Void> worker = new SwingWorker<List<String>, Void>() {
            @Override
            protected List<String> doInBackground() throws Exception {
                return apiClient.getModelTypes();
            }
            
            @Override
            protected void done() {
                try {
                    List<String> types = get();
                    for (String type : types) {
                        modelTypeCombo.addItem(type);
                    }
                } catch (Exception e) {
                    JOptionPane.showMessageDialog(AddModelDialog.this, "Error loading model types: " + e.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        };
        worker.execute();
    }
    
    public boolean isModelAdded() {
        return modelAdded;
    }
}