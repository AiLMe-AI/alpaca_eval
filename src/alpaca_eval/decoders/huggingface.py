import copy
import functools
import logging
import multiprocessing
import os
import random
from typing import Sequence
from huggingface_hub.inference_api import InferenceApi

import tqdm

__all__ = ["huggingface_completions"]


def huggingface_completions(
    prompts: Sequence[str],
    model_name: str,
    gpu: bool = False,
    do_sample: bool = False,
    num_procs: int = 8,
    **kwargs,
) -> str:
    n_examples = len(prompts)
    if n_examples == 0:
        logging.info("No samples to annotate.")
        return []
    else:
        logging.info(
            f"Using `huggingface_completions` on {n_examples} prompts using {model_name}."
        )

    if "HUGGINGFACEHUB_API_TOKEN" in os.environ:
        API_TOKEN = os.environ["HUGGINGFACEHUB_API_TOKEN"]
    else:
        API_TOKEN = None
    inference = InferenceApi(
        model_name, task="text-generation", token=API_TOKEN, gpu=gpu
    )

    default_kwargs = dict(
        do_sample=do_sample, options=dict(wait_for_model=True), return_full_text=False
    )
    default_kwargs.update(kwargs)
    logging.info(f"Kwargs to completion: {default_kwargs}")

    if num_procs == 1:
        completions = [
            inference(inputs=prompt, params=default_kwargs)
            for prompt in tqdm.tqdm(prompts, desc="prompts")
        ]
    else:
        with multiprocessing.Pool(num_procs) as p:
            partial_completion_helper = functools.partial(
                inference, params=default_kwargs
            )
            completions = list(
                tqdm.tqdm(
                    p.imap(partial_completion_helper, prompts),
                    desc="prompts",
                    total=len(prompts),
                )
            )

    completions = [completion[0]["generated_text"] if "error" not in completion else "error:"+completion["error"]
                   for completion in completions]

    return completions