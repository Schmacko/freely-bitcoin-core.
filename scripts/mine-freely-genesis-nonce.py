#!/usr/bin/env python3
"""Restartable parallel SHA256d search for an explicitly supplied FREELY genesis header.

This tool never selects consensus parameters. It searches only the header
specified by the operator and binds checkpoints/results to that exact job.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import struct
import time

MAX_U32 = 0xFFFFFFFF


def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def decode_compact(bits: int) -> int:
    if not 0 <= bits <= MAX_U32:
        raise ValueError("nBits must fit uint32")
    size, word = bits >> 24, bits & 0x007FFFFF
    negative = word != 0 and bool(bits & 0x00800000)
    overflow = word != 0 and (
        size > 34 or (word > 0xFF and size > 33) or (word > 0xFFFF and size > 32)
    )
    if negative or overflow:
        raise ValueError("nBits encodes a negative or overflowing target")
    target = word >> (8 * (3 - size)) if size <= 3 else word << (8 * (size - 3))
    if target == 0:
        raise ValueError("nBits target must be nonzero")
    return target


def atomic_json(path: Path, value: dict) -> None:
    # Include the process ID so simultaneous workers cannot clobber the same
    # temporary file when more than one worker discovers a valid nonce.
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def worker(worker_id: int, workers: int, start_nonce: int, chunk_size: int,
           prefix: bytes, target: int, job_id: str, directory: str,
           stop_event) -> None:
    root = Path(directory)
    checkpoint = root / f"worker-{worker_id:03d}.json"
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        if (state.get("job_id") != job_id or state.get("worker_id") != worker_id
                or state.get("workers") != workers or state.get("chunk_size") != chunk_size):
            raise ValueError("checkpoint does not match this exact search job/topology")
        nonce = int(state["next_nonce"])
        first_nonce = start_nonce + worker_id
        if (nonce < first_nonce or nonce > MAX_U32 + workers
                or (nonce - first_nonce) % workers != 0):
            raise ValueError("checkpoint next_nonce is outside this worker's nonce sequence")
    else:
        nonce = start_nonce + worker_id

    tested = 0
    while nonce <= MAX_U32 and not stop_event.is_set():
        end = min(nonce + chunk_size * workers, MAX_U32 + 1)
        while nonce < end and not stop_event.is_set():
            header = prefix + struct.pack("<I", nonce)
            digest = hash256(header)
            if int.from_bytes(digest, "little") <= target:
                atomic_json(root / "FOUND.json", {
                    "job_id": job_id, "nonce": nonce,
                    "block_hash": digest[::-1].hex(), "header_hex": header.hex(),
                    "worker_id": worker_id,
                })
                stop_event.set()
                return
            nonce += workers
            tested += 1
        # Persist only fully completed chunks; unfinished work is retried.
        atomic_json(checkpoint, {
            "job_id": job_id, "worker_id": worker_id, "workers": workers,
            "chunk_size": chunk_size, "next_nonce": nonce, "tested": tested,
        })


def worker_entry(*args) -> None:
    """Stop sibling workers promptly if one worker encounters an error."""
    stop_event = args[-1]
    try:
        worker(*args)
    except BaseException:
        stop_event.set()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merkle-root", required=True, help="display-order 32-byte Merkle root")
    parser.add_argument("--time", required=True, type=int, help="approved uint32 timestamp")
    parser.add_argument("--n-bits", required=True, type=lambda x: int(x, 0))
    parser.add_argument("--pow-limit", required=True, help="32-byte big-endian powLimit hex")
    parser.add_argument("--start-nonce", type=int, default=0)
    parser.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    args = parser.parse_args()

    for name, value in (("merkle-root", args.merkle_root), ("pow-limit", args.pow_limit)):
        if len(value) != 64 or any(c not in "0123456789abcdefABCDEF" for c in value):
            parser.error(f"--{name} must be exactly 64 hexadecimal characters")
    if not 0 <= args.time <= MAX_U32 or not 0 <= args.start_nonce <= MAX_U32:
        parser.error("timestamp and start nonce must fit uint32")
    if args.workers < 1 or args.chunk_size < 1:
        parser.error("workers and chunk-size must be positive")
    target = decode_compact(args.n_bits)
    pow_limit = int(args.pow_limit, 16)
    if pow_limit == 0:
        parser.error("--pow-limit must be nonzero")
    if target > pow_limit:
        parser.error("decoded nBits target exceeds supplied powLimit")

    prefix = (struct.pack("<i", 1) + bytes(32)
              + bytes.fromhex(args.merkle_root)[::-1]
              + struct.pack("<II", args.time, args.n_bits))
    if len(prefix) != 76:
        raise RuntimeError("serialized header prefix must be 76 bytes")
    job = {
        "header_prefix_hex": prefix.hex(), "target_hex": f"{target:064x}",
        "pow_limit_hex": f"{pow_limit:064x}", "start_nonce": args.start_nonce,
        "workers": args.workers, "chunk_size": args.chunk_size,
    }
    job_id = hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()
    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.checkpoint_dir / "JOB.json"
    if manifest.exists():
        if json.loads(manifest.read_text(encoding="utf-8")) != {"job_id": job_id, **job}:
            parser.error("checkpoint directory belongs to a different search job; choose a fresh directory")
    else:
        # Refuse to adopt an unlabelled directory containing old state.
        if any(args.checkpoint_dir.iterdir()):
            parser.error("checkpoint directory is non-empty but has no matching JOB.json")
        atomic_json(manifest, {"job_id": job_id, **job})

    found_path = args.checkpoint_dir / "FOUND.json"
    if found_path.exists():
        found = json.loads(found_path.read_text(encoding="utf-8"))
        if found.get("job_id") != job_id:
            parser.error("saved result belongs to a different search job")
        header = bytes.fromhex(found["header_hex"])
        digest = hash256(header)
        nonce = int(found["nonce"])
        if (len(header) != 80 or header != prefix + struct.pack("<I", nonce)
                or digest[::-1].hex() != found["block_hash"]
                or int.from_bytes(digest, "little") > target):
            raise RuntimeError("saved nonce failed exact-header proof-of-work re-verification")
        print(json.dumps({"status": "nonce_found_and_verified", **found}, indent=2))
        return 0

    context = mp.get_context("spawn")
    stop = context.Event()
    processes = [context.Process(
        target=worker_entry,
        args=(i, args.workers, args.start_nonce, args.chunk_size, prefix,
              target, job_id, str(args.checkpoint_dir), stop),
    ) for i in range(args.workers)]
    started = time.monotonic()
    for process in processes:
        process.start()
    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        stop.set()
        for process in processes:
            process.join()
        print("Interrupted safely; completed worker chunks are checkpointed.")
        return 130

    if found_path.exists():
        found = json.loads(found_path.read_text(encoding="utf-8"))
        header = bytes.fromhex(found["header_hex"])
        digest = hash256(header)
        if (found.get("job_id") != job_id or len(header) != 80
                or header[:76] != prefix or digest[::-1].hex() != found["block_hash"]
                or int.from_bytes(digest, "little") > target):
            raise RuntimeError("found nonce failed exact-header proof-of-work re-verification")
        print(json.dumps({
            "status": "nonce_found_and_verified",
            "elapsed_seconds": round(time.monotonic() - started, 3), **found,
        }, indent=2))
        return 0

    failures = [p.exitcode for p in processes if p.exitcode not in (0, None)]
    if failures:
        raise RuntimeError(f"nonce workers exited abnormally: {failures}")
    print(json.dumps({
        "status": "nonce_space_exhausted",
        "checkpoint_dir": str(args.checkpoint_dir),
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
