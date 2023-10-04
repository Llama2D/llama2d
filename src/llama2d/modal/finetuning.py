# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the
# terms of the Llama 2 Community License Agreement.

import os

import fire
import torch
import torch.distributed as dist
import torch.optim as optim
from llama_recipes.configs import fsdp_config, train_config
from llama_recipes.policies import AnyPrecisionAdamW, apply_fsdp_checkpointing
from llama_recipes.utils import fsdp_auto_wrap_policy
from llama_recipes.utils.config_utils import (
    generate_dataset_config,
    generate_peft_config,
    update_config,
)
from llama_recipes.utils.dataset_utils import get_preprocessed_dataset
from llama_recipes.utils.train_utils import (
    clear_gpu_cache,
    freeze_transformer_layers,
    get_policies,
    print_model_size,
    setup,
    setup_environ_flags,
    train,
)
from peft import get_peft_model, prepare_model_for_int8_training
from pkg_resources import packaging
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.fully_sharded_data_parallel import CPUOffload
from torch.optim.lr_scheduler import StepLR
from torch.utils.data import DistributedSampler

from transformers import AutoTokenizer, default_data_collator
from transformers.models.llama.modeling_llama import LlamaDecoderLayer
from transformers.models.llama.sam_embed import PositionEmbeddingRandom


