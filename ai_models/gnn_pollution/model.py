import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, global_mean_pool

class PollutionGNN(nn.Module):
    """
    Graph Neural Network for Pollution Spread Prediction
    Uses GAT layers with attention mechanisms
    """
    def __init__(self, node_features=8, hidden_dim=64, heads=4):
        super().__init__()
        self.gat1 = GATConv(node_features, hidden_dim, heads=heads)
        self.gat2 = GATConv(hidden_dim*heads, hidden_dim, heads=2)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim*2, 64),
            nn.ReLU(),
            nn.Linear(64, 1)  # Predict PM2.5 delta
        )
        
    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        
        # GAT layers
        x = F.elu(self.gat1(x, edge_index))
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.gat2(x, edge_index)
        
        # Readout layer
        x = global_mean_pool(x, batch)
        return self.fc(x)

class GNNDataLoader:
    """Convert tabular data to graph format"""
    def __init__(self, sensor_locs):
        self.locations = sensor_locs
        
    def create_graph(self, features, window=3):
        """Create graph with edges based on wind patterns"""
        nodes = []
        edges = []
        edge_attrs = []
        
        # Create nodes from windowed features
        for i in range(len(features)-window):
            node = torch.FloatTensor(features.iloc[i:i+window].values.flatten())
            nodes.append(node)
            
        # Create edges based on wind direction similarity
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if i != j:
                    wind_sim = 1 - abs(features['wind_dir_sin'][i] - 
                                 features['wind_dir_sin'][j])
                    edges.append([i, j])
                    edge_attrs.append(wind_sim)
        
        return torch_geometric.data.Data(
            x=torch.stack(nodes),
            edge_index=torch.LongTensor(edges).t().contiguous(),
            edge_attr=torch.FloatTensor(edge_attrs)
