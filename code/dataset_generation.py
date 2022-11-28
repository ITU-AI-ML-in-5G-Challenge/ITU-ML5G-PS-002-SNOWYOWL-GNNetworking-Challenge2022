import networkx as nx
import random
import os
import numpy as np
import yaml
from getpass import getpass

np.random.seed(65123184)
random.seed(65123184)


def generate_topology(net_size, prob, seed):
    ''' 
    This function generates a graph topology.
    Args:
         net_size (int): The number of nodes of the network
         prob (float): Probability for edge creation
         seed (int): Seed for random number generator
         
    Returns:
            G (nx graph): The generated graph topology
    '''
    
    G = nx.fast_gnp_random_graph(n=net_size, p=prob, seed=int(seed))
   
    policies = ["FIFO","SP","WFQ","DRR"]
    buffer_sz = [8000, 16000, 32000, 64000]
    wfq_weights = ["70,20,10", "33.3,33.3,33.4", "60,30,10", "80,10,10", "65,25,10"]
    drr_weights = ["60,30,10", "70,25,5", "33.3,33.3,33.4", "50,40,10", "90,5,5"]
    
    for i in G.nodes():
        
        # Assign to each node the scheduling Policy
        G.nodes[i]["schedulingPolicy"] = random.choice(policies)
        
        # Assign the buffer size of all the ports of the node
        if G.nodes[i]["schedulingPolicy"] == "FIFO":
            G.nodes[i]["bufferSizes"] = random.choice(buffer_sz)
        else:
            G.nodes[i]["bufferSizes"] = random.choice(buffer_sz)
            
        #queue weights if relevant
        if G.nodes[i]["schedulingPolicy"] == "WFQ":
            G.nodes[i]["schedulingWeights"] = random.choice(wfq_weights)
        if G.nodes[i]["schedulingPolicy"] == "DRR":
            G.nodes[i]["schedulingWeights"] = random.choice(drr_weights)
            
    for edge in G.edges():
        # Assign initial link capacity to the link that will be update based on the routing
        bwidth = random.choices([10000, 25000, 50000, 75000, 100000], weights=[0.1, 0.2, 0.4, 0.2, 0.1])
        G[edge[0]][edge[1]]["bandwidth"] = bwidth[0]
        
    
    return (G)


def generate_routing(G, routing_file):
    ''' 
    This function generates a file with the shortest path routing of the topology G.
    Args:
         G (nx graph): The graph topology
         routing_file (str): A location to save the routing file
         
    Returns:
            lPaths (dict): A dictionary of dictionaries with lPaths[source][target]=[list of nodes in path].
    '''
    
    with open(routing_file,"w") as r_fd:
        lPaths = nx.shortest_path(G)
        
        for src in G:
            for dst in G:
                if (src == dst):
                    continue
                path =  ','.join(str(x) for x in lPaths[src][dst])
                r_fd.write(path+"\n")
    return lPaths


