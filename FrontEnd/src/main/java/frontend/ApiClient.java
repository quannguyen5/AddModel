package frontend;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.IOException;
import java.lang.reflect.Type;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.List;
import java.util.Map;
import javax.swing.ImageIcon;

public class ApiClient {
    private final String modelServiceUrl;
    private final String trainServiceUrl;
    private final String templateServiceUrl;
    private final Gson gson;
    
    public ApiClient(String modelServiceUrl, String trainServiceUrl) {
        this.modelServiceUrl = modelServiceUrl;
        this.trainServiceUrl = trainServiceUrl;
        this.templateServiceUrl = "http://localhost:8003";
        this.gson = new Gson();
    }
    
    public List<ModelData> getAllModels() throws Exception {
        String response = sendGetRequest(modelServiceUrl + "/models");
        Type listType = new TypeToken<List<ModelData>>(){}.getType();
        return gson.fromJson(response, listType);
    }
    
    public List<TemplateData> getAllTemplates() throws Exception {
        String response = sendGetRequest(templateServiceUrl + "/templates");
        Type listType = new TypeToken<List<TemplateData>>(){}.getType();
        return gson.fromJson(response, listType);
    }
    
    public List<String> getModelTypes() throws Exception {
        String response = sendGetRequest(modelServiceUrl + "/model-types");
        Map<String, List<String>> result = gson.fromJson(response, Map.class);
        return result.get("model_types");
    }
    
    public String createModel(CreateModelRequest request) throws Exception {
        String jsonRequest = gson.toJson(request);
        String response = sendPostRequest(modelServiceUrl + "/models", jsonRequest);
        Map<String, Object> result = gson.fromJson(response, Map.class);
        
        if (!(Boolean) result.get("success")) {
            throw new Exception((String) result.get("message"));
        }
        
        return "Model created successfully!";
    }
    
    public TrainResponse startTraining(TrainRequest request) throws Exception {
        String jsonRequest = gson.toJson(request);
        String response = sendPostRequest(trainServiceUrl + "/train", jsonRequest);
        return gson.fromJson(response, TrainResponse.class);
    }
    
    public TrainingStatus getTrainingStatus(String modelId) throws Exception {
        String response = sendGetRequest(trainServiceUrl + "/status/" + modelId);
        return gson.fromJson(response, TrainingStatus.class);
    }
    
    public void cancelTraining(String modelId) throws Exception {
        sendPostRequest(trainServiceUrl + "/cancel/" + modelId, "{}");
    }
    
    public DeleteResponse deleteTrainingFolder(String modelId) throws Exception {
        String response = sendDeleteRequest(trainServiceUrl + "/delete-training/" + modelId);
        return gson.fromJson(response, DeleteResponse.class);
    }
    
    public void cleanupFailedTraining(String modelId) throws Exception {
        sendPostRequest(trainServiceUrl + "/cleanup/" + modelId, "{}");
    }
    
    public ImageIcon loadImageFromUrl(String imageUrl) {
        if (imageUrl == null || imageUrl.isEmpty()) {
            return null;
        }
        
        try {
            String filename = extractFilename(imageUrl);
            String encodedFilename = URLEncoder.encode(filename, "UTF-8");
            String templateImageUrl = templateServiceUrl + "/images/" + encodedFilename;
            return loadImageWithTimeout(templateImageUrl);
            
        } catch (Exception e) {
            System.err.println(e.getMessage());
            return null;
        }
    }
    
    private ImageIcon loadImageWithTimeout(String urlString) {
        try {
            URL url = new URL(urlString);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            
            connection.setRequestMethod("GET");
            connection.setRequestProperty("User-Agent", "Java-YOLO-Client/1.0");
            connection.setRequestProperty("Accept", "image/*,*/*");
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(15000);
            connection.setDoInput(true);
            connection.setInstanceFollowRedirects(true);
            
            int responseCode = connection.getResponseCode();
            
            if (responseCode == 200) {
                byte[] imageData = connection.getInputStream().readAllBytes();
                connection.disconnect();
                
                if (imageData.length > 0) {
                    System.out.println("Image loaded successfully, size: " + imageData.length + " bytes");
                    ImageIcon icon = new ImageIcon(imageData);
                    
                    if (icon.getIconWidth() > 0 && icon.getIconHeight() > 0) {
                        System.out.println("Image dimensions: " + icon.getIconWidth() + "x" + icon.getIconHeight());
                        return icon;
                    } else {
                        System.err.println("Invalid image data received");
                        return null;
                    }
                } else {
                    System.err.println("Empty image data received");
                    return null;
                }
            } else {
                System.err.println("HTTP " + responseCode + " for image: " + urlString);
                connection.disconnect();
                return null;
            }
        } catch (Exception e) {
            System.err.println("Exception loading image from " + urlString + ": " + e.getMessage());
            return null;
        }
    }
    
