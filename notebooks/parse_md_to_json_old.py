"""
2 versions: 

1) MD with all grammars -> Json file with grammars
- Takes a markdown file with all grammar entries and converts it to JSON.
- Used before the create_qdrant_collection.py or create_qdrant_collection.ipynb

2) Split MD with all grammars -> a folder of MD files
"""

import json

from src.utils.md_to_json import parse_entry_v1, parse_entry_v2


# !INFO Used for MD to Json parsing
def parse_input(input_text):
    # Split the entire input by the delimiter.
    parts = input_text.split('---')
    entries = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        #? INFO Find parse_entry in llm_agent utils
        entry = parse_entry_v1(part)
        entries.append(entry)
    return entries


# !INFO Used for just splitting into MD files
def parse_input_md(input_text):
    parts = input_text.split('---')
    entries = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        entry = parse_entry_v2(part)
        entries.append(entry)
    return entries


if __name__ == "__main__":
    # Read input_text from the specified file
    with open("data/grammar-level-1/grammar_list_clean.md", "r", encoding="utf-8") as infile:
        input_text = infile.read()

    #!INFO Save the JSON result to the specified file

    # result = parse_input(input_text)
    # print(f"Parsed {len(result)} grammar entries")
    #
    # output_json = json.dumps(result, ensure_ascii=False, indent=2)
    # with open("data/grammar-level-1/entries.json", "w", encoding="utf-8") as outfile:
    #     outfile.write(output_json)
    
    #!INFO For V2 split
    grammar_list = parse_input_md(input_text)
    print(grammar_list)
    # for i, grammar in enumerate(grammar_list):
    #     filename = f"data/grammar-level-1/entries_md/grammar_{i+1}.md"
    #     with open(filename, "w", encoding="utf-8") as outfile:
    #         outfile.write(grammar)