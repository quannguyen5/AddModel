package frontend;

import javax.swing.*;
import javax.swing.table.AbstractTableModel;
import javax.swing.table.TableCellRenderer;
import javax.swing.table.TableCellEditor;
import javax.swing.AbstractCellEditor;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage;
import java.io.File;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

public class AddModelDialog extends JDialog {
    private ApiClient apiClient;
    private boolean modelAdded = false;
    
    // Form components
    private JTextField modelNameField;
    private JComboBox<String> modelTypeCombo;
    private JTextField versionField;
    private JTextArea descriptionArea;
    private JSpinner epochsSpinner;
    private JSpinner batchSizeSpinner;
    private JSpinner imageSizeSpinner;
    private JSpinner learningRateSpinner;
    
    // Template selection
    private JTable templateTable;
    private TemplateTableModel templateTableModel;
    private List<TemplateData> templates;
    
    // Buttons
    private JButton trainButton;
    private JButton cancelButton;
    private JButton saveButton;
    
    // Training status
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
        setSize(800, 600);
        setLocationRelativeTo(getParent());
        
        // Create main panel with tabs
        JTabbedPane tabbedPane = new JTabbedPane();
        
        // Model Info Tab
        JPanel modelInfoPanel = createModelInfoPanel();
        tabbedPane.addTab("Model Information", modelInfoPanel);
        
        // Training Parameters Tab
        JPanel trainingPanel = createTrainingParametersPanel();
        tabbedPane.addTab("Training Parameters", trainingPanel);
        
        // Template Selection Tab
        JPanel templatePanel = createTemplateSelectionPanel();
        tabbedPane.addTab("Training Templates", templatePanel);
        
        add(tabbedPane, BorderLayout.CENTER);
        
