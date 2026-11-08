"""
Unit tests for EvaluationService.
"""
import pytest
import json
import numpy as np
from pathlib import Path

from backend.evaluation_service import EvaluationService
from backend.exceptions import EvaluationError


class TestEvaluationService:
    """Test cases for EvaluationService class."""
    
    def test_initialization(self):
        """Test EvaluationService initialization."""
        service = EvaluationService()
        
        assert service.storage_manager is not None
    
    def test_load_ground_truth_success(self, sample_ground_truth):
        """Test loading valid ground truth file."""
        service = EvaluationService()
        
        ground_truth = service.load_ground_truth(sample_ground_truth)
        
        assert isinstance(ground_truth, dict)
        assert len(ground_truth) > 0
        assert "image_0.jpg" in ground_truth
    
    def test_load_ground_truth_file_not_found(self, temp_dir):
        """Test loading non-existent ground truth file."""
        service = EvaluationService()
        
        non_existent = temp_dir / "non_existent.json"
        
        with pytest.raises(FileNotFoundError):
            service.load_ground_truth(non_existent)
    
    def test_load_ground_truth_invalid_json(self, temp_dir):
        """Test loading invalid JSON ground truth file."""
        service = EvaluationService()
        
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("not valid json {")
        
        with pytest.raises(json.JSONDecodeError):
            service.load_ground_truth(invalid_file)
    
    def test_load_ground_truth_invalid_format(self, temp_dir):
        """Test loading ground truth with invalid format."""
        service = EvaluationService()
        
        # Create file with list instead of dict
        invalid_file = temp_dir / "invalid_format.json"
        with open(invalid_file, 'w') as f:
            json.dump(["not", "a", "dict"], f)
        
        with pytest.raises(ValueError):
            service.load_ground_truth(invalid_file)
    
    def test_load_ground_truth_empty(self, temp_dir):
        """Test loading empty ground truth file."""
        service = EvaluationService()
        
        empty_file = temp_dir / "empty.json"
        with open(empty_file, 'w') as f:
            json.dump({}, f)
        
        with pytest.raises(ValueError):
            service.load_ground_truth(empty_file)
    
    def test_match_and_validate_data_success(self, sample_ground_truth, sample_predictions):
        """Test matching ground truth with predictions."""
        service = EvaluationService()
        
        ground_truth = service.load_ground_truth(sample_ground_truth)
        
        y_true, y_pred, image_names = service.match_and_validate_data(
            ground_truth,
            sample_predictions
        )
        
        assert len(y_true) == len(y_pred) == len(image_names)
        assert len(y_true) == 5  # All 5 images match
        assert isinstance(y_true, list)
        assert isinstance(y_pred, list)
    
    def test_match_and_validate_data_no_match(self):
        """Test matching with no common images."""
        service = EvaluationService()
        
        ground_truth = {"image_a.jpg": "cat"}
        predictions = {"image_b.jpg": "dog"}
        
        with pytest.raises(ValueError, match="No matching images"):
            service.match_and_validate_data(ground_truth, predictions)
    
    def test_match_and_validate_data_empty_ground_truth(self):
        """Test matching with empty ground truth."""
        service = EvaluationService()
        
        with pytest.raises(ValueError, match="Ground truth is empty"):
            service.match_and_validate_data({}, {"image.jpg": "cat"})
    
    def test_match_and_validate_data_empty_predictions(self):
        """Test matching with empty predictions."""
        service = EvaluationService()
        
        with pytest.raises(ValueError, match="Predictions are empty"):
            service.match_and_validate_data({"image.jpg": "cat"}, {})
    
    def test_calculate_metrics_perfect_accuracy(self):
        """Test metrics calculation with perfect predictions."""
        service = EvaluationService()
        
        y_true = ["cat", "dog", "cat", "dog"]
        y_pred = ["cat", "dog", "cat", "dog"]
        classes = ["cat", "dog"]
        
        metrics = service.calculate_metrics(y_true, y_pred, classes)
        
        assert metrics['accuracy'] == 1.0
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1_score'] == 1.0
        assert metrics['total_samples'] == 4
        assert 'per_class_metrics' in metrics
    
    def test_calculate_metrics_partial_accuracy(self):
        """Test metrics calculation with some errors."""
        service = EvaluationService()
        
        y_true = ["cat", "dog", "cat", "dog", "cat"]
        y_pred = ["cat", "dog", "dog", "dog", "cat"]  # One error
        classes = ["cat", "dog"]
        
        metrics = service.calculate_metrics(y_true, y_pred, classes)
        
        assert 0.0 < metrics['accuracy'] < 1.0
        assert 0.0 <= metrics['precision'] <= 1.0
        assert 0.0 <= metrics['recall'] <= 1.0
        assert 0.0 <= metrics['f1_score'] <= 1.0
        assert metrics['total_samples'] == 5
    
    def test_calculate_metrics_empty_data(self):
        """Test metrics calculation with empty data."""
        service = EvaluationService()
        
        with pytest.raises(ValueError):
            service.calculate_metrics([], [], [])
    
    def test_calculate_metrics_length_mismatch(self):
        """Test metrics calculation with mismatched lengths."""
        service = EvaluationService()
        
        y_true = ["cat", "dog"]
        y_pred = ["cat"]
        
        with pytest.raises(ValueError, match="Length mismatch"):
            service.calculate_metrics(y_true, y_pred)
    
    def test_generate_confusion_matrix(self):
        """Test confusion matrix generation."""
        service = EvaluationService()
        
        y_true = ["cat", "dog", "cat", "dog"]
        y_pred = ["cat", "dog", "cat", "dog"]
        classes = ["cat", "dog"]
        
        cm = service.generate_confusion_matrix(y_true, y_pred, classes)
        
        assert isinstance(cm, np.ndarray)
        assert cm.shape == (2, 2)
        assert cm.sum() == 4  # Total predictions
    
    def test_visualize_confusion_matrix(self, temp_dir):
        """Test confusion matrix visualization."""
        service = EvaluationService()
        
        cm = np.array([[10, 2], [1, 15]])
        classes = ["cat", "dog"]
        output_path = temp_dir / "cm.png"
        
        service.visualize_confusion_matrix(cm, classes, output_path)
        
        assert output_path.exists()
    
    def test_visualize_confusion_matrix_normalized(self, temp_dir):
        """Test normalized confusion matrix visualization."""
        service = EvaluationService()
        
        cm = np.array([[10, 2], [1, 15]])
        classes = ["cat", "dog"]
        output_path = temp_dir / "cm_normalized.png"
        
        service.visualize_confusion_matrix(
            cm, classes, output_path, normalize=True
        )
        
        assert output_path.exists()
    
    def test_save_results(self):
        """Test saving evaluation results."""
        service = EvaluationService()
        
        model_name = "test_model"
        metrics = {
            'accuracy': 0.95,
            'precision': 0.94,
            'recall': 0.93,
            'f1_score': 0.935
        }
        cm = np.array([[10, 2], [1, 15]])
        classes = ["cat", "dog"]
        
        result_id = service.save_results(model_name, metrics, cm, classes)
        
        assert isinstance(result_id, str)
        assert model_name in result_id
        assert '/' in result_id
    
    def test_load_predictions_success(self, temp_dir, mock_prediction_data):
        """Test loading prediction data."""
        service = EvaluationService()
        
        # Save prediction data
        prediction_id = mock_prediction_data['prediction_id']
        prediction_path = service.storage_manager.get_prediction_path(prediction_id)
        service.storage_manager.save_json(mock_prediction_data, prediction_path)
        
        # Load predictions
        loaded_data = service.load_predictions(prediction_id)
        
        assert loaded_data == mock_prediction_data
    
    def test_load_predictions_not_found(self):
        """Test loading non-existent predictions."""
        service = EvaluationService()
        
        with pytest.raises(FileNotFoundError):
            service.load_predictions("non-existent-id")
    
    def test_evaluate_complete_workflow(self, temp_dir, sample_ground_truth):
        """Test complete evaluation workflow."""
        service = EvaluationService()
        
        # Create prediction data
        prediction_id = "test-prediction-123"
        prediction_data = {
            'prediction_id': prediction_id,
            'model_id': 'test-model',
            'model_name': 'test/model',
            'timestamp': '2025-11-13T10:35:00',
            'classes': ['cat', 'dog'],
            'predictions': {
                'image_0.jpg': 'cat',
                'image_1.jpg': 'dog',
                'image_2.jpg': 'cat',
                'image_3.jpg': 'dog',
                'image_4.jpg': 'cat'
            }
        }
        
        prediction_path = service.storage_manager.get_prediction_path(prediction_id)
        service.storage_manager.save_json(prediction_data, prediction_path)
        
        # Run evaluation
        result = service.evaluate(
            prediction_id=prediction_id,
            ground_truth_path=sample_ground_truth,
            model_name='test_model'
        )
        
        assert 'result_id' in result
        assert 'metrics' in result
        assert 'confusion_matrix' in result
        assert 'classes' in result
        assert result['matched_samples'] == 5
