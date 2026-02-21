import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Translator Pro", layout="wide")
st.title("🌐 AI Translator (Hỗ trợ PDF & Word)")

# Ô nhập API Key bên trái để bảo mật
with st.sidebar:
    st.header("Cấu hình")
    user_api_key = st.text_input("Dán Gemini API Key vào đây:", type="password")
    model_name = st.selectbox("Chọn Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
    target_lang = st.selectbox("Ngôn ngữ đích", ["Tiếng Việt", "English", "French", "Japanese", "Korean", "Chinese"])
    st.info("Lấy Key tại: https://aistudio.google.com/app/apikey")

# Hàm trích xuất văn bản từ PDF
def get_pdf_text(pdf_file):
    text = ""
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# Hàm xuất file Word
def export_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# GIAO DIỆN CHÍNH
col1, col2 = st.columns(2)

input_text = ""
if user_api_key:
    genai.configure(api_key=user_api_key)
    
    with col1:
        st.subheader("Đầu vào")
        input_type = st.radio("Chọn hình thức:", ["Nhập văn bản", "Tải file PDF"])
        
        if input_type == "Nhập văn bản":
            input_text = st.text_area("Dán văn bản cần dịch:", height=300)
        else:
            uploaded_file = st.file_uploader("Chọn file PDF", type=["pdf"])
            if uploaded_file:
                input_text = get_pdf_text(uploaded_file)
                st.success("Đã đọc xong PDF!")

    with col2:
        st.subheader("Kết quả dịch")
        if st.button("Dịch ngay 🚀"):
            if not input_text.strip():
                st.warning("Vui lòng nhập nội dung!")
            else:
                with st.spinner("Đang dịch..."):
                    try:
                        model = genai.GenerativeModel(model_name)
                        prompt = f"Dịch văn bản sau đây sang {target_lang}. Chỉ trả về nội dung đã dịch:\n\n{input_text}"
                        response = model.generate_content(prompt)
                        
                        st.session_state.translated_result = response.text
                        st.text_area("Bản dịch:", st.session_state.translated_result, height=300)
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

        if 'translated_result' in st.session_state:
            st.markdown("---")
            docx_data = export_docx(st.session_state.translated_result)
            st.download_button(
                label="📥 Tải về file .doc (Word)",
                data=docx_data,
                file_name="ban_dich.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
else:
    st.warning("Vui lòng nhập API Key ở cột bên trái để bắt đầu!")
