package frontend.uicustom;

public class SimpleDocumentListener implements javax.swing.event.DocumentListener {
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