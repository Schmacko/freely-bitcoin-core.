#!/usr/bin/env python3
"""Validate the FREELY network-identity and consensus-parameter manifest.

This is a preflight validator, not a replacement for Core's startup checks.
It deliberately fails while the derived genesis commitment and required production-readiness evidence are incomplete, even when all owner-approved parameters are populated.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

BITCOIN_NETWORKS = {
    "main": {"message_start": "f9beb4d9", "p2p_port": 8333, "rpc_port": 8332, "data_directory": "", "bech32_hrp": "bc"},
    "testnet3": {"message_start": "0b110907", "p2p_port": 18333, "rpc_port": 18332, "data_directory": "testnet3", "bech32_hrp": "tb"},
    "testnet4": {"message_start": "1c163f28", "p2p_port": 48333, "rpc_port": 48332, "data_directory": "testnet4", "bech32_hrp": "tb"},
    # Default BIP325 signet challenge magic; custom challenges derive a different magic and require runtime collision validation.
    "signet": {"message_start": "0a03cf40", "p2p_port": 38333, "rpc_port": 38332, "data_directory": "signet", "bech32_hrp": "tb"},
    "regtest": {"message_start": "fabfb5da", "p2p_port": 18444, "rpc_port": 18443, "data_directory": "regtest", "bech32_hrp": "bcrt"},
}
BITCOIN_BASE58_PREFIXES = {
    "base58_public_key_prefix": {0, 111},
    "base58_script_prefix": {5, 196},
    "base58_secret_key_prefix": {128, 239},
}
BITCOIN_EXTENDED_KEY_PREFIXES = {
    "base58_extended_public_key_prefix": {"0488b21e", "043587cf"},
    "base58_extended_secret_key_prefix": {"0488ade4", "04358394"},
}
ALL_BITCOIN_BASE58_PREFIXES = set().union(*BITCOIN_BASE58_PREFIXES.values())
ALL_BITCOIN_EXTENDED_KEY_PREFIXES = set().union(*BITCOIN_EXTENDED_KEY_PREFIXES.values())
BITCOIN_GENESIS_HASH = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"

# Owner-approved values from docs/FREELY-APPROVED-PROTOCOL-PARAMETERS.md.
# The genesis nonce and block hash are derived outputs and remain unset until
# the approved candidate header has been mined and independently reproduced.
APPROVED_VALUES = {
    "network": {
        "message_start": "fac3b7d1",
        "p2p_port": 49444,
        "rpc_port": 49445,
        "data_directory": "freely",
        "config_section": "freely",
    },
    "address": {
        "base58_public_key_prefix": 55,
        "base58_script_prefix": 117,
        "base58_secret_key_prefix": 183,
        "base58_extended_public_key_prefix": "04464c59",
        "base58_extended_secret_key_prefix": "04666c79",
        "bech32_hrp": "fly",
    },
    "genesis": {
        "timestamp": 1794960000,
        "version": 1,
        "n_bits": "0x1d00ffff",
        "pow_limit": "0x00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "coinbase_message": "FREELY FLY genesis 2026-11-18",
        "coinbase_output_script": "6a12465245454c5920464c592047454e45534953",
        "coinbase_spendable": False,
    },
    "consensus": {
        "target_spacing_seconds": 600,
        "target_timespan_seconds": 1209600,
        "retarget_interval": 2016,
        "retarget_min_timespan_seconds": 302400,
        "retarget_max_timespan_seconds": 4838400,
        "allow_min_difficulty_blocks": False,
        "no_retargeting": False,
        "bip94_enabled": True,
        "script_activation_heights": {
            "bip34": 1,
            "bip65": 1,
            "bip66": 1,
            "csv": 1,
            "segwit": 1,
        },
        "min_bip9_warning_height": 0,
        "version_bits": {
            "testdummy": {
                "bit": 28,
                "start_time": -2,
                "timeout": 9223372036854775807,
                "min_activation_height": 0,
                "threshold": 1815,
                "period": 2016,
            },
        },
        "taproot_witness_v1": "verify using Bitcoin Core v32.1 script flags; no separate chain-parameter activation field",
    },
}


def matches_approved(actual: Any, expected: Any) -> bool:
    """Compare JSON values without Python's bool/int equality ambiguity."""
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and all(key in actual and matches_approved(actual[key], value) for key, value in expected.items())
        )
    return type(actual) is type(expected) and actual == expected


