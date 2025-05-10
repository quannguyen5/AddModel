import os
import time
import json
import threading
from datetime import datetime
from colab_integration import colab_trainer

# File lưu trữ trạng thái
TRAINING_STATES_FILE = "training_states.json"

# Khởi tạo trạng thái
training_states = {}

def load_training_states():
    """Load training states from file"""
    if os.path.exists(TRAINING_STATES_FILE):
        try:
            with open(TRAINING_STATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading training states: {e}")
            return {}
    return {}

def save_training_states(states):
    """Save training states to file"""
    try:
        with open(TRAINING_STATES_FILE, 'w', encoding='utf-8') as f:
            # Use ensure_ascii=True để tránh lỗi Unicode trên Windows
            json.dump(states, f, indent=2, ensure_ascii=True)
    except Exception as e:
        print(f"Error saving training states: {e}")

# Load states from file if exists
training_states = load_training_states()

def get_training_status(model_id):
    """Get training status for a model"""
    model_id = str(model_id)
    
    # Reload from file to get fresh data
    global training_states
    training_states = load_training_states()
    
    if model_id not in training_states:
        return {'status': 'not_found'}
    
    state = training_states[model_id]
    
    # If the status is 'training' or 'monitoring', check with Colab for updates
    if state['status'] in ['training', 'monitoring'] and 'colab_session_id' in state:
        try:
            # Get updated status from Colab
            colab_status = colab_trainer.get_training_status(model_id)
            
            if colab_status.get('status') != 'not_found':
                # Update our state with Colab data
                state.update({
                    'status': colab_status.get('status', state['status']),
                    'current_epoch': colab_status.get('current_epoch', state.get('current_epoch', 0)),
                    'progress': colab_status.get('progress', state.get('progress', 0)),
                    'metrics': colab_status.get('metrics', state.get('metrics', {})),
                    'epoch_metrics': colab_status.get('epoch_metrics', state.get('epoch_metrics', {})),
                })
                
                # Special handling for completed state
                if colab_status.get('status') == 'completed':
                    state['status'] = 'completed'
                    state['progress'] = 100
                    state['current_epoch'] = state.get('total_epochs', 100)
                
                # Save updated state
                training_states[model_id] = state
                save_training_states(training_states)
        except Exception as e:
            print(f"Error updating status from Colab: {e}")
    
    return state

def train_yolo_model(model_id, model_name, model_type, version, epochs, batch_size, image_size, learning_rate, template_ids):
    """Start model training with Google Colab"""
    model_id = str(model_id)
    print(f"Starting training setup for model ID: {model_id}, name: {model_name}")
    
    # Initialize training state
    training_states[model_id] = {
        'status': 'initializing',
        'progress': 0,
        'model_name': model_name,
        'model_type': model_type,
        'version': version,
        'current_epoch': 0,
        'total_epochs': epochs,
        'batch_size': batch_size,
        'learning_rate': learning_rate,
        'template_ids': template_ids,
        'metrics': {},
        'epoch_metrics': {},
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save state to file
    save_training_states(training_states)
    
    # Start Colab training process in background
    def _start_colab_training():
        try:
            # Update status to preparing dataset
            training_states[model_id]['status'] = 'preparing_dataset'
            save_training_states(training_states)
            
            # Import DAOs for dataset preparation
            from dao.fraud_template_dao import FraudTemplateDAO
            from dao.fraud_label_dao import FraudLabelDAO
            
            fraud_template_dao = FraudTemplateDAO()
            fraud_label_dao = FraudLabelDAO()
            
            # Start training with Colab
            training_result = colab_trainer.start_training(
                model_id=model_id,
                model_name=model_name,
                model_type=model_type,
                version=version,
                epochs=epochs,
                batch_size=batch_size,
                image_size=image_size,
                learning_rate=learning_rate,
                template_ids=template_ids,
                fraud_template_dao=fraud_template_dao,
                fraud_label_dao=fraud_label_dao
            )
            
            if not training_result['success']:
                # Handle error
                error_msg = training_result.get('message', 'Unknown error')
                print(f"Error starting Colab training: {error_msg}")
                training_states[model_id]['status'] = 'failed'
                training_states[model_id]['error'] = error_msg
                save_training_states(training_states)
                return
            
            # Update training state with Colab information
            training_states[model_id].update({
                'status': 'ready',
                'colab_session_id': model_id,
                'colab_url': training_result.get('colab_url', ''),
                'notebook_path': training_result.get('notebook_path', ''),
                'dataset_path': training_result.get('dataset_path', ''),
                'instructions': training_result.get('instructions', '')
            })
            
            save_training_states(training_states)
            print(f"Colab training setup completed for model ID: {model_id}")
            
        except Exception as e:
            # Handle exception
            error_msg = str(e)
            print(f"Error in Colab training setup: {error_msg}")
            training_states[model_id]['status'] = 'failed'
            training_states[model_id]['error'] = error_msg
            save_training_states(training_states)
    
    # Start the training thread
    thread = threading.Thread(target=_start_colab_training)
    thread.daemon = True
    thread.start()
    
    return {'success': True, 'message': 'Training setup started', 'model_id': model_id}

def register_colab_webhook(model_id, webhook_url):
    """Register a webhook URL for a Colab session"""
    model_id = str(model_id)
    
    if model_id not in training_states:
        return False
    
    # Register webhook with Colab trainer
    result = colab_trainer.register_webhook(model_id, webhook_url)
    
    if result['success']:
        # Update our state
        training_states[model_id]['status'] = 'monitoring'
        training_states[model_id]['webhook_url'] = webhook_url
        save_training_states(training_states)
        return True
    
    return False

def cancel_training(model_id):
    """Cancel a running training job"""
    model_id = str(model_id)
    print(f"Cancelling training for model ID: {model_id}")
    
    if model_id not in training_states:
        return False
    
    # For Colab we don't have a direct way to cancel, so we just mark it as cancelled
    training_states[model_id]['status'] = 'cancelled'
    save_training_states(training_states)
    
    return True

def download_trained_model(model_id, output_dir='models'):
    """Download trained model from Google Colab or local storage"""
    model_id = str(model_id)
    print(f"Downloading model {model_id}")
    
    if model_id not in training_states:
        return {'success': False, 'message': 'Model not found'}
    
    state = training_states[model_id]
    
    if state['status'] not in ['completed', 'uploaded']:
        return {'success': False, 'message': f"Model training not completed (status: {state['status']})"}
    
    # Try to download model
    try:
        # If the model has been uploaded to our system
        if 'model_path' in state and os.path.exists(state['model_path']):
            # Copy to output directory
            model_dir = os.path.join(output_dir, model_id)
            os.makedirs(model_dir, exist_ok=True)
            
            import shutil
            dest_path = os.path.join(model_dir, os.path.basename(state['model_path']))
            shutil.copy(state['model_path'], dest_path)
            
            return {
                'success': True,
                'message': 'Model copied from local storage',
                'model_path': dest_path
            }
        else:
            # Try to download from Colab storage
            download_result = colab_trainer.download_model(model_id, output_dir)
            
            if download_result['success']:
                # Update model path in state
                state['model_path'] = download_result['model_path']
                save_training_states(training_states)
                return download_result
            else:
                return {
                    'success': False,
                    'message': 'Model file not found. You need to upload the trained model file from Colab first.'
                }
    except Exception as e:
        error_msg = str(e)
        print(f"Error downloading model: {error_msg}")
        return {'success': False, 'message': f'Error downloading model: {error_msg}'}

def upload_trained_model(model_id, model_file):
    """Upload a trained model file from user (after manual Colab training)"""
    model_id = str(model_id)
    
    if model_id not in training_states:
        return {'success': False, 'message': 'Model training session not found'}
    
    try:
        # Upload model to our storage
        upload_result = colab_trainer.upload_trained_model(model_id, model_file)
        
        if upload_result['success']:
            # Update our state
            training_states[model_id]['status'] = 'uploaded'
            training_states[model_id]['model_path'] = upload_result['model_path']
            save_training_states(training_states)
            
            return upload_result
        else:
            return upload_result
    except Exception as e:
        error_msg = str(e)
        print(f"Error uploading model: {error_msg}")
        return {'success': False, 'message': f'Error uploading model: {error_msg}'}

def cleanup_training_data(model_id, keep_model=True):
    """Clean up training data after completion"""
    model_id = str(model_id)
    
    # We keep the model file but clean up temporary files
    if model_id in training_states:
        state = training_states[model_id]
        
        # Delete dataset file if it exists
        if 'dataset_path' in state and os.path.exists(state['dataset_path']):
            try:
                os.remove(state['dataset_path'])
                print(f"Deleted dataset file: {state['dataset_path']}")
            except Exception as e:
                print(f"Error deleting dataset file: {e}")
        
        # Delete notebook file if it exists
        if 'notebook_path' in state and os.path.exists(state['notebook_path']):
            try:
                os.remove(state['notebook_path'])
                print(f"Deleted notebook file: {state['notebook_path']}")
            except Exception as e:
                print(f"Error deleting notebook file: {e}")
        
        # Remove state if not keeping model
        if not keep_model:
            del training_states[model_id]
            save_training_states(training_states)
    
    return True