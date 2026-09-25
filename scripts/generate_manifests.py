#!/usr/bin/env python3
"""
scripts/generate_manifests.py
Tự động đọc danh sách link từ data/raw_urls.txt với 3 chế độ:
  1. [seed]: Tự động quét (Auto-Discovery) các bài viết và file PDF đính kèm từ trang danh mục/tổng quan.
  2. [legal]: Thêm trực tiếp các URL tài liệu pháp quy (PDF/DOCX).
  3. [news]: Thêm trực tiếp các URL bài viết/thông báo (HTML).
(Hoặc dán URL tự do để hệ thống tự nhận diện).

Kết quả: Xuất ra manifest_legal.csv và manifest_news.csv để con người (HITL) duyệt/chỉnh sửa.
"""

import argparse
import csv
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlparse
from bs4 import BeautifulSoup
import requests


ROOT_DIR = Path(__file__).parent.parent
RAW_URLS_FILE = ROOT_DIR / "data" / "raw_urls.txt"
MANIFEST_LEGAL = ROOT_DIR / "data" / "manifest_legal.csv"
MANIFEST_NEWS = ROOT_DIR / "data" / "manifest_news.csv"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Ánh xạ tên quy chế đẹp mắt từ các từ khoá trong tên file
LEGAL_TITLE_MAP = {
    "quy-che-drl": "Quy chế đánh giá kết quả rèn luyện sinh viên",
    "qc-drl": "Quy chế đánh giá kết quả rèn luyện sinh viên",
    "hbkk-qd575": "Quy định xét cấp học bổng khuyến khích học tập QĐ 575/2024",
    "hbkk-423": "Quy định xét cấp học bổng khuyến khích học tập QĐ 423/2023",
    "hbkk-qd593": "Quy định xét cấp học bổng khuyến khích học tập QĐ 593/2022",
    "qd326": "Quy định đào tạo trình độ đại học theo học chế tín chỉ QĐ 326",
    "hoc-phi": "Quy định về mức thu học phí và lộ trình học phí",
    "shub": "Hướng dẫn sổ tay sinh viên và sinh hoạt công dân",
}

# Các từ khoá loại trừ khỏi danh sách bài viết (tránh trang tĩnh, giới thiệu chung)
EXCLUDED_KEYWORDS = [
    "/category/", "/author/", "/tag/", "/page/", "facebook.com", "youtube.com",
    "hinh-thanh-va-phat-trien", "chien-luoc-phat-trien", "tuyen-bo-su-menh",
    "dhqg-tp-hcm-va-cac-don-vi", "co-cau-to-chuc", "doi-ngu-nghien-cuu",
    "hoi-dong-khoa-hoc", "khoa-vien", "trung-tam-phong-thi-nghiem",
    "he-thong-nhan-dien", "dstn", "tra-cuu", "congkhaigiaoduc", "quytrinh-bieumau"
]


def sanitize_filename(url: str, title: str = "") -> str:
    path = urlparse(url).path
    name = Path(path).name
    if not name.lower().endswith(".pdf"):
        name = (title or "document") + ".pdf"
    clean = re.sub(r"[^\w\-.]+", "-", unquote(name)).strip("-").lower()
    return clean or "document.pdf"


def guess_legal_title(filename: str, fallback_title: str = "") -> str:
    for key, val in LEGAL_TITLE_MAP.items():
        if key in filename.lower():
            return val
    if fallback_title and len(fallback_title) > 10:
        return fallback_title
    return Path(filename).stem.replace("-", " ").replace("_", " ").title()


def guess_category(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ["hoc-bong", "hbkk", "hoc bong", "học bổng"]):
        return "hoc-bong"
    if any(k in lowered for k in ["ren-luyen", "drl", "rèn luyện"]):
        return "ctsv"
    if any(k in lowered for k in ["tot-nghiep", "tốt nghiệp", "xét tốt nghiệp"]):
        return "tot-nghiep"
    if any(k in lowered for k in ["hoc-phi", "học phí"]):
        return "hoc-phi"
    if any(k in lowered for k in ["thoi-khoa-bieu", "hoc-phan", "học phần", "đào tạo", "dao-tao"]):
        return "hoc-vu"
    return "chung"


