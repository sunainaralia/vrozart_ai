import fitz  # PyMuPDF for PDF
from docx import Document as DocxDocument  # python-docx for DOCX
from fastapi import UploadFile
import io

async def extract_text_from_file(file: UploadFile) -> str:
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return await extract_pdf(file)
    elif filename.endswith(".docx"):
        return await extract_docx(file)
    elif filename.endswith(".txt"):
        return await extract_txt(file)
    else:
        raise ValueError("Unsupported file format. Only PDF, DOCX, and TXT supported.")

async def extract_pdf(file: UploadFile) -> str:
    contents = await file.read()
    doc = fitz.open(stream=contents, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

async def extract_docx(file: UploadFile) -> str:
    contents = await file.read()
    docx = DocxDocument(io.BytesIO(contents))
    return "\n".join([para.text for para in docx.paragraphs]).strip()

async def extract_txt(file: UploadFile) -> str:
    contents = await file.read()
    return contents.decode("utf-8").strip()
