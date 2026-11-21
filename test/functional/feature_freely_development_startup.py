#!/usr/bin/env python3
# Copyright (c) 2026 The FREELY developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Verify ordinary FREELY startup remains gated without an explicit development mode."""

from test_framework.test_framework import BitcoinTestFramework
from test_framework.test_node import ErrorMatch


class FreelyStartupFailClosedTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.chain = "freely"
        # Keep the framework's connect=0 setting so offline mode cannot
        # dial peers restored from the address manager.
        self.bind_to_localhost_only = False
        self.disable_autoconnect = True
        self.setup_clean_chain = True
        # Start safely for test setup, then restart without the explicit
        # development gate to assert that ordinary startup is rejected.
        self.extra_args = [[
            "-freelydev=1",
            "-listen=0",
            "-discover=0",
            "-dnsseed=0",
            "-natpmp=0",
            "-upnp=0",
            "-listenonion=0",
        ]]

    def run_test(self):
        node = self.nodes[0]
        self.stop_node(0)

        # Deliberately do not pass -listen=0: upstream DEFAULT_LISTEN is true.
        # If FREELY chain selection ever falls through to normal node startup,
        # this test must catch the regression before P2P initialization.
        node.assert_start_raises_init_error(
            extra_args=[],
            expected_msg="FREELY startup requires exactly one of -freelydev=1 or -freelyprivate=1.",
            match=ErrorMatch.PARTIAL_REGEX,
        )

        # The two mutually exclusive development modes must also fail closed
        # when an operator accidentally enables both at once.
        node.assert_start_raises_init_error(
            extra_args=["-freelydev=1", "-freelyprivate=1"],
            expected_msg="FREELY startup requires exactly one of -freelydev=1 or -freelyprivate=1.",
            match=ErrorMatch.PARTIAL_REGEX,
        )

        # UPnP can create an external router mapping independently of the
        # loopback/offline bind policy, so both FREELY modes must reject it.
        node.assert_start_raises_init_error(
            extra_args=[
                "-freelydev=1",
                "-listen=0",
                "-discover=0",
                "-dnsseed=0",
                "-natpmp=0",
                "-upnp=1",
                "-listenonion=0",
            ],
            expected_msg="FREELY offline development requires external discovery services and port mapping to be disabled.",
            match=ErrorMatch.PARTIAL_REGEX,
        )
        node.assert_start_raises_init_error(
            extra_args=[
                "-freelyprivate=1",
                "-bind=127.0.0.1",
                "-discover=0",
                "-dnsseed=0",
                "-natpmp=0",
                "-upnp=1",
                "-listenonion=0",
            ],
            expected_msg="FREELY loopback private mode prohibits external discovery, port mapping and listener services.",
            match=ErrorMatch.PARTIAL_REGEX,
        )


if __name__ == "__main__":
    FreelyStartupFailClosedTest(__file__).main()
