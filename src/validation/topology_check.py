import networkx as nx


def check_topology(pipes):

    graph = nx.DiGraph()

    for pipe in pipes:
        graph.add_edge(
            pipe.source_equipment_id,
            pipe.target_equipment_id
        )


    print(
        "Nodes:",
        graph.number_of_nodes()
    )

    print(
        "Connections:",
        graph.number_of_edges()
    )


    if nx.is_weakly_connected(graph):
        print("Topology OK ✅")

    else:
        print("Topology has disconnected components ❌")