import os
import tempfile
import pytest
import pdfrw
import yaml

from app.pdf_generator import (generate_invoice_files, merge_pdfs_by_month,
                               generate_individual_invoices, write_config_yaml)

# Dummy-Daten für Tests
TEST_DATA = {
    "Beleg Nummer": "INV-TEST",
    "Brutto": "1000",
    "MwSatz": "19%",
    "Mwst": "190",
    "Netto": "810",
    "Betrag in Worten": "Achthundertzehn",
    "Zahlung von": "TestFirma",
    "Jahr": "2023",
    "Ort": "TestOrt",
    "Kontierung": "12345",
    "Verwendungszweck": "TestRechnung"
}

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_single_invoice_generation(temp_dir):
    files = generate_invoice_files(TEST_DATA, ganzes_jahr=False, output_dir=temp_dir, concat=False)
    assert len(files) == 1
    assert os.path.exists(files[0])
    pdf = pdfrw.PdfReader(files[0])
    assert len(pdf.pages) >= 1

def test_individual_invoices_generation(temp_dir):
    files = generate_invoice_files(TEST_DATA, ganzes_jahr=True, output_dir=temp_dir, concat=False)
    assert len(files) == 12
    for file in files:
        assert os.path.exists(file)
        pdf = pdfrw.PdfReader(file)
        assert len(pdf.pages) >= 1

def test_merged_invoice_generation(temp_dir):
    files = generate_invoice_files(TEST_DATA, ganzes_jahr=True, output_dir=temp_dir, concat=True)
    # Es muss genau eine zusammengeführte PDF geben
    assert len(files) == 1
    merged_pdf = pdfrw.PdfReader(files[0])
    # Die zusammengeführte PDF sollte 12 Seiten enthalten
    assert len(merged_pdf.pages) == 12

def test_write_config_yaml(temp_dir):
    config_path = write_config_yaml(TEST_DATA, temp_dir)
    assert os.path.exists(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f)
    assert loaded == TEST_DATA
