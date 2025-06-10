package frontend.uicustom;

import frontend.ApiClient;

import javax.swing.*;
import javax.swing.table.TableCellRenderer;
import java.awt.*;
import java.awt.image.BufferedImage;

public class ImageRenderer extends JLabel implements TableCellRenderer {
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
            
            try {
                ImageIcon icon = loadImageIcon(imageUrl);
                if (icon != null) {
                    Image img = icon.getImage().getScaledInstance(60, 60, Image.SCALE_SMOOTH);
                    setIcon(new ImageIcon(img));
                    setText("");
                } else {
                    setIcon(createPlaceholderIcon());
                }
            } catch (Exception e) {
                setIcon(createPlaceholderIcon());
                System.err.println("Error in ImageRenderer for " + imageUrl + ": " + e.getMessage());
            }
        } else {
            setIcon(createPlaceholderIcon());
        }
        return this;
    }
    
    private ImageIcon loadImageIcon(String imageUrl) {
        try {
            ImageIcon icon = apiClient.loadImageFromUrl(imageUrl);
            if (icon != null) {
                return icon;
            } else {
                System.out.println("ApiClient returned null for image");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        return createPlaceholderIcon();
    }
    
    private ImageIcon createPlaceholderIcon() {
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