from common import BASE_MODELS, GPU_MEM, N_GPUS, VOLUME_CONFIG, stub
from modal import Mount, gpu

import sys
import os

# add llama2d to path
sys.path.append(f"{os.path.dirname(os.path.realpath(__file__))}/../../.")
import llama2d

@stub.function(
    volumes=VOLUME_CONFIG,
    memory=1024 * 100,
    timeout=3600 * 4,
    secrets=[Secret.from_name("huggingface")],
)
def download(model_name: str):

    assert 'HUGGINGFACE_TOKEN' in os.environ, 'Please set the HUGGINGFACE_TOKEN environment variable.'
    from huggingface_hub.hf_api import HfFolder; HfFolder.save_token(os.environ['HUGGINGFACE_TOKEN'])

    from huggingface_hub import snapshot_download

    from transformers.utils import move_cache

    from llama_recipes.finetuning import is_llama2d_enabled

    try:
        snapshot_download(model_name, local_files_only=True)
        print(f"Volume contains {model_name}.")
    except FileNotFoundError:
        print(f"Downloading {model_name} (no progress bar) ...")
        snapshot_download(model_name)
        move_cache()

        print("Committing /pretrained directory (no progress bar) ...")
        stub.pretrained_volume.commit()


def library_entrypoint(config):
    assert 'HUGGINGFACE_TOKEN' in os.environ, 'Please set the HUGGINGFACE_TOKEN environment variable.'
    from huggingface_hub.hf_api import HfFolder; HfFolder.save_token(os.environ['HUGGINGFACE_TOKEN'])

    from llama_recipes.finetuning import main,is_llama2d_enabled
    print("Is llama2d enabled?", is_llama2d_enabled)
    print(config)

    main(**config)


@stub.function(
    volumes=VOLUME_CONFIG,
    mounts=[
        Mount.from_local_dir("./datasets", remote_path="/root"),
    ],
    gpu=gpu.A100(count=N_GPUS, memory=GPU_MEM),
    timeout=3600 * 12,
)
def train(train_kwargs):
    from torch.distributed.run import config_from_args, elastic_launch, parse_args

    torch_args = parse_args(["--nnodes", "1", "--nproc_per_node", str(N_GPUS), ""])
    print(f"{torch_args=}\n{train_kwargs=}")

    elastic_launch(
        config=config_from_args(torch_args)[0],
        entrypoint=library_entrypoint,
    )(train_kwargs)

    print("Committing results volume (no progress bar) ...")
    stub.results_volume.commit()


import modal
@stub.local_entrypoint()  # Runs locally to kick off remote training job.
def main(
    dataset: str,
    base: str = "base7",
    run_id: str = "",
    num_epochs: int = 10,
    batch_size: int = 16,
):
    import os
    print(f"Welcome to Modal Llama fine-tuning.")
    print(f"Dataset is {dataset}.")

    # print(dict(Secret.from_name("huggingface").__dict__))
    # os.environ["HUGGINGFACE_TOKEN"] = Secret.from_name("huggingface")["HUGGINGFACE_TOKEN"]
    # print(f"Huggingface API key is {os.environ['HUGGINGFACE_TOKEN']}.")

    model_name = BASE_MODELS[base]
    print(f"Syncing base model {model_name} to volume.")
    download.remote(model_name)

    if not run_id:
        import secrets

        run_id = f"{base}-{secrets.token_hex(3)}"
    elif not run_id.startswith(base):
        run_id = f"{base}-{run_id}"

    print(f"Beginning run {run_id=}.")
    train.remote(
        {
            "model_name": BASE_MODELS[base],
            "output_dir": f"/results/{run_id}",
            "batch_size_training": batch_size,
            "lr": 3e-4,
            "num_epochs": num_epochs,
            "val_batch_size": 1,
            # --- Dataset options ---
            "dataset": "custom_dataset",
            "custom_dataset.file": dataset,
            # --- FSDP options ---
            "enable_fsdp": True,
            "low_cpu_fsdp": True,  # Optimization for FSDP model loading (RAM won't scale with num GPUs)
            "fsdp_config.use_fast_kernels": True,  # Only works when FSDP is on
            "fsdp_config.fsdp_activation_checkpointing": True,  # Activation checkpointing for fsdp
            "pure_bf16": True,
            # --- Required for 70B ---
            "fsdp_config.fsdp_cpu_offload": True,
            "fsdp_peft_cpu_offload_for_save": True,  # Experimental
            # --- PEFT options ---
            "use_peft": True,
            "peft_method": "lora",
            "lora_config.r": 8,
            "lora_config.lora_alpha": 16,

            "use_2d": False,
            "ignore_pos_embeds": True,

            "label_names": ["coords"],
        }
    )

    print(f"Training completed {run_id=}.")
    print(
        f"Test: `modal run compare.py --base {base} --run-id {run_id} --prompt '...'`."
    )
