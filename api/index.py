import os
import shutil
import tempfile
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

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
    return {"status": "online", "engine": "ToolifyHub High-Fidelity Engine Live"}

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

        # Total pages count check
        doc = fitz.open(input_pdf)
        total_pages = len(doc)
        doc.close()

        # High-Fidelity Layout Converter
        cv = Converter(input_pdf)
        
        # Single-process sequential stream (Stable for cloud containers)
        cv.convert(
            output_docx,
            start=0,
            end=total_pages,
            multi_processing=False,
            cpu_count=1
        )
        cv.close()

        if not os.path.exists(output_docx):
            cleanup_temp_dir(temp_dir)
            return JSONResponse(status_code=500, content={"error": "Failed to create DOCX file"})

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