        // Button panel
        JPanel buttonPanel = createButtonPanel();
        add(buttonPanel, BorderLayout.SOUTH);
    }
    
    private JPanel createModelInfoPanel() {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));
        GridBagConstraints gbc = new GridBagConstraints();
        
        // Model Name
        gbc.gridx = 0; gbc.gridy = 0;
        gbc.anchor = GridBagConstraints.WEST;
        gbc.insets = new Insets(5, 5, 5, 5);
        panel.add(new JLabel("Model Name:*"), gbc);
        
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        modelNameField = new JTextField(20);
        panel.add(modelNameField, gbc);
        
        // Model Type
        gbc.gridx = 0; gbc.gridy = 1;
        gbc.fill = GridBagConstraints.NONE;
        gbc.weightx = 0;
        panel.add(new JLabel("Model Type:*"), gbc);
        
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.weightx = 1.0;
        modelTypeCombo = new JComboBox<>();
        panel.add(modelTypeCombo, gbc);
        
        // Version
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
        
        // Info label
        JLabel infoLabel = new JLabel("Select at least one template for training:");
        panel.add(infoLabel, BorderLayout.NORTH);
        
        // Template table with checkbox column
        templateTableModel = new TemplateTableModel();
        templateTableModel.setParentDialog(this); // Set parent reference
        templateTable = new JTable(templateTableModel);
        
        // Enable checkbox selection for first column
        templateTable.getColumnModel().getColumn(0).setCellEditor(new CheckboxCellEditor());
        templateTable.getColumnModel().getColumn(0).setCellRenderer(new CheckboxRenderer());
        
        // Set column widths
        templateTable.getColumnModel().getColumn(0).setPreferredWidth(50);  // Checkbox
        templateTable.getColumnModel().getColumn(1).setPreferredWidth(50);  // ID
        templateTable.getColumnModel().getColumn(2).setPreferredWidth(100); // Image
        templateTable.getColumnModel().getColumn(3).setPreferredWidth(200); // Description
        templateTable.getColumnModel().getColumn(4).setPreferredWidth(150); // Time
        
        // Add image renderer for image column
        templateTable.getColumnModel().getColumn(2).setCellRenderer(new ImageRenderer(apiClient));
        
        templateTable.setRowHeight(80); // Make rows taller for images
        
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
        
        saveButton = new JButton("Save Model");
        saveButton.addActionListener(this::onSaveClicked);
        saveButton.setEnabled(false);
        
        panel.add(cancelButton);
        panel.add(trainButton);
        panel.add(saveButton);
        
        // Add listeners to enable/disable train button
        modelNameField.getDocument().addDocumentListener(new SimpleDocumentListener(this::updateTrainButtonState));
        versionField.getDocument().addDocumentListener(new SimpleDocumentListener(this::updateTrainButtonState));
        // Remove the old table selection listener since we're using checkboxes now
        
        return panel;
    }
    
    public void updateTrainButtonState() {
        boolean hasName = !modelNameField.getText().trim().isEmpty();
        boolean hasVersion = !versionField.getText().trim().isEmpty();
        boolean hasModelType = modelTypeCombo.getSelectedItem() != null;
        
        // Check if any templates are selected via checkbox
        boolean hasSelectedTemplates = false;
        if (templateTableModel != null) {
            hasSelectedTemplates = templateTableModel.hasSelectedTemplates();
        }
        
        trainButton.setEnabled(hasName && hasVersion && hasModelType && hasSelectedTemplates);
    }
    
    private void onTrainClicked(ActionEvent e) {
        if (!validateInput()) return;
        
        try {
            // Create train request
            TrainRequest request = createTrainRequest();
            
            // Start training
            TrainResponse response = apiClient.startTraining(request);
            
            if (response.isSuccess()) {
                currentModelId = response.getModel_id();
                
                // Show training progress dialog
                trainingDialog = new TrainingProgressDialog(this, apiClient, currentModelId);
                trainingDialog.setVisible(true);
                
                // Check if training completed successfully
                if (trainingDialog.isTrainingCompleted()) {
                    saveButton.setEnabled(true);
                    trainButton.setEnabled(false);
                    JOptionPane.showMessageDialog(this, "Training completed successfully!", "Success", JOptionPane.INFORMATION_MESSAGE);
                }
            } else {
                JOptionPane.showMessageDialog(this, "Failed to start training: " + response.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
            
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, "Error starting training: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
        }
    }
    
    private void onSaveClicked(ActionEvent e) {
        if (currentModelId == null) {
            JOptionPane.showMessageDialog(this, "No trained model to save.", "Error", JOptionPane.ERROR_MESSAGE);
            return;
        }
        
        try {
            CreateModelRequest request = createModelRequest();
            String message = apiClient.createModel(request);
            
            modelAdded = true;
            JOptionPane.showMessageDialog(this, message, "Success", JOptionPane.INFORMATION_MESSAGE);
            dispose();
            
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, "Error saving model: " + ex.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
        }
    }
    
    private boolean validateInput() {
        if (modelNameField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter a model name.", "Validation Error", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (versionField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter a version.", "Validation Error", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (modelTypeCombo.getSelectedItem() == null) {
            JOptionPane.showMessageDialog(this, "Please select a model type.", "Validation Error", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (templateTable.getColumnModel().getColumnCount() == 0) {
            JOptionPane.showMessageDialog(this, "Please select at least one template.", "Validation Error", JOptionPane.WARNING_MESSAGE);
            return false;
        }
        
        if (!templateTableModel.hasSelectedTemplates()) {
            JOptionPane.showMessageDialog(this, "Please select at least one template.", "Validation Error", JOptionPane.WARNING_MESSAGE);
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
            0.85 // Default accuracy, will be updated from training results
        );
    }
    
    private void loadTemplates() {
        SwingWorker<List<TemplateData>, Void> worker = new SwingWorker<List<TemplateData>, Void>() {
            @Override
            protected List<TemplateData> doInBackground() throws Exception {
                // Test connection first
                if (!apiClient.testTemplateServiceConnection()) {
                    throw new Exception("Template service is not accessible");
                }
                return apiClient.getAllTemplates();
            }
            
            @Override
            protected void done() {
                try {
                    templates = get();
                    templateTableModel.setTemplates(templates);
                    
                    // Test image loading for first template
                    if (templates != null && !templates.isEmpty()) {
                        String firstImageUrl = templates.get(0).getImageUrl();
                        if (firstImageUrl != null) {
                            String filename = apiClient.extractFilename(firstImageUrl);
                            boolean imageAccessible = apiClient.testImageEndpoint(filename);
                            System.out.println("First image accessibility test: " + imageAccessible);
                        }
                    }
                    
                } catch (Exception e) {
                    JOptionPane.showMessageDialog(AddModelDialog.this, 
                        "Error loading templates: " + e.getMessage(), 
                        "Error", JOptionPane.ERROR_MESSAGE);
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

// Custom checkbox cell editor
class CheckboxCellEditor extends AbstractCellEditor implements TableCellEditor {
    private JCheckBox checkBox;
    
    public CheckboxCellEditor() {
        checkBox = new JCheckBox();
        checkBox.setHorizontalAlignment(JLabel.CENTER);
    }
    
    @Override
    public Component getTableCellEditorComponent(JTable table, Object value,
            boolean isSelected, int row, int column) {
        checkBox.setSelected(value != null && (Boolean) value);
        return checkBox;
    }
    
    @Override
    public Object getCellEditorValue() {
        return checkBox.isSelected();
    }
}

// Checkbox renderer
class CheckboxRenderer extends JCheckBox implements TableCellRenderer {
    public CheckboxRenderer() {
        setHorizontalAlignment(JLabel.CENTER);
    }
    
    @Override
    public Component getTableCellRendererComponent(JTable table, Object value,
            boolean isSelected, boolean hasFocus, int row, int column) {
        setSelected(value != null && (Boolean) value);
        
        if (isSelected) {
            setBackground(table.getSelectionBackground());
            setForeground(table.getSelectionForeground());
        } else {
            setBackground(table.getBackground());
            setForeground(table.getForeground());
        }
        
        return this;
    }
}

// Image renderer
class ImageRenderer extends JLabel implements TableCellRenderer {
    private ApiClient apiClient;
    
    public ImageRenderer(ApiClient apiClient) {
        this.apiClient = apiClient;
        setHorizontalAlignment(JLabel.CENTER);
        setOpaque(true);
    }
    
    @Override
    public Component getTableCellRendererComponent(JTable table, Object value,
            boolean isSelected, boolean hasFocus, int row, int column) {
        
        if (isSelected) {
            setBackground(table.getSelectionBackground());
            setForeground(table.getSelectionForeground());
        } else {
            setBackground(table.getBackground());
            setForeground(table.getForeground());
        }
        
        if (value != null) {
            String imageUrl = value.toString();
            System.out.println("ImageRenderer processing URL: " + imageUrl);
            
            try {
                // Try to load image from URL
                ImageIcon icon = loadImageIcon(imageUrl);
                if (icon != null) {
                    // Scale image to fit cell
                    Image img = icon.getImage().getScaledInstance(60, 60, Image.SCALE_SMOOTH);
                    setIcon(new ImageIcon(img));
                    setText("");
                    System.out.println("Image rendered successfully for: " + imageUrl);
                } else {
                    setIcon(createPlaceholderIcon());
                    setText("No Image");
                    System.out.println("Failed to load image, using placeholder for: " + imageUrl);
                }
            } catch (Exception e) {
                setIcon(createPlaceholderIcon());
                setText("Error");
                System.err.println("Error in ImageRenderer for " + imageUrl + ": " + e.getMessage());
            }
        } else {
            setIcon(createPlaceholderIcon());
            setText("No Image");
        }
        
        return this;
    }
    
    private ImageIcon loadImageIcon(String imageUrl) {
        try {
            System.out.println("ImageRenderer loading: " + imageUrl);
            
            // Use the provided ApiClient to load image from template service
            ImageIcon icon = apiClient.loadImageFromUrl(imageUrl);
            if (icon != null) {
                System.out.println("Successfully loaded image via ApiClient");
                return icon;
            } else {
                System.out.println("ApiClient returned null for image");
            }
        } catch (Exception e) {
            System.err.println("Error loading image from URL: " + e.getMessage());
            e.printStackTrace();
        }
        
        // Fallback to placeholder
        System.out.println("Using placeholder for: " + imageUrl);
        return createPlaceholderIcon();
    }
    
    private ImageIcon createPlaceholderIcon() {
        // Create a simple colored rectangle as placeholder
        BufferedImage img = new BufferedImage(60, 60, BufferedImage.TYPE_INT_RGB);
        Graphics2D g2d = img.createGraphics();
        g2d.setColor(Color.LIGHT_GRAY);
        g2d.fillRect(0, 0, 60, 60);
        g2d.setColor(Color.DARK_GRAY);
        g2d.drawRect(0, 0, 59, 59);
        g2d.setColor(Color.BLACK);
        g2d.drawString("IMG", 20, 35);
        g2d.dispose();
        return new ImageIcon(img);
    }
}

// Helper class for document listener
class SimpleDocumentListener implements javax.swing.event.DocumentListener {
    private final Runnable callback;
    
    public SimpleDocumentListener(Runnable callback) {
        this.callback = callback;
    }
    
    @Override
    public void insertUpdate(javax.swing.event.DocumentEvent e) { callback.run(); }
    
    @Override
    public void removeUpdate(javax.swing.event.DocumentEvent e) { callback.run(); }
    
    @Override
    public void changedUpdate(javax.swing.event.DocumentEvent e) { callback.run(); }
}

// Template table model
class TemplateTableModel extends AbstractTableModel {
    private final String[] columnNames = {"Select", "ID", "Image", "Description", "Time Update"};
    private List<TemplateData> templates = new ArrayList<>();
    private List<Boolean> selectedRows = new ArrayList<>();
    
    public void setTemplates(List<TemplateData> templates) {
        this.templates = templates != null ? templates : new ArrayList<>();
        this.selectedRows = new ArrayList<>();
        for (int i = 0; i < this.templates.size(); i++) {
            this.selectedRows.add(false);
        }
        fireTableDataChanged();
    }
    
    public boolean hasSelectedTemplates() {
        return selectedRows.contains(true);
    }
    
    public List<Integer> getSelectedTemplateIds() {
        List<Integer> selectedIds = new ArrayList<>();
        for (int i = 0; i < selectedRows.size(); i++) {
            if (selectedRows.get(i)) {
                selectedIds.add(templates.get(i).getIdTemplate());
            }
        }
        return selectedIds;
    }
    
    @Override
    public int getRowCount() {
        return templates.size();
    }
    
    @Override
    public int getColumnCount() {
        return columnNames.length;
    }
    
    @Override
    public String getColumnName(int columnIndex) {
        return columnNames[columnIndex];
    }
    
    @Override
    public Object getValueAt(int rowIndex, int columnIndex) {
        if (rowIndex >= templates.size()) return null;
        
        TemplateData template = templates.get(rowIndex);
        switch (columnIndex) {
            case 0: return selectedRows.get(rowIndex); // Checkbox
            case 1: return template.getIdTemplate();
            case 2: return template.getImageUrl(); // Image URL for renderer
            case 3: return template.getDescription();
            case 4: return template.getTimeUpdate();
            default: return null;
        }
    }
    
    @Override
    public void setValueAt(Object value, int rowIndex, int columnIndex) {
        if (columnIndex == 0 && rowIndex < selectedRows.size()) {
            selectedRows.set(rowIndex, (Boolean) value);
            fireTableCellUpdated(rowIndex, columnIndex);
            
            // Trigger update of train button state
            SwingUtilities.invokeLater(() -> {
                if (parentDialog != null) {
                    parentDialog.updateTrainButtonState();
                }
            });
        }
    }
    
    public void setParentDialog(AddModelDialog dialog) {
        this.parentDialog = dialog;
    }
    
    private AddModelDialog parentDialog;
    
    @Override
    public Class<?> getColumnClass(int columnIndex) {
        switch (columnIndex) {
            case 0: return Boolean.class; // Checkbox
            case 1: return Integer.class; // ID
            case 2: return String.class;  // Image URL
            default: return String.class;
        }
    }
    
    @Override
    public boolean isCellEditable(int rowIndex, int columnIndex) {
        return columnIndex == 0; // Only checkbox column is editable
    }
}