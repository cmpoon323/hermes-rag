"""Retrieval + answer: embed query → top-k chunks → LLM with context."""
from .config import TOP_K
from .minimax import get_client as get_minimax
from . import vector_store


SYSTEM_PROMPT = """你係一個精準嘅文件問答助手。請根據以下 context 回答用戶問題。

規則：
1. 只用 context 裏面嘅資料回答，唔好作
2. 如果 context 冇相關資料，答「文件入面冇呢個資料」
3. 引用資料時講明邊份文件
4. 用繁體中文回答

Context:
{context}
"""


async def answer(question: str, top_k: int = TOP_K) -> dict:
    """Embed question, retrieve, ask LLM."""
    minimax = get_minimax()
    q_vec = await minimax.embed_query(question)

    hits = vector_store.search(q_vec, top_k=top_k)

    if not hits:
        return {
            "answer": "文件庫入面冇相關資料。請先 upload 文件。",
            "sources": [],
        }

    context_parts = []
    for i, h in enumerate(hits, 1):
        src = h.get("source", "unknown")
        text = h.get("text", "")
        score = h.get("_score", 0)
        context_parts.append(f"[{i}] (來源: {src}, 相關度: {score:.2f})\n{text}")

    context = "\n\n".join(context_parts)

    answer_text = await minimax.chat([
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
        {"role": "user", "content": question},
    ])

    return {
        "answer": answer_text,
        "sources": [
            {
                "source": h.get("source"),
                "chunk_index": h.get("chunk_index"),
                "score": h.get("_score"),
                "preview": h.get("text", "")[:200],
            }
            for h in hits
        ],
    }
