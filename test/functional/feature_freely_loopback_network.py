# Copyright (c) 2026 The FREELY contributors
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Verify FREELY private-node mode permits loopback peers only."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, assert_raises_rpc_error


GENESIS_HASH = "0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78"


class FreelyLoopbackNetworkTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.chain = "freely"
        self.setup_clean_chain = True
        # The framework binds each node to 127.0.0.1 and connects node 1 to
        # node 0 through the guarded addnode RPC. Automatic peers are disabled.
        self.extra_args = [[
            "-freelyprivate=1",
            "-discover=0",
            "-dnsseed=0",
            "-natpmp=0",
            "-listenonion=0",
        ] for _ in range(self.num_nodes)]

    def run_test(self):
        # setup_network connects node 1 to node 0 using a numeric loopback
        # address. Reject public addresses, hostnames, IPv4-mapped IPv6
        # spellings, and lookalike host strings. DNS must not change the
        # destination after the local-only policy has been checked.
        for peer_address in (
            "192.0.2.1:49444",
            "0.0.0.0:49444",
            "0.0.0.1:49444",
            "0.1.2.3:49444",
            "localhost:49444",
            "[::ffff:127.0.0.1]:49444",
            "[::FFFF:7f00:1]:49444",
            # Expanded mapped-IPv6 spellings normalize to IPv4 in CNetAddr.
            # They must remain rejected based on the original literal syntax.
            "[0:0:0:0:0:ffff:127.0.0.1]:49444",
            "[0:0:0:0:0:ffff:7f00:1]:49444",
            "0:0:0:0:0:ffff:7f00:1",
            "127.0.0.1.evil.example:49444",
            "127.0.0.1:invalid",
        ):
            assert_raises_rpc_error(
                -8,
                "FREELY loopback private mode only permits loopback peer addresses.",
                self.nodes[0].addnode,
                peer_address,
                "onetry",
            )

        # addconnection is a regtest-only RPC and must not bypass FREELY policy.
        assert_raises_rpc_error(
            -1,
            "addconnection is for regression testing (-regtest mode) only.",
            self.nodes[0].addconnection,
            "192.0.2.1:49444",
            "outbound-full-relay",
            False,
        )

        # Verify both nodes selected the exact candidate genesis and that the
        # only connected peer is a literal IPv4 loopback address. This test
        # deliberately does not mine: FREELY retains its production proof-of-
        # work target, unlike regtest's instant-mining target.
        for node in self.nodes:
            chain_info = node.getblockchaininfo()
            assert_equal(chain_info["chain"], "freely")
            assert_equal(chain_info["blocks"], 0)
            assert_equal(node.getblockhash(0), GENESIS_HASH)
            assert_equal(node.getnetworkinfo()["connections"], 1)
            peers = node.getpeerinfo()
            assert_equal(len(peers), 1)
            assert_equal(peers[0]["addr"].startswith("127.0.0.1:"), True)


if __name__ == "__main__":
    FreelyLoopbackNetworkTest(__file__).main()
