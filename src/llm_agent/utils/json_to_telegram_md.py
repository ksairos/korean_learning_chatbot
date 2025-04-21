import re

from src.schemas.schemas import GrammarEntry


def grammar_entry_to_markdown(entry: GrammarEntry):

    lines = []
    # Emphasize all Korean words
    pattern = r'([가-힣]+)'

    # Header: combine the Korean and Russian grammar names in a bold line.
    grammar_name_kr = entry.grammar_name_kr.strip()
    grammar_name_rus = entry.grammar_name_rus.strip()
    header = f"**{grammar_name_kr} - {grammar_name_rus}**"
    lines.append(header)
    lines.append("")

    # Описание section: Bold any occurrence of the Korean grammar name in the description.
    lines.append("**Описание:**")
    description = entry.description.strip()
    # Replace occurrences of the grammar name with its bolded version.
    description = re.sub(pattern, r'**\1**', description)
    lines.append(description)
    lines.append("")  # blank line

    # Форма section.
    lines.append("**Форма:**")
    usage_form = entry.usage_form.strip()
    # Replace occurrences of the grammar name with its bolded version.
    usage_form = re.sub(pattern, r'**\1**', usage_form)
    lines.append(usage_form)
    lines.append("")  # blank line

    # Примеры section.
    examples = entry.examples
    if examples:
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
    notes = entry.notes
    if notes:
        lines.append("**Примечания:**")
        for idx, note in enumerate(notes, start=1):
            # Replace occurrences of the grammar name with its bolded version.
            note = re.sub(pattern, r'**\1**', note)
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
        ],
        "notes": [
          "Если слово заканчивается на согласную, обычно добавляется 을, а если на гласную – 를.",
          "Правильное употребление этих окончаний помогает чётко определить объект действия."
        ]
      }

    md_output = grammar_entry_to_markdown(GrammarEntry(**foo))

    print(md_output)
