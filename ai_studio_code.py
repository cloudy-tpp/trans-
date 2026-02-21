import streamlit as st
import google.generativeai as genai
from docx import Document
import io
import time

# --- CẤU HÌNH ---
st.set_page_config(page_title="AI Translator Pro", layout="wide")
st.title("🌐 AI Translator (Fixed 404 Error)")

with st.sidebar:
    st.header("Cấu hình API")
    user_api_key = st.text_input("Dán Gemini API Key:", type="password")
    
    # SỬA ĐỔI: Thêm tiền tố 'models/' để tránh lỗi 404
    model_choice = st.selectbox("Chọn Model", [
        "models/gemini-1.5-flash", 
        "models/gemini-1.5-pro",
        "models/gemini-2.0-flash-exp"
    ])
    
    target_lang = st.selectbox("Ngôn ngữ đích", ["Tiếng Việt", "English", "French", "Japanese", "Korean", "Chinese"])
    
    if st.button("Kiểm tra API Key ✅"):
        if user_api_key:
            try:
                genai.configure(api_key=user_api_key)
                for m in genai.list_models():
                    pass
                st.success("API Key hoạt động tốt!")
            except Exception as e:
                st.error(f"Lỗi Key: {e}")

def export_docx(text):
    doc = Document()
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

if user_api_key:
    genai.configure(api_key=user_api_key)
    
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
                st.error("Chưa có dữ liệu!")
            else:
                with st.spinner("Đang xử lý..."):
                    try:
                        model = genai.GenerativeModel(model_name=model_choice)
                        
                        if input_type == "Nhập văn bản":
                            response = model.generate_content(f"Dịch sang {target_lang}: {input_data}")
                            result_text = response.text
                        else:
                            # Xử lý file PDF lớn
                            with open("temp.pdf", "wb") as f:
                                f.write(input_data.getbuffer())
                            
                            uploaded_file = genai.upload_file(path="temp.pdf", mime_type="application/pdf")
                            
                            while uploaded_file.state.name == "PROCESSING":
                                time.sleep(3)
                                uploaded_file = genai.get_file(uploaded_file.name)
                            
                            prompt = f"Dịch toàn bộ nội dung file này sang {target_lang}. Chỉ trả về bản dịch."
                            response = model.generate_content([prompt, uploaded_file])
                            result_text = response.text
                            
                            # Xóa file trên server Google sau khi dùng
                            genai.delete_file(uploaded_file.name)

                        st.session_state.translated_result = result_text
                        st.text_area("Bản dịch:", result_text, height=400)
                        
                    except Exception as e:
                        st.error(f"Lỗi: {str(e)}")
                        st.info("Mẹo: Nếu vẫn gặp 404, hãy thử chọn model 'models/gemini-2.0-flash-exp'.")

        if 'translated_result' in st.session_state:
            docx_data = export_docx(st.session_state.translated_result)
            st.download_button("📥 Tải file .docx", data=docx_data, file_name="dich.docx")
