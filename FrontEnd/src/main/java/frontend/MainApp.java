package frontend;

import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.List;

public class MainApp extends JFrame {
    private static final String MODEL_SERVICE_URL = "http://localhost:8001";
    private static final String TRAIN_SERVICE_URL = "http://localhost:8002";
    
    private JPanel mainPanel;
    private JTable modelTable;
    private ModelTableModel modelTableModel;
    private ApiClient apiClient;
    
    public MainApp() {
        apiClient = new ApiClient(MODEL_SERVICE_URL, TRAIN_SERVICE_URL);
        initializeUI();
        loadModels();
    }
    
    private void initializeUI() {
        setTitle("YOLO Model Management System");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1000, 600);
        setLocationRelativeTo(null);
        
        // Create menu bar
        createMenuBar();
        
        // Create main panel
        mainPanel = new JPanel(new BorderLayout());
        
        // Create toolbar
        JPanel toolbar = createToolbar();
        mainPanel.add(toolbar, BorderLayout.NORTH);
        
        // Create model table
        createModelTable();
        
        // Create status bar
        JLabel statusBar = new JLabel("Ready");
        statusBar.setBorder(BorderFactory.createEmptyBorder(5, 10, 5, 10));
        mainPanel.add(statusBar, BorderLayout.SOUTH);
        
        add(mainPanel);
    }
    
    private void createMenuBar() {
        JMenuBar menuBar = new JMenuBar();
        
        // File menu
        JMenu fileMenu = new JMenu("File");
        JMenuItem refreshItem = new JMenuItem("Refresh");
        refreshItem.addActionListener(e -> loadModels());
        JMenuItem exitItem = new JMenuItem("Exit");
        exitItem.addActionListener(e -> System.exit(0));
        
        fileMenu.add(refreshItem);
        fileMenu.addSeparator();
        fileMenu.add(exitItem);
        
        // Model menu
        JMenu modelMenu = new JMenu("Model");
        JMenuItem addModelItem = new JMenuItem("Add New Model");
        addModelItem.addActionListener(e -> openAddModelDialog());
        JMenuItem deleteModelItem = new JMenuItem("Delete Model");
        deleteModelItem.addActionListener(e -> deleteSelectedModel());
        
        modelMenu.add(addModelItem);
        modelMenu.add(deleteModelItem);
        
        menuBar.add(fileMenu);
        menuBar.add(modelMenu);
        
        setJMenuBar(menuBar);
    }
    
    private JPanel createToolbar() {
        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.LEFT));
        toolbar.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));
        
        JButton addButton = new JButton("Add Model");
        addButton.setIcon(createIcon("+")); // Simple text icon
        addButton.addActionListener(e -> openAddModelDialog());
        
        JButton refreshButton = new JButton("Refresh");
        refreshButton.setIcon(createIcon("↻"));
        refreshButton.addActionListener(e -> loadModels());
        
        JButton deleteButton = new JButton("Delete");
        deleteButton.setIcon(createIcon("✗"));
        deleteButton.addActionListener(e -> deleteSelectedModel());
        
        toolbar.add(addButton);
        toolbar.add(refreshButton);
        toolbar.add(deleteButton);
        
        return toolbar;
    }
    
    private void createModelTable() {
        modelTableModel = new ModelTableModel();
        modelTable = new JTable(modelTableModel);
        modelTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        
        // Set column widths
        modelTable.getColumnModel().getColumn(0).setPreferredWidth(50);  // ID
        modelTable.getColumnModel().getColumn(1).setPreferredWidth(200); // Name
        modelTable.getColumnModel().getColumn(2).setPreferredWidth(150); // Type
        modelTable.getColumnModel().getColumn(3).setPreferredWidth(100); // Version
        modelTable.getColumnModel().getColumn(4).setPreferredWidth(100); // Accuracy
        modelTable.getColumnModel().getColumn(5).setPreferredWidth(150); // Last Update
        
        JScrollPane scrollPane = new JScrollPane(modelTable);
        scrollPane.setBorder(BorderFactory.createTitledBorder("Models"));
        
        mainPanel.add(scrollPane, BorderLayout.CENTER);
    }
    
    private Icon createIcon(String text) {
        return new Icon() {
            @Override
            public void paintIcon(Component c, Graphics g, int x, int y) {
                g.setFont(new Font("Arial", Font.BOLD, 12));
                g.drawString(text, x, y + 12);
            }
            
            @Override
            public int getIconWidth() { return 20; }
            
            @Override
            public int getIconHeight() { return 16; }
        };
    }
    
    private void openAddModelDialog() {
        AddModelDialog dialog = new AddModelDialog(this, apiClient);
        dialog.setVisible(true);
        
        // Refresh models after dialog closes
        if (dialog.isModelAdded()) {
            loadModels();
        }
    }
    
    private void deleteSelectedModel() {
        int selectedRow = modelTable.getSelectedRow();
        if (selectedRow == -1) {
            JOptionPane.showMessageDialog(this, "Please select a model to delete.", "No Selection", JOptionPane.WARNING_MESSAGE);
            return;
        }
        
        ModelData model = modelTableModel.getModelAt(selectedRow);
        
        int result = JOptionPane.showConfirmDialog(
            this,
            "Are you sure you want to delete model: " + model.getModelName() + "?",
            "Confirm Delete",
            JOptionPane.YES_NO_OPTION
        );
        
        if (result == JOptionPane.YES_OPTION) {
            try {
                apiClient.deleteModel(model.getId());
                loadModels();
                JOptionPane.showMessageDialog(this, "Model deleted successfully!", "Success", JOptionPane.INFORMATION_MESSAGE);
            } catch (Exception e) {
                JOptionPane.showMessageDialog(this, "Error deleting model: " + e.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
            }
        }
    }
    
    private void loadModels() {
        SwingWorker<List<ModelData>, Void> worker = new SwingWorker<List<ModelData>, Void>() {
            @Override
            protected List<ModelData> doInBackground() throws Exception {
                return apiClient.getAllModels();
            }
            
            @Override
            protected void done() {
                try {
                    List<ModelData> models = get();
                    modelTableModel.setModels(models);
                } catch (Exception e) {
                    JOptionPane.showMessageDialog(MainApp.this, "Error loading models: " + e.getMessage(), "Error", JOptionPane.ERROR_MESSAGE);
                }
            }
        };
        worker.execute();
    }
    
    public static void main(String[] args) {
        // Set look and feel
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        SwingUtilities.invokeLater(() -> {
            new MainApp().setVisible(true);
        });
    }
}