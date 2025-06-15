import json
from pprint import pprint
import re

LEVEL = 1

def parse_entry_v2(text):
    """
    Parse the MD files into JSON format:
    - Separate Korean and Russian grammar names
    - Add level
    -
    - Keep the rest together
    """
    lines = text.strip().splitlines()
    
    # Parse grammar names from the first line
    header_line = lines[0]
    grammar_name_kr, grammar_name_rus = [part.strip() for part in header_line.split('|', 1)]
    
    # Everything after the header is content
    content_lines = lines[1:]
    content_lines = [line.strip() for line in content_lines]
    
    # Remove any leading/trailing empty lines
    while content_lines and not content_lines[0].strip():
        content_lines.pop(0)
    while content_lines and not content_lines[-1].strip():
        content_lines.pop()
    
    content = "\n".join(content_lines)
    
    return {
        "grammar_name_kr": grammar_name_kr,
        "grammar_name_rus": grammar_name_rus,
        "level": LEVEL,
        "content": content
    }

def parse_entry_v1(text):
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

    # Assemble the entry, only including non-empty fields
    entry = {"level": LEVEL}
    if grammar_name_kr:
        entry["grammar_name_kr"] = grammar_name_kr
    if grammar_name_rus:
        entry["grammar_name_rus"] = grammar_name_rus
    if description:
        entry["description"] = description
    if usage_form:
        entry["usage_form"] = usage_form
    if examples:
        entry["examples"] = examples
    if notes:
        entry["notes"] = notes

    return entry


if __name__ == "__main__":
    with open("data/grammar-level-1/entries_md/grammar_3.md", "r", encoding="utf-8") as infile:
        input_text = infile.read()

    result = parse_entry_v2(input_text)
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    with open("data/grammar-level-1/entries_md/grammar_1_clean.json", "w", encoding="utf-8") as infile:
        infile.write(output_json)
    pprint(result, indent=0)