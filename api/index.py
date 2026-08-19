import os
import shutil
import tempfile
import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def cleanup_temp_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

@app.get("/")
def home():
    return {"status": "online", "engine": "ToolifyHub High-Speed Engine"}

@app.post("/convert/pdf-to-docx")
def convert_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF allowed"})

    temp_dir = tempfile.mkdtemp()
    input_pdf = os.path.join(temp_dir, "input.pdf")
    output_docx = os.path.join(temp_dir, "output.docx")

    try:
        with open(input_pdf, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # High-Speed Engine using PyMuPDF + python-docx
        doc = fitz.open(input_pdf)
        word_doc = Document()

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            # Page content write karein
            for line in text.split("\n"):
                clean_line = line.strip()
                if clean_line:
                    p = word_doc.add_paragraph(clean_line)
                    p.paragraph_format.space_after = Pt(4)

            # Agar agla page hai toh page break daalein
            if page_num < len(doc) - 1:
                word_doc.add_page_break()

        doc.close()
        word_doc.save(output_docx)

        background_tasks.add_task(cleanup_temp_dir, temp_dir)
        clean_name = os.path.splitext(file.filename)[0]

        return FileResponse(
            path=output_docx,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{clean_name}.docx",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )

    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return JSONResponse(status_code=500, content={"error": str(e)})
