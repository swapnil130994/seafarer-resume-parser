from pathlib import Path
import os,tempfile
from fastapi import FastAPI,UploadFile,File,HTTPException
from .extractor import extract_text
from .seafarer_parser import parse_resume
app=FastAPI(title="Seafarer Crew Resume Parser",version="1.1.0")
ALLOWED={".pdf",".docx",".jpg",".jpeg",".png",".webp"}; MAX_FILE_SIZE=15*1024*1024
@app.get("/")
def root():return {"status":"ok","service":"Seafarer Crew Resume Parser","version":"1.1.0"}
@app.get("/health")
def health():return {"status":"healthy"}
@app.post("/parse")
async def parse(file:UploadFile=File(...)):
    filename=file.filename or ""; ext=Path(filename).suffix.lower()
    if ext not in ALLOWED: raise HTTPException(400,"Allowed: PDF, DOCX, JPG, JPEG, PNG, WEBP. Convert old DOC to DOCX/PDF.")
    data=await file.read()
    if len(data)>MAX_FILE_SIZE: raise HTTPException(413,"Maximum file size is 15 MB.")
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(delete=False,suffix=ext) as f:f.write(data);tmp=f.name
        text,ocr=extract_text(tmp)
        if len(text.strip())<20:raise HTTPException(422,"Could not extract readable text from this resume.")
        result=parse_resume(text,filename)
        result["_meta"]={"ocr_used":ocr,"extracted_text_length":len(text),"parser":"PyMuPDF/pdfplumber + python-docx + Tesseract + custom seafarer rules"}
        return result
    finally:
        if tmp and os.path.exists(tmp):os.remove(tmp)
