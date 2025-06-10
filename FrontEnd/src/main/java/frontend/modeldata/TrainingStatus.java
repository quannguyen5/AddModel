package frontend.modeldata;

import java.util.Map;

public class TrainingStatus {
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