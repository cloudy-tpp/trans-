import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time
import os

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="AI Translator Ultimate", layout="wide")
st.title("🌐 AI Translator (Gemini 1.5 Flash/Pro)")

# Sidebar
with st.sidebar:
    st.header("Cài đặt API")
    user_api_key = st.text_input("Dán Gemini API Key:", type="password")
    
    # Sử dụng các ID model chuẩn xác nhất để tránh lỗi 404
    model_choice = st.selectbox("Chọn Model", [
        "gemini-1.5-flash-latest", 
        "gemini-1.5-pro-latest",
        "gemini-2.0-flash-exp"
    ])
    
    target_lang = st.selectbox("Ngôn ngữ đích", ["Tiếng Việt", "English", "French", "Japanese", "Korean", "Chinese"])
    st.markdown("---")
    st.info("Lưu ý: Với file 160MB, AI cần thời gian để tải lên và phân tích. Vui lòng kiên nhẫn.")

def export_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# Kiểm tra API Key
if user_api_key:
    genai.configure(api_key=user_api_key)
    
    col1, col2 = st.columns(2)
    
    input_data = None
    with col1:
        st.subheader("Đầu vào")
        input_type = st.radio("Phương thức:", ["Nhập văn bản", "Tải file PDF lớn"])
        
        if input_type == "Nhập văn bản":
            input_data = st.text_area("Dán nội dung:", height=300)
        else:
            input_data = st.file_uploader("Chọn file PDF (Tối đa 200MB)", type=["pdf"])
            if input_data:
                st.success(f"✅ Đã nhận: {input_data.name}")

    with col2:
        st.subheader("Kết quả dịch")
        if st.button("Bắt đầu dịch ngay 🚀"):
            if not input_data:
                st.error("Vui lòng cung cấp nội dung!")
            else:
                with st.spinner("Đang xử lý dữ liệu... (File lớn có thể mất hơn 1 phút)"):
                    try:
                        # 1. Khởi tạo Model
                        model = genai.GenerativeModel(model_name=model_choice)
                        
                        if input_type == "Nhập văn bản":
                            response = model.generate_content(f"Dịch đoạn văn sau sang {target_lang}: {input_data}")
                            result_text = response.text
                        else:
                            # 2. Xử lý File PDF lớn qua File API
                            # Lưu file tạm
                            with open("temp_file.pdf", "wb") as f:
                                f.write(input_data.getbuffer())
                            
                            # Upload lên server Google
                            st.write(" đang tải file lên server AI...")
                            uploaded_file = genai.upload_file(path="temp_file.pdf", mime_type="application/pdf")
                            
                            # Đợi file xử lý xong
                            while uploaded_file.state.name == "PROCESSING":
                                time.sleep(5)
                                uploaded_file = genai.get_file(uploaded_file.name)
                            
                            if uploaded_file.state.name == "FAILED":
                                raise Exception("AI không thể xử lý file này.")

                            # 3. Gửi yêu cầu dịch
                            prompt = f"Hãy dịch toàn bộ nội dung trong file PDF này sang {target_lang}. Chỉ trả về văn bản đã dịch."
                            response = model.generate_content([prompt, uploaded_file])
                            result_text = response.text
                            
                            # Xóa file sau khi dịch xong để bảo mật
                            genai.delete_file(uploaded_file.name)

                        st.session_state.translated_result = result_text
                        st.text_area("Bản dịch:", result_text, height=400)
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "404" in error_msg:
                            st.error("Lỗi 404: Tên model không hợp lệ hoặc API Key của bạn chưa hỗ trợ model này. Hãy thử chọn 'gemini-1.5-flash-latest'.")
                        elif "429" in error_msg:
                            st.error("Lỗi 429: Bạn đã hết hạn mức sử dụng miễn phí (Rate limit).")
                        else:
                            st.error(f"Lỗi: {error_msg}")

        # Nút tải file Word
        if 'translated_result' in st.session_state:
            st.markdown("---")
            docx_data = export_docx(st.session_state.translated_result)
            st.download_button(
                label="📥 Tải bản dịch (.docx)",
                data=docx_data,
                file_name=f"dich_{target_lang}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
else:
    st.info("Vui lòng nhập API Key để tiếp tục.")
