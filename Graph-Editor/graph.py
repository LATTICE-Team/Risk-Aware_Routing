import networkx as nx
import matplotlib.pyplot as plt
import random
import math


def create_graph(anzahl_andere_knoten=10, seed=11):
    random.seed(seed)

    G = nx.DiGraph()

    # Startknoten mit allen Attributen
    G.add_node(
        0, 
        pos=(random.uniform(0.5, 10.0),random.uniform(0.5, 10.0)),
        color="red",
        label="Start"
    )

    # Weitere Knoten mit zufälligen positiven Koordinaten
    for node in range(1, anzahl_andere_knoten + 1):
        x = random.uniform(0.5, 10.0)
        y = random.uniform(0.5, 10.0)

        G.add_node(
            node,
            pos=(x, y),
            color="lightblue",
            label=f"Knoten {node}"
        )

    # Vollständig gerichteter Graph:
    # Zwischen jedem Knotenpaar existieren beide Richtungen.
    # Gewicht = euklidische Distanz
    for u in G.nodes():
        for v in G.nodes():
            if u < v:
                pos_u = G.nodes[u]["pos"]
                pos_v = G.nodes[v]["pos"]

                distanz = math.dist(pos_u, pos_v)

                G.add_edge(u, v, weight=distanz)
                G.add_edge(v, u, weight=distanz)

    return G


def plot_graph(G):
    # Position und Knotenfarbe extrahieren
    pos = nx.get_node_attributes(G, "pos")
    node_colors = [
        G.nodes[node]["color"]
        for node in G.nodes()
    ]
    # Kantenfarben aus Attributen extrahieren
    # Falls keine Farbe gesetzt ist: Standardfarbe grau
    edge_colors = [
        G[u][v].get("color", "gray")
        for u, v in G.edges()
    ]

    # Kantendicken aus Attributen extrahieren
    # Falls keine Dicke gesetzt ist: Standardwert 0.8
    edge_widths = [
        G[u][v].get("width", 0.8)
        for u, v in G.edges()
    ]

    edge_labels = {
        (u, v): f"{data['weight']:.2f}"
        for u, v, data in G.edges(data=True)
    }

    plt.figure(figsize=(8, 8))

    nx.draw(
        G,
        pos=pos,
        with_labels=True,
        node_color=node_colors,
        node_size=700,
        arrows=True,
        arrowsize=10,
        edge_color=edge_colors,
        width=edge_widths
    )

    nx.draw_networkx_edge_labels(
        G,
        pos=pos,
        edge_labels=edge_labels,
        font_size=7
    )


    plt.title("Gerichteter Graph mit vollständig gespeicherten Attributen")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.axis("equal")
    plt.grid(True)
    plt.show()


    import math

def graph_to_cost_list(G, weight_attr="weight", missing_value=0.0, diagonal_value=0.0):

    n = G.number_of_nodes()

    # Matrix initialisieren
    c = [
        [missing_value for _ in range(n)]
        for _ in range(n)
    ]

    # Kanten eintragen
    for u,v,data in G.edges(data=True):
        c[u][v] = data["weight"]

    return c

if __name__ == '__main__':
    # Graph erzeugen
    G = create_graph()
    print(G.nodes)
    # Graph plotten
    plot_graph(G)

    # Kontrolle: alle Knotenattribute
    # print("Knotenattribute:")
    # for node, data in G.nodes(data=True):
    #     print(node, data)

    # print("\nKantenattribute:")
    # for u, v, data in G.edges(data=True):
    #     print(f"{u} -> {v}: {data}")

    nx.write_gml(G, "Lattice/my_graph_1.gml")