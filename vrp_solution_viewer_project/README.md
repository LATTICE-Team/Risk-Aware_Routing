# VRP Solution Viewer

PySide6/NetworkX-Anwendung zur Visualisierung einer erweiterten VRP-Lösung mit Robotern und Containern.

## Start

```bash
pip install -r requirements.txt
python main.py
```

Alternativ:

```bash
python -m vrp_solution_viewer
```

Ohne Eingabedatei wird eine Demo-Instanz geladen.

## Eingabeformat

Die GUI lädt eine JSON-Datei mit folgender Struktur:

```json
{
  "graph": {
    "directed": true,
    "multigraph": false,
    "graph": {},
    "nodes": [
      {"id": "0", "label": "Depot", "pos": [0, 0]},
      {"id": "1", "label": "Job 1", "pos": [200, 60]}
    ],
    "edges": [
      {"source": "0", "target": "1", "weight": 5.0}
    ]
  },
  "containers": ["K1", "K2"],
  "robots": ["R1", "R2"],
  "container_colors": {"K1": "#e41a1c", "K2": "#377eb8"},
  "container_movements": [
    {"agent_id": "K1", "source": "0", "target": "1", "start": 0.0, "end": 5.0}
  ],
  "robot_movements": [
    {"agent_id": "R1", "source": "0", "target": "1", "start": 0.0, "end": 5.0, "loaded": true, "container_id": "K1"}
  ]
}
```

Knotenpositionen können als `pos`, `position` oder als `x`/`y`-Attribute angegeben werden.

## Adapter für MIP-Ausgabe

`vrp_solution_viewer/adapters` enthält Adapterfunktionen, die aktive Binärvariablen in Bewegungsereignisse überführt. Der Kernviewer bleibt dadurch unabhängig davon, ob die Variablen aus `python-mip`, aus JSON oder aus einer Testinstanz stammen.
