import types
import subprocess

from datasets import Dataset
from torch.utils import data
import numpy as np, torch
#
from llama2d.datasets.cached import CachedDataset

from dataclasses import dataclass

@dataclass
class DatasetInfo:
  repo: str
  desc: str

def dataset_dict_to_list(dataset_dict):
  """
  Converts a Torch dataset stored as a dictionary to a list of dictionaries.

  Args:
      dataset_dict (dict): The input dataset dictionary with keys 'input_ids', 'coords', 'labels', and 'attention_mask'.

  Returns:
      list: A list of dictionaries where each dictionary contains values for the keys at each index.
  """
  keys = dataset_dict.keys()
  num_samples = len(dataset_dict[list(keys)[0]])  
  # Assuming all keys have the same length
  dataset_list = []
  for i in range(num_samples):
    sample_dict = dict.fromkeys(keys)
    for key in keys:
      sample_dict[key] = dataset_dict[key][i]
    dataset_list.append(sample_dict)
  return dataset_list


def pt2hf(torch_dataset: data.Dataset,
          convert_type: types=torch.float32):
  def gen(torch_dataset):
    for idx in len(torch_dataset):
      yield torch_dataset[idx]  # this has to be a dictionary
  if convert_type:
    torch_dataset = [
      {k: v.to(convert_type) for k,v in torch_dataset[i].items()} 
        for i in range(len(torch_dataset))
    ]
  # dset = Dataset.from_generator(gen(torch_dataset))
  dset_hf = Dataset.from_list(torch_dataset)  
  return dset_hf

def publish_pt_dataset(ds_pt, args):
  try:
    ds = pt2hf(ds_pt)   # may require setting: convert_type=np.float32
    print(f"Dataset type:{ds}")
    ds.info.description = args.desc
    ds.set_format(type='torch', columns=list(ds_pt[0].keys()))
    ds.push_to_hub(args.repo)
    print(f"Push succeeded.")
  except Exception as e:
      print(f"Exception while publishing: {e}")

if __name__=="__main__":
  from ..constants import PRETRAINING_CACHE_DIR
  import argparse
  parser = argparse.ArgumentParser(description="Description of your script")
  # Argument 1: First argument (e.g., input file)
  parser.add_argument("-C", "--cache_dir", type=str, default=PRETRAINING_CACHE_DIR,
                      help="Cache directory")
  # Argument 2: Second argument (e.g., output file)
  parser.add_argument("-R", "--repo", default="supermomo668/Llama2D-Pretrain",
                      type=str, help="Name of Repo")
  # Argument 2: Second argument (e.g., output file)
  parser.add_argument("-D", "--desc", 
                      default="Llama2D is a project from AGI UI/UX Hackathon. Check our main Git Repo at : https://github.com/Llama2D/llama2d/tree/main",
                      type=str, help="Name of Repo")
  
  args = parser.parse_args()
  ds_pt = CachedDataset(args.cache_dir)
  publish_pt_dataset(ds_pt, args)