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

BOOST_AUTO_TEST_CASE(invalid_chain_type_enum_is_rejected)
{
    const auto invalid_chain{static_cast<ChainType>(-1)};
    BOOST_CHECK_THROW(ChainTypeToString(invalid_chain), std::invalid_argument);
    BOOST_CHECK_THROW(CreateBaseChainParams(invalid_chain), std::invalid_argument);
    BOOST_CHECK_THROW(CreateChainParams(*m_node.args, invalid_chain), std::invalid_argument);
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

BOOST_AUTO_TEST_SUITE_END()
