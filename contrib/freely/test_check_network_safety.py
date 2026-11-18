import copy
import json
import unittest
from pathlib import Path

from check_network_safety import validate


MANIFEST = json.loads(Path(__file__).with_name("network-safety.json").read_text(encoding="utf-8"))


def complete_fixture():
    data = copy.deepcopy(MANIFEST)
    data["network"].update({
        "message_start": "deadbeef",
        "p2p_port": 29444,
        "rpc_port": 29443,
        "data_directory": "freely",
        "config_section": "freely",
    })
    data["address"].update({
        "base58_public_key_prefix": 55,
        "base58_script_prefix": 56,
        "base58_secret_key_prefix": 57,
        "base58_extended_public_key_prefix": "01020304",
        "base58_extended_secret_key_prefix": "05060708",
        "bech32_hrp": "fly",
    })
    data["genesis"].update({
        "hash": "11" * 32,
        "n_bits": "0x207fffff",
        "pow_limit": "0x7fffff" + "00" * 29,
        "coinbase_spendable": False,
    })
    data["consensus"].update({
        "bip94_enabled": True,
        "script_activation_heights": {},
    })
    return data


class NetworkSafetyTests(unittest.TestCase):
    def test_rejects_boolean_schema_version(self):
        data = complete_fixture()
        data["schema_version"] = True
        self.assertTrue(any("schema_version must be the integer 1" in item for item in validate(data)))

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
        self.assertTrue(any("existing Bitcoin network magic" in item for item in errors))
        self.assertTrue(any("reserved Bitcoin network TCP port" in item for item in errors))
        self.assertTrue(any("reserved Bitcoin network TCP port" in item for item in errors))

    def test_rejects_bitcoin_address_identity(self):
        data = complete_fixture()
        data["address"].update({
            "base58_public_key_prefix": 111,
            "base58_script_prefix": 196,
            "base58_secret_key_prefix": 239,
            "base58_extended_public_key_prefix": "043587cf",
            "base58_extended_secret_key_prefix": "04358394",
            "bech32_hrp": "tb",
        })
        errors = validate(data)
        self.assertTrue(any("public_key_prefix" in item and "existing Bitcoin network" in item for item in errors))
        self.assertTrue(any("script_prefix" in item and "existing Bitcoin network" in item for item in errors))
        self.assertTrue(any("collides with an existing Bitcoin network HRP" in item for item in errors))

    def test_rejects_bitcoin_extended_wallet_prefixes(self):
        data = complete_fixture()
        data["address"]["base58_extended_public_key_prefix"] = "0488b21e"
        data["address"]["base58_extended_secret_key_prefix"] = "0488ade4"
        errors = validate(data)
        self.assertTrue(any("extended_public_key_prefix" in item and "existing Bitcoin network" in item for item in errors))
        self.assertTrue(any("extended_secret_key_prefix" in item and "existing Bitcoin network" in item for item in errors))

    def test_rejects_testnet_and_regtest_identity_collisions(self):
        data = complete_fixture()
        data["network"]["message_start"] = "0b110907"
        data["network"]["p2p_port"] = 48333
        data["network"]["rpc_port"] = 18443
        data["network"]["data_directory"] = "testnet4"
        data["address"]["bech32_hrp"] = "bcrt"
        errors = validate(data)
        self.assertGreaterEqual(sum("existing Bitcoin network" in item for item in errors), 3)
        self.assertTrue(any("directory" in item for item in errors))
        self.assertTrue(any("HRP" in item for item in errors))

    def test_rejects_unsafe_data_directory_paths_on_all_platforms(self):
        # The manifest field is a single directory suffix, not an arbitrary
        # path. Validate Windows and POSIX forms identically on every runner.
        for unsafe_path in (
            "C:\\bitcoin",
            "..\\bitcoin",
            "\\\\server\\share",
            "../bitcoin",
            "/tmp/freely",
            ".",
            "..",
            "nested/freely",
            "nested\\freely",
        ):
            with self.subTest(data_directory=unsafe_path):
                data = complete_fixture()
                data["network"]["data_directory"] = unsafe_path
                self.assertTrue(
                    any("absolute or traverse parent directories" in item for item in validate(data)),
                    msg=f"unsafe data directory was accepted: {unsafe_path!r}",
                )

    def test_accepts_single_safe_data_directory_name(self):
        data = complete_fixture()
        data["network"]["data_directory"] = "freely_node-1"
        self.assertEqual(validate(data), [])

    def test_rejects_unsafe_or_wrong_config_section(self):
        data = complete_fixture()
        data["network"]["data_directory"] = "../bitcoin"
        data["network"]["config_section"] = "main"
        errors = validate(data)
        self.assertTrue(any("traverse parent directories" in item for item in errors))
        self.assertTrue(any("canonical" in item for item in errors))

    def test_rejects_bitcoin_genesis(self):
        data = complete_fixture()
        data["genesis"]["hash"] = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
        self.assertTrue(any("Bitcoin mainnet genesis" in item for item in validate(data)))

    def test_rejects_cross_role_port_collisions(self):
        data = complete_fixture()
        data["network"]["p2p_port"] = 8332
        errors = validate(data)
        self.assertTrue(any("reserved Bitcoin network TCP port" in item for item in errors))

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

    def test_enforces_approved_bip94_policy(self):
        data = complete_fixture()
        data["consensus"]["bip94_enabled"] = False
        self.assertTrue(any("bip94_enabled must be true" in item for item in validate(data)))

    def test_candidate_network_identity_is_distinct_from_builtin_bitcoin(self):
        data = complete_fixture()
        data["network"].update({
            "message_start": "464c5931",
            "p2p_port": 19444,
            "rpc_port": 19443,
            "data_directory": "freely",
            "config_section": "freely",
        })
        data["address"].update({
            "base58_public_key_prefix": 35,
            "base58_script_prefix": 50,
            "base58_secret_key_prefix": 186,
            "base58_extended_public_key_prefix": "04464c59",
            "base58_extended_secret_key_prefix": "04464c5a",
            "bech32_hrp": "fly",
        })
        self.assertEqual(validate(data), [])

    def test_enforces_approved_retarget_policy(self):
        data = complete_fixture()
        data["consensus"]["target_spacing_seconds"] = 300
        data["consensus"]["retarget_interval"] = True
        data["consensus"]["allow_min_difficulty_blocks"] = True
        errors = validate(data)
        self.assertTrue(any("target_spacing_seconds" in item for item in errors))
        self.assertTrue(any("retarget_interval" in item for item in errors))
        self.assertTrue(any("allow_min_difficulty_blocks must remain false" in item for item in errors))

    def test_rejects_invalid_compact_genesis_targets(self):
        for compact in ("0x01000001", "0x20800001", "0x23010000"):
            data = complete_fixture()
            data["genesis"]["n_bits"] = compact
            self.assertTrue(any("negative, zero, or overflowing" in item for item in validate(data)))
        data = complete_fixture()
        data["genesis"]["pow_limit"] = "0x7ffffe" + "00" * 29
        self.assertTrue(any("exceeds genesis.pow_limit" in item for item in validate(data)))

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


    def test_rejects_spendable_genesis_coinbase(self):
        data = complete_fixture()
        data["genesis"]["coinbase_spendable"] = True
        self.assertTrue(any(
            "coinbase_spendable must be false" in item for item in validate(data)
        ))

    def test_rejects_cross_role_bitcoin_base58_prefix_collision(self):
        data = complete_fixture()
        # 5 is Bitcoin mainnet's P2SH prefix, not a safe FREELY P2PKH prefix.
        data["address"]["base58_public_key_prefix"] = 5
        self.assertTrue(any(
            "public_key_prefix" in item and "existing Bitcoin network prefix" in item
            for item in validate(data)
        ))

    def test_rejects_duplicate_freely_address_and_extended_key_prefixes(self):
        data = complete_fixture()
        data["address"]["base58_script_prefix"] = data["address"]["base58_public_key_prefix"]
        data["address"]["base58_extended_secret_key_prefix"] = data["address"]["base58_extended_public_key_prefix"]
        errors = validate(data)
        self.assertTrue(any("Base58 public-key, script, and secret-key prefixes must be distinct" in item for item in errors))
        self.assertTrue(any("extended public and private key prefixes must be distinct" in item for item in errors))

    def test_rejects_case_insensitive_bitcoin_data_directory_collision(self):
        data = complete_fixture()
        data["network"]["data_directory"] = "TESTNET3"
        self.assertTrue(any(
            "data_directory collides with an existing Bitcoin network directory" in item
            for item in validate(data)
        ))

    def test_rejects_unapproved_or_missing_target_timespan(self):
        data = complete_fixture()
        data["consensus"]["target_timespan_seconds"] = 1_209_599
        self.assertTrue(any(
            "target_timespan_seconds must match the approved value 1209600" in item
            for item in validate(data)
        ))

        del data["consensus"]["target_timespan_seconds"]
        self.assertTrue(any(
            "target_timespan_seconds must match the approved value 1209600" in item
            for item in validate(data)
        ))

    def test_rejects_compact_n_bits_wider_than_32_bits_even_with_leading_zeroes(self):
        data = complete_fixture()
        data["genesis"]["n_bits"] = "0x000000001"
        self.assertTrue(any(
            "1-8 hexadecimal digits" in item for item in validate(data)
        ))


if __name__ == "__main__":
    unittest.main()
