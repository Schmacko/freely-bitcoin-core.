// Copyright (c) 2010 Satoshi Nakamoto
// Copyright (c) 2009-present The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>

#include <chainparamsbase.h>
#include <common/args.h>
#include <consensus/params.h>
#include <deploymentinfo.h>
#include <tinyformat.h>
#include <util/chaintype.h>
#include <util/log.h>
#include <util/strencodings.h>
#include <util/string.h>

#include <cassert>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

using util::SplitString;

// Bitcoin Core v32.1 defines DEFAULT_NATPMP as true in mapport.h. Keep this
// dependency-local copy because including mapport.h here would create the
// cycle chainparams -> mapport -> net -> chainparams.
static constexpr bool FREELY_DEFAULT_NATPMP{true};

static void HandleDeploymentArgs(const ArgsManager& args, CChainParams::DeploymentOptions& options)
{
    for (const std::string& arg : args.GetArgs("-testactivationheight")) {
        const auto found{arg.find('@')};
        if (found == std::string::npos) {
            throw std::runtime_error(strprintf("Invalid format (%s) for -testactivationheight=name@height.", arg));
        }

        const auto value{arg.substr(found + 1)};
        const auto height{ToIntegral<int32_t>(value)};
        if (!height || *height < 0 || *height >= std::numeric_limits<int>::max()) {
            throw std::runtime_error(strprintf("Invalid height value (%s) for -testactivationheight=name@height.", arg));
        }

        const auto deployment_name{arg.substr(0, found)};
        if (const auto buried_deployment = GetBuriedDeployment(deployment_name)) {
            options.activation_heights[*buried_deployment] = *height;
        } else {
            throw std::runtime_error(strprintf("Invalid name (%s) for -testactivationheight=name@height.", arg));
        }
    }

    for (const std::string& strDeployment : args.GetArgs("-vbparams")) {
        std::vector<std::string> vDeploymentParams = SplitString(strDeployment, ':');
        if (vDeploymentParams.size() < 3 || 4 < vDeploymentParams.size()) {
            throw std::runtime_error("Version bits parameters malformed, expecting deployment:start:end[:min_activation_height]");
        }
        CChainParams::VersionBitsParameters vbparams{};
        const auto start_time{ToIntegral<int64_t>(vDeploymentParams[1])};
        if (!start_time) {
            throw std::runtime_error(strprintf("Invalid nStartTime (%s)", vDeploymentParams[1]));
        }
        vbparams.start_time = *start_time;
        const auto timeout{ToIntegral<int64_t>(vDeploymentParams[2])};
        if (!timeout) {
            throw std::runtime_error(strprintf("Invalid nTimeout (%s)", vDeploymentParams[2]));
        }
        vbparams.timeout = *timeout;
        if (vDeploymentParams.size() >= 4) {
            const auto min_activation_height{ToIntegral<int64_t>(vDeploymentParams[3])};
            if (!min_activation_height) {
                throw std::runtime_error(strprintf("Invalid min_activation_height (%s)", vDeploymentParams[3]));
            }
            vbparams.min_activation_height = *min_activation_height;
        } else {
            vbparams.min_activation_height = 0;
        }
        bool found = false;
        for (int j=0; j < (int)Consensus::MAX_VERSION_BITS_DEPLOYMENTS; ++j) {
            if (vDeploymentParams[0] == VersionBitsDeploymentInfo[j].name) {
                options.version_bits_parameters[Consensus::DeploymentPos(j)] = vbparams;
                found = true;
                LogInfo("Setting version bits activation parameters for %s to start=%ld, timeout=%ld, min_activation_height=%d",
                        vDeploymentParams[0], vbparams.start_time, vbparams.timeout, vbparams.min_activation_height);
                break;
            }
        }
        if (!found) {
            throw std::runtime_error(strprintf("Invalid deployment (%s)", vDeploymentParams[0]));
        }
    }
}

void ReadMainNetArgs(const ArgsManager& args, CChainParams::MainNetOptions& options)
{
    HandleDeploymentArgs(args, options.dep_opts);
}

void ReadTestNetArgs(const ArgsManager& args, CChainParams::TestNetOptions& options)
{
    HandleDeploymentArgs(args, options.dep_opts);
}

