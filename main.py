import os
import sys
import tempfile
import zipfile
from io import BytesIO

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.pdf_generator import generate_invoice_files, write_config_yaml
from app.rate_limiter import RateLimitMiddleware

# Setup loguru logger to log to stdout with DEBUG level.
logger.remove()
logger.add(sys.stdout, level="DEBUG")

app = FastAPI()

# Füge die Rate-Limiting-Middleware hinzu (max. 10 Requests/Minute pro IP)
app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=60)

templates = Jinja2Templates(directory="templates")

FIELDS = [
    'Beleg Nummer', 'Brutto', 'MwSatz', 'Mwst', 'Netto', 
    'Betrag in Worten', 'Zahlung von', 'Jahr', 'Ort', 'Kontierung', 'Verwendungszweck'
]

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    """
    Zeigt das Eingabeformular der Webseite an.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info("Received GET request for form page from IP: {}", client_ip)
    return templates.TemplateResponse("form.html", {"request": request, "fields": FIELDS})

@app.post("/generate")
async def generate(request: Request):
    """
    Liest die Formulareingaben, generiert die PDFs (alle einzeln oder zusammengeführt),
    speichert zusätzlich die Eingaben als config.yml und liefert alles als Download zurück.
    """
    form_data = await request.form()
    data = {field: form_data.get(field, "") for field in FIELDS}
    ganzes_jahr = form_data.get("Ganzes Jahr") == "on"
    pdf_concat = form_data.get("PDF zusammenführen") == "on"
    
    client_ip = request.client.host if request.client else "unknown"
    logger.info("Received POST /generate request from IP: {} with data: {}", client_ip, data)
    logger.debug("Options selected - Ganzes Jahr: {}, PDF zusammenführen: {}", ganzes_jahr, pdf_concat)

    with tempfile.TemporaryDirectory() as tmpdirname:
        logger.debug("Created temporary directory: {}", tmpdirname)
        # Erzeuge die (PDF-)Dateien
        files = generate_invoice_files(data, ganzes_jahr, tmpdirname, concat=pdf_concat)
        logger.info("Invoice files generated: {}", files)
        # Schreibe die config.yml
        config_path = write_config_yaml(data, tmpdirname)
        logger.info("Configuration YAML created at: {}", config_path)

        if len(files) > 1 or (ganzes_jahr and not pdf_concat):
            # Packe alle Dateien (PDFs + config.yml) in ein ZIP-Archiv
            zip_filename = f"{data.get('Zahlung von','Rechnung')}{data.get('Jahr','')}_Rechnungen.zip"
            zip_path = os.path.join(tmpdirname, zip_filename)
            logger.info("Creating ZIP archive: {}", zip_path)
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in files:
                    logger.debug("Adding file to ZIP: {}", file)
                    zipf.write(file, os.path.basename(file))
                zipf.write(config_path, "config.yml")
            response_file_path = zip_path
            media_type = "application/zip"
            filename = os.path.basename(zip_path)
            logger.info("ZIP archive created successfully")
        else:
            response_file_path = files[0]
            media_type = "application/pdf" if response_file_path.endswith('.pdf') else "application/octet-stream"
            filename = os.path.basename(response_file_path)
            logger.info("Single PDF ready for download: {}", response_file_path)

        with open(response_file_path, "rb") as f:
            file_bytes = f.read()

        logger.info("Sending response file: {} to client", filename)
        return StreamingResponse(BytesIO(file_bytes), media_type=media_type,
                                 headers={"Content-Disposition": f"attachment; filename={filename}"})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)