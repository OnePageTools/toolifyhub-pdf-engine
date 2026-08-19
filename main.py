import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

app = FastAPI()

# Frontend se call allow karne ke liye CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def cleanup_files(temp_dir: str):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/")
def health_check():
    return {"status": "online", "message": "PDF to DOCX Engine is Running"}

@app.post("/convert")
def convert_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sirf PDF file upload karein.")

    temp_dir = tempfile.mkdtemp()
    input_pdf = os.path.join(temp_dir, "input.pdf")
    output_docx = os.path.join(temp_dir, "output.docx")

    try:
        # File save karein
        with open(input_pdf, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # PDF ko complete Word file me convert karein
        cv = Converter(input_pdf)
        cv.convert(output_docx, start=0, end=None)
        cv.close()

        # Download complete hone ke baad background me temp folder delete karein
        background_tasks.add_task(cleanup_files, temp_dir)

        clean_name = os.path.splitext(file.filename)[0]
        return FileResponse(
            path=output_docx,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{clean_name}.docx"
        )
    except Exception as e:
        cleanup_files(temp_dir)
        raise HTTPException(status_code=500, detail=str(e))
