#!/usr/bin/env python3
"""Restartable, parallel SHA256d nonce search for an approved FREELY genesis header.

This utility does not select consensus parameters. Supply the approved Merkle
root, timestamp, nBits and powLimit explicitly. Each worker owns a disjoint
nonce sequence and checkpoints only completed chunks, so interrupted work can
resume without silently skipping unfinished ranges.
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

MAX_NONCE = 0xFFFFFFFF


def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def decode_compact(bits: int) -> int:
    if not 0 <= bits <= 0xFFFFFFFF:
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


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def worker(worker_id: int, workers: int, start_nonce: int, chunk_size: int,
           header_prefix: bytes, target: int, checkpoint_dir: str,
           found_path: str, stop_event) -> None:
    directory = Path(checkpoint_dir)
    checkpoint = directory / f"worker-{worker_id:03d}.json"
    found = Path(found_path)
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text(encoding="utf-8"))
        if state.get("worker_id") != worker_id or state.get("workers") != workers:
            raise ValueError("checkpoint worker topology differs; use a fresh checkpoint directory")
        nonce = int(state["next_nonce"])
    else:
        nonce = start_nonce + worker_id

    tested = 0
    last_report = time.monotonic()
    while nonce <= MAX_NONCE and not stop_event.is_set():
        chunk_end = min(nonce + chunk_size * workers, MAX_NONCE + 1)
        while nonce < chunk_end and not stop_event.is_set():
            header = header_prefix + struct.pack("<I", nonce)
            digest = hash256(header)
            if int.from_bytes(digest, "little") <= target:
                atomic_json(found, {
                    "nonce": nonce,
                    "block_hash": digest[::-1].hex(),
                    "header_hex": header.hex(),
                    "worker_id": worker_id,
                    "verified": True,
                })
                stop_event.set()
                return
            nonce += workers
            tested += 1

        # Save only after this worker's entire assigned chunk is complete.
        atomic_json(checkpoint, {
            "worker_id": worker_id,
            "workers": workers,
            "next_nonce": nonce,
            "tested_by_worker": tested,
        })
        now = time.monotonic()
        if now - last_report >= 30:
            last_report = now


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--merkle-root", required=True, help="display-order 32-byte Merkle root")
    parser.add_argument("--time", required=True, type=int, help="approved uint32 block timestamp")
    parser.add_argument("--n-bits", required=True, type=lambda x: int(x, 0), help="approved compact target")
    parser.add_argument("--pow-limit", required=True, help="approved 32-byte big-endian powLimit hex")
    parser.add_argument("--start-nonce", type=int, default=0)
    parser.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    parser.add_argument("--chunk-size", type=int, default=100_000,
                        help="nonce attempts per worker checkpoint interval")
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    args = parser.parse_args()

    if len(args.merkle_root) != 64 or any(c not in "0123456789abcdefABCDEF" for c in args.merkle_root):
        parser.error("--merkle-root must be exactly 64 hexadecimal characters")
    if len(args.pow_limit) != 64 or any(c not in "0123456789abcdefABCDEF" for c in args.pow_limit):
        parser.error("--pow-limit must be exactly 64 hexadecimal characters")
    if not 0 <= args.time <= MAX_NONCE or not 0 <= args.start_nonce <= MAX_NONCE:
        parser.error("time and start nonce must fit uint32")
    if args.workers < 1 or args.chunk_size < 1:
        parser.error("--workers and --chunk-size must be positive")
    target = decode_compact(args.n_bits)
    pow_limit = int(args.pow_limit, 16)
    if target > pow_limit:
        parser.error("decoded nBits target exceeds approved powLimit")

    # Bitcoin block-header wire serialization: version, previous hash,
    # internal-order Merkle root, timestamp, nBits; nonce is appended per try.
    prefix = (struct.pack("<i", 1) + bytes(32)
              + bytes.fromhex(args.merkle_root)[::-1]
              + struct.pack("<II", args.time, args.n_bits))
    if len(prefix) != 76:
        raise RuntimeError("header prefix must be exactly 76 bytes")

    args.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    found_path = str(args.checkpoint_dir / "FOUND.json")
    if Path(found_path).exists():
        result = json.loads(Path(found_path).read_text(encoding="utf-8"))
        print(json.dumps({"status": "previous_result_found", **result}, indent=2))
        return 0

    context = mp.get_context("spawn")
    stop_event = context.Event()
    processes = [
        context.Process(
            target=worker,
            args=(i, args.workers, args.start_nonce, args.chunk_size, prefix,
                  target, str(args.checkpoint_dir), found_path, stop_event),
        )
        for i in range(args.workers)
    ]
    started = time.monotonic()
    for process in processes:
        process.start()
    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        stop_event.set()
        for process in processes:
            process.join()
        print("Interrupted safely; completed worker chunks are checkpointed.")
        return 130

    if Path(found_path).exists():
        result = json.loads(Path(found_path).read_text(encoding="utf-8"))
        header = bytes.fromhex(result["header_hex"])
        digest = hash256(header)
        if len(header) != 80 or digest[::-1].hex() != result["block_hash"]:
            raise RuntimeError("found nonce failed independent local header re-verification")
        if int.from_bytes(digest, "little") > target:
            raise RuntimeError("found nonce does not satisfy the approved target")
        print(json.dumps({"status": "nonce_found_and_verified",
                          "elapsed_seconds": round(time.monotonic() - started, 3),
                          **result}, indent=2))
        return 0

    failed = [p.exitcode for p in processes if p.exitcode not in (0, None)]
    if failed:
        raise RuntimeError(f"nonce workers exited abnormally: {failed}")
    print(json.dumps({
        "status": "nonce_space_exhausted",
        "message": "No valid nonce remains at or above the supplied start nonce.",
        "checkpoint_dir": str(args.checkpoint_dir),
    }, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
