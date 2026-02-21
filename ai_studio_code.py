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

st.set_page_config(page_title="AI Translator Pro", layout="wide")

# --- 2. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cấu hình hệ thống")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    available_models = []
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Tự động lấy danh sách model mà Key của bạn được phép dùng
            models = genai.list_models()
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            st.success("API Key hợp lệ!")
        except Exception as e:
            st.error(f"Lỗi API Key hoặc Vùng địa lý: {e}")

    # Lựa chọn model từ danh sách thực tế của Google trả về
    if available_models:
        # Làm sạch tên để hiển thị (bỏ chữ 'models/')
        display_models = [m.replace('models/', '') for m in available_models]
        choice = st.selectbox("Chọn Model (Hệ thống tự quét):", display_models)
        model_name = f"models/{choice}"
    else:
        model_name = st.selectbox("Chọn Model mặc định:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])
    
    st.markdown("---")
    st.subheader("📜 Lịch sử dịch")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            idx = len(st.session_state.history) - 1 - i
            if st.button(f"Bản {idx + 1}: {item['name'][:15]}...", key=f"h_{idx}"):
                st.session_state.current_res = item['content']

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🌐 AI Translator (Anti-404 & Multi-Format)")

if api_key:
    col1, col2 = st.columns(2)
    text_to_translate = ""
    input_label = ""

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Chọn hình thức:", ["Dán văn bản", "Tải file PDF"])
        
        if option == "Dán văn bản":
            raw_text = st.text_area("Dán nội dung:", height=300)
            if st.button("Dịch văn bản 🚀"):
                if raw_text.strip():
                    text_to_translate = raw_text
                    input_label = "Văn bản dán"
                else: st.warning("Hãy dán nội dung.")
        else:
            file = st.file_uploader("Chọn PDF (160MB+ ok)", type=["pdf"])
            if file:
                try:
                    reader = PdfReader(file)
                    total = len(reader.pages)
                    st.success(f"Tài liệu: {total} trang")
                    c1, c2 = st.columns(2)
                    start = c1.number_input("Từ trang:", 1, total, 1)
                    end = c2.number_input("Đến trang:", 1, total, min(5, total))
                    
                    if st.button("Dịch PDF 🚀"):
                        with st.spinner("Đang trích xuất chữ..."):
                            extracted = ""
                            for i in range(start - 1, end):
                                extracted += reader.pages[i].extract_text() + "\n"
                            if extracted.strip():
                                text_to_translate = extracted
                                input_label = f"{file.name} (P{start}-{end})"
                            else: st.error("Không thấy chữ trong PDF.")
                except Exception as e: st.error(f"Lỗi PDF: {e}")

    # --- XỬ LÝ DỊCH AI ---
    if text_to_translate:
        try:
            with st.spinner("AI đang dịch..."):
                model = genai.GenerativeModel(model_name=model_name)
                prompt = f"Dịch đoạn sau sang {target_lang}. Chỉ trả về bản dịch:\n\n{text_to_translate}"
                response = model.generate_content(prompt)
                
                st.session_state.current_res = response.text
                st.session_state.history.append({"name": input_label, "content": response.text})
                st.balloons()
        except Exception as e:
            st.error(f"Lỗi: {e}")

    # --- 4. HIỂN THỊ KẾT QUẢ & XUẤT FILE ---
    with col2:
        st.subheader("📝 Kết quả")
        if st.session_state.current_res:
            st.text_area("Bản dịch:", st.session_state.current_res, height=450)
            st.write("📥 **Tải về bản dịch:**")
            
            # Xuất .docx
            doc = Document()
            doc.add_paragraph(st.session_state.current_res)
            bio = io.BytesIO()
            doc.save(bio)
            st.download_button("Tải file Word (.docx)", bio.getvalue(), "dich.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
            # Xuất .txt
            st.download_button("Tải file Text (.txt)", st.session_state.current_res, "dich.txt", "text/plain")
        else:
            st.info("Kết quả sẽ hiện ở đây.")
else:
    st.info("Vui lòng nhập API Key ở bên trái.")
