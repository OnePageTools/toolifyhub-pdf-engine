import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2docx import Converter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def cleanup_temp_dir(path: str):
    """File send hone ke baad temp folder delete karne ke liye"""
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)

@app.get("/")
def home():
    return {"status": "online", "engine": "ToolifyHub Python Backend Live"}

@app.post("/convert/pdf-to-docx")
def convert_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    # Temp folder create karein
    temp_dir = tempfile.mkdtemp()
    input_pdf = os.path.join(temp_dir, "input.pdf")
    output_docx = os.path.join(temp_dir, "output.docx")

    try:
        # File save karein
        with open(input_pdf, "wb") as f:
            f.write(file.file.read())

        # Conversion process
        cv = Converter(input_pdf)
        cv.convert(output_docx, start=0, end=None)
        cv.close()

        if not os.path.exists(output_docx):
            raise HTTPException(status_code=500, detail="Conversion failed to generate file")

        # Response deliver hone ke baad background mein cleanup chalana
        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        clean_name = os.path.splitext(file.filename)[0]
        return FileResponse(
            path=output_docx,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{clean_name}.docx"
        )

    except Exception as e:
        # Agar koi error aaye toh foran clean up karein
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")
