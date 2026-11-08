"""
Unit tests for ModelManager.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from backend.model_manager import ModelManager
from backend.exceptions import (
    AuthenticationError,
    ModelNotFoundError,
    ModelDownloadError,
    ValidationError
)


class TestModelManager:
    """Test cases for ModelManager class."""
    
    def test_initialization(self):
        """Test ModelManager initialization."""
        manager = ModelManager()
        
        assert manager.models_dir.exists()
        assert manager.storage is not None
    
    def test_validate_api_key_format(self):
        """Test API key format validation."""
        manager = ModelManager()
        
        # Valid API key format
        valid_key = "hf_" + "a" * 30
        
        # Invalid API keys should raise ValidationError in validators
        from backend.validators import validate_api_key
        
        with pytest.raises(ValidationError):
            validate_api_key("")
        
        with pytest.raises(ValidationError):
            validate_api_key("invalid_key")
    
    @patch('backend.model_manager.HfApi')
    def test_validate_api_key_with_hf_success(self, mock_hf_api):
        """Test successful API key validation with Hugging Face."""
        manager = ModelManager()
        
        # Mock successful authentication
        mock_api_instance = Mock()
        mock_api_instance.whoami.return_value = {'name': 'test_user'}
        mock_hf_api.return_value = mock_api_instance
        
        valid_key = "hf_" + "a" * 30
        
        result = manager.validate_api_key_with_hf(valid_key)
        
        assert result is True
        mock_hf_api.assert_called_once_with(token=valid_key)
        mock_api_instance.whoami.assert_called_once()
    
    @patch('backend.model_manager.HfApi')
    def test_validate_api_key_with_hf_invalid(self, mock_hf_api):
        """Test API key validation with invalid key."""
        manager = ModelManager()
        
        # Mock authentication failure
        mock_api_instance = Mock()
        mock_api_instance.whoami.side_effect = Exception("401 Unauthorized")
        mock_hf_api.return_value = mock_api_instance
        
        invalid_key = "hf_invalid"
        
        with pytest.raises(AuthenticationError):
            manager.validate_api_key_with_hf(invalid_key)
    
    def test_list_models_empty(self):
        """Test listing models when no models exist."""
        manager = ModelManager()
        
        models = manager.list_models()
        
        assert isinstance(models, list)
    
    def test_save_and_load_model_metadata(self, temp_dir, mock_model_metadata):
        """Test saving and loading model metadata."""
        manager = ModelManager()
        
        model_id = mock_model_metadata['id']
        
        # Save metadata
        manager._save_model_metadata(model_id, mock_model_metadata)
        
        # Load metadata
        loaded_metadata = manager._load_model_metadata(model_id)
        
        assert loaded_metadata == mock_model_metadata
    
    def test_load_model_metadata_not_found(self):
        """Test loading non-existent model metadata returns None."""
        manager = ModelManager()
        
        metadata = manager._load_model_metadata("non-existent-id")
        
        assert metadata is None
    
    def test_get_model_path_not_found(self):
        """Test getting path for non-existent model raises error."""
        manager = ModelManager()
        
        with pytest.raises(ModelNotFoundError):
            manager.get_model_path("non-existent-id")
    
    def test_get_model_info_not_found(self):
        """Test getting info for non-existent model raises error."""
        manager = ModelManager()
        
        with pytest.raises(ModelNotFoundError):
            manager.get_model_info("non-existent-id")
    
    def test_list_models_with_data(self, mock_model_metadata):
        """Test listing models with actual data."""
        manager = ModelManager()
        
        # Save a model metadata
        model_id = mock_model_metadata['id']
        model_path = manager.models_dir / model_id
        model_path.mkdir(parents=True, exist_ok=True)
        
        mock_model_metadata['path'] = str(model_path)
        manager._save_model_metadata(model_id, mock_model_metadata)
        
        # List models
        models = manager.list_models()
        
        # Should find at least one model
        assert len(models) > 0
        
        # Check if our model is in the list
        model_ids = [m['id'] for m in models]
        assert model_id in model_ids
    
    @patch('backend.model_manager.AutoProcessor')
    @patch('backend.model_manager.AutoModelForVision2Seq')
    @patch('backend.model_manager.HfApi')
    def test_download_model_success(
        self,
        mock_hf_api,
        mock_model_class,
        mock_processor_class
    ):
        """Test successful model download."""
        manager = ModelManager()
        
        # Mock HF API authentication
        mock_api_instance = Mock()
        mock_api_instance.whoami.return_value = {'name': 'test_user'}
        mock_hf_api.return_value = mock_api_instance
        
        # Mock model and processor
        mock_processor = Mock()
        mock_model = Mock()
        mock_processor_class.from_pretrained.return_value = mock_processor
        mock_model_class.from_pretrained.return_value = mock_model
        
        api_key = "hf_" + "a" * 30
        model_name = "test/model"
        
        model_id = manager.download_model(api_key, model_name)
        
        # Verify model_id is returned
        assert isinstance(model_id, str)
        assert len(model_id) > 0
        
        # Verify API calls
        mock_processor_class.from_pretrained.assert_called_once()
        mock_model_class.from_pretrained.assert_called_once()
    
    @patch('backend.model_manager.HfApi')
    def test_download_model_invalid_api_key(self, mock_hf_api):
        """Test model download with invalid API key."""
        manager = ModelManager()
        
        # Mock authentication failure
        mock_api_instance = Mock()
        mock_api_instance.whoami.side_effect = Exception("401 Unauthorized")
        mock_hf_api.return_value = mock_api_instance
        
        api_key = "hf_invalid"
        model_name = "test/model"
        
        with pytest.raises(AuthenticationError):
            manager.download_model(api_key, model_name)
    
    def test_delete_model_not_found(self):
        """Test deleting non-existent model raises error."""
        manager = ModelManager()
        
        with pytest.raises(ModelNotFoundError):
            manager.delete_model("non-existent-id")
    
    def test_delete_model_success(self, mock_model_metadata):
        """Test successful model deletion."""
        manager = ModelManager()
        
        # Create a model with metadata
        model_id = mock_model_metadata['id']
        model_path = manager.models_dir / model_id
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy file in model directory
        (model_path / "dummy.txt").write_text("test")
        
        mock_model_metadata['path'] = str(model_path)
        manager._save_model_metadata(model_id, mock_model_metadata)
        
        # Delete model
        result = manager.delete_model(model_id)
        
        assert result is True
        assert not model_path.exists()
