import torch
import torch.nn as nn
import numpy as np

def parse_list_from_string(s):
    string = s.strip('[]')
    # Split the string into individual components
    string_list = string.split(", ")
    # Convert each component to a float
    float_list = [float(item) for item in string_list]
    return float_list


class LSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, prediction_horizon):
        super(LSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size * prediction_horizon)
        self.prediction_horizon = prediction_horizon
        self.output_size = output_size
    
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])  # Take the output of the last time step
        out = out.view(-1, self.prediction_horizon, self.output_size)  # Reshape to (batch_size, prediction_horizon, output_size)

        return out