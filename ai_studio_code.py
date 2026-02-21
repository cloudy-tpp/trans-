# 1. Cài đặt thư viện
!pip install -q streamlit google-generativeai pypdf python-docx pyngrok

# 2. Tạo file app.py
with open('app.py', 'w', encoding='utf-8') as f:
    f.write("""
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

st.set_page_config(page_title="AI Translator", layout="wide")
st.title("🌐 AI Translator (Text & PDF)")

# Ô nhập API Key ngay trên giao diện để bảo mật
api_key = st.sidebar.text_input("Nhập Gemini API Key của bạn:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    with st.sidebar:
        model_name = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
        target_lang = st.selectbox("Ngôn ngữ đích", ["Tiếng Việt", "English", "French", "Japanese", "Korean", "Chinese"])
    
    col1, col2 = st.columns(2)
    input_text = ""

    with col1:
        st.subheader("Đầu vào")
        input_type = st.radio("Nguồn:", ["Văn bản", "File PDF"])
        if input_type == "Văn bản":
            input_text = st.text_area("Dán nội dung:", height=300)
        else:
            uploaded_file = st.file_uploader("Chọn PDF", type=["pdf"])
            if uploaded_file:
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    input_text += page.extract_text() + "\\n"
                st.success("Đã đọc file PDF")

    with col2:
        st.subheader("Bản dịch")
        if st.button("Dịch 🚀"):
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(f"Dịch sang {target_lang}:\\n\\n{input_text}")
            st.session_state.result = response.text
            
        if 'result' in st.session_state:
            st.text_area("Kết quả:", st.session_state.result, height=300)
            
            # Export Word
            doc = Document()
            doc.add_paragraph(st.session_state.result)
            bio = io.BytesIO()
            doc.save(bio)
            
            st.download_button("Tải file .doc (Word)", data=bio.getvalue(), file_name="dich.docx")
else:
    st.warning("Vui lòng nhập API Key ở cột bên trái để bắt đầu!")
    st.info("Lấy API Key miễn phí tại: https://aistudio.google.com/app/apikey")
    """)

# 3. Chạy App và tạo Link
from google.colab.output import eval_js
print("Click vào link dưới đây để mở App:")
print(eval_js("google.colab.kernel.proxyPort(8501)"))
!streamlit run app.py & npx localtunnel --port 8501