REQUIRED_PATHS = (
    "network.message_start",
    "network.p2p_port",
    "network.rpc_port",
    "network.data_directory",
    "network.config_section",
    "address.base58_public_key_prefix",
    "address.base58_script_prefix",
    "address.base58_secret_key_prefix",
    "address.base58_extended_public_key_prefix",
    "address.base58_extended_secret_key_prefix",
    "address.bech32_hrp",
    "genesis.hash",
    "genesis.nonce",
    "genesis.n_bits",
    "genesis.pow_limit",
    "genesis.coinbase_spendable",
    "consensus.target_timespan_seconds",
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


def decode_compact_target(compact: int) -> int | None:
    """Decode Bitcoin's unsigned compact target; return None for invalid/zero targets."""
    size = compact >> 24
    word = compact & 0x007FFFFF
    negative = word != 0 and (compact & 0x00800000) != 0
    overflow = word != 0 and (
        size > 34 or (word > 0xFF and size > 33) or (word > 0xFFFF and size > 32)
    )
    if negative or overflow:
        return None
    if size <= 3:
        target = word >> (8 * (3 - size))
    else:
        target = word << (8 * (size - 3))
    return target if target > 0 else None


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        errors.append("schema_version must be the integer 1")
    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("project must be a JSON object")
        project = {}
    if project.get("name") != "FREELY" or project.get("ticker") != "FLY":
        errors.append("project identity must be FREELY / FLY")

    for path in REQUIRED_PATHS:
        if at_path(data, path) is None:
            errors.append(f"{path} is unset; production configuration is fail-closed")

    sections = {}
    for section in ("network", "address", "genesis", "consensus"):
        value = data.get(section)
        if not isinstance(value, dict):
            errors.append(f"{section} must be a JSON object")
            value = {}
        sections[section] = value
    network = sections["network"]
    address = sections["address"]
    genesis = sections["genesis"]
    consensus = sections["consensus"]

    for section, expected_values in APPROVED_VALUES.items():
        for field, expected in expected_values.items():
            if not matches_approved(sections[section].get(field), expected):
                errors.append(f"{section}.{field} differs from the owner-approved protocol parameter baseline")

    magic = network.get("message_start")
    if magic is not None:
        if not isinstance(magic, str) or not re.fullmatch(r"[0-9a-fA-F]{8}", magic):
            errors.append("network.message_start must be exactly 4 bytes encoded as 8 hex characters")
        elif any(magic.lower() == item["message_start"] for item in BITCOIN_NETWORKS.values() if item["message_start"]):
            errors.append("network.message_start collides with an existing Bitcoin network magic")

    for field in ("p2p_port", "rpc_port"):
        value = network.get(field)
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 65535:
                errors.append(f"network.{field} must be an integer from 1 to 65535")
            elif value in {
                item[port_field]
                for item in BITCOIN_NETWORKS.values()
                for port_field in ("p2p_port", "rpc_port")
            }:
                errors.append(f"network.{field} collides with a reserved Bitcoin network TCP port")
    if network.get("p2p_port") is not None and network.get("p2p_port") == network.get("rpc_port"):
        errors.append("P2P and RPC ports must be different")

    datadir = network.get("data_directory")
    if datadir is not None:
        if not isinstance(datadir, str) or not datadir.strip():
            errors.append("network.data_directory must be a non-empty relative directory name")
        elif not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", datadir):
            # This value is a single data-directory suffix, not an arbitrary path.
            # Restricting it to one portable path component rejects POSIX and
            # Windows separators, drive paths, UNC paths, dot segments and
            # traversal regardless of the host running this validator.
            errors.append("network.data_directory must not be absolute or traverse parent directories; use one safe directory name")
        elif datadir.casefold() in {item["data_directory"].casefold() for item in BITCOIN_NETWORKS.values()}:
            errors.append("network.data_directory collides with an existing Bitcoin network directory")
    config_section = network.get("config_section")
    if config_section is not None and config_section != "freely":
        errors.append("network.config_section must be the canonical 'freely' section name")


    for field in BITCOIN_BASE58_PREFIXES:
        value = address.get(field)
        if value is not None:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 255:
                errors.append(f"address.{field} must be an integer from 0 to 255")
            elif value in ALL_BITCOIN_BASE58_PREFIXES:
                errors.append(f"address.{field} collides with an existing Bitcoin network prefix")

    base58_values = [address.get(field) for field in BITCOIN_BASE58_PREFIXES]
    if all(type(value) is int for value in base58_values) and len(set(base58_values)) != len(base58_values):
        errors.append("FREELY Base58 public-key, script, and secret-key prefixes must be distinct")

    for field in ("base58_extended_public_key_prefix", "base58_extended_secret_key_prefix"):
        value = address.get(field)
        if value is not None:
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{8}", value):
                errors.append(f"address.{field} must be exactly 4 bytes encoded as 8 hex characters")
            elif value.lower() in ALL_BITCOIN_EXTENDED_KEY_PREFIXES:
                errors.append(f"address.{field} collides with an existing Bitcoin network extended-key prefix")

    extended_values = [address.get(field) for field in BITCOIN_EXTENDED_KEY_PREFIXES]
    if all(isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{8}", value) for value in extended_values):
        if len({value.lower() for value in extended_values}) != len(extended_values):
            errors.append("FREELY extended public and private key prefixes must be distinct")

    hrp = address.get("bech32_hrp")
    if hrp is not None:
        if not isinstance(hrp, str) or not re.fullmatch(r"[a-z]{1,83}", hrp):
            errors.append("address.bech32_hrp must be 1-83 lowercase letters")
        elif hrp in {item["bech32_hrp"] for item in BITCOIN_NETWORKS.values()}:
            errors.append("address.bech32_hrp collides with an existing Bitcoin network HRP")

    genesis_hash = genesis.get("hash")
    genesis_nonce = genesis.get("nonce")
    if genesis_nonce is not None:
        if not isinstance(genesis_nonce, int) or isinstance(genesis_nonce, bool) or not 0 <= genesis_nonce <= 0xFFFFFFFF:
            errors.append("genesis.nonce must be an integer from 0 to 4294967295")
    if (genesis_hash is None) != (genesis_nonce is None):
        errors.append("genesis.hash and genesis.nonce must either both be unset or both be set")
    if genesis_hash is not None:
        if not isinstance(genesis_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", genesis_hash):
            errors.append("genesis.hash must be a 32-byte hash encoded as 64 hex characters")
        elif genesis_hash.lower() == BITCOIN_GENESIS_HASH:
            errors.append("genesis.hash reuses Bitcoin mainnet genesis")
        elif int(genesis_hash, 16) == 0:
            errors.append("genesis.hash must not be the all-zero hash")

    for field in ("n_bits", "pow_limit"):
        value = genesis.get(field)
        if value is not None:
            if field == "n_bits":
                valid_format = isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{1,8}", value)
            else:
                valid_format = isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]+", value)
            if not valid_format or int(value, 16) == 0:
                if field == "n_bits":
                    errors.append("genesis.n_bits must be a non-zero 32-bit compact value encoded as 1-8 hexadecimal digits with a 0x prefix")
                else:
                    errors.append("genesis.pow_limit must be a non-zero hexadecimal string such as '0x1d00ffff'")
            elif field == "pow_limit" and int(value, 16).bit_length() > 256:
                errors.append("genesis.pow_limit must not exceed 256 bits")

    if genesis.get("coinbase_spendable") is not None:
        if not isinstance(genesis.get("coinbase_spendable"), bool):
            errors.append("genesis.coinbase_spendable must be explicitly true or false")
        elif genesis.get("coinbase_spendable") is not False:
            errors.append("genesis.coinbase_spendable must be false under the owner-approved FREELY genesis accounting")

    compact_value = genesis.get("n_bits")
    pow_limit_value = genesis.get("pow_limit")
    if (
        isinstance(compact_value, str)
        and re.fullmatch(r"0x[0-9a-fA-F]{1,8}", compact_value)
        and int(compact_value, 16) <= 0xFFFFFFFF
        and isinstance(pow_limit_value, str)
        and re.fullmatch(r"0x[0-9a-fA-F]+", pow_limit_value)
        and 0 < int(pow_limit_value, 16).bit_length() <= 256
    ):
        target = decode_compact_target(int(compact_value, 16))
        if target is None:
            errors.append("genesis.n_bits encodes a negative, zero, or overflowing compact target")
        elif target > int(pow_limit_value, 16):
            errors.append("genesis.n_bits target exceeds genesis.pow_limit")

    for field, expected in (
        ("target_spacing_seconds", 600),
        ("target_timespan_seconds", 1_209_600),
        ("retarget_interval", 2016),
    ):
        value = consensus.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value != expected:
            errors.append(f"consensus.{field} must match the approved value {expected}")

    for field in ("allow_min_difficulty_blocks", "no_retargeting", "bip94_enabled"):
        value = consensus.get(field)
        if not isinstance(value, bool):
            errors.append(f"consensus.{field} must be explicitly true or false")
        elif field in ("allow_min_difficulty_blocks", "no_retargeting") and value is not False:
            errors.append(f"consensus.{field} must remain false under the approved policy")
        elif field == "bip94_enabled" and value is not True:
            errors.append("consensus.bip94_enabled must be true under the owner-approved FREELY policy")

    activations = consensus.get("script_activation_heights")
    if activations is not None:
        if not isinstance(activations, dict):
            errors.append("consensus.script_activation_heights must be a JSON object")
        elif not activations:
            errors.append("consensus.script_activation_heights must contain at least one explicit activation entry")
        else:
            for deployment, height in activations.items():
                if not isinstance(deployment, str) or not deployment:
                    errors.append("script activation names must be non-empty strings")
                if not isinstance(height, int) or isinstance(height, bool) or height < 0:
                    errors.append(f"script activation height for {deployment!r} must be a non-negative integer")

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
