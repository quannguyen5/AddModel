package frontend.modeldata;

public class ModelData {
    private int idModel;
    private String modelName;
    private String modelType;
    private String version;
    private String description;
    private String lastUpdate;
    private double accuracy;

    public int getId() { return idModel; }
    public String getModelName() { return modelName; }
    public String getModelType() { return modelType; }
    public String getVersion() { return version; }
    public String getLastUpdate() { return lastUpdate; }
    public double getAccuracy() { return accuracy; }
}