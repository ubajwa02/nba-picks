"""Small on-disk result cache for research code (data/cache/, git-ignored).

A cached value is keyed by sha256 of: the function name, its parameters (JSON), a data
version, and a fingerprint of every source file it depends on. Large files are
fingerprinted by size + mtime (cheap); files under ``CONTENT_HASH_MAX`` bytes (code,
config) by their content, so editing a model file invalidates results computed with it.
``refresh=True`` recomputes and overwrites. Writes are atomic (temp file + rename), so an
interrupted run never leaves a half-written entry.
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import tempfile

CACHE_DIR = "data/cache"
DATA_VERSION = 1
CONTENT_HASH_MAX = 1 << 20

stats = {"hits": 0, "misses": 0}


def fingerprint(paths) -> list:
    out = []
    for p in sorted(set(map(str, paths))):
        if not os.path.exists(p):
            out.append([p, None])
            continue
        st = os.stat(p)
        if st.st_size <= CONTENT_HASH_MAX:
            with open(p, "rb") as fh:
                out.append([p, "sha256:" + hashlib.sha256(fh.read()).hexdigest()])
        else:
            out.append([p, st.st_size, st.st_mtime_ns])
    return out


def make_key(name: str, params, sources=(), version: int = DATA_VERSION) -> str:
    blob = json.dumps(dict(name=name, params=params, sources=fingerprint(sources), version=version),
                      sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def path_for(name: str, key: str, cache_dir: str = CACHE_DIR, fmt: str = "pickle") -> str:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return os.path.join(cache_dir, f"{safe}-{key[:20]}.{'pkl' if fmt == 'pickle' else 'json'}")


def cached(name: str, params, sources, compute, *, refresh: bool = False, cache_dir: str = CACHE_DIR,
           version: int = DATA_VERSION, fmt: str = "pickle"):
    """Return compute() from the cache when the key matches, else compute and store it."""
    key = make_key(name, params, sources, version)
    path = path_for(name, key, cache_dir, fmt)
    if not refresh and os.path.exists(path):
        try:
            with open(path, "rb" if fmt == "pickle" else "r") as fh:
                val = pickle.load(fh) if fmt == "pickle" else json.load(fh)
            stats["hits"] += 1
            return val
        except Exception:
            pass   # unreadable entry: recompute
    stats["misses"] += 1
    val = compute()
    os.makedirs(cache_dir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=cache_dir, suffix=".part")
    try:
        with os.fdopen(fd, "wb" if fmt == "pickle" else "w") as fh:
            if fmt == "pickle":
                pickle.dump(val, fh, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                json.dump(val, fh, default=str)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return val
