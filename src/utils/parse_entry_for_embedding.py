def parse_entry_for_embedding(text):
    """
    Convert a 
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
    
    description = "\n".join(content_lines)
    
    return {
        "grammar_name_kr": grammar_name_kr,
        "grammar_name_rus": grammar_name_rus,
        "description": description
    }