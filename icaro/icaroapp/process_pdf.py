import pdfplumber

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip():
            return None  # Manejo de error en caso de que el PDF no tenga texto
        return text
    except Exception as e:
        print(f"Error procesando el PDF: {e}")
        return None