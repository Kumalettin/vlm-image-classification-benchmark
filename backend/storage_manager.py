"""
Storage Manager for handling file system operations and data persistence.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from backend.config import (
    DATA_DIR,
    MODELS_DIR,
    PREDICTIONS_DIR,
    RESULTS_DIR,
    TEMP_DIR
)


class StorageManager:
    """Manages file system operations and data persistence."""
    
    def __init__(self):
        """Initialize the storage manager and create necessary directories."""
        self.data_dir = DATA_DIR
        self.models_dir = MODELS_DIR
        self.predictions_dir = PREDICTIONS_DIR
        self.results_dir = RESULTS_DIR
        self.temp_dir = TEMP_DIR
        
        self.create_directories()
    
    def create_directories(self) -> None:
        """
        Create all necessary directories for the application.
        Creates: data/, models/, predictions/, results/, temp/
        """
        directories = [
            self.data_dir,
            self.models_dir,
            self.predictions_dir,
            self.results_dir,
            self.temp_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_json(self, data: Dict[str, Any], file_path: Path) -> None:
        """Save data to a JSON file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, TypeError) as e:
            raise IOError(f"Failed to save JSON to {file_path}: {str(e)}")
    
    def load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load data from a JSON file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in file {file_path}: {str(e)}",
                e.doc,
                e.pos
            )
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a unique identifier."""
        return str(uuid.uuid4())
    
    @staticmethod
    def format_timestamp(dt: Optional[datetime] = None) -> str:
        """Format a datetime object to 'YYYY-MM-DD_HH-MM-SS'."""
        if dt is None:
            dt = datetime.now()
        return dt.strftime("%Y-%m-%d_%H-%M-%S")
    
    @staticmethod
    def format_iso_timestamp(dt: Optional[datetime] = None) -> str:
        """Format a datetime object to ISO 8601 'YYYY-MM-DDTHH:MM:SS'."""
        if dt is None:
            dt = datetime.now()
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    def list_results(self) -> List[Dict[str, Any]]:
        """
        List all evaluation results stored in the results directory.
        Results are organized as: results/{model_name}/{date}/
        """
        results = []
        
        if not self.results_dir.exists():
            return results
        
        for model_dir in self.results_dir.iterdir():
            if not model_dir.is_dir():
                continue
            
            clean_model_name = model_dir.name
            
            for date_dir in model_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                date = date_dir.name
                result_id = f"{clean_model_name}/{date}"
                
                metrics_file = date_dir / "metrics.json"
                original_model_name = clean_model_name
                metrics_data = None
                
                if metrics_file.exists():
                    try:
                        metrics_data = self.load_json(metrics_file)
                        original_model_name = metrics_data.get('model_name', clean_model_name)
                    except (json.JSONDecodeError, IOError):
                        pass
                
                result_info = {
                    'id': result_id,
                    'result_id': result_id,
                    'model_name': original_model_name,
                    'date': date,
                    'path': date_dir
                }
                
                if metrics_data:
                    result_info['metrics'] = metrics_data
                
                results.append(result_info)
        
        results.sort(key=lambda x: x['date'], reverse=True)
        return results
    
    def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific evaluation result by its ID ('model_name/date')."""
        parts = result_id.split('/')
        if len(parts) != 2:
            return None
        
        clean_model_name, date = parts
        result_dir = self.results_dir / clean_model_name / date
        
        if not result_dir.exists():
            return None
        
        metrics_file = result_dir / "metrics.json"
        original_model_name = clean_model_name
        metrics_data = None
        
        if metrics_file.exists():
            try:
                metrics_data = self.load_json(metrics_file)
                original_model_name = metrics_data.get('model_name', clean_model_name)
            except (json.JSONDecodeError, IOError):
                pass
        
        result_data = {
            'id': result_id,
            'result_id': result_id,
            'model_name': original_model_name,
            'date': date,
            'path': result_dir,
            'metrics': metrics_data
        }
        
        cm_file = result_dir / "confusion_matrix.png"
        if cm_file.exists():
            result_data['confusion_matrix_path'] = cm_file
        else:
            result_data['confusion_matrix_path'] = None
        
        return result_data
    
    def save_result(
        self,
        model_name: str,
        metrics: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> str:
        """Save evaluation results to the results directory."""
        if timestamp is None:
            timestamp = self.format_timestamp()
        
        result_dir = self.results_dir / model_name / timestamp
        result_dir.mkdir(parents=True, exist_ok=True)
        
        metrics_file = result_dir / "metrics.json"
        self.save_json(metrics, metrics_file)
        
        return f"{model_name}/{timestamp}"
    
    def get_prediction_path(self, prediction_id: str) -> Path:
        """
        Get the file path for a prediction file.
        Supports both UUID format and model_name_date format.
        """
        direct_path = self.predictions_dir / f"{prediction_id}.json"
        if direct_path.exists():
            return direct_path
        
        if self.predictions_dir.exists():
            for pred_file in self.predictions_dir.glob("*.json"):
                try:
                    pred_data = self.load_json(pred_file)
                    if pred_data.get('prediction_id') == prediction_id:
                        return pred_file
                except Exception:
                    continue
        
        return direct_path
    
    def list_predictions(self) -> List[Dict[str, Any]]:
        """List all available prediction files."""
        predictions = []
        
        if not self.predictions_dir.exists():
            return predictions
        
        for pred_file in self.predictions_dir.glob("*.json"):
            try:
                pred_data = self.load_json(pred_file)
                predictions.append({
                    'id': pred_data.get('prediction_id'),
                    'model_name': pred_data.get('model_name'),
                    'timestamp': pred_data.get('timestamp'),
                    'total_images': pred_data.get('total_images', len(pred_data.get('predictions', {})))
                })
            except Exception:
                continue
        
        predictions.sort(
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return predictions
    
    def get_temp_path(self, filename: str) -> Path:
        """Get a path in the temporary directory."""
        return self.temp_dir / filename
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours."""
        if not self.temp_dir.exists():
            return 0
        
        current_time = datetime.now()
        deleted_count = 0
        
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                age_hours = (current_time - file_mtime).total_seconds() / 3600
                
                if age_hours >= older_than_hours:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except OSError:
                        pass
        
        return deleted_count


# Global instance
storage_manager = StorageManager()
