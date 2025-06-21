def parse_entry_for_embedding(entry) -> str:
    """
    Convert a single row of grammar dataframe into a string for embedding
    """
    grammar_name_kr = entry["grammar_name_kr"]
    grammar_name_rus = entry["grammar_name_rus"]
    content_lines = entry["content"].split("**Форма:**")[0].replace("\n", " ").strip()

    text_to_embed = f"Название грамматики: {grammar_name_kr} - {grammar_name_rus}\n{content_lines}"
    return text_to_embed