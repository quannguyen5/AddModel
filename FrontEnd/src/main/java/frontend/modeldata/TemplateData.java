package frontend.modeldata;

import java.util.List;
import java.util.Map;

public class TemplateData {
    private int idTemplate;
    private String description;
    private String imageUrl;
    private String timeUpdate;
    private List<Map<String, Object>> labels;
    private List<Map<String, Object>> boundingBox;

    public int getIdTemplate() { return idTemplate; }
    public String getDescription() { return description; }
    public String getImageUrl() { return imageUrl; }
    public String getTimeUpdate() { return timeUpdate; }
    public List<Map<String, Object>> getLabels() { return labels; }
    public List<Map<String, Object>> getBoundingBox() { return boundingBox; }
}