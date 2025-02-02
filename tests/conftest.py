import os
import sys

# Füge den Root-Pfad dem sys.path hinzu, damit das "app"-Modul gefunden wird
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) 