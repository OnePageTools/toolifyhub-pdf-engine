import os
import shutil
import tempfile
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
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
    return {"status": "online", "engine": "ToolifyHub Python Backend Live"}

@app.options("/{path:path}")
async def preflight_handler(path: str):
    return JSONResponse(
        content={"message": "ok"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/convert/pdf-to-docx")
def convert_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    start_page: int = Form(0),
    end_page: int = Form(None)
):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF allowed"},
            headers={"Access-Control-Allow-Origin": "*"}
        )

    temp_dir = tempfile.mkdtemp()
    input_pdf = os.path.join(temp_dir, "input.pdf")
    output_docx = os.path.join(temp_dir, "output.docx")

    try:
        with open(input_pdf, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # PDF total pages verify
        doc = fitz.open(input_pdf)
        total_pages = len(doc)
        doc.close()

        actual_end = end_page if (end_page is not None and end_page <= total_pages) else total_pages

        # Convert specific chunk quickly
        cv = Converter(input_pdf)
        cv.convert(output_docx, start=start_page, end=actual_end, multi_processing=False)
        cv.close()

        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        clean_name = os.path.splitext(file.filename)[0]
        return FileResponse(
            path=output_docx,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{clean_name}_chunk.docx",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Expose-Headers": "Content-Disposition",
            }
        )

    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={"Access-Control-Allow-Origin": "*"}
        )
