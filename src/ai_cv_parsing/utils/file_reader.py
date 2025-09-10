import magic
from fastapi import HTTPException


async def read_and_validate_file(file):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    content = await file.read()
    
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="File is not a valid PDF")
    
    return content