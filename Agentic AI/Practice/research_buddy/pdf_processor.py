"""
- Methodology
- Experiment 
- Results
- Experiment
- Limitations
- Future possible work
"""

import requests

# We have the pdf_url in the Citation class 


def download_pdf(pdf_url: str, save_path: str):
    response = requests.get(pdf_url, timeout=30)
    response.raise_for_status

    with open(save_path, "wb") as f: # "wb" = download and save binary files like image, video, pdfs, audio
        f.write(response.content) 

    return save_path

### PDF parser 
import fitz

def pdf_extractor(pdf_path):
    doc = fitz.open(pdf_path)
    
    pages = []

    for page in doc:
        pages.append(page.get_text())

    return "\n".join(pages)

def chunk_text(text, chunk_size=2000):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i+chunk_size])
    return chunks


def pdf_processor(pdf_url):
    pdf_path = download_pdf(pdf_url)

    text = pdf_extractor(pdf_path)

    chunk = chunk_text(text)
    return {"text": text,   
            "chunk": chunk}