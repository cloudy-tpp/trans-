import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io
import time

# --- 1. CẤU HÌNH BỘ NHỚ ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = ""

st.set_page_config(page_title="AI Translator Pro (Fix 404)", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Cấu hình hệ thống")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    # Danh sách model rút gọn, ổn định nhất
    model_options = [
        "gemini-1.5-flash", 
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-2.0-flash-exp"
    ]
    selected_model = st.selectbox("Chọn Model:", model_options)
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])

    st.markdown("---")
    st.subheader("📜 Lịch sử")
    for i, item in enumerate(st.session_state.history):
        col_h1, col_h2 = st.columns([4, 1])
        if col_h1.button(f"📄 {item['name'][:10]}...", key=f"v_{i}"):
            st.session_state.current_res = item['content']
        if col_h2.button("🗑️", key=f"d_{i}"):
            st.session_state.history.pop(i)
            st.rerun()

# --- GIAO DIỆN CHÍNH ---
st.title("🌐 AI Translator (Phiên bản chống lỗi 404)")

if api_key:
    genai.configure(api_key=api_key)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Hình thức:", ["Dán văn bản", "Tải file PDF"])
        input_txt, input_name = "", ""

        if option == "Dán văn bản":
            raw = st.text_area("Nội dung:", height=200)
            if st.button("Dịch ngay 🚀"):
                input_txt, input_name = raw, "Văn bản dán"
        else:
            file = st.file_uploader("Chọn PDF (Lên đến 200MB)", type=["pdf"])
            if file:
                reader = PdfReader(file)
                total = len(reader.pages)
                st.success(f"Tài liệu: {total} trang")
                c1, c2 = st.columns(2)
                start = c1.number_input("Từ trang:", 1, total, 1)
                end = c2.number_input("Đến trang:", 1, total, min(start+4, total))
                
                if st.button("Dịch PDF 🚀"):
                    with st.spinner("Đang trích xuất chữ..."):
                        extracted = ""
                        for j in range(start-1, end):
                            extracted += reader.pages[j].extract_text() + "\n"
                        input_txt, input_name = extracted, f"{file.name} (P{start}-{end})"

    # --- XỬ LÝ DỊCH (VỚI CƠ CHẾ THỬ LẠI KHI LỖI 404) ---
    if input_txt:
        try:
            with st.spinner("AI đang dịch..."):
                # Thử các định dạng tên model khác nhau để tránh lỗi 404
                success = False
                error_log = ""
                
                # Danh sách các kiểu gọi tên model mà Google chấp nhận
                test_names = [selected_model, f"models/{selected_model}"]
                
                for name in test_names:
                    try:
                        model = genai.GenerativeModel(model_name=name)
                        prompt = f"Dịch sang {target_lang}. Chỉ trả về bản dịch:\n\n{input_txt}"
                        response = model.generate_content(prompt)
                        st.session_state.current_res = response.text
                        st.session_state.history.append({"name": input_name, "content": response.text})
                        success = True
                        break # Thoát vòng lặp nếu thành công
                    except Exception as sub_e:
                        error_log = str(sub_e)
                        continue
                
                if success:
                    st.balloons()
                else:
                    if "429" in error_log:
                        st.error("⚠️ Lỗi 429: Hết hạn mức! Hãy đợi 60 giây.")
                    else:
                        st.error(f"Lỗi AI: {error_log}")
                        st.info("Mẹo: Hãy thử đổi API Key mới hoặc chọn Model 'gemini-1.5-pro'.")

        except Exception as e:
            st.error(f"Lỗi hệ thống: {e}")

    with col2:
        st.subheader("📝 Kết quả")
        if st.session_state.current_res:
            st.text_area("Bản dịch:", st.session_state.current_res, height=450)
            col_d1, col_d2 = st.columns(2)
            
            doc = Document()
            doc.add_paragraph(st.session_state.current_res)
            bio = io.BytesIO()
            doc.save(bio)
            col_d1.download_button("Tải file .docx", bio.getvalue(), "translation.docx")
            col_d2.download_button("Tải file .txt", st.session_state.current_res, "translation.txt")
else:
    st.info("Hãy nhập API Key ở bên trái để bắt đầu.")
