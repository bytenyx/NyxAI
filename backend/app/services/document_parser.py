import os
import tempfile
from typing import Tuple

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024


def is_allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def parse_pdf(file_path: str) -> str:
    try:
        import PyPDF2

        text = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text())
        return "\n".join(text)
    except ImportError:
        return ""
    except Exception as e:
        raise ValueError(f"PDF解析失败: {str(e)}")


def parse_docx(file_path: str) -> str:
    try:
        from docx import Document

        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        return ""
    except Exception as e:
        raise ValueError(f"DOCX解析失败: {str(e)}")


def parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_document(file_path: str, filename: str) -> Tuple[str, str]:
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        content = parse_pdf(file_path)
    elif ext in [".doc", ".docx"]:
        content = parse_docx(file_path)
    elif ext == ".txt":
        content = parse_txt(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

    return content, ext
