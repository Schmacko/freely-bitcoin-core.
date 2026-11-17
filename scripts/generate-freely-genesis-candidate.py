#!/usr/bin/env python3
"""Generate a reproducible FREELY genesis coinbase candidate (not a full block).

The script validates its transaction serializer against Bitcoin's known genesis
coinbase txid, then emits a candidate FREELY coinbase txid/Merkle root. It does
not select block time, powLimit, nBits, nonce, or a production genesis hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct

COIN = 100_000_000
GENESIS_REWARD = 50 * COIN
DEFAULT_MESSAGE = "FREELY — Freedom Through Decentralisation"
BITCOIN_GENESIS_MESSAGE = b"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
BITCOIN_GENESIS_PUBKEY = bytes.fromhex(
    "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f"
)
BITCOIN_GENESIS_TXID = "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"


def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def compact_size(value: int) -> bytes:
    if value < 0:
        raise ValueError("CompactSize cannot encode a negative value")
    if value < 253:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + struct.pack("<H", value)
    if value <= 0xFFFFFFFF:
        return b"\xfe" + struct.pack("<I", value)
    return b"\xff" + struct.pack("<Q", value)


def encode_script_number(value: int) -> bytes:
    if value == 0:
        return b""
    negative = value < 0
    absolute = -value if negative else value
    result = bytearray()
    while absolute:
        result.append(absolute & 0xFF)
        absolute >>= 8
    if result[-1] & 0x80:
        result.append(0x80 if negative else 0)
    elif negative:
        result[-1] |= 0x80
    return bytes(result)


def push_data(data: bytes) -> bytes:
    length = len(data)
    if length <= 75:
        return bytes([length]) + data
    if length <= 0xFF:
        return b"\x4c" + bytes([length]) + data
    if length <= 0xFFFF:
        return b"\x4d" + struct.pack("<H", length) + data
    raise ValueError("genesis script push is unexpectedly large")


def push_script_number(value: int) -> bytes:
    if value == -1:
        return b"\x4f"
    if value == 0:
        return b"\x00"
    if 1 <= value <= 16:
        return bytes([0x50 + value])
    return push_data(encode_script_number(value))


def serialize_coinbase(timestamp: bytes, output_script: bytes, amount: int = GENESIS_REWARD) -> bytes:
    script_sig = (
        push_script_number(486604799)
        + push_data(encode_script_number(4))
        + push_data(timestamp)
    )
    tx = (
        struct.pack("<i", 1)
        + b"\x01"
        + bytes(32)
        + struct.pack("<I", 0xFFFFFFFF)
        + compact_size(len(script_sig))
        + script_sig
        + struct.pack("<I", 0xFFFFFFFF)
        + b"\x01"
        + struct.pack("<q", amount)
        + compact_size(len(output_script))
        + output_script
        + struct.pack("<I", 0)
    )
    return tx


def display_hash(raw_hash: bytes) -> str:
    return raw_hash[::-1].hex()


def decode_compact_target(bits: int) -> int:
    """Decode Bitcoin's compact target and reject negative/zero/overflow values."""
    if not 0 <= bits <= 0xFFFFFFFF:
        raise ValueError("nBits must fit in uint32")
    size = bits >> 24
    word = bits & 0x007FFFFF
    negative = word != 0 and bool(bits & 0x00800000)
    overflow = word != 0 and (
        size > 34 or (word > 0xFF and size > 33) or (word > 0xFFFF and size > 32)
    )
    if negative:
        raise ValueError("compact target is negative")
    if overflow:
        raise ValueError("compact target overflows 256 bits")
    if size <= 3:
        target = word >> (8 * (3 - size))
    else:
        target = word << (8 * (size - 3))
    if target == 0:
        raise ValueError("compact target decodes to zero")
    return target


def verify_genesis_header(
    merkle_root: str, block_time: int, bits: int, nonce: int, pow_limit_hex: str
) -> dict[str, str | int]:
    """Serialize and verify an 80-byte candidate genesis header using explicit inputs."""
    if not 0 <= block_time <= 0xFFFFFFFF:
        raise ValueError("block time must fit in uint32")
    if not 0 <= nonce <= 0xFFFFFFFF:
        raise ValueError("nonce must fit in uint32")
    if len(merkle_root) != 64:
        raise ValueError("Merkle root must be exactly 32 bytes of hex")
    if len(pow_limit_hex) != 64:
        raise ValueError("powLimit must be exactly 32 bytes of hex")
    try:
        merkle_wire = bytes.fromhex(merkle_root)[::-1]
        pow_limit = int(pow_limit_hex, 16)
    except ValueError as exc:
        raise ValueError("Merkle root and powLimit must be valid hexadecimal") from exc
    target = decode_compact_target(bits)
    if target > pow_limit:
        raise ValueError("decoded nBits target exceeds the supplied powLimit")
    header = (
        struct.pack("<i", 1)
        + bytes(32)
        + merkle_wire
        + struct.pack("<III", block_time, bits, nonce)
    )
    if len(header) != 80:
        raise RuntimeError("serialized genesis header is not 80 bytes")
    raw_hash = hash256(header)
    hash_value = int.from_bytes(raw_hash, "little")
    if hash_value > target:
        raise ValueError("candidate header does not satisfy proof of work")
    return {
        "header_hex": header.hex(),
        "block_hash": display_hash(raw_hash),
        "target_hex": f"{target:064x}",
        "pow_limit_hex": f"{pow_limit:064x}",
    }


