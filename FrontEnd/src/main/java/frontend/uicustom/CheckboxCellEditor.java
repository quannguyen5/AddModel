package frontend.uicustom;

import javax.swing.*;
import javax.swing.table.TableCellEditor;
import java.awt.*;

public class CheckboxCellEditor extends AbstractCellEditor implements TableCellEditor {
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