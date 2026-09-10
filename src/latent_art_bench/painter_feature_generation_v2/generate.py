"""Pinned local generation with a complete prospective request grid and no rerolls."""

from __future__ import annotations

import hmac
import importlib.metadata
import subprocess
from collections import Counter
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    PROTOCOL,
    WORKSPACE,
    append_event,
    bindings,
    digest,
    events,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.corpus import PROMPTS

CONFIG = Path("configs/painter_feature_generation_v2/sd_turbo.json")
SELF = Path("src/latent_art_bench/painter_feature_generation_v2/generate.py")


def request_grid(config: dict, library: dict) -> list[dict]:
    key = bytes.fromhex(config["master_seed"])
    if len(key) != 32 or config["repetitions"] < 25:
        raise ValueError("invalid registered seed or repetition count")
    if library["counts"]["templates"] != 16:
        raise ValueError("the complete 16-template census is required")
    rows = []
    for block in range(config["repetitions"]):
        block_rows = []
        for template in library["templates"]:
            template_id = template["template_id"]
            message = f"pfg-v2/1.0-seed|{template_id}|{block}".encode()
            seed = int.from_bytes(hmac.new(key, message, "sha256").digest()[:8], "big") >> 1
            prompts = {"artist_free": template["artist_free_prompt"],
                       **{p: entry["prompt"] for p, entry in template["named_prompts"].items()}}
            for condition, prompt in prompts.items():
                request_id = f"b{block:03d}-{template_id}-{condition}"
                block_rows.append(dict(
                    request_id=request_id, block=block, template_id=template_id,
                    condition=condition, prompt=prompt, seed=seed,
                    order_hash=digest([config["master_seed"], "order", request_id]),
                ))
        rows.extend(sorted(block_rows, key=lambda r: r["order_hash"]))
    if len(rows) != 80 * config["repetitions"]:
        raise ValueError("unexpected generation grid")
    return [dict(row, sequence=i) for i, row in enumerate(rows)]


def download_model(root: Path, config_path: Path = CONFIG) -> dict:
    from huggingface_hub import snapshot_download

    config = read_json(root / config_path)
    path = WORKSPACE / "models" / f"sd-turbo-{config['revision'][:12]}"
    receipt_path = root / MANIFESTS / "model_sd_turbo.json"
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        verify_bindings(root, receipt["files"])
        return receipt
    snapshot_download(
        config["model_id"], revision=config["revision"], local_dir=root / path,
        allow_patterns=["*.json", "*.txt", "*.model", "**/*.json", "**/*.txt", "**/*.model",
                        "**/*fp16.safetensors", "README.md", "LICENSE*"],
        max_workers=2,
    )
    paths = [p.relative_to(root) for p in (root / path).rglob("*")
             if p.is_file() and ".cache" not in p.parts]
    receipt = dict(model_id=config["model_id"], revision=config["revision"],
                   model_path=str(path), files=bindings(root, paths),
                   downloaded_at_utc=utc_now().isoformat())
    publish(receipt_path, receipt)
    return receipt


def prepare(root: Path, experiment_id: str, config_path: Path = CONFIG) -> dict:
    identifier(experiment_id)
    output = root / MANIFESTS / experiment_id
    if output.exists():
        raise FileExistsError(output)
    config = read_json(root / config_path)
    model_receipt = MANIFESTS / "model_sd_turbo.json"
    model = read_json(root / model_receipt)
    verify_bindings(root, model["files"])
    if (model["model_id"], model["revision"]) != (config["model_id"], config["revision"]):
        raise ValueError("downloaded model differs from registered configuration")
    paths = [config_path, model_receipt, PROMPTS, PROTOCOL, SELF, Path("uv.lock"),
             Path("pyproject.toml"), Path("src/latent_art_bench/io.py"),
             Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
             Path("src/latent_art_bench/painter_feature_generation_v2/features.py"),
             Path("src/latent_art_bench/painter_feature_generation_v2/statistics.py")]
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit exact generation input first: {path}")
    grid = request_grid(config, read_json(root / PROMPTS))
    publish(output / "requests.jsonl", grid, lines=True)
    receipt = dict(
        schema_version="pfg-v2-generation-freeze/1.0", experiment_id=experiment_id,
        model_path=model["model_path"], config=config, requests=len(grid),
        requests_sha256=hash_file(output / "requests.jsonl"), inputs=bindings(root, paths),
        recorded_git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        software={p: importlib.metadata.version(p) for p in
                  ("torch", "diffusers", "transformers", "Pillow", "numpy")},
        authorization="2026-09-05 maintainer session: implement complete research analysis; "
                      "local model, no paid API spending.",
        reviewer_kind="operator_self_check_not_independent_review",
        prepared_at_utc=utc_now().isoformat(),
    )
    publish(output / "generation_freeze.json", receipt)
    return receipt


