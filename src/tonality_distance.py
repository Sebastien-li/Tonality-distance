import networkx as nx
import numpy as np


def get_tonality_distance(neighbor_weight = 1,
                          relative_weight = 0.7,
                          parallel_weight = 1.3,
                          enharmonic_weight = 0.5,
                          dominant_weight = 1.2): 
    """
    Returns a 7x12x4 array of tonality distances and also returns the tonality graph. 

    Tonality distance:
    The first two dimensions represent the diatonic and chromatic space of the desired interval.
    The last dimension represents the mode transition: 
    0 for major -> major
    1 for major -> minor
    2 for minor -> major
    3 for minor -> minor

    Tonality graph:
    The tonality graph is a directed graph with 7x12x2 nodes that represent the diatonic, chromatic space and the mode of the key
    
    """
    
    keys_graph = nx.DiGraph()
    for dia in range(7):
        for chro in range(12):
            for mode in ['m','M']:
                key = (dia,chro,mode)
                keys_graph.add_node(key)

    for dia in range(7):
        for chro in range(12):
            for mode in ['m','M']:
                key = (dia,chro,mode)
                neighbor = ((dia+4)%7,(chro+7)%12,mode)
                keys_graph.add_edge(key,neighbor,weight=neighbor_weight, modulation = 'Neighbor (sharp)')
                keys_graph.add_edge(neighbor,key,weight=neighbor_weight, modulation = 'Neighbor (flat)')

                if mode == 'm':
                    relative = ((dia+2)%7,(chro+3)%12,'M')
                    keys_graph.add_edge(key,relative,weight=relative_weight, modulation = 'Relative major')
                    keys_graph.add_edge(relative,key,weight=relative_weight, modulation = 'Relative minor')
                
                parallel = (dia, chro, 'M' if mode == 'm' else 'm')
                keys_graph.add_edge(key,parallel,weight=parallel_weight, modulation = 'Parallel')

                enharmonic = ((dia+1)%7, chro, mode)
                keys_graph.add_edge(key,enharmonic,weight=enharmonic_weight, modulation = 'Enharmonic')
                keys_graph.add_edge(enharmonic,key,weight=enharmonic_weight, modulation = 'Enharmonic')

                if mode == 'm':
                    dominant = ((dia+4)%7,(chro+7)%12,'M')
                    keys_graph.add_edge(key,dominant,weight=dominant_weight, modulation = 'Dominant minor (to V)')
                    keys_graph.add_edge(dominant,key,weight=dominant_weight, modulation = 'Dominant minor (to i)')

    shortest_path_length_major = nx.shortest_path_length(keys_graph,(0,0,'M'),weight='weight')
    tonality_distance = np.zeros((7,12,4)) 
    for (dia, chro, mode), distance in shortest_path_length_major.items():
        tonality_distance[dia,chro,int(mode == 'm')] = distance

    shortest_path_length_minor = nx.shortest_path_length(keys_graph,(0,0,'m'),weight='weight')
    for (dia, chro, mode), distance in shortest_path_length_minor.items():
        tonality_distance[dia,chro,2+int(mode == 'm')] = distance
    return tonality_distance, keys_graph