def generate_tm(G, intensity, traffic_file):
    ''' 
    This function generates a traffic matrix file.
    Args:
         G (nx graph): The graph topology
         intensity (float) : The traffic intensity
         traffic_file (str): A location to save the traffic file
         
    Returns:
        traffic_ar (array): An array of traffic flow for each src, dst pair  
    '''
    
    poisson = "0" 
    cbr = "1"
    on_off = "2, 5, 5" #time_distribution, avg off_time exp, avg on_time exp
    time_dist = [poisson, cbr, on_off]
    
    pkt_dist_1 = "0, 500, 0.22, 750, 0.05, 1000, 0.06, 1250, 0.62, 1500, 0.05" 
    pkt_dist_2 = "0, 500, 0.08, 750, 0.16, 1000, 0.35, 1250, 0.21, 1500, 0.2" 
    pkt_dist_3 = "0, 500, 0.53, 750, 0.16, 1000, 0.07, 1250, 0.1,  1500, 0.14" 
    pkt_dist_4 = "0, 500,  0.1, 750, 0.16, 1000, 0.36, 1250, 0.24, 1500, 0.14" 
    pkt_dist_5 = "0, 500, 0.05, 750, 0.28, 1000, 0.25, 1250, 0.27, 1500, 0.15"  
    
    pkt_size_dist = [pkt_dist_1, pkt_dist_2, pkt_dist_3, pkt_dist_4, pkt_dist_5]
    tos_lst = [0, 1, 2]
    
    traffic_ar =  np.zeros((len(G), len(G)))
    
    with open(traffic_file, "w") as tm_fd:
        for src in G:
            for dst in G:
                avg_bw = random.randint(intensity//2, intensity)
                td = np.random.choice(time_dist, p=[0.8, 0.1, 0.1])
                sd = np.random.choice(pkt_size_dist, p=[0.1, 0.2, 0.3, 0.3, 0.1])
                tos = np.random.choice(tos_lst, p=[0.1, 0.3, 0.6])
                traffic_ar[src][dst] = avg_bw
                
                traffic_line = "{},{},{},{},{},{}".format(
                    src, dst, avg_bw, td, sd, tos)
                tm_fd.write(traffic_line+"\n")
                
    return traffic_ar

def get_load():
    ''' 
    This function generates a link utilization.
    
    Returns:
        link_load (flat): A speecific link utilization 
    '''
    
    while True:
        mean = random.choices([0.2, 0.4, 0.6, 0.8], weights=[0.3, 0.3, 0.3, 0.1])[0]   
        std = mean/2
        link_load = np.random.normal(mean, std)
        
        if 0 <= link_load <= 1:
            break
    return link_load


def get_link_cap(cap):
    ''' 
    This function finds a link capacity from a target set.
    Args:
         cap (float): A given link capacity
         
    Returns:
        capacity (float): A link capacity from the candidates set  
    '''
    
    candidates = [10000, 25000, 40000, 100000, 250000, 400000]
    distance  = abs(np.array(candidates) - cap)
    idx = np.argmin(distance)
    
    capacity = candidates[idx]
    
    return capacity


def update_link_bw(G, lPaths, traffic_ar, graph_file):
    ''' 
    This function updates the link capacity of the network graph and save it in a file.
    Args:
        G (nx graph): The graph topology
        lPaths (dict) : A dictionary of dictionaries with lPaths[source][target]=[list of nodes in path].
        traffic_ar (array): An array of traffic flow for each src, dst pair
        graph_file (str): A location to save the graph file
 
    '''
    
    
    link_bw_ar =  np.zeros((len(G), len(G)))

    for src in G:
        for dst in G:
            if (src == dst):
                continue
            
            path = lPaths[src][dst]
            for  i in range(len(path)-1):
                link_bw_ar[path[i], path[i+1]] += traffic_ar[src, dst]
    
   
    for e in G.edges():
        link_load = get_load()
        cap = np.round(link_bw_ar[e[0], e[1]]/link_load, -3)
        G[e[0]][e[1]]["bandwidth"] = get_link_cap(cap)
        
        
    nx.write_gml(G, graph_file)


def docker_cmd(training_dataset_path):
    raw_cmd = f"docker run --rm --mount type=bind,src={os.path.join(os.getcwd(),training_dataset_path)},dst=/data bnnupc/netsim:v0.1"
    terminal_cmd = raw_cmd
    if os.name != 'nt': # Unix, requires sudo
        print("Superuser privileges are required to run docker. Introduce sudo password when prompted")
        terminal_cmd = f"echo {getpass()} | sudo -S " + raw_cmd
        raw_cmd = "sudo " + raw_cmd
    return raw_cmd, terminal_cmd




if __name__=="__main__":

    # Define destination for the generated samples
    training_dataset_path = "training_snowyowl"
    
    #paths relative to data folder
    graphs_path = "graphs"
    routings_path = "routings"
    tm_path = "tm"
    
    # Path to simulator file
    simulation_file = os.path.join(training_dataset_path,"simulation.txt")
    # Name of the dataset: Allows you to store several datasets in the same path
    # Each dataset will be stored at <training_dataset_path>/results/<name>
    dataset_name = "dataset_snowyowl"
    
    # Create folders
    if (os.path.isdir(training_dataset_path)):
        print ("Destination path already exists. Files within the directory may be overwritten.")
    else:
        os.makedirs(os.path.join(training_dataset_path,graphs_path))
        os.mkdir(os.path.join(training_dataset_path,routings_path))
        os.mkdir(os.path.join(training_dataset_path,tm_path))
    
    net_size = 10
    seed_list = [9, 110, 21, 1110, 19650, 1960, 1750, 9005, 5895, 3845]
    
    
    with open (simulation_file, "w") as fd:
        for j in range(10):
           
            # Generate TM:
            for i in range (10):
                G = generate_topology(net_size, 1/4, seed_list[j])
                # Generate routing
                routing_file = os.path.join(routings_path, "routing_10_{}_{}.txt".format(j, i))
                lPaths = generate_routing(G, os.path.join(training_dataset_path, routing_file))
                
                #traffic flow intensity
                intensity = random.choice([1000,2000,3000,4000])
                
                tm_file = os.path.join(tm_path, "tm_{}_{}.txt".format(net_size, i))
                traffic_ar = generate_tm(G, intensity, os.path.join(training_dataset_path, tm_file))
                
                #update link bandwidth and save graph
                graph_file = os.path.join(graphs_path, "graph_10_{}_{}.txt".format(j, i))
                update_link_bw(G, lPaths, traffic_ar, os.path.join(training_dataset_path, graph_file))
                
                sim_line = "{},{},{}\n".format(graph_file, routing_file, tm_file)   
                # If dataset has been generated in windows, convert paths into linux format
                fd.write(sim_line.replace("\\","/"))
                
    
    # First we generate the configuration file
    conf_file = os.path.join(training_dataset_path, "conf.yml")
    conf_parameters = {
        "threads": 6,# Number of threads to use 
        "dataset_name": dataset_name, # Name of the dataset. It is created in <training_dataset_path>/results/<name>
        "samples_per_file": 10, # Number of samples per compressed file
        "rm_prev_results": "n", # If 'y' is selected and the results folder already exists, the folder is removed.
    }
    
    with open(conf_file, 'w') as fd:
        yaml.dump(conf_parameters, fd)
        
        
    # Start the docker
    raw_cmd, terminal_cmd = docker_cmd(training_dataset_path)
    print("The next cell will launch docker from the notebook. Alternatively, run the following command from a terminal:")
    print(raw_cmd)
    
    os.system(terminal_cmd)
    
    

    
    
    
    
    
    