def verify_synthetic_header_fixture(merkle_root: str) -> dict[str, str | int]:
    """Exercise header serialization/PoW with synthetic test-only parameters."""
    synthetic_pow_limit = "7f" + "ff" * 31
    result = verify_genesis_header(
        merkle_root, 1_700_000_000, 0x207FFFFF, 1, synthetic_pow_limit
    )
    if result["block_hash"] != "6801d3dee3797d9893f3568d2dba2bd3a8ecc729cea407ab91dd50598a02f01a":
        raise RuntimeError("synthetic genesis header hash self-check failed")
    try:
        verify_genesis_header(
            merkle_root, 1_700_000_000, 0x207FFFFF, 0, synthetic_pow_limit
        )
    except ValueError as exc:
        if "does not satisfy proof of work" not in str(exc):
            raise
    else:
        raise RuntimeError("synthetic invalid-nonce header unexpectedly passed proof of work")
    return result


def verify_bitcoin_genesis_serialization() -> None:
    bitcoin_output = push_data(BITCOIN_GENESIS_PUBKEY) + b"\xac"
    serialized = serialize_coinbase(BITCOIN_GENESIS_MESSAGE, bitcoin_output)
    actual = display_hash(hash256(serialized))
    if actual != BITCOIN_GENESIS_TXID:
        raise RuntimeError(
            "Bitcoin genesis serialization self-check failed: "
            f"expected {BITCOIN_GENESIS_TXID}, got {actual}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", default=DEFAULT_MESSAGE,
                        help="candidate coinbase timestamp/message; final wording requires approval")
    parser.add_argument("--time", type=int, default=None,
                        help="optional candidate block timestamp as Unix seconds; not a final parameter")
    parser.add_argument("--n-bits", type=lambda value: int(value, 0), default=None,
                        help="optional compact target (for example 0x1d00ffff); candidate only")
    parser.add_argument("--nonce", type=int, default=None,
                        help="optional candidate nonce; candidate only")
    parser.add_argument("--pow-limit", default=None,
                        help="optional 32-byte big-endian powLimit hex; candidate only")
    parser.add_argument("--self-test-header", action="store_true",
                        help="run a deterministic synthetic header/PoW fixture; selects no production values")
    args = parser.parse_args()

    if not args.message:
        parser.error("--message must not be empty")
    if args.time is not None and not 0 <= args.time <= 0xFFFFFFFF:
        parser.error("--time must fit in the unsigned 32-bit block-header timestamp")
    header_args = (args.n_bits, args.nonce, args.pow_limit)
    if any(value is not None for value in header_args) and not all(value is not None for value in header_args):
        parser.error("--n-bits, --nonce and --pow-limit must be supplied together")
    if args.self_test_header and any(value is not None for value in header_args):
        parser.error("--self-test-header cannot be combined with explicit header inputs")

    verify_bitcoin_genesis_serialization()
    timestamp = args.message.encode("utf-8")
    output_script = b"\x6a"  # OP_RETURN: provably unspendable
    transaction = serialize_coinbase(timestamp, output_script)
    txid = display_hash(hash256(transaction))
    header_result = None
    if args.self_test_header:
        header_result = verify_synthetic_header_fixture(txid)
    elif all(value is not None for value in header_args):
        if args.time is None:
            parser.error("--time is required when explicit header inputs are supplied")
        try:
            header_result = verify_genesis_header(
                txid, args.time, args.n_bits, args.nonce, args.pow_limit
            )
        except ValueError as exc:
            parser.error(str(exc))

    result = {
        "status": "candidate_only_not_production",
        "message": args.message,
        "block_time_candidate_unix": args.time,
        "coinbase": {
            "version": 1,
            "script_sig_hex": (
                push_script_number(486604799)
                + push_data(encode_script_number(4))
                + push_data(timestamp)
            ).hex(),
            "output_value_base_units": GENESIS_REWARD,
            "output_value_fly": "50.00000000",
            "output_script_hex": output_script.hex(),
            "output_provably_unspendable": True,
            "serialized_transaction_hex": transaction.hex(),
            "txid": txid,
            "merkle_root_for_single_transaction_block": txid,
        },
        "header": {
            "version": 1,
            "previous_block_hash": "00" * 32,
            "merkle_root": txid,
            "time": args.time,
            "n_bits": args.n_bits,
            "nonce": args.nonce,
            "block_hash": None if header_result is None else header_result["block_hash"],
            "serialized_header_hex": None if header_result is None else header_result["header_hex"],
            "decoded_target_hex": None if header_result is None else header_result["target_hex"],
            "pow_limit_hex": args.pow_limit if args.pow_limit is not None else (
                "7f" + "ff" * 31 if args.self_test_header else None
            ),
            "header_verification": (
                "synthetic_test_fixture_passed" if args.self_test_header else (
                    "candidate_header_proof_of_work_passed" if header_result is not None else "not_run"
                )
            ),
        },
        "owner_approved_accounting": {
            "scheduled_issuance_fly": "20999999.97690000",
            "spendable_scheduled_subsidy_fly": "20999949.97690000",
            "genesis_reward_spendable": False,
        },
        "warning": (
            "Candidate transaction only. The message and optional time are not final; "
            "powLimit, genesis nBits, nonce and full genesis block hash are unresolved."
        ),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
