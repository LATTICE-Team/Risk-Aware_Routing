"""Vorwaertspropagation von CDF-Huellkurven, keine Pfadoptimalitaetsgarantie."""
from collections import deque
import numpy as np
from distributions import cdf2pdf, pdf2cdf, isvalid_pdf
from labelprop import labelprop
from maxcdf import maxcdf

def cdf_values(cdf, times):
    """Wertet eine diskrete CDF an den angegebenen Zeitpunkten aus."""

	# Letzte Stützstelle finden, die <= dem Abfragezeitpunkt ist.
    indices = np.searchsorted(cdf[0], times, side="right") - 1

	# Eine vorangestellte Null beschreibt die CDF vor der ersten Stützstelle.
    values = np.concatenate(([0.0], cdf[1]))

    return values[indices + 1]

def propagate_distributions(graph, start, target=None, *, start_cdf=None,
                            atol=1e-12, max_updates=100000, write_back=True):
    """Falte Vorgaenger-PMF und Kanten-PMF, kombiniere danach mit maxcdf.

    Unterstuetzt NetworkX Graph/DiGraph ohne parallele Kanten. Fahrtzeiten
    muessen nichtnegativ sein, die Faltung setzt Unabhaengigkeit voraus.
    start_cdf: 2 x N Array; Standard: graph.nodes[start]['ArrCDF'].
    Alte CDFs anderer Knoten werden ignoriert (neue Berechnung).
    Rueckgabe: Dictionary Knoten -> CDF oder None bei Unerreichbarkeit.
    Bei write_back wird ArrCDF erst nach erfolgreichem Abschluss geschrieben;
    T0 und Pfad werden nicht geaendert. Das Ziel ist absorbierend.

    Ein erneutes Einreihen erfolgt nur bei Verbesserung um mehr als atol.
    atol ist eine lokale Toleranz, keine globale Fehlerschranke.
    Bei max_updates wird RuntimeError statt eines Teilergebnisses ausgeloest.
    Die Huelle muss keiner realisierbaren Route entsprechen. Fuer zyklische
    Graphen wird keine allgemeine endliche Konvergenz zugesichert.
    """
    if start not in graph or (target is not None and target not in graph):
        raise ValueError('Start und Ziel muessen im Graphen vorhanden sein.')
    if graph.is_multigraph():
        raise ValueError('Parallele Kanten werden nicht unterstuetzt.')
    if not np.isfinite(atol) or atol < 0:
        raise ValueError('atol muss endlich und nichtnegativ sein.')
    if not isinstance(max_updates, int) or max_updates < 1:
        raise ValueError('max_updates muss eine positive Ganzzahl sein.')
    if start_cdf is None:
        start_cdf = graph.nodes[start]['ArrCDF']

    # Einmalige Validierung und Konvertierung der statischen Kantendaten.
    outgoing = {u: [] for u in graph}
    for u, v, data in graph.edges(data=True):
        pdf = np.asarray(data['TransittimesPDF'], dtype=float).copy()
        isvalid_pdf(pdf)
        if np.any(pdf[0] < 0):
            raise ValueError('Negative Kantenfahrtzeiten sind unzulaessig.')
        # pdf = pdf[:, pdf[1] > 0]
        # pdf[1] /= pdf[1].sum()
        outgoing[u].append((v, pdf))
        if not graph.is_directed() and u != v:
            outgoing[v].append((u, pdf))

    cdfs = {u: None for u in graph}
    cdfs[start] = np.asarray(start_cdf, dtype=float).copy()
    pending = deque([start])
    in_queue = {start}
    updates = 0
    while pending:
        u = pending.popleft()
        in_queue.remove(u)
        if u == target:
            continue
        source_pdf = cdf2pdf(cdfs[u])
        for v, transit_pdf in outgoing[u]:
            if v == start:
                continue  # Fest vorgegebene Randbedingung am Start.
            candidate_pdf = labelprop(source_pdf, transit_pdf)
            candidate_pdf[1] /= candidate_pdf[1].sum()
            candidate = pdf2cdf(candidate_pdf)
            old = cdfs[v]
            merged = candidate if old is None else maxcdf(old, candidate)
            if old is not None:
                times = np.union1d(old[0], merged[0])
                if not np.any(cdf_values(merged, times) > cdf_values(old, times) + atol):
                    continue
            updates += 1
            if updates > max_updates:
                raise RuntimeError('max_updates erreicht; keine Konvergenz bestaetigt.')
            cdfs[v] = merged
            if v not in in_queue:
                pending.append(v)
                in_queue.add(v)
    if write_back:
        for u, cdf in cdfs.items():
            graph.nodes[u]['ArrCDF'] = None if cdf is None else cdf.copy()
    return cdfs
