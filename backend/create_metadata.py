"""
Utility script to create metadata for manually added models.
Run this script if you manually copy models to the data/models folder.

Usage:
    python backend/create_metadata.py
"""
import json
from pathlib import Path
from datetime import datetime
import uuid

# Base directories
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "data" / "models"

def create_metadata_for_model(model_folder: Path):
    """Create metadata file for a model folder."""
    
    # Check if metadata already exists
    metadata_path = model_folder / "model_metadata.json"
    if metadata_path.exists():
        print(f"✓ Metadata already exists for: {model_folder.name}")
        return
    
    # Extract model name from folder name (replace _ with /)
    folder_name = model_folder.name
    model_name = folder_name.replace('_', '/', 1)  # Only replace first underscore
    
    # Generate metadata
    metadata = {
        "id": str(uuid.uuid4()),
        "name": model_name,
        "download_date": datetime.now().isoformat(),
        "path": str(model_folder.absolute()),
        "model_type": "vision2seq",
        "has_vision": True,
        "processor_available": True
    }
    
    # Save metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created metadata for: {model_name}")
    print(f"  ID: {metadata['id']}")
    print(f"  Path: {metadata_path}")

def main():
    """Scan models directory and create metadata for models without it."""
    
    if not MODELS_DIR.exists():
        print(f"❌ Models directory not found: {MODELS_DIR}")
        return
    
    print("Scanning for models without metadata...\n")
    
    found_models = 0
    created_metadata = 0
    
    for model_folder in MODELS_DIR.iterdir():
        if model_folder.is_dir() and not model_folder.name.startswith('.'):
            found_models += 1
            
            metadata_path = model_folder / "model_metadata.json"
            if not metadata_path.exists():
                create_metadata_for_model(model_folder)
                created_metadata += 1
            else:
                print(f"✓ Metadata exists for: {model_folder.name}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total models found: {found_models}")
    print(f"  Metadata created: {created_metadata}")
    print(f"  Already had metadata: {found_models - created_metadata}")
    print(f"{'='*60}")
    
    if created_metadata > 0:
        print("\n✓ Done! Restart the backend server to see the new models.")
    else:
        print("\n✓ All models already have metadata.")

if __name__ == "__main__":
    main()
