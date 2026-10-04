# Seafarer Crew Resume Parser API

Core PHP 7.2 compatible client + Python FastAPI parser using only open-source libraries.

## Stack
FastAPI + PyMuPDF + pdfplumber + python-docx + Pillow + Tesseract OCR + dateparser + custom seafarer rules.

## Supported input
PDF, DOCX, JPG, JPEG, PNG, WEBP. Old .doc should be converted to DOCX/PDF.

## API
GET /health
POST /parse (multipart field name: file)

## Local run
Python 3.11+

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

Open http://127.0.0.1:8000/docs

## Render
Push this project to GitHub. In Render create a Web Service, connect the repository, choose Docker runtime and deploy. The Dockerfile uses Render's PORT variable.

API: https://YOUR-APP.onrender.com/parse

Test:
curl -X POST -F "file=@resume.pdf" https://YOUR-APP.onrender.com/parse

## Core PHP 7.2
Copy php70_client.php into your PHP project. Then:

require_once __DIR__ . '/php70_client.php';
$result = parseSeafarerResume(__DIR__.'/upload/resume.pdf','https://YOUR-APP.onrender.com/parse');
if($result['success']) { $data=$result['data']; print_r($data); }

The returned JSON contains personal_details, sea_experience, course_details and uploaded_file_name.

## Notes
- This is a rule-based parser, not an LLM. It is free but cannot guarantee 100% extraction from every possible CV layout.
- OCR is automatically used for scanned PDFs/images when normal PDF text extraction returns little text.
- Render free services can sleep and have ephemeral local storage. Do not use Render local disk as permanent resume storage.
- Save uploaded resumes on your PHP server/object storage if needed.
"# seafarer-resume-parser" 
