"""
Evaluation Service for calculating model performance metrics.
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from backend.storage_manager import StorageManager
from backend.config import RESULTS_DIR
from backend.exceptions import EvaluationError, ValidationError


class EvaluationService:
    """Service for evaluating model predictions against ground truth."""
    
    def __init__(self):
        """Initialize the evaluation service."""
        self.storage_manager = StorageManager()
    
    def load_ground_truth(self, file_path: Path) -> Dict[str, str]:
        """
        Load ground truth data from a JSON file.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ground_truth = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in ground truth file: {str(e)}",
                e.doc,
                e.pos
            )
        
        if not isinstance(ground_truth, dict):
            raise ValueError("Ground truth must be a dictionary")
        
        if not ground_truth:
            raise ValueError("Ground truth file is empty")
        
        for key, value in ground_truth.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    "Ground truth must map image filenames (str) to class names (str)"
                )
        
        return ground_truth
    
    def load_predictions(self, prediction_id: str) -> Dict[str, Any]:
        """
        Load prediction data from storage.
        """
        prediction_path = self.storage_manager.get_prediction_path(prediction_id)
        
        if not prediction_path.exists():
            raise FileNotFoundError(
                f"Prediction file not found: {prediction_id}"
            )
        
        return self.storage_manager.load_json(prediction_path)

    def match_and_validate_data(
        self,
        ground_truth: Dict[str, str],
        predictions: Dict[str, str]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Match and validate ground truth with predictions.
        """
        if not ground_truth:
            raise ValueError("Ground truth is empty")
        
        if not predictions:
            raise ValueError("Predictions are empty")
        
        gt_images = set(ground_truth.keys())
        pred_images = set(predictions.keys())
        common_images = gt_images.intersection(pred_images)
        
        if not common_images:
            raise ValueError(
                "No matching images found between ground truth and predictions. "
                f"Ground truth has {len(gt_images)} images, "
                f"predictions have {len(pred_images)} images."
            )
        
        y_true = []
        y_pred = []
        image_names = []
        
        for image_name in sorted(common_images):
            y_true.append(ground_truth[image_name])
            y_pred.append(predictions[image_name])
            image_names.append(image_name)
        
        return y_true, y_pred, image_names
    
    def calculate_metrics(
        self,
        y_true: List[str],
        y_pred: List[str],
        classes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate evaluation metrics.
        """
        if not y_true or not y_pred:
            raise ValueError("Cannot calculate metrics on empty data")
        
        if len(y_true) != len(y_pred):
            raise ValueError(
                f"Length mismatch: y_true has {len(y_true)} samples, "
                f"y_pred has {len(y_pred)} samples"
            )
        
        if classes is None:
            classes = sorted(list(set(y_true) | set(y_pred)))
        
        accuracy = accuracy_score(y_true, y_pred)
        precision_macro = precision_score(
            y_true, y_pred, average='macro', zero_division=0
        )
        recall_macro = recall_score(
            y_true, y_pred, average='macro', zero_division=0
        )
        f1_macro = f1_score(
            y_true, y_pred, average='macro', zero_division=0
        )
        
        precision_per_class = precision_score(
            y_true, y_pred, average=None, labels=classes, zero_division=0
        )
        recall_per_class = recall_score(
            y_true, y_pred, average=None, labels=classes, zero_division=0
        )
        f1_per_class = f1_score(
            y_true, y_pred, average=None, labels=classes, zero_division=0
        )
        
        per_class_metrics = {}
        for i, class_name in enumerate(classes):
            per_class_metrics[class_name] = {
                'precision': float(precision_per_class[i]),
                'recall': float(recall_per_class[i]),
                'f1': float(f1_per_class[i])
            }
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision_macro),
            'recall': float(recall_macro),
            'f1_score': float(f1_macro),
            'per_class_metrics': per_class_metrics,
            'total_samples': len(y_true),
            'classes': classes
        }
    
    def generate_confusion_matrix(
        self,
        y_true: List[str],
        y_pred: List[str],
        classes: List[str]
    ) -> np.ndarray:
        """Generate confusion matrix."""
        return confusion_matrix(y_true, y_pred, labels=classes)
    
    def visualize_confusion_matrix(
        self,
        cm: np.ndarray,
        classes: List[str],
        output_path: Path,
        normalize: bool = False
    ) -> None:
        """Create and save confusion matrix visualization."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if normalize:
            row_sums = cm.sum(axis=1)[:, np.newaxis]
            cm = np.divide(cm.astype('float'), row_sums, out=np.zeros_like(cm, dtype=float), where=row_sums != 0)
            fmt = '.2f'
            title = 'Normalized Confusion Matrix'
        else:
            fmt = 'd'
            title = 'Confusion Matrix'
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt=fmt,
            cmap='Blues',
            xticklabels=classes,
            yticklabels=classes,
            cbar_kws={'label': 'Count' if not normalize else 'Proportion'}
        )
        
        plt.title(title, fontsize=16, pad=20)
        plt.ylabel('True Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(
        self,
        model_name: str,
        metrics: Dict[str, Any],
        confusion_matrix: np.ndarray,
        classes: List[str],
        timestamp: Optional[str] = None
    ) -> str:
        """
        Save evaluation results to storage.
        Returns Result ID in format 'model_name/timestamp'.
        """
        if timestamp is None:
            timestamp = self.storage_manager.format_timestamp()
        
        clean_model_name = model_name.replace('/', '-')
        result_dir = RESULTS_DIR / clean_model_name / timestamp
        result_dir.mkdir(parents=True, exist_ok=True)
        
        metrics_with_cm = metrics.copy()
        metrics_with_cm['confusion_matrix'] = confusion_matrix.tolist()
        metrics_with_cm['model_name'] = model_name
        
        metrics_file = result_dir / "metrics.json"
        self.storage_manager.save_json(metrics_with_cm, metrics_file)
        
        cm_file = result_dir / "confusion_matrix.png"
        self.visualize_confusion_matrix(
            confusion_matrix,
            classes,
            cm_file,
            normalize=False
        )
        
        return f"{clean_model_name}/{timestamp}"
    
    def evaluate(
        self,
        prediction_id: str,
        ground_truth_path: Path,
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete evaluation workflow."""
        ground_truth = self.load_ground_truth(ground_truth_path)
        prediction_data = self.load_predictions(prediction_id)
        predictions = prediction_data.get('predictions', {})
        
        if model_name is None:
            model_name = prediction_data.get('model_name', prediction_data.get('model_id', 'Unknown Model'))
        
        y_true, y_pred, _ = self.match_and_validate_data(
            ground_truth,
            predictions
        )
        
        classes = prediction_data.get('classes')
        if classes is None:
            classes = sorted(list(set(y_true) | set(y_pred)))
        
        metrics = self.calculate_metrics(y_true, y_pred, classes)
        cm = self.generate_confusion_matrix(y_true, y_pred, classes)
        
        timestamp = self.storage_manager.format_timestamp()
        result_id = self.save_results(
            model_name,
            metrics,
            cm,
            classes,
            timestamp=timestamp
        )
        
        clean_model_name = model_name.replace('/', '-')
        cm_image_path = str(RESULTS_DIR / clean_model_name / timestamp / "confusion_matrix.png")
        
        return {
            'result_id': result_id,
            'metrics': metrics,
            'confusion_matrix': cm.tolist(),
            'classes': classes,
            'confusion_matrix_image': cm_image_path,
            'matched_samples': len(y_true),
            'total_ground_truth': len(ground_truth),
            'total_predictions': len(predictions)
        }
    
    def evaluate_direct(
        self,
        predictions: Dict[str, str],
        ground_truth: Dict[str, str],
        model_name: str = "Unknown Model",
        save_results: bool = True
    ) -> Dict[str, Any]:
        """Evaluate predictions directly without file IDs."""
        y_true, y_pred, _ = self.match_and_validate_data(
            ground_truth,
            predictions
        )
        
        classes = sorted(list(set(y_true) | set(y_pred)))
        metrics = self.calculate_metrics(y_true, y_pred, classes)
        cm = self.generate_confusion_matrix(y_true, y_pred, classes)
        
        result_id = None
        cm_image_path = None
        if save_results:
            timestamp = self.storage_manager.format_timestamp()
            result_id = self.save_results(model_name, metrics, cm, classes, timestamp=timestamp)
            clean_model_name = model_name.replace('/', '-')
            cm_image_path = str(RESULTS_DIR / clean_model_name / timestamp / "confusion_matrix.png")
        
        result = {
            'metrics': metrics,
            'confusion_matrix': cm.tolist(),
            'classes': classes,
            'matched_samples': len(y_true),
            'total_ground_truth': len(ground_truth),
            'total_predictions': len(predictions)
        }
        
        if result_id:
            result['result_id'] = result_id
            result['confusion_matrix_image'] = cm_image_path
        
        return result


# Global instance
evaluation_service = EvaluationService()
