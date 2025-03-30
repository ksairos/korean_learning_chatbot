"""
Script to create a Qdrant collection and upload grammar entries.
This script reads JSON grammar entries, converts them to vectors using a sentence
transformer model, and uploads them to a Qdrant collection.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.models import Distance, VectorParams

def load_json_entries(dir_path: str) -> List[Dict[str, Any]]:
    """Load all JSON grammar entries from a directory."""
    entries = []
    path = Path(dir_path)
    
    # If path is a file and it's a combined JSON file
    if path.is_file() and path.name.endswith('.json'):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data]
    
    return entries

def create_qdrant_collection(client: QdrantClient, collection_name: str) -> None:
    """Create a Qdrant collection if it doesn't exist."""
    # List existing collections
    collections = client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if collection_name in collection_names:
        print(f"Collection {collection_name} already exists.")
        return
    
    # Create a new collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )
    print(f"Created collection: {collection_name}")

def prepare_grammar_payload(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare payload data for Qdrant from a grammar entry."""
    return {
        "level": entry.get("level", 1),
        "grammar_name_kr": entry.get("grammar_name_kr", ""),
        "grammar_name_rus": entry.get("grammar_name_rus", ""),
        "description": entry.get("description", ""),
        "usage_form": entry.get("usage_form", ""),
        "examples": entry.get("examples", []),
        "notes": entry.get("notes", []),
        # Add a combined text field for search
        "text": f"{entry.get('grammar_name_kr', '')} {entry.get('grammar_name_rus', '')} {entry.get('description', '')}"
    }

def get_mock_vector(dim: int = 768) -> List[float]:
    """Generate a mock vector for testing without a real model."""
    # In a real application, you would use a sentence transformer
    # But for this example, we'll just use random vectors
    return list(np.random.random(dim))

def main():
    """Main function to create a Qdrant collection and upload grammar entries."""
    # Initialize Qdrant client
    client = QdrantClient(host="localhost", port=6333)
    collection_name = "korean_grammar"
    
    # Create collection
    create_qdrant_collection(client, collection_name)
    
    # Load grammar entries
    data_dir = Path("data/grammar-level-1")
    all_entries_file = data_dir / "all_entries.json"
    
    if all_entries_file.exists():
        entries = load_json_entries(str(all_entries_file))
    else:
        json_dir = data_dir / "json"
        if not json_dir.exists():
            print("Please run parse_md_to_json.py first to generate JSON files.")
            return
        entries = load_json_entries(str(json_dir))
    
    print(f"Loaded {len(entries)} grammar entries")
    
    # Upload entries to Qdrant
    points = []
    for i, entry in enumerate(entries):
        # In a real application, you would generate vectors from the text
        # using a sentence transformer model
        vector = get_mock_vector()
        payload = prepare_grammar_payload(entry)
        
        points.append(models.PointStruct(
            id=i,
            vector=vector,
            payload=payload
        ))
    
    # Upload in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        print(f"Uploaded {len(batch)} entries (IDs {i} to {i+len(batch)-1})")
    
    print(f"Upload complete. {len(points)} entries added to {collection_name} collection.")
    print(f"You can now query the collection using the Qdrant client.")

if __name__ == "__main__":
    main()