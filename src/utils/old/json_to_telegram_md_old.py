# import re
# import time

def grammar_entry_to_markdown(entry: dict) -> str:
    lines = []
    # Emphasize all Korean words
    # pattern = r'([가-힣]+)'

    # Header: combine the Korean and Russian grammar names in a bold line.
    grammar_name_kr = entry["grammar_name_kr"].strip()
    grammar_name_rus = entry["grammar_name_rus"].strip()
    header = f"**{grammar_name_kr} - {grammar_name_rus}**"
    lines.append(header)
    lines.append("")

    # Описание section: Bold any occurrence of the Korean grammar name in the description.
    lines.append("**Описание:**")
    description = entry["description"].strip()
    # Replace occurrences of the grammar name with its bolded version.
    # description = re.sub(pattern, r'**\1**', description)
    lines.append(description)
    lines.append("")  # blank line

    # Форма section.
    if "usage_form" in entry.keys():
      usage_form = entry["usage_form"].strip()
      lines.append("**Форма:**")
      # Replace occurrences of the grammar name with its bolded version.
      # usage_form = re.sub(pattern, r'**\1**', usage_form)
      lines.append(usage_form)
      lines.append("")  # blank line

    # Примеры section.
    
    if "examples" in entry.keys():
        examples = entry["examples"]
        lines.append("**Примеры:**")
        for example in examples:
            # For Korean example: display the text in bold.
            korean = example["korean"].strip()
            korean_line = f"**{korean}**"
            lines.append(korean_line)

            # For Russian example: display the text in italics.
            russian = example["russian"].strip()
            if russian:
                russian_line = f"*{russian}*"
                lines.append(russian_line)

        lines.append("")  # blank line to separate examples

    # Примечания section (if provided).
    if "notes" in entry.keys():
      notes = entry["notes"]
      lines.append("**Примечания:**")
      for idx, note in enumerate(notes, start=1):
        # Replace occurrences of the grammar name with its bolded version.
        # note = re.sub(pattern, r'**\1**', note)
        lines.append(f"{idx}. {note}")

    # Combine all lines into a single markdown string.
    markdown_text = "\n".join(lines).strip()

    return markdown_text


if __name__ == '__main__':
  
  foo =   {
      "level": 1,
      "grammar_name_kr": "을1, 를, ㄹ1",
      "grammar_name_rus": "объектные (винительные) падежные окончания",
      "description": "Окончания 을 и 를 используются для выделения прямого объекта в предложении, отвечая на вопрос «кого? что?». Выбор между ними зависит от последней буквы существительного.",
      "usage_form": "Существительное + 을/를",
      "examples": [
        {
          "korean": "사과를 먹어요.",
          "russian": "Я ем яблоко."
        },
        {
          "korean": "책을 읽어요.",
          "russian": "Я читаю книгу."
        }
      ]

    }

  # start_time = time.perf_counter()
  md_output = grammar_entry_to_markdown(foo)
  print(md_output)
  # elapsed = time.perf_counter() - start_time
  # print(f"\nRun time: {elapsed:.6f} seconds")