// Copyright (c) 2026-present The FREELY contributors
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <chainparamsbase.h>
#include <test/util/setup_common.h>
#include <util/chaintype.h>

#include <boost/test/unit_test.hpp>

#include <stdexcept>

BOOST_FIXTURE_TEST_SUITE(chaintype_tests, BasicTestingSetup)

BOOST_AUTO_TEST_CASE(freely_chain_type_name_roundtrip)
{
    const auto chain{ChainTypeFromString("freely")};
    BOOST_REQUIRE(chain.has_value());
    BOOST_CHECK(*chain == ChainType::FREELY);
    BOOST_CHECK_EQUAL(ChainTypeToString(*chain), "freely");
}

BOOST_AUTO_TEST_CASE(all_supported_chain_type_names_roundtrip)
{
    BOOST_CHECK_EQUAL(ChainTypeToString(ChainType::MAIN), "main");
    BOOST_CHECK_EQUAL(ChainTypeToString(ChainType::TESTNET), "test");
    BOOST_CHECK_EQUAL(ChainTypeToString(ChainType::TESTNET4), "testnet4");
    BOOST_CHECK_EQUAL(ChainTypeToString(ChainType::SIGNET), "signet");
    BOOST_CHECK_EQUAL(ChainTypeToString(ChainType::REGTEST), "regtest");
    BOOST_CHECK_EQUAL(ChainTypeToString(ChainType::FREELY), "freely");

    BOOST_CHECK(ChainTypeFromString("main") == ChainType::MAIN);
    BOOST_CHECK(ChainTypeFromString("test") == ChainType::TESTNET);
    BOOST_CHECK(ChainTypeFromString("testnet4") == ChainType::TESTNET4);
    BOOST_CHECK(ChainTypeFromString("signet") == ChainType::SIGNET);
    BOOST_CHECK(ChainTypeFromString("regtest") == ChainType::REGTEST);
    BOOST_CHECK(ChainTypeFromString("freely") == ChainType::FREELY);
}

BOOST_AUTO_TEST_CASE(unknown_chain_type_is_rejected)
{
    BOOST_CHECK(!ChainTypeFromString("not-a-chain").has_value());
    BOOST_CHECK(!ChainTypeFromString("FREELY").has_value());
}

BOOST_AUTO_TEST_CASE(freely_approved_base_parameters_are_selected)
{
    const auto base{CreateBaseChainParams(ChainType::FREELY)};
    BOOST_REQUIRE(base);
    BOOST_CHECK_EQUAL(base->DataDir(), "freely");
    BOOST_CHECK_EQUAL(base->RPCPort(), 49445);
}

BOOST_AUTO_TEST_CASE(freely_consensus_startup_remains_fail_closed_until_genesis_is_mined)
{
    BOOST_CHECK_THROW(CreateChainParams(*m_node.args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_chain_selection_sets_base_but_rejects_incomplete_consensus)
{
    // The approved data-directory and RPC identity are available to clients.
    // Full node startup must still stop until the mined genesis commitment is fixed.
    BOOST_CHECK_NO_THROW(SelectBaseParams(ChainType::FREELY));
    BOOST_CHECK_EQUAL(BaseParams().DataDir(), "freely");
    BOOST_CHECK_EQUAL(BaseParams().RPCPort(), 49445);
    BOOST_CHECK_THROW(SelectParams(ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_message_magic_maps_to_freely_chain_type)
{
    constexpr MessageStartChars freely_message_start{0xfa, 0xc3, 0xb7, 0xd1};
    const auto network = GetNetworkForMagic(freely_message_start);
    BOOST_REQUIRE(network.has_value());
    BOOST_CHECK(*network == ChainType::FREELY);

    constexpr MessageStartChars unknown_message_start{0xde, 0xad, 0xbe, 0xef};
    BOOST_CHECK(!GetNetworkForMagic(unknown_message_start).has_value());
}

BOOST_AUTO_TEST_CASE(all_builtin_message_magics_keep_their_chain_type)
{
    const auto mainnet{CChainParams::Main()};
    const auto testnet{CChainParams::TestNet()};
    const auto testnet4{CChainParams::TestNet4()};
    const auto signet{CChainParams::SigNet()};
    const auto regtest{CChainParams::RegTest()};

    BOOST_CHECK(GetNetworkForMagic(mainnet->MessageStart()) == ChainType::MAIN);
    BOOST_CHECK(GetNetworkForMagic(testnet->MessageStart()) == ChainType::TESTNET);
    BOOST_CHECK(GetNetworkForMagic(testnet4->MessageStart()) == ChainType::TESTNET4);
    BOOST_CHECK(GetNetworkForMagic(signet->MessageStart()) == ChainType::SIGNET);
    BOOST_CHECK(GetNetworkForMagic(regtest->MessageStart()) == ChainType::REGTEST);
}

BOOST_AUTO_TEST_SUITE_END()
