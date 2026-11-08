"""
Unit tests for ClassificationService.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from backend.classification_service import ClassificationService
from backend.exceptions import (
    ClassificationError,
    ImageLoadError,
    ModelNotFoundError,
    ValidationError
)


class TestClassificationService:
    """Test cases for ClassificationService class."""
    
    def test_initialization_invalid_classes(self):
        """Test initialization with invalid classes."""
        with pytest.raises(ValidationError):
            ClassificationService("model-id", [])
    
    def test_load_image_success(self, sample_image, sample_classes):
        """Test loading a valid image."""
        # Mock the model loading
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            image = service.load_image(sample_image)
            
            assert isinstance(image, Image.Image)
            assert image.mode == 'RGB'
    
    def test_load_image_not_found(self, temp_dir, sample_classes):
        """Test loading non-existent image."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            non_existent = temp_dir / "non_existent.jpg"
            
            with pytest.raises(ImageLoadError):
                service.load_image(non_existent)
    
    def test_load_image_unsupported_format(self, temp_dir, sample_classes):
        """Test loading image with unsupported format."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            # Create a file with unsupported extension
            unsupported_file = temp_dir / "image.xyz"
            unsupported_file.write_text("not an image")
            
            with pytest.raises(ImageLoadError):
                service.load_image(unsupported_file)
    
    def test_load_image_converts_to_rgb(self, temp_dir, sample_classes):
        """Test that images are converted to RGB mode."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            # Create a grayscale image
            gray_image_path = temp_dir / "gray.jpg"
            gray_img = Image.new('L', (100, 100), color=128)
            gray_img.save(gray_image_path)
            
            loaded_image = service.load_image(gray_image_path)
            
            assert loaded_image.mode == 'RGB'
    
    def test_create_prompt(self, sample_classes):
        """Test prompt creation for classification."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            prompt = service.create_prompt(sample_classes)
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            # Check that all classes are mentioned in prompt
            for class_name in sample_classes:
                assert class_name in prompt
    
    def test_set_progress_callback(self, sample_classes):
        """Test setting progress callback."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            callback_called = []
            
            def callback(current, total):
                callback_called.append((current, total))
            
            service.set_progress_callback(callback)
            service._update_progress(5, 10)
            
            assert len(callback_called) == 1
            assert callback_called[0] == (5, 10)
    
    def test_get_progress(self, sample_classes):
        """Test getting classification progress."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            service._update_progress(3, 10)
            progress = service.get_progress()
            
            assert progress['current'] == 3
            assert progress['total'] == 10
    
    def test_save_predictions(self, sample_classes, sample_predictions):
        """Test saving prediction results."""
        with patch.object(ClassificationService, '_load_model'):
            # Mock model manager
            with patch('backend.classification_service.ModelManager') as MockModelManager:
                mock_manager = Mock()
                mock_manager.get_model_info.return_value = {
                    'name': 'test/model',
                    'id': 'test-model-id'
                }
                MockModelManager.return_value = mock_manager
                
                service = ClassificationService("model-id", sample_classes)
                service.model_manager = mock_manager
                
                prediction_id = "test-prediction-123"
                
                service.save_predictions(sample_predictions, prediction_id)
                
                # Verify file was created
                prediction_path = service.storage.get_prediction_path(prediction_id)
                assert prediction_path.exists()
                
                # Verify content
                loaded_data = service.storage.load_json(prediction_path)
                assert loaded_data['prediction_id'] == prediction_id
                assert loaded_data['predictions'] == sample_predictions
    
    def test_load_predictions(self, sample_classes, sample_predictions):
        """Test loading prediction results."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            # Create prediction file
            prediction_id = "test-prediction-123"
            prediction_data = {
                'prediction_id': prediction_id,
                'predictions': sample_predictions
            }
            
            prediction_path = service.storage.get_prediction_path(prediction_id)
            service.storage.save_json(prediction_data, prediction_path)
            
            # Load predictions
            loaded_data = service.load_predictions(prediction_id)
            
            assert loaded_data['prediction_id'] == prediction_id
            assert loaded_data['predictions'] == sample_predictions
    
    def test_load_predictions_not_found(self, sample_classes):
        """Test loading non-existent predictions."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            with pytest.raises(FileNotFoundError):
                service.load_predictions("non-existent-id")
    
    def test_classify_folder_no_images(self, temp_dir, sample_classes):
        """Test classifying folder with no images."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            # Create empty folder
            empty_folder = temp_dir / "empty"
            empty_folder.mkdir()
            
            with pytest.raises(ClassificationError, match="No image files found"):
                service.classify_folder(empty_folder)
    
    def test_classify_folder_invalid_path(self, sample_classes):
        """Test classifying non-existent folder."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            with pytest.raises(FileNotFoundError):
                service.classify_folder(Path("/non/existent/path"))
    
    @patch('backend.classification_service.torch')
    def test_classify_image_mock(self, mock_torch, sample_image, sample_classes):
        """Test image classification with mocked model."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            # Mock model and processor
            mock_processor = Mock()
            mock_model = Mock()
            
            # Mock processor output
            mock_processor.return_value = {'pixel_values': Mock()}
            
            # Mock model output
            mock_output = Mock()
            mock_model.generate.return_value = mock_output
            
            # Mock decode to return a class name
            mock_processor.decode.return_value = sample_classes[0]
            
            service.processor = mock_processor
            service.model = mock_model
            
            # Mock CUDA availability
            mock_torch.cuda.is_available.return_value = False
            mock_torch.no_grad.return_value.__enter__ = Mock()
            mock_torch.no_grad.return_value.__exit__ = Mock()
            
            result = service.classify_image(sample_image)
            
            assert result in sample_classes
    
    def test_preprocess_image(self, sample_classes):
        """Test image preprocessing."""
        with patch.object(ClassificationService, '_load_model'):
            service = ClassificationService("model-id", sample_classes)
            
            # Create a simple image
            img = Image.new('RGB', (100, 100), color='red')
            
            # Preprocess should return the image as-is (processor handles it)
            result = service.preprocess_image(img)
            
            assert isinstance(result, Image.Image)
