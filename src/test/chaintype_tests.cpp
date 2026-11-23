// Copyright (c) 2026-present The FREELY contributors
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <chainparamsbase.h>
#include <consensus/amount.h>
#include <pow.h>
#include <script/script.h>
#include <test/util/setup_common.h>
#include <util/chaintype.h>
#include <common/args.h>

#include <boost/test/unit_test.hpp>

#include <array>

#include <stdexcept>
#include <vector>

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

BOOST_AUTO_TEST_CASE(freely_production_startup_remains_fail_closed_until_launch_authorization)
{
    BOOST_CHECK_THROW(CreateChainParams(*m_node.args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(runtime_signet_magic_is_checked_against_reserved_networks)
{
    const auto default_signet = CChainParams::SigNet();
    BOOST_CHECK(GetNetworkForMagic(default_signet->MessageStart()) == ChainType::SIGNET);

    ArgsManager signet_args;
    signet_args.ForceSetArg("-signetchallenge", "51");
    const auto signet_params = CreateChainParams(signet_args, ChainType::SIGNET);
    BOOST_CHECK(signet_params->GetConsensus().signet_challenge != default_signet->GetConsensus().signet_challenge);
    BOOST_CHECK(signet_params->MessageStart() != default_signet->MessageStart());

    const auto detected_network = GetNetworkForMagic(signet_params->MessageStart());
    BOOST_CHECK(!detected_network || *detected_network == ChainType::SIGNET);
}

BOOST_AUTO_TEST_CASE(freely_chain_selection_sets_base_but_requires_launch_authorization)
{
    // The approved data-directory and RPC identity are available to clients.
    // Full node startup remains disabled pending explicit owner authorization.
    BOOST_CHECK_NO_THROW(SelectBaseParams(ChainType::FREELY));
    BOOST_CHECK_EQUAL(BaseParams().DataDir(), "freely");
    BOOST_CHECK_EQUAL(BaseParams().RPCPort(), 49445);
    BOOST_CHECK_THROW(SelectParams(ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_candidate_contains_approved_network_and_consensus_parameters)
{
    const auto params{CChainParams::FreelyCandidate()};
    BOOST_REQUIRE(params);

    BOOST_CHECK(params->GetChainType() == ChainType::FREELY);
    BOOST_CHECK_EQUAL(params->GetChainTypeString(), "freely");
    BOOST_CHECK(!params->IsTestChain());
    BOOST_CHECK(params->IsProductionChain());
    BOOST_CHECK(!params->IsMockableChain());

    const auto& consensus = params->GetConsensus();
    BOOST_CHECK_EQUAL(consensus.nSubsidyHalvingInterval, 210000);
    BOOST_CHECK_EQUAL(consensus.BIP34Height, 1);
    BOOST_CHECK_EQUAL(consensus.BIP34Hash.GetHex(),
                      "0000000000000000000000000000000000000000000000000000000000000000");
    BOOST_CHECK_EQUAL(consensus.BIP65Height, 1);
    BOOST_CHECK_EQUAL(consensus.BIP66Height, 1);
    BOOST_CHECK_EQUAL(consensus.CSVHeight, 1);
    BOOST_CHECK_EQUAL(consensus.SegwitHeight, 1);
    BOOST_CHECK_EQUAL(consensus.MinBIP9WarningHeight, 0);
    BOOST_CHECK_EQUAL(consensus.powLimit.GetHex(),
                      "00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
    BOOST_CHECK_EQUAL(consensus.nPowTargetSpacing, 600);
    BOOST_CHECK_EQUAL(consensus.nPowTargetTimespan, 1209600);
    BOOST_CHECK_EQUAL(consensus.DifficultyAdjustmentInterval(), 2016);
    BOOST_CHECK(!consensus.fPowAllowMinDifficultyBlocks);
    BOOST_CHECK(consensus.enforce_BIP94);
    BOOST_CHECK(!consensus.fPowNoRetargeting);
    BOOST_CHECK(consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].bit == 28);
    BOOST_CHECK_EQUAL(consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nStartTime,
                      Consensus::BIP9Deployment::NEVER_ACTIVE);
    BOOST_CHECK_EQUAL(consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nTimeout,
                      Consensus::BIP9Deployment::NO_TIMEOUT);
    BOOST_CHECK_EQUAL(consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].min_activation_height, 0);
    BOOST_CHECK_EQUAL(consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].threshold, 1815);
    BOOST_CHECK_EQUAL(consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].period, 2016);
    BOOST_CHECK(!consensus.signet_blocks);
    BOOST_CHECK(consensus.signet_challenge.empty());
    BOOST_CHECK(consensus.nMinimumChainWork.IsNull());
    BOOST_CHECK(consensus.defaultAssumeValid.IsNull());

    BOOST_CHECK_EQUAL(params->MessageStart()[0], 0xfa);
    BOOST_CHECK_EQUAL(params->MessageStart()[1], 0xc3);
    BOOST_CHECK_EQUAL(params->MessageStart()[2], 0xb7);
    BOOST_CHECK_EQUAL(params->MessageStart()[3], 0xd1);
    BOOST_CHECK_EQUAL(params->GetDefaultPort(), 49444);
    BOOST_CHECK(params->Base58Prefix(CChainParams::PUBKEY_ADDRESS) == std::vector<unsigned char>{55});
    BOOST_CHECK(params->Base58Prefix(CChainParams::SCRIPT_ADDRESS) == std::vector<unsigned char>{117});
    BOOST_CHECK(params->Base58Prefix(CChainParams::SECRET_KEY) == std::vector<unsigned char>{183});
    BOOST_CHECK(params->Base58Prefix(CChainParams::EXT_PUBLIC_KEY) ==
                (std::vector<unsigned char>{0x04, 0x46, 0x4c, 0x59}));
    BOOST_CHECK(params->Base58Prefix(CChainParams::EXT_SECRET_KEY) ==
                (std::vector<unsigned char>{0x04, 0x66, 0x6c, 0x79}));
    BOOST_CHECK_EQUAL(params->Bech32HRP(), "fly");
    BOOST_CHECK(GetNetworkForMagic(params->MessageStart()) == ChainType::FREELY);
    BOOST_CHECK(params->DNSSeeds().empty());
    BOOST_CHECK(params->FixedSeeds().empty());
    BOOST_CHECK(params->GetAvailableSnapshotHeights().empty());

    // The genesis transaction and proof of work are fixed and independently
    // verified. Normal production chain selection remains disabled until the
    // owner explicitly authorizes network activation.
    const auto& genesis = params->GenesisBlock();
    BOOST_CHECK_EQUAL(genesis.nVersion, 1);
    BOOST_CHECK(genesis.hashPrevBlock.IsNull());
    BOOST_CHECK_EQUAL(genesis.nTime, 1'794'960'000U);
    BOOST_CHECK_EQUAL(genesis.nBits, 0x1d00ffffU);
    BOOST_CHECK_EQUAL(genesis.nNonce, 2238688522U);
    BOOST_CHECK_EQUAL(genesis.hashMerkleRoot.GetHex(),
                      "c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1");
    BOOST_REQUIRE_EQUAL(genesis.vtx.size(), 1U);
    BOOST_REQUIRE_EQUAL(genesis.vtx[0]->vout.size(), 1U);
    BOOST_CHECK_EQUAL(genesis.vtx[0]->GetHash().GetHex(),
                      "c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1");
    BOOST_CHECK_EQUAL(genesis.vtx[0]->vout[0].nValue, 50 * COIN);
    BOOST_CHECK(genesis.vtx[0]->vout[0].scriptPubKey.IsUnspendable());
    BOOST_CHECK(consensus.hashGenesisBlock == genesis.GetHash());
    BOOST_CHECK_EQUAL(consensus.hashGenesisBlock.GetHex(),
                      "0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78");
    BOOST_CHECK(CheckProofOfWorkImpl(genesis.GetHash(), genesis.nBits, consensus));

    BOOST_CHECK_THROW(CreateChainParams(*m_node.args, ChainType::FREELY), std::runtime_error);

    const auto freely_base{CreateBaseChainParams(ChainType::FREELY)};
    BOOST_CHECK(params->GetDefaultPort() != freely_base->RPCPort());
    const std::array<ChainType, 5> builtin_chains{
        ChainType::MAIN, ChainType::TESTNET, ChainType::TESTNET4, ChainType::SIGNET, ChainType::REGTEST,
    };
    for (const auto chain : builtin_chains) {
        const auto builtin_base{CreateBaseChainParams(chain)};
        const auto builtin_params = chain == ChainType::MAIN ? CChainParams::Main() :
            chain == ChainType::TESTNET ? CChainParams::TestNet() :
            chain == ChainType::TESTNET4 ? CChainParams::TestNet4() :
            chain == ChainType::SIGNET ? CChainParams::SigNet() : CChainParams::RegTest();
        BOOST_CHECK(freely_base->DataDir() != builtin_base->DataDir());
        BOOST_CHECK(freely_base->RPCPort() != builtin_base->RPCPort());
        BOOST_CHECK(params->GetDefaultPort() != builtin_params->GetDefaultPort());
        BOOST_CHECK(params->GetDefaultPort() != builtin_base->RPCPort());
        BOOST_CHECK(freely_base->RPCPort() != builtin_params->GetDefaultPort());
        BOOST_CHECK(params->MessageStart() != builtin_params->MessageStart());
        BOOST_CHECK(params->Bech32HRP() != builtin_params->Bech32HRP());
        BOOST_CHECK(params->Base58Prefix(CChainParams::PUBKEY_ADDRESS) !=
                    builtin_params->Base58Prefix(CChainParams::PUBKEY_ADDRESS));
        BOOST_CHECK(params->Base58Prefix(CChainParams::SCRIPT_ADDRESS) !=
                    builtin_params->Base58Prefix(CChainParams::SCRIPT_ADDRESS));
        BOOST_CHECK(params->Base58Prefix(CChainParams::SECRET_KEY) !=
                    builtin_params->Base58Prefix(CChainParams::SECRET_KEY));
        BOOST_CHECK(params->Base58Prefix(CChainParams::EXT_PUBLIC_KEY) !=
                    builtin_params->Base58Prefix(CChainParams::EXT_PUBLIC_KEY));
        BOOST_CHECK(params->Base58Prefix(CChainParams::EXT_SECRET_KEY) !=
                    builtin_params->Base58Prefix(CChainParams::EXT_SECRET_KEY));
    }
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
