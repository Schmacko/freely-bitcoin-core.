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
import struct
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
    def test_manifest_comparison_rejects_boolean_integer_aliases(self):
        self.assertFalse(MINER.matches_exact_json({"workers": True}, {"workers": 1}))
        self.assertFalse(MINER.matches_exact_json({"workers": False}, {"workers": 0}))
        self.assertTrue(MINER.matches_exact_json(
            {"job_id": "job", "workers": 1},
            {"job_id": "job", "workers": 1},
        ))

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

    def test_worker_refuses_checkpoint_beyond_nonce_space(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "worker-000.json"
            checkpoint.write_text(json.dumps({
                "job_id": "expected-job", "worker_id": 0,
                "workers": 1, "chunk_size": 1,
                "next_nonce": MINER.MAX_U32 + 2,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nonce sequence"):
                MINER.worker(0, 1, 0, 1, bytes(76), 1, "expected-job",
                             temporary, StopFlag())

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

    def test_worker_refuses_checkpoint_with_boolean_topology_fields(self):
        for field in ("worker_id", "workers", "chunk_size"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                state = {
                    "job_id": "expected-job", "worker_id": 0,
                    "workers": 1, "chunk_size": 1, "next_nonce": 0,
                }
                state[field] = True
                checkpoint = Path(temporary) / "worker-000.json"
                checkpoint.write_text(json.dumps(state), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "does not match"):
                    MINER.worker(0, 1, 0, 1, bytes(76), 1, "expected-job",
                                 temporary, StopFlag())

    def test_worker_refuses_boolean_checkpoint_nonce(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "worker-000.json"
            checkpoint.write_text(json.dumps({
                "job_id": "expected-job", "worker_id": 0,
                "workers": 1, "chunk_size": 1, "next_nonce": True,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "next_nonce must be an integer"):
                MINER.worker(0, 1, 0, 1, bytes(76), 1, "expected-job",
                             temporary, StopFlag())

    def test_worker_refuses_checkpoint_from_different_topology(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary) / "worker-000.json"
            checkpoint.write_text(json.dumps({
                "job_id": "expected-job", "worker_id": 0,
                "workers": 2, "chunk_size": 1, "next_nonce": 0,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                MINER.worker(0, 1, 0, 1, bytes(76), 1, "expected-job",
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


    def test_approved_freely_genesis_header_vector(self):
        merkle_root = "c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1"
        expected_hash = "0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78"
        timestamp = 1_794_960_000
        bits = 0x1D00FFFF
        nonce = 2_238_688_522
        prefix = (MINER.struct.pack("<i", 1) + bytes(32)
                  + bytes.fromhex(merkle_root)[::-1]
                  + MINER.struct.pack("<II", timestamp, bits))
        header = prefix + MINER.struct.pack("<I", nonce)

        digest = MINER.hash256(header)
        target = MINER.decode_compact(bits)
        pow_limit = int("00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff", 16)

        self.assertEqual(len(header), 80)
        self.assertEqual(digest[::-1].hex(), expected_hash)
        self.assertLessEqual(int.from_bytes(digest, "little"), target)
        self.assertLessEqual(target, pow_limit)

    def test_approved_freely_genesis_coinbase_and_merkle_root(self):
        # Independently serialize the approved C++ coinbase without using
        # Bitcoin Core's CScript or transaction serializer.
        def push_data(data):
            if len(data) >= 76:
                raise ValueError("this regression only needs direct pushes below 76 bytes")
            return bytes((len(data),)) + data

        timestamp_message = b"FREELY FLY genesis 2026-11-18"
        output_message = b"FREELY FLY GENESIS"
        # CScript << 486604799 << CScriptNum(4) << vector(timestamp).
        script_sig = (
            push_data((486604799).to_bytes(4, "little"))
            + push_data(bytes((0x04,)))
            + push_data(timestamp_message)
        )
        script_pub_key = bytes((0x6A,)) + push_data(output_message)

        coinbase = b"".join((
            struct.pack("<i", 1),                 # transaction version
            bytes((1,)),                            # one input
            bytes(32),                            # null prevout hash
            struct.pack("<I", 0xFFFFFFFF),        # null prevout index
            bytes((len(script_sig),)),
            script_sig,
            struct.pack("<I", 0xFFFFFFFF),        # final sequence
            bytes((1,)),                            # one output
            struct.pack("<q", 50 * 100_000_000),  # 50 FLY, 8 decimals
            bytes((len(script_pub_key),)),
            script_pub_key,
            struct.pack("<I", 0),                 # locktime
        ))

        txid = hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()[::-1].hex()
        expected = "c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1"
        self.assertEqual(len(coinbase), 117)
        self.assertEqual(txid, expected)
        # A one-transaction genesis block's Merkle root is the coinbase txid.
        merkle_root = txid
        self.assertEqual(merkle_root, expected)


if __name__ == "__main__":
    unittest.main()
