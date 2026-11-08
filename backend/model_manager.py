"""
Model Manager for handling Hugging Face model downloads and management.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import importlib
import shutil

try:
    from huggingface_hub import HfApi
except ImportError:
    HfApi = None

try:
    from transformers import AutoConfig, AutoProcessor, AutoModelForVision2Seq
except ImportError:
    AutoConfig = None
    AutoProcessor = None
    AutoModelForVision2Seq = None

from backend.config import MODELS_DIR
from backend.storage_manager import StorageManager
from backend.exceptions import (
    AuthenticationError,
    ModelNotFoundError,
    ModelDownloadError,
    ValidationError
)
from backend.validators import validate_api_key, validate_model_name


class ModelManager:
    """Manages Hugging Face model downloads and local model storage."""
    
    def __init__(self):
        """Initialize the model manager."""
        self.models_dir = MODELS_DIR
        self.storage = StorageManager()
        
        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_api_key_with_hf(self, api_key: str) -> bool:
        """
        Validate Hugging Face API key with HF API.
        
        Args:
            api_key: Hugging Face API key to validate
            
        Returns:
            True if API key is valid
            
        Raises:
            AuthenticationError: If API key is invalid or authentication fails
        """
        try:
            if HfApi is None:
                raise ImportError("huggingface_hub not installed")
            
            api = HfApi(token=api_key)
            api.whoami()
            return True
            
        except ImportError:
            raise AuthenticationError(
                "huggingface_hub library not installed. "
                "Please install it with: pip install huggingface_hub"
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "401" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                raise AuthenticationError(f"Invalid API key: {str(e)}")
            else:
                raise AuthenticationError(f"API key validation failed: {str(e)}")
    
    def download_model(
        self,
        api_key: str,
        model_name: str,
        force_download: bool = False
    ) -> str:
        """
        Download a model from Hugging Face Hub.
        
        Args:
            api_key: Hugging Face API key for authentication
            model_name: Name of the model on Hugging Face (e.g., 'openai/clip-vit-base-patch32')
            force_download: If True, re-download even if model exists locally
            
        Returns:
            Model ID (UUID) for the downloaded model
            
        Raises:
            AuthenticationError: If API key is invalid
            ModelNotFoundError: If model doesn't exist on Hugging Face
            ModelDownloadError: If download fails
        """
        api_key = validate_api_key(api_key)
        model_name = validate_model_name(model_name)
        
        self.validate_api_key_with_hf(api_key)
        
        if not force_download:
            existing_models = self.list_models()
            for model in existing_models:
                if model['name'] == model_name:
                    return model['id']
        
        folder_name = model_name.replace('/', '_').replace('\\', '_')
        model_id = self.storage.generate_uuid()
        model_path = self.models_dir / folder_name
        model_path.mkdir(parents=True, exist_ok=True)
        
        try:
            transformers_module = importlib.import_module('transformers')
            
            # Optional config check
            if AutoConfig is not None:
                try:
                    AutoConfig.from_pretrained(
                        model_name,
                        token=api_key,
                        trust_remote_code=True
                    )
                except Exception as cfg_err:
                    err_str = str(cfg_err).lower()
                    if "404" in err_str or "401" in err_str or "403" in err_str:
                        raise
            
            processor = None
            model = None
            model_type = 'unknown'
            has_vision = False
            
            is_vilt = 'vilt' in model_name.lower()
            strategies = []
            
            if is_vilt:
                strategies.append({
                    'processor_class': 'ViltProcessor',
                    'model_class': 'ViltForQuestionAnswering',
                    'type': 'vqa',
                    'has_vision': True
                })
            
            strategies.extend([
                {
                    'processor_class': 'AutoProcessor',
                    'model_class': 'AutoModelForVision2Seq',
                    'type': 'vision2seq',
                    'has_vision': True
                },
                {
                    'processor_class': 'AutoProcessor',
                    'model_class': 'AutoModelForCausalLM',
                    'type': 'causal_lm_vision',
                    'has_vision': True
                },
                {
                    'processor_class': 'AutoProcessor',
                    'model_class': 'AutoModel',
                    'type': 'automodel_processor',
                    'has_vision': True
                },
                {
                    'processor_class': 'AutoTokenizer',
                    'model_class': 'AutoModel',
                    'type': 'automodel_tokenizer',
                    'has_vision': False
                },
                {
                    'processor_class': 'AutoImageProcessor',
                    'model_class': 'AutoModel',
                    'type': 'automodel_image',
                    'has_vision': True
                },
            ])
            
            last_error = None
            
            for strategy in strategies:
                try:
                    ProcessorClass = (
                        globals().get(strategy['processor_class'])
                        or getattr(transformers_module, strategy['processor_class'])
                    )
                    ModelClass = (
                        globals().get(strategy['model_class'])
                        or getattr(transformers_module, strategy['model_class'])
                    )
                    
                    try:
                        processor = ProcessorClass.from_pretrained(
                            model_name,
                            token=api_key,
                            cache_dir=str(model_path),
                            trust_remote_code=True
                        )
                    except Exception:
                        if strategy['processor_class'] == 'AutoTokenizer':
                            raise
                        processor = None
                    
                    model = ModelClass.from_pretrained(
                        model_name,
                        token=api_key,
                        cache_dir=str(model_path),
                        trust_remote_code=True
                    )
                    
                    model_type = strategy['type']
                    has_vision = strategy['has_vision']
                    break
                    
                except Exception as e:
                    last_error = e
                    continue
            
            if model is None:
                raise ModelDownloadError(
                    f"Failed to load model '{model_name}' with any strategy. "
                    f"Last error: {str(last_error)}"
                )
            
            metadata = {
                'id': model_id,
                'name': model_name,
                'download_date': self.storage.format_iso_timestamp(),
                'path': str(model_path),
                'model_type': model_type,
                'has_vision': has_vision,
                'processor_available': processor is not None
            }
            
            self._save_model_metadata(model_id, metadata)
            return model_id
            
        except ImportError:
            raise ModelDownloadError(
                "Required libraries not installed. "
                "Please install: pip install transformers torch"
            )
        except Exception as e:
            error_msg = str(e).lower()
            
            should_cleanup = (
                "404" in error_msg or 
                "not found" in error_msg or
                "401" in error_msg or 
                "403" in error_msg or 
                "unauthorized" in error_msg or
                "connection" in error_msg or
                "network" in error_msg
            )
            
            if should_cleanup and model_path.exists():
                try:
                    shutil.rmtree(model_path)
                except OSError:
                    pass
            
            if "404" in error_msg or "not found" in error_msg:
                raise ModelNotFoundError(
                    f"Model '{model_name}' not found on Hugging Face Hub"
                )
            elif "401" in error_msg or "403" in error_msg or "unauthorized" in error_msg:
                raise AuthenticationError(
                    f"Authentication failed while downloading model: {str(e)}"
                )
            else:
                error_details = str(e)
                if "einops" in error_msg or "timm" in error_msg:
                    raise ModelDownloadError(
                        "Missing required libraries. Please install: pip install einops timm"
                    )
                elif "embed_dim" in error_msg or "attribute" in error_msg:
                    raise ModelDownloadError(
                        f"Model loading failed (compatibility issue). "
                        f"Try: pip install --upgrade transformers torch. "
                        f"Error: {error_details}"
                    )
                else:
                    raise ModelDownloadError(
                        f"Failed to download model '{model_name}': {error_details}"
                    )
    
    def _save_model_metadata(self, model_id: str, metadata: Dict[str, Any]) -> None:
        """
        Save model metadata to a JSON file inside the model folder.
        """
        model_path = Path(metadata['path'])
        metadata_path = model_path / "model_metadata.json"
        self.storage.save_json(metadata, metadata_path)
    
    def _load_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Load model metadata from a JSON file.
        """
        if not self.models_dir.exists():
            return None

        for model_folder in self.models_dir.iterdir():
            if model_folder.is_dir():
                metadata_path = model_folder / "model_metadata.json"
                if metadata_path.exists():
                    try:
                        metadata = self.storage.load_json(metadata_path)
                        if metadata.get('id') == model_id:
                            return metadata
                    except Exception:
                        continue
        
        return None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List all downloaded models.
        """
        models = []
        
        if not self.models_dir.exists():
            return models
        
        for model_folder in self.models_dir.iterdir():
            if model_folder.is_dir():
                metadata_file = model_folder / "model_metadata.json"
                if metadata_file.exists():
                    try:
                        metadata = self.storage.load_json(metadata_file)
                        model_path = Path(metadata.get('path', ''))
                        if model_path.exists():
                            models.append({
                                'id': metadata.get('id'),
                                'name': metadata.get('name'),
                                'download_date': metadata.get('download_date'),
                                'path': metadata.get('path'),
                                'folder_name': model_folder.name
                            })
                    except Exception:
                        continue
        
        models.sort(
            key=lambda x: x.get('download_date', ''),
            reverse=True
        )
        
        return models
    
    def get_model_path(self, model_id: str) -> Path:
        """
        Get the file system path for a model.
        """
        metadata = self._load_model_metadata(model_id)
        
        if metadata is None:
            raise ModelNotFoundError(f"Model with ID '{model_id}' not found")
        
        model_path = Path(metadata['path'])
        
        if not model_path.exists():
            raise ModelNotFoundError(
                f"Model directory not found: {model_path}"
            )
        
        return model_path
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.
        """
        metadata = self._load_model_metadata(model_id)
        
        if metadata is None:
            raise ModelNotFoundError(f"Model with ID '{model_id}' not found")
        
        return metadata
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model from local storage.
        """
        metadata = self._load_model_metadata(model_id)
        
        if metadata is None:
            raise ModelNotFoundError(f"Model with ID '{model_id}' not found")
        
        model_path = Path(metadata['path'])
        
        if model_path.exists():
            try:
                shutil.rmtree(model_path)
            except Exception as e:
                raise IOError(f"Failed to delete model directory: {str(e)}")
        
        return True


# Global instance
model_manager = ModelManager()
