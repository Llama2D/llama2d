import os
import subprocess

from common import BASE_MODELS, VOLUME_CONFIG, stub
from modal import Image, gpu, method

from loguru import logger
import torch

from transformers import LlamaConfig, LlamaForCausalLM, AutoTokenizer

tgi_image = (
    Image.from_registry("ghcr.io/huggingface/text-generation-inference:1.0.3")
    .dockerfile_commands("ENTRYPOINT []")
    .pip_install("text-generation", "transformers>=4.33.0")
    # .pip_install("git+https://github.com/Llama2D/transformers")
    .env(dict(HUGGINGFACE_HUB_CACHE="/pretrained"))
)


def _download_and_unload_peft(model_id, revision, trust_remote_code):
    """
    from: https://github.com/huggingface/text-generation-inference/blob/00b8f36fba62e457ff143cce35564ac6704db860/server/text_generation_server/utils/peft.py#L10
    """
    torch_dtype = torch.float16

    logger.info("Peft model detected.")
    logger.info("Loading the model it might take a while without feedback")

    model = LlamaForCausalLM.from_pretrained(
        model_id,
        revision=revision,
        torch_dtype=torch_dtype,
        trust_remote_code=trust_remote_code,
        low_cpu_mem_usage=True,
    )

    logger.info(f"Loaded.")
    logger.info(f"Merging the lora weights.")

    model = model.merge_and_unload()

    os.makedirs(model_id, exist_ok=True)
    cache_dir = model_id
    logger.info(f"Saving the newly created merged model to {cache_dir}")

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.add_special_tokens(
        {
            "pad_token": "<PAD>",
        }
    )

    model.save_pretrained(cache_dir, safe_serialization=True)
    model.config.save_pretrained(cache_dir)
    tokenizer.save_pretrained(cache_dir)


@stub.function(image=tgi_image, volumes=VOLUME_CONFIG, timeout=60 * 20)
def merge(run_id: str, commit: bool = False):
    os.mkdir(f"/results/{run_id}/merged")
    subprocess.call(f"cp /results/{run_id}/*.* /results/{run_id}/merged", shell=True)

    print(f"Merging weights for fine-tuned {run_id=}.")
    _download_and_unload_peft(f"/results/{run_id}/merged", None, False)

    if commit:
        print("Committing merged model permanently (can take a few minutes).")
        stub.results_volume.commit()


@stub.cls(
    image=tgi_image,
    gpu=gpu.A100(count=1, memory=40),
    allow_concurrent_inputs=100,
    volumes=VOLUME_CONFIG,
)
class Model:
    def __init__(self, base: str = "", run_id: str = ""):
        import socket
        import time

        from text_generation import AsyncClient

        model = f"/results/{run_id}/merged" if run_id else BASE_MODELS[base]

        if run_id and not os.path.isdir(model):
            merge.local(run_id)  # local = run in the same container

        print(f"Loading {model} into GPU ... ")
        launch_cmd = ["text-generation-launcher", "--model-id", model, "--port", "8000"]
        self.launcher = subprocess.Popen(launch_cmd, stdout=subprocess.DEVNULL)

        self.client = None
        while not self.client and self.launcher.returncode is None:
            try:
                socket.create_connection(("127.0.0.1", 8000), timeout=1).close()
                self.client = AsyncClient("http://127.0.0.1:8000", timeout=60)
            except (socket.timeout, ConnectionRefusedError):
                time.sleep(1.0)

        assert self.launcher.returncode is None

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.launcher.terminate()

    @method()
    async def generate(self, prompt: str, coords):
        result = await self.client.generate(prompt, coords, max_new_tokens=512)

        return result.generated_text


@stub.local_entrypoint()
def main(prompt: str, coords, base: str, run_id: str = "", batch: int = 1,):
    print(f"Running completion for prompt:\n{prompt} \ncoords{coords}")

    if run_id:
        print("=" * 20 + "Generating with adapter" + "=" * 20)
        for output in Model(base, run_id).generate.map([prompt] * batch, [coords] * batch):
            print(output)
