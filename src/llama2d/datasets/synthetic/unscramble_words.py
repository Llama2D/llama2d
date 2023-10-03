
from llama2d.vision import debug_dataset,Llama2dTokenizer,Llama2dScreen
from llama2d.datasets.huggingface import DatasetInfo, publish_pt_dataset
from torch.utils.data import Dataset

from random import choice,random
rand_words = "bob,jane,alice,carol,ted,lisa,barry,frank,george,harold,henry,ian,john,james,kevin,mark,neil,oliver,peter,quinn,robert,steve,thomas,william".split(",")

class UnscrambleDataset(Dataset):
    def __init__(
            self,
            num_screens:int,
            words_per_screen:int,
            words_per_line:int=20,
            lines_per_screen:int=5,
            tokenizer:Llama2dTokenizer=None
        ):
        self.num_screens = num_screens
        self.words_per_screen = words_per_screen

        if tokenizer is None:
            tokenizer = Llama2dTokenizer()
        self.tokenizer = tokenizer

        self.screens = []
        for i in range(num_screens):
            screen = Llama2dScreen()

            words = [choice(rand_words) for _ in range(words_per_screen)]

            # render in a grid of lines
            for k,word in enumerate(words):
                i,j = k%words_per_line,k//words_per_line
                # convert i,j to x,y, where x is horizontal and y is vertical
                # x is in [0,1] and y is in [0,1]

                x = (i+0.5)/words_per_line
                y = (j+0.5)/lines_per_screen

                assert y<1,"Too many words for the screen"

                screen.push_word(word=word,xy=(x,y))

            from random import shuffle
            shuffle(screen.words)
            
            prompt = "Read out the words in the order they appear."
            response = " ".join(words)

            self.screens.append(self.tokenizer.process(prompt,screen,response))
    
    def __len__(self):
        return self.num_screens
    def __getitem__(self,i:int):
        return self.screens[i]

if __name__ == "__main__":

    dataset = UnscrambleDataset(
        num_screens=5000,
        words_per_screen=50,
        words_per_line=15,
        lines_per_screen=5
    )

    debug_dataset(dataset)

    info = DatasetInfo(repo="llama2d/llama2d-unscramble",desc="Unscramble the words displayed on the screen.")
    publish_pt_dataset(dataset,info)