#!/usr/bin/env python3
"""
InvoiceGenerator.py

Diese Datei stellt zwei Möglichkeiten zur Erstellung von PDFs bereit:
1. Eine responsive Website, über die die Felder eingegeben werden können.
2. Eine CLI-Option, die eine YAML-Konfigurationsdatei einliest.

Die PDF-Erstellung erfolgt über die pdfrw-Bibliothek und basiert auf der Vorlage 
aus 'Einnahmbeleg.pdf'. Die Felder werden in die entsprechenden PDF-Annotierungen 
eingetragen.

Erweiterungen in dieser Version:
- PDFs werden in einem temporären Ordner erstellt und als Download (einzelnes PDF oder ZIP) 
  zur Verfügung gestellt.
- Möglichkeit zur Konkatinierung der PDFs (bei "Ganzes Jahr" und aktiver "PDF zusammenführen" Checkbox).
"""

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import pdfrw
import uvicorn
import yaml
import sys
import os
import tempfile
import zipfile
from io import BytesIO

# Liste der benötigten Felder
FIELDS = [
    'Beleg Nummer', 'Brutto', 'MwSatz', 'Mwst', 'Netto', 
    'Betrag in Worten', 'Zahlung von', 'Jahr', 'Ort', 'Kontierung', 'Verwendungszweck'
]

# Monatsabkürzungen in der korrekten Reihenfolge
MONTHS = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez']

# Initialisiere FastAPI und stelle die Templates bereit
app = FastAPI()
templates = Jinja2Templates(directory="templates")

def create_base_template(template_pdf, data):
    """
    Aktualisiert die Basiseinträge in der PDF-Vorlage.

    :param template_pdf: PDF-Vorlage (pdfrw.PdfReader-Objekt)
    :param data: Dictionary mit den Eingabedaten
    """
    # Setze das gleiche Feld an mehreren Annotation-Positionen
    template_pdf.Root.Pages.Kids[0].Annots[0].update(pdfrw.PdfDict(V=data['Beleg Nummer']))
    template_pdf.Root.Pages.Kids[0].Annots[10].update(pdfrw.PdfDict(V=data['Beleg Nummer']))

    template_pdf.Root.Pages.Kids[0].Annots[1].update(pdfrw.PdfDict(V=data['Brutto']))
    template_pdf.Root.Pages.Kids[0].Annots[11].update(pdfrw.PdfDict(V=data['Brutto']))

    template_pdf.Root.Pages.Kids[0].Annots[2].update(pdfrw.PdfDict(V=data['MwSatz']))
    template_pdf.Root.Pages.Kids[0].Annots[12].update(pdfrw.PdfDict(V=data['MwSatz']))

    template_pdf.Root.Pages.Kids[0].Annots[3].update(pdfrw.PdfDict(V=data['Mwst']))
    template_pdf.Root.Pages.Kids[0].Annots[13].update(pdfrw.PdfDict(V=data['Mwst']))

    template_pdf.Root.Pages.Kids[0].Annots[4].update(pdfrw.PdfDict(V=data['Netto']))
    template_pdf.Root.Pages.Kids[0].Annots[14].update(pdfrw.PdfDict(V=data['Netto']))

    template_pdf.Root.Pages.Kids[0].Annots[5].update(pdfrw.PdfDict(V=data['Betrag in Worten']))
    template_pdf.Root.Pages.Kids[0].Annots[15].update(pdfrw.PdfDict(V=data['Betrag in Worten']))

    template_pdf.Root.Pages.Kids[0].Annots[6].update(pdfrw.PdfDict(V=data['Zahlung von']))
    template_pdf.Root.Pages.Kids[0].Annots[16].update(pdfrw.PdfDict(V=data['Zahlung von']))

    template_pdf.Root.Pages.Kids[0].Annots[9].update(pdfrw.PdfDict(V=data['Kontierung']))
    template_pdf.Root.Pages.Kids[0].Annots[19].update(pdfrw.PdfDict(V=data['Kontierung']))

