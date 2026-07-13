"""Streamlit UI: upload + chat + document list."""
import os
import streamlit as st
import httpx

# Ponytail: prefer env API_URL (Zeabur), then st.secrets, then localhost
API_URL = os.getenv("API_URL") or st.secrets.get("API_URL", "http://localhost:8000") if hasattr(st, "secrets") else os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Hermes RAG", page_icon="📚", layout="wide")
st.title("📚 Hermes RAG — 文件問答")

# === Sidebar: upload + document list ===
with st.sidebar:
    st.header("📤 Upload 文件")
    uploaded = st.file_uploader(
        "PDF 或 Word",
        type=["pdf", "docx", "doc"],
        accept_multiple_files=False,
    )
    if uploaded and st.button("Ingest"):
        with st.spinner("處理中..."):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
            r = httpx.post(f"{API_URL}/upload", files=files, timeout=300)
            if r.status_code == 200:
                data = r.json()
                st.success(f"✓ {data['source']}: {data['chunks']} chunks")
            else:
                st.error(f"✗ {r.text}")

    st.divider()
    st.header("📂 文件庫")
    if st.button("Refresh"):
        st.session_state.refresh_docs = True
    try:
        r = httpx.get(f"{API_URL}/documents", timeout=10)
        if r.status_code == 200:
            for doc in r.json().get("documents", []):
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{doc['source']}** ({doc['chunks']} chunks)")
                if col2.button("🗑", key=doc["source"]):
                    httpx.delete(f"{API_URL}/documents/{doc['source']}")
                    st.rerun()
    except Exception as e:
        st.error(f"Backend 連唔到: {e}")

# === Main: chat ===
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander(f"📎 {len(msg['sources'])} 個來源"):
                for s in msg["sources"]:
                    st.write(f"**{s['source']}** (chunk {s['chunk_index']}, score {s['score']:.2f})")
                    st.caption(s["preview"])

if question := st.chat_input("問條問題..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("諗緊..."):
            r = httpx.post(
                f"{API_URL}/ask",
                json={"question": question},
                timeout=60,
            )
            if r.status_code == 200:
                data = r.json()
                st.write(data["answer"])
                if data.get("sources"):
                    with st.expander(f"📎 {len(data['sources'])} 個來源"):
                        for s in data["sources"]:
                            st.write(f"**{s['source']}** (chunk {s['chunk_index']}, score {s['score']:.2f})")
                            st.caption(s["preview"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data["answer"],
                    "sources": data.get("sources", []),
                })
            else:
                st.error(f"Error: {r.text}")
