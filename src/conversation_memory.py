"""
Conversation Memory & Contextual Query Reformulation module for UniGuide HCMUS.

Giải quyết vấn đề câu hỏi nối tiếp (follow-up questions) trong giao tiếp nhiều lượt:
Người dùng thường hỏi vắn tắt dựa trên ngữ cảnh lượt trước:
- Lượt 1: "Điều kiện xét học bổng khuyến khích học tập là gì?"
- Lượt 2: "Thế còn loại Xuất sắc thì sao?"
- Lượt 3: "Thời hạn nộp hồ sơ khi nào?"

Module này tự động tái cấu trúc câu hỏi nối tiếp thành Standalone Query hoàn chỉnh
trước khi đưa vào Retrieval Pipeline.
"""

from __future__ import annotations

import re
from typing import Any


def format_history_for_prompt(chat_history: list[dict[str, Any]], max_turns: int = 3) -> str:
    """Định dạng các lượt đối thoại gần nhất thành văn bản cho prompt."""
    if not chat_history:
        return ""

    lines = []
    # Lấy tối đa max_turns lượt gần nhất
    recent = chat_history[-(max_turns * 2):]
    for msg in recent:
        role = "Sinh viên" if msg.get("role") == "user" else "UniGuide"
        content = msg.get("content") or msg.get("answer") or ""
        # Rút gọn câu trả lời nếu quá dài để tiết kiệm context
        if len(content) > 250:
            content = content[:240].rstrip() + "…"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def reformulate_query(query: str, chat_history: list[dict[str, Any]] | None = None) -> str:
    """Tái cấu trúc câu hỏi người dùng dựa trên lịch sử trò chuyện.
    
    Nếu có lịch sử và câu hỏi mang tính nối tiếp (phụ thuộc ngữ cảnh),
    viết lại thành câu hỏi độc lập (standalone query).
    Nếu câu hỏi đã độc lập hoặc không có lịch sử, trả về nguyên bản.
    """
    clean_query = query.strip()
    if not clean_query or not chat_history:
        return clean_query

    # Kiểm tra nhanh các tín hiệu câu hỏi phụ thuộc (pronouns / demonstratives)
    follow_up_signals = [
        r"^(thế\s+)?còn\b",
        r"^vậy\b",
        r"\bnhư\s+trên\b",
        r"\bnó\b",
        r"\bở\s+đó\b",
        r"\bthì\s+sao\b",
        r"\bbao\s+nhiêu\s+tiền\b",
        r"\bkhi\s+nào\b",
        r"\bở\s+đâu\b",
        r"\bđược\s+không\b",
        r"\bmức\s+nào\b",
        r"\bloại\s+nào\b",
    ]
    query_lower = clean_query.lower()
    is_likely_followup = any(re.search(sig, query_lower) for sig in follow_up_signals) or len(clean_query.split()) <= 4

    if not is_likely_followup:
        return clean_query

    history_text = format_history_for_prompt(chat_history)
    if not history_text:
        return clean_query

    # Gọi LLM để viết lại câu hỏi độc lập
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from .task10_generation import call_llm

        system_prompt = (
            "Bạn là trợ lý hỗ trợ tra cứu quy định sinh viên Trường ĐH Khoa học Tự nhiên, ĐHQG-HCM (HCMUS). "
            "Nhiệm vụ của bạn là dựa vào lịch sử trao đổi và câu hỏi tiếp theo, "
            "hãy viết lại câu hỏi tiếp theo thành một câu hỏi độc lập duy nhất (standalone question) "
            "chứa đầy đủ chủ ngữ, vị ngữ và thực thể cụ thể (ví dụ: học bổng khuyến khích học tập, điểm rèn luyện, ký túc xá, tốt nghiệp). "
            "KHÔNG trả lời câu hỏi, KHÔNG thêm lời chào hay giải thích, chỉ xuất ra duy nhất câu hỏi đã viết lại."
        )
        user_msg = f"[LỊCH SỬ TRAO ĐỔI]:\n{history_text}\n\nCâu hỏi tiếp theo: {clean_query}"
        reformulated = call_llm(system_prompt, user_msg)
        if reformulated and len(reformulated.strip()) >= 5:
            res = reformulated.strip().strip('"').strip("'")
            # Loại bỏ các tiền tố không mong muốn nếu có
            res = re.sub(r"^(câu hỏi độc lập:\s*|standalone question:\s*)", "", res, flags=re.IGNORECASE).strip()
            return res
    except Exception as error:
        print(f"Conversation reformulation error: {error}")

    return clean_query

