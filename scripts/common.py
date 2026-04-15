"""Shared utilities: OpenRouter client, caching, cost tracking, rate limiting."""
import os
import json
import time
import hashlib
import random
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI
import diskcache

load_dotenv(Path(__file__).parent.parent / ".env")

ROOT = Path(__file__).parent.parent
CACHE = diskcache.Cache(str(ROOT / "cache"))
COST_LOG = ROOT / "results" / "cost_log.jsonl"
COST_LOG.parent.mkdir(parents=True, exist_ok=True)

HARD_STOP_USD = 45.0

PRICING = {
    "anthropic/claude-sonnet-4": (3.0, 15.0),
    "meta-llama/llama-3.1-8b-instruct": (0.02, 0.05),
    "openai/text-embedding-3-small": (0.02, 0.0),
}

# Scale parameters (documented: reduced from spec's 100 papers / 120 questions
# to keep a single end-to-end run tractable. Pipeline is identical.)
N_PAPERS = int(os.environ.get("N_PAPERS", 30))
N_FACTUAL = int(os.environ.get("N_FACTUAL", 25))
N_SYNTHESIS = int(os.environ.get("N_SYNTHESIS", 25))
N_CONTRADICTION = int(os.environ.get("N_CONTRADICTION", 10))
BATCH_SIZE_WIKI = int(os.environ.get("BATCH_SIZE_WIKI", 5))  # papers per wiki batch

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


def cost_of(model: str, in_tok: int, out_tok: int) -> float:
    ip, op = PRICING.get(model, (0.0, 0.0))
    return (in_tok * ip + out_tok * op) / 1_000_000


def _cumulative_cost() -> float:
    if not COST_LOG.exists():
        return 0.0
    total = 0.0
    with open(COST_LOG) as f:
        for line in f:
            try:
                total += json.loads(line)["cost_usd"]
            except Exception:
                pass
    return total


def _log_cost(model: str, in_tok: int, out_tok: int):
    cost = cost_of(model, in_tok, out_tok)
    cum = _cumulative_cost() + cost
    rec = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": cost,
        "cumulative_usd": cum,
    }
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    if cum > HARD_STOP_USD:
        raise RuntimeError(f"HARD STOP: cumulative cost ${cum:.2f} > ${HARD_STOP_USD}")
    return cum


def _cache_key(model: str, messages, **kwargs) -> str:
    blob = json.dumps({"m": model, "msgs": messages, "kw": kwargs}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def chat(model: str, messages, max_tokens=2000, temperature=0.0, **kwargs):
    """Cached chat completion with retries + cost logging."""
    key = _cache_key(model, messages, max_tokens=max_tokens, temperature=temperature, **kwargs)
    cached = CACHE.get(key)
    if cached is not None:
        return cached

    sleep = 1.0 if "sonnet" in model else 2.0
    time.sleep(sleep)

    last_err = None
    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
            content = resp.choices[0].message.content or ""
            usage = resp.usage
            in_tok = usage.prompt_tokens if usage else 0
            out_tok = usage.completion_tokens if usage else 0
            cum = _log_cost(model, in_tok, out_tok)
            result = {
                "content": content,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "cumulative_cost": cum,
            }
            CACHE.set(key, result)
            return result
        except Exception as e:
            last_err = e
            wait = min(60, 5 * (2**attempt)) + random.random()
            print(f"  chat error ({type(e).__name__}): {e}; retry in {wait:.1f}s")
            time.sleep(wait)
    raise RuntimeError(f"chat failed after retries: {last_err}")


def embed(texts: list[str], model: str = "openai/text-embedding-3-small"):
    """Cached batch embedding."""
    out = [None] * len(texts)
    to_fetch_idx, to_fetch_text = [], []
    for i, t in enumerate(texts):
        k = _cache_key(model, [], text=t)
        c = CACHE.get(k)
        if c is not None:
            out[i] = c
        else:
            to_fetch_idx.append(i)
            to_fetch_text.append(t)
    # batch at 64
    for start in range(0, len(to_fetch_text), 64):
        batch = to_fetch_text[start : start + 64]
        idxs = to_fetch_idx[start : start + 64]
        for attempt in range(5):
            try:
                r = client.embeddings.create(model=model, input=batch)
                total_tok = r.usage.total_tokens if r.usage else sum(len(x) // 4 for x in batch)
                _log_cost(model, total_tok, 0)
                for j, d in zip(idxs, r.data):
                    emb = d.embedding
                    out[j] = emb
                    CACHE.set(_cache_key(model, [], text=texts[j]), emb)
                time.sleep(0.5)
                break
            except Exception as e:
                wait = min(60, 5 * (2**attempt))
                print(f"  embed error: {e}; retry in {wait}s")
                time.sleep(wait)
        else:
            raise RuntimeError("embed failed")
    return out


def cumulative_cost() -> float:
    return _cumulative_cost()


def print_cost():
    c = _cumulative_cost()
    print(f"[cost] cumulative: ${c:.4f}")


SONNET = "anthropic/claude-sonnet-4"
LLAMA8B = "meta-llama/llama-3.1-8b-instruct"
EMBED_MODEL = "openai/text-embedding-3-small"
