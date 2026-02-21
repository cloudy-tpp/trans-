import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io
import time

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Translator Pro", layout="wide")

# Khởi tạo bộ nhớ lịch sử
if 'trans_history' not in st.session_state:
    st.session_state.trans_history = []
if 'last_result' not in st.session_state:
    st.session_state.last_result = ""

st.title("🌐 AI Translator (Xử lý File lớn & Lưu trữ)")

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cài đặt")
    user_api_key = st.text_input("Dán Gemini API Key:", type="password")
    
    model_choice = "gemini-1.5-flash"
    if user_api_key:
        try:
            genai.configure(api_key=user_api_key)
            model_choice = st.selectbox("Chọn Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])
        except:
            pass
            
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese"])

    st.markdown("---")
    st.subheader("📚 Lịch sử dịch")
    if not st.session_state.trans_history:
        st.write("Chưa có bản ghi.")
    else:
        for i, item in enumerate(st.session_state.trans_history):
            with st.expander(f"Bản dịch {i+1}: {item['pages']}"):
                st.write(item['content'][:150] + "...")
                # Nút tải lại file từ lịch sử
                doc_io = io.BytesIO()
                d = Document()
                d.add_paragraph(item['content'])
                d.save(doc_io)
                st.download_button(f"Tải lại .docx", data=doc_io.getvalue(), file_name=f"history_{i+1}.docx", key=f"hist_{i}")

# --- KHU VỰC CHÍNH ---
if user_api_key:
    genai.configure(api_key=user_api_key)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📁 Tải tài liệu")
        uploaded_file = st.file_uploader("Chọn PDF (Tối đa 200MB)", type=["pdf"])
        
        if uploaded_file:
            try:
                # Đọc số trang mà không load toàn bộ file vào RAM để tránh lỗi 160MB
                pdf_reader = PdfReader(uploaded_file)
                total_pages = len(pdf_reader.pages)
                st.success(f"Tài liệu: {total_pages} trang")
                
                st.markdown("---")
                st.subheader("✂️ Chọn đoạn dịch")
                st.write("Gợi ý: Dịch 5-10 trang mỗi lần để tránh quá tải API.")
                
                c1, c2 = st.columns(2)
                start_p = c1.number_input("Từ trang:", min_value=1, max_value=total_pages, value=1)
                end_p = c2.number_input("Đến trang:", min_value=1, max_value=total_pages, value=min(5, total_pages))
                
                if st.button("Bắt đầu dịch đoạn này 🚀"):
                    with st.spinner(f"Đang xử lý trang {start_p} đến {end_p}..."):
                        try:
                            model = genai.GenerativeModel(model_name=model_choice)
                            
                            # Lưu file tạm để AI đọc
                            with open("temp_p.pdf", "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            
                            google_file = genai.upload_file(path="temp_p.pdf", mime_type="application/pdf")
                            
                            while google_file.state.name == "PROCESSING":
                                time.sleep(3)
                                google_file = genai.get_file(google_file.name)
                            
                            prompt = f"Hãy dịch nội dung từ trang {start_p} đến trang {end_p} của tài liệu này sang {target_lang}. Chỉ trả về văn bản dịch."
                            
                            response = model.generate_content([prompt, google_file])
                            
                            # Lưu vào lịch sử và hiển thị
                            st.session_state.last_result = response.text
                            st.session_state.trans_history.append({
                                "name": uploaded_file.name,
                                "pages": f"Trang {start_p}-{end_p}",
                                "content": response.text
                            })
                            
                            genai.delete_file(google_file.name)
                            st.balloons()
                            
                        except Exception as e:
                            if "429" in str(e):
                                st.error(f"Hết hạn mức tại trang {start_p}. Hãy đổi Key và dịch tiếp từ trang này!")
                            else:
                                st.error(f"Lỗi: {e}")
            except Exception as read_err:
                st.error(f"Không thể đọc file PDF: {read_err}")

    with col2:
        st.subheader("📝 Kết quả hiện tại")
        if st.session_state.last_result:
            st.text_area("Bản dịch:", st.session_state.last_result, height=500)
            
            # Xuất Word
            doc = Document()
            doc.add_paragraph(st.session_state.last_result)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("📥 Tải về file Word (.docx)", data=bio.getvalue(), file_name=f"dich_trang_{start_p}_{end_p}.docx")
        else:
            st.info("Kết quả dịch sẽ hiện ở đây.")

else:
    st.warning("Vui lòng nhập API Key ở bên trái để bắt đầu.")
