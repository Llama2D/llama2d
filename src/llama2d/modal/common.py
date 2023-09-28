from modal import Image, Secret, Stub, Volume

N_GPUS = 2
GPU_MEM = 80
BASE_MODELS = {
    "base7": "meta-llama/Llama-2-7b-hf",
    "chat7": "meta-llama/Llama-2-7b-chat-hf",
    "chat13": "meta-llama/Llama-2-13b-chat-hf",
    "code7": "codellama/CodeLlama-7b-hf",
    "code34": "codellama/CodeLlama-34b-hf",
    "instruct7": "codellama/CodeLlama-7b-Instruct-hf",
    "instruct13": "codellama/CodeLlama-13b-Instruct-hf",
    "instruct34": "codellama/CodeLlama-34b-Instruct-hf",
    # Training 70B requires experimental flag fsdp_peft_cpu_offload_for_save.
    "chat70": "meta-llama/Llama-2-70b-chat-hf",
}

import os

secrets_dir = f"{os.path.dirname(os.path.realpath(__file__))}/../../secrets/"
data_dir = f"{os.path.dirname(os.path.realpath(__file__))}/../../data/"
dataset_dir = f"{os.path.dirname(os.path.realpath(__file__))}/datasets/"

fresh_build = True
import random

image = (
    Image.micromamba()
    .micromamba_install(
        "cudatoolkit=11.8",
        "cudnn=8.1.0",
        "cuda-nvcc",
        channels=["conda-forge", "nvidia"],
    )
    .apt_install("git", "unzip")
    .pip_install(
        "huggingface_hub==0.17.1",
        "hf-transfer==0.1.3",
        "scipy",
        "gdown",
        "google-cloud-vision",
        "sentencepiece",
        "playwright",
        "wandb",
        "transformers",
    )
    .pip_install(
        f"llama-recipes @ git+https://github.com/modal-labs/llama-recipes.git",
        extra_index_url="https://download.pytorch.org/whl/nightly/cu118",
        pre=True,
    )
    .run_commands(f"echo {random.random()}" if fresh_build else "echo 0.0")
    .run_commands(
        "pip install 'llama-recipes @ git+https://github.com/llama2d/llama-recipes.git@andrew-dev' git+https://github.com/llama2d/transformers.git@overwriting-llama --no-deps"
    )
    .env(dict(HUGGINGFACE_HUB_CACHE="/pretrained", HF_HUB_ENABLE_HF_TRANSFER="1"))
    .copy_local_dir(secrets_dir, "/root/secrets")
    .copy_local_file(
        f"{os.path.dirname(os.path.realpath(__file__))}/finetuning.py",
        "/root/finetuning.py",
    )
)

stub = Stub(
    "llama-finetuning",
    image=image,
    secrets=[Secret.from_name("huggingface"), Secret.from_name("wandb")],
)

# Download pre-trained models into this volume.
stub.pretrained_volume = Volume.persisted("example-pretrained-vol")

# Save trained models into this volume.
stub.results_volume = Volume.persisted("example-results-vol")

VOLUME_CONFIG = {
    "/pretrained": stub.pretrained_volume,
    "/results": stub.results_volume,
}
