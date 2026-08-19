import os
import shutil
import tempfile
import traceback
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
    return {"status": "online", "engine": "ToolifyHub Python Backend Live"}

# Browser preflight bypass
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
def convert_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed."},
            headers={"Access-Control-Allow-Origin": "*"}
        )

    temp_dir = tempfile.mkdtemp()
    input_pdf = os.path.join(temp_dir, "input.pdf")
    output_docx = os.path.join(temp_dir, "output.docx")

    try:
        # 1. Write file directly from stream
        with open(input_pdf, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 2. Layout & Coordinate Aware Conversion (Serverless Safe)
        cv = Converter(input_pdf)
        
        # Serverless environment mein multi_processing=False hona zaroori hai
        # start=0, end=None sare pages ko sequential aur clean table flow me convert karega
        cv.convert(output_docx, start=0, end=None, multi_processing=False)
        cv.close()

        if not os.path.exists(output_docx):
            cleanup_temp_dir(temp_dir)
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to create DOCX output"},
                headers={"Access-Control-Allow-Origin": "*"}
            )

        # Background cleanup after file is sent
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
        print("CONVERSION CRASH LOG:", traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Conversion error: {str(e)}"},
            headers={"Access-Control-Allow-Origin": "*"}
        )
