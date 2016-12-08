#!/usr/bin/python3
import igraph as ig
import networkx as nx
import pdb
import sys
import display_graph as dg

def ig_to_nx(g):
    nxg = nx.Graph()
    nxg.add_nodes_from(g.vs.indices)
    nxg.add_edges_from([(x.source, x.target) for x in g.es])
    return nxg

def nx_to_ig(g):
    node_map = dict([(n, i) for i, n in enumerate(sorted(g.nodes()))])
    edges = [(node_map[x], node_map[y]) for x,y in g.edges()]
    return ig.Graph(edges=edges)


def remove_degree_x_vertices(g, x, verbose=False):
    """Return a graph with all vertices of degree <= x. Since removing
    nodes will likely reduce the degree of other nodes, we have to do
    this iteratively until no nodes of degree <= k remain.

    """

    work_graph = nx.Graph(g)
    deg_dict = nx.degree(work_graph)
    iteration = 0
    while deg_dict and min(deg_dict.values()) <= x:
        ok_nodes = [n for n,d in deg_dict.items() if d > x]
        work_graph  = nx.Graph(work_graph.subgraph(ok_nodes))
        deg_dict = nx.degree(work_graph)
        iteration += 1
        if verbose:
            print("Iteration {0}. length deg_dict = {1}".format(iteration, len(deg_dict)))
    return work_graph

class SubgraphTooBigException(Exception):
    pass

class GraphNot2ConnectedException(Exception):
    pass

def find_two_connected_subgraphs(g, verbose=False):
    """Find the largest 2-connected subgraph of the graph passed in."""
    work_graph = remove_degree_x_vertices(g, 1, verbose)

    nodes_to_remove = set()
    iteration = 0
    for nodes in nx.all_node_cuts(work_graph, 1):
        if verbose:
            sys.stdout.write("{0}\r".format(iteration))
        iteration += 1
        nodes_to_remove = nodes_to_remove.union(nodes)

    if verbose:
        sys.stdout.write("\n")

    if nodes_to_remove:
        nodes_to_keep = set(work_graph.nodes()) - nodes_to_remove
        work_graph  = nx.Graph(work_graph.subgraph(list(nodes_to_keep)))
        components = list(nx.connected_components(work_graph))
        for component in components:
            yield(nx.Graph(work_graph.subgraph(list(component))))
    return

def find_case_1_two_connected_subgraphs(g, q, verbose=False):
    """Find subgraphs of g that has a single separating pair (ie, that is
    suitable for the first 2-connected case in section 3.2 of the DBCP
    paper. Each subgraph Gi must have |Vi| < |V|(q-1)/q. Make a
    generating function that returns valid subgraphs and nodes.

    """
    g = remove_degree_x_vertices(g, 1, verbose)

    all_nodes = g.nodes()
    size = len(all_nodes)
    q = float(q)
    max_subgraph_size = (q-1.0)/q*size

    
    if any(nx.all_node_cuts(g, 1)):
        raise GraphNot2ConnectedException()

    for nodes in nx.all_node_cuts(g, 2):
        sub_graph_nodes = [n for n in all_nodes if n not in nodes]
        disconnected_graph = nx.Graph(g.subgraph(sub_graph_nodes))
        try:
            for component in nx.connected_components(disconnected_graph):
                if verbose:
                    print("Subcomponent has size {0}".format(len(component)))
                if len(component) >= max_subgraph_size:
                    if verbose:
                        print("Too big!")
                        dg.show_graph(nx_to_ig(disconnected_graph))
                    raise SubgraphTooBigException()
        except SubgraphTooBigException:
            if verbose:
                print("For nodes {0} found a subgraph > (q-1)/q*size = {1}".format(nodes, max_subgraph_size))
            continue
        yield(nodes, disconnected_graph)
    return

def do_case_1_two_connected_subgraphs(g, verbose=False):
    found_count = 0
    for nodes, subgraph in find_case_1_two_connected_subgraphs(g, 4, verbose):
        found_count += 1
        if verbose:
            dg.show_graph(nx_to_ig(subgraph))
            print("\n\n***** found a case 1 2-connected subgraph from nodes {}*****\n\n".format(nodes))
    print("Found {} case-1 subgraphs".format(found_count))
    return

def extract_power_k_connected(verbose=False):
    nxg = ig_to_nx(ig.Graph.Read_GML('data/power.gml'))
    k_connected = nx.k_components(nxg)
    for k, components in k_connected.items():
        for i, component in enumerate(components):
            subgraph = nx.Graph(nxg.subgraph(component))
            file_name = "data/power_{}_connected_subset_{:>04}_{:>02}.gml".format(k, len(component), i)
            if verbose:
                print("Writing {}".format(file_name))
                nx_to_ig(subgraph).write_gml(file_name)

def main():
#    extract_power_k_connected()
    file_name = sys.argv[1]
    verbose = len(sys.argv) > 2
    if verbose:
        dg.show_file(file_name)
    nxg = ig_to_nx(ig.Graph.Read_GML(file_name))
    pdb.set_trace()
    c = nx.cycle_basis(nxg)
    do_case_1_two_connected_subgraphs(nxg, verbose=verbose)
    return

if __name__=='__main__':
    main()
    