void ReadSigNetArgs(const ArgsManager& args, CChainParams::SigNetOptions& options)
{
    if (!args.GetArgs("-signetseednode").empty()) {
        options.seeds.emplace(args.GetArgs("-signetseednode"));
    }
    if (!args.GetArgs("-signetchallenge").empty()) {
        const auto signet_challenge = args.GetArgs("-signetchallenge");
        if (signet_challenge.size() != 1) {
            throw std::runtime_error("-signetchallenge cannot be multiple values.");
        }
        const auto val{TryParseHex<uint8_t>(signet_challenge[0])};
        if (!val) {
            throw std::runtime_error(strprintf("-signetchallenge must be hex, not '%s'.", signet_challenge[0]));
        }
        options.challenge.emplace(*val);
    }
    HandleDeploymentArgs(args, options.dep_opts);
}

void ReadRegTestArgs(const ArgsManager& args, CChainParams::RegTestOptions& options)
{
    if (auto value = args.GetBoolArg("-fastprune")) options.fastprune = *value;
    if (HasTestOption(args, "bip94")) options.enforce_bip94 = true;

    HandleDeploymentArgs(args, options.dep_opts);
}

static std::unique_ptr<const CChainParams> globalChainParams;

const CChainParams &Params() {
    assert(globalChainParams);
    return *globalChainParams;
}