def clean_title(title: str) -> str:
    title = re.sub(r"\s*[-|–]\s*(Trường Đại học Khoa học Tự nhiên|HCMUS|ĐHQG-HCM).*$", "", title, flags=re.I)
    return title.strip()


def inspect_url(url: str) -> dict:
    url = url.strip()
    is_pdf = url.lower().endswith((".pdf", ".doc", ".docx"))

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15, stream=True)
        content_type = response.headers.get("Content-Type", "").lower()
        if any(mime in content_type for mime in ["application/pdf", "application/msword", "officedocument"]):
            is_pdf = True

        title = ""
        if not is_pdf and "text/html" in content_type:
            chunk = next(response.iter_content(65536), b"").decode("utf-8", errors="ignore")
            soup = BeautifulSoup(chunk, "html.parser")
            og_title = soup.find("meta", property="og:title")
            title_tag = soup.find("title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif title_tag:
                title = title_tag.get_text().strip()
            title = clean_title(title)

        return {
            "url": url,
            "is_pdf": is_pdf,
            "title": title,
            "status": response.status_code,
        }
    except Exception as e:
        print(f"  [!] Lỗi kết nối tới {url}: {e}")
        return {"url": url, "is_pdf": is_pdf, "title": "", "status": "error"}


def discover_from_seed(seed_url: str, max_articles: int = 5) -> tuple[list[dict], list[dict]]:
    """Tự động cào trang tổng quan để tìm bài viết con và các tài liệu đính kèm (Auto-Discovery)."""
    print(f"\n🔍 [AUTO-DISCOVERY] Đang quét trang mồi: {seed_url}...")
    legal_found = []
    news_found = []

    try:
        response = requests.get(seed_url, headers=DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        seen_urls = set()
        articles_to_inspect = []

        for a in soup.find_all("a", href=True):
            href = urljoin(seed_url, a["href"]).split("#")[0].strip()
            text = a.get_text(strip=True)

            if not href or href in seen_urls:
                continue

            # Bắt link PDF trực tiếp trên trang seed
            if href.lower().endswith((".pdf", ".doc", ".docx")):
                seen_urls.add(href)
                legal_found.append({
                    "url": href,
                    "title": text or Path(href).name,
                })
                continue

            # Bắt các link bài viết thông báo
            is_hcmus = "hcmus.edu.vn" in href
            is_excluded = any(ex in href for ex in EXCLUDED_KEYWORDS)
            has_good_title = len(text) >= 20 or any(k in href for k in ["thong-bao", "thoi-khoa-bieu", "sinh-hoat"])

            if is_hcmus and not is_excluded and has_good_title:
                seen_urls.add(href)
                articles_to_inspect.append((href, text))

        print(f"  -> Tìm thấy {len(articles_to_inspect)} bài viết tiềm năng.")

        # Lấy tối đa max_articles bài viết và quét thêm file PDF đính kèm bên trong bài
        for article_url, article_title in articles_to_inspect[:max_articles]:
            news_found.append({
                "url": article_url,
                "title": clean_title(article_title),
            })

            # Quét nhanh xem bài viết có link đính kèm file PDF quy chế không
            try:
                sub_res = requests.get(article_url, headers=DEFAULT_HEADERS, timeout=10)
                sub_soup = BeautifulSoup(sub_res.text, "html.parser")
                for sub_a in sub_soup.find_all("a", href=True):
                    sub_href = urljoin(article_url, sub_a["href"]).split("#")[0].strip()
                    if sub_href.lower().endswith((".pdf", ".doc", ".docx")) and sub_href not in seen_urls:
                        seen_urls.add(sub_href)
                        attach_title = sub_a.get_text(strip=True) or Path(sub_href).name
                        legal_found.append({
                            "url": sub_href,
                            "title": f"Đính kèm: {article_title[:40]} ({attach_title})",
                        })
                        print(f"  -> Nhặt được file PDF đính kèm: {sub_href}")
            except Exception:
                pass

    except Exception as e:
        print(f"  [!] Lỗi khi quét trang mồi {seed_url}: {e}")

    return legal_found, news_found


def parse_raw_urls() -> tuple[list[tuple[str, str | None]], list[str]]:
    """Đọc file raw_urls.txt, phân tách mục [seed], [legal], [news]."""
    if not RAW_URLS_FILE.exists():
        print(f"File {RAW_URLS_FILE} không tồn tại!")
        return [], []

    lines = RAW_URLS_FILE.read_text(encoding="utf-8").splitlines()
    direct_items: list[tuple[str, str | None]] = []
    seed_urls: list[str] = []
    current_section: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        section_match = re.match(r"^\[(legal|news|seed)\]$", stripped, flags=re.I)
        if section_match:
            current_section = section_match.group(1).lower()
            continue

        if current_section == "seed":
            seed_urls.append(stripped)
        elif "|" in stripped:
            parts = [p.strip() for p in stripped.split("|", 1)]
            url, inline_sec = parts[0], parts[1].lower()
            if inline_sec == "seed":
                seed_urls.append(url)
            else:
                sec = inline_sec if inline_sec in {"legal", "news"} else current_section
                direct_items.append((url, sec))
        else:
            direct_items.append((stripped, current_section))

    return direct_items, seed_urls


def process_urls():
    direct_items, seed_urls = parse_raw_urls()

    legal_entries = []
    news_entries = []
    seen_urls = set()

    # 1. Quét từ các Seed URL (nếu có)
    for seed in seed_urls:
        discovered_legal, discovered_news = discover_from_seed(seed)
        for item in discovered_legal:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                legal_entries.append(item)
        for item in discovered_news:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                news_entries.append(item)

    # 2. Xử lý các Direct URLs
    print(f"\n🔍 [DIRECT CHECK] Kiểm tra {len(direct_items)} URLs trực tiếp...")
    for idx, (url, assigned_type) in enumerate(direct_items, 1):
        if url in seen_urls:
            continue
        seen_urls.add(url)

        tag_str = f"[{assigned_type.upper()}]" if assigned_type else "[Tự đoán]"
        print(f"[{idx}/{len(direct_items)}] {tag_str} Kiểm tra: {url}")
        info = inspect_url(url)

        doc_type = assigned_type if assigned_type in {"legal", "news"} else ("legal" if info["is_pdf"] else "news")
        if doc_type == "legal":
            legal_entries.append({"url": url, "title": info["title"]})
        else:
            news_entries.append({"url": url, "title": info["title"]})

    # 3. Định dạng và ghi vào manifest_legal.csv
    legal_rows = []
    for item in legal_entries:
        filename = sanitize_filename(item["url"], item.get("title", ""))
        title = guess_legal_title(filename, item.get("title", ""))
        category = guess_category(f"{filename} {title}")
        legal_rows.append({
            "filename": filename,
            "title": title,
            "url": item["url"],
            "category": category,
            "source_type": "legal"
        })

    if legal_rows:
        with open(MANIFEST_LEGAL, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["filename", "title", "url", "category", "source_type"])
            writer.writeheader()
            writer.writerows(legal_rows)
        print(f"\n-> Đã cập nhật: {MANIFEST_LEGAL} ({len(legal_rows)} tài liệu PDF)")

    # 4. Định dạng và ghi vào manifest_news.csv
    news_rows = []
    for index, item in enumerate(news_entries, 1):
        doc_id = f"article_{index:02d}"
        raw_slug_title = Path(urlparse(item["url"]).path).name.replace("-", " ").capitalize()
        title = item.get("title") or raw_slug_title or f"Thông báo học vụ HCMUS #{index}"
        category = guess_category(f"{title} {item['url']}")
        news_rows.append({
            "doc_id": doc_id,
            "title": title,
            "url": item["url"],
            "category": category,
            "source_type": "news"
        })

    if news_rows:
        with open(MANIFEST_NEWS, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["doc_id", "title", "url", "category", "source_type"])
            writer.writeheader()
            writer.writerows(news_rows)
        print(f"-> Đã cập nhật: {MANIFEST_NEWS} ({len(news_rows)} bài viết HTML)")

    print("\n✅ HOÀN TẤT AUTO-DISCOVERY & TẠO MANIFEST!")
    print("👉 Bây giờ bạn (HITL) có thể xem lại 2 file CSV để kiểm tra, chỉnh sửa trước khi tải:")
    print(f"   1. {MANIFEST_LEGAL}")
    print(f"   2. {MANIFEST_NEWS}")


if __name__ == "__main__":
    process_urls()