def execute(root: Path, experiment_id: str) -> dict:
    identifier(experiment_id)
    with stage_lock(root / WORKSPACE / experiment_id / ".generation.writer.lock"):
        return _execute(root, experiment_id)


def _execute(root: Path, experiment_id: str) -> dict:
    import torch
    from diffusers import AutoPipelineForText2Image

    identifier(experiment_id)
    output = root / MANIFESTS / experiment_id
    freeze_path = output / "generation_freeze.json"
    frozen = read_json(freeze_path)
    verify_bindings(root, frozen["inputs"])
    model_receipt = read_json(root / MANIFESTS / "model_sd_turbo.json")
    verify_bindings(root, model_receipt["files"])
    if hash_file(output / "requests.jsonl") != frozen["requests_sha256"]:
        raise ValueError("generation request frame changed")
    if (output / "generation_receipt.json").exists():
        raise FileExistsError("generation is terminal")
    config = frozen["config"]
    for package, version in frozen["software"].items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f"generation environment changed: {package}")
    requests = read_jsonl(output / "requests.jsonl")
    ledger = output / "generation_events.jsonl"
    previous = events(ledger)
    done = {r["request_id"]: r for r in previous if r["kind"] == "terminal"}
    attempted = {r["request_id"] for r in previous if r["kind"] == "attempt"}
    if attempted - set(done):
        raise ValueError("interrupted generation outcome is uncertain; no automatic reroll")
    torch.set_num_threads(config["torch_num_threads"])
    pipe = AutoPipelineForText2Image.from_pretrained(
        root / frozen["model_path"], torch_dtype=torch.float16,
        variant=config["variant"], local_files_only=True,
    ).to(config["device"])
    pipe.enable_attention_slicing(config["attention_slicing"])
    pipe.set_progress_bar_config(disable=True)
    image_dir = root / WORKSPACE / experiment_id / "generated"
    image_dir.mkdir(parents=True, exist_ok=True)
    for index, request in enumerate(requests):
        request_id = request["request_id"]
        if request_id in done:
            if done[request_id]["status"] == "generated":
                if hash_file(root / done[request_id]["image_path"]) != done[request_id]["sha256"]:
                    raise ValueError("generated evidence changed")
            continue
        append_event(ledger, dict(kind="attempt", request_id=request_id,
                                 request_sha256=digest(request)))
        outcome = dict(kind="terminal", request_id=request_id, block=request["block"],
                       template_id=request["template_id"], condition=request["condition"])
        try:
            generator = torch.Generator(device="cpu").manual_seed(request["seed"])
            with torch.inference_mode():
                result = pipe(
                    prompt=request["prompt"], generator=generator,
                    width=config["width"], height=config["height"],
                    num_inference_steps=config["num_inference_steps"],
                    guidance_scale=config["guidance_scale"],
                )
            image = result.images[0]
            image_path = image_dir / f"{request_id}.png"
            if image_path.exists():
                raise FileExistsError("unrecorded output must not be overwritten")
            image.save(image_path, format="PNG")
            outcome.update(status="generated", image_path=str(image_path.relative_to(root)),
                           sha256=hash_file(image_path), width=image.width, height=image.height,
                           safety_flag=getattr(result, "nsfw_content_detected", None))
        except (RuntimeError, ValueError, OSError) as exc:
            outcome.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        done[request_id] = append_event(ledger, outcome)
        if (index + 1) % 10 == 0:
            print(f"generation {index + 1}/{len(requests)} "
                  f"{dict(Counter(r['status'] for r in done.values()))}", flush=True)
    ordered = [done[r["request_id"]] for r in requests]
    publish(output / "outputs.jsonl", ordered, lines=True)
    receipt = dict(
        experiment_id=experiment_id, completed_at_utc=utc_now().isoformat(),
        statuses=dict(Counter(r["status"] for r in ordered)),
        expected_requests=len(requests), terminal_requests=len(ordered),
        complete_generated_grid=all(r["status"] == "generated" for r in ordered),
        freeze_sha256=hash_file(freeze_path), ledger_sha256=hash_file(ledger),
        outputs_sha256=hash_file(output / "outputs.jsonl"),
    )
    publish(output / "generation_receipt.json", receipt)
    return receipt
