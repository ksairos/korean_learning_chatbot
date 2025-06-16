from markdown import markdown
from bs4 import BeautifulSoup

def strip_markdown(md_text):
    html = markdown(md_text)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

if __name__ == "__main__":
    example_text = ("**Описание:**\nЧастицы **이/가** обозначают **именительный падеж**"
                    "и *используются* для указания...\n")
    print(strip_markdown(example_text))