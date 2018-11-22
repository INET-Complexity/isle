import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

class ReinsuranceNetwork():
    def __init__(self, insurancefirms, reinsurancefirms, catbonds):
        """save entities"""
        self.insurancefirms = insurancefirms
        self.reinsurancefirms = reinsurancefirms
        self.catbonds = catbonds
        
        """obtain lists of operational entities"""
        op_entities = {}
        self.num_entities = {}
        for firmtype, firmlist in [("insurers", self.insurancefirms), ("reinsurers", self.reinsurancefirms), ("catbonds", self.catbonds)]:
            op_firmtype = [firm for firm in firmlist if firm.operational]
            op_entities[firmtype] = op_firmtype
            self.num_entities[firmtype] = len(op_firmtype)
        
        #op_entities_flat = [firm for firm in entities_list for entities_list in op_entities]
        self.network_size = sum(self.num_entities.values())
        
        """create weigthed adjacency matrix"""
        weights_matrix = np.zeros(self.network_size**2).reshape(self.network_size, self.network_size)
        for idx_to, firm in enumerate(op_entities["insurers"] + op_entities["reinsurers"]):
            eolrs = firm.get_excess_of_loss_reinsurance()
            for eolr in eolrs:
                #pdb.set_trace()
                idx_from = self.num_entities["insurers"] + (op_entities["reinsurers"] + op_entities["catbonds"]).index(eolr["reinsurer"])
                weights_matrix[idx_from][idx_to] = eolr["value"]
        
        """unweighted adjacency matrix"""
        adj_matrix = np.sign(weights_matrix)
                
        """define network"""
        self.network = nx.from_numpy_array(weights_matrix, create_using=nx.DiGraph())  # weighted
        self.network_unweighted = nx.from_numpy_array(adj_matrix, create_using=nx.DiGraph())     # unweighted
    
    def compute_measures(self):
        """obtain measures"""
        #degrees = self.network.degree()
        degree_distr = dict(self.network.degree()).values()
        in_degree_distr = dict(self.network.in_degree()).values()
        out_degree_distr = dict(self.network.out_degree()).values()
        is_connected = nx.is_weakly_connected(self.network)
        #is_connected = nx.is_strongly_connected(self.network)  # must always be False
        try:
            node_centralities = nx.eigenvector_centrality(self.network)
        except:
            node_centralities = nx.betweenness_centrality(self.network)
        # TODO: and more, choose more meaningful ones...
        
        print("Graph is connected: ", is_connected, "\nIn degrees ", in_degree_distr, "\nOut degrees", out_degree_distr, \
              "\nCentralities", node_centralities)

    def visualize(self):        
        """visualize"""
        plt.figure()
        firmtypes = np.ones(self.network_size)
        firmtypes[self.num_entities["insurers"]:self.num_entities["insurers"]+self.num_entities["reinsurers"]] = 0.5
        firmtypes[self.num_entities["insurers"]+self.num_entities["reinsurers"]:] = 1.3
        print(firmtypes, self.num_entities["insurers"], self.num_entities["insurers"] + self.num_entities["reinsurers"])
        pos = nx.spring_layout(self.network_unweighted)
        nx.draw(self.network_unweighted, pos, node_color=firmtypes, with_labels=True, cmap=plt.cm.winter)
        plt.show()
