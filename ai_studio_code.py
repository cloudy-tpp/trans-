import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io
import time

# --- 1. CẤU HÌNH BỘ NHỚ ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = ""

st.set_page_config(page_title="AI Translator Ultimate", layout="wide")

# --- SIDEBAR: CẤU HÌNH & LỊCH SỬ ---
with st.sidebar:
    st.header("🔑 Cấu hình hệ thống")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    selected_model_id = ""
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # TỰ ĐỘNG DÒ TÌM CÁC MODEL MÀ KEY CỦA BẠN ĐƯỢC PHÉP DÙNG
            models = genai.list_models()
            valid_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            
            if valid_models:
                # Tạo danh sách tên dễ đọc
                display_names = [m.replace('models/', '') for m in valid_models]
                # Ưu tiên chọn 1.5-flash nếu có trong danh sách
                default_idx = 0
                if "gemini-1.5-flash" in display_names:
                    default_idx = display_names.index("gemini-1.5-flash")
                
                choice = st.selectbox("Chọn Model (Hệ thống tự quét):", display_names, index=default_idx)
                selected_model_id = f"models/{choice}"
                st.success("Kết nối API thành công!")
            else:
                st.error("Không tìm thấy model nào khả dụng cho Key này.")
        except Exception as e:
            st.error(f"Lỗi API Key: {e}")

    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])

    st.markdown("---")
    st.subheader("📜 Lịch sử lưu trữ")
    if st.session_state.history:
        if st.button("🗑️ Xóa toàn bộ lịch sử"):
            st.session_state.history = []
            st.rerun()
            
        for i, item in enumerate(st.session_state.history):
            col_h1, col_h2 = st.columns([4, 1])
            if col_h1.button(f"📄 {i+1}. {item['name'][:10]}...", key=f"v_{i}"):
                st.session_state.current_res = item['content']
            if col_h2.button("🗑️", key=f"d_{i}"):
                st.session_state.history.pop(i)
                st.rerun()
    else:
        st.write("Chưa có bản lưu.")

# --- GIAO DIỆN CHÍNH ---
st.title("🌐 AI Translator (Phiên bản tự sửa lỗi 404)")

if api_key:
    col1, col2 = st.columns(2)
    input_txt, input_name = "", ""

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Hình thức:", ["Dán văn bản", "Tải file PDF"])
        
        if option == "Dán văn bản":
            raw = st.text_area("Nội dung:", height=250)
            if st.button("Dịch ngay 🚀"):
                if raw.strip():
                    input_txt, input_name = raw, "Văn bản dán"
        else:
            file = st.file_uploader("Chọn PDF (Hỗ trợ file lớn)", type=["pdf"])
            if file:
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
                            extracted += reader.pages[j].extract_text() + "\n"
                        input_txt, input_name = extracted, f"{file.name} (P{start}-{end})"

    # XỬ LÝ DỊCH
    if input_txt and selected_model_id:
        try:
            with st.spinner("AI đang dịch..."):
                model = genai.GenerativeModel(model_name=selected_model_id)
                prompt = f"Dịch đoạn văn sau sang {target_lang}. Chỉ trả về nội dung đã dịch:\n\n{input_txt}"
                response = model.generate_content(prompt)
                
                st.session_state.current_res = response.text
                st.session_state.history.append({"name": input_name, "content": response.text})
                st.balloons()
        except Exception as e:
            err = str(e)
            if "429" in err:
                st.error("⚠️ Lỗi 429: Hết hạn mức! Hãy đợi 60 giây.")
            else:
                st.error(f"Lỗi AI: {err}")

    with col2:
        st.subheader("📝 Kết quả")
        if st.session_state.current_res:
            st.text_area("Bản dịch:", st.session_state.current_res, height=450)
            
            st.write("📥 **Tải về:**")
            col_d1, col_d2 = st.columns(2)
            
            # Xuất file Word (.docx)
            doc = Document()
            doc.add_paragraph(st.session_state.current_res)
            bio = io.BytesIO()
            doc.save(bio)
            col_d1.download_button("Tải file .docx", bio.getvalue(), "translation.docx")
            
            # Xuất file Text (.txt)
            col_d2.download_button("Tải file .txt", st.session_state.current_res, "translation.txt")
        else:
            st.info("Bản dịch sẽ hiển thị ở đây.")
else:
    st.info("Hãy nhập API Key ở bên trái để bắt đầu.")
