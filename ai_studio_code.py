import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- 1. KHỞI TẠO BỘ NHỚ APP (SESSION STATE) ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = ""

st.set_page_config(page_title="Siêu Ứng Dụng Dịch Thuật AI", layout="wide")

# --- 2. GIAO DIỆN THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cấu hình hệ thống")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    model_name = st.selectbox("Chọn Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])
    
    st.markdown("---")
    st.subheader("📜 Lịch sử dịch thuật")
    if not st.session_state.history:
        st.write("Chưa có bản lưu nào.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Bản dịch {len(st.session_state.history)-i}: {item['name']}"):
                st.write(f"**Nguồn:** {item['type']}")
                st.write(item['content'][:200] + "...")
                # Nút cho phép xem lại bản dịch cũ
                if st.button(f"Xem lại bản {len(st.session_state.history)-i}", key=f"rev_{i}"):
                    st.session_state.current_res = item['content']

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🌐 AI Translator Multi-Tool")
st.markdown("Hỗ trợ: Văn bản thuần túy, PDF nhỏ và PDF khổng lồ (160MB+).")

if api_key:
    genai.configure(api_key=api_key)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Chọn hình thức dịch:", ["Dán văn bản", "Tải file PDF"])
        
        final_text_to_translate = ""
        input_name = ""

        if option == "Dán văn bản":
            input_text = st.text_area("Nhập hoặc dán đoạn văn cần dịch:", height=300)
            if input_text:
                final_text_to_translate = input_text
                input_name = "Văn bản nhập tay"

        else:
            uploaded_file = st.file_uploader("Chọn file PDF (Tối đa 200MB)", type=["pdf"])
            if uploaded_file:
                # Đọc PDF cục bộ để tiết kiệm RAM và tránh lỗi 404
                reader = PdfReader(uploaded_file)
                total_pages = len(reader.pages)
                st.success(f"Tài liệu: {total_pages} trang")
                
                st.info("💡 Mẹo: Với file lớn, hãy chọn khoảng 5-10 trang mỗi lần dịch.")
                c1, c2 = st.columns(2)
                start_p = c1.number_input("Từ trang:", min_value=1, max_value=total_pages, value=1)
                end_p = c2.number_input("Đến trang:", min_value=1, max_value=total_pages, value=min(5, total_pages))
                
                input_name = f"File: {uploaded_file.name} (Trang {start_p}-{end_p})"

                if st.button("Trích xuất và Dịch 🚀"):
                    with st.spinner("Đang đọc và dịch..."):
                        try:
                            extracted_text = ""
                            for i in range(start_p - 1, end_p):
                                extracted_text += reader.pages[i].extract_text() + "\n"
                            
                            if extracted_text.strip():
                                final_text_to_translate = extracted_text
                            else:
                                st.error("Không tìm thấy chữ trong các trang này (có thể là ảnh scan).")
