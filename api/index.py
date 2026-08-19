import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
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
)

def cleanup_temp_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

@app.get("/")
def home():
    return {"status": "online", "engine": "ToolifyHub Python Backend Live"}

@app.post("/convert/pdf-to-docx")
def convert_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    temp_dir = tempfile.mkdtemp()
    input_pdf = os.path.join(temp_dir, "input.pdf")
    output_docx = os.path.join(temp_dir, "output.docx")

    try:
        # 1. Fast stream write
        with open(input_pdf, "wb") as f:
            f.write(file.file.read())

        # 2. Optimized Converter with layout precision
        cv = Converter(input_pdf)
        
        # multi_processing=True conversion speed ko 2x-3x fast kar deta hai
        cv.convert(output_docx, start=0, end=None, multi_processing=True, cpu_count=2)
        cv.close()

        if not os.path.exists(output_docx):
            raise HTTPException(status_code=500, detail="Conversion failed to generate file")

        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        clean_name = os.path.splitext(file.filename)[0]
        return FileResponse(
            path=output_docx,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{clean_name}.docx",
            headers={"Access-Control-Allow-Origin": "*"}
        )

    except Exception as e:
        cleanup_temp_dir(temp_dir)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={"Access-Control-Allow-Origin": "*"}
        )
