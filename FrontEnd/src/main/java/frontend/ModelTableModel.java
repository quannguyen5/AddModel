package frontend;

import javax.swing.table.AbstractTableModel;
import java.util.ArrayList;
import java.util.List;

public class ModelTableModel extends AbstractTableModel {
    private final String[] columnNames = {
        "ID", "Model Name", "Type", "Version", "Accuracy (%)", "Last Update"
    };
    
    private List<ModelData> models = new ArrayList<>();
    
    public void setModels(List<ModelData> models) {
        this.models = models != null ? models : new ArrayList<>();
        fireTableDataChanged();
    }
    
    public ModelData getModelAt(int rowIndex) {
        return models.get(rowIndex);
    }
    
    @Override
    public int getRowCount() {
        return models.size();
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
        ModelData model = models.get(rowIndex);
        
        switch (columnIndex) {
            case 0: return model.getId();
            case 1: return model.getModelName();
            case 2: return model.getModelType();
            case 3: return model.getVersion();
            case 4: return String.format("%.2f", model.getAccuracy() * 100);
            case 5: return model.getLastUpdate();
            default: return null;
        }
    }
    
    @Override
    public Class<?> getColumnClass(int columnIndex) {
        switch (columnIndex) {
            case 0: return Integer.class;
            case 4: return String.class; // Accuracy as formatted string
            default: return String.class;
        }
    }
    
    @Override
    public boolean isCellEditable(int rowIndex, int columnIndex) {
        return false;
    }
}