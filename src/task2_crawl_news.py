"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Đọc danh sách bài viết từ data/manifest_news.csv.
    2. Cào từng URL, trích xuất text/markdown sạch bằng TextExtractor (adapt từ Day 7)
       hoặc Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ trường: url, title, date_crawled và content_markdown.
"""

import csv
from datetime import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"
MANIFEST_PATH = Path(__file__).parent.parent / "data" / "manifest_news.csv"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Danh sách bài viết dự phòng nếu không tìm thấy file manifest_news.csv
FALLBACK_ARTICLES = [
    {
        "doc_id": "article_01",
        "title": "Thông báo kết quả chính thức HBKK HK2 Khoa CNTT và các Khoa",
        "url": "https://hcmus.edu.vn/thong-bao-ket-qua-chinh-thuc-hbkk-hk2-2025-2026-khoa-cong-nghe-thong-tin-dien-tu-vien-thong-hoa-hoc-khoa-hoccnvl-moi-truong-sinh-hoc-cnsh-vat-ly-vlkt-ctda/",
    },
    {
        "doc_id": "article_02",
        "title": "Thông báo Kết quả dự kiến Điểm rèn luyện HK2 và HK3",
        "url": "https://hcmus.edu.vn/thong-bao-ket-qua-du-kien-diem-ren-luyen-hk2-2025-2026-ct-chuan-va-hk3-2025-2026-ct-de-an/",
    },
    {
        "doc_id": "article_03",
        "title": "Thời khóa biểu chính thức môn giai đoạn đại cương HK1 tại cơ sở 2",
        "url": "https://hcmus.edu.vn/thoi-khoa-bieu-chinh-thuc-mon-giai-doan-dai-cuong-chuong-trinh-dai-tra-tai-nang-trong-hk1-2026-2027-tai-co-so-2/",
    },
    {
        "doc_id": "article_04",
        "title": "Thông báo nộp hồ sơ xét tốt nghiệp đại học hệ chính quy các chương trình",
        "url": "https://hcmus.edu.vn/thong-bao-nop-ho-so-xet-tot-nghiep-dai-hoc-he-chinh-quy-cac-chuong-trinh-cho-cac-dot-cong-bo-danh-sach-tot-nghiep-thang-9-10-va-11-nam-2025/",
    },
    {
        "doc_id": "article_05",
        "title": "Sinh hoạt công dân đầu khóa năm học 2026",
        "url": "https://hcmus.edu.vn/sinh-hoat-cong-dan-dau-khoa-2026/",
    },
]

# --- HTML-to-Markdown Text Extractor (kế thừa từ Day 7) ---
BLOCK_TAGS = {"p", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "div", "section", "article"}
SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg", "iframe", "aside"}


class TextExtractor(HTMLParser):
    """Bộ bóc tách nội dung HTML sang text/markdown sạch sẽ không cần phụ thuộc bên ngoài."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth += 1
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = True
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = False
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            if self.in_title:
                self.title_parts.append(data)
            self.parts.append(data)

    def text(self) -> str:
        text = re.sub(r"[ \t]+", " ", "".join(self.parts))
        text = re.sub(r"\n[ \t]+", "\n", text)
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def page_title(self) -> str:
        return " ".join("".join(self.title_parts).split())


def load_manifest() -> list[dict[str, str]]:
    """Đọc danh sách bài viết từ manifest_news.csv."""
    if not MANIFEST_PATH.exists():
        return FALLBACK_ARTICLES

    articles = []
    with open(MANIFEST_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, 1):
            url = row.get("url", "").strip()
            title = row.get("title", "").strip()
            doc_id = row.get("doc_id", "").strip() or f"article_{index:02d}"
            if url:
                articles.append({
                    "doc_id": doc_id,
                    "title": title,
                    "url": url,
                })
    return articles or FALLBACK_ARTICLES


def crawl_article(url: str, title: str = "") -> dict:
    """Crawl một bài viết và trả về dict đúng contract yêu cầu."""
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    response.raise_for_status()

    extractor = TextExtractor()
    extractor.feed(response.text)

    extracted_title = title or extractor.page_title() or "Thông báo HCMUS"
    markdown_content = extractor.text()

    if len(markdown_content) < 50:
        raise ValueError(f"Nội dung cào được quá ngắn ({len(markdown_content)} ký tự) tại {url}")

    return {
        "url": url,
        "title": extracted_title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": markdown_content,
    }


def crawl_all() -> None:
    """Crawl toàn bộ danh sách bài viết và lưu thành JSON vào data/landing/news/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    articles = load_manifest()
    print(f"Bắt đầu crawl {len(articles)} bài viết từ manifest...")

    for index, item in enumerate(articles, 1):
        url = item["url"]
        title = item.get("title", "")
        doc_id = item.get("doc_id") or f"article_{index:02d}"
        output = DATA_DIR / f"{doc_id}.json"

        print(f"[{index}/{len(articles)}] Đang tải: {url}")
        try:
            article_data = crawl_article(url, title=title)
            output.write_text(
                json.dumps(article_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"-> Đã lưu: {output}")
        except Exception as error:
            print(f"Lỗi khi crawl {url}: {error}")


if __name__ == "__main__":
    crawl_all()
