"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import hashlib
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from .contracts import Chunk, Document, EmbeddedChunk

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip().lower()
# Nhẹ, đa ngôn ngữ và hoạt động tốt với tiếng Việt. Model này tải một lần về máy.
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
).strip()
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
# CPU là lựa chọn ổn định trên máy Windows không cấu hình CUDA đầy đủ. Có thể
# đổi EMBEDDING_DEVICE=cuda trong .env khi đã xác nhận GPU/PyTorch tương thích.
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu").strip().lower()
# Gemini counts each ``embed_content`` call against a request quota.  Keep this
# configurable so a limited/free project can index the corpus without changing
# source code; retries below respect the delay returned by the provider.
GEMINI_EMBED_BATCH_SIZE = int(os.getenv("GEMINI_EMBED_BATCH_SIZE", "50"))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "6"))
# Không hard-code dimension: SentenceTransformer sẽ trả đúng chiều của model đang dùng.
EMBEDDING_DIM: int | None = None

COLLECTION_PREFIX = "rag_documents"

SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# Provider được hỗ trợ: sentence_transformers | openai | gemini | openrouter.
# Model mặc định tương ứng, dùng khi EMBEDDING_MODEL trong .env vẫn là model local.
PROVIDER_DEFAULT_MODELS = {
    "sentence_transformers": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "openai": "text-embedding-3-small",
    "gemini": "gemini-embedding-001",
    "openrouter": "openai/text-embedding-3-small",
}

# OpenRouter là endpoint OpenAI-compatible; lấy từ OPENROUTER_BASE_URL hoặc
# BASE_URL trong .env, mặc định https://openrouter.ai/api/v1.
OPENROUTER_BASE_URL = (
    os.getenv("OPENROUTER_BASE_URL") or os.getenv("BASE_URL") or ""
).strip() or "https://openrouter.ai/api/v1"

# Task 3 ghi header Markdown: "# {title}" và frontmatter YAML.
_HEADING_PATTERN = re.compile(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)[ \t]*$", re.MULTILINE)
_SOURCE_PATTERN = re.compile(r"^\s*\*\*Source:\*\*\s*(?P<url>\S+)[ \t]*$", re.MULTILINE)
_FM_TITLE_PATTERN = re.compile(r"^title:\s*[\"']?(.*?)[\"']?\s*$", re.MULTILINE)
_FM_URL_PATTERN = re.compile(r"^url:\s*[\"']?(https?://[^\s\"']+)[\"']?\s*$", re.MULTILINE)

# Cache model local để chỉ load một lần cho cả pipeline.
_LOCAL_MODEL = None


def _embedding_model_name(provider: str) -> str:
    """Chọn tên model cho provider, tôn trọng EMBEDDING_MODEL trong .env.

    EMBEDDING_MODEL mặc định là model local; bỏ qua giá trị đó khi nhóm chuyển
    sang provider khác để không gửi sai tên model lên API.
    """
    local_default = PROVIDER_DEFAULT_MODELS["sentence_transformers"]
    if EMBEDDING_MODEL and (
        provider == "sentence_transformers" or EMBEDDING_MODEL != local_default
    ):
        return EMBEDDING_MODEL
    # Trả chuỗi rỗng cho provider lạ để embed_texts báo lỗi rõ ràng thay vì KeyError.
    return PROVIDER_DEFAULT_MODELS.get(provider, "")


def _api_key(variable: str) -> str:
    """Đọc API key từ môi trường và báo lỗi rõ ràng nếu còn thiếu."""
    key = os.getenv(variable, "").strip()
    if not key:
        raise RuntimeError(
            f"Thiếu {variable}; điền key vào .env trước khi embed."
        )
    return key


def _local_embedding_model(model_name: str):
    """Load SentenceTransformer một lần rồi tái sử dụng cho mọi lần embed."""
    global _LOCAL_MODEL
    if _LOCAL_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _LOCAL_MODEL = SentenceTransformer(model_name, device=EMBEDDING_DEVICE)
    return _LOCAL_MODEL


def embedding_dimension() -> int:
    """Trả về chiều vector thực tế của local model, không phụ thuộc hằng số."""
    global EMBEDDING_DIM
    if EMBEDDING_PROVIDER != "sentence_transformers":
        raise RuntimeError("embedding_dimension() chỉ dùng cho sentence_transformers")
    if EMBEDDING_DIM is None:
        model = _local_embedding_model(_embedding_model_name(EMBEDDING_PROVIDER))
        # sentence-transformers 5 renamed this method; retain compatibility
        # with older installed releases.
        get_dimension = (
            model.get_embedding_dimension
            if hasattr(model, "get_embedding_dimension")
            else model.get_sentence_embedding_dimension
        )
        EMBEDDING_DIM = int(get_dimension())
    return EMBEDDING_DIM


def _collection_name() -> str:
    """Tách index theo model để vector khác chiều không thể lẫn vào nhau."""
    model = _embedding_model_name(EMBEDDING_PROVIDER)
    safe_model = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")[-48:]
    fingerprint = hashlib.sha1(model.encode("utf-8")).hexdigest()[:8]
    return f"{COLLECTION_PREFIX}-{safe_model}-{fingerprint}"


def _openai_compatible_embeddings(
    texts: list[str],
    *,
    model: str,
    api_key: str,
    base_url: str | None = None,
) -> list[list[float]]:
    """Embed qua endpoint OpenAI-compatible và giữ đúng thứ tự input."""
    from openai import BadRequestError, RateLimitError, APIError, OpenAI

    # Do not let an unavailable OpenAI-compatible provider freeze the UI/index
    # indefinitely. Retrying is handled explicitly below so errors remain clear.
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=45.0, max_retries=0)
    vectors: list[list[float]] = []
    total = len(texts)

    for start in range(0, total, EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        current_end = min(start + EMBED_BATCH_SIZE, total)
        if total > EMBED_BATCH_SIZE:
            print(f"Embedding batch {start + 1}-{current_end}/{total}...")

        success = False
        for attempt in range(5):
            try:
                response = client.embeddings.create(model=model, input=batch)
                sorted_items = sorted(response.data, key=lambda x: getattr(x, "index", 0))
                vectors.extend(item.embedding for item in sorted_items)
                success = True
                break
            except BadRequestError:
                # Vài endpoint chỉ nhận một text mỗi request
                break
            except (RateLimitError, APIError, Exception) as exc:
                if attempt == 4:
                    raise
                wait_time = 2 ** (attempt + 1)
                print(f"Lỗi kết nối embedding ({exc}), thử lại sau {wait_time}s...")
                time.sleep(wait_time)

        if not success:
            for text in batch:
                for attempt in range(5):
                    try:
                        response = client.embeddings.create(model=model, input=text)
                        vectors.extend(item.embedding for item in response.data)
                        break
                    except (RateLimitError, APIError, Exception) as exc:
                        if attempt == 4:
                            raise
                        wait_time = 2 ** (attempt + 1)
                        print(f"Lỗi kết nối embedding ({exc}), thử lại sau {wait_time}s...")
                        time.sleep(wait_time)

    return [[float(value) for value in vector] for vector in vectors]


def embed_texts(texts: list[str], input_type: str = "passage") -> list[list[float]]:
    """Embed texts bằng provider trong .env; Task 4 và Task 5 dùng chung hàm này."""
    if not texts:
        return []

    model_name = _embedding_model_name(EMBEDDING_PROVIDER)

    if EMBEDDING_PROVIDER == "sentence_transformers":
        # E5 cần prefix query/passage để retrieval đa ngôn ngữ chính xác hơn.
        prepared_texts = texts
        if "e5" in model_name.lower():
            prefix = "query: " if input_type == "query" else "passage: "
            prepared_texts = [prefix + text for text in texts]
        # normalize_embeddings=True để cosine distance của Chroma ổn định.
        vectors = _local_embedding_model(model_name).encode(
            prepared_texts,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        result = [[float(value) for value in vector] for vector in vectors]
        if result:
            global EMBEDDING_DIM
            EMBEDDING_DIM = len(result[0])
        return result

    if EMBEDDING_PROVIDER == "openai":
        return _openai_compatible_embeddings(
            texts,
            model=model_name,
            api_key=_api_key("OPENAI_API_KEY"),
        )

    if EMBEDDING_PROVIDER == "openrouter":
        return _openai_compatible_embeddings(
            texts,
            model=model_name,
            api_key=_api_key("OPENROUTER_API_KEY"),
            base_url=OPENROUTER_BASE_URL,
        )

    if EMBEDDING_PROVIDER == "gemini":
        from google import genai

        client = genai.Client(api_key=_api_key("GEMINI_API_KEY"))
        vectors: list[list[float]] = []
        for start in range(0, len(texts), GEMINI_EMBED_BATCH_SIZE):
            batch = texts[start : start + GEMINI_EMBED_BATCH_SIZE]
            for attempt in range(GEMINI_MAX_RETRIES):
                try:
                    response = client.models.embed_content(
                        model=model_name, contents=batch
                    )
                    break
                except Exception as exc:
                    if attempt == GEMINI_MAX_RETRIES - 1:
                        raise RuntimeError(
                            "Gemini embedding không hoàn tất sau nhiều lần thử. "
                            "Kiểm tra quota/billing hoặc chạy lại sau ít phút."
                        ) from exc
                    # Gemini includes a retry delay in 429 responses but does
                    # not expose it consistently across SDK releases. Exponential
                    # backoff is predictable and prevents a tight retry loop.
                    wait_time = min(60, 10 * (attempt + 1))
                    print(
                        f"Gemini đang giới hạn embedding; thử lại batch "
                        f"{start + 1}-{start + len(batch)}/{len(texts)} sau "
                        f"{wait_time}s..."
                    )
                    time.sleep(wait_time)
            vectors.extend(
                [float(val) for val in embedding.values]
                for embedding in response.embeddings
            )
        return vectors

    supported = " | ".join(sorted(PROVIDER_DEFAULT_MODELS))
    raise ValueError(
        f"EMBEDDING_PROVIDER không được hỗ trợ: {EMBEDDING_PROVIDER!r} "
        f"(hợp lệ: {supported})"
    )


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=_collection_name(),
        metadata={
            "hnsw:space": "cosine",
            "embedding_provider": EMBEDDING_PROVIDER,
            "embedding_model": _embedding_model_name(EMBEDDING_PROVIDER),
        },
    )


def _document_title(content: str, fallback: str) -> str:
    """Lấy title từ frontmatter hoặc heading đầu tiên của Markdown, fallback về tên file."""
    fm_match = _FM_TITLE_PATTERN.search(content)
    if fm_match and fm_match.group(1).strip():
        return fm_match.group(1).strip()
    match = _HEADING_PATTERN.search(content)
    return match.group("title").strip() if match else fallback


def _document_url(content: str) -> str | None:
    """Lấy URL từ frontmatter hoặc dòng '**Source:** ...' mà Task 3 ghi ở đầu file."""
    fm_match = _FM_URL_PATTERN.search(content)
    if fm_match and fm_match.group(1).strip():
        return fm_match.group(1).strip()
    match = _SOURCE_PATTERN.search(content)
    return match.group("url").strip() if match else None


def load_documents() -> list[Document]:
    """Đọc Markdown và trả về danh sách Document."""
    if not STANDARDIZED_DIR.is_dir():
        raise FileNotFoundError(
            f"Chưa có dữ liệu chuẩn hoá: {STANDARDIZED_DIR}"
        )

    documents: list[Document] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        # id = đường dẫn tương đối nên ổn định và không trùng giữa legal/news.
        relative = path.relative_to(STANDARDIZED_DIR)
        documents.append(
            {
                "id": relative.as_posix(),
                "content": content,
                "metadata": {
                    "source": path.name,
                    "title": _document_title(content, path.stem),
                    "doc_type": "legal" if "legal" in relative.parts else "news",
                    "url": _document_url(content),
                },
            }
        )
    return documents



def chunk_documents(documents: list[Document]) -> list[Chunk]:
    """Chia Document thành chunks có id và chunk_index."""
    if CHUNKING_METHOD != "recursive":
        raise ValueError(f"CHUNKING_METHOD không được hỗ trợ: {CHUNKING_METHOD!r}")

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
    )

    chunks: list[Chunk] = []
    for document in documents:
        # chunk_index đếm theo thứ tự chunk thực sự được giữ lại (bỏ chunk rỗng).
        chunk_index = 0
        for text in splitter.split_text(document["content"]):
            text = text.strip()
            if not text:
                continue
            chunks.append(
                {
                    "id": f"{document['id']}::chunk-{chunk_index}",
                    "content": text,
                    "metadata": {**document["metadata"], "chunk_index": chunk_index},
                }
            )
            chunk_index += 1
    return chunks


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedChunk]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []

    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Số vector trả về không khớp số chunk")

    # Tạo dict mới thay vì sửa tại chỗ để không làm thay đổi input.
    return [
        {**chunk, "embedding": vector}
        for chunk, vector in zip(chunks, vectors)
    ]


def _chroma_metadata(metadata: dict) -> dict:
    """Chuẩn hoá metadata cho ChromaDB.

    Chroma chỉ chấp nhận str/int/float/bool cho giá trị metadata khi add/upsert
    (None chỉ hợp lệ ở đường update để xoá key). Vì vậy url=None được ghi thành
    chuỗi rỗng; contract ``url: str | None`` vẫn được thoả khi đọc lại.
    """
    return {key: ("" if value is None else value) for key, value in metadata.items()}


def index_to_vectorstore(chunks: list[EmbeddedChunk]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        return

    # id ổn định + upsert nên chạy lại pipeline không tạo dữ liệu trùng.
    collection = get_collection()
    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[start : start + EMBED_BATCH_SIZE]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in batch],
        )


def _chunks_needing_embedding(chunks: list[Chunk]) -> list[Chunk]:
    """Bỏ qua chunk đã index với đúng nội dung để chạy lại có thể resume."""
    if not chunks:
        return []
    collection = get_collection()
    pending: list[Chunk] = []
    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[start : start + EMBED_BATCH_SIZE]
        existing = collection.get(
            ids=[chunk["id"] for chunk in batch], include=["documents"]
        )
        cached = dict(zip(existing["ids"], existing["documents"]))
        pending.extend(chunk for chunk in batch if cached.get(chunk["id"]) != chunk["content"])
    return pending


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    pending_chunks = _chunks_needing_embedding(chunks)
    if pending_chunks and EMBEDDING_PROVIDER == "sentence_transformers":
        print(f"Using local model: {_embedding_model_name(EMBEDDING_PROVIDER)} ({embedding_dimension()} dimensions)")
    for start in range(0, len(pending_chunks), EMBED_BATCH_SIZE):
        batch = pending_chunks[start : start + EMBED_BATCH_SIZE]
        index_to_vectorstore(embed_chunks(batch))
        print(f"Indexed {min(start + len(batch), len(pending_chunks))}/{len(pending_chunks)} new or changed chunks")
    print(f"Index ready: {len(chunks)} chunks ({len(pending_chunks)} embedded, {len(chunks) - len(pending_chunks)} reused)")


if __name__ == "__main__":
    run_pipeline()
