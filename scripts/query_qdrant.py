"""
Script to query the Qdrant collection with Korean grammar data.
This script allows searching for grammar patterns by keyword or similarity.
"""

import argparse
import json
from typing import Dict, List, Union

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, SearchParams

def get_mock_query_vector(dim: int = 768) -> List[float]:
    """Generate a mock query vector for testing without a real model."""
    # In a real application, you would generate this from the query text
    # using a sentence transformer model
    return list(np.random.random(dim))

def format_search_result(result: Dict) -> str:
    """Format a search result for display."""
    payload = result.payload
    
    # Extract basic info
    grammar_kr = payload.get("grammar_name_kr", "")
    grammar_rus = payload.get("grammar_name_rus", "")
    description = payload.get("description", "")
    usage_form = payload.get("usage_form", "")
    
    # Format examples
    examples = payload.get("examples", [])
    examples_text = ""
    for i, example in enumerate(examples, 1):
        examples_text += f"\n  {i}. {example.get('korean', '')} - {example.get('russian', '')}"
    
    # Format notes
    notes = payload.get("notes", [])
    notes_text = ""
    for i, note in enumerate(notes, 1):
        notes_text += f"\n  {i}. {note}"
    
    # Build the formatted output
    output = f"Grammar: {grammar_kr} | {grammar_rus}\n"
    output += f"Description: {description}\n"
    output += f"Usage: {usage_form}\n"
    
    if examples_text:
        output += f"Examples:{examples_text}\n"
    
    if notes_text:
        output += f"Notes:{notes_text}\n"
    
    output += f"Score: {result.score:.4f}\n"
    
    return output

def search_by_keyword(client: QdrantClient, collection_name: str, keyword: str, limit: int = 5) -> List[Dict]:
    """Search for grammar patterns by keyword match."""
    # Define the search filter
    search_filter = Filter(
        must=[
            FieldCondition(
                key="text",
                match=MatchValue(value=keyword)
            )
        ]
    )
    
    # Perform the search
    results = client.search(
        collection_name=collection_name,
        query_vector=get_mock_query_vector(),
        query_filter=search_filter,
        limit=limit,
        search_params=SearchParams(exact=False)
    )
    
    return results

def search_by_similarity(client: QdrantClient, collection_name: str, query: str, limit: int = 5) -> List[Dict]:
    """Search for grammar patterns by semantic similarity."""
    # In a real application, you would convert the query to a vector
    # using the same sentence transformer model used for indexing
    query_vector = get_mock_query_vector()
    
    # Perform the search
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )
    
    return results

def main():
    """Main function to query the Qdrant collection."""
    parser = argparse.ArgumentParser(description="Search Korean grammar patterns in Qdrant")
    parser.add_argument("--keyword", type=str, help="Keyword to search for (exact match)")
    parser.add_argument("--query", type=str, help="Text query for semantic search")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results to return")
    parser.add_argument("--collection", type=str, default="korean_grammar", help="Qdrant collection name")
    parser.add_argument("--host", type=str, default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    args = parser.parse_args()
    
    # Validate arguments
    if not args.keyword and not args.query:
        parser.error("Either --keyword or --query must be provided")
    
    # Initialize Qdrant client
    client = QdrantClient(host=args.host, port=args.port)
    
    # Perform search
    if args.keyword:
        print(f"Searching for keyword: {args.keyword}")
        results = search_by_keyword(client, args.collection, args.keyword, args.limit)
    else:
        print(f"Searching for similar content to: {args.query}")
        results = search_by_similarity(client, args.collection, args.query, args.limit)
    
    # Display results
    if not results:
        print("No results found")
    else:
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(format_search_result(result))

if __name__ == "__main__":
    main()