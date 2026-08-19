import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
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

@app.get("/")
def home():
    return {"status": "online", "engine": "ToolifyHub Python Backend Live"}

@app.post("/convert/pdf-to-docx")
async def convert_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    temp_dir = tempfile.mkdtemp()
    input_pdf = os.path.join(temp_dir, "input.pdf")
    output_docx = os.path.join(temp_dir, "output.docx")

    with open(input_pdf, "wb") as f:
        f.write(await file.read())

    cv = Converter(input_pdf)
    cv.convert(output_docx, start=0, end=None)
    cv.close()

    clean_name = os.path.splitext(file.filename)[0]
    return FileResponse(
        output_docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"{clean_name}.docx"
    )
