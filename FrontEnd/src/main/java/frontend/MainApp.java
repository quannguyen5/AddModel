package frontend;

import frontend.modeldata.ModelData;

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
        setTitle("Model Management");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1000, 600);
        setLocationRelativeTo(null);

        mainPanel = new JPanel(new BorderLayout());

        JPanel toolbar = createToolbar();
        mainPanel.add(toolbar, BorderLayout.NORTH);

        createModelTable();

        JLabel statusBar = new JLabel("Ready");
        statusBar.setBorder(BorderFactory.createEmptyBorder(5, 10, 5, 10));
        mainPanel.add(statusBar, BorderLayout.SOUTH);
        
        add(mainPanel);
    }
    
    private JPanel createToolbar() {
        JPanel toolbar = new JPanel(new FlowLayout(FlowLayout.LEFT));
        toolbar.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));
        
        JButton addButton = new JButton("Add Model");
        addButton.addActionListener(e -> openAddModelDialog());
        
        JButton refreshButton = new JButton("Refresh");
        refreshButton.addActionListener(e -> loadModels());
        
        JButton deleteButton = new JButton("Delete");
        
        toolbar.add(addButton);
        toolbar.add(refreshButton);
        toolbar.add(deleteButton);
        
        return toolbar;
    }
    
    private void createModelTable() {
        modelTableModel = new ModelTableModel();
        modelTable = new JTable(modelTableModel);
        modelTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);

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
    
    private void openAddModelDialog() {
        AddModelDialog dialog = new AddModelDialog(this, apiClient);
        dialog.setVisible(true);
        if (dialog.isModelAdded()) {
            loadModels();
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