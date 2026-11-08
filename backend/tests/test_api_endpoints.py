"""
Unit tests for Flask API endpoints.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import io

from backend.app import app
from backend.exceptions import (
    ValidationError,
    AuthenticationError,
    ModelNotFoundError,
    ClassificationError
)


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPIEndpoints:
    """Test cases for Flask API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    @patch('backend.app.model_manager.download_model')
    @patch('backend.app.model_manager')
    def test_download_model_success(self, mock_manager, mock_download, client):
        """Test successful model download."""
        mock_download.return_value = 'test-model-id-123'
        
        payload = {
            'api_key': 'hf_' + 'a' * 30,
            'model_name': 'test/model'
        }
        
        response = client.post(
            '/api/download-model',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'model_id' in data
        assert data['model_id'] == 'test-model-id-123'
    
    def test_download_model_missing_fields(self, client):
        """Test model download with missing required fields."""
        payload = {
            'api_key': 'hf_test'
            # Missing model_name
        }
        
        response = client.post(
            '/api/download-model',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_download_model_invalid_json(self, client):
        """Test model download with invalid JSON."""
        response = client.post(
            '/api/download-model',
            data='not valid json',
            content_type='application/json'
        )
        
        assert response.status_code in [400, 500]
    
    @patch('backend.app.model_manager.list_models')
    def test_list_models(self, mock_list, client):
        """Test listing models."""
        mock_list.return_value = [
            {
                'id': 'model-1',
                'name': 'test/model-1',
                'download_date': '2025-11-13T10:30:00'
            },
            {
                'id': 'model-2',
                'name': 'test/model-2',
                'download_date': '2025-11-13T11:00:00'
            }
        ]
        
        response = client.get('/api/models')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'models' in data
        assert len(data['models']) == 2
    
    @patch('backend.app.storage_manager.generate_uuid')
    @patch('backend.app.ClassificationService')
    def test_classify_images_success(self, mock_service_class, mock_uuid, client, temp_dir):
        """Test starting image classification."""
        mock_uuid.return_value = 'test-prediction-123'
        
        # Create a test folder with images
        test_folder = temp_dir / "test_images"
        test_folder.mkdir()
        
        payload = {
            'model_id': 'test-model-id',
            'folder_path': str(test_folder),
            'classes': ['cat', 'dog', 'bird']
        }
        
        response = client.post(
            '/api/classify',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'prediction_id' in data
        assert data['status'] == 'processing'
    
    def test_classify_images_missing_fields(self, client):
        """Test classification with missing required fields."""
        payload = {
            'model_id': 'test-model-id'
            # Missing folder_path and classes
        }
        
        response = client.post(
            '/api/classify',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_get_classification_status_not_found(self, client):
        """Test getting status for non-existent classification."""
        response = client.get('/api/classification-status/non-existent-id')
        
        assert response.status_code == 404
    
    def test_upload_ground_truth_success(self, client, temp_dir):
        """Test uploading ground truth file."""
        # Create a valid ground truth JSON
        ground_truth = {
            'image1.jpg': 'cat',
            'image2.jpg': 'dog'
        }
        
        # Create file-like object
        data = {
            'file': (io.BytesIO(json.dumps(ground_truth).encode()), 'ground_truth.json')
        }
        
        response = client.post(
            '/api/upload-ground-truth',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert 'file_path' in response_data
    
    def test_upload_ground_truth_no_file(self, client):
        """Test uploading ground truth without file."""
        response = client.post(
            '/api/upload-ground-truth',
            data={},
            content_type='multipart/form-data'
        )
        
        assert response.status_code in [400, 500]
    
    @patch('backend.app.evaluation_service.evaluate')
    def test_evaluate_predictions_success(self, mock_evaluate, client, temp_dir):
        """Test evaluating predictions."""
        # Create ground truth file
        gt_file = temp_dir / "ground_truth.json"
        gt_file.write_text(json.dumps({'image1.jpg': 'cat'}))
        
        mock_evaluate.return_value = {
            'result_id': 'test_model/2025-11-13_10-30-00',
            'metrics': {
                'accuracy': 0.95,
                'precision': 0.94,
                'recall': 0.93,
                'f1_score': 0.935
            },
            'confusion_matrix': [[10, 2], [1, 15]],
            'classes': ['cat', 'dog'],
            'matched_samples': 28,
            'total_ground_truth': 30,
            'total_predictions': 28
        }
        
        payload = {
            'prediction_id': 'test-prediction-123',
            'ground_truth_path': str(gt_file),
            'model_name': 'test_model'
        }
        
        response = client.post(
            '/api/evaluate',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'result_id' in data
        assert 'metrics' in data
    
    def test_evaluate_predictions_missing_fields(self, client):
        """Test evaluation with missing required fields."""
        payload = {
            'prediction_id': 'test-prediction-123'
            # Missing ground_truth_path
        }
        
        response = client.post(
            '/api/evaluate',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    @patch('backend.app.storage_manager.list_results')
    def test_list_results(self, mock_list, client):
        """Test listing evaluation results."""
        mock_list.return_value = [
            {
                'result_id': 'model1/2025-11-13_10-30-00',
                'model_name': 'model1',
                'date': '2025-11-13_10-30-00',
                'metrics': {'accuracy': 0.95}
            }
        ]
        
        response = client.get('/api/results')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert len(data['results']) == 1
    
    @patch('backend.app.storage_manager.get_result')
    def test_get_result_success(self, mock_get, client):
        """Test getting a specific result."""
        mock_get.return_value = {
            'result_id': 'model1/2025-11-13_10-30-00',
            'model_name': 'model1',
            'date': '2025-11-13_10-30-00',
            'metrics': {'accuracy': 0.95},
            'confusion_matrix_path': Path('/path/to/cm.png')
        }
        
        response = client.get('/api/result/model1/2025-11-13_10-30-00')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['result_id'] == 'model1/2025-11-13_10-30-00'
    
    @patch('backend.app.storage_manager.get_result')
    def test_get_result_not_found(self, mock_get, client):
        """Test getting non-existent result."""
        mock_get.return_value = None
        
        response = client.get('/api/result/non-existent/2025-01-01_00-00-00')
        
        assert response.status_code == 404
    
    @patch('backend.app.storage_manager.get_result')
    def test_compare_results_success(self, mock_get, client):
        """Test comparing multiple results."""
        mock_get.side_effect = [
            {
                'result_id': 'model1/date1',
                'model_name': 'model1',
                'date': 'date1',
                'metrics': {'accuracy': 0.95}
            },
            {
                'result_id': 'model2/date2',
                'model_name': 'model2',
                'date': 'date2',
                'metrics': {'accuracy': 0.92}
            }
        ]
        
        payload = {
            'result_ids': ['model1/date1', 'model2/date2']
        }
        
        response = client.post(
            '/api/compare',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'comparison' in data
        assert len(data['comparison']) == 2
    
    def test_compare_results_missing_fields(self, client):
        """Test comparison with missing required fields."""
        payload = {}
        
        response = client.post(
            '/api/compare',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_error_handler_404(self, client):
        """Test 404 error handler."""
        response = client.get('/api/non-existent-endpoint')
        
        assert response.status_code == 404
