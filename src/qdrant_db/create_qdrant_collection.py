"""
Creates and populates the qdrant collection with Korean grammar
Notebook version is available at notebooks/create_qdrant_collection.ipynb
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
from src.qdrant_db.parse_md_to_json import parse_entry_v1

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
    """Generate embedding vector from OpenAI."""
    try:
        response = openai_client.embeddings.create(
            model= config.embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error


# def reformat_for_embedding(entry: dict) -> str:
    # """
    # Reformat a single JSON entry into a single string for embedding.
    # """
    # parts = []

    # # Include grammar names if available
    # if "grammar_name_kr" in entry:
    #     parts.append(f"НАЗВАНИЕ НА КОРЕЙСКОМ: {entry['grammar_name_kr']}")
    # if "grammar_name_rus" in entry:
    #     parts.append(f"НАЗВАНИЕ НА РУССКОМ: {entry['grammar_name_rus']}")

    # # Include level information (optional)
    # level_mapping = {
    #     1: "Начинающий",
    #     2: "Базовый",
    #     3: "Средний",
    #     4: "Выше среднего",
    #     5: "Продвинутый",
    #     6: "Экспертный"
    # }

    # if "level" in entry:
    #     level_value = entry.get("level")
    #     level_name = level_mapping.get(level_value, f"Level {level_value}")
    #     parts.append(f"Level: {level_name} ({level_value})")

    # # Append description
    # if "description" in entry and entry["description"]:
    #     parts.append(f"ОПИСАНИЕ: {entry['description']}")

    # # Append usage form
    # if "usage_form" in entry and entry["usage_form"]:
    #     parts.append(f"ФОРМА: {entry['usage_form']}")

    # # Append examples
    # if "examples" in entry and entry["examples"]:
    #     for idx, example in enumerate(entry["examples"], start=1):
    #         korean = example.get("korean", "")
    #         russian = example.get("russian", "")
    #         parts.append(f"ПРИМЕР {idx}: НА КОРЕЙСКОМ: {korean} | НА РУССКОМ: {russian}")

    # # Append notes
    # if "notes" in entry and entry["notes"]:
    #     # Join notes with a semicolon for clarity
    #     notes_combined = "; ".join(entry["notes"])
    #     parts.append(f"ПРИМЕЧАНИЯ: {notes_combined}")

    # # TODO: Add irregular verbs examples
    # # Combine all parts into one final string separated by newlines
    # return "\n".join(parts)

def reformat_for_embedding(entry: dict) -> str:
    return f"Грамматика {entry['grammar_name_kr']} - {entry['grammar_name_rus']}: {entry['description']}"

#? INFO For JSON grammars
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


#? INFO For MD grammars

def load_md_entries(dir_path: Path) -> List[str]:
    """Load all MD grammar entries from a directory"""
    content_list = [file.read_text(encoding='utf-8') for file in dir_path.glob("*.md")]
    return content_list

def create_qdrant_collection(collection_name: str) -> None:
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


if __name__ == "__main__":
    #! Select Mode before using: md or json
    MODE = "md"
    LEVEL = 1
    
    #? Load grammar entries from JSON
    if MODE == "json":
        COLLECTION_NAME = config.qdrant_collection_name
        create_qdrant_collection(COLLECTION_NAME)
        
        all_entries_json_file = Path("data/grammar-level-1/entries.json")

        if all_entries_json_file.exists():
            entries = load_json_entries(str(all_entries_json_file))
            print(f"{len(entries)} grammar entries to upload")
        else:
            print("Please run parse_md_to_json.py first to generate JSON files.")
            exit()
            
        # Generate embeddings and create points
        points = []
        for i, entry in enumerate(entries):

            formatted_entry = reformat_for_embedding(entry)
            vector = get_embedding(formatted_entry)
            sparse_vector = next(bm25_embedding_model.embed(formatted_entry)).as_object()
            
            points.append(models.PointStruct(
                id=i,
                vector={
                    config.embedding_model: vector,
                    config.sparse_embedding_model: sparse_vector
                },
                payload=entry
            ))
        
    elif MODE == "md":
        #? Load grammar entries from MD files
        COLLECTION_NAME = config.qdrant_collection_name_v2
        create_qdrant_collection(COLLECTION_NAME)
        
        all_entries_md_folder = Path("data/grammar-level-1/entries_md/")
        
        if all_entries_md_folder.exists():
            entries = load_md_entries(all_entries_md_folder)
            print(f"{len(entries)} grammar entries to upload")
        else:
            print("Please run parse_md_to_json.py first to generate JSON files.")
            exit()
            
        # Generate embeddings and create points
        points = []
        for i, entry in enumerate(entries):

            parsed_entry = parse_entry_v1(entry) # Create disctionary 
            formatted_entry = reformat_for_embedding(parsed_entry) # Select only grammar name and description for embedding
    
            vector = get_embedding(formatted_entry)
            sparse_vector = next(bm25_embedding_model.embed(formatted_entry)).as_object()
            
            grammar_name = f"{parsed_entry['grammar_name_kr']} - {parsed_entry['grammar_name_rus']}"
            payload = {
                "grammar_name": grammar_name,
                "level" : LEVEL,
                "content": entry
            }
            
            points.append(models.PointStruct(
                id=i,
                vector={
                    config.embedding_model: vector,
                    config.sparse_embedding_model: sparse_vector
                },
                payload=payload
            ))
    
    else:
        print("Select MODE")
        exit()

    print(f"Generated {len(points)} points")

    # Ingest points to the vector database

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"Upload complete. {len(points)} entries added to {COLLECTION_NAME} collection.")
    print("You can now query the collection using the Qdrant client.")