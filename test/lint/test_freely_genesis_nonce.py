#!/usr/bin/env python3
# Copyright (c) 2026 The FREELY developers
# Distributed under the MIT software license.

"""Focused unit tests for the standalone FREELY genesis nonce-search helper.

Run from the repository root with:
    python3 test/lint/test_freely_genesis_nonce.py
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "mine-freely-genesis-nonce.py"
SPEC = importlib.util.spec_from_file_location("freely_genesis_nonce", SCRIPT)
MINER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MINER)


class StopFlag:
    def __init__(self):
        self.stopped = False

    def is_set(self):
        return self.stopped

    def set(self):
        self.stopped = True


class GenesisNonceSearchTest(unittest.TestCase):
    def test_hash256_is_sha256d(self):
        expected = hashlib.sha256(hashlib.sha256(b"").digest()).digest()
        self.assertEqual(MINER.hash256(b""), expected)

    def test_decode_approved_compact_target(self):
        self.assertEqual(MINER.decode_compact(0x1D00FFFF),
                         0xFFFF << (8 * (0x1D - 3)))

    def test_decode_compact_rejects_negative_zero_and_overflow(self):
        for bits in (0x1D80FFFF, 0x01000000, 0x23000001):
            with self.subTest(bits=hex(bits)):
                with self.assertRaises(ValueError):
                    MINER.decode_compact(bits)

    def test_worker_finds_and_persists_exact_header(self):
        timestamp = 1_800_000_000
        bits = 0x1D00FFFF
        prefix = (MINER.struct.pack("<i", 1) + bytes(32) + bytes(32)
                  + MINER.struct.pack("<II", timestamp, bits))
        nonce = 17
        header = prefix + MINER.struct.pack("<I", nonce)
        target = int.from_bytes(MINER.hash256(header), "little")
        job_id = "unit-test-job"

        with tempfile.TemporaryDirectory() as temporary:
            stop = StopFlag()
            MINER.worker(0, 1, nonce, 1, prefix, target, job_id, temporary, stop)
            result_path = Path(temporary) / "FOUND.json"
            result = json.loads(result_path.read_text(encoding="utf-8"))
            digest = MINER.hash256(header)
            self.assertTrue(stop.is_set())
            self.assertEqual(result["job_id"], job_id)
            self.assertEqual(result["nonce"], nonce)
            self.assertEqual(result["header_hex"], header.hex())
            self.assertEqual(result["block_hash"], digest[::-1].hex())
            self.assertLessEqual(int.from_bytes(digest, "little"), target)

    def test_worker_refuses_misaligned_checkpoint_nonce(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "worker-001.json"
            checkpoint.write_text(json.dumps({
                "job_id": "expected-job", "worker_id": 1,
                "workers": 3, "chunk_size": 1, "next_nonce": 5,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nonce sequence"):
                MINER.worker(1, 3, 0, 1, bytes(76), 1, "expected-job",
                             temporary, StopFlag())

    def test_worker_refuses_checkpoint_from_another_job(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "worker-000.json"
            checkpoint.write_text(json.dumps({
                "job_id": "different-job", "worker_id": 0,
                "workers": 1, "chunk_size": 1, "next_nonce": 0,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                MINER.worker(0, 1, 0, 1, bytes(76), 1, "expected-job",
                             temporary, StopFlag())


if __name__ == "__main__":
    unittest.main()
