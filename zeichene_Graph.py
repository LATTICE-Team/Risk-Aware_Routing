import networkx as nx
import matplotlib.pyplot as plt

def zeichne_graph(knoten, kanten, gerichtet=False):
    """
    Erstellt eine grafische Darstellung eines Graphen.

    :param knoten: Liste von Knoten (z.B. ['A', 'B', 'C'])
    :param kanten: Liste von Kanten (z.B. [('A','B'), ('B','C')])
    :param gerichtet: True für gerichteten Graphen, False für ungerichtet
    """
    
    # Graph erstellen
    if gerichtet:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    
    # Knoten und Kanten hinzufügen
    G.add_nodes_from(knoten)
    G.add_edges_from(kanten)
    
    # Layout berechnen (Positionen der Knoten)
    pos = nx.spring_layout(G)
    
    # Zeichnen
    nx.draw(
        G, pos,
        with_labels=True,
        node_color='lightblue',
        edge_color='gray',
        node_size=2000,
        font_size=12
    )
    
    # Anzeigen
    plt.title("Graph-Darstellung")
    plt.savefig("graph.png")
    print("Graph wurde als graph.png gespeichert")