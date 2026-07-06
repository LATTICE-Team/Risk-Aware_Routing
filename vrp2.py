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
K = set(range(3))   # Set of Containers
V = set(range(3))   # Set of Roboters

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

roboter_used = [model.add_var(var_type=mip.BINARY) for v in V]     # Roboter v is used
y = [[[[ model.add_var(var_type=mip.BINARY) for j in I] for i in I] for k in K] for v in V] # Roboter v fährt Container k von i zu j
A = [(k,i,j) for k in K for i in I for j in I if i != j]    # Liste von möglichen Bewegungsaufgaben
A_idx = range(len(A))
nexttask = [[[model.add_var(var_type=mip.BINARY) for b in A_idx] for a in A_idx] for v in V] # Roboter v macht Task b nach a
firsttask = [[model.add_var(var_type=mip.BINARY) for a in A_idx] for v in V]     # Der erste Task von Roboter v ist a
lasttask = [[model.add_var(var_type=mip.BINARY) for a in A_idx] for v in V]      # Der letzte Task von Roboter v ist a

def y_task(v, a):   # Roboter v macht Task a
    k, i, j = A[a]
    return y[v][k][i][j]

def pickup_node(a): # Startknoten Task a
    k, i, j = A[a]
    return i

def drop_node(a):   # Endknoten Task a
    k, i, j = A[a]
    return j

def task_start(a):  # Startzeit Task a
    k, i, j = A[a]
    if i == 0:
        return cont_start[k]
    else:
        return cont_departure[k][i]

def task_end(a):    # Endzeit Task a
    k, i, j = A[a]
    if j == 0:
        return cont_end[k]
    else:
        return cont_arrival[k][j]

robo_end = [model.add_var(lb=0.0, ub=H, var_type=mip.CONTINUOUS) for v in V]

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

######### Roboter
# jede Containerbewegung wird von genau einem Roboter gefahren
for k in K:
    for i in I:
        for j in I:
            if i != j:
                model += mip.xsum(y[v][k][i][j] for v in V) == x[k][i][j]

# Verhindert zweimal gleiche Aufgabe hintereinander 
for v in V:
    for a in A_idx:
        model += nexttask[v][a][a] == 0

for v in V:
    for a in A_idx:
        # genau ein Vorgänger, falls Aufgabe a von Roboter v ausgeführt wird:
        # entweder a ist erste Aufgabe oder sie hat eine vorherige Aufgabe
        model += firsttask[v][a] + mip.xsum(nexttask[v][b][a] for b in A_idx if b != a) == y_task(v, a)

        # genau ein Nachfolger, falls Aufgabe a von Roboter v ausgeführt wird:
        # entweder a ist letzte Aufgabe oder sie hat eine nächste Aufgabe
        model += lasttask[v][a] + mip.xsum(nexttask[v][a][b] for b in A_idx if b != a) == y_task(v, a)

# Genau eine erste und letzte Aufgabe
for v in V:
    model += mip.xsum(firsttask[v][a] for a in A_idx) == roboter_used[v]
    model += mip.xsum(lasttask[v][a] for a in A_idx) == roboter_used[v]

# nur genutzte Roboter könenn Aufgaben erledigen
for v in V:
    for a in A_idx:
        model += y_task(v, a) <= roboter_used[v]

# Zeitbedingung Tasks
for v in V:
    for a in A_idx:
        for b in A_idx:
            if a != b:
                model += task_start(b) >= task_end(a) + T[drop_node(a)][pickup_node(b)] - M*(1 - nexttask[v][a][b])
# zeitliche Machbarkeit erster Task
for v in V:
    for a in A_idx:
        model += task_start(a) >= T[0][pickup_node(a)] - M*(1 - firsttask[v][a])
# zeitliche Machbarkeit letzter Task
for v in V:
    for a in A_idx:
        model += robo_end[v] >= task_end(a) + T[drop_node(a)][0] - M*(1 - lasttask[v][a])



#-----Zielfunktion-------------------------------------------------------------------------------------
loaded_cost = mip.xsum(y[v][k][i][j] * w[i][j] for v in V for k in K for i in I for j in I if i != j)
# empty_start_cost = mip.xsum(firsttask[v][a] * w[0][pickup_node(a)] for v in V for a in A_idx)
# empty_between_cost = mip.xsum(nexttask[v][a][b] * w[drop_node(a)][pickup_node(b)] for v in V for a in A_idx for b in A_idx if a != b)
# empty_end_cost = mip.xsum(lasttask[v][a] * w[drop_node(a)][0] for v in V for a in A_idx)
# model.objective = (loaded_cost + empty_start_cost + empty_between_cost + empty_end_cost)
model.objective = mip.xsum(x[k][i][j] for k in K for i in I for j in I) + loaded_cost
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

    PROJECT_ROOT = Path(__file__).resolve().parent
    OUTPUT_DIR = PROJECT_ROOT / "solutions"
    OUTPUT_DIR.mkdir(exist_ok=True)

    output_path = OUTPUT_DIR / "solution_from_vrp2.json"
    export_viewer_json(
        output_path,
        graph=G,
        I=I,
        K=K,
        V=V,
        T=T,
        c=c,
        x=x,
        y=y,
        A=A,
        firsttask=firsttask,
        nexttask=nexttask,
        lasttask=lasttask,
        cont_start=cont_start,
        cont_arrival=cont_arrival,
        cont_departure=cont_departure,
        cont_end=cont_end,
    )

    print("Viewer-Datei geschrieben: solution_from_vrp2.json")
