import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Translator Pro", layout="wide")
st.title("🌐 AI Translator (Hỗ trợ PDF lớn & Word)")

# Sidebar cấu hình
with st.sidebar:
    st.header("Cấu hình")
    user_api_key = st.text_input("Dán Gemini API Key vào đây:", type="password")
    # Cập nhật lại tên model chuẩn xác nhất
    model_choice = st.selectbox("Chọn Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
    target_lang = st.selectbox("Ngôn ngữ đích", ["Tiếng Việt", "English", "French", "Japanese", "Korean", "Chinese"])
    st.info("Lấy Key tại: https://aistudio.google.com/app/apikey")

# Hàm xuất file Word
def export_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# GIAO DIỆN CHÍNH
if user_api_key:
    genai.configure(api_key=user_api_key)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Đầu vào")
        input_type = st.radio("Chọn hình thức:", ["Nhập văn bản", "Tải file PDF"])
        
        input_data = None
        if input_type == "Nhập văn bản":
            input_data = st.text_area("Dán văn bản cần dịch:", height=300)
        else:
            input_data = st.file_uploader("Chọn file PDF (Hỗ trợ file lớn)", type=["pdf"])
            if input_data:
                st.success(f"Đã nhận file: {input_data.name} ({input_data.size/1024/1024:.2f} MB)")

    with col2:
        st.subheader("Kết quả dịch")
        if st.button("Dịch ngay 🚀"):
            if not input_data:
                st.warning("Vui lòng nhập nội dung hoặc tải file!")
            else:
                with st.spinner("Đang xử lý (File lớn có thể mất 1-2 phút)..."):
                    try:
                        model = genai.GenerativeModel(model_name=model_choice)
                        
                        if input_type == "Nhập văn bản":
                            prompt = f"Dịch văn bản sau đây sang {target_lang}. Chỉ trả về nội dung đã dịch:\n\n{input_data}"
                            response = model.generate_content(prompt)
                        else:
                            # Tải file lên Google File API để xử lý file lớn/nặng
                            # Lưu file tạm để upload
                            with open("temp_file.pdf", "wb") as f:
                                f.write(input_data.getbuffer())
                            
                            uploaded_file = genai.upload_file(path="temp_file.pdf", mime_type="application/pdf")
                            
                            # Đợi file được xử lý trên server Google
                            while uploaded_file.state.name == "PROCESSING":
                                time.sleep(2)
                                uploaded_file = genai.get_file(uploaded_file.name)
                            
                            prompt = f"Hãy dịch toàn bộ nội dung trong file PDF này sang {target_lang}. Chỉ trả về văn bản đã dịch, giữ nguyên cấu trúc nếu có thể."
                            response = model.generate_content([prompt, uploaded_file])
                        
                        st.session_state.translated_result = response.text
                        st.text_area("Bản dịch:", st.session_state.translated_result, height=400)
                        
                    except Exception as e:
                        st.error(f"Lỗi chi tiết: {str(e)}")

        # Nút tải file Word
        if 'translated_result' in st.session_state:
            st.markdown("---")
            docx_data = export_docx(st.session_state.translated_result)
            st.download_button(
                label="📥 Tải về file Word (.docx)",
                data=docx_data,
                file_name=f"ban_dich_{target_lang}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
else:
    st.warning("Vui lòng nhập API Key ở cột bên trái để bắt đầu!")