def main(Llama, LlamaCfg, **kwargs):
    # Update the configuration for the training and sharding process
    update_config((train_config, fsdp_config), **kwargs)

    print(f"Full config: {train_config=},{kwargs=}")
    dataset_config = generate_dataset_config(train_config, kwargs)
    print(f"Dataset config: {dataset_config=}")

    use_2d = train_config.use_2d
    # Set the seeds for reproducibility
    torch.cuda.manual_seed(train_config.seed)
    torch.manual_seed(train_config.seed)

    if train_config.enable_fsdp:
        setup()
        # torchrun specific
        local_rank = int(os.environ["LOCAL_RANK"])
        rank = int(os.environ["RANK"])
        # world_size = int(os.environ["WORLD_SIZE"])

    if torch.distributed.is_initialized():
        torch.cuda.set_device(local_rank)
        clear_gpu_cache(local_rank)
        setup_environ_flags(rank)

    # Load the tokenizer and add special tokens
    tokenizer = AutoTokenizer.from_pretrained(train_config.model_name)
    tokenizer.add_special_tokens(
        {
            "pad_token": "<PAD>",
        }
    )

    # Load and preprocess the dataset for training and validation
    dataset_train = get_preprocessed_dataset(
        tokenizer,
        dataset_config,
        split="train",
    )

    if not train_config.enable_fsdp or rank == 0:
        print(f"--> Training Set Length = {len(dataset_train)}")

    dataset_val = get_preprocessed_dataset(
        tokenizer,
        dataset_config,
        split="test",
    )
    if not train_config.enable_fsdp or rank == 0:
        print(f"--> Validation Set Length = {len(dataset_val)}")

    kwargs = {
        "use_2d": use_2d,
        "lbd_start_value": train_config.lbd_start_value,
        "use_point_embed": train_config.use_point_embed,
    }  # if use_2d else {}

    # Load the pre-trained model and setup its configuration
    use_cache = False if train_config.enable_fsdp else None
    if train_config.enable_fsdp and train_config.low_cpu_fsdp:
        """
        for FSDP, we can save cpu memory by loading pretrained model on rank0 only.
        this avoids cpu oom when loading large models like llama 70B, in which case
        model alone would consume 2+TB cpu mem (70 * 4 * 8). This will add some comms
        overhead and currently requires latest nightly.
        """
        v = packaging.version.parse(torch.__version__)
        verify_latest_nightly = v.is_devrelease and v.dev >= 20230701
        if not verify_latest_nightly:
            raise Exception(
                "latest pytorch nightly build is required to "
                "run with low_cpu_fsdp config, "
                "please install latest nightly."
            )
        if rank == 0:
            model = Llama.from_pretrained(
                train_config.model_name,
                load_in_8bit=True if train_config.quantization else None,
                device_map="auto" if train_config.quantization else None,
                use_cache=use_cache,
                **kwargs,
            )
        else:
            llama_config = LlamaCfg.from_pretrained(train_config.model_name)
            llama_config.use_cache = use_cache

            llama_config.use_2d = use_2d
            llama_config.lbd_start_value = train_config.lbd_start_value
            llama_config.use_point_embed = train_config.use_point_embed

            with torch.device("meta"):
                model = Llama(llama_config)

    else:
        model = Llama.from_pretrained(
            train_config.model_name,
            load_in_8bit=True if train_config.quantization else None,
            device_map="auto" if train_config.quantization else None,
            use_cache=use_cache,
            **kwargs,
        )

    print(f"Using model type: {type(model)}")

    if train_config.enable_fsdp and train_config.use_fast_kernels:
        """
        For FSDP and FSDP+PEFT, setting 'use_fast_kernels' will enable
        using of Flash Attention or Xformer memory-efficient kernels
        based on the hardware being used. This would speed up fine-tuning.
        """
        try:
            from optimum.bettertransformer import BetterTransformer

            model = BetterTransformer.transform(model)
        except ImportError:
            print(
                "Module 'optimum' not found."
                " Please install 'optimum' it before proceeding."
            )
    print_model_size(model, train_config, rank if train_config.enable_fsdp else 0)

    # Prepare the model for int8 training if quantization is enabled
    if train_config.quantization:
        model = prepare_model_for_int8_training(model)

    # Convert the model to bfloat16 if fsdp and pure_bf16 is enabled
    if train_config.enable_fsdp and fsdp_config.pure_bf16:
        print("Converting to bfloat16")
        model.to(torch.bfloat16)

    if train_config.use_peft:
        peft_config = generate_peft_config(train_config, kwargs)
        print(f"PEFT config: {peft_config=}")
        model = get_peft_model(model, peft_config)

        # Llama2D weight initialization code

        trainable_params_before, _ = model.get_nb_trainable_parameters()

        print("--------IGNORE POS EMBEDS IS FALSE--------")
        for k, v in model.named_parameters():
            if k.endswith(".lbd"):
                v.requires_grad = True
                print(k, "requires_grad=", v.requires_grad, v)

        trainable_params_after, _ = model.get_nb_trainable_parameters()
        assert trainable_params_after > trainable_params_before, (
            "Looks like lambda gating parameter isn't marked as trainable."
            f" Before: {trainable_params_before}, after: {trainable_params_after}"
        )

        model.print_trainable_parameters()
    else:
        for k, v in model.named_parameters():
            if k.endswith(".lbd"):
                v.requires_grad = v.data.requires_grad = True
                print(k, "requires_grad=", v.requires_grad, v.data)

    # setting up FSDP if enable_fsdp is enabled
    if train_config.enable_fsdp:
        if not train_config.use_peft and train_config.freeze_layers:
            freeze_transformer_layers(train_config.num_freeze_layers)

        mixed_precision_policy, wrapping_policy = get_policies(fsdp_config, rank)
        my_auto_wrapping_policy = fsdp_auto_wrap_policy(
            model, LlamaDecoderLayer, PositionEmbeddingRandom
        )

        model = FSDP(
            model,
            auto_wrap_policy=my_auto_wrapping_policy
            if train_config.use_peft
            else wrapping_policy,
            cpu_offload=CPUOffload(offload_params=True)
            if fsdp_config.fsdp_cpu_offload
            else None,
            mixed_precision=mixed_precision_policy
            if not fsdp_config.pure_bf16
            else None,
            sharding_strategy=fsdp_config.sharding_strategy,
            device_id=torch.cuda.current_device(),
            limit_all_gathers=True,
            sync_module_states=train_config.low_cpu_fsdp,
            param_init_fn=lambda module: module.to_empty(
                device=torch.device("cuda"), recurse=False
            )
            if train_config.low_cpu_fsdp and rank != 0
            else None,
        )
        if fsdp_config.fsdp_activation_checkpointing:
            apply_fsdp_checkpointing(model)
    elif not train_config.quantization and not train_config.enable_fsdp:
        model.to("cuda")

    train_sampler = None
    val_sampler = None
    if train_config.enable_fsdp:
        train_sampler = DistributedSampler(
            dataset_train,
            rank=dist.get_rank(),
            num_replicas=dist.get_world_size(),
            shuffle=True,
        )
        if train_config.run_validation:
            val_sampler = DistributedSampler(
                dataset_val,
                rank=dist.get_rank(),
                num_replicas=dist.get_world_size(),
            )

    # Create DataLoaders for the training and validation dataset
    train_dataloader = torch.utils.data.DataLoader(
        dataset_train,
        batch_size=train_config.batch_size_training,
        num_workers=train_config.num_workers_dataloader,
        pin_memory=True,
        sampler=train_sampler if train_sampler else None,
        drop_last=True,
        collate_fn=default_data_collator,
    )

    eval_dataloader = None
    if train_config.run_validation:
        eval_dataloader = torch.utils.data.DataLoader(
            dataset_val,
            batch_size=train_config.val_batch_size,
            num_workers=train_config.num_workers_dataloader,
            pin_memory=True,
            sampler=val_sampler if val_sampler else None,
            drop_last=True,
            collate_fn=default_data_collator,
        )

    # Initialize the optimizer and learning rate scheduler

    # make custom param groups
    group_substrs = {
        "lambda":[train_config.lambda_lr,"lbd"],
        "point_embed":[train_config.point_embed_lr,"is_a_point_embed"],
    }
    param_groups = []
    for n,p in model.named_parameters():
        for group_name,(lr,substr) in group_substrs.items():
            if substr in n:
                param_groups.append({"params":[p],"lr":lr})
                break
        else:
            param_groups.append({"params":[p],"lr":train_config.lr})


    if fsdp_config.pure_bf16 and fsdp_config.optimizer == "anyprecision":
        optimizer = AnyPrecisionAdamW(
            param_groups,
            momentum_dtype=torch.bfloat16,
            variance_dtype=torch.bfloat16,
            use_kahan_summation=False,
            weight_decay=train_config.weight_decay,
        )
    else:
        optimizer = optim.AdamW(
            param_groups,
            weight_decay=train_config.weight_decay,
        )
    scheduler = StepLR(optimizer, step_size=1, gamma=train_config.gamma)

    if train_config.num_epochs > 0:
        # Start the training process
        results = train(
            model,
            train_dataloader,
            eval_dataloader,
            tokenizer,
            optimizer,
            scheduler,
            train_config.gradient_accumulation_steps,
            train_config,
            fsdp_config if train_config.enable_fsdp else None,
            local_rank if train_config.enable_fsdp else None,
            rank if train_config.enable_fsdp else None,
        )
        if not train_config.enable_fsdp or rank == 0:
            [print(f"Key: {k}, Value: {v}") for k, v in results.items()]
    else:
        print("Skipping training")

    # print lambda values
    print("-----Lambda gating values-------")
    with FSDP.summon_full_params(
        model, rank0_only=True, writeback=False, with_grads=False
    ):
        print("-----full-params Lambda gating values-------")
        for k, v in model.named_parameters():
            if k.endswith(".lbd"):
                print(k, v.data)
    print("--------------------------------")

    print_generations()


if __name__ == "__main__":
    fire.Fire(main)
