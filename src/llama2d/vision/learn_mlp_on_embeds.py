from transformers.models.llama.sam_embed import PositionEmbeddingRandom
import torch
from torch.nn import functional as F
from tqdm import tqdm

from torch import nn
class CoordMlp(nn.Module):
    def __init__(self,n:int,hidden:int):
        super().__init__()
        self.embed = PositionEmbeddingRandom(n,torch_dtype=torch.float32)
        self.a = nn.Linear(n*2,hidden)
        self.b = nn.Linear(hidden,1)

        self.n = n
        self.hidden =hidden

    def forward(self,x):
        b,c,d = x.shape
        assert d==2,"Coords are not 2d"

        max_y_el = torch.argmax(x[:,:,1],dim=1)

        pos_embeds = self.embed(x).squeeze(1)
        assert pos_embeds.shape == (b,c,self.n*2),f"Pos_embeds are {pos_embeds.shape}. vs. {(b,c,self.n*2)}"

        logits = self.b(F.relu(self.a(pos_embeds)))

        preds = logits.squeeze(dim=2)
        loss = F.cross_entropy(preds,F.one_hot(max_y_el).to(torch.float32))

        return loss

def learn_mlp_for_top_point():

    rand_points = torch.rand((100,50,2))

    model = CoordMlp(100,100)
    params = model.parameters()
    lr = 3e-2
    optimizer = torch.optim.SGD(params,lr=lr)

    epochs = 500
    for epoch in tqdm(range(epochs)):
        loss = model(rand_points)

        print(loss.item(),loss.shape)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()


if __name__ == "__main__":
    learn_mlp_for_top_point()