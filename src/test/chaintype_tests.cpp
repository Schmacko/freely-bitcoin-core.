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
#include <validation.h>

#include <boost/test/unit_test.hpp>

#include <array>

#include <stdexcept>
#include <utility>
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

BOOST_AUTO_TEST_CASE(freely_chain_alias_selects_chain_type)
{
    ArgsManager args;
    args.ForceSetArg("-freely", "1");
    BOOST_CHECK(args.GetChainType() == ChainType::FREELY);

    args.ForceSetArg("-chain", "freely");
    BOOST_CHECK_THROW(args.GetChainType(), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_development_modes_are_mutually_exclusive)
{
    // Production startup must not become reachable by omitting both explicit
    // development gates or by enabling both gates simultaneously.
    ArgsManager no_mode_args;
    BOOST_CHECK_THROW(CreateChainParams(no_mode_args, ChainType::FREELY), std::runtime_error);

    ArgsManager both_modes_args;
    both_modes_args.ForceSetArg("-freelydev", "1");
    both_modes_args.ForceSetArg("-freelyprivate", "1");
    BOOST_CHECK_THROW(CreateChainParams(both_modes_args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_development_startup_requires_isolated_mode)
{
    ArgsManager args;
    args.ForceSetArg("-freelydev", "1");
    args.ForceSetArg("-connect", "0");
    BOOST_CHECK_THROW(CreateChainParams(args, ChainType::FREELY), std::runtime_error);

    args.ForceSetArg("-listen", "0");
    args.ForceSetArg("-discover", "0");
    args.ForceSetArg("-dnsseed", "0");
    args.ForceSetArg("-listenonion", "0");
    const auto offline_params = CreateChainParams(args, ChainType::FREELY);
    BOOST_CHECK(!offline_params->AllowsLoopbackPeers());
}

BOOST_AUTO_TEST_CASE(freely_offline_mode_rejects_proxy_and_overlay_services)
{
    ArgsManager proxy_args;
    proxy_args.ForceSetArg("-freelydev", "1");
    proxy_args.ForceSetArg("-connect", "0");
    proxy_args.ForceSetArg("-listen", "0");
    proxy_args.ForceSetArg("-discover", "0");
    proxy_args.ForceSetArg("-dnsseed", "0");
    proxy_args.ForceSetArg("-listenonion", "0");
    proxy_args.ForceSetArg("-proxy", "127.0.0.1:9050");
    BOOST_CHECK_THROW(CreateChainParams(proxy_args, ChainType::FREELY), std::runtime_error);

    ArgsManager external_ip_args;
    external_ip_args.ForceSetArg("-freelydev", "1");
    external_ip_args.ForceSetArg("-connect", "0");
    external_ip_args.ForceSetArg("-listen", "0");
    external_ip_args.ForceSetArg("-discover", "0");
    external_ip_args.ForceSetArg("-dnsseed", "0");
    external_ip_args.ForceSetArg("-listenonion", "0");
    external_ip_args.ForceSetArg("-externalip", "198.51.100.7");
    BOOST_CHECK_THROW(CreateChainParams(external_ip_args, ChainType::FREELY), std::runtime_error);

    ArgsManager i2p_args;
    i2p_args.ForceSetArg("-freelydev", "1");
    i2p_args.ForceSetArg("-connect", "0");
    i2p_args.ForceSetArg("-listen", "0");
    i2p_args.ForceSetArg("-discover", "0");
    i2p_args.ForceSetArg("-dnsseed", "0");
    i2p_args.ForceSetArg("-listenonion", "0");
    i2p_args.ForceSetArg("-i2psam", "127.0.0.1:7656");
    BOOST_CHECK_THROW(CreateChainParams(i2p_args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_offline_mode_rejects_zmq_publish_endpoints)
{
    ArgsManager args;
    args.ForceSetArg("-freelydev", "1");
    args.ForceSetArg("-connect", "0");
    args.ForceSetArg("-listen", "0");
    args.ForceSetArg("-discover", "0");
    args.ForceSetArg("-dnsseed", "0");
    args.ForceSetArg("-listenonion", "0");
    args.ForceSetArg("-zmqpubrawtx", "tcp://203.0.113.1:28332");
    BOOST_CHECK_THROW(CreateChainParams(args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_development_mode_rejects_outbound_peers)
{
    ArgsManager connect_args;
    connect_args.ForceSetArg("-freelydev", "1");
    connect_args.ForceSetArg("-listen", "0");
    connect_args.ForceSetArg("-connect", "127.0.0.1:49444");
    BOOST_CHECK_THROW(CreateChainParams(connect_args, ChainType::FREELY), std::runtime_error);

    ArgsManager addnode_args;
    addnode_args.ForceSetArg("-freelydev", "1");
    addnode_args.ForceSetArg("-connect", "0");
    addnode_args.ForceSetArg("-listen", "0");
    addnode_args.ForceSetArg("-addnode", "127.0.0.1:49444");
    BOOST_CHECK_THROW(CreateChainParams(addnode_args, ChainType::FREELY), std::runtime_error);

    ArgsManager seednode_args;
    seednode_args.ForceSetArg("-freelydev", "1");
    seednode_args.ForceSetArg("-connect", "0");
    seednode_args.ForceSetArg("-listen", "0");
    seednode_args.ForceSetArg("-seednode", "127.0.0.1:49444");
    BOOST_CHECK_THROW(CreateChainParams(seednode_args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_development_mode_rejects_listener_overrides)
{
    ArgsManager bind_args;
    bind_args.ForceSetArg("-freelydev", "1");
    bind_args.ForceSetArg("-connect", "0");
    bind_args.ForceSetArg("-listen", "0");
    bind_args.ForceSetArg("-bind", "127.0.0.1:49444");
    BOOST_CHECK_THROW(CreateChainParams(bind_args, ChainType::FREELY), std::runtime_error);

    ArgsManager whitebind_args;
    whitebind_args.ForceSetArg("-freelydev", "1");
    whitebind_args.ForceSetArg("-connect", "0");
    whitebind_args.ForceSetArg("-listen", "0");
    whitebind_args.ForceSetArg("-whitebind", "127.0.0.1:49444");
    BOOST_CHECK_THROW(CreateChainParams(whitebind_args, ChainType::FREELY), std::runtime_error);

    ArgsManager onion_args;
    onion_args.ForceSetArg("-freelydev", "1");
    onion_args.ForceSetArg("-connect", "0");
    onion_args.ForceSetArg("-listen", "0");
    onion_args.ForceSetArg("-listenonion", "1");
    BOOST_CHECK_THROW(CreateChainParams(onion_args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_CASE(freely_loopback_private_mode_requires_explicit_local_binding)
{
    ArgsManager no_connect_args;
    no_connect_args.ForceSetArg("-freelyprivate", "1");
    no_connect_args.ForceSetArg("-bind", "127.0.0.1:49444");
    no_connect_args.ForceSetArg("-discover", "0");
    no_connect_args.ForceSetArg("-dnsseed", "0");
    no_connect_args.ForceSetArg("-listenonion", "0");
    BOOST_CHECK_THROW(CreateChainParams(no_connect_args, ChainType::FREELY), std::runtime_error);

    ArgsManager no_bind_args;
    no_bind_args.ForceSetArg("-freelyprivate", "1");
    no_bind_args.ForceSetArg("-discover", "0");
    no_bind_args.ForceSetArg("-dnsseed", "0");
    no_bind_args.ForceSetArg("-listenonion", "0");
    BOOST_CHECK_THROW(CreateChainParams(no_bind_args, ChainType::FREELY), std::runtime_error);

    ArgsManager loopback_args;
    loopback_args.ForceSetArg("-freelyprivate", "1");
    loopback_args.ForceSetArg("-connect", "0");
    loopback_args.ForceSetArg("-bind", "127.0.0.1:49444");
    loopback_args.ForceSetArg("-discover", "0");
    loopback_args.ForceSetArg("-dnsseed", "0");
    loopback_args.ForceSetArg("-listenonion", "0");
    const auto private_params = CreateChainParams(loopback_args, ChainType::FREELY);
    BOOST_CHECK(private_params->AllowsLoopbackPeers());

    ArgsManager public_bind_args;
    public_bind_args.ForceSetArg("-freelyprivate", "1");
    public_bind_args.ForceSetArg("-bind", "0.0.0.0:49444");
    public_bind_args.ForceSetArg("-discover", "0");
    public_bind_args.ForceSetArg("-dnsseed", "0");
    public_bind_args.ForceSetArg("-listenonion", "0");
    BOOST_CHECK_THROW(CreateChainParams(public_bind_args, ChainType::FREELY), std::runtime_error);

    // Bind strings must be literal loopback IPs, not hostnames, mapped
    // addresses, or lookalike prefixes that could resolve outside loopback.
    for (const auto& unsafe_bind : {
             "localhost:49444",
             "127.0.0.1.evil.example:49444",
             "[::ffff:127.0.0.1]:49444",
         }) {
        ArgsManager unsafe_bind_args;
        unsafe_bind_args.ForceSetArg("-freelyprivate", "1");
        unsafe_bind_args.ForceSetArg("-connect", "0");
        unsafe_bind_args.ForceSetArg("-bind", unsafe_bind);
        unsafe_bind_args.ForceSetArg("-discover", "0");
        unsafe_bind_args.ForceSetArg("-dnsseed", "0");
        unsafe_bind_args.ForceSetArg("-listenonion", "0");
        BOOST_CHECK_THROW(CreateChainParams(unsafe_bind_args, ChainType::FREELY), std::runtime_error);
    }
}

BOOST_AUTO_TEST_CASE(freely_loopback_private_mode_rejects_external_services)
{
    ArgsManager rpc_args;
    rpc_args.ForceSetArg("-freelyprivate", "1");
    rpc_args.ForceSetArg("-connect", "0");
    rpc_args.ForceSetArg("-bind", "127.0.0.1:49444");
    rpc_args.ForceSetArg("-discover", "0");
    rpc_args.ForceSetArg("-dnsseed", "0");
    rpc_args.ForceSetArg("-listenonion", "0");
    rpc_args.ForceSetArg("-rpcbind", "0.0.0.0");
    BOOST_CHECK_THROW(CreateChainParams(rpc_args, ChainType::FREELY), std::runtime_error);

    ArgsManager proxy_args;
    proxy_args.ForceSetArg("-freelyprivate", "1");
    proxy_args.ForceSetArg("-connect", "0");
    proxy_args.ForceSetArg("-bind", "127.0.0.1:49444");
    proxy_args.ForceSetArg("-discover", "0");
    proxy_args.ForceSetArg("-dnsseed", "0");
    proxy_args.ForceSetArg("-listenonion", "0");
    proxy_args.ForceSetArg("-proxy", "127.0.0.1:9050");
    BOOST_CHECK_THROW(CreateChainParams(proxy_args, ChainType::FREELY), std::runtime_error);

    ArgsManager external_ip_args;
    external_ip_args.ForceSetArg("-freelyprivate", "1");
    external_ip_args.ForceSetArg("-connect", "0");
    external_ip_args.ForceSetArg("-bind", "127.0.0.1:49444");
    external_ip_args.ForceSetArg("-discover", "0");
    external_ip_args.ForceSetArg("-dnsseed", "0");
    external_ip_args.ForceSetArg("-listenonion", "0");
    external_ip_args.ForceSetArg("-externalip", "198.51.100.7");
    BOOST_CHECK_THROW(CreateChainParams(external_ip_args, ChainType::FREELY), std::runtime_error);

    ArgsManager zmq_args;
    zmq_args.ForceSetArg("-freelyprivate", "1");
    zmq_args.ForceSetArg("-connect", "0");
    zmq_args.ForceSetArg("-bind", "127.0.0.1:49444");
    zmq_args.ForceSetArg("-discover", "0");
    zmq_args.ForceSetArg("-dnsseed", "0");
    zmq_args.ForceSetArg("-listenonion", "0");
    zmq_args.ForceSetArg("-zmqpubhashblock", "tcp://203.0.113.1:28332");
    BOOST_CHECK_THROW(CreateChainParams(zmq_args, ChainType::FREELY), std::runtime_error);
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

    // Also verify the consensus API maps each buried deployment to the
    // approved activation height; this catches enum-to-field mapping drift.
    BOOST_CHECK_EQUAL(consensus.DeploymentHeight(Consensus::DEPLOYMENT_HEIGHTINCB), 1);
    BOOST_CHECK_EQUAL(consensus.DeploymentHeight(Consensus::DEPLOYMENT_CLTV), 1);
    BOOST_CHECK_EQUAL(consensus.DeploymentHeight(Consensus::DEPLOYMENT_DERSIG), 1);
    BOOST_CHECK_EQUAL(consensus.DeploymentHeight(Consensus::DEPLOYMENT_CSV), 1);
    BOOST_CHECK_EQUAL(consensus.DeploymentHeight(Consensus::DEPLOYMENT_SEGWIT), 1);
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
    // GetBlockScriptFlags enables TAPROOT for every block, except explicitly
    // listed historical exceptions. A new FREELY chain must have none.
    BOOST_CHECK(consensus.script_flag_exceptions.empty());

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

BOOST_AUTO_TEST_CASE(freely_monetary_schedule_uses_integer_halvings_and_stays_below_cap)
{
    const auto params{CChainParams::FreelyCandidate()};
    const auto& consensus = params->GetConsensus();

    BOOST_CHECK_EQUAL(GetBlockSubsidy(0, consensus), 50 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(209999, consensus), 50 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(210000, consensus), 25 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(419999, consensus), 25 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(420000, consensus), 12 * COIN + COIN / 2);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(32 * 210000, consensus), CAmount{1});
    BOOST_CHECK_EQUAL(GetBlockSubsidy(33 * 210000, consensus), CAmount{0});
    BOOST_CHECK_EQUAL(GetBlockSubsidy(64 * 210000, consensus), CAmount{0});

    // Sum the integer subsidy schedule in base units. The genesis coinbase
    // is unspendable, so spendable issuance is one 50-FLY subsidy below this
    // scheduled amount. The 21-million-FLY ceiling is never exceeded.
    CAmount scheduled_total{0};
    for (int halving = 0; halving < 64; ++halving) {
        const CAmount subsidy = GetBlockSubsidy(halving * 210000, consensus);
        scheduled_total += subsidy * consensus.nSubsidyHalvingInterval;
    }
    BOOST_CHECK_EQUAL(scheduled_total, CAmount{2099999997690000});
    BOOST_CHECK(scheduled_total <= MAX_MONEY);
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


BOOST_AUTO_TEST_CASE(freely_loopback_private_mode_rejects_peer_and_overlay_configuration)
{
    // A loopback-only node may connect to peers through the guarded addnode
    // RPC, but must not inherit any configured peer, proxy, or overlay path.
    const std::array<std::pair<const char*, const char*>, 8> forbidden_options{{
        {"-addnode", "127.0.0.1:49444"},
        {"-seednode", "127.0.0.1:49444"},
        {"-proxy", "127.0.0.1:9050"},
        {"-onion", "127.0.0.1:9050"},
        {"-i2psam", "127.0.0.1:7656"},
        {"-torcontrol", "127.0.0.1:9051"},
        {"-torpassword", "test-only"},
        {"-rpcallowip", "0.0.0.0/0"},
    }};

    for (const auto& [option, value] : forbidden_options) {
        ArgsManager args;
        args.ForceSetArg("-freelyprivate", "1");
        args.ForceSetArg("-connect", "0");
        args.ForceSetArg("-bind", "127.0.0.1:49444");
        args.ForceSetArg("-discover", "0");
        args.ForceSetArg("-dnsseed", "0");
        args.ForceSetArg("-natpmp", "0");
        args.ForceSetArg("-upnp", "0");
        args.ForceSetArg("-listenonion", "0");
        args.ForceSetArg(option, value);

        BOOST_TEST_CONTEXT("forbidden option " << option) {
            BOOST_CHECK_THROW(CreateChainParams(args, ChainType::FREELY), std::runtime_error);
        }
    }
}

BOOST_AUTO_TEST_CASE(freely_loopback_private_mode_rejects_external_discovery_and_listener_overrides)
{
    const std::array<std::pair<const char*, const char*>, 5> forbidden_options{{
        {"-discover", "1"},
        {"-dnsseed", "1"},
        {"-natpmp", "1"},
        {"-upnp", "1"},
        {"-listenonion", "1"},
    }};

    for (const auto& [option, value] : forbidden_options) {
        ArgsManager args;
        args.ForceSetArg("-freelyprivate", "1");
        args.ForceSetArg("-connect", "0");
        args.ForceSetArg("-bind", "127.0.0.1:49444");
        args.ForceSetArg("-discover", "0");
        args.ForceSetArg("-dnsseed", "0");
        args.ForceSetArg("-natpmp", "0");
        args.ForceSetArg("-upnp", "0");
        args.ForceSetArg("-listenonion", "0");
        args.ForceSetArg(option, value);

        BOOST_TEST_CONTEXT("forbidden option " << option) {
            BOOST_CHECK_THROW(CreateChainParams(args, ChainType::FREELY), std::runtime_error);
        }
    }

    ArgsManager no_listen_args;
    no_listen_args.ForceSetArg("-freelyprivate", "1");
    no_listen_args.ForceSetArg("-connect", "0");
    no_listen_args.ForceSetArg("-bind", "127.0.0.1:49444");
    no_listen_args.ForceSetArg("-listen", "0");
    no_listen_args.ForceSetArg("-discover", "0");
    no_listen_args.ForceSetArg("-dnsseed", "0");
    no_listen_args.ForceSetArg("-natpmp", "0");
    no_listen_args.ForceSetArg("-upnp", "0");
    no_listen_args.ForceSetArg("-listenonion", "0");
    BOOST_CHECK_THROW(CreateChainParams(no_listen_args, ChainType::FREELY), std::runtime_error);
}

BOOST_AUTO_TEST_SUITE_END()
