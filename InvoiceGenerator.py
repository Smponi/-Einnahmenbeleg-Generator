#!/usr/bin/env python3
"""
InvoiceGenerator.py

Diese Datei stellt zwei Möglichkeiten zur Erstellung von PDFs bereit:
1. Eine responsive Website, über die die Felder eingegeben werden können.
2. Eine CLI-Option, die eine YAML-Konfigurationsdatei einliest.

Die PDF-Erstellung erfolgt über die pdfrw-Bibliothek und basiert auf der Vorlage 
aus 'Einnahmbeleg.pdf'. Die Felder werden in die entsprechenden PDF-Annotierungen 
eingetragen.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pdfrw
import uvicorn
import yaml
import sys

# Liste der benötigten Felder
FIELDS = [
    'Beleg Nummer', 'Brutto', 'MwSatz', 'Mwst', 'Netto', 
    'Betrag in Worten', 'Zahlung von', 'Jahr', 'Ort', 'Kontierung', 'Verwendungszweck'
]

# Monatsabkürzungen
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

def generate_invoice(data, ganzes_jahr):
    """
    Erzeugt PDF(s) basierend auf den übergebenen Daten.
    
    :param data: Dictionary mit den benötigten Feldern.
    :param ganzes_jahr: Boolean, ob Rechnungen für das ganze Jahr erstellt werden sollen.
    """
    if ganzes_jahr:
        counter = 1
        # Erstelle für jeden Monat eine eigene PDF
        for month in MONTHS:
            # Lese die Vorlage neu ein, um unbeeinflusste Bearbeitung zu gewährleisten
            template_pdf = pdfrw.PdfReader('Einnahmbeleg.pdf')
            create_base_template(template_pdf, data)
            # Aktualisiere den Verwendungszweck für den aktuellen Monat
            month_text = f"{data['Verwendungszweck']} {month} {data['Jahr']}"
            template_pdf.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=month_text))
            template_pdf.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=month_text))

            # Aktualisiere das Ortsfeld mit fortlaufender Nummerierung
            ort_text = f"{data['Ort']}/ 1.{counter}.{data['Jahr']}"
            template_pdf.Root.Pages.Kids[0].Annots[8].update(pdfrw.PdfDict(V=ort_text))
            template_pdf.Root.Pages.Kids[0].Annots[18].update(pdfrw.PdfDict(V=ort_text))

            # Erstelle den Dateinamen und schreibe die PDF
            file_name = f"{data['Zahlung von']}{data['Jahr']}{month}.pdf"
            pdfrw.PdfWriter().write(file_name, template_pdf)
            counter += 1
    else:
        # Für einzelne Rechnung(en)
        template_pdf = pdfrw.PdfReader('Einnahmbeleg.pdf')
        create_base_template(template_pdf, data)
        template_pdf.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=data['Verwendungszweck']))
        template_pdf.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=data['Verwendungszweck']))
        file_name = f"{data['Zahlung von']}{data['Jahr']}.pdf"
        pdfrw.PdfWriter().write(file_name, template_pdf)

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    """
    Zeigt das Eingabeformular der Webseite an.
    """
    return templates.TemplateResponse("form.html", {"request": request, "fields": FIELDS})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request):
    """
    Verarbeitet die Formulareingaben aus der Website und erzeugt die PDF(s).
    """
    form_data = await request.form()
    # Erstelle das Daten-Dictionary anhand der vorgegebenen Felder
    data = {}
    for field in FIELDS:
        data[field] = form_data.get(field, "")
    # Prüfe, ob das Kontrollkästchen 'Ganzes Jahr?' aktiviert wurde
    ganzes_jahr = form_data.get("Ganzes Jahr") == "on"
    
    # Generiere die Rechnung(en)
    generate_invoice(data, ganzes_jahr)
    
    # Rückmeldung an den Benutzer
    return templates.TemplateResponse("form.html", {"request": request, "fields": FIELDS, "message": "Dokumente erfolgreich erstellt."})

if __name__ == "__main__":
    # Wenn via CLI ein YAML-File angegeben wurde, wird dieser Modus genutzt.
    if len(sys.argv) > 2 and sys.argv[1] == "--config":
        config_file = sys.argv[2]
        # Einlesen der YAML-Konfiguration
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        # Lese das Feld "Ganzes Jahr" – Standard ist False
        ganzes_jahr = config_data.get("Ganzes Jahr", False)
        generate_invoice(config_data, ganzes_jahr)
        print("Dokumente erfolgreich erstellt.")
    else:
        # Starte den FastAPI-Webserver
        uvicorn.run(app, host="0.0.0.0", port=8000)

