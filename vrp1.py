import mip
import networkx as nx
import sys
sys.path.insert(1, 'Lattice/Graph-Editor')
from graph import plot_graph, graph_to_cost_list
from itertools import product

G = nx.read_gml("Lattice/Graph-Editor/my_graph_1.gml",destringizer=int)

n = G.number_of_nodes()
k = 3               # Number of Vehicles
N = set(range(n))   # Set of Nodes/Vertices
K = set(range(k))   # Set of Vehicles

c = graph_to_cost_list(G)   # Edge Weights

## Optimierungsproblem
model = mip.Model()

x = [[[ model.add_var(var_type=mip.BINARY) for k in K ] for j in N] for i in N]
y = [[ model.add_var(var_type=mip.CONTINUOUS) for k in K ] for i in N]
# w = [[ model.add_var(var_type="CONTINUOUS") for i in N] for k in K]

model.objective = mip.xsum(mip.xsum(mip.xsum(c[i][j]*x[i][j][k] for i in N)for j in N) for k in K)

# jeder Knoten wird mindestens einmal besucht
for i in N-{0}:
    model += mip.xsum(mip.xsum(x[i][j][k] for j in N-{0}) for k in K) == 1    


z = [model.add_var(var_type=mip.BINARY) for k in K]     # 1: Fahrzeug wird benutzt, 0: Fahrzeug wird nicht benutzt
# jedes Fahrzeug, das benutzt wird, startet und endet am Depot
for k in K:
    model += mip.xsum(x[0][j][k] for j in N-{0}) == z[k]
    model += mip.xsum(x[i][0][k] for i in N-{0}) == z[k]

# eingehend = ausgehend
for k in K:
    for j in N:
        model += mip.xsum(x[i][j][k] for i in N) - mip.xsum(x[j][i][k] for i in N) == 0    

# Keine Verbindung von Knoten zu sich selbst
for k in K:
    for i in N:
        model += x[i][i][k] == 0    

# subtour elimination
for k in K:
    for (i, j) in product(N - {0}, N - {0}):
        if i != j:
            model += y[i][k] - (n+1)*x[i][j][k] >= y[j][k]-n 


status = model.optimize(max_seconds=300)

x_sol_float = [[[x[i][j][k].x for k in K] for j in N] for i in N]
x_sol = [[[round(x[i][j][k].x) for k in K] for j in N] for i in N]
obj_sol = sum(sum(sum(c[i][j]*x_sol[i][j][k] for i in N)for j in N) for k in K)
for k in K:
    test = sum(x_sol[0][j][k] for j in N)
#print(x_sol)

color_palette_int = [(235, 172, 35), (184, 0, 88), (0, 140, 249), (0, 110, 0), (0, 187, 173), (209, 99, 230), (178, 69, 2), (255, 146, 135), (89, 84, 214), (0, 198, 248), (135, 133, 0), (0, 167, 108), (189, 189, 189)]
color_palette = [tuple(channel/255 for channel in color) for color in color_palette_int]

route = [[] for k in K]
for k in K:
    for j in N:
        for i in N:
            if x_sol[i][j][k] == 1:
                #G[i][j]["color"] = color_palette[k]
                #G[i][j]["width"] = 2
                route[k].append((i,j))

print(route)
plot_graph(G)
