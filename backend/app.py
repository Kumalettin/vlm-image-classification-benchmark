"""
Flask API Server for Multimodal Image Classifier.
"""
import sys
from pathlib import Path

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import werkzeug
if not hasattr(werkzeug, "__version__"):
    try:
        import importlib.metadata
        werkzeug.__version__ = importlib.metadata.version("werkzeug")
    except Exception:
        werkzeug.__version__ = "3.0.1"

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import traceback
from typing import Dict, Any

from backend.config import (
    HOST,
    PORT,
    DEBUG,
    SECRET_KEY,
    CORS_ORIGINS,
    MAX_CONTENT_LENGTH,
)
from backend.model_manager import model_manager
from backend.classification_service import ClassificationService
from backend.evaluation_service import evaluation_service
from backend.storage_manager import storage_manager
from backend.exceptions import (
    ApplicationError,
    ValidationError,
    AuthenticationError,
    ModelNotFoundError,
    ModelDownloadError,
    ClassificationError,
    EvaluationError,
)
from backend.validators import (
    validate_api_key,
    validate_model_name,
    validate_folder_path,
    validate_classes,
    validate_file_upload,
    validate_result_ids,
    validate_json_data,
)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = SECRET_KEY

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS if CORS_ORIGINS != ["*"] else "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Store for async classification tasks
classification_tasks: Dict[str, Dict[str, Any]] = {}


# Error handlers
@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors."""
    return jsonify({
        'error': 'Bad Request',
        'message': str(error)
    }), 400


@app.errorhandler(404)
def not_found(error):
    """Handle not found errors."""
    return jsonify({
        'error': 'Not Found',
        'message': str(error)
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


@app.errorhandler(ApplicationError)
def handle_application_error(error):
    """Handle custom application errors."""
    app.logger.error(f"Application error: {str(error)}")
    
    return jsonify({
        'error': error.__class__.__name__,
        'message': error.message
    }), error.status_code


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions."""
    app.logger.error(f"Unhandled exception: {str(error)}")
    app.logger.error(traceback.format_exc())
    
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error) if DEBUG else 'An unexpected error occurred'
    }), 500


# API Endpoints

@app.route('/api/download-model', methods=['POST'])
def download_model():
    """
    Download a model from Hugging Face Hub.
    """
    try:
        data = request.get_json()
        validate_json_data(data, ['api_key', 'model_name'])
        
        api_key = validate_api_key(data.get('api_key'))
        model_name = validate_model_name(data.get('model_name'))
        force_download = data.get('force_download', False)
        
        model_id = model_manager.download_model(
            api_key=api_key,
            model_name=model_name,
            force_download=force_download
        )
        
        return jsonify({
            'model_id': model_id,
            'message': 'Model downloaded successfully'
        }), 200
        
    except (ValidationError, AuthenticationError, ModelNotFoundError, ModelDownloadError):
        raise
    except Exception as e:
        app.logger.error(f"Error downloading model: {str(e)}")
        app.logger.error(traceback.format_exc())
        raise


