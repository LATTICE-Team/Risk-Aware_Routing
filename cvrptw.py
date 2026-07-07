import mip
import networkx as nx
import sys
sys.path.insert(1, 'Lattice/Risk-Aware_Routing/Graph-Editor')
from graph import plot_graph, graph_to_cost_list, edge_attribute_to_list
sys.path.insert(1, "Lattice/Risk-Aware_Routing/vrp_solution_viewer_project")
from vrp_solution_viewer.adapters.vrp_viewer_adapter import export_viewer_json

G = nx.read_gml("Lattice/Risk-Aware_Routing/Graph-Editor/my_graph_1.gml",destringizer=int)

n = G.number_of_nodes()
I = set(range(n))   # Set of Nodes/Vertices/Jobs
K = set(range(10))   # Set of Containers
V = set(range(10))   # Set of Roboters

w = graph_to_cost_list(G)   # Edge Weights
T = edge_attribute_to_list(G, "distance")   # Travel-Time
C = [6 for k in K]          # Container-Capacity
service_duration = [G.nodes[i]["service_duration"] for i in I]   # service duration at each Job
d = [G.nodes[i]["demand"] for i in I]    # demand for each Job
time_window = [[G.nodes[i]["start"], G.nodes[i]["end"]] for i in I] # Time Window for Jobs

max_T = max(T[i][j] for i in I for j in I)
H = max(time_window[i][1] for i in I) + sum(service_duration[i] for i in I) + n * max_T
M = H + max_T

#------------------------------------------------------------------------------------------------------------------
## Optimization problem
model = mip.Model()

container_used = [model.add_var(var_type=mip.BINARY) for k in K]     # Container k is used
c = [[ model.add_var(var_type=mip.BINARY) for i in I] for k in K]                   # Container k does Job i
x = [[[ model.add_var(var_type=mip.BINARY) for j in I ] for i in I] for k in K]     # Container k goes from i to j
cont_arrival = [[model.add_var(lb=0.0, ub=H, var_type=mip.CONTINUOUS) for i in I] for k in K]     # Arrival-Time Container k at Job i
cont_departure = [[model.add_var(lb=0.0, ub=H, var_type=mip.CONTINUOUS) for i in I] for k in K]   # Departure-Time Container k at Job i
cont_start = [model.add_var(lb=0.0, ub=H, var_type=mip.CONTINUOUS) for k in K]    # Startzeit Container k am Depot
cont_end = [model.add_var(lb=0.0, ub=H, var_type=mip.CONTINUOUS) for k in K]      # Rückkehrzeit Container k zum Depot


#-----Constraints---------------------------------------------------------------------------------------
######### Conatiner
# Kapazitätsbeschränkung Container
for k in K:
    model += mip.xsum(d[i] * c[k][i] for i in I - {0}) <= C[k] * container_used[k]

# Container darf nur bewegt werden, wenn er auch benutzt wird
for k in K:
    for i in I - {0}:
        model += c[k][i] <= container_used[k]

# genau dann, wenn Container Job j macht, hat er eine eingehende und ausgehende Kante zu j
for k in K:
    for i in I-{0}:
        model += mip.xsum(x[k][j][i] for j in I if j != i) == c[k][i]
        model += mip.xsum(x[k][i][j] for j in I if j != i) == c[k][i]

# jeder Job wird von genau einem Container erledigt
for i in I-{0}:
    model += mip.xsum(c[k][i] for k in K) == 1


# jeder Container, der benutzt wird, startet und endet am Depot
for k in K:
    model += mip.xsum(x[k][0][j] for j in I if j != 0) == container_used[k]
    model += mip.xsum(x[k][i][0] for i in I if i != 0) == container_used[k]

# Keine Verbindung von Knoten zu sich selbst
for i in I:
    for k in K:
        model += x[k][i][i] == 0    


# zeitliche Constraints Container
for k in K:
    for i in I-{0}:
        model += cont_arrival[k][i] <= (time_window[i][1]-service_duration[i]) * c[k][i]
        model += cont_arrival[k][i] >= time_window[i][0] * c[k][i]

# zeitliche Konsistenz von Depot zu Kunden
for k in K:
    for j in I - {0}:
        model += cont_arrival[k][j] >= cont_start[k] + T[0][j] - M*(1 - x[k][0][j])
        model += cont_arrival[k][j] <= cont_start[k] + T[0][j] + M*(1 - x[k][0][j])

# zeitliche Konsistenz Kunde zu Kunde
for k in K:
    for i in I - {0}:
        for j in I - {0}:
            if i != j:
                model += cont_arrival[k][j] >= cont_departure[k][i] + T[i][j] - M*(1 - x[k][i][j])

# zeitliche Konsistenz Servicezeit
for k in K:
    for i in I - {0}:
        model += cont_departure[k][i] >= cont_arrival[k][i] + service_duration[i] - M * (1 - c[k][i])
        model += cont_departure[k][i] <= M * c[k][i]
# zeitliche Konsistenz Containerrückkehr
for k in K:
    for i in I - {0}:
        model += cont_end[k] >= cont_departure[k][i] + T[i][0] - M * (1 - x[k][i][0])
        model += cont_end[k] <= cont_departure[k][i] + T[i][0] + M * (1 - x[k][i][0])



#-----Zielfunktion-------------------------------------------------------------------------------------
model.objective = mip.xsum(x[k][i][j] * w[i][j] for k in K for i in I for j in I)

#-----Solution---------------------------------------------------------------------------------------
model.max_seconds = 300
status = model.optimize()
if status == mip.OptimizationStatus.OPTIMAL:
    print('optimal solution cost {} found'.format(model.objective_value))
elif status == mip.OptimizationStatus.FEASIBLE:
    print('sol.cost {} found, best possible: {}'.format(model.objective_value, model.objective_bound))
elif status == mip.OptimizationStatus.NO_SOLUTION_FOUND:
    print('no feasible solution found, lower bound is: {}'.format(model.objective_bound))
elif status == mip.OptimizationStatus.INFEASIBLE:
    print('model is infeasible')
elif status == mip.OptimizationStatus.UNBOUNDED:
    print('model is unbounded')
else:
    print('other status:', status)
if status == mip.OptimizationStatus.OPTIMAL or status == mip.OptimizationStatus.FEASIBLE:
    from pathlib import Path


x_sol_float = [[[x[k][i][j].x for j in I] for i in I] for k in K]
x_sol = [[[round(x[k][i][j].x) for j in I] for i in I] for k in K]

route = [[] for k in K]
for k in K:
    for j in I:
        for i in I:
            if x_sol[k][i][j] == 1:
                route[k].append((i,j))
print(route)
