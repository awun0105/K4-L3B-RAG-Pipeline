"""
Query Expansion & Domain-Specific Term Normalization module for UniGuide HCMUS.

Cung cấp:
1. Dictionary-based Domain Expansion: Chuẩn hóa và mở rộng các từ viết tắt,
   thuật ngữ chuyên môn đặc thù tại Trường ĐH Khoa học Tự nhiên & ĐHQG-HCM
   (ĐRL, HBKK, KTX, BHYT, CTĐT, GDQP-AN, ĐKHP, buộc thôi học, bảo lưu,...).
2. HyDE (Hypothetical Document Embeddings): Dùng LLM sinh một đoạn trích
   giả thuyết ngắn hỗ trợ câu hỏi mờ ngữ cảnh trước khi truy vấn vector.
"""

from __future__ import annotations

import re
from typing import Optional

# Bảng từ điển thuật ngữ và từ viết tắt đặc thù tại HCMUS & ĐHQG-HCM
DOMAIN_ACRONYMS: dict[str, str] = {
    r"\bđrl\b": "điểm rèn luyện",
    r"\bdrl\b": "điểm rèn luyện",
    r"\bhbkk\b": "học bổng khuyến khích học tập",
    r"\bhb\b": "học bổng",
    r"\bktx\b": "ký túc xá đại học quốc gia",
    r"\bbhyt\b": "bảo hiểm y tế",
    r"\bctđt\b": "chương trình đào tạo",
    r"\bctdt\b": "chương trình đào tạo",
    r"\bđkhp\b": "đăng ký học phần",
    r"\bdkhp\b": "đăng ký học phần",
    r"\bgdqp\b": "giáo dục quốc phòng an ninh",
    r"\bgdqp-an\b": "giáo dục quốc phòng an ninh",
    r"\bhsv\b": "hội sinh viên",
    r"\bđtn\b": "đoàn thanh niên",
    r"\bcnsh\b": "công nghệ sinh học",
    r"\bcntt\b": "công nghệ thông tin",
    r"\bkhmt\b": "khoa học máy tính",
    r"\bkhtn\b": "khoa học tự nhiên",
    r"\bhcmus\b": "trường đại học khoa học tự nhiên",
    r"\bđhqg\b": "đại học quốc gia tp hcm",
    r"\bdhqg\b": "đại học quốc gia tp hcm",
}

# Bổ sung từ khóa mở rộng theo chủ đề (Semantic Topical Expansion)
TOPICAL_KEYWORDS: dict[str, list[str]] = {
    r"thang điểm.*rèn luyện": ["được đánh giá bằng thang điểm 100", "thang điểm 100"],
    r"kết quả rèn luyện.*phân loại": ["phân loại kết quả rèn luyện", "loại xuất sắc", "tốt", "khá", "trung bình", "yếu", "kém"],
    r"ý thức tham gia học tập": ["từ 0 – 20 điểm", "Điều 4", "thái độ trong học tập"],
    r"ý thức chấp hành nội quy": ["Điều 5", "từ 0 – 25 điểm", "chấp hành nội quy quy chế"],
    r"buộc thôi học": ["bị buộc thôi học", "Điều 16", "cảnh báo học tập", "xử lý kết quả học tập"],
    r"cảnh báo học tập": ["buộc thôi học", "điểm trung bình tích lũy", "Điều 16"],
    r"ưu tiên.*ký túc xá": ["đối tượng ưu tiên", "chính sách ưu tiên nội trú", "KTX ĐHQG-HCM"],
    r"học bổng khuyến khích": ["tiêu chuẩn học bổng", "điểm rèn luyện tốt", "điểm trung bình học tập"],
    r"tốt nghiệp": ["điều kiện xét tốt nghiệp", "chuẩn đầu ra", "chứng chỉ ngoại ngữ tin học"],
    r"bảo lưu": ["nghỉ học tạm thời", "tạm ngừng học tập"],
    r"hạ bậc rèn luyện": ["khiển trách", "cảnh cáo", "kỷ luật sinh viên", "Điều 11"],
    r"giáo dục quốc phòng": ["không tính vào điểm trung bình tích lũy", "chứng chỉ GDQP-AN", "học phần điều kiện"],
}


def expand_query(query: str, use_synonyms: bool = True) -> str:
    """Mở rộng query với các từ viết tắt và từ khóa đồng nghĩa chuyên ngành HCMUS.
    
    Giữ nguyên câu hỏi gốc và bổ sung các thuật ngữ chuẩn hóa vào cuối câu
    để cả BM25 và Dense Search đều khớp chính xác hơn.
    """
    cleaned = query.strip()
    if not cleaned or not use_synonyms:
        return cleaned

    query_lower = cleaned.lower()
    additions: list[str] = []

    # 1. Phát hiện và bổ sung từ viết tắt
    for pattern, expansion in DOMAIN_ACRONYMS.items():
        if re.search(pattern, query_lower):
            if expansion not in query_lower and expansion not in additions:
                additions.append(expansion)

    # 2. Phát hiện và bổ sung từ khóa chuyên đề
    for pattern, terms in TOPICAL_KEYWORDS.items():
        if re.search(pattern, query_lower):
            for term in terms:
                if term.lower() not in query_lower and term not in additions:
                    additions.append(term)

    if additions:
        return f"{cleaned} {' '.join(additions)}"
    return cleaned


def generate_hypothetical_document(query: str) -> Optional[str]:
    """Sinh văn bản giả định (HyDE) bằng LLM để cầu nối khoảng cách từ vựng."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        from .task10_generation import call_llm

        system_prompt = (
            "Bạn là trợ lý quy chế sinh viên Trường ĐH Khoa học Tự nhiên, ĐHQG-HCM (HCMUS). "
            "Hãy viết 1 đoạn văn ngắn (2 câu, tối đa 50 từ) nêu câu trả lời giả định hoặc các điều khoản "
            "liên quan cho câu hỏi của sinh viên. Trả lời trực tiếp, không giải thích thêm."
        )
        user_msg = f"Câu hỏi: {query}"
        hypo = call_llm(system_prompt, user_msg)
        if hypo and len(hypo.strip()) > 10:
            return hypo.strip()
    except Exception:
        pass
    return None


def expand_query_hyde(query: str) -> str:
    """Kết hợp query expansion và HyDE để tạo chuỗi truy vấn giàu ngữ nghĩa nhất."""
    base_expanded = expand_query(query)
    hypo = generate_hypothetical_document(query)
    if hypo:
        return f"{base_expanded} {hypo}"
    return base_expanded
