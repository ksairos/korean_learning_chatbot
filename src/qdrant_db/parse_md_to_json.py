"""
Takes a markdown file with all grammar entries and converts it to JSON.
Used before the create_qdrant_collection.py or create_qdrant_collection.ipynb
"""

import json
import re


def parse_entry(text):
    # Split text into non-empty, stripped lines.
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # The first line contains the grammar names.
    header = lines[0]
    parts = header.split("|")
    grammar_name_kr = parts[0].strip()
    grammar_name_rus = parts[1].strip() if len(parts) > 1 else ""

    description = ""
    usage_form = ""
    examples = []
    notes = []

    state = None
    i = 1
    while i < len(lines):
        line = lines[i]

        # Detect markers and set state accordingly.
        if line.startswith("Описание:"):
            state = "description"
            # Capture any text on the same line (after the colon)
            desc_line = line[len("Описание:"):].strip()
            if desc_line:
                description += desc_line + " "
            i += 1
            continue
        elif line.startswith("Форма:"):
            state = "usage_form"
            form_line = line[len("Форма:"):].strip()
            if form_line:
                usage_form = form_line
                state = None  # reset state once captured
            i += 1
            continue
        elif line.startswith("Примеры:"):
            state = "examples"
            i += 1
            continue
        elif line.startswith("Примечания:"):
            state = "notes"
            i += 1
            continue

        # Process line based on current state.
        if state == "description":
            description += line + " "
        elif state == "usage_form":
            if not usage_form:
                usage_form = line
            state = None  # only one line expected
        elif state == "examples":
            # Each example starts with "- ".
            if line.startswith("- "):
                # Remove the dash and space to get the Korean example.
                korean = line[2:].strip()
                russian = ""
                # Check if the next line is the Russian translation (in parentheses).
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.startswith("(") and next_line.endswith(")"):
                        russian = next_line[1:-1].strip()
                        i += 1  # Skip the translation line
                examples.append({
                    "korean": korean,
                    "russian": russian
                })
        elif state == "notes":
            # Each note line starts with a number and a dot.
            match = re.match(r"^\d+\.\s*(.*)$", line)
            if match:
                notes.append(match.group(1).strip())

        # TODO: Add irregular verbs examples
        i += 1

    # Clean up extra spaces.
    description = description.strip()

    # Build the JSON entry.
    return {
        "level": 1,
        "grammar_name_kr": grammar_name_kr,
        "grammar_name_rus": grammar_name_rus,
        "description": description,
        "usage_form": usage_form,
        "examples": examples,
        "notes": notes
    }


def parse_input(input_text):
    # Split the entire input by the delimiter.
    parts = input_text.split('---')
    entries = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        entry = parse_entry(part)
        entries.append(entry)
    return entries


if __name__ == "__main__":
    # Read input_text from the specified file
    with open("../data/grammar-level-1/generated-data.md", "r", encoding="utf-8") as infile:
        input_text = infile.read()

    result = parse_input(input_text)
    print(f"Parsed {len(result)} grammar entries")
    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    # Save the JSON result to the specified file
    with open("../data/grammar-level-1/entries.json", "w", encoding="utf-8") as outfile:
        outfile.write(output_json)
