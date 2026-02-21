import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI Translator Ultimate", layout="wide")
st.title("🌐 AI Translator (Phiên bản Tự động Sửa lỗi 404)")

# Sidebar
with st.sidebar:
    st.header("Cấu hình API")
    user_api_key = st.text_input("Dán Gemini API Key:", type="password")
    
    available_models = []
    if user_api_key:
        try:
            genai.configure(api_key=user_api_key)
            # Tự động quét các model mà API Key này có quyền truy cập
            models = genai.list_models()
            available_models = [m.name.replace('models/', '') for m in models if 'generateContent' in m.supported_generation_methods]
            st.success("Đã kết nối API thành công!")
        except Exception as e:
            st.error(f"Lỗi kết nối API: {e}")

    # Cho người dùng chọn từ danh sách thực tế của Google
    if available_models:
        model_choice = st.selectbox("Chọn Model (Hệ thống tự quét):", available_models)
    else:
        model_choice = st.selectbox("Chọn Model mặc định:", ["gemini-1.5-flash", "gemini-1.5-pro"])
        
    target_lang = st.selectbox("Ngôn ngữ đích", ["Tiếng Việt", "English", "French", "Japanese", "Korean", "Chinese"])
    st.info("Mẹo: Nếu lỗi 404, hãy thử chọn model có chữ 'flash' trong danh sách.")

def export_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# GIAO DIỆN CHÍNH
if user_api_key:
    col1, col2 = st.columns(2)
    input_data = None
    
    with col1:
        st.subheader("Đầu vào")
        input_type = st.radio("Phương thức:", ["Nhập văn bản", "Tải file PDF"])
        if input_type == "Nhập văn bản":
            input_data = st.text_area("Dán nội dung:", height=300)
        else:
            input_data = st.file_uploader("Chọn file PDF", type=["pdf"])
            if input_data:
                st.success(f"Đã nhận file: {input_data.name}")

    with col2:
        st.subheader("Kết quả dịch")
        if st.button("Dịch ngay 🚀"):
            if not input_data:
                st.error("Chưa có nội dung để dịch!")
            else:
                with st.spinner("Đang xử lý (Vui lòng đợi)..."):
                    try:
                        # Sử dụng chính xác ID model từ hệ thống
                        model = genai.GenerativeModel(model_name=model_choice)
                        
                        if input_type == "Nhập văn bản":
                            response = model.generate_content(f"Dịch sang {target_lang}: {input_data}")
                            result_text = response.text
                        else:
                            # Lưu file tạm và upload
                            with open("temp.pdf", "wb") as f:
                                f.write(input_data.getbuffer())
                            
                            # Upload file (Cần dùng v1beta cho tính năng PDF)
                            uploaded_file = genai.upload_file(path="temp.pdf", mime_type="application/pdf")
                            
                            while uploaded_file.state.name == "PROCESSING":
                                time.sleep(3)
                                uploaded_file = genai.get_file(uploaded_file.name)
                            
                            prompt = f"Hãy dịch toàn bộ nội dung trong file PDF này sang {target_lang}. Chỉ trả về nội dung đã dịch."
                            response = model.generate_content([prompt, uploaded_file])
                            result_text = response.text
                            
                            genai.delete_file(uploaded_file.name)

                        st.session_state.translated_result = result_text
                        st.text_area("Bản dịch:", result_text, height=400)
                        
                    except Exception as e:
                        st.error(f"Lỗi: {str(e)}")
                        st.info("Hãy thử chọn một Model khác trong danh sách bên trái.")

        if 'translated_result' in st.session_state:
            docx_data = export_docx(st.session_state.translated_result)
            st.download_button("📥 Tải về file Word (.docx)", data=docx_data, file_name="ban_dich.docx")
else:
    st.warning("Vui lòng nhập API Key ở bên trái.")
