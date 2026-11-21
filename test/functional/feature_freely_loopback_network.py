#!/usr/bin/env python3
# Copyright (c) 2026 The FREELY contributors
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Verify two FREELY nodes can connect over loopback only."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal, assert_raises_rpc_error, sync_blocks, sync_mempools


GENESIS_HASH = "0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78"


class FreelyLoopbackNetworkTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 2
        self.chain = "freely"
        self.setup_clean_chain = True
        # The framework writes connect=0, disabling automatic outbound peers.
        # Its manual addnode RPC below is restricted to loopback addresses.
        # The framework supplies bind=127.0.0.1 and unique local P2P ports.
        self.extra_args = [[
            "-freelyprivate=1",
            "-discover=0",
            "-dnsseed=0",
            "-upnp=0",
            "-natpmp=0",
            "-listenonion=0",
        ] for _ in range(self.num_nodes)]

    def run_test(self):
        # setup_network connects node 1 to node 0 using a loopback addnode RPC.
        # Reject public addresses, hostnames (even if they may resolve locally),
        # IPv4-mapped IPv6 spellings, and lookalike host strings. The policy is
        # intentionally literal-IP-only so DNS cannot change the trust boundary.
        for peer_address in (
            "192.0.2.1:49444",
            "0.0.0.0:49444",
            "0.0.0.1:49444",
            "0.1.2.3:49444",
            "localhost:49444",
            "[::ffff:127.0.0.1]:49444",
            "[::FFFF:7f00:1]:49444",
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
        assert_raises_rpc_error(-1, "addconnection is for regression testing (-regtest mode) only.",
                                self.nodes[0].addconnection, "192.0.2.1:49444",
                                "outbound-full-relay", False)
        for node in self.nodes:
            chain_info = node.getblockchaininfo()
            assert_equal(chain_info["chain"], "freely")
            assert_equal(chain_info["blocks"], 0)
            assert_equal(node.getblockhash(0), GENESIS_HASH)
            assert_equal(node.getnetworkinfo()["connections"], 1)
            peers = node.getpeerinfo()
            assert_equal(len(peers), 1)
            assert_equal(peers[0]["addr"].startswith("127.0.0.1:"), True)

        # Exercise real block propagation between the two isolated nodes.
        # The first node mines 101 blocks so its initial coinbase outputs have
        # reached maturity before funding a wallet transaction.
        miner = self.nodes[0]
        receiver = self.nodes[1]
        mining_address = miner.getnewaddress()
        miner.generatetoaddress(101, mining_address)
        sync_blocks(self.nodes)
        assert_equal(receiver.getblockcount(), 101)

        # Exercise transaction relay, mempool synchronization, block
        # propagation, and confirmation on the receiving node.
        destination = receiver.getnewaddress()
        txid = miner.sendtoaddress(destination, 1)
        sync_mempools(self.nodes)
        assert_equal(txid in receiver.getrawmempool(), True)

        confirmation_hash = miner.generatetoaddress(1, miner.getnewaddress())[0]
        sync_blocks(self.nodes)
        assert_equal(receiver.getblockhash(102), confirmation_hash)
        confirmed_block = receiver.getblock(confirmation_hash, 2)
        assert_equal(any(tx["txid"] == txid for tx in confirmed_block["tx"]), True)


if __name__ == "__main__":
    FreelyLoopbackNetworkTest(__file__).main()