@app.route('/api/models', methods=['GET'])
def list_models():
    """
    List all downloaded models.
    """
    try:
        models = model_manager.list_models()
        
        return jsonify({
            'models': models
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error listing models: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/classify', methods=['POST'])
def classify_images():
    """
    Start async classification of images in a folder.
    """
    try:
        data = request.get_json()
        validate_json_data(data, ['model_id', 'folder_path', 'classes'])
        
        model_id = data.get('model_id')
        folder_path_obj = validate_folder_path(data.get('folder_path'))
        classes = validate_classes(data.get('classes'))
        
        prediction_id = storage_manager.generate_uuid()
        
        classification_tasks[prediction_id] = {
            'status': 'processing',
            'progress': {'current': 0, 'total': 0},
            'error': None
        }
        
        def classify_async():
            try:
                service = ClassificationService(model_id, classes)
                
                def update_progress(current, total):
                    classification_tasks[prediction_id]['progress'] = {
                        'current': current,
                        'total': total
                    }
                
                service.set_progress_callback(update_progress)
                service.classify_folder(folder_path_obj, prediction_id)
                classification_tasks[prediction_id]['status'] = 'completed'
                
            except Exception as e:
                app.logger.error(f"Classification error: {str(e)}")
                classification_tasks[prediction_id]['status'] = 'failed'
                classification_tasks[prediction_id]['error'] = str(e)
        
        thread = threading.Thread(target=classify_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'prediction_id': prediction_id,
            'status': 'processing',
            'message': 'Classification started'
        }), 202
        
    except (ValidationError, ModelNotFoundError, ClassificationError):
        raise
    except Exception as e:
        app.logger.error(f"Error starting classification: {str(e)}")
        app.logger.error(traceback.format_exc())
        raise


@app.route('/api/classification-status/<prediction_id>', methods=['GET'])
def get_classification_status(prediction_id: str):
    """
    Get the status of an async classification task.
    """
    try:
        if prediction_id in classification_tasks:
            task = classification_tasks[prediction_id]
            return jsonify({
                'prediction_id': prediction_id,
                'status': task['status'],
                'progress': task['progress'],
                'error': task['error']
            }), 200
        
        # Check if prediction file exists on disk (task completed previously)
        prediction_path = storage_manager.get_prediction_path(prediction_id)
        if prediction_path.exists():
            total_images = 0
            try:
                pred_data = storage_manager.load_json(prediction_path)
                total_images = pred_data.get('total_images', len(pred_data.get('predictions', {})))
            except Exception:
                pass
            return jsonify({
                'prediction_id': prediction_id,
                'status': 'completed',
                'progress': {'current': total_images, 'total': total_images},
                'error': None
            }), 200
        
        return jsonify({'error': 'Prediction not found'}), 404
        
    except Exception as e:
        app.logger.error(f"Error getting classification status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/predictions', methods=['GET'])
def list_predictions():
    """
    List all available prediction files.
    """
    try:
        predictions = storage_manager.list_predictions()
        
        return jsonify({
            'predictions': predictions
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error listing predictions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-ground-truth', methods=['POST'])
def upload_ground_truth():
    """
    Upload ground truth data file.
    """
    try:
        if 'file' not in request.files:
            raise ValidationError('No file provided')
        
        file = request.files['file']
        validate_file_upload(file, ['.json'], max_size_mb=10)
        
        filename = f"ground_truth_{storage_manager.generate_uuid()}.json"
        file_path = storage_manager.get_temp_path(filename)
        
        file.save(str(file_path))
        
        try:
            evaluation_service.load_ground_truth(file_path)
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise ValidationError(f'Invalid ground truth file: {str(e)}')
        
        return jsonify({
            'file_path': str(file_path),
            'message': 'Ground truth uploaded successfully'
        }), 200
        
    except ValidationError:
        raise
    except Exception as e:
        app.logger.error(f"Error uploading ground truth: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate', methods=['POST'])
def evaluate_predictions():
    """
    Evaluate predictions against ground truth.
    """
    try:
        data = request.get_json()
        if data and 'ground_truth_id' in data and 'ground_truth_path' not in data:
            data['ground_truth_path'] = data['ground_truth_id']
        validate_json_data(data, ['prediction_id', 'ground_truth_path'])
        
        prediction_id = data.get('prediction_id')
        ground_truth_path = data.get('ground_truth_path')
        model_name = data.get('model_name')
        
        gt_path = Path(ground_truth_path)
        if not gt_path.exists():
            raise ValidationError(f'Ground truth file not found: {ground_truth_path}')
        
        result = evaluation_service.evaluate(
            prediction_id=prediction_id,
            ground_truth_path=gt_path,
            model_name=model_name
        )
        
        return jsonify(result), 200
        
    except (ValidationError, FileNotFoundError, EvaluationError):
        raise
    except Exception as e:
        app.logger.error(f"Error evaluating predictions: {str(e)}")
        app.logger.error(traceback.format_exc())
        raise


@app.route('/api/evaluate-direct', methods=['POST'])
def evaluate_direct():
    """
    Evaluate predictions directly with provided data (no file IDs needed).
    Automatically saves results with confusion matrix to data/results/model_name/date/
    """
    try:
        data = request.get_json()
        validate_json_data(data, ['predictions', 'ground_truth'])
        
        predictions = data.get('predictions')
        ground_truth = data.get('ground_truth')
        model_name = data.get('model_name', 'Unknown Model')
        save_results = data.get('save_results', True)
        
        result = evaluation_service.evaluate_direct(
            predictions=predictions,
            ground_truth=ground_truth,
            model_name=model_name,
            save_results=save_results
        )
        
        return jsonify(result), 200
        
    except (ValidationError, EvaluationError):
        raise
    except Exception as e:
        app.logger.error(f"Error in direct evaluation: {str(e)}")
        app.logger.error(traceback.format_exc())
        raise


@app.route('/api/results', methods=['GET'])
def list_results():
    """
    List all evaluation results.
    """
    try:
        results = storage_manager.list_results()
        
        return jsonify({
            'results': results
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error listing results: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/result/<path:result_id>', methods=['GET'])
def get_result(result_id: str):
    """
    Get a specific evaluation result.
    """
    try:
        result = storage_manager.get_result(result_id)
        
        if result is None:
            return jsonify({'error': 'Result not found'}), 404
        
        if 'path' in result:
            result['path'] = str(result['path'])
        if 'confusion_matrix_path' in result and result['confusion_matrix_path']:
            result['confusion_matrix_path'] = str(result['confusion_matrix_path'])
        
        return jsonify(result), 200
        
    except Exception as e:
        app.logger.error(f"Error getting result: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def compare_results():
    """
    Compare multiple evaluation results.
    """
    try:
        data = request.get_json()
        validate_json_data(data, ['result_ids'])
        
        result_ids = validate_result_ids(data.get('result_ids'))
        
        comparison = []
        for result_id in result_ids:
            result = storage_manager.get_result(result_id)
            
            if result is None:
                raise ValidationError(f'Result not found: {result_id}')
            
            comparison.append({
                'result_id': result['result_id'],
                'model_name': result['model_name'],
                'date': result['date'],
                'metrics': result.get('metrics')
            })
        
        return jsonify({
            'comparison': comparison
        }), 200
        
    except ValidationError:
        raise
    except Exception as e:
        app.logger.error(f"Error comparing results: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Multimodal Image Classifier API is running'
    }), 200


if __name__ == '__main__':
    from backend.config import create_directories

    create_directories()
    app.run(host=HOST, port=PORT, debug=DEBUG)
