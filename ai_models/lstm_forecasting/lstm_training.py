import torch
import torch.nn as nn

class PollutionLSTM(nn.Module):
    """LSTM for Time-Series Forecasting"""
    def __init__(self, input_size=6, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=0.2
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Linear(32, 1)  # Predict next PM2.5
        )
        
    def forward(self, x):
        out, (hn, cn) = self.lstm(x)
        return self.fc(out[:, -1, :])

def train_lstm(train_loader, epochs=100):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = PollutionLSTM().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(epochs):
        for seq, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(seq.to(device))
            loss = criterion(outputs, labels.to(device))
            loss.backward()
            optimizer.step()
    
    torch.save(model.state_dict(), 'pollution_lstm.pth')
    return model

def create_sequences(data, window=6):
    sequences = []
    for i in range(len(data)-window):
        seq = data[i:i+window]
        label = data[i+window]
        sequences.append((seq, label))
    return sequences
