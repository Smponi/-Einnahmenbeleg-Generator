import os
import pdfrw
import yaml
from loguru import logger

# Reihenfolge der Monate, in der auch gemerged werden soll
MONTHS = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez']

def create_base_template(template_pdf, data):
    """
    Aktualisiert die Standardfelder in der PDF-Vorlage.
    """
    logger.debug("Updating base template with data: {}", data)
    template_pdf.Root.Pages.Kids[0].Annots[0].update(pdfrw.PdfDict(V=data.get('Beleg Nummer', '')))
    template_pdf.Root.Pages.Kids[0].Annots[10].update(pdfrw.PdfDict(V=data.get('Beleg Nummer', '')))
    
    template_pdf.Root.Pages.Kids[0].Annots[1].update(pdfrw.PdfDict(V=data.get('Brutto', '')))
    template_pdf.Root.Pages.Kids[0].Annots[11].update(pdfrw.PdfDict(V=data.get('Brutto', '')))
    
    template_pdf.Root.Pages.Kids[0].Annots[2].update(pdfrw.PdfDict(V=data.get('MwSatz', '')))
    template_pdf.Root.Pages.Kids[0].Annots[12].update(pdfrw.PdfDict(V=data.get('MwSatz', '')))
    
    template_pdf.Root.Pages.Kids[0].Annots[3].update(pdfrw.PdfDict(V=data.get('Mwst', '')))
    template_pdf.Root.Pages.Kids[0].Annots[13].update(pdfrw.PdfDict(V=data.get('Mwst', '')))
    
    template_pdf.Root.Pages.Kids[0].Annots[4].update(pdfrw.PdfDict(V=data.get('Netto', '')))
    template_pdf.Root.Pages.Kids[0].Annots[14].update(pdfrw.PdfDict(V=data.get('Netto', '')))
    
    template_pdf.Root.Pages.Kids[0].Annots[5].update(pdfrw.PdfDict(V=data.get('Betrag in Worten', '')))
    template_pdf.Root.Pages.Kids[0].Annots[15].update(pdfrw.PdfDict(V=data.get('Betrag in Worten', '')))
    
    template_pdf.Root.Pages.Kids[0].Annots[6].update(pdfrw.PdfDict(V=data.get('Zahlung von', '')))
    template_pdf.Root.Pages.Kids[0].Annots[16].update(pdfrw.PdfDict(V=data.get('Zahlung von', '')))
    
    template_pdf.Root.Pages.Kids[0].Annots[9].update(pdfrw.PdfDict(V=data.get('Kontierung', '')))
    template_pdf.Root.Pages.Kids[0].Annots[19].update(pdfrw.PdfDict(V=data.get('Kontierung', '')))

def generate_single_invoice(data, output_dir):
    """
    Generiert eine einzelne PDF (für die nicht-"Ganzes Jahr"-Variante).
    """
    output_file = os.path.join(output_dir, f"{data.get('Zahlung von', 'Rechnung')}{data.get('Jahr', '')}.pdf")
    logger.info("Generating single invoice: {}", output_file)
    template_pdf = pdfrw.PdfReader('Einnahmbeleg.pdf')
    create_base_template(template_pdf, data)
    template_pdf.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=data.get('Verwendungszweck', '')))
    template_pdf.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=data.get('Verwendungszweck', '')))
    pdfrw.PdfWriter().write(output_file, template_pdf)
    logger.debug("Single invoice generated successfully at {}", output_file)
    return output_file

def generate_individual_invoices(data, output_dir):
    """
    Erzeugt 12 PDFs (eine pro Monat) und gibt ein Dictionary zurück, in dem jedem Monat der zugehörige Dateipfad zugeordnet ist.
    """
    invoices = {}
    counter = 1
    logger.info("Generating individual invoices for each month")
    for month in MONTHS:
        template_pdf = pdfrw.PdfReader('Einnahmbeleg.pdf')
        create_base_template(template_pdf, data)
        month_text = f"{data.get('Verwendungszweck', '')} {month} {data.get('Jahr', '')}"
        template_pdf.Root.Pages.Kids[0].Annots[7].update(pdfrw.PdfDict(V=month_text))
        template_pdf.Root.Pages.Kids[0].Annots[17].update(pdfrw.PdfDict(V=month_text))
        ort_text = f"{data.get('Ort', '')}/ 1.{counter}.{data.get('Jahr', '')}"
        template_pdf.Root.Pages.Kids[0].Annots[8].update(pdfrw.PdfDict(V=ort_text))
        template_pdf.Root.Pages.Kids[0].Annots[18].update(pdfrw.PdfDict(V=ort_text))
        file_path = os.path.join(output_dir, f"{data.get('Zahlung von', 'Rechnung')}{data.get('Jahr','')}_{month}.pdf")
        pdfrw.PdfWriter().write(file_path, template_pdf)
        invoices[month] = file_path
        logger.debug("Invoice for {} generated at {}", month, file_path)
        counter += 1
    return invoices

def merge_pdfs_by_month(invoices_dict, output_dir, data):
    """
    Führt die 12 PDFs in der Reihenfolge der MONTHS zu einer einzigen PDF zusammen.
    """
    output_file = os.path.join(output_dir, f"{data.get('Zahlung von', 'Rechnung')}{data.get('Jahr', '')}_combined.pdf")
    logger.info("Merging individual invoices into one PDF: {}", output_file)
    writer = pdfrw.PdfWriter()
    for month in MONTHS:
        file_path = invoices_dict.get(month)
        if file_path and os.path.exists(file_path):
            pdf = pdfrw.PdfReader(file_path)
            if pdf.pages:
                writer.addpage(pdf.pages[0])
                logger.debug("Added page for month: {} from file: {}", month, file_path)
            else:
                logger.warning("No pages found in PDF for month: {}", month)
    writer.write(output_file)
    logger.info("Merged PDF created at {}", output_file)
    return output_file

def write_config_yaml(data, output_dir):
    """
    Schreibt die eingegebenen Felddaten als config.yml in den output_dir.
    """
    config_path = os.path.join(output_dir, "config.yml")
    logger.info("Writing configuration to YAML: {}", config_path)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
    logger.debug("Configuration data written: {}", data)
    return config_path

def generate_invoice_files(data, ganzes_jahr, output_dir, concat=False):
    """
    Generiert die PDF(s) entsprechend der Eingabedaten.
    
    Bei ganzes_jahr=True werden 12 PDFs erstellt. Ist concat aktiviert,
    werden diese zu einer einzigen PDF zusammengeführt.
    """
    logger.info("Generating invoice files with options - Ganzes Jahr: {}, PDF zusammenführen: {}", ganzes_jahr, concat)
    if ganzes_jahr:
        invoices_dict = generate_individual_invoices(data, output_dir)
        if concat:
            merged_pdf = merge_pdfs_by_month(invoices_dict, output_dir, data)
            logger.info("Returning merged PDF")
            return [merged_pdf]
        else:
            logger.info("Returning individual monthly invoices")
            # Rückgabe der einzelnen PDFs in der Reihenfolge der MONTHS
            return [invoices_dict[month] for month in MONTHS if month in invoices_dict]
    else:
        single_invoice = generate_single_invoice(data, output_dir)
        logger.info("Returning single invoice PDF")
        return [single_invoice]