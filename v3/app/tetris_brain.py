import torch
import torch.nn as nn


class TetrisBrain(nn.Module):
    def __init__(self, width: int = 10, height: int = 20):
        super(TetrisBrain, self).__init__()
        self.fc1 = nn.Linear(width * height, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 7)  # Output: 7 possible moves
        self.softmax = nn.Softmax(dim=1)  # For probability distribution

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = self.softmax(x)
        return x


def crossover(parent_a, parent_b):
    child = TetrisBrain()
    for child_param, parent_a_param, parent_b_param in zip(
        child.parameters(), parent_a.parameters(), parent_b.parameters()
    ):
        # Coin flip for each weight
        mask = torch.randint(0, 2, parent_a_param.shape).bool()
        child_param.data = torch.where(mask, parent_a_param.data, parent_b_param.data)
    return child


def mutate_v1(network, mutation_rate=0.01):
    for param in network.parameters():
        # Randomly select weights to mutate
        mask = torch.rand(param.shape) < mutation_rate

        # Generate Gaussian noise (mean=0, std_dev=1)
        mutation = torch.randn(param.shape)

        # Apply mutation and clamp weights between -1 and 1
        param.data = torch.clamp(param.data + mutation * mask, -1, 1)


# v2
def mutate(network, mutation_rate=0.01):
    for param in network.parameters():
        # Create a mask to select weights to mutate
        mask = torch.rand(param.shape, device=param.device) < mutation_rate

        # Generate Gaussian noise
        noise = torch.randn(param.shape, device=param.device) * param.data.std()

        # Apply mutation only to selected weights
        param.data += noise * mask
