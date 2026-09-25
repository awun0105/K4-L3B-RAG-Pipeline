"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

try:
    from pageindex import PageIndexAPIError, PageIndexClient
    from pageindex import client as pageindex_client
except ImportError:  # PageIndex is an optional fallback, never an import blocker.
    PageIndexAPIError = RuntimeError
    PageIndexClient = None
    pageindex_client = None

from .task4_chunking_indexing import load_documents


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "").strip()
DATA_DIR = Path(__file__).parent.parent / "data"
STANDARDIZED_DIR = DATA_DIR / "standardized"
# Tên file/dir khớp .gitignore để cache cục bộ không bị commit.
CACHE_PATH = DATA_DIR / "pageindex_doc_ids.json"
TEMP_PDF_DIR = DATA_DIR / "_tmp_pdf"

HTTP_TIMEOUT = 60.0   # giây cho mỗi request tới PageIndex
POLL_INTERVAL = 3.0   # giây giữa hai lần kiểm tra trạng thái
POLL_TIMEOUT = 180.0  # giây tối đa cho một lần chờ (upload hoặc retrieval)

# SDK không tài liệu hoá tên field của response retrieval, nên parser chấp nhận
# nhiều tên thay vì hard-code một tên chưa được xác minh với API thật.
NODE_LIST_KEYS = (
    "retrieved_nodes",
    "relevant_contents",
    "retrieved_contents",
    "results",
    "nodes",
    "docs",
)
NODE_TEXT_KEYS = ("text", "content", "markdown", "summary", "description")

# Các field bắt buộc của một entry trong cache.
CACHE_REQUIRED_FIELDS = ("doc_id", "source", "title", "doc_type")

# PDF do fpdf2 tạo chỉ giữ được tiếng Việt khi nhúng font Unicode TTF.
# Đặt PAGEINDEX_PDF_FONT để trỏ tới font khác nếu máy không có các font dưới.
FONT_CANDIDATES = (
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)


def _require_api_key() -> str:
    """Trả về API key, báo lỗi rõ nếu .env chưa điền."""
    if not PAGEINDEX_API_KEY:
        raise RuntimeError(
            "Thiếu PAGEINDEX_API_KEY trong .env; PageIndex chỉ là fallback nên "
            "pipeline vẫn chạy bình thường khi không có key."
        )
    if PageIndexClient is None:
        raise RuntimeError("Chưa cài package pageindex; fallback này đang không khả dụng.")
    return PAGEINDEX_API_KEY


class _TimeoutRequests:
    """Proxy của ``requests`` để mọi request đều có timeout.

    SDK gọi thẳng ``requests.post/get/delete`` mà không truyền ``timeout``;
    requests khi đó chuyển ``None`` xuống socket (``settimeout(None)`` = chờ vô
    hạn), nên ``socket.setdefaulttimeout`` không chặn được. Phải chèn timeout
    ngay tại lời gọi.
    """

    def __init__(self, module, timeout: float):
        self._module = module
        self._timeout = timeout

    def _call(self, verb: str, url: str, kwargs: dict):
        kwargs.setdefault("timeout", self._timeout)
        return getattr(self._module, verb)(url, **kwargs)

    def get(self, url, **kwargs):
        return self._call("get", url, kwargs)

    def post(self, url, **kwargs):
        return self._call("post", url, kwargs)

    def delete(self, url, **kwargs):
        return self._call("delete", url, kwargs)

    def __getattr__(self, name: str):
        # Các thuộc tính khác (requests.Response, exceptions, ...) giữ nguyên.
        return getattr(self._module, name)


@contextmanager
def _request_timeout(seconds: float = HTTP_TIMEOUT):
    """Buộc các request PageIndex có timeout, rồi trả lại module gốc."""
    if pageindex_client is None:
        yield
        return
    original = pageindex_client.requests
    pageindex_client.requests = _TimeoutRequests(original, seconds)
    try:
        yield
    finally:
        pageindex_client.requests = original


def _load_cache() -> dict:
    """Đọc cache doc_id; file hỏng thì coi như chưa upload gì."""
    if not CACHE_PATH.is_file():
        return {}
    try:
        cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return cached if isinstance(cached, dict) else {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _cached_entries() -> list[dict]:
    """Các entry cache đủ field để dựng SearchResult."""
    return [
        entry
        for entry in _load_cache().values()
        if isinstance(entry, dict)
        and all(entry.get(field) for field in CACHE_REQUIRED_FIELDS)
    ]


def _find_unicode_font() -> str | None:
    override = os.getenv("PAGEINDEX_PDF_FONT", "").strip()
    if override and Path(override).is_file():
        return override
    return next((path for path in FONT_CANDIDATES if Path(path).is_file()), None)


def _write_temp_pdf(document: dict) -> Path:
    """Render Markdown thành PDF tạm vì PageIndex nhận PDF."""
    from fpdf import FPDF

    font_path = _find_unicode_font()
    if not font_path:
        raise RuntimeError(
            "Không tìm thấy font Unicode TTF để render PDF; đặt PAGEINDEX_PDF_FONT "
            "trỏ tới một file .ttf hỗ trợ tiếng Việt."
        )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font("Doc", fname=font_path)
    pdf.set_font("Doc", size=11)
    pdf.multi_cell(w=0, h=6, text=document["content"])

    TEMP_PDF_DIR.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        dir=TEMP_PDF_DIR, prefix="pageindex-", suffix=".pdf", delete=False
    )
    handle.close()
    pdf.output(handle.name)
    return Path(handle.name)


