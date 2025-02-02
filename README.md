# Einnahmenbeleg Generator

Der Einnahmenbeleg Generator ist ein Open-Source Python-Projekt, mit dem du Einnahmenbelege für ein ganzes Jahr automatisch erstellen kannst. Dabei können die Belege entweder einzeln oder zu einem einzigen PDF-Dokument zusammengeführt werden.

## Features

- **PDF-Generierung:** Erstelle einzelne PDFs oder ein zusammengeführtes PDF für das ganze Jahr.
- **Konfigurationsdatei:** Speichert die Eingaben automatisch in einer `config.yml`.
- **Rate Limiting:** Eingebautes Rate Limiting (10 Requests/Minute pro IP), um Missbrauch zu verhindern.
- **Modernes Logging:** Das Projekt nutzt [Loguru](https://github.com/Delgan/loguru) für umfangreiches und modernes Logging.
- **Docker-Unterstützung:** Dank des beiliegenden Dockerfiles kannst du die Anwendung in einem Container starten.

## Nutzung

### Lokale Ausführung

1. **Klonen des Repositories:**

   ```bash
   git clone https://github.com/dein-nutzername/einnahmenbeleg-generator.git
   cd einnahmenbeleg-generator
   ```

2. **Virtuelle Umgebung erstellen und aktivieren:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

3. **Abhängigkeiten installieren:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Anwendung starten:**

   ```bash
   python main.py
   ```

   Die Anwendung läuft nun unter [http://localhost:8000](http://localhost:8000).

### Ausführung mit Docker

1. **Image bauen:**

   ```bash
   docker build -t einnahmenbeleg-generator .
   ```

2. **Container starten:**

   ```bash
   docker run -p 8000:8000 einnahmenbeleg-generator
   ```

   Anschließend ist die Anwendung unter [http://localhost:8000](http://localhost:8000) erreichbar.

### Tests ausführen

Um die Tests zu starten, führe im Root-Verzeichnis folgenden Befehl aus:

```bash
pytest
```

## Hinweise zur Nutzung

- **Flexibilität:** Es müssen nicht alle Felder ausgefüllt werden; der Benutzer hat die Wahl, welche Informationen eingegeben werden.
- **Modulare Erzeugung:** Bei Auswahl "Ganzes Jahr" werden automatisch 12 Belege erstellt, mit der jeweiligen Monatsbezeichnung im Verwendungszweck.
- **Config-Datei:** Zusätzlich wird eine `config.yml` erzeugt, in der die Eingaben als Konfiguration gespeichert werden.

## Disclaimer

Dieses Projekt wird "as is" bereitgestellt.  

**Wichtig:**  
Ich übernehme keinerlei Haftung für etwaige Schäden oder Verluste, die durch die Nutzung dieses Programms entstehen könnten. Die Anwendung dient ausschließlich der Unterstützung und wurde ohne Gewährleistung hinsichtlich Fehlerfreiheit oder Vollständigkeit entwickelt.

## Lizenz

Dieses Projekt ist Open Source und steht unter der [MIT Lizenz](LICENSE).

---

Viel Spaß bei der Nutzung des Generators!
