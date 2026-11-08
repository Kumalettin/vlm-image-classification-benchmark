"""
Pytest configuration and shared fixtures for backend tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
import json
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for tests


@pytest.fixture(autouse=True)
def isolated_data_dirs(monkeypatch):
    """Isolate data directories per test so tests never pollute real data/ folder."""
    base_temp = Path(tempfile.mkdtemp())
    data_dir = base_temp / "data"
    models_dir = data_dir / "models"
    predictions_dir = data_dir / "predictions"
    results_dir = data_dir / "results"
    temp_dir = data_dir / "temp"

    for d in (data_dir, models_dir, predictions_dir, results_dir, temp_dir):
        d.mkdir(parents=True, exist_ok=True)

    import backend.config as cfg
    import backend.storage_manager as sm
    import backend.model_manager as mm
    import backend.evaluation_service as es

    monkeypatch.setattr(cfg, "DATA_DIR", data_dir)
    monkeypatch.setattr(cfg, "MODELS_DIR", models_dir)
    monkeypatch.setattr(cfg, "PREDICTIONS_DIR", predictions_dir)
    monkeypatch.setattr(cfg, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(cfg, "TEMP_DIR", temp_dir)

    monkeypatch.setattr(sm, "DATA_DIR", data_dir)
    monkeypatch.setattr(sm, "MODELS_DIR", models_dir)
    monkeypatch.setattr(sm, "PREDICTIONS_DIR", predictions_dir)
    monkeypatch.setattr(sm, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(sm, "TEMP_DIR", temp_dir)

    monkeypatch.setattr(mm, "MODELS_DIR", models_dir)
    monkeypatch.setattr(es, "RESULTS_DIR", results_dir)

    # Update global instances as well
    sm.storage_manager.data_dir = data_dir
    sm.storage_manager.models_dir = models_dir
    sm.storage_manager.predictions_dir = predictions_dir
    sm.storage_manager.results_dir = results_dir
    sm.storage_manager.temp_dir = temp_dir
    mm.model_manager.models_dir = models_dir

    yield data_dir

    shutil.rmtree(base_temp, ignore_errors=True)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup after test
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample RGB image for testing."""
    image_path = temp_dir / "test_image.jpg"
    
    # Create a simple 100x100 RGB image
    img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, 'RGB')
    img.save(image_path)
    img.close()
    
    return image_path


@pytest.fixture
def sample_images(temp_dir):
    """Create multiple sample images for testing."""
    images = []
    for i in range(5):
        image_path = temp_dir / f"image_{i}.jpg"
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, 'RGB')
        img.save(image_path)
        img.close()
        images.append(image_path)
    
    return images


@pytest.fixture
def sample_ground_truth(temp_dir):
    """Create a sample ground truth JSON file."""
    ground_truth = {
        "image_0.jpg": "cat",
        "image_1.jpg": "dog",
        "image_2.jpg": "cat",
        "image_3.jpg": "dog",
        "image_4.jpg": "cat"
    }
    
    gt_path = temp_dir / "ground_truth.json"
    with open(gt_path, 'w') as f:
        json.dump(ground_truth, f)
    
    return gt_path


@pytest.fixture
def sample_predictions():
    """Create sample prediction data."""
    return {
        "image_0.jpg": "cat",
        "image_1.jpg": "dog",
        "image_2.jpg": "dog",  # Wrong prediction
        "image_3.jpg": "dog",
        "image_4.jpg": "cat"
    }


@pytest.fixture
def sample_classes():
    """Return sample class names."""
    return ["cat", "dog", "bird"]


@pytest.fixture
def mock_model_metadata(isolated_data_dirs):
    """Create mock model metadata."""
    return {
        'id': 'test-model-id-123',
        'name': 'test/model-name',
        'download_date': '2025-11-13T10:30:00',
        'path': str(isolated_data_dirs / 'models' / 'test-model-id-123'),
        'model_type': 'vision2seq'
    }


@pytest.fixture
def mock_prediction_data():
    """Create mock prediction data."""
    return {
        'prediction_id': 'test-prediction-123',
        'model_id': 'test-model-id-123',
        'model_name': 'test/model-name',
        'timestamp': '2025-11-13T10:35:00',
        'classes': ['cat', 'dog', 'bird'],
        'predictions': {
            'image_0.jpg': 'cat',
            'image_1.jpg': 'dog',
            'image_2.jpg': 'bird'
        },
        'total_images': 3,
        'errors': {}
    }
