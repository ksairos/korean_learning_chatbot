# import re
# import time
import re

from chatgpt_md_converter.converters import convert_html_chars
from chatgpt_md_converter.extractors import extract_and_convert_code_blocks, reinsert_code_blocks
from chatgpt_md_converter.formatters import combine_blockquotes
from chatgpt_md_converter.helpers import remove_blockquote_escaping, remove_spoiler_escaping

def split_by_tag(out_text: str, md_tag: str, html_tag: str) -> str:
    """
    Splits the text by markdown tag and replaces it with the specified HTML tag.
    """
    tag_pattern = re.compile(
        r"{}(.*?){}".format(re.escape(md_tag), re.escape(md_tag)),
        re.DOTALL,
    )

    # Special handling for the tg-spoiler tag
    if html_tag == 'span class="tg-spoiler"':
        return tag_pattern.sub(r'<span class="tg-spoiler">\1</span>', out_text)

    return tag_pattern.sub(r"<{}>\1</{}>".format(html_tag, html_tag), out_text)


def extract_inline_code_snippets(text: str):
    """
    Extracts inline code (single-backtick content) from the text,
    replacing it with placeholders, returning modified text and a dict of placeholders -> code text.
    This ensures characters like '*' or '_' inside inline code won't be interpreted as Markdown.
    """
    placeholders = []
    code_snippets = {}
    inline_code_pattern = re.compile(r"`([^`]+)`")

    def replacer(match):
        snippet = match.group(1)
        placeholder = f"INLINECODEPLACEHOLDER{len(placeholders)}"
        placeholders.append(placeholder)
        code_snippets[placeholder] = snippet
        return placeholder

    new_text = inline_code_pattern.sub(replacer, text)
    return new_text, code_snippets

def custom_telegram_format(text: str) -> str:
    """
    Converts markdown in the provided text to HTML supported by Telegram.
    """

    # Step 0: Combine blockquotes
    text = combine_blockquotes(text)

    # Step 1: Convert HTML reserved symbols
    text = convert_html_chars(text)

    # Step 2: Extract and convert triple-backtick code blocks first
    output, triple_code_blocks = extract_and_convert_code_blocks(text)

    # Step 2.5: Extract inline code snippets (single backticks) so they won't be parsed as italics, etc.
    output, inline_code_snippets = extract_inline_code_snippets(output)

    # Step 3: Escape HTML special characters in the output text (for non-code parts)
    output = output.replace("<", "&lt;").replace(">", "&gt;")

    # Convert headings (H1-H6)
    output = re.sub(r"^(#{1,6})\s+(.+)$", r"<b>\2</b>", output, flags=re.MULTILINE)

    # Convert unordered lists
    output = re.sub(r"^(\s*)[\-\*]\s+(.+)$", r"\1• \2", output, flags=re.MULTILINE)

    # Nested Bold and Italic
    output = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", output)
    output = re.sub(r"\_\_\_(.*?)\_\_\_", r"<u><i>\1</i></u>", output)

    # Bold, underline, strikethrough, spoiler
    output = split_by_tag(output, "**", "b")
    output = split_by_tag(output, "__", "u")
    output = split_by_tag(output, "~~", "s")
    output = split_by_tag(output, "||", 'span class="tg-spoiler"')
    
    # Custom approach for single-asterisk italic
    italic_pattern = re.compile(
        r"(?<![A-Za-z0-9])\*(?=[^\s])(.*?)(?<!\s)\*(?![A-Za-z0-9])", re.DOTALL
    )
    output = italic_pattern.sub(r"<i>\1</i>", output)

    # Process single underscore-based italic (works the same)
    output = split_by_tag(output, "_", "i")

    # Remove storage links
    output = re.sub(r"【[^】]+】", "", output)

    # Links and images
    link_pattern = r"(?:!?)\[((?:[^\[\]]|\[.*?\])*)\]\(([^)]+)\)"
    output = re.sub(link_pattern, r'<a href="\2">\1</a>', output)

    # Reinsert inline code snippets
    for placeholder, snippet in inline_code_snippets.items():
        escaped_snippet = (
            snippet.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
        )
        output = output.replace(placeholder, f"<code>{escaped_snippet}</code>")

    # Reinsert triple-backtick code blocks
    output = reinsert_code_blocks(output, triple_code_blocks)

    # Unescape blockquotes and spoilers
    output = remove_blockquote_escaping(output)
    output = remove_spoiler_escaping(output)

    # Cleanup
    output = re.sub(r"\n{3,}", "\n\n", output)

    return output.strip()


def grammar_entry_to_markdown(entry: dict) -> str:
    lines = []
    
    # Header: combine the Korean and Russian grammar names in a bold line.
    grammar_name_kr = entry["grammar_name_kr"].strip()
    grammar_name_rus = entry["grammar_name_rus"].strip()
    header = f"**{grammar_name_kr} - {grammar_name_rus}**"
    lines.append(header)
    lines.append("")

    description = entry["content"].strip()
    lines.append(description)

    # Combine all lines into a single markdown string.
    markdown_text = "\n".join(lines).strip()

    return custom_telegram_format(markdown_text)


if __name__ == '__main__':
  
  foo =   {
    'grammar_name_kr': '까지', 
    'grammar_name_rus': '«до»', 
    'level': 1, 
    'content': '**Описание:**\nЧастица **까지** используется для обозначения предела действия или состояния в значении **«до»**. Может указывать как на **временные границы** (до какого времени), так и на **пространственные пределы** (до какого места).\n\n**Форма:**\n**Существительное + 까지**\nПрисоединяется непосредственно к существительному, обозначающему время или место.\n\n**Примеры:**\n학교**까지** 걸어서 갔어요.\nЯ пошёл до школы пешком.\n\n밤 12시**까지** 공부했어요.\nУчился до полуночи.\n\n부산**까지** 기차로 가요.\nДо Пусана еду на поезде.\n\n이번 주 금요일**까지** 숙제를 내세요.\nСдайте домашнее задание до этой пятницы.\n\n**Примечания:**\n\n1. Часто используется вместе с **부터** (с): **부터 … 까지** - «от … до» - если говорить о времени.\n    **Например:**\n\n오전 9시**부터** 오후 5시**까지** 일해요.\nРаботаю с 9 утра до 5 вечера.\n\n1. Часто используется вместе с **에서** (из): **에서 … 까지** - «из … до» - если говорить о местах.\n    **Например:**\n\n서울**에서** 경주**까지** 기차로 왔어요.\n\nДоехал из Сеула до Кёнджу на поезде.\n\n1. Может использоваться не только в буквальном, но и в переносном смысле.\n    **Например:**\n\n너**까지** 나를 의심해?\nДаже ты меня подозреваешь?\n', 
    'related_grammars': ['부터', '에서 «из»']
  }

  # start_time = time.perf_counter()
  md_output = grammar_entry_to_markdown(foo)
  print(md_output)
  # elapsed = time.perf_counter() - start_time
  # print(f"\nRun time: {elapsed:.6f} seconds")