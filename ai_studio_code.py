import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- 1. CẤU HÌNH BỘ NHỚ ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = ""

st.set_page_config(page_title="AI Translator Pro", layout="wide")

# --- 2. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cấu hình hệ thống")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    # Sửa lỗi 404 bằng cách sử dụng ID model chuẩn xác
    model_name = st.selectbox("Chọn Model:", [
        "gemini-1.5-flash", 
        "gemini-1.5-pro", 
        "gemini-2.0-flash-exp"
    ])
    
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])
    
    st.markdown("---")
    st.subheader("📜 Lịch sử dịch thuật")
    if not st.session_state.history:
        st.write("Chưa có bản lưu.")
    else:
        for i, item in enumerate(reversed(st.session_state.history)):
            real_idx = len(st.session_state.history) - 1 - i
            if st.button(f"Bản {real_idx + 1}: {item['name'][:15]}...", key=f"hist_{real_idx}"):
                st.session_state.current_res = item['content']

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🌐 AI Translator Multi-Format")

if api_key:
    # Cấu hình API ngay khi có Key
    genai.configure(api_key=api_key)
    
    col1, col2 = st.columns(2)
    text_to_translate = ""
    input_label = ""

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Chọn hình thức:", ["Dán văn bản", "Tải file PDF"])
        
        if option == "Dán văn bản":
            raw_text = st.text_area("Dán nội dung cần dịch:", height=300)
            if st.button("Dịch văn bản 🚀"):
                if raw_text.strip():
                    text_to_translate = raw_text
                    input_label = "Văn bản nhập tay"
                else:
                    st.warning("Vui lòng dán văn bản.")

        else:
            uploaded_file = st.file_uploader("Chọn file PDF (Hỗ trợ file lớn)", type=["pdf"])
            if uploaded_file:
                try:
                    reader = PdfReader(uploaded_file)
                    total_pages = len(reader.pages)
                    st.success(f"Tài liệu: {total_pages} trang")
                    
                    c1, c2 = st.columns(2)
                    start_p = c1.number_input("Từ trang:", min_value=1, max_value=total_pages, value=1)
                    end_p = c2.number_input("Đến trang:", min_value=1, max_value=total_pages, value=min(10, total_pages))
                    
                    if st.button("Dịch PDF 🚀"):
                        with st.spinner("Đang trích xuất chữ..."):
                            extracted = ""
                            for i in range(start_p - 1, end_p):
                                page_text = reader.pages[i].extract_text()
                                if page_text:
                                    extracted += page_text + "\n"
                            
                            if extracted.strip():
                                text_to_translate = extracted
                                input_label = f"{uploaded_file.name} (P{start_p}-{end_p})"
                            else:
                                st.error("Không tìm thấy chữ (PDF ảnh scan).")
                except Exception as e:
                    st.error(f"Lỗi đọc PDF: {e}")

    # --- XỬ LÝ DỊCH AI ---
    if text_to_translate:
        try:
            with st.spinner("AI đang xử lý..."):
                # Ép sử dụng tiền tố models/ để tránh lỗi 404
                full_model_path = f"models/{model_name}" if "models/" not in model_name else model_name
                model = genai.GenerativeModel(full_model_path)
                
                prompt = f"Dịch đoạn sau sang {target_lang}. Chỉ trả về nội dung dịch:\n\n{text_to_translate}"
                response = model.generate_content(prompt)
                
                st.session_state.current_res = response.text
                st.session_state.history.append({
                    "name": input_label,
                    "content": response.text
                })
                st.balloons()
        except Exception as e:
            st.error(f"Lỗi AI (404/Quota): {e}")
            st.info("Mẹo: Nếu lỗi 404, hãy thử đổi Model sang 'gemini-1.5-flash'.")

    # --- 4. HIỂN THỊ KẾT QUẢ & XUẤT FILE ---
    with col2:
        st.subheader("📝 Kết quả")
        if st.session_state.current_res:
            st.text_area("Nội dung dịch:", st.session_state.current_res, height=450)
            
            st.markdown("---")
            st.write("📥 **Tùy chọn tải về:**")
            format_option = st.selectbox("Chọn định dạng file:", [".docx (Word)", ".txt (Văn bản)"])
            
            if format_option == ".docx (Word)":
                doc = Document()
                doc.add_paragraph(st.session_state.current_res)
                bio = io.BytesIO()
                doc.save(bio)
                st.download_button(
                    label="Tải file Word (.docx)",
                    data=bio.getvalue(),
                    file_name="translation.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            else:
                st.download_button(
                    label="Tải file Text (.txt)",
                    data=st.session_state.current_res,
                    file_name="translation.txt",
                    mime="text/plain"
                )
        else:
            st.info("Bản dịch sẽ hiện ở đây.")

else:
    st.warning("Vui lòng nhập API Key ở bên trái.")
