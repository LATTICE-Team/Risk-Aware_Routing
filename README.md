# Risk-Aware_Routing
Risk-Aware Routing Algorithm for LATTICE

Was ist das?:
Ein Algorythmus-Ansatz um durch den Graphen eine Verteilungsfunktion als Label durch zu Propagieren. 

Beispiel Graph ist ein Gitter,erstellt in createGitter.py.
Um das Programm auzuführen reicht es die Main zu starten. 
Ablauf des Programms: 
  1. Initalisier einen Graphen
     a. Setze Zielknotnen und Startknotnen fest
     b. Bestimme über Dijskstra einen minalen Pfad mit angenommen kürzester Überganzszeit
     c. Bestimme über Dijskstra einen minimalen Pfad mit angenommen längster Überganzszeit     
  2. Propagiere Verteilungsfunktionenn vom Startknoten über verteilte Katen den Graphen entlang
  3. Merke dir den Pfad
  4. Aktualisiere Pfad und Kummuluierte Verteilungsfunkton
  5. Ende

Offene Aufgaben: 
  1. Runden einfügen für die Effizens 
  2. Überprüfen der Pfade
  3. Sensibilitäts Analyse des Rundungsfaktor 
  4. 