    public String extractFilename(String path) {
        if (path == null) return "";
        
        if (path.contains("/")) {
            return path.substring(path.lastIndexOf("/") + 1);
        }
        return path;
    }
    
    private String sendGetRequest(String urlString) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");
        connection.setRequestProperty("Content-Type", "application/json");
        
        int responseCode = connection.getResponseCode();
        if (responseCode != 200) {
            throw new Exception("HTTP " + responseCode + ": " + connection.getResponseMessage());
        }
        
        BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        StringBuilder response = new StringBuilder();
        String line;
        
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        
        reader.close();
        connection.disconnect();
        
        return response.toString();
    }
    
    private String sendPostRequest(String urlString, String jsonInputString) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setDoOutput(true);
        
        try (OutputStream os = connection.getOutputStream()) {
            byte[] input = jsonInputString.getBytes("utf-8");
            os.write(input, 0, input.length);
        }
        
        int responseCode = connection.getResponseCode();
        BufferedReader reader;
        
        if (responseCode >= 200 && responseCode < 300) {
            reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        } else {
            reader = new BufferedReader(new InputStreamReader(connection.getErrorStream()));
        }
        
        StringBuilder response = new StringBuilder();
        String line;
        
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        
        reader.close();
        connection.disconnect();
        
        if (responseCode < 200 || responseCode >= 300) {
            throw new Exception("HTTP " + responseCode + ": " + response.toString());
        }
        
        return response.toString();
    }
    
    private String sendDeleteRequest(String urlString) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("DELETE");
        connection.setRequestProperty("Content-Type", "application/json");
        
        int responseCode = connection.getResponseCode();
        BufferedReader reader;
        
        if (responseCode >= 200 && responseCode < 300) {
            reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
        } else {
            reader = new BufferedReader(new InputStreamReader(connection.getErrorStream()));
        }
        
        StringBuilder response = new StringBuilder();
        String line;
        
        while ((line = reader.readLine()) != null) {
            response.append(line);
        }
        
        reader.close();
        connection.disconnect();
        
        if (responseCode < 200 || responseCode >= 300) {
            throw new Exception("HTTP " + responseCode + ": " + response.toString());
        }
        
        return response.toString();
    }
}


// Các class data
class ModelData {
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

class TemplateData {
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

class CreateModelRequest {
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

class TrainRequest {
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

class TrainResponse {
    private boolean success;
    private String model_id;
    private String message;

    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }
    
    public String getModel_id() { return model_id; }
    public void setModel_id(String model_id) { this.model_id = model_id; }
    
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}

class TrainingStatus {
    private String status;
    private String model_id;
    private String model_name;
    private int current_epoch;
    private int total_epochs;
    private String start_time;
    private String end_time;
    private String error;
    private Map<String, Object> final_metrics;
    private Map<String, Object> dataset_info;
    private String model_path;
    
    // Getters and setters
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    
    public String getModel_id() { return model_id; }
    public void setModel_id(String model_id) { this.model_id = model_id; }
    
    public String getModel_name() { return model_name; }
    public void setModel_name(String model_name) { this.model_name = model_name; }
    
    public int getCurrent_epoch() { return current_epoch; }
    public void setCurrent_epoch(int current_epoch) { this.current_epoch = current_epoch; }
    
    public int getTotal_epochs() { return total_epochs; }
    public void setTotal_epochs(int total_epochs) { this.total_epochs = total_epochs; }
    
    public String getStart_time() { return start_time; }
    public void setStart_time(String start_time) { this.start_time = start_time; }
    
    public String getEnd_time() { return end_time; }
    public void setEnd_time(String end_time) { this.end_time = end_time; }
    
    public String getError() { return error; }
    public void setError(String error) { this.error = error; }
    
    public Map<String, Object> getFinal_metrics() { return final_metrics; }
    public void setFinal_metrics(Map<String, Object> final_metrics) { this.final_metrics = final_metrics; }
    
    public Map<String, Object> getDataset_info() { return dataset_info; }
    public void setDataset_info(Map<String, Object> dataset_info) { this.dataset_info = dataset_info; }
    
    public String getModel_path() { return model_path; }
    public void setModel_path(String model_path) { this.model_path = model_path; }
}

class DeleteResponse {
    private boolean success;
    private String message;
    
    public boolean isSuccess() { return success; }
    public void setSuccess(boolean success) { this.success = success; }
    
    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }
}