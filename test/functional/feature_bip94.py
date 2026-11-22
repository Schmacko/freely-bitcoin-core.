# Copyright (c) 2026 The FREELY developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the BIP94 first-block-of-period timestamp constraint."""

from test_framework.blocktools import create_block, create_coinbase
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import assert_equal


class BIP94TimewarpTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True
        # This test-only option enables the upstream BIP94 path on regtest.
        # It does not configure or activate FREELY production parameters.
        self.extra_args = [["-test=bip94"]]

    def run_test(self):
        node = self.nodes[0]
        assert_equal(node.getblockchaininfo()["chain"], "regtest")
        assert_equal(node.getblockcount(), 0)
        tip_hash = int(node.getbestblockhash(), 16)
        genesis = node.getblockheader(node.getbestblockhash())
        genesis_time = genesis["time"]
        tip_time = genesis_time

        # Regtest's difficulty period is 144 blocks. Build heights 1..143
        # with 600-second timestamp increments so the candidate boundary
        # block can be earlier than the previous block while remaining above
        # median-time-past.
        for height in range(1, 144):
            block = create_block(
                tip_hash,
                create_coinbase(height),
                ntime=genesis_time + height * 600,
                height=height,
            )
            block.solve()
            assert_equal(node.submitblock(block.serialize().hex()), None)
            tip_hash = block.hash_int
            tip_time = block.nTime

        assert_equal(node.getblockcount(), 143)

        # Height 144 is the first block of a new difficulty period. A
        # timestamp 601 seconds before the previous block is still above MTP
        # in this fixture, so only the BIP94 rule should reject it.
        invalid = create_block(
            tip_hash,
            create_coinbase(144),
            ntime=tip_time - 601,
            height=144,
        )
        invalid.solve()
        assert_equal(
            node.submitblock(invalid.serialize().hex()),
            "time-timewarp-attack",
        )
        assert_equal(node.getblockcount(), 143)

        # The exact 600-second grace boundary is valid.
        valid = create_block(
            tip_hash,
            create_coinbase(144),
            ntime=tip_time - 600,
            height=144,
        )
        valid.solve()
        assert_equal(node.submitblock(valid.serialize().hex()), None)
        assert_equal(node.getblockcount(), 144)


if __name__ == "__main__":
    BIP94TimewarpTest(__file__).main()