def generate_invoice_files(data, ganzes_jahr, output_dir, concat=False):
    """
    Generiert die PDF Dateien im output_dir.
    
    :param data: Dictionary mit den Feldern.
    :param ganzes_jahr: Boolean, ob für das ganze Jahr (alle Monate) oder nur eine Rechnung.
    :param output_dir: Pfad des Ausgabeordners.
    :param concat: Boolean, ob bei Ganzes Jahr alle PDFs zu einer zusammengeführt werden sollen.
    :return: Liste der Pfade zu den generierten Dateien.
    """
    if ganzes_jahr:
        if concat:
            pages = []
            counter = 1
            # Erstelle für jeden Monat eine einzelne Seite und füge sie zusammen.
            for month in MONTHS:
                template_pdf = pdfrw.PdfReader('Einnahmbeleg.pdf')
                create_base_template(template_pdf, data)
                month_text = f"{data['Verwendungszweck']} {month} {data['Jahr']}"
                template_pdf.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=month_text))
                template_pdf.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=month_text))
                ort_text = f"{data['Ort']}/ 1.{counter}.{data['Jahr']}"
                template_pdf.Root.Pages.Kids[0].Annots[8].update(pdfrw.PdfDict(V=ort_text))
                template_pdf.Root.Pages.Kids[0].Annots[18].update(pdfrw.PdfDict(V=ort_text))
                pages.append(template_pdf.pages[0])
                counter += 1
            combined_pdf_path = os.path.join(output_dir, f"{data['Zahlung von']}{data['Jahr']}_combined.pdf")
            writer = pdfrw.PdfWriter()
            writer.addpages(pages)
            writer.write(combined_pdf_path)
            return [combined_pdf_path]
        else:
            files = []
            counter = 1
            for idx, month in enumerate(MONTHS):
                template_pdf = pdfrw.PdfReader('Einnahmbeleg.pdf')
                create_base_template(template_pdf, data)
                month_text = f"{data['Verwendungszweck']} {month} {data['Jahr']}"
                template_pdf.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=month_text))
                template_pdf.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=month_text))
                ort_text = f"{data['Ort']}/ 1.{counter}.{data['Jahr']}"
                template_pdf.Root.Pages.Kids[0].Annots[8].update(pdfrw.PdfDict(V=ort_text))
                template_pdf.Root.Pages.Kids[0].Annots[18].update(pdfrw.PdfDict(V=ort_text))
                file_path = os.path.join(output_dir, f"{data['Zahlung von']}{data['Jahr']}_{month}.pdf")
                pdfrw.PdfWriter().write(file_path, template_pdf)
                files.append(file_path)
                counter += 1
            return files
    else:
        file_path = os.path.join(output_dir, f"{data['Zahlung von']}{data['Jahr']}.pdf")
        template_pdf = pdfrw.PdfReader('Einnahmbeleg.pdf')
        create_base_template(template_pdf, data)
        template_pdf.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=data['Verwendungszweck']))
        template_pdf.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=data['Verwendungszweck']))
        pdfrw.PdfWriter().write(file_path, template_pdf)
        return [file_path]

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    """
    Zeigt das Eingabeformular der Webseite an.
    """
    return templates.TemplateResponse("form.html", {"request": request, "fields": FIELDS})

@app.post("/generate")
async def generate(request: Request, background_tasks: BackgroundTasks):
    """
    Verarbeitet die Formulareingaben aus der Website, erzeugt die PDF(s) in einem temporären Ordner, 
    verpackt sie bei Bedarf in einem ZIP oder führt sie zusammen und stellt sie zum Download bereit.
    """
    form_data = await request.form()
    # Erstelle das Daten-Dictionary anhand der vorgegebenen Felder
    data = {}
    for field in FIELDS:
        data[field] = form_data.get(field, "")
    ganzes_jahr = form_data.get("Ganzes Jahr") == "on"
    pdf_concat = form_data.get("PDF zusammenführen") == "on"
    
    # Erzeuge ein temporäres Verzeichnis und generiere die PDFs darin
    with tempfile.TemporaryDirectory() as tmpdirname:
        files = generate_invoice_files(data, ganzes_jahr, tmpdirname, concat=pdf_concat)
        
        # Falls mehrere Dateien vorliegen, packe sie in ein ZIP (sofern nicht zusammengeführt)
        if len(files) > 1:
            zip_path = os.path.join(tmpdirname, f"{data['Zahlung von']}{data['Jahr']}_Rechnungen.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Füge die Dateien in der korrekten Reihenfolge anhand von MONTHS hinzu
                for month in MONTHS:
                    for fpath in files:
                        if month in fpath:
                            zipf.write(fpath, os.path.basename(fpath))
                            break
            response_file_path = zip_path
            media_type = "application/zip"
            filename = os.path.basename(zip_path)
        else:
            response_file_path = files[0]
            media_type = "application/pdf" if response_file_path.endswith('.pdf') else "application/octet-stream"
            filename = os.path.basename(response_file_path)
        
        # Lese die zu sendende Datei als Bytes in den Speicher
        with open(response_file_path, "rb") as f:
            file_bytes = f.read()
        
        return StreamingResponse(BytesIO(file_bytes), media_type=media_type,
                                 headers={"Content-Disposition": f"attachment; filename={filename}"})

if __name__ == "__main__":
    # Bei CLI-Nutzung (YAML-Config) wird im aktuellen Verzeichnis gearbeitet.
    if len(sys.argv) > 2 and sys.argv[1] == "--config":
        config_file = sys.argv[2]
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        ganzes_jahr = config_data.get("Ganzes Jahr", False)
        # Beim CLI-Modus wird keine Zusammenführung unterstützt (concat=False)
        generate_invoice_files(config_data, ganzes_jahr, os.getcwd(), concat=False)
        print("Dokumente erfolgreich erstellt.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)

