import copy
import json
import unittest
from pathlib import Path

from check_network_safety import validate


MANIFEST = json.loads(Path(__file__).with_name("network-safety.json").read_text(encoding="utf-8"))


def complete_fixture():
    data = copy.deepcopy(MANIFEST)
    data["network"].update({
        "message_start": "fabfb5da",
        "p2p_port": 18444,
        "rpc_port": 18443,
        "data_directory": "freely",
    })
    data["address"].update({
        "base58_public_key_prefix": 111,
        "base58_script_prefix": 196,
        "bech32_hrp": "fly",
    })
    data["genesis"].update({
        "hash": "11" * 32,
        "n_bits": "0x207fffff",
        "pow_limit": "0x7fffff" + "00" * 29,
        "coinbase_spendable": False,
    })
    data["consensus"].update({
        "bip94_enabled": False,
        "script_activation_heights": {},
    })
    return data


class NetworkSafetyTests(unittest.TestCase):
    def test_unconfigured_template_fails_closed(self):
        errors = validate(MANIFEST)
        self.assertTrue(any("network.message_start is unset" in item for item in errors))
        self.assertTrue(any("genesis.coinbase_spendable is unset" in item for item in errors))
        self.assertTrue(any("consensus.bip94_enabled is unset" in item for item in errors))

    def test_complete_distinct_fixture_passes(self):
        self.assertEqual(validate(complete_fixture()), [])

    def test_rejects_bitcoin_mainnet_magic_and_ports(self):
        data = complete_fixture()
        data["network"]["message_start"] = "f9beb4d9"
        data["network"]["p2p_port"] = 8333
        data["network"]["rpc_port"] = 8332
        errors = validate(data)
        self.assertTrue(any("Bitcoin mainnet magic" in item for item in errors))
        self.assertTrue(any("Bitcoin mainnet port 8333" in item for item in errors))
        self.assertTrue(any("Bitcoin mainnet port 8332" in item for item in errors))

    def test_rejects_bitcoin_address_identity(self):
        data = complete_fixture()
        data["address"].update({
            "base58_public_key_prefix": 0,
            "base58_script_prefix": 5,
            "bech32_hrp": "bc",
        })
        errors = validate(data)
        self.assertTrue(any("public_key_prefix" in item and "Bitcoin mainnet" in item for item in errors))
        self.assertTrue(any("script_prefix" in item and "Bitcoin mainnet" in item for item in errors))
        self.assertTrue(any("must not be 'bc'" in item for item in errors))

    def test_rejects_bitcoin_genesis(self):
        data = complete_fixture()
        data["genesis"]["hash"] = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
        self.assertTrue(any("Bitcoin mainnet genesis" in item for item in validate(data)))

    def test_rejects_invalid_ports_and_equal_ports(self):
        data = complete_fixture()
        data["network"]["p2p_port"] = 70000
        data["network"]["rpc_port"] = 70000
        errors = validate(data)
        self.assertTrue(any("from 1 to 65535" in item for item in errors))
        self.assertTrue(any("must be different" in item for item in errors))

    def test_rejects_malformed_magic_and_genesis_hash(self):
        data = complete_fixture()
        data["network"]["message_start"] = "xyz"
        data["genesis"]["hash"] = "not-a-hash"
        errors = validate(data)
        self.assertTrue(any("exactly 4 bytes" in item for item in errors))
        self.assertTrue(any("64 hex characters" in item for item in errors))

    def test_rejects_malformed_sections_without_crashing(self):
        data = complete_fixture()
        data["project"] = []
        data["network"] = "not-an-object"
        data["consensus"] = None
        errors = validate(data)
        self.assertTrue(any("project must be a JSON object" in item for item in errors))
        self.assertTrue(any("network must be a JSON object" in item for item in errors))
        self.assertTrue(any("consensus must be a JSON object" in item for item in errors))

    def test_enforces_approved_retarget_policy(self):
        data = complete_fixture()
        data["consensus"]["target_spacing_seconds"] = 300
        data["consensus"]["retarget_interval"] = True
        data["consensus"]["allow_min_difficulty_blocks"] = True
        errors = validate(data)
        self.assertTrue(any("target_spacing_seconds" in item for item in errors))
        self.assertTrue(any("retarget_interval" in item for item in errors))
        self.assertTrue(any("allow_min_difficulty_blocks must remain false" in item for item in errors))

    def test_rejects_out_of_range_genesis_fields_and_activation_heights(self):
        data = complete_fixture()
        data["genesis"]["n_bits"] = "0x100000000"
        data["genesis"]["pow_limit"] = "0x1" + "0" * 64
        data["genesis"]["coinbase_spendable"] = 0
        data["consensus"]["script_activation_heights"] = {"taproot": -1}
        errors = validate(data)
        self.assertTrue(any("unsigned 32-bit" in item for item in errors))
        self.assertTrue(any("must not exceed 256 bits" in item for item in errors))
        self.assertTrue(any("coinbase_spendable" in item for item in errors))
        self.assertTrue(any("non-negative integer" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
