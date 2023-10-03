from math import inf
from random import choice, random

from torch.utils.data import Dataset

from llama2d.datasets.huggingface import DatasetInfo, publish_pt_dataset
from llama2d.vision import Llama2dScreen, Llama2dTokenizer, debug_dataset

animals = "frog,cat,bear,big lion,eagle,elephant,tiger,baboon,archerfish,gorilla,gerbil,ant colony".split(
    ","
)
directions = {
    "northernmost": (0, -1),  # in -y direction
    "farthest west": (-1, 0),  # in -x direction
    "southernmost": (0, 1),  # in +y direction
    "farthest east": (1, 0),  # in +x direction
}


class Llama2dZooCompassDataset(Dataset):
    def __init__(
        self,
        num_screens: int,
        words_per_screen: int,
        tokenizer: Llama2dTokenizer = None,
    ):
        self.num_screens = num_screens

        if tokenizer is None:
            tokenizer = Llama2dTokenizer()
        self.tokenizer = tokenizer

        self.screens = []
        for i in range(num_screens):
            screen = Llama2dScreen()
            direction, vector = choice(list(directions.items()))

            farthest_animal = None
            farthest_distance = -inf
            for j in range(words_per_screen):
                animal = choice(animals)
                coords = (random(), random())
                screen.push_word(word=animal, xy=coords)

                distance = coords[0] * vector[0] + coords[1] * vector[1]
                if distance > farthest_distance:
                    farthest_animal = animal
                    farthest_distance = distance

            assert farthest_animal is not None, "No animal is farthest"

            prompt = (
                f"Here is a map of the zoo. Find the {direction} animal in the zoo."
            )
            output = farthest_animal

            self.screens.append(self.tokenizer.process(prompt, screen, output))

    def __len__(self):
        return self.num_screens

    def __getitem__(self, i: int):
        return self.screens[i]


if __name__ == "__main__":
    tokenizer = Llama2dTokenizer()
    dataset = Llama2dZooCompassDataset(
        tokenizer=tokenizer, num_screens=10_000, words_per_screen=20
    )

    debug_dataset(dataset)

    info = DatasetInfo(
        repo="llama2d/llama2d-zoo-compass",
        desc="Identify the animal farthest north/west/east/south in the zoo.",
    )
    publish_pt_dataset(dataset, info)
