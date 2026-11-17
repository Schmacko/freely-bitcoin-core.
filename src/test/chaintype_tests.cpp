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

BOOST_AUTO_TEST_CASE(freely_chain_startup_fails_closed_until_parameters_are_final)
{
    BOOST_CHECK_THROW(CreateBaseChainParams(ChainType::FREELY), std::runtime_error);
    BOOST_CHECK_THROW(CreateChainParams(*m_node.args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_chain_selection_entrypoints_fail_closed)
{
    // Exercise the same public selectors used during application startup.
    // Both must fail before global chain parameters or config selection can be set.
    BOOST_CHECK_THROW(SelectBaseParams(ChainType::FREELY), std::runtime_error);
    BOOST_CHECK_THROW(SelectParams(ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_SUITE_END()
