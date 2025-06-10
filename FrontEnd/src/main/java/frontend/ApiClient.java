package frontend;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.lang.reflect.Type;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.List;
import java.util.Map;
import javax.swing.ImageIcon;
import frontend.modeldata.*;

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
                    ImageIcon icon = new ImageIcon(imageData);
                    
                    if (icon.getIconWidth() > 0 && icon.getIconHeight() > 0) {
                        return icon;
                    } else {
                        return null;
                    }
                } else {
                    return null;
                }
            } else {
                connection.disconnect();
                return null;
            }
        } catch (Exception e) {
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