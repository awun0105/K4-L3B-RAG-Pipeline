"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm (HCMUS - Dịch vụ sinh viên, đào tạo, học bổng).
    2. Đọc danh sách tài liệu từ data/manifest_legal.csv.
    3. Tải tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    4. Lưu file gốc vào data/landing/legal/.
    5. Đặt tên không dấu và thể hiện đúng nội dung.
"""

import csv
from pathlib import Path
import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"
MANIFEST_PATH = Path(__file__).parent.parent / "data" / "manifest_legal.csv"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Danh sách dự phòng nếu không đọc được từ file CSV
FALLBACK_SOURCES = {
    "quy-che-diem-ren-luyen-hcmus.pdf": "https://hcmus.edu.vn/wp-content/uploads/2018/03/2016-07-Quy-che-DRL.pdf",
    "quy-dinh-hoc-bong-kkht-qd575.pdf": "https://hcmus.edu.vn/wp-content/uploads/2025/06/QUYDINH-HBKK-QD575-2024.pdf",
    "quy-dinh-hoc-bong-kkht-qd423.pdf": "https://hcmus.edu.vn/wp-content/uploads/2023/11/QD-HBKK-423-28112003.pdf",
    "quy-che-dao-tao-tin-chi-qd326.pdf": "https://hcmus.edu.vn/wp-content/uploads/2024/01/QD326.pdf",
}


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def load_manifest() -> dict[str, str]:
    """Đọc cấu hình URL từ manifest_legal.csv."""
    if not MANIFEST_PATH.exists():
        return FALLBACK_SOURCES

    sources: dict[str, str] = {}
    with open(MANIFEST_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            filename = row.get("filename", "").strip()
            url = row.get("url", "").strip()
            if filename and url:
                sources[filename] = url
    return sources or FALLBACK_SOURCES


def download_documents() -> None:
    """Tải các tài liệu PDF/DOCX từ nguồn công khai vào landing/legal/."""
    setup_directory()
    sources = load_manifest()
    print(f"Tìm thấy {len(sources)} tài liệu trong manifest.")

    for filename, url in sources.items():
        destination = DATA_DIR / filename
        if destination.exists() and destination.stat().st_size > 1024:
            print(f"Skipped (already exists): {filename} ({destination.stat().st_size} bytes)")
            continue

        print(f"Đang tải {filename} từ {url}...")
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
            response.raise_for_status()

            if len(response.content) <= 1024:
                print(f"Cảnh báo: Kích thước file quá nhỏ ({len(response.content)} bytes) tại {url}")
                continue

            destination.write_bytes(response.content)
            print(f"Đã lưu thành công: {filename} ({len(response.content)} bytes)")
        except Exception as error:
            print(f"Lỗi khi tải {filename} ({url}): {error}")


if __name__ == "__main__":
    download_documents()
