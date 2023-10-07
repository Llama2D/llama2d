from common import transformers_dir,llama_recipes_dir,root_dir
import os
import sys

from modal import secret

def check_all_code_committed(dir):

    old_dir = os.getcwd()
    os.chdir(dir)

    # assert that all code in current directory is committed
    git_diff = os.popen(f"git diff").read()
    git_diff_cached = os.popen("git diff --cached").read()

    dir_name = os.path.basename(dir)
    assert (
        git_diff == "" and git_diff_cached == ""
    ), f"Please commit all code in {dir_name} before running this script."

    git_commit_hash = os.popen(f"git rev-parse HEAD").read().strip()

    # assert that all code in transformers is committed
    os.chdir(old_dir)

    return git_commit_hash

def check_llama2d_code():
    llama2d = check_all_code_committed(root_dir)
    transformers = check_all_code_committed(transformers_dir)
    llama_recipes = check_all_code_committed(llama_recipes_dir)

    return {
        "llama2d": llama2d,
        "transformers": transformers,
        "llama_recipes": llama_recipes,
    }


from common import BASE_MODELS, GPU_MEM, N_GPUS, VOLUME_CONFIG, stub
from modal import Mount, Secret, gpu
@stub.function(
    # memory=1024 * 100,
    # timeout=3600 * 4,
    secrets=[Secret.from_name("huggingface")],
)
def get_dataset_info(repo:str,version:str=None):
    from huggingface_hub import hf_api
    hf_info = hf_api.dataset_info(repo_id=repo,revision=version)

    # get commit hash from download checksums
    commit_hash = hf_info.sha

    print(f"Dataset commit hash: {commit_hash}")

    return commit_hash

from typing import Optional
def make_repro_command(dataset:str,repo:Optional[str]=None,version:Optional[str] = None):
    # get full command line command
    command = " ".join(sys.argv)

    # huggingface check
    if dataset == "hf_dataset.py":
        assert repo is not None, "Please specify repo for HF dataset."
        commit_hash =  get_dataset_info.local(repo,version)
        assert version is None or version == commit_hash, "Version must match commit hash - no branch name shenanigans."
        if version is None:
            version = commit_hash
            command += f" --version {version}"

    commits = check_llama2d_code()

    return f"""
    # run in llama2d/ directory
    git checkout {commits["llama2d"]}
    cd transformers && git checkout {commits["transformers"]} && cd ..
    cd llama-recipes && git checkout {commits["llama_recipes"]} && cd ..
    cd src/llama2d/modal
    {command}
    """, commits