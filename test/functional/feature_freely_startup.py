#!/usr/bin/env python3
# Copyright (c) 2026 The FREELY developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Verify FREELY cannot start before its consensus and network parameters exist."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.test_node import ErrorMatch


class FreelyStartupFailClosedTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.setup_clean_chain = True

    def run_test(self):
        node = self.nodes[0]
        self.stop_node(0)

        # Deliberately do not pass -listen=0: upstream DEFAULT_LISTEN is true.
        # If FREELY chain selection ever falls through to normal node startup,
        # this test must catch the regression before P2P initialization.
        node.assert_start_raises_init_error(
            # The functional framework initializes a regtest=1 config. Disable
            # that inherited setting before selecting the FREELY chain.
            extra_args=["-regtest=0", "-chain=freely"],
            expected_msg="FREELY consensus and genesis parameters are not finalized; refusing startup.",
            match=ErrorMatch.PARTIAL_REGEX,
        )


if __name__ == "__main__":
    FreelyStartupFailClosedTest(__file__).main()
