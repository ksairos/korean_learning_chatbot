"""
Script to create a Qdrant collection and upload grammar entries.
This script reads JSON grammar entries, converts them to vectors using a sentence
transformer model, and uploads them to a Qdrant collection.
"""

import json
import logging

from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import SparseVectorParams, Modifier
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv
from fastembed import SparseTextEmbedding

from src.config.settings import Config

load_dotenv()
openai_client = OpenAI()
config = Config()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# prefer_grpc is set True to avoid timeout error
client = QdrantClient(
    host=config.qdrant_host,
    port=config.qdrant_port,
    # prefer_grpc=True
)

bm25_embedding_model = SparseTextEmbedding(config.sparse_embedding_model)

def get_embedding(text: str) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model= config.embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error

def reformat_for_embedding(entry: dict) -> str:
    """
    Reformat a single JSON entry into a single string for embedding.

    Args:
        entry (dict): The JSON entry with keys such as 'description', 'usage_form', 'examples', etc.

    Returns:
        str: A concatenated string containing the main textual content.
    """
    parts = []

    # Include grammar names if available
    if "grammar_name_kr" in entry:
        parts.append(f"НАЗВАНИЕ НА КОРЕЙСКОМ: {entry['grammar_name_kr']}")
    if "grammar_name_rus" in entry:
        parts.append(f"НАЗВАНИЕ НА РУССКОМ: {entry['grammar_name_rus']}")

    # Include level information (optional)
    level_mapping = {
        1: "Начинающий",
        2: "Базовый",
        3: "Средний",
        4: "Выше среднего",
        5: "Продвинутый",
        6: "Экспертный"
    }

    if "level" in entry:
        level_value = entry.get("level")
        level_name = level_mapping.get(level_value, f"Level {level_value}")
        parts.append(f"Level: {level_name} ({level_value})")

    # Append description
    if "description" in entry and entry["description"]:
        parts.append(f"ОПИСАНИЕ: {entry['description']}")

    # Append usage form
    if "usage_form" in entry and entry["usage_form"]:
        parts.append(f"ФОРМА: {entry['usage_form']}")

    # Append examples
    if "examples" in entry and entry["examples"]:
        for idx, example in enumerate(entry["examples"], start=1):
            korean = example.get("korean", "")
            russian = example.get("russian", "")
            parts.append(f"ПРИМЕР {idx}: НА КОРЕЙСКОМ: {korean} | НА РУССКОМ: {russian}")

    # Append notes
    if "notes" in entry and entry["notes"]:
        # Join notes with a semicolon for clarity
        notes_combined = "; ".join(entry["notes"])
        parts.append(f"ПРИМЕЧАНИЯ: {notes_combined}")

    # Combine all parts into one final string separated by newlines
    return "\n".join(parts)

def load_json_entries(dir_path: str) -> List[Dict[str, Any]]:
    """Load all JSON grammar entries from a directory."""
    entries = []
    path = Path(dir_path)
    
    # If path is a file, and it's a combined JSON file
    if path.is_file() and path.name.endswith('.json'):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data]
    
    return entries

def create_qdrant_collection(collection_name: str = config.qdrant_collection_name) -> None:
    """Create a Qdrant collection if it doesn't exist."""
    # List existing collections
    # Create a collection if it doesn't exist
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                config.embedding_model: VectorParams(
                    size=1536,
                    distance=Distance.COSINE,
                    on_disk=True
                ),
            },
            sparse_vectors_config={
                config.sparse_embedding_model: SparseVectorParams(modifier=Modifier.IDF) # INFO has GRPC version for Modifier
            },
            # INFO Set up a quantization for Droplet due to lack of RAM
            # INFO Check out https://qdrant.tech/documentation/guides/optimize/ for additional information
            # quantization_config=models.ScalarQuantization(
            #     scalar=models.ScalarQuantizationConfig(
            #         type=models.ScalarType.INT8,
            #         always_ram=True,
            #     ),
            # ) if quantization else None
        )
        logger.info(f"Collection {collection_name} created")
    else:
        logger.info(f"Collection {collection_name} already exists")

def main():
    """Main function to create a Qdrant collection and upload grammar entries."""
    
    # Create collection
    create_qdrant_collection()
    
    # Load grammar entries
    data_dir = Path("../data/grammar-level-1")
    all_entries_file = data_dir / "entries.json"
    
    if all_entries_file.exists():
        entries = load_json_entries(str(all_entries_file))
    else:
        logger.info("Please run parse_md_to_json.py first to generate JSON files.")
        return
    
    logger.info(f"Loaded {len(entries)} grammar entries")
    
    # Upload entries to Qdrant
    points = []
    for i, entry in enumerate(entries):

        formatted_entry = reformat_for_embedding(entry)
        vector = get_embedding(formatted_entry)
        sparse_vector = bm25_embedding_model.embed(formatted_entry)
        
        points.append(models.PointStruct(
            id=i,
            vector={
                config.embedding_model: vector,
                config.sparse_embedding_model: sparse_vector
            },
            payload=entry
        ))

    client.upsert(
        collection_name=config.qdrant_collection_name,
        points=points
    )
    
    logger.info(f"Upload complete. {len(points)} entries added to {config.qdrant_collection_name} collection.")
    logger.info(f"You can now query the collection using the Qdrant client.")

if __name__ == "__main__":
    main()