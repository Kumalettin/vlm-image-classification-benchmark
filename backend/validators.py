"""
Input validation utilities for the Multimodal Image Classifier application.
"""
import os
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from backend.exceptions import ValidationError


def validate_api_key(api_key: Optional[str]) -> str:
    """
    Validate Hugging Face API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        Validated API key (stripped)
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError("API key is required")
    
    api_key = api_key.strip()
    
    if len(api_key) < 10:
        raise ValidationError("API key is too short")
    
    # Hugging Face API keys start with 'hf_'
    if not api_key.startswith('hf_'):
        raise ValidationError("Invalid API key format. Hugging Face API keys must start with 'hf_'")
    
    return api_key


def validate_model_name(model_name: Optional[str]) -> str:
    """
    Validate Hugging Face model name format.
    
    Args:
        model_name: Model name to validate
        
    Returns:
        Validated model name (stripped)
        
    Raises:
        ValidationError: If model name is invalid
    """
    if not model_name:
        raise ValidationError("Model name is required")
    
    model_name = model_name.strip()
    
    if len(model_name) < 3:
        raise ValidationError("Model name is too short")
    
    # Model names should follow 'organization/model-name' pattern
    if '/' not in model_name:
        raise ValidationError(
            "Model name should follow the format: organization/model-name"
        )
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z0-9_\-./]+$', model_name):
        raise ValidationError(
            "Model name contains invalid characters. "
            "Only alphanumeric, hyphens, underscores, dots, and slashes are allowed."
        )
    
    return model_name


def validate_folder_path(folder_path: Optional[str]) -> Path:
    """
    Validate folder path.
    
    Args:
        folder_path: Folder path to validate
        
    Returns:
        Path object
        
    Raises:
        ValidationError: If folder path is invalid
    """
    if not folder_path:
        raise ValidationError("Folder path is required")
    
    folder_path = folder_path.strip()
    
    try:
        path = Path(folder_path)
    except Exception as e:
        raise ValidationError(f"Invalid folder path: {str(e)}")
    
    if not path.exists():
        raise ValidationError(f"Folder does not exist: {folder_path}")
    
    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {folder_path}")
    
    # Check if folder is readable
    if not os.access(path, os.R_OK):
        raise ValidationError(f"Folder is not accessible: {folder_path}")
    
    return path


def validate_classes(classes: Optional[List[str]]) -> List[str]:
    """
    Validate class names list.
    
    Args:
        classes: List of class names to validate
        
    Returns:
        Validated list of class names
        
    Raises:
        ValidationError: If classes list is invalid
    """
    if not classes:
        raise ValidationError("Classes list is required")
    
    if not isinstance(classes, list):
        raise ValidationError("Classes must be a list")
    
    if len(classes) < 2:
        raise ValidationError("At least 2 classes are required")
    
    if len(classes) > 50:
        raise ValidationError("Maximum 50 classes allowed")
    
    # Validate each class name
    validated_classes = []
    seen_classes = set()
    
    for i, class_name in enumerate(classes):
        if not isinstance(class_name, str):
            raise ValidationError(f"Class {i+1} must be a string")
        
        class_name = class_name.strip()
        
        if not class_name:
            raise ValidationError(f"Class {i+1} cannot be empty")
        
        if len(class_name) > 100:
            raise ValidationError(f"Class {i+1} name is too long (max 100 characters)")
        
        # Check for duplicates (case-insensitive)
        class_lower = class_name.lower()
        if class_lower in seen_classes:
            raise ValidationError(f"Duplicate class name: {class_name}")
        
        seen_classes.add(class_lower)
        validated_classes.append(class_name)
    
    return validated_classes


def validate_file_upload(file, allowed_extensions: List[str], max_size_mb: int = 10) -> None:
    """
    Validate uploaded file.
    
    Args:
        file: File object from request
        allowed_extensions: List of allowed file extensions (e.g., ['.json', '.txt'])
        max_size_mb: Maximum file size in megabytes
        
    Raises:
        ValidationError: If file is invalid
    """
    if not file:
        raise ValidationError("No file provided")
    
    if not file.filename:
        raise ValidationError("No file selected")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise ValidationError(
            f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check file size (if available)
    if hasattr(file, 'content_length') and file.content_length:
        max_size_bytes = max_size_mb * 1024 * 1024
        if file.content_length > max_size_bytes:
            raise ValidationError(
                f"File too large. Maximum size: {max_size_mb}MB"
            )


def validate_prediction_id(prediction_id: Optional[str]) -> str:
    """
    Validate prediction ID format.
    
    Args:
        prediction_id: Prediction ID to validate
        
    Returns:
        Validated prediction ID
        
    Raises:
        ValidationError: If prediction ID is invalid
    """
    if not prediction_id:
        raise ValidationError("Prediction ID is required")
    
    prediction_id = prediction_id.strip()
    
    if not re.match(r'^[a-zA-Z0-9_\-]{3,128}$', prediction_id):
        raise ValidationError("Invalid prediction ID format")
    
    return prediction_id


def validate_result_ids(result_ids: Optional[List[str]]) -> List[str]:
    """
    Validate list of result IDs for comparison.
    
    Args:
        result_ids: List of result IDs to validate
        
    Returns:
        Validated list of result IDs
        
    Raises:
        ValidationError: If result IDs list is invalid
    """
    if not result_ids:
        raise ValidationError("Result IDs list is required")
    
    if not isinstance(result_ids, list):
        raise ValidationError("Result IDs must be a list")
    
    if len(result_ids) < 2:
        raise ValidationError("At least 2 result IDs are required for comparison")
    
    if len(result_ids) > 10:
        raise ValidationError("Maximum 10 results can be compared at once")
    
    # Validate each result ID
    validated_ids = []
    for result_id in result_ids:
        if not isinstance(result_id, str):
            raise ValidationError("Result ID must be a string")
        
        result_id = result_id.strip()
        
        if not result_id:
            raise ValidationError("Result ID cannot be empty")
        
        validated_ids.append(result_id)
    
    return validated_ids


def validate_json_data(data: Any, required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate JSON request data.
    
    Args:
        data: JSON data to validate
        required_fields: List of required field names
        
    Returns:
        Validated data dictionary
        
    Raises:
        ValidationError: If data is invalid
    """
    if not data:
        raise ValidationError("Request body is required")
    
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    
    # Check required fields
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}"
        )
    
    return data
