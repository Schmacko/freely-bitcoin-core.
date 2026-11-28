import copy
import json
import unittest
from pathlib import Path

from check_network_safety import validate


MANIFEST = json.loads(Path(__file__).with_name("network-safety.json").read_text(encoding="utf-8"))


def complete_fixture():
    # Use the pinned, independently reproduced genesis candidate and approved policy.
    return copy.deepcopy(MANIFEST)


class NetworkSafetyTests(unittest.TestCase):
    def test_rejects_boolean_schema_version(self):
        data = complete_fixture()
        data["schema_version"] = True
        self.assertTrue(any("schema_version must be the integer 1" in item for item in validate(data)))

    def test_candidate_genesis_commitment_is_pinned_and_reproducible(self):
        self.assertEqual(validate(MANIFEST), [])
        self.assertEqual(MANIFEST["genesis"]["commitment_status"], "candidate_pending_owner_approval")
        self.assertEqual(MANIFEST["network"]["message_start"], "fac3b7d1")
        self.assertEqual(MANIFEST["network"]["p2p_port"], 49444)
        self.assertEqual(MANIFEST["network"]["rpc_port"], 49445)
        self.assertEqual(MANIFEST["genesis"]["hash"],
                         "0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78")
        self.assertEqual(MANIFEST["genesis"]["merkle_root"],
                         "c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1")
        self.assertEqual(MANIFEST["genesis"]["nonce"], 2238688522)
        self.assertEqual(MANIFEST["genesis"]["n_bits"], "0x1d00ffff")
        self.assertEqual(MANIFEST["genesis"]["pow_limit"], "0x00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
        self.assertIs(MANIFEST["genesis"]["coinbase_spendable"], False)
        self.assertIs(MANIFEST["consensus"]["bip94_enabled"], True)

    def test_rejects_unapproved_genesis_commitment_status(self):
        for status in ("final_approved", "production", None):
            with self.subTest(status=status):
                data = complete_fixture()
                data["genesis"]["commitment_status"] = status
                self.assertTrue(any("commitment_status must remain candidate_pending_owner_approval" in item
                                    for item in validate(data)))

    def test_rejects_mutated_genesis_commitment(self):
        for field, value in (
            ("hash", "11" * 32),
            ("merkle_root", "22" * 32),
            ("nonce", 2238688523),
        ):
            with self.subTest(field=field):
                data = complete_fixture()
                data["genesis"][field] = value
                self.assertTrue(any("independently reproduced FREELY genesis candidate" in item
                                    for item in validate(data)))

    def test_rejects_missing_owner_approved_policy_fields(self):
        data = complete_fixture()
        data["genesis"]["coinbase_spendable"] = None
        data["consensus"]["bip94_enabled"] = None
        errors = validate(data)
        self.assertTrue(any("genesis.coinbase_spendable is unset" in item for item in errors))
        self.assertTrue(any("consensus.bip94_enabled is unset" in item for item in errors))


    def test_rejects_mutation_of_owner_approved_parameter_values(self):
        mutations = (
            ("network", "message_start", "deadbeef"),
            ("network", "p2p_port", 49446),
            ("network", "rpc_port", 49447),
            ("address", "base58_public_key_prefix", 56),
            ("address", "base58_script_prefix", 118),
            ("address", "base58_secret_key_prefix", 184),
            ("address", "bech32_hrp", "flytest"),
            ("genesis", "timestamp", 1794960001),
            ("genesis", "coinbase_message", "unapproved message"),
            ("genesis", "coinbase_output_script", "6a00"),
            ("genesis", "coinbase_reward_base_units", 5_000_000_001),
            ("consensus", "retarget_min_timespan_seconds", 302399),
            ("consensus", "retarget_max_timespan_seconds", 4838401),
            ("consensus", "script_activation_heights", {"bip34": 2}),
        )
        for section, field, value in mutations:
            with self.subTest(section=section, field=field):
                data = complete_fixture()
                data[section][field] = value
                self.assertTrue(
                    any("owner-approved protocol parameter baseline" in item for item in validate(data)),
                    f"{section}.{field} mutation unexpectedly passed",
                )

    def test_rejects_unapproved_activation_or_version_bits_entries(self):
        data = complete_fixture()
        data["consensus"]["script_activation_heights"]["taproot"] = 1
        self.assertTrue(any("owner-approved protocol parameter baseline" in item for item in validate(data)))

        data = complete_fixture()
        data["consensus"]["version_bits"]["experimental"] = {
            "bit": 27,
            "start_time": -2,
            "timeout": 9223372036854775807,
            "min_activation_height": 0,
            "threshold": 1815,
            "period": 2016,
        }
        self.assertTrue(any("owner-approved protocol parameter baseline" in item for item in validate(data)))

    def test_rejects_partial_genesis_commitment(self):
        data = complete_fixture()
        data["genesis"]["nonce"] = None
        self.assertTrue(any("hash and genesis.nonce" in item for item in validate(data)))
        data = complete_fixture()
        data["genesis"]["hash"] = None
        self.assertTrue(any("genesis.hash is unset" in item for item in validate(data)))
        self.assertTrue(any("hash and genesis.nonce" in item for item in validate(data)))

    def test_rejects_invalid_genesis_nonce(self):
        for nonce in (True, -1, 0x100000000, "1"):
            with self.subTest(nonce=nonce):
                data = complete_fixture()
                data["genesis"]["nonce"] = nonce
                self.assertTrue(any("genesis.nonce must be an integer" in item for item in validate(data)))

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

    def test_rejects_default_signet_magic_collision(self):
        data = complete_fixture()
        data["network"]["message_start"] = "0a03cf40"
        self.assertTrue(any("existing Bitcoin network magic" in item for item in validate(data)))

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
        for unsafe_path in (
            "C:\\bitcoin", "..\\bitcoin", "\\\\server\\share",
            "../bitcoin", "/tmp/freely", ".", "..", "nested/freely", "nested\\freely",
        ):
            with self.subTest(data_directory=unsafe_path):
                data = complete_fixture()
                data["network"]["data_directory"] = unsafe_path
                self.assertTrue(any("absolute or traverse parent directories" in item for item in validate(data)))

    def test_accepts_owner_approved_data_directory_name(self):
        data = complete_fixture()
        data["network"]["data_directory"] = "freely"
        self.assertEqual(validate(data), [])

    def test_rejects_safe_but_unapproved_data_directory_name(self):
        data = complete_fixture()
        data["network"]["data_directory"] = "freely_node-1"
        self.assertTrue(any("owner-approved protocol parameter baseline" in item for item in validate(data)))

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
        # A deliberately tiny limit must reject the otherwise valid approved
        # compact target, independently of the owner-approved-value check.
        data["genesis"]["pow_limit"] = "0x1"
        self.assertTrue(any("exceeds genesis.pow_limit" in item for item in validate(data)))

    def test_rejects_out_of_range_genesis_fields_and_activation_heights(self):
        data = complete_fixture()
        data["genesis"]["n_bits"] = "0x100000000"
        data["genesis"]["pow_limit"] = "0x1" + "0" * 64
        data["consensus"]["script_activation_heights"] = {"segwit": -1}
        errors = validate(data)
        self.assertTrue(any("32-bit compact" in item for item in errors))
        self.assertTrue(any("256 bits" in item for item in errors))
        self.assertTrue(any("activation height" in item for item in errors))

    def test_rejects_empty_script_activation_matrix(self):
        data = complete_fixture()
        data["consensus"]["script_activation_heights"] = {}
        self.assertTrue(any("script_activation_heights must be a non-empty object" in item for item in validate(data)))


if __name__ == "__main__":
    unittest.main()
