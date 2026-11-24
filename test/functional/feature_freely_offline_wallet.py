# Copyright (c) 2026 The FREELY contributors
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Verify FREELY wallet address encodings and persistence in offline mode."""

import hashlib
from decimal import Decimal

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def decode_base58check(value):
    number = 0
    for character in value:
        number = number * 58 + BASE58_ALPHABET.index(character)
    decoded = number.to_bytes((number.bit_length() + 7) // 8, "big")
    decoded = b"\x00" * (len(value) - len(value.lstrip("1"))) + decoded
    assert len(decoded) >= 5
    payload, checksum = decoded[:-4], decoded[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    assert_equal(checksum, expected)
    return payload


class FreelyOfflineWalletTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.chain = "freely"
        self.bind_to_localhost_only = False
        self.setup_clean_chain = True
        self.disable_autoconnect = True
        # Retain the framework's connect=0 setting to disable automatic
        # outbound connections, including addresses restored from peers.dat.
        # None keeps the wallet enabled when present without importing the
        # framework's regtest-only deterministic private key.
        self.uses_wallet = None
        self.extra_args = [[
            "-freelydev=1",
            "-listen=0",
            "-dnsseed=0",
            "-discover=0",
            "-natpmp=0",
            "-listenonion=0",
        ]]

    def run_test(self):
        node = self.nodes[0]
        wallet_name = "freely-wallet"
        node.createwallet(wallet_name=wallet_name, descriptors=True)
        wallet = node.get_wallet_rpc(wallet_name)

        # Exercise every standard address output type against the active
        # FREELY Base58 and Bech32 network parameters.
        addresses = {}
        for address_type in ("legacy", "p2sh-segwit", "bech32", "bech32m"):
            address = wallet.getnewaddress("", address_type)
            addresses[address_type] = address
            address_info = wallet.getaddressinfo(address)
            assert_equal(address_info["ismine"], True)
            assert_equal(address_info["address"], address)
            if address_type == "legacy":
                assert_equal(decode_base58check(address)[0], 55)
            elif address_type == "p2sh-segwit":
                assert_equal(decode_base58check(address)[0], 117)
            else:
                assert_equal(address.startswith("fly1"), True)

        # Exercise offline transaction signing for every supported FREELY
        # address family. The synthetic prevouts are supplied explicitly to
        # the signer; these transactions are deliberately not broadcast or
        # treated as spendable chain UTXOs.
        for index, (address_type, address) in enumerate(addresses.items()):
            prevout = {"txid": f"{index + 1:064x}", "vout": index}
            raw = node.createrawtransaction([prevout], {wallet.getnewaddress(): Decimal("0.9")})
            signed = wallet.signrawtransactionwithwallet(raw, [{
                **prevout,
                "scriptPubKey": wallet.getaddressinfo(address)["scriptPubKey"],
                "amount": Decimal("1.0"),
            }])
            assert_equal(signed["complete"], True)
            decoded = node.decoderawtransaction(signed["hex"])
            assert_equal(len(decoded["vin"]), 1)
            assert_equal(len(decoded["vout"]), 1)
            assert_equal(decoded["vout"][0]["value"], Decimal("0.9"))
            if address_type == "legacy":
                assert decoded["vin"][0]["scriptSig"]["hex"]
                assert "txinwitness" not in decoded["vin"][0]
            else:
                assert "txinwitness" in decoded["vin"][0]
                assert decoded["vin"][0]["txinwitness"]

        # Verify the approved WIF secret-key prefix as well as address
        # prefixes, without exposing or logging the generated private key.
        private_key = wallet.dumpprivkey(wallet.getnewaddress("", "legacy"))
        wif_payload = decode_base58check(private_key)
        assert_equal(wif_payload[0], 183)
        assert_equal(len(wif_payload), 34)
        assert_equal(wif_payload[-1], 1)

        default_address = wallet.getnewaddress()
        assert_equal(default_address.startswith("fly1"), True)
        assert_equal(wallet.getaddressinfo(default_address)["ismine"], True)

        # Verify wallet database recovery and key ownership after a clean restart.
        self.stop_node(0)
        self.start_node(0)
        node = self.nodes[0]
        node.loadwallet(wallet_name)
        wallet = node.get_wallet_rpc(wallet_name)
        assert_equal(wallet.getaddressinfo(default_address)["ismine"], True)
        assert_equal(wallet.getwalletinfo()["walletname"], wallet_name)


if __name__ == "__main__":
    FreelyOfflineWalletTest(__file__).main()
