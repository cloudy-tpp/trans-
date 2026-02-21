import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- 1. KHỞI TẠO BỘ NHỚ APP (SESSION STATE) ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_res' not in st.session_state:
    st.session_state.current_res = ""

st.set_page_config(page_title="AI Translator Pro Max", layout="wide")

# --- 2. GIAO DIỆN THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("🔑 Cấu hình hệ thống")
    api_key = st.text_input("Nhập Gemini API Key:", type="password")
    model_name = st.selectbox("Chọn Model:", ["gemini-1.5-flash", "gemini-1.5-pro"])
    target_lang = st.selectbox("Ngôn ngữ đích:", ["Tiếng Việt", "English", "Chinese", "French", "Japanese", "Korean"])
    
    st.markdown("---")
    st.subheader("📜 Lịch sử dịch thuật")
    if not st.session_state.history:
        st.write("Chưa có bản lưu nào.")
    else:
        # Hiển thị lịch sử từ mới nhất đến cũ nhất
        for i, item in enumerate(reversed(st.session_state.history)):
            real_index = len(st.session_state.history) - 1 - i
            with st.expander(f"Bản dịch {real_index + 1}: {item['name']}"):
                st.write(f"**Nguồn:** {item['type']}")
                st.write(item['content'][:200] + "...")
                if st.button(f"Xem lại bản {real_index + 1}", key=f"rev_{real_index}"):
                    st.session_state.current_res = item['content']

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🌐 AI Translator Multi-Tool")
st.markdown("Hỗ trợ: Văn bản thuần túy và PDF lớn (160MB+).")

if api_key:
    genai.configure(api_key=api_key)
    col1, col2 = st.columns(2)

    # Biến trung gian để lưu dữ liệu cần dịch
    text_to_translate = ""
    input_label = ""
    input_type_label = ""

    with col1:
        st.subheader("📥 Đầu vào")
        option = st.radio("Chọn hình thức dịch:", ["Dán văn bản", "Tải file PDF"])
        
        if option == "Dán văn bản":
            raw_text = st.text_area("Nhập hoặc dán đoạn văn cần dịch:", height=300)
            if st.button("Dịch văn bản 🚀"):
                if raw_text.strip():
                    text_to_translate = raw_text
                    input_label = "Văn bản nhập tay"
                    input_type_label = "Văn bản"
                else:
                    st.warning("Vui lòng nhập nội dung trước.")

        else:
            uploaded_file = st.file_uploader("Chọn file PDF (Hỗ trợ file lớn)", type=["pdf"])
            if uploaded_file:
                try:
                    reader = PdfReader(uploaded_file)
                    total_pages = len(reader.pages)
                    st.success(f"Tài liệu: {total_pages} trang")
                    
                    st.info("💡 Mẹo: Với file >100MB, hãy dịch khoảng 5-10 trang mỗi lần.")
                    c1, c2 = st.columns(2)
                    start_p = c1.number_input("Từ trang:", min_value=1, max_value=total_pages, value=1)
                    end_p = c2.number_input("Đến trang:", min_value=1, max_value=total_pages, value=min(5, total_pages))
                    
                    if st.button("Trích xuất và Dịch PDF 🚀"):
                        with st.spinner("Đang đọc nội dung PDF..."):
                            extracted_content = ""
                            for i in range(start_p - 1, end_p):
                                page_text = reader.pages[i].extract_text()
                                if page_text:
                                    extracted_content += page_text + "\n"
                            
                            if extracted_content.strip():
                                text_to_translate = extracted_content
                                input_label = f"{uploaded_file.name} (Trang {start_p}-{end_p})"
                                input_type_label = "File PDF"
                            else:
                                st.error("Không tìm thấy chữ trong các trang này (có thể là ảnh scan).")
                except Exception as e:
                    st.error(f"Lỗi đọc PDF: {e}")

    # --- 4. XỬ LÝ DỊCH THUẬT QUA AI ---
    if text_to_translate:
        try:
            with st.spinner("AI đang dịch..."):
                model = genai.GenerativeModel(model_name)
                prompt = f"Bạn là dịch giả chuyên nghiệp. Hãy dịch đoạn văn sau sang {target_lang}. Chỉ trả về nội dung đã dịch:\n\n{text_to_translate}"
                response = model.generate_content(prompt)
                
                # Cập nhật kết quả hiện tại
                st.session_state.current_res = response.text
                
                # Lưu vào lịch sử
                st.session_state.history.append({
                    "name": input_label,
                    "type": input_type_label,
                    "content": response.text
                })
                st.balloons()
        except Exception as e:
            st.error(f"Lỗi AI: {e}")

    # --- 5. HIỂN THỊ KẾT QUẢ (CỘT 2) ---
    with col2:
        st.subheader("📝 Kết quả bản dịch")
        if st.session_state.current_res:
            st.text_area("Nội dung dịch:", st.session_state.current_res, height=500)
            
            # Tạo file Word để tải về
            try:
                doc = Document()
                doc.add_paragraph(st.session_state.current_res)
                bio = io.BytesIO()
                doc.save(bio)
                
                st.download_button(
                    label="📥 Tải về file Word (.docx)",
                    data=bio.getvalue(),
                    file_name=f"ban_dich_{target_lang}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Lỗi tạo file Word: {e}")
        else:
            st.info("Bản dịch sẽ hiển thị ở đây.")

else:
    st.warning("Vui lòng nhập Gemini API Key ở thanh bên trái để sử dụng app.")