def _upload_document(client: PageIndexClient, document: dict) -> str:
    """Upload một document và trả về doc_id."""
    source_path = STANDARDIZED_DIR / document["id"]
    try:
        # Thử Markdown trước; nếu API không nhận thì đổi sang PDF tạm.
        response = client.submit_document(str(source_path))
    except PageIndexAPIError:
        pdf_path = _write_temp_pdf(document)
        try:
            response = client.submit_document(str(pdf_path))
        finally:
            pdf_path.unlink(missing_ok=True)

    doc_id = response.get("doc_id")
    if not doc_id:
        raise RuntimeError(f"PageIndex không trả doc_id cho {document['id']}")
    return doc_id


def _wait_until_ready(client: PageIndexClient, doc_id: str) -> bool:
    """Chờ tài liệu xử lý xong, tối đa POLL_TIMEOUT giây."""
    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        if client.is_retrieval_ready(doc_id):
            return True
        time.sleep(POLL_INTERVAL)
    return False


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    client = PageIndexClient(api_key=_require_api_key())
    cache = _load_cache()
    documents = load_documents()

    if not documents:
        print(f"Không có Markdown nào trong {STANDARDIZED_DIR} để upload.")
        return

    with _request_timeout():
        for document in documents:
            if document["id"] in cache:
                continue

            doc_id = _upload_document(client, document)
            metadata = document["metadata"]
            cache[document["id"]] = {
                "doc_id": doc_id,
                "source": metadata["source"],
                "title": metadata["title"],
                "doc_type": metadata["doc_type"],
                "url": metadata["url"],
            }
            # Lưu ngay sau mỗi tài liệu để lần chạy sau không upload lại.
            _save_cache(cache)
            ready = _wait_until_ready(client, doc_id)
            print(f"{document['id']} -> {doc_id} (retrieval_ready={ready})")


def _extract_nodes(payload: object) -> list:
    """Lấy list node trong response retrieval mà không phụ thuộc tên field."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    for key in NODE_LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list) and value:
            return value

    # Dự phòng: list dict đầu tiên trông giống danh sách node.
    for value in payload.values():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value
    return []


def _node_text(node: object) -> str:
    """Lấy phần text của một node retrieval."""
    if isinstance(node, str):
        return node.strip()
    if not isinstance(node, dict):
        return ""
    for key in NODE_TEXT_KEYS:
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _node_chunk_index(node: object) -> int:
    """chunk_index theo contract; dùng page_index của node nếu có."""
    page_index = node.get("page_index") if isinstance(node, dict) else None
    if isinstance(page_index, int) and page_index >= 0:
        return page_index
    return 0


def _retrieve_nodes(client: PageIndexClient, doc_id: str, query: str) -> list:
    """Submit query rồi chờ lấy kết quả retrieval của một tài liệu."""
    submitted = client.submit_query(doc_id, query)
    retrieval_id = submitted.get("retrieval_id")
    if not retrieval_id:
        return []

    deadline = time.monotonic() + POLL_TIMEOUT
    while time.monotonic() < deadline:
        payload = client.get_retrieval(retrieval_id)
        nodes = _extract_nodes(payload)
        if nodes:
            return nodes
        if str(payload.get("status", "")).lower() in {"failed", "error", "cancelled"}:
            return []
        time.sleep(POLL_INTERVAL)
    return []


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult.

    Không có key, chưa upload tài liệu, hoặc tài liệu lỗi thì trả list rỗng để
    Task 9 giữ kết quả hybrid thay vì crash.
    """
    if top_k <= 0 or not PAGEINDEX_API_KEY or PageIndexClient is None:
        return []

    entries = _cached_entries()
    if not entries:
        return []

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    collected: list[tuple[dict, object, str]] = []

    with _request_timeout():
        for entry in entries:
            try:
                nodes = _retrieve_nodes(client, entry["doc_id"], query)
            except Exception:
                # Một tài liệu lỗi không được làm hỏng cả fallback.
                continue
            for node in nodes:
                text = _node_text(node)
                if text:
                    collected.append((entry, node, text))

    results = []
    for rank, (entry, node, text) in enumerate(collected, 1):
        results.append(
            {
                "id": f"{entry['source']}::pageindex-{rank - 1}",
                "content": text,
                # API không đảm bảo trả score, nên dùng điểm giảm dần theo thứ hạng.
                "score": 1.0 / rank,
                "metadata": {
                    "source": entry["source"],
                    "title": entry["title"],
                    "doc_type": entry["doc_type"],
                    "url": entry.get("url"),
                    "chunk_index": _node_chunk_index(node),
                },
                "retrieval_method": "pageindex",
            }
        )
    return results[:top_k]


if __name__ == "__main__":
    upload_documents()
