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
        this.templateServiceUrl = "http://localhost:8003"; // Template service URL
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
        
        return (String) result.get("message");
    }
    
    public void deleteModel(int modelId) throws Exception {
        sendDeleteRequest(modelServiceUrl + "/models/" + modelId);
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
    
    public ImageIcon loadImageFromUrl(String imageUrl) {
        if (imageUrl == null || imageUrl.isEmpty()) {
            return null;
        }
        
        try {
            System.out.println("Loading image from URL: " + imageUrl);
            
            // If it's already a full HTTP URL, use it directly
            if (imageUrl.startsWith("http")) {
                return loadImageWithTimeout(imageUrl);
            }
            
            // If it's a local path, convert to template service URL
            String filename = extractFilename(imageUrl);
            String encodedFilename = URLEncoder.encode(filename, "UTF-8");
            String templateImageUrl = templateServiceUrl + "/images/" + encodedFilename;
            
            System.out.println("Converted to template URL: " + templateImageUrl);
            return loadImageWithTimeout(templateImageUrl);
            
        } catch (Exception e) {
            System.err.println("Failed to load image from: " + imageUrl + " - " + e.getMessage());
            return null;
        }
    }
    
    private ImageIcon loadImageWithTimeout(String urlString) {
        try {
            System.out.println("Attempting to load image from: " + urlString);
            
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
            System.out.println("HTTP Response Code: " + responseCode + " for " + urlString);
            
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
    
    public boolean testTemplateServiceConnection() {
        try {
            String response = sendGetRequest(templateServiceUrl + "/health");
            System.out.println("Template service health check: " + response);
            return true;
        } catch (Exception e) {
            System.err.println("Template service connection failed: " + e.getMessage());
            return false;
        }
    }
    
    public boolean testImageEndpoint(String filename) {
        try {
            String encodedFilename = URLEncoder.encode(filename, "UTF-8");
            String testUrl = templateServiceUrl + "/images/" + encodedFilename;
            
            URL url = new URL(testUrl);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod("HEAD");
            connection.setConnectTimeout(5000);
            
            int responseCode = connection.getResponseCode();
            System.out.println("Image endpoint test for " + filename + ": " + responseCode);
            connection.disconnect();
            
            return responseCode == 200;
        } catch (Exception e) {
            System.err.println("Image endpoint test failed for " + filename + ": " + e.getMessage());
            return false;
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
    
    private void sendDeleteRequest(String urlString) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("DELETE");
        connection.setRequestProperty("Content-Type", "application/json");
        
        int responseCode = connection.getResponseCode();
        if (responseCode < 200 || responseCode >= 300) {
            BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getErrorStream()));
            StringBuilder response = new StringBuilder();
            String line;
            
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            
            reader.close();
            throw new Exception("HTTP " + responseCode + ": " + response.toString());
        }
        
        connection.disconnect();
    }
}

// Data classes
class ModelData {
    private int idModel;
    private String modelName;
    private String modelType;
    private String version;
    private String description;
    private String lastUpdate;
    private double accuracy;
    
    // Getters and setters
    public int getId() { return idModel; }
    public void setId(int id) { this.idModel = id; }
    
    public String getModelName() { return modelName; }
    public void setModelName(String modelName) { this.modelName = modelName; }
    
    public String getModelType() { return modelType; }
    public void setModelType(String modelType) { this.modelType = modelType; }
    
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public String getLastUpdate() { return lastUpdate; }
    public void setLastUpdate(String lastUpdate) { this.lastUpdate = lastUpdate; }
    
    public double getAccuracy() { return accuracy; }
    public void setAccuracy(double accuracy) { this.accuracy = accuracy; }
}

class TemplateData {
    private int idTemplate;
    private String description;
    private String imageUrl;
    private String timeUpdate;
    
    // Getters and setters
    public int getIdTemplate() { return idTemplate; }
    public void setIdTemplate(int idTemplate) { this.idTemplate = idTemplate; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }
    
    public String getTimeUpdate() { return timeUpdate; }
    public void setTimeUpdate(String timeUpdate) { this.timeUpdate = timeUpdate; }
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
    
    // Constructors
    public CreateModelRequest() {}
    
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
    
    // Getters and setters
    public String getModel_name() { return model_name; }
    public void setModel_name(String model_name) { this.model_name = model_name; }
    
    public String getModel_type() { return model_type; }
    public void setModel_type(String model_type) { this.model_type = model_type; }
    
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public List<Integer> getTemplate_ids() { return template_ids; }
    public void setTemplate_ids(List<Integer> template_ids) { this.template_ids = template_ids; }
    
    public int getEpochs() { return epochs; }
    public void setEpochs(int epochs) { this.epochs = epochs; }
    
    public int getBatch_size() { return batch_size; }
    public void setBatch_size(int batch_size) { this.batch_size = batch_size; }
    
    public double getLearning_rate() { return learning_rate; }
    public void setLearning_rate(double learning_rate) { this.learning_rate = learning_rate; }
    
    public double getAccuracy() { return accuracy; }
    public void setAccuracy(double accuracy) { this.accuracy = accuracy; }
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
    
    // Constructors and getters/setters
    public TrainRequest() {}
    
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
    
    // Getters and setters
    public String getModel_name() { return model_name; }
    public void setModel_name(String model_name) { this.model_name = model_name; }
    
    public String getModel_type() { return model_type; }
    public void setModel_type(String model_type) { this.model_type = model_type; }
    
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    
    public List<Integer> getTemplate_ids() { return template_ids; }
    public void setTemplate_ids(List<Integer> template_ids) { this.template_ids = template_ids; }
    
    public int getEpochs() { return epochs; }
    public void setEpochs(int epochs) { this.epochs = epochs; }
    
    public int getBatch_size() { return batch_size; }
    public void setBatch_size(int batch_size) { this.batch_size = batch_size; }
    
    public int getImage_size() { return image_size; }
    public void setImage_size(int image_size) { this.image_size = image_size; }
    
    public double getLearning_rate() { return learning_rate; }
    public void setLearning_rate(double learning_rate) { this.learning_rate = learning_rate; }
}

class TrainResponse {
    private boolean success;
    private String model_id;
    private String message;
    
    // Getters and setters
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