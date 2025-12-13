from bs4 import BeautifulSoup


def parse_seo(html: str):
    h1_text = None
    title_text = None
    description_text = None

    soup = BeautifulSoup(html, "html.parser")

    h1_tag = soup.find("h1")
    if h1_tag:
        h1_text = h1_tag.get_text(strip=True)

    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text(strip=True)

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description_text = meta_desc["content"].strip()

    return h1_text, title_text, description_text