std::unique_ptr<const CChainParams> CreateChainParams(const ArgsManager& args, const ChainType chain)
{
    switch (chain) {
    case ChainType::MAIN: {
        auto opts = CChainParams::MainNetOptions{};
        ReadMainNetArgs(args, opts);
        return CChainParams::Main(opts);
    }
    case ChainType::TESTNET: {
        auto opts = CChainParams::TestNetOptions{};
        ReadTestNetArgs(args, opts);
        return CChainParams::TestNet(opts);
    }
    case ChainType::TESTNET4: {
        auto opts = CChainParams::TestNetOptions{};
        ReadTestNetArgs(args, opts);
        return CChainParams::TestNet4(opts);
    }
    case ChainType::SIGNET: {
        auto opts = CChainParams::SigNetOptions{};
        ReadSigNetArgs(args, opts);
        auto params = CChainParams::SigNet(opts);
        const auto detected_network = GetNetworkForMagic(params->MessageStart());
        if (detected_network && *detected_network != ChainType::SIGNET) {
            throw std::runtime_error("Custom signet message magic collides with a reserved built-in network magic.");
        }
        if (detected_network && *detected_network == ChainType::SIGNET) {
            // A custom challenge can collide with the default signet's 4-byte
            // message start. That is a distinct network identity collision even
            // though GetNetworkForMagic necessarily labels both as SIGNET.
            // Compare the challenge payload because the enum alone loses identity.
            const auto default_signet = CChainParams::SigNet();
            if (params->GetConsensus().signet_challenge != default_signet->GetConsensus().signet_challenge) {
                throw std::runtime_error("Custom signet message magic collides with the default signet network magic.");
            }
        }
        return params;
    }
    case ChainType::REGTEST: {
        auto opts = CChainParams::RegTestOptions{};
        ReadRegTestArgs(args, opts);
        return CChainParams::RegTest(opts);
    }
    case ChainType::FREELY: {
        const bool offline_dev{args.GetBoolArg("-freelydev", false)};
        const bool loopback_private{args.GetBoolArg("-freelyprivate", false)};
        if (offline_dev == loopback_private) {
            throw std::runtime_error("FREELY startup requires exactly one of -freelydev=1 or -freelyprivate=1.");
        }

        if (offline_dev) {
            // Offline development cannot listen for P2P peers or initiate
            // outbound peer connections.
            if (args.GetBoolArg("-listen", true)) {
                throw std::runtime_error("FREELY offline development requires -listen=0.");
            }
            if (!args.GetArgs("-bind").empty() ||
                !args.GetArgs("-whitebind").empty() ||
                args.GetBoolArg("-listenonion", true)) {
                throw std::runtime_error("FREELY offline development does not permit P2P listener bindings.");
            }
            if (args.GetBoolArg("-discover", true) ||
                args.GetBoolArg("-dnsseed", true) ||
                args.GetBoolArg("-natpmp", FREELY_DEFAULT_NATPMP)) {
                throw std::runtime_error("FREELY offline development requires external discovery services and port mapping to be disabled.");
            }
            if (!args.GetArgs("-rpcbind").empty() || !args.GetArgs("-rpcallowip").empty()) {
                throw std::runtime_error("FREELY offline development requires the default loopback-only RPC binding.");
            }
            // -listen=0 prevents inbound P2P only. Require -connect=0 as well
            // so ThreadOpenConnections cannot dial addresses restored from peers.dat
            // or otherwise learned by the address manager. Do not treat a fresh
            // data directory as a substitute for enforcing this at startup.
            const auto connect_args{args.GetArgs("-connect")};
            if (connect_args.size() != 1 || connect_args.front() != "0") {
                throw std::runtime_error("FREELY offline development requires -connect=0 to disable automatic outbound connections.");
            }
            if (!args.GetArgs("-addnode").empty() ||
                !args.GetArgs("-seednode").empty() ||
                !args.GetArgs("-proxy").empty() ||
                !args.GetArgs("-onion").empty() ||
                !args.GetArgs("-i2psam").empty() ||
                !args.GetArgs("-torcontrol").empty() ||
                !args.GetArgs("-torpassword").empty() ||
                !args.GetArgs("-externalip").empty()) {
                throw std::runtime_error("FREELY offline development does not permit configured peers, proxies or overlay-network services.");
            }
            // ZMQ notifiers create outbound sockets independently of P2P;
            // they must not provide a side channel around the offline boundary.
            if (!args.GetArgs("-zmqpubhashblock").empty() ||
                !args.GetArgs("-zmqpubhashtx").empty() ||
                !args.GetArgs("-zmqpubrawblock").empty() ||
                !args.GetArgs("-zmqpubrawtx").empty() ||
                !args.GetArgs("-zmqpubsequence").empty()) {
                throw std::runtime_error("FREELY offline development does not permit ZMQ publish endpoints.");
            }
            return CChainParams::FreelyCandidate(false);
        }

        // Private-network mode is restricted to explicit loopback bindings.
        // RPC remains loopback-only by default; custom RPC binds/allowlists,
        // proxies, external addresses, discovery and overlay services are prohibited.
        if (!args.GetBoolArg("-listen", true)) {
            throw std::runtime_error("FREELY loopback private mode requires P2P listening.");
        }
        const auto binds{args.GetArgs("-bind")};
        if (binds.empty()) {
            throw std::runtime_error("FREELY loopback private mode requires an explicit loopback -bind.");
        }
        for (const auto& bind : binds) {
            const bool ipv4_loopback{bind == "127.0.0.1" || (bind.starts_with("127.0.0.1:") && bind.find('=') == std::string::npos)};
            const bool ipv6_loopback{bind == "[::1]" || (bind.starts_with("[::1]:") && bind.find('=') == std::string::npos)};
            if (!ipv4_loopback && !ipv6_loopback) {
                throw std::runtime_error("FREELY loopback private mode accepts only 127.0.0.1 or [::1] bind addresses.");
            }
        }
        if (!args.GetArgs("-whitebind").empty() ||
            args.GetBoolArg("-discover", true) ||
            args.GetBoolArg("-dnsseed", true) ||
            args.GetBoolArg("-natpmp", FREELY_DEFAULT_NATPMP) ||
            args.GetBoolArg("-listenonion", true) ||
            !args.GetArgs("-externalip").empty()) {
            throw std::runtime_error("FREELY loopback private mode prohibits external discovery, port mapping and listener services.");
        }
        if (!args.GetArgs("-zmqpubhashblock").empty() ||
            !args.GetArgs("-zmqpubhashtx").empty() ||
            !args.GetArgs("-zmqpubrawblock").empty() ||
            !args.GetArgs("-zmqpubrawtx").empty() ||
            !args.GetArgs("-zmqpubsequence").empty()) {
            throw std::runtime_error("FREELY loopback private mode does not permit ZMQ publish endpoints.");
        }
        const auto connect_args{args.GetArgs("-connect")};
        if (connect_args.size() != 1 || connect_args.front() != "0" ||
            !args.GetArgs("-addnode").empty() ||
            !args.GetArgs("-seednode").empty() ||
            !args.GetArgs("-proxy").empty() ||
            !args.GetArgs("-onion").empty() ||
            !args.GetArgs("-i2psam").empty() ||
            !args.GetArgs("-torcontrol").empty() ||
            !args.GetArgs("-torpassword").empty()) {
            throw std::runtime_error("FREELY loopback private mode requires -connect=0 and prohibits configured external peers, proxies and overlay-network services.");
        }
        if (!args.GetArgs("-rpcbind").empty() || !args.GetArgs("-rpcallowip").empty()) {
            throw std::runtime_error("FREELY loopback private mode requires the default loopback-only RPC binding.");
        }
        return CChainParams::FreelyCandidate(true);
    }
    }
    assert(false);
}

void SelectParams(const ChainType chain)
{
    SelectBaseParams(chain);
    globalChainParams = CreateChainParams(gArgs, chain);
}
