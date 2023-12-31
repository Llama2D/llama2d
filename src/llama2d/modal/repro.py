from common import transformers_dir,llama_recipes_dir,root_dir
import os
import sys

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

def make_repro_command():
    commits = check_llama2d_code()

    # get full command line command
    command = " ".join(sys.argv)

    # TODO: fill in HF dataset name if it's not there

    return f"""
    # run in llama2d
    git checkout {commits["llama2d"]}
    cd transformers && git checkout {commits["transformers"]}
    cd ../llama-recipes && git checkout {commits["llama_recipes"]}
    cd src/llama2d/modal
    {command}
    """