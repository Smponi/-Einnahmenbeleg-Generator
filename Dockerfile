# Verwende ein schlankes, sicheres Python Alpine Image
FROM python:3.11-alpine

# Erstelle einen nicht-root Benutzer
RUN adduser -D appuser

# Installiere notwendige Build-Abhängigkeiten
RUN apk add --no-cache gcc musl-dev

WORKDIR /app

# Kopiere Abhängigkeitsdateien und installiere diese
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Anwendungscode, Templates und die PDF-Vorlage
COPY app/ app/
COPY templates/ templates/
COPY Einnahmbeleg.pdf .

EXPOSE 8000

# Wechsel zum nicht-root Benutzer
USER appuser

CMD ["python", "app/main.py"] 