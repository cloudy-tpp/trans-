import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io
import time

# --- 1. CẤU HÌNH SESSION ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = ""

st.set_page_config(page_title="AI Translator Pro Max", layout="wide")

# --- HÀM XỬ LÝ LỊCH SỬ ---
def delete_item(index):
    st.session_state.history.pop(index)
    st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Cấu hình & Lịch sử")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    # DANH SÁCH MODEL (Cố định các model quan trọng + Tự động quét thêm)
    available = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-latest", "gemini-2.0-flash-exp"]
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Thử quét thêm các model khác nếu có
            models = genai.list_models()
            for m in models:
                name = m.name.replace('models/', '')
                if name not in available:
                    available.append(name)
            st.success("Đã kết nối API!")
        except:
            st.warning("Không thể quét thêm model, sử dụng danh sách mặc định.")

    # Hiển thị menu chọn Model
    selected_model = st.selectbox("Chọn Model (Khuyên dùng: 1.5-flash):", available, index=0)
    
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])

    st.markdown("---")
    st.subheader("📜 Lịch sử dịch thuật")
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            c_h1, c_h2 = st.columns([4, 1])
            if c_h1.button(f"📄 {item['name'][:15]}...", key=f"v_{i}"):
                st.session_state.current_res = item['content']
            if c_h2.button("🗑️", key=f"d_{i}"):
                delete_item(i)
    else:
        st.write("Chưa có bản lưu.")

# --- CHÍNH ---
st.title("🌐 AI Translator (Giao diện chuẩn hóa)")

if api_key:
    col1, col2 = st.columns(2)
    input_txt, input_name = "", ""

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Hình thức:", ["Dán văn bản", "Tải file PDF"])
        
        if option == "Dán văn bản":
            raw = st.text_area("Nội dung:", height=200)
            if st.button("Dịch ngay 🚀"):
                if raw.strip():
                    input_txt, input_name = raw, "Văn bản dán"
                else: st.warning("Hãy nhập nội dung.")
        else:
            file = st.file_uploader("Chọn PDF (Lên đến 200MB)", type=["pdf"])
            if file:
                try:
                    reader = PdfReader(file)
                    total = len(reader.pages)
                    st.success(f"Tài liệu: {total} trang")
                    c1, c2 = st.columns(2)
                    start = c1.number_input("Từ trang:", 1, total, 1)
                    end = c2.number_input("Đến trang:", 1, total, min(start+4, total))
                    
                    if st.button("Dịch PDF 🚀"):
                        with st.spinner("Đang trích xuất chữ..."):
                            extracted = ""
                            for j in range(start-1, end):
                                page_text = reader.pages[j].extract_text()
                                if page_text: extracted += page_text + "\n"
                            
                            if extracted.strip():
                                input_txt, input_name = extracted, f"{file.name} (P{start}-{end})"
                            else: st.error("Không tìm thấy chữ trong PDF.")
                except Exception as e: st.error(f"Lỗi PDF: {e}")

    # Xử lý AI
    if input_txt:
        try:
            with st.spinner("AI đang xử lý (Vui lòng đợi 10-30s)..."):
                model = genai.GenerativeModel(selected_model)
                # Prompt tối ưu để AI tập trung vào dịch
                prompt = f"Bạn là dịch giả chuyên nghiệp. Hãy dịch nội dung sau sang {target_lang}. Chỉ trả về nội dung đã dịch, không thêm lời dẫn:\n\n{input_txt}"
                response = model.generate_content(prompt)
                
                st.session_state.current_res = response.text
                st.session_state.history.append({"name": input_name, "content": response.text})
                st.balloons()
        except Exception as e:
            err = str(e)
            if "429" in err:
                st.error("⚠️ Lỗi 429: Hết hạn mức! Hãy đợi 60 giây và thử lại.")
            elif "404" in err:
                st.error("⚠️ Lỗi 404: Model này không khả dụng với Key của bạn. Hãy thử chọn 'gemini-1.5-flash-latest'.")
            else:
                st.error(f"Lỗi hệ thống: {err}")

    with col2:
        st.subheader("📝 Kết quả")
        if st.session_state.current_res:
            st.text_area("Bản dịch:", st.session_state.current_res, height=450)
            
            st.write("📥 **Tải về:**")
            col_d1, col_d2 = st.columns(2)
            
            # Xuất Word
            doc = Document()
            doc.add_paragraph(st.session_state.current_res)
            bio = io.BytesIO()
            doc.save(bio)
            col_d1.download_button("Tải file .docx", bio.getvalue(), "translation.docx")
            # Xuất Text
            col_d2.download_button("Tải file .txt", st.session_state.current_res, "translation.txt")
        else:
            st.info("Bản dịch sẽ hiển thị ở đây.")
else:
    st.info("Hãy nhập API Key ở bên trái để bắt đầu.")
