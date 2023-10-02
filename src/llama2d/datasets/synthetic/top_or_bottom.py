from llama2d.vision import debug_dataset,Llama2dTokenizer,Llama2dScreen
from llama2d.datasets.huggingface import DatasetInfo, publish_pt_dataset
from torch.utils.data import Dataset

from math import inf
from random import choice,random
directions = {
    "t":(0.5,0), # in -y direction
    "b":(0.5,1), # in +y direction
}

rand_words = "bob,jane,alice,carol,ted,lisa,barry,frank,george,harold,henry,ian,john,james,kevin,mark,neil,oliver,peter,quinn,robert,steve,thomas,william".split(",")

class TopBottomDataset(Dataset):
    def __init__(
            self,
            num_screens:int,
            tokenizer:Llama2dTokenizer=None
        ):
        self.num_screens = num_screens

        if tokenizer is None:
            tokenizer = Llama2dTokenizer()
        self.tokenizer = tokenizer

        self.screens = []
        for i in range(num_screens):
            screen = Llama2dScreen()
            direction,vector = choice(list(directions.items()))

            screen.push_word(word=choice(rand_words),xy=vector)

            prompt = f"Top or bottom? (t/b)"
            output = direction
            
            self.screens.append(self.tokenizer.process(prompt,screen,output))
            
    
    def __len__(self):
        return self.num_screens
    def __getitem__(self,i:int):
        return self.screens[i]

if __name__ == "__main__":

    dataset = TopBottomDataset(num_screens=500)

    debug_dataset(dataset)

    info = DatasetInfo(repo="llama2d/llama2d-top-or-bottom",desc="Identify if a person is up or down.")
    publish_pt_dataset(dataset,info)