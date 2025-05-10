import os
import json
import shutil
from kaggle.api.kaggle_api_extended import KaggleApi

class KaggleModelTrainer:
    def __init__(self):
        # Initialize Kaggle API
        self.api = KaggleApi()
        self.api.authenticate()

        # Create directory for Kaggle credentials if it doesn't exist
        self.kaggle_dir = os.path.join(os.path.expanduser('~'), '.kaggle')
        os.makedirs(self.kaggle_dir, exist_ok=True)

    def get_training_progress(self, kernel_path, model_id):
        """Get detailed training progress from Kaggle kernel"""
        try:
            # Get kernel status first
            kernel_info = self.api.kernel_status(kernel_path)
            
            # Check if kernel exists
            if not kernel_info:
                return {
                    "success": False,
                    "error": "Kernel not found"
                }
            
            status = kernel_info.get('status', 'unknown')
            run_time = kernel_info.get('totalRunTime', 0)
            
            # If kernel is completed or has error, try to download progress.json
            if status in ['complete', 'error', 'running']:
                try:
                    # Create temp directory for output
                    temp_dir = f"temp_progress_{model_id}"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Download output
                    self.api.kernels_output(kernel_path, path=temp_dir)
                    
                    # Check for progress.json
                    progress_path = os.path.join(temp_dir, "progress.json")
                    if os.path.exists(progress_path):
                        with open(progress_path, 'r') as f:
                            progress_data = json.load(f)
                        
                        # Clean up
                        shutil.rmtree(temp_dir)
                        
                        return {
                            "success": True,
                            "kernel_status": status,
                            "run_time": run_time,
                            "progress_data": progress_data
                        }
                    else:
                        # No progress file yet
                        shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.error(f"Error downloading progress data: {str(e)}")
            
            # Return basic kernel status
            return {
                "success": True,
                "kernel_status": status,
                "run_time": run_time
            }
        except Exception as e:
            self.logger.error(f"Error getting training progress: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    def setup_credentials(self, username, key):
        cred_path = os.path.join(self.kaggle_dir, 'kaggle.json')
        try:
            with open(cred_path, 'w') as f:
                json.dump({"username": username, "key": key}, f)
            os.chmod(cred_path, 0o600)  # Set permissions
            self.logger.info(f"Saved Kaggle credentials to {cred_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set Kaggle credentials: {str(e)}")
            return False

    def create_kaggle_dataset(self, model_id, template_ids, fraud_template_dao, fraud_label_dao):
        """Create Kaggle Dataset from selected templates"""
        # Initialize temp folder for dataset preparation
        dataset_folder = f"temp_dataset_{model_id}"
        dataset_path = Path(dataset_folder)
        
        # Create directory structure
        dataset_path.mkdir(exist_ok=True)
        (dataset_path / "images").mkdir(exist_ok=True)
        (dataset_path / "labels").mkdir(exist_ok=True)
        
        # Prepare dataset info
        dataset_name = f"yolo-fraud-detection-{model_id}-{int(time.time())}"
        dataset_title = f"YOLO Fraud Detection Dataset {model_id}"
        
        # Create metadata for the dataset
        metadata = {
            "title": dataset_title,
            "id": f"_internal/{dataset_name}",
            "licenses": [{"name": "CC0-1.0"}]
        }
        
        with open(dataset_path / "dataset-metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Create dataset.yaml for YOLOv8
        yaml_content = """
# YOLOv8 dataset configuration
path: ../
train: images/
val: images/

# Classes
names:
  0: HumanDetect
  1: literal
"""
        
        with open(dataset_path / "dataset.yaml", "w") as f:
            f.write(yaml_content)
        
        # Process each template
        processed_images = 0
        for template_id in template_ids:
            # Get template from database
            template = fraud_template_dao.get_by_id(int(template_id))
            
            if not template:
                self.logger.warning(f"Template ID not found: {template_id}")
                continue
            
            # Get image path
            image_path = template.imageUrl
            if image_path.startswith('/'):
                image_path = image_path[1:]  # Remove leading slash if present
            
            # Check if image file exists
            if not os.path.exists(image_path):
                self.logger.warning(f"Image file not found: {image_path}")
                continue
            
            # New image filename
            image_filename = f"img_{template_id}.jpg"
            
            try:
                # Copy image to dataset folder
                shutil.copy(
                    image_path,
                    str(dataset_path / "images" / image_filename)
                )
                
                # Create YOLO format annotation if bounding boxes exist
                if template.boundingBox and len(template.boundingBox) > 0:
                    with open(dataset_path / "labels" / f"img_{template_id}.txt", "w") as f:
                        for box in template.boundingBox:
                            # Get class id from label
                            label = fraud_label_dao.get_by_id(box.fraudLabelId)
                            class_id = 0  # Default class
                            
                            if label and label.typeLabel:
                                type_label = label.typeLabel
                                if isinstance(type_label, str):
                                    if type_label == "HumanDetect":
                                        class_id = 0
                                    elif type_label == "literal":
                                        class_id = 1
                            
                            # YOLO format: <class_id> <x_center> <y_center> <width> <height>
                            f.write(f"{class_id} {box.xCenter} {box.yCenter} {box.width} {box.height}\n")
                processed_images += 1
            except Exception as e:
                self.logger.error(f"Error processing template {template_id}: {str(e)}")
        
        # Check if we have enough images
        if processed_images == 0:
            self.logger.error("No valid images were processed")
            return {
                "success": False,
                "error": "No valid images were processed"
            }
        
        # Upload dataset to Kaggle
        try:
            self.logger.info(f"Uploading dataset {dataset_name} to Kaggle...")
            self.api.dataset_create_new(folder=str(dataset_path), convert_to_csv=False, dir_mode="zip")
            self.logger.info(f"Dataset upload successful: {dataset_name}")
            
            # Clean up temp folder
            shutil.rmtree(str(dataset_path))
            
            return {
                "success": True,
                "dataset_name": dataset_name,
                "dataset_path": f"_internal/{dataset_name}"
            }
        except Exception as e:
            self.logger.error(f"Error uploading dataset: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_training_kernel(self, model_id, dataset_path, config):
        """
        Create and upload a new Kaggle kernel for training
        
        Args:
            model_id: Model ID
            dataset_path: Path to the dataset on Kaggle
            config: Training configuration
            
        Returns:
            Dict with results
        """
        # Add timestamp to prevent duplicates
        timestamp = int(time.time())
        
        # Create safe slug for kernel
        kernel_slug = f"yolo-train-model-{model_id}-{timestamp}"
        
        # Create temp directory for kernel
        kernel_folder = f"temp_kernel_{model_id}"
        kernel_path = Path(kernel_folder)
        kernel_path.mkdir(exist_ok=True)
        
        # Get username from Kaggle credentials
        username = "_internal"  # Default
        try:
            cred_path = Path(self.kaggle_dir) / 'kaggle.json'
            if cred_path.exists():
                with open(cred_path, 'r') as f:
                    creds = json.load(f)
                    username = creds.get('username', "_internal")
        except Exception as e:
            self.logger.warning(f"Could not get username from credentials: {e}")
        
        # Create kernel metadata
        kernel_metadata = {
            "id": f"{username}/{kernel_slug}",
            "title": f"YOLO Train Model {model_id} {timestamp}",
            "code_file": "train.py",
            "language": "python",
            "kernel_type": "script",
            "is_private": True,
            "enable_gpu": True,
            "enable_internet": True,
            "dataset_sources": [dataset_path],
            "competition_sources": [],
            "kernel_sources": []
        }
        
        # Write metadata file
        with open(kernel_path / "kernel-metadata.json", "w") as f:
            json.dump(kernel_metadata, f, indent=2)
        
        # Create training script
        training_script = self._create_training_script(model_id, dataset_path, config)
        
        # Write script to file
        with open(kernel_path / "train.py", "w", encoding='utf-8') as f:
            f.write(training_script)
        
        # Debug info
        self.logger.info(f"Creating kernel {kernel_slug} on Kaggle...")
        self.logger.info(f"Using dataset: {dataset_path}")
        
        # Store current directory
        original_dir = os.getcwd()
        
        try:
            # Change to kernel directory for API call
            os.chdir(str(kernel_path.absolute()))
            self.logger.info(f"Changed working directory to: {os.getcwd()}")
            
            # Push kernel to Kaggle
            response = self.api.kernels_push(".")
            self.logger.info(f"Kernel push successful, response: {response}")
            
            # Return to original directory
            os.chdir(original_dir)
            
            # Clean up temp folder
            shutil.rmtree(str(kernel_path))
            
            return {
                "success": True,
                "kernel_name": kernel_slug,
                "kernel_path": f"{username}/{kernel_slug}"
            }
        except Exception as e:
            self.logger.error(f"Error creating kernel: {type(e).__name__}: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Make sure we return to original directory
            try:
                if os.getcwd() != original_dir:
                    os.chdir(original_dir)
            except:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def download_model(self, model_id, kernel_path, output_dir='models'):
        """Download trained model from Kaggle kernel"""
        try:
            # Create destination directory
            model_dir = os.path.join(output_dir, str(model_id))
            os.makedirs(model_dir, exist_ok=True)
            
            # Download all output files from kernel
            self.logger.info(f"Downloading output from kernel {kernel_path}...")
            self.api.kernels_output(kernel_path, path=model_dir)
            
            # Check for downloaded model files
            model_files = []
            for root, _, files in os.walk(model_dir):
                for file in files:
                    if file.endswith(('.pt', '.onnx', '.pth')):
                        model_files.append(os.path.join(root, file))
            
            if not model_files:
                return {
                    'success': False, 
                    'message': 'No model files found in output'
                }
            
            # Get latest model file (usually best.pt or last.pt)
            best_model = None
            for model_file in model_files:
                file_name = os.path.basename(model_file).lower()
                if file_name == 'best.pt':
                    best_model = model_file
                    break
                elif file_name == 'last.pt' and not best_model:
                    best_model = model_file
            
            # If no best/last model, use first one found
            if not best_model and model_files:
                best_model = model_files[0]
            
            return {
                'success': True, 
                'message': 'Model downloaded successfully',
                'model_path': best_model,
                'all_files': model_files
            }
        except Exception as e:
            self.logger.error(f"Error downloading model: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {'success': False, 'message': f"Error downloading model: {str(e)}"}

# Create global instance
kaggle_trainer = KaggleModelTrainer()