import mip
import networkx as nx
import sys
sys.path.insert(1, 'Lattice/Risk-Aware_Routing/Graph-Editor')
from graph import plot_graph, graph_to_cost_list, edge_attribute_to_list
from itertools import product

G = nx.read_gml("Lattice/Risk-Aware_Routing/Graph-Editor/my_graph_1.gml",destringizer=int)

n = G.number_of_nodes()
I = set(range(n))   # Set of Nodes/Vertices/Jobs
K = set(range(4))   # Set of Containers
V = set(range(3))   # Set of Roboters

w = graph_to_cost_list(G)   # Edge Weights
T = edge_attribute_to_list(G, "distance")   # Travel-Time
C = [3 for k in K]          # Container-Capacity
service_duration = [G.nodes[i]["service_duration"] for i in I]   # service duration at each Job
d = [G.nodes[i]["demand"] for i in I]    # demand for each Job
print(d)
time_window = [[G.nodes[i]["start"], G.nodes[i]["end"]] for i in I] # Time Window for Jobs

M = 1000    # Constant for big-M-method
#------------------------------------------------------------------------------------------------------------------
## Optimization problem
model = mip.Model()

c = [[ model.add_var(var_type=mip.BINARY) for i in I] for k in K]                   # Container k does Job i
x = [[[ model.add_var(var_type=mip.BINARY) for j in I ] for i in I] for k in K]     # Container k goes from i to j
r_0 = [[[ model.add_var(var_type=mip.BINARY) for j in I] for i in I] for v in V]    # Roboter v drives empty from i to j
r_1 = [[[ model.add_var(var_type=mip.BINARY) for j in I] for i in I] for v in V]    # Roboter v drives with a Container from i to j
robo_arrival = [[model.add_var(var_type=mip.CONTINUOUS) for i in I] for v in V]     # Arrival-Time Roboter v at Job i
robo_departure = [[model.add_var(var_type=mip.CONTINUOUS) for i in I] for v in V]   # Departure-Time Roboter v at Job i
cont_arrival = [[model.add_var(var_type=mip.CONTINUOUS) for i in I] for k in K]     # Arrival-Time Container k at Job i
cont_departure = [[model.add_var(var_type=mip.CONTINUOUS) for i in I] for k in K]   # Departure-Time Container k at Job i

container_used = [model.add_var(var_type=mip.BINARY) for k in K]     # Container k is used
roboter_used = [model.add_var(var_type=mip.BINARY) for v in V]     # Roboter v is used

model.objective = (mip.xsum(mip.xsum(mip.xsum(x[k][i][j]*w[i][j] for i in I)for j in I) for k in K)
                  + mip.xsum(mip.xsum(mip.xsum(r_0[v][i][j]*w[i][j] for i in I) for j in I) for v in V))

#-----Constraints---------------------------------------------------------------------------------------
for k in K:
    model += mip.xsum(c[k][i] for i in I-{0})/n <= container_used[k]
    model += mip.xsum(c[k][i] for i in I-{0}) <= C[k]

# wenn Container Job j macht, fährt er nach j
for k in K:
    for j in I-{0}:
        model += mip.xsum(x[k][i][j] for i in I) == c[k][j]

# jeder Job wird von genau einem Container erledigt
for i in I-{0}:
    model += mip.xsum(c[k][i] for k in K) == 1

# jeder Knoten wird genau von einem Container besucht
for i in I-{0}:
    model += mip.xsum(mip.xsum(x[k][i][j] for j in I) for k in K) == 1
    model += mip.xsum(mip.xsum(x[k][j][i] for j in I) for k in K) == 1

# jeder Container, der benutzt wird, startet und endet am Depot
for k in K:
    model += mip.xsum(x[k][0][i] for i in I) == container_used[k]
    model += mip.xsum(x[k][i][0] for i in I) == container_used[k]
for v in V:
    model += mip.xsum(r_0[v][0][i]+r_1[v][0][i] for i  in I-{0}) == roboter_used[v]
    model += mip.xsum(r_0[v][i][0]+r_1[v][i][0] for i  in I-{0}) == roboter_used[v]

# eingehend = ausgehend
for k in K:
    for j in I:
        model += mip.xsum(x[k][i][j] for i in I) - mip.xsum(x[k][j][i] for i in I) == 0
for v in V:
    for j in I:
        model += mip.xsum(r_0[v][i][j]+r_1[v][i][j] for i in I) - mip.xsum(r_0[v][j][i]+r_1[v][j][i] for i in I) == 0

# Keine Verbindung von Knoten zu sich selbst
for i in I:
    for k in K:
        model += x[k][i][i] == 0    
    for v in V:
        model += r_0[v][i][i] == 0
        model += r_1[v][i][i] == 0

# Kapazitätsbeschränkung Container
for k in K:
    model += mip.xsum(mip.xsum(x[k][i][j]*d[j] for i in I-{0}) for j in I-{0}) <= C[k]

# zeitliche Constraints Container
for k in K:
    for i in I-{0}:
        cont_arrival[k][i] + service_duration[i] <= cont_departure[k][i]
        cont_arrival[k][i] <= time_window[i][1]
        cont_arrival[k][i] >= time_window[i][0]
for k in K:
    for i in I:
        for j in I:
            T[i][j] - M*(1-x[k][i][j]) <= cont_arrival[k][j] - cont_departure[k][i]


#-----Solution---------------------------------------------------------------------------------------
status = model.optimize(max_seconds=300)

x_sol_float = [[[x[k][i][j].x for i in I] for j in I] for k in K]
# print(x_sol_float)
x_sol = [[[round(x[k][i][j].x) for i in I] for j in I] for k in K]

color_palette_int = [(235, 172, 35), (184, 0, 88),
                    (0, 140, 249), (0, 110, 0),
                    (0, 187, 173), (209, 99, 230),
                    (178, 69, 2), (255, 146, 135),
                    (89, 84, 214), (0, 198, 248),
                    (135, 133, 0), (0, 167, 108), 
                    (189, 189, 189)]
color_palette = [tuple(channel/255 for channel in color) for color in color_palette_int]

route = [[] for k in K]
for k in K:
    for i in I:
        for j in I:
            if  x_sol[k][i][j] == 1:
                G[i][j]["color"] = color_palette[k]
                G[i][j]["width"] = 2
                route[k].append((i,j))
print(route)
print([container_used[k].x for k in K])
print([[c[k][i].x for i in I] for k in K])