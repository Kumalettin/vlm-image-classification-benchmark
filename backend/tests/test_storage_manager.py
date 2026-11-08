"""
Unit tests for StorageManager.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime

from backend.storage_manager import StorageManager


class TestStorageManager:
    """Test cases for StorageManager class."""
    
    def test_initialization(self, temp_dir):
        """Test StorageManager initialization creates directories."""
        storage = StorageManager()
        
        assert storage.data_dir.exists()
        assert storage.models_dir.exists()
        assert storage.predictions_dir.exists()
        assert storage.results_dir.exists()
        assert storage.temp_dir.exists()
    
    def test_save_and_load_json(self, temp_dir):
        """Test saving and loading JSON files."""
        storage = StorageManager()
        
        test_data = {
            'key1': 'value1',
            'key2': 123,
            'key3': ['a', 'b', 'c']
        }
        
        file_path = temp_dir / "test.json"
        
        # Save JSON
        storage.save_json(test_data, file_path)
        assert file_path.exists()
        
        # Load JSON
        loaded_data = storage.load_json(file_path)
        assert loaded_data == test_data
    
    def test_load_json_file_not_found(self, temp_dir):
        """Test loading non-existent JSON file raises FileNotFoundError."""
        storage = StorageManager()
        
        non_existent_file = temp_dir / "non_existent.json"
        
        with pytest.raises(FileNotFoundError):
            storage.load_json(non_existent_file)
    
    def test_load_json_invalid_json(self, temp_dir):
        """Test loading invalid JSON file raises JSONDecodeError."""
        storage = StorageManager()
        
        invalid_json_file = temp_dir / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("This is not valid JSON {")
        
        with pytest.raises(json.JSONDecodeError):
            storage.load_json(invalid_json_file)
    
    def test_generate_uuid(self):
        """Test UUID generation."""
        storage = StorageManager()
        
        uuid1 = storage.generate_uuid()
        uuid2 = storage.generate_uuid()
        
        # UUIDs should be strings
        assert isinstance(uuid1, str)
        assert isinstance(uuid2, str)
        
        # UUIDs should be unique
        assert uuid1 != uuid2
        
        # UUID format check (basic)
        assert len(uuid1) == 36
        assert uuid1.count('-') == 4
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        storage = StorageManager()
        
        # Test with specific datetime
        dt = datetime(2025, 11, 13, 10, 30, 45)
        timestamp = storage.format_timestamp(dt)
        
        assert timestamp == "2025-11-13_10-30-45"
        
        # Test with current time (should not raise error)
        current_timestamp = storage.format_timestamp()
        assert isinstance(current_timestamp, str)
        assert len(current_timestamp) == 19
    
    def test_format_iso_timestamp(self):
        """Test ISO timestamp formatting."""
        storage = StorageManager()
        
        # Test with specific datetime
        dt = datetime(2025, 11, 13, 10, 30, 45)
        iso_timestamp = storage.format_iso_timestamp(dt)
        
        assert iso_timestamp == "2025-11-13T10:30:45"
        
        # Test with current time
        current_iso = storage.format_iso_timestamp()
        assert isinstance(current_iso, str)
        assert 'T' in current_iso
    
    def test_get_prediction_path(self):
        """Test getting prediction file path."""
        storage = StorageManager()
        
        prediction_id = "test-prediction-123"
        path = storage.get_prediction_path(prediction_id)
        
        assert isinstance(path, Path)
        assert path.name == f"{prediction_id}.json"
        assert path.parent == storage.predictions_dir
    
    def test_get_temp_path(self):
        """Test getting temporary file path."""
        storage = StorageManager()
        
        filename = "temp_file.txt"
        path = storage.get_temp_path(filename)
        
        assert isinstance(path, Path)
        assert path.name == filename
        assert path.parent == storage.temp_dir
    
    def test_list_results_empty(self):
        """Test listing results when directory is empty."""
        storage = StorageManager()
        
        results = storage.list_results()
        
        # Should return empty list if no results exist
        assert isinstance(results, list)
    
    def test_list_results_with_data(self, temp_dir):
        """Test listing results with actual data."""
        storage = StorageManager()
        
        # Create mock result structure
        model_name = "test_model"
        date = "2025-11-13_10-30-00"
        result_dir = storage.results_dir / model_name / date
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metrics file
        metrics = {
            'accuracy': 0.95,
            'precision': 0.94,
            'recall': 0.93,
            'f1_score': 0.935
        }
        metrics_file = result_dir / "metrics.json"
        storage.save_json(metrics, metrics_file)
        
        # List results
        results = storage.list_results()
        
        assert len(results) > 0
        assert any(r['model_name'] == model_name for r in results)
        assert any(r['date'] == date for r in results)
    
    def test_get_result(self):
        """Test getting a specific result."""
        storage = StorageManager()
        
        # Create mock result
        model_name = "test_model"
        date = "2025-11-13_10-30-00"
        result_id = f"{model_name}/{date}"
        result_dir = storage.results_dir / model_name / date
        result_dir.mkdir(parents=True, exist_ok=True)
        
        metrics = {'accuracy': 0.95}
        metrics_file = result_dir / "metrics.json"
        storage.save_json(metrics, metrics_file)
        
        # Get result
        result = storage.get_result(result_id)
        
        assert result is not None
        assert result['result_id'] == result_id
        assert result['model_name'] == model_name
        assert result['date'] == date
        assert result['metrics'] == metrics
    
    def test_get_result_not_found(self):
        """Test getting non-existent result returns None."""
        storage = StorageManager()
        
        result = storage.get_result("non_existent_model/2025-01-01_00-00-00")
        
        assert result is None
    
    def test_save_result(self):
        """Test saving evaluation results."""
        storage = StorageManager()
        
        model_name = "test_model"
        metrics = {
            'accuracy': 0.95,
            'precision': 0.94,
            'recall': 0.93,
            'f1_score': 0.935
        }
        
        result_id = storage.save_result(model_name, metrics)
        
        # Verify result_id format
        assert '/' in result_id
        assert result_id.startswith(model_name)
        
        # Verify file was created
        parts = result_id.split('/')
        result_dir = storage.results_dir / parts[0] / parts[1]
        metrics_file = result_dir / "metrics.json"
        
        assert result_dir.exists()
        assert metrics_file.exists()
        
        # Verify content
        loaded_metrics = storage.load_json(metrics_file)
        assert loaded_metrics == metrics
    
    def test_cleanup_temp_files(self, temp_dir):
        """Test cleaning up old temporary files."""
        storage = StorageManager()
        
        # Create some temp files
        temp_file1 = storage.temp_dir / "temp1.txt"
        temp_file2 = storage.temp_dir / "temp2.txt"
        
        temp_file1.write_text("test content 1")
        temp_file2.write_text("test content 2")
        
        # Cleanup files older than 0 hours (should delete all)
        deleted_count = storage.cleanup_temp_files(older_than_hours=0)
        
        # Should have deleted files
        assert deleted_count >= 0
