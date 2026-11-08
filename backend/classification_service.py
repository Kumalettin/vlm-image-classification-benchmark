"""
Classification Service for handling image classification with multimodal models.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from PIL import Image
import torch
from difflib import SequenceMatcher
import re

from backend.config import ALLOWED_IMAGE_EXTENSIONS
from backend.storage_manager import StorageManager
from backend.model_manager import ModelManager
from backend.exceptions import (
    ClassificationError,
    ImageLoadError,
    ModelNotFoundError,
)
from backend.validators import validate_classes, validate_folder_path


class ClassificationService:
    """Handles image classification using multimodal models."""
    
    def __init__(self, model_id: str, classes: List[str]):
        """
        Initialize the classification service.
        
        Args:
            model_id: Unique identifier for the model to use
            classes: List of class names to constrain predictions to
            
        Raises:
            ModelNotFoundError: If model doesn't exist
            ValidationError: If classes list is invalid
        """
        self.classes = validate_classes(classes)
        self.model_id = model_id
        self.storage = StorageManager()
        self.model_manager = ModelManager()
        
        self.model = None
        self.processor = None
        self.device = "cpu"
        self.model_info: Dict[str, Any] = {
            "id": model_id,
            "name": model_id,
            "model_type": "vision2seq",
            "has_vision": True,
            "processor_available": True,
        }
        self._load_model()
        
        # Progress tracking
        self.current_progress = 0
        self.total_images = 0
        self.progress_callback = None
    
    def _load_model(self) -> None:
        """
        Load the model and processor from disk.
        
        Raises:
            ModelNotFoundError: If model doesn't exist
            ClassificationError: If model loading fails
        """
        try:
            import importlib
            
            model_path = self.model_manager.get_model_path(self.model_id)
            model_info = self.model_manager.get_model_info(self.model_id)
            self.model_info = model_info
            model_name = model_info['name']
            model_type = model_info.get('model_type', 'vision2seq')
            has_vision = model_info.get('has_vision', True)
            processor_available = model_info.get('processor_available', True)
            
            if not has_vision:
                raise ClassificationError(
                    f"Model '{model_name}' does not support vision/image processing. "
                    "Please use a multimodal vision-language model."
                )
            
            transformers_module = importlib.import_module('transformers')
            
            type_mapping = {
                'vision2seq': {
                    'processor': 'AutoProcessor',
                    'model': 'AutoModelForVision2Seq'
                },
                'causal_lm_vision': {
                    'processor': 'AutoProcessor',
                    'model': 'AutoModelForCausalLM'
                },
                'vqa': {
                    'processor': 'ViltProcessor',
                    'model': 'ViltForQuestionAnswering'
                },
                'automodel_processor': {
                    'processor': 'AutoProcessor',
                    'model': 'AutoModel'
                },
                'automodel_tokenizer': {
                    'processor': 'AutoTokenizer',
                    'model': 'AutoModel'
                },
                'automodel_image': {
                    'processor': 'AutoImageProcessor',
                    'model': 'AutoModel'
                }
            }
            
            if model_type in type_mapping:
                mapping = type_mapping[model_type]
                try:
                    ProcessorClass = getattr(transformers_module, mapping['processor'])
                    ModelClass = getattr(transformers_module, mapping['model'])
                except AttributeError:
                    ProcessorClass = getattr(transformers_module, 'AutoProcessor')
                    ModelClass = getattr(transformers_module, 'AutoModel')
            else:
                ProcessorClass = getattr(transformers_module, 'AutoProcessor')
                ModelClass = getattr(transformers_module, 'AutoModel')
            
            if processor_available:
                try:
                    self.processor = ProcessorClass.from_pretrained(
                        model_name,
                        cache_dir=str(model_path),
                        trust_remote_code=True
                    )
                except Exception as e:
                    raise ClassificationError(f"Failed to load processor: {str(e)}")
            else:
                self.processor = None
            
            try:
                if torch.cuda.is_available():
                    try:
                        self.model = ModelClass.from_pretrained(
                            model_name,
                            cache_dir=str(model_path),
                            trust_remote_code=True
                        )
                        try:
                            self.model = self.model.half().cuda()
                            self.device = "cuda"
                        except RuntimeError:
                            self.model = self.model.cuda()
                            self.device = "cuda"
                    except RuntimeError as gpu_error:
                        if "out of memory" in str(gpu_error).lower() or "cuda" in str(gpu_error).lower():
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                            self.model = ModelClass.from_pretrained(
                                model_name,
                                cache_dir=str(model_path),
                                trust_remote_code=True
                            )
                            self.device = "cpu"
                        else:
                            raise
                else:
                    self.model = ModelClass.from_pretrained(
                        model_name,
                        cache_dir=str(model_path),
                        trust_remote_code=True
                    )
                    self.device = "cpu"
                    
            except Exception as e:
                raise ClassificationError(f"Failed to load model: {str(e)}")
            
            self.model.eval()
                
        except ImportError:
            raise ClassificationError(
                "Required libraries not installed. "
                "Please install: pip install transformers torch pillow"
            )
        except ModelNotFoundError:
            raise
        except Exception as e:
            raise ClassificationError(f"Failed to load model: {str(e)}")
    
    def set_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set a callback function for progress tracking."""
        self.progress_callback = callback
    
    def _update_progress(self, current: int, total: int) -> None:
        """Update progress and call callback if set."""
        self.current_progress = current
        self.total_images = total
        
        if self.progress_callback:
            self.progress_callback(current, total)
    
    def load_image(self, image_path: Path) -> Image.Image:
        """
        Load and validate an image file, closing the file descriptor immediately.
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise ImageLoadError(f"Image file not found: {image_path}")
        
        if image_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            raise ImageLoadError(
                f"Unsupported image format: {image_path.suffix}. "
                f"Allowed formats: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            )
        
        try:
            with Image.open(image_path) as img:
                return img.convert('RGB')
        except Exception as e:
            raise ImageLoadError(f"Failed to load image {image_path}: {str(e)}")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for model input."""
        return image
    
    def create_prompt(self, classes: List[str]) -> str:
        """
        Create a prompt for the multimodal model that includes the candidate classes.
        """
        classes_str = ", ".join(classes)
        return f"Classify into ({classes_str}). a photo of"
    
    def _classify_with_clip(self, image: Image.Image) -> str:
        """Classify image using CLIP model (zero-shot classification)."""
        text_prompts = [f"a photo of {class_name}" for class_name in self.classes]
        
        inputs = self.processor(
            text=text_prompts,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        if getattr(self, "device", "cpu") == "cuda":
            inputs = {
                k: v.cuda() if isinstance(v, torch.Tensor) else v
                for k, v in inputs.items()
            }
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        
        predicted_idx = probs.argmax().item()
        return self.classes[predicted_idx]
    
    def _classify_with_vilt(self, image: Image.Image) -> str:
        """Classify image using ViLT model (VQA-based classification)."""
        class_scores = {}
        
        # Locate the 'yes' answer token index in ViLT config if available
        yes_idx = None
        model_config = getattr(self.model, "config", None)
        label2id = getattr(model_config, "label2id", None)
        if isinstance(label2id, dict):
            for k, v in label2id.items():
                if str(k).lower() == "yes":
                    yes_idx = v
                    break
        
        for class_name in self.classes:
            question = f"Is this a {class_name}?"
            
            inputs = self.processor(
                images=image,
                text=question,
                return_tensors="pt"
            )
            
            if getattr(self, "device", "cpu") == "cuda":
                inputs = {
                    k: v.cuda() if isinstance(v, torch.Tensor) else v
                    for k, v in inputs.items()
                }
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            logits = outputs.logits
            if yes_idx is not None and hasattr(logits, "shape") and logits.shape[-1] > yes_idx:
                score = logits[0, yes_idx].item()
            else:
                score = logits.max().item()
            class_scores[class_name] = score
        
        return max(class_scores, key=class_scores.get)
    
    def classify_image(self, image_path: Path) -> str:
        """
        Classify a single image.
        """
        try:
            image = self.load_image(image_path)
            image = self.preprocess_image(image)
            
            try:
                model_info = self.model_manager.get_model_info(self.model_id)
            except ModelNotFoundError:
                model_info = getattr(self, "model_info", {"name": self.model_id})
            model_name = model_info.get('name', self.model_id).lower()
            
            if 'clip' in model_name:
                return self._classify_with_clip(image)
            
            if 'vilt' in model_name:
                return self._classify_with_vilt(image)
            
            # For vision2seq / captioning models, use standard caption prefix
            prompt = "a photo of"
            
            inputs = self.processor(
                text=prompt,
                images=image,
                return_tensors="pt"
            )
            
            if getattr(self, "device", "cpu") == "cuda":
                inputs = {
                    k: v.cuda() if isinstance(v, torch.Tensor) else v
                    for k, v in inputs.items()
                }
            
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=20)
            
            first_output = outputs[0] if hasattr(outputs, "__getitem__") else outputs
            description = self.processor.decode(first_output, skip_special_tokens=True)
            description = description.strip().lower()
            description = description.replace("a photo of", "").replace("an image of", "")
            description = description.replace("this is", "").replace("this image shows", "")
            description = description.strip()
            
            description_clean = re.sub(r'[^\w\s]', '', description)
            description_words = description_clean.split()
            
            class_scores = {}
            
            for class_name in self.classes:
                class_lower = class_name.lower()
                class_words = class_lower.split()
                score = 0.0
                
                if description == class_lower:
                    score += 100.0
                
                if class_lower in description:
                    score += 50.0
                
                for class_word in class_words:
                    if class_word in description_words:
                        score += 30.0
                
                similarity = SequenceMatcher(None, description, class_lower).ratio()
                score += similarity * 20.0
                
                for desc_word in description_words:
                    for class_word in class_words:
                        word_similarity = SequenceMatcher(None, desc_word, class_word).ratio()
                        if word_similarity > 0.8:
                            score += word_similarity * 15.0
                
                for desc_word in description_words:
                    for class_word in class_words:
                        if class_word in desc_word or desc_word in class_word:
                            if len(class_word) > 3:
                                score += 25.0
                
                class_scores[class_name] = score
            
            best_class = max(class_scores, key=class_scores.get)
            return best_class
            
        except ImageLoadError:
            raise
        except Exception as e:
            raise ClassificationError(
                f"Failed to classify image {image_path}: {str(e)}"
            )
    
    def classify_folder(
        self,
        folder_path: Path,
        prediction_id: Optional[str] = None
    ) -> str:
        """
        Classify all images in a folder.
        """
        raw_path = Path(folder_path)
        if not raw_path.exists():
            raise FileNotFoundError(f"Folder does not exist: {folder_path}")
        
        folder_path = validate_folder_path(str(folder_path))
        
        if prediction_id is None:
            prediction_id = self.storage.generate_uuid()
        
        image_files_set = set()
        for ext in ALLOWED_IMAGE_EXTENSIONS:
            image_files_set.update(folder_path.glob(f"*{ext}"))
            image_files_set.update(folder_path.glob(f"*{ext.upper()}"))
        
        image_files = sorted(image_files_set)
        
        if len(image_files) == 0:
            raise ClassificationError(
                f"No image files found in folder: {folder_path}"
            )
        
        self._update_progress(0, len(image_files))
        
        predictions = {}
        errors = {}
        
        for idx, image_path in enumerate(image_files):
            try:
                prediction = self.classify_image(image_path)
                predictions[image_path.name] = prediction
            except (ImageLoadError, ClassificationError) as e:
                errors[image_path.name] = str(e)
            
            self._update_progress(idx + 1, len(image_files))
        
        self.save_predictions(predictions, prediction_id, errors)
        return prediction_id
    
    def save_predictions(
        self,
        predictions: Dict[str, str],
        prediction_id: str,
        errors: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Save prediction results to a JSON file.
        Format: model_name_YYYY-MM-DD_HH-MM-SS.json
        """
        try:
            model_info = self.model_manager.get_model_info(self.model_id)
            model_name = model_info['name']
        except ModelNotFoundError:
            model_name = getattr(self, "model_info", {}).get("name", self.model_id)
        
        clean_model_name = model_name.replace('/', '-')
        timestamp = self.storage.format_timestamp()
        filename = f"{clean_model_name}_{timestamp}.json"
        
        prediction_data = {
            'prediction_id': prediction_id,
            'model_id': self.model_id,
            'model_name': model_name,
            'timestamp': self.storage.format_iso_timestamp(),
            'classes': self.classes,
            'predictions': predictions,
            'total_images': len(predictions),
            'errors': errors or {}
        }
        
        prediction_path = self.storage.predictions_dir / filename
        self.storage.save_json(prediction_data, prediction_path)
    
    def load_predictions(self, prediction_id: str) -> Dict[str, Any]:
        """Load prediction results from a JSON file."""
        prediction_path = self.storage.get_prediction_path(prediction_id)
        
        if not prediction_path.exists():
            raise FileNotFoundError(
                f"Prediction file not found: {prediction_id}"
            )
        
        return self.storage.load_json(prediction_path)
    
    def get_progress(self) -> Dict[str, int]:
        """Get current classification progress."""
        return {
            'current': self.current_progress,
            'total': self.total_images
        }
