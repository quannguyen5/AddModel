package frontend.modeldata;

import java.util.List;

public class TrainRequest {
    private String model_name;
    private String model_type;
    private String version;
    private List<Integer> template_ids;
    private int epochs;
    private int batch_size;
    private int image_size;
    private double learning_rate;

    public TrainRequest(String modelName, String modelType, String version,
                       List<Integer> templateIds, int epochs, int batchSize,
                       int imageSize, double learningRate) {
        this.model_name = modelName;
        this.model_type = modelType;
        this.version = version;
        this.template_ids = templateIds;
        this.epochs = epochs;
        this.batch_size = batchSize;
        this.image_size = imageSize;
        this.learning_rate = learningRate;
    }
}