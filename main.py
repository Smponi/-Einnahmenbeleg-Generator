import os
import re
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

REQUIRED_FIELDS = ['Brutto', 'Beleg Nummer', 'Jahr', 'Zahlung von']
MAX_FIELD_LENGTH = 200


def sanitize_filename_part(value: str) -> str:
    """Entfernt/ersetzt Zeichen, die in Dateinamen problematisch sind."""
    return re.sub(r'[^\w\-_. ]', '_', value)


def _error_html(message: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8"><title>Fehler</title>
<style>body{{font-family:Arial,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f7f7f7;}}
.box{{background:#fff;padding:2rem;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1);text-align:center;max-width:500px;}}
h2{{color:#dc3545;}}p{{color:#555;}}a{{color:#007BFF;}}</style></head>
<body><div class="box"><h2>Fehler</h2><p>{message}</p>
<p><a href="/">&#8592; Zurück zum Formular</a></p></div></body></html>"""


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
    # Nur Keys loggen, keine sensiblen Werte
    logger.info("Received POST /generate from IP: {} with fields: {}", client_ip, list(data.keys()))
    logger.debug("Options - Ganzes Jahr: {}, PDF zusammenführen: {}", ganzes_jahr, pdf_concat)

    # Längen-Validierung
    for field, value in data.items():
        if len(value) > MAX_FIELD_LENGTH:
            logger.warning("Field '{}' exceeds max length from IP: {}", field, client_ip)
            return HTMLResponse(
                content=_error_html(f"Feld &#39;{field}&#39; überschreitet die maximale Länge von {MAX_FIELD_LENGTH} Zeichen."),
                status_code=422,
            )

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            logger.debug("Created temporary directory: {}", tmpdirname)
            files = generate_invoice_files(data, ganzes_jahr, tmpdirname, concat=pdf_concat)
            logger.info("Invoice files generated: {}", len(files))
            config_path = write_config_yaml(data, tmpdirname)
            logger.info("Configuration YAML created at: {}", config_path)

            # Sanitierte Dateinamen-Bestandteile
            zahlung_von = sanitize_filename_part(data.get('Zahlung von', 'Rechnung'))
            jahr = sanitize_filename_part(data.get('Jahr', ''))

            if len(files) > 1 or (ganzes_jahr and not pdf_concat):
                zip_filename = f"{zahlung_von}{jahr}_Rechnungen.zip"
                zip_path = os.path.join(tmpdirname, zip_filename)
                logger.info("Creating ZIP archive")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file in files:
                        zipf.write(file, os.path.basename(file))
                    zipf.write(config_path, "config.yml")
                response_file_path = zip_path
                media_type = "application/zip"
                filename = zip_filename
                logger.info("ZIP archive created successfully")
            else:
                response_file_path = files[0]
                media_type = "application/pdf" if response_file_path.endswith('.pdf') else "application/octet-stream"
                filename = sanitize_filename_part(os.path.basename(response_file_path))
                logger.info("Single PDF ready for download")

            with open(response_file_path, "rb") as f:
                file_bytes = f.read()

        logger.info("Sending response file to client")
        return StreamingResponse(BytesIO(file_bytes), media_type=media_type,
                                 headers={"Content-Disposition": f"attachment; filename={filename}"})

    except Exception as e:
        logger.error("Error generating invoice: {}", e)
        return HTMLResponse(
            content=_error_html("Bei der PDF-Generierung ist ein Fehler aufgetreten. Bitte überprüfen Sie Ihre Eingaben."),
            status_code=500,
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
