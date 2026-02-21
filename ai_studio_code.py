import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io
import time

# --- CẤU HÌNH ---
st.set_page_config(page_title="AI Translator Pro Max", layout="wide")

# Khởi tạo bộ nhớ lưu trữ lịch sử dịch trong phiên làm việc
if 'trans_history' not in st.session_state:
    st.session_state.trans_history = []

st.title("🌐 AI Translator (Lưu trữ & Dịch nối tiếp)")

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cấu hình & Lịch sử")
    user_api_key = st.text_input("Dán Gemini API Key:", type="password")
    
    # Quét model
    model_choice = "gemini-1.5-flash"
    if user_api_key:
        try:
            genai.configure(api_key=user_api_key)
            model_choice = st.selectbox("Chọn Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])
        except:
            pass
            
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French"])

    st.markdown("---")
    st.subheader("📚 Lịch sử dịch (Session)")
    if not st.session_state.trans_history:
        st.write("Chưa có bản ghi nào.")
    else:
        for i, item in enumerate(st.session_state.trans_history):
            with st.expander(f"Bản dịch {i+1}: {item['name']}"):
                st.write(f"**Trang:** {item['pages']}")
                st.write(item['content'][:200] + "...")
                # Nút tải lại file word cho bản ghi cũ
                doc_io = io.BytesIO()
                d = Document()
                d.add_paragraph(item['content'])
                d.save(doc_io)
                st.download_button(f"Tải lại .docx ({i+1})", data=doc_io.getvalue(), file_name=f"history_{i+1}.docx", key=f"dl_{i}")

# --- KHU VỰC CHÍNH ---
if user_api_key:
    genai.configure(api_key=user_api_key)
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📁 Tải tài liệu")
        uploaded_file = st.file_uploader("Chọn file PDF (Hỗ trợ file cực lớn)", type=["pdf"])
        
        if uploaded_file:
            # Đọc thông tin số trang
            pdf_reader = PdfReader(uploaded_file)
            total_pages = len(pdf_reader.pages)
            st.success(f"Tài liệu có tổng cộng: **{total_pages} trang**")
            
            st.markdown("---")
            st.subheader("✂️ Chọn đoạn cần dịch")
            st.info("Vì file rất lớn, bạn nên dịch từng đoạn (ví dụ 10 trang một lần) để không bị lỗi hạn mức.")
            
            start_p = st.number_input("Từ trang:", min_value=1, max_value=total_pages, value=1)
            end_p = st.number_input("Đến trang:", min_value=1, max_value=total_pages, value=min(10, total_pages))
            
            if st.button("Bắt đầu dịch đoạn này 🚀"):
                with st.spinner(f"Đang dịch từ trang {start_p} đến {end_p}..."):
                    try:
                        model = genai.GenerativeModel(model_name=model_choice)
                        
                        # Upload file lên File API
                        with open("temp_p.pdf", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        google_file = genai.upload_file(path="temp_p.pdf", mime_type="application/pdf")
                        
                        while google_file.state.name == "PROCESSING":
                            time.sleep(3)
                            google_file = genai.get_file(google_file.name)
                        
                        prompt = f"""
                        Bạn là dịch giả chuyên nghiệp. 
                        Hãy dịch nội dung từ trang {start_p} đến trang {end_p} của tài liệu này sang {target_lang}.
                        Yêu cầu: Chỉ trả về nội dung đã dịch, không giải thích. 
                        Giữ nguyên các tiêu đề và định dạng văn bản cơ bản.
                        """
                        
                        response = model.generate_content([prompt, google_file])
                        
                        # Lưu vào lịch sử
                        new_record = {
                            "name": uploaded_file.name,
                            "pages": f"{start_p} - {end_p}",
                            "content": response.text
                        }
                        st.session_state.trans_history.append(new_record)
                        st.session_state.last_result = response.text
                        
                        genai.delete_file(google_file.name)
                        st.balloons()
                        
                    except Exception as e:
                        err = str(e)
                        if "429" in err:
                            st.error(f"Dừng tại trang {start_p}. Lỗi: Hết hạn mức (Quota). Hãy đổi API Key khác và dịch tiếp từ trang {start_p}!")
                        else:
                            st.error(f"Lỗi: {err}")

    with col2:
        st.subheader("📝 Kết quả hiện tại")
        if 'last_result' in st.session_state:
            st.text_area("Bản dịch mới nhất:", st.session_state.last_result, height=500)
            
            # Xuất Word
            doc = Document()
            doc.add_paragraph(st.session_state.last_result)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("📥 Tải về bản dịch (.docx)", data=bio.getvalue(), file_name=f"dich_trang_{start_p}_{end_p}.docx")
        else:
            st.write("Chưa có kết quả dịch trong phiên này.")

else:
    st.warning("Vui lòng nhập API Key để bắt đầu.")
