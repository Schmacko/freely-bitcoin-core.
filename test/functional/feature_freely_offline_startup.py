#!/usr/bin/env python3
# Copyright (c) 2026 The FREELY contributors
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Exercise the approved FREELY candidate in explicitly isolated offline mode."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, assert_raises_rpc_error


GENESIS_HASH = "0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78"


class FreelyOfflineStartupTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.chain = "freely"
        self.bind_to_localhost_only = False
        self.setup_clean_chain = True
        self.disable_autoconnect = True
        # Retain the framework's connect=0 setting to disable automatic
        # outbound connections, including addresses restored from peers.dat.
        self.extra_args = [[
            "-freelydev=1",
            "-listen=0",
            "-dnsseed=0",
            "-discover=0",
            "-natpmp=0",
            "-upnp=0",
            "-listenonion=0",
        ]]

    def run_test(self):
        node = self.nodes[0]

        chain_info = node.getblockchaininfo()
        assert_equal(chain_info["chain"], "freely")
        assert_equal(chain_info["blocks"], 0)
        assert_equal(node.getblockhash(0), GENESIS_HASH)

        genesis = node.getblockheader(GENESIS_HASH)
        assert_equal(genesis["height"], 0)
        assert_equal(genesis["nonce"], 2238688522)
        assert_equal(genesis["bits"], "1d00ffff")

        # This first-stage mode is deliberately offline: it cannot listen for
        # inbound peers and the chain-parameter gate rejects outbound peers.
        assert_equal(node.getnetworkinfo()["connections"], 0)
        assert_equal(node.getpeerinfo(), [])
        assert_raises_rpc_error(-8, "FREELY offline mode does not permit peer connections.",
                                node.addnode, "127.0.0.1:49444", "onetry")


if __name__ == "__main__":
    FreelyOfflineStartupTest(__file__).main()
