package frontend.modeldata;

public class TrainResponse {
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