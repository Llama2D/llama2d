from playwright.sync_api import sync_playwright
from torch.utils.data import Dataset

from src.data.pretraining_urls import urls
from llama2d.datasets.huggingface import DatasetInfo, publish_pt_dataset
from llama2d.vision.url_to_llama_input import Llama2dWebsiteFeatureExtractor

class Llama2dPretrainingDataset(Dataset):
    def __init__(
        self, model="decapoda-research/llama-7b-hf", urls=[], include_coords=True
    ):
        self.__extractor = Llama2dWebsiteFeatureExtractor(model, mask_out_body=False)
        self.__urls = urls

        self.__include_coords = include_coords

        with sync_playwright() as p:
            # Using the Chromium browser but you can also use 'firefox' or 'webkit'
            browser = p.chromium.launch()
            page = browser.new_page()

            page.set_extra_http_headers(
                {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko)"
                    " Chrome/116.0.0.0 Safari/537.36"
                }
            )
            # exceptional() is a function calling helper that returns
            # None if the method errors.
            # we call all the functions
            self.extractions = [
                exceptional(self.__extractor.create_inference_data, args=(page, "", i))
                for i in self.__urls
            ]
            # or otherwise return None
            self.extractions = [i for i in self.extractions if i]

    def __getitem__(self, index):
        ret = self.extractions[index]
        if not self.__include_coords:
            return {k: v for k, v in ret.items() if k != "coords"}
        return ret

    def __len__(self):
        return len(self.extractions)


def exceptional(call, args):
    """Wrapper function to return None for a function if it errors.

    Parameters
    ----------
    call : callable
        The function to call
    args : List[Any]
        The arguments to call it with

    Returns
    -------
    Any
        The output of the funciton.
    """

    try:
        return call(*args)
    except Exception as e:
        print("your call to", call, "errored! Returning None")
        print(e)

        return None


pretraining_repo = "llama2d/llama2d-pretraining"

if __name__ == "__main__":
    print("Downloading pretraining dataset with Playwright...")

    ds_info = DatasetInfo(
        repo=pretraining_repo,
        desc="Llama2d pretraining dataset - next-token prediction "
        "on real estate websites",
    )

    dataset = Llama2dPretrainingDataset(
        model="decapoda-research/llama-7b-hf", urls=urls, include_coords=True
    )

    publish_pt_dataset(dataset, ds_info)
