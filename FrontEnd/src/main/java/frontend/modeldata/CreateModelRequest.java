package frontend.modeldata;

import java.util.List;

public class CreateModelRequest {
    private String model_name;
    private String model_type;
    private String version;
    private String description;
    private List<Integer> template_ids;
    private int epochs;
    private int batch_size;
    private double learning_rate;
    private double accuracy;

    public CreateModelRequest(String modelName, String modelType, String version,
                            String description, List<Integer> templateIds,
                            int epochs, int batchSize, double learningRate, double accuracy) {
        this.model_name = modelName;
        this.model_type = modelType;
        this.version = version;
        this.description = description;
        this.template_ids = templateIds;
        this.epochs = epochs;
        this.batch_size = batchSize;
        this.learning_rate = learningRate;
        this.accuracy = accuracy;
    }
}