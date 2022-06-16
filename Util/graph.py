import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

# precedence = pd.read_excel(r"D:\Project\scheduling\Util\precedence.xlsx")
# points = list(set(list(set(precedence["first_job_id"].tolist())) + list(set(precedence["second_job_id"].tolist()))))
# precedence["arcs"] = precedence.apply(lambda x: (x["first_job_id"], x["second_job_id"]), axis=1)
# arcs = precedence["arcs"].tolist()
# G = nx.DiGraph()
# G.add_nodes_from(points)
# G.add_edges_from(arcs)
# # nx.draw(G,with_labels=True)
# # plt.show()
# sub_graphs = [G.subgraph(c) for c in nx.weakly_connected_components(G)]
# print(sub_graphs[0].nodes)
#
# nx.draw(sub_graphs[0], with_labels=True)
# plt.show()

def find_root(sub_graph):
    roots = []
    succesors = []
    for node in sub_graph.nodes:
        if len(list(sub_graph.predecessors(node))) == 0:
            roots.append(node)
            succesors = succesors + list(sub_graph.successors(node))
    succesors = list(set(succesors))

    return roots,succesors

def cal_connected_components(precedence_df: pd.DataFrame, arc_jobs_df: pd.DataFrame):
    nodes = list(arc_jobs_df["job_id"].tolist())
    precedence_df["arcs"] = precedence_df.apply(lambda x: (x["first_job_id"], x["second_job_id"]), axis=1)
    precedence_df.set_index(keys="arcs",drop=False,inplace=True)
    arcs = precedence_df["arcs"].tolist()
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(arcs)
    sub_graphs = [nx.DiGraph(G.subgraph(c)) for c in nx.weakly_connected_components(G)]

    arc_jobs_df.rename(columns={"completion":"max_completion"},inplace=True)
    arc_jobs_df["completion"] = -1

    for sub_graph in sub_graphs:
        roots,successors = find_root(sub_graph)
        for r in roots:
            arc_jobs_df.loc[r, "completion"] = arc_jobs_df.loc[r,"max_completion"]
        arc = dict(zip(successors, [list(sub_graph.predecessors(i)) for i in successors]))

        sub_graph.remove_nodes_from(roots)
        while len(sub_graph.nodes):
            roots, successors = find_root(sub_graph)
            arc = dict(zip(successors,[list(sub_graph.predecessors(i)) for i in successors]))
            print(roots)
            print(arc)
            sub_graph.remove_nodes_from(roots)

    nx.draw(sub_graphs[0],with_labels=True)
    plt.show()
