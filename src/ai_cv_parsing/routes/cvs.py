from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from ..utils.file_reader import read_and_validate_file
from ..utils.pdf_extractor import extract_text_from_pdf

router = APIRouter(prefix="/cvs", tags=["CVS"])


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    content = await read_and_validate_file(file)

    # Extract text directly from PDF bytes
    extracted_text = extract_text_from_pdf(content)

    return JSONResponse(content={
        "message": "PDF uploaded successfully",
        "filename": file.filename,
        "size": len(content),
        "extracted_text": extracted_text
    })

