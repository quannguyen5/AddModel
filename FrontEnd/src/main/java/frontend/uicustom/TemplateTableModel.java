package frontend.uicustom;

import frontend.AddModelDialog;
import frontend.modeldata.*;

import javax.swing.*;
import javax.swing.table.AbstractTableModel;
import java.util.*;

public class TemplateTableModel extends AbstractTableModel {
    private final String[] columnNames = {"Select", "ID", "Image", "Description", "Labels", "Time Update"};
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
            case 4: return formatLabels(template.getLabels()); // Labels column
            case 5: return template.getTimeUpdate();
            default: return null;
        }
    }
    
    private String formatLabels(List<Map<String, Object>> labels) {
        if (labels == null || labels.isEmpty()) {
            return "No labels";
        }
        
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < labels.size(); i++) {
            Map<String, Object> label = labels.get(i);
            if (i > 0) sb.append(", ");
            sb.append(label.get("typeLabel"));
        }
        
        return sb.toString();
    }
    public void setParentDialog(AddModelDialog dialog) {
        this.parentDialog = dialog;
    }

    private AddModelDialog parentDialog;

}