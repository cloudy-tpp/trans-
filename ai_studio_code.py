import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# 1. Khởi tạo trạng thái App (Quan trọng để tránh sập)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_text' not in st.session_state:
    st.session_state.last_text = ""

st.set_page_config(page_title="AI Translator Pro", layout="wide")

# 2. Giao diện Sidebar
with st.sidebar:
    st.header("🔑 Cấu hình")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    model_name = st.selectbox("Chọn Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "Tiếng Anh", "Tiếng Trung", "Tiếng Pháp"])
    
    st.markdown("---")
    st.subheader("📜 Lịch sử phiên này")
    for i, item in enumerate(st.session_state.history):
        st.write(f"Đoạn {i+1}: {item['range']}")

st.title("🌐 AI Translator (Xử lý file lớn)")

# 3. Khu vực xử lý chính
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📁 Tải tài liệu")
            uploaded_file = st.file_uploader("Chọn PDF (Lên đến 200MB)", type=["pdf"])
            
            if uploaded_file:
                # Đọc số trang một cách tiết kiệm RAM
                reader = PdfReader(uploaded_file)
                total_pages = len(reader.pages)
                st.success(f"✅ Đã nhận: {total_pages} trang")
                
                st.markdown("---")
                st.write("💡 **Gợi ý:** Với file 168MB, hãy dịch mỗi lần khoảng 5-10 trang.")
                c1, c2 = st.columns(2)
                start_p = c1.number_input("Từ trang:", min_value=1, max_value=total_pages, value=1)
                end_p = c2.number_input("Đến trang:", min_value=1, max_value=total_pages, value=min(5, total_pages))
                
                if st.button("Dịch đoạn này 🚀"):
                    if end_p - start_p > 20:
                        st.error("Để tránh sập RAM, bạn không nên dịch quá 20 trang một lần.")
                    else:
                        with st.spinner(f"Đang xử lý trang {start_p} đến {end_p}..."):
                            try:
                                # Trích xuất văn bản cục bộ
                                text_to_trans = ""
                                for i in range(start_p - 1, end_p):
                                    page_text = reader.pages[i].extract_text()
                                    if page_text:
                                        text_to_trans += page_text + "\n"
                                
                                if text_to_trans.strip():
                                    model = genai.GenerativeModel(model_name)
                                    prompt = f"Dịch nội dung sau sang {target_lang}. Chỉ trả về bản dịch:\n\n{text_to_trans}"
                                    response = model.generate_content(prompt)
                                    
                                    # Lưu kết quả vào Session
                                    st.session_state.last_text = response.text
                                    st.session_state.history.append({
                                        "range": f"Trang {start_p}-{end_p}",
                                        "content": response.text
                                    })
                                else:
                                    st.warning("Không tìm thấy văn bản trong các trang này.")
                            except Exception as e:
                                st.error(f"Lỗi khi dịch: {e}")

        with col2:
            st.subheader("📝 Bản dịch")
            if st.session_state.last_text:
                st.text_area("Nội dung:", st.session_state.last_text, height=400)
                
                # Nút tải file Word
                doc = Document()
                doc.add_paragraph(st.session_state.last_text)
                bio = io.BytesIO()
                doc.save(bio)
                st.download_button("📥 Tải file .docx", data=bio.getvalue(), file_name=f"dich_trang_{start_p}_{end_p}.docx")
            else:
                st.info("Kết quả sẽ hiển thị tại đây.")
                
    except Exception as e:
        st.error(f"Lỗi API: {e}")
else:
    st.info("Vui lòng nhập API Key ở thanh bên trái để bắt đầu.")
