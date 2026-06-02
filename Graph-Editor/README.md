# VRP Graph Editor

Modularer Prototyp eines graphischen Editors für VRP-Instanzen mit PySide6 und NetworkX.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Start

```bash
python main.py
```

Alternativ:

```bash
python -m vrp_graph_editor
```

## Bedienung

- **Auswahl**: Knoten verschieben, Knoten/Kanten auswählen und Attribute rechts bearbeiten.
- **Knoten**: Linksklick auf freie Zeichenfläche erzeugt einen neuen Knoten.
- **Kante**: Zwei Knoten nacheinander anklicken, um eine Kante zu erzeugen.
- **Zoom**: Mausrad.
- **Pan**: mittlere oder rechte Maustaste gedrückt halten und ziehen.
- **Löschen**: Entf oder Backspace.
- **Speichern/Laden**: NetworkX Node-Link-JSON.

## Architektur

```text
vrp_graph_editor/
├── app/          # Hauptfenster, Szene, View, Attributpanel
├── config/       # Konstanten und Defaultwerte
├── graphics/     # QGraphicsItems für Knoten und Kanten
├── io/           # Persistenz über NetworkX Node-Link-JSON
├── model/        # Graphmodell und Attributnormalisierung
└── solver/       # Platzhalter für spätere VRP/MIP-Anbindung
```

Die GUI hängt von `GraphModel` ab, der Solver sollte später nur gegen NetworkX-Graphen oder reine Datenstrukturen arbeiten. Dadurch bleibt die Optimierung von der Qt-Oberfläche entkoppelt.
