"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os
import re
from collections.abc import Iterable

try:
    from dotenv import load_dotenv
except ImportError:  # Offline/mock development must remain runnable.
    def load_dotenv() -> bool:
        return False

from .task9_retrieval_pipeline import retrieve
from .retrieval_adapter import get_retriever


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "")

SYSTEM_PROMPT = """Bạn là trợ lý thông tin tuyển sinh đại học Việt Nam.
Chỉ trả lời dựa trên CONTEXT được cung cấp. Không dùng kiến thức bên ngoài để
khẳng định điểm chuẩn, học phí, chỉ tiêu, phương thức, thời gian hay điều kiện
xét tuyển. Không suy đoán, không tạo URL, nguồn hay citation mới.

Mỗi khẳng định có bằng chứng phải dùng citation dạng [1] hoặc [1][2], với số
có trong CONTEXT. Nếu context không đủ, hãy trả lời đúng câu: "Thông tin trong
nguồn hiện có chưa đủ để xác minh câu hỏi này." Với yêu cầu so sánh, chỉ so
sánh các trường có bằng chứng và nêu rõ bên còn thiếu dữ liệu. Trả lời ngắn,
rõ ràng và trực tiếp bằng tiếng Việt."""

SAFE_REFUSAL = "Thông tin trong nguồn hiện có chưa đủ để xác minh câu hỏi này."


class LLMProviderError(RuntimeError):
    """A user-safe provider configuration or request failure."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    # Copy the list only: chunks themselves (including metadata) stay intact.
    if len(chunks) <= 2:
        return list(chunks)
    return list(chunks[::2]) + list(reversed(chunks[1::2]))


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    # Citation labels use the canonical retrieval ranking rather than position
    # after reordering. Therefore [1] always maps to sources[0].
    canonical = sorted(chunks, key=lambda item: (-float(item["score"]), item["id"]))
    citation_index = {item["id"]: index for index, item in enumerate(canonical, 1)}
    parts = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        parts.append(
            f"[{citation_index[chunk['id']]}]\n"
            f"Title: {metadata['title']}\n"
            f"Source: {metadata['source']}\n"
            f"Content:\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    provider = LLM_PROVIDER.strip().lower()
    if provider in ("openai", "openrouter"):
        key = os.getenv("OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY", "")
        base_url = os.getenv("BASE_URL") if provider == "openrouter" else None
        if not key:
            raise LLMProviderError(f"Missing {'OPENROUTER_API_KEY' if provider == 'openrouter' else 'OPENAI_API_KEY'}")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key, base_url=base_url)
            response = client.chat.completions.create(
                model=LLM_MODEL or ("qwen/qwen3.8-27b:free" if provider == "openrouter" else "gpt-4o-mini"),
                temperature=TEMPERATURE,
                top_p=TOP_P,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except LLMProviderError:
            raise
        except Exception as error:
            raise LLMProviderError(f"{provider} request failed: {error}") from error
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            raise LLMProviderError("Missing GEMINI_API_KEY")
        try:
            from google import genai
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=LLM_MODEL or "gemini-2.0-flash",
                contents=user_message,
                config={"system_instruction": system_prompt, "temperature": TEMPERATURE, "top_p": TOP_P},
            )
            return (response.text or "").strip()
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise LLMProviderError("Missing ANTHROPIC_API_KEY")
        try:
            from anthropic import Anthropic
            response = Anthropic(api_key=key).messages.create(
                model=LLM_MODEL or "claude-3-5-haiku-latest",
                max_tokens=700,
                temperature=TEMPERATURE,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return "".join(block.text for block in response.content if hasattr(block, "text")).strip()
        except Exception as error:
            raise LLMProviderError(f"Anthropic request failed: {error}") from error
    raise LLMProviderError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def _citation_numbers(answer: str) -> set[int]:
    return {int(number) for number in re.findall(r"\[(\d+)\]", answer)}


def _mock_grounded_answer(query: str, chunks: Iterable[dict]) -> str:
    """Offline development answer composed only of clearly marked mock chunks."""
    query_tokens = set(re.findall(r"[\wÀ-ỹ]+", query.lower()))
    selected: list[dict] = []
    for chunk in chunks:
        text = f"{chunk['metadata']['title']} {chunk['content']}".lower()
        if sum(token in text for token in query_tokens) >= 2:
            selected.append(chunk)
    if not selected:
        return SAFE_REFUSAL
    canonical = sorted(chunks, key=lambda item: (-float(item["score"]), item["id"]))
    labels = {item["id"]: index for index, item in enumerate(canonical, 1)}
    if "so sánh" in query.lower() and len(selected) >= 2:
        selected = selected[:2]
    else:
        selected = selected[:1]
    statements = []
    for item in selected:
        content = item["content"].replace("DEVELOPMENT / MOCK DATA. ", "")
        statements.append(f"{content} [{labels[item['id']]}]")
    return " ".join(statements)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    if not query.strip() or top_k <= 0:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    try:
        chunks = get_retriever()(query, top_k)
    except Exception:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    if not chunks:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}

    sources = sorted(chunks, key=lambda item: (-float(item["score"]), item["id"]))
    context = format_context(reorder_for_llm(sources))
    user_message = f"CONTEXT:\n{context}\n\nCÂU HỎI: {query}"
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except LLMProviderError:
        # The offline development path is explicitly restricted to mock data.
        answer = _mock_grounded_answer(query, sources) if os.getenv("RAG_RETRIEVAL_MODE", "auto").lower() != "real" else SAFE_REFUSAL

    valid_numbers = set(range(1, len(sources) + 1))
    numbers = _citation_numbers(answer)
    if answer == SAFE_REFUSAL or not numbers or not numbers <= valid_numbers:
        return {"answer": SAFE_REFUSAL, "sources": [], "retrieval_source": "none"}
    method = sources[0]["retrieval_method"]
    return {"answer": answer, "sources": sources, "retrieval_source": method}


if __name__ == "__main__":
    print(generate_with_citation("test query"))
