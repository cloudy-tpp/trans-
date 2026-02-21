import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- 1. CẤU HÌNH BỘ NHỚ (SESSION STATE) ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = ""

st.set_page_config(page_title="AI Translator Pro Max", layout="wide")

# --- 2. HÀM XỬ LÝ XÓA LỊCH SỬ ---
def delete_history_item(index):
    st.session_state.history.pop(index)
    st.session_state.current_res = "" # Xóa hiển thị hiện tại để giải phóng RAM
    st.rerun()

def clear_all_history():
    st.session_state.history = []
    st.session_state.current_res = ""
    st.rerun()

# --- 3. THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cấu hình & Lịch sử")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    
    # Tự động quét Model để tránh lỗi 404
    model_choice = "gemini-1.5-flash"
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            available = [m.name.replace('models/', '') for m in models if 'generateContent' in m.supported_generation_methods]
            model_choice = st.selectbox("Chọn Model (Auto-scan):", available)
        except:
            model_choice = st.selectbox("Chọn Model mặc định:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])

    st.markdown("---")
    st.subheader("📜 Lịch sử lưu trữ")
    
    if st.session_state.history:
        if st.button("🗑️ Xóa toàn bộ lịch sử", use_container_width=True):
            clear_all_history()
            
        st.write("---")
        # Hiển thị danh sách lịch sử với nút Xem và Xóa
        for i, item in enumerate(st.session_state.history):
            col_h1, col_h2 = st.columns([4, 1])
            if col_h1.button(f"📄 {i+1}. {item['name'][:12]}...", key=f"v_{i}", use_container_width=True):
                st.session_state.current_res = item['content']
            if col_h2.button("🗑️", key=f"d_{i}", help="Xóa mục này"):
                delete_history_item(i)
    else:
        st.write("Chưa có bản lưu.")

# --- 4. GIAO DIỆN CHÍNH ---
st.title("🌐 AI Translator (Hỗ trợ PDF lớn & Quản lý bộ nhớ)")

if api_key:
    genai.configure(api_key=api_key)
    col1, col2 = st.columns(2)
    text_to_trans = ""
    input_label = ""

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Chọn hình thức:", ["Dán văn bản", "Tải file PDF"])
        
        if option == "Dán văn bản":
            raw = st.text_area("Nhập nội dung:", height=250)
            if st.button("Dịch văn bản 🚀"):
                if raw.strip():
                    text_to_trans = raw
                    input_label = "Văn bản dán"
                else: st.warning("Hãy nhập nội dung.")
        else:
            file = st.file_uploader("Chọn PDF (Hỗ trợ file 160MB+)", type=["pdf"])
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
                            for j in range(start - 1, end):
                                page_text = reader.pages[j].extract_text()
                                if page_text: extracted += page_text + "\n"
                            
                            if extracted.strip():
                                text_to_trans = extracted
                                input_label = f"{file.name} (P{start}-{end})"
                            else: st.error("Không tìm thấy chữ trong PDF.")
                except Exception as e: st.error(f"Lỗi PDF: {e}")

    # Xử lý AI
    if text_to_trans:
        try:
            with st.spinner("AI đang dịch..."):
                model = genai.GenerativeModel(model_name=f"models/{model_choice}" if "models/" not in model_choice else model_choice)
                prompt = f"Dịch sang {target_lang}. Chỉ trả về bản dịch:\n\n{text_to_trans}"
                response = model.generate_content(prompt)
                
                st.session_state.current_res = response.text
                st.session_state.history.append({"name": input_label, "content": response.text})
                st.balloons()
        except Exception as e:
            st.error(f"Lỗi AI: {e}")

    # --- 5. HIỂN THỊ KẾT QUẢ & XUẤT FILE ---
    with col2:
        st.subheader("📝 Kết quả")
        if st.session_state.current_res:
            st.text_area("Nội dung:", st.session_state.current_res, height=450)
            
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
            st.info("Bản dịch sẽ hiện ở đây.")
else:
    st.info("Vui lòng nhập API Key ở bên trái.")
