#!/usr/bin/env python3
"""Validate the FREELY network-identity and consensus-parameter manifest.

This is a preflight validator, not a replacement for Core's startup checks.
It deliberately fails while owner-approved production parameters are unset.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BITCOIN_MAINNET = {
    "message_start": "f9beb4d9",
    "p2p_port": 8333,
    "rpc_port": 8332,
    "data_directory": "bitcoin",
    "base58_public_key_prefix": 0,
    "base58_script_prefix": 5,
    "bech32_hrp": "bc",
    "genesis_hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172f1b60a8ce26f".replace(" ", ""),
}

REQUIRED_PATHS = (
    "network.message_start",
    "network.p2p_port",
    "network.rpc_port",
    "network.data_directory",
    "address.base58_public_key_prefix",
    "address.base58_script_prefix",
    "address.bech32_hrp",
    "genesis.hash",
    "genesis.n_bits",
    "genesis.pow_limit",
    "genesis.coinbase_spendable",
    "consensus.bip94_enabled",
    "consensus.script_activation_heights",
)


def at_path(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    project = data.get("project", {})
    if project.get("name") != "FREELY" or project.get("ticker") != "FLY":
        errors.append("project identity must be FREELY / FLY")

    for path in REQUIRED_PATHS:
        if at_path(data, path) is None:
            errors.append(f"{path} is unset; production configuration is fail-closed")

    network = data.get("network", {})
    address = data.get("address", {})
    genesis = data.get("genesis", {})
    consensus = data.get("consensus", {})

    magic = network.get("message_start")
    if magic is not None:
        if not isinstance(magic, str) or not re.fullmatch(r"[0-9a-fA-F]{8}", magic):
            errors.append("network.message_start must be exactly 4 bytes encoded as 8 hex characters")
        elif magic.lower() == BITCOIN_MAINNET["message_start"]:
            errors.append("network.message_start reuses Bitcoin mainnet magic")

    for field, forbidden in (("p2p_port", 8333), ("rpc_port", 8332)):
        value = network.get(field)
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 65535:
                errors.append(f"network.{field} must be an integer from 1 to 65535")
            elif value == forbidden:
                errors.append(f"network.{field} reuses Bitcoin mainnet port {forbidden}")
    if network.get("p2p_port") is not None and network.get("p2p_port") == network.get("rpc_port"):
        errors.append("P2P and RPC ports must be different")

    datadir = network.get("data_directory")
    if datadir is not None and (not isinstance(datadir, str) or not datadir.strip() or datadir.lower() == "bitcoin"):
        errors.append("network.data_directory must be non-empty and must not be Bitcoin's data directory")

    for field, forbidden in (("base58_public_key_prefix", 0), ("base58_script_prefix", 5)):
        value = address.get(field)
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 255:
                errors.append(f"address.{field} must be an integer from 0 to 255")
            elif value == forbidden:
                errors.append(f"address.{field} reuses Bitcoin mainnet prefix {forbidden}")

    hrp = address.get("bech32_hrp")
    if hrp is not None and (not isinstance(hrp, str) or not re.fullmatch(r"[a-z]{1,83}", hrp) or hrp == "bc"):
        errors.append("address.bech32_hrp must be 1-83 lowercase letters and must not be 'bc'")

    genesis_hash = genesis.get("hash")
    if genesis_hash is not None:
        if not isinstance(genesis_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", genesis_hash):
            errors.append("genesis.hash must be a 32-byte hash encoded as 64 hex characters")
        elif genesis_hash.lower() == BITCOIN_MAINNET["genesis_hash"]:
            errors.append("genesis.hash reuses Bitcoin mainnet genesis")

    for field in ("n_bits", "pow_limit"):
        value = genesis.get(field)
        if value is not None and (not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-fA-F]+", value) or int(value, 16) == 0):
            errors.append(f"genesis.{field} must be a non-zero hexadecimal string such as '0x1d00ffff'")

    for field in ("target_spacing_seconds", "retarget_interval"):
        value = consensus.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"consensus.{field} must be a positive integer")

    for field in ("allow_min_difficulty_blocks", "no_retargeting"):
        if not isinstance(consensus.get(field), bool):
            errors.append(f"consensus.{field} must be explicitly true or false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("network-safety.json"),
        help="path to the FREELY network-safety JSON manifest",
    )
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read manifest: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("ERROR: manifest root must be a JSON object", file=sys.stderr)
        return 2

    errors = validate(data)
    if errors:
        print(f"FREELY network preflight: BLOCKED ({len(errors)} issue(s))")
        for error in errors:
            print(f" - {error}")
        return 1
    print("FREELY network preflight: PASS")
    print("Manifest identity and required fields are internally consistent.")
    print("This does not replace consensus-code review, compilation, or runtime startup tests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
