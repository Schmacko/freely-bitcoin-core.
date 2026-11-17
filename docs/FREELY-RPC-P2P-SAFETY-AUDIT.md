# FREELY RPC, P2P and chain-selection safety audit

**Status:** source audit and fail-closed design review  
**Source baseline:** Bitcoin Core v32.1 fork, FREELY core-chain implementation branch  
**Date:** 17 November 2026  
**Scope:** chain selection, RPC binding defaults, P2P listener defaults, data-directory isolation, CLI chain reporting, and network-magic dispatch.

This document records source-level findings. It does not claim that a FREELY node is runnable, that a public service is safe, or that a FREELY network has been activated.

## 1. Executive findings

- `-chain=freely` is registered by the chain selector, but both `CreateBaseChainParams(FREELY)` and `CreateChainParams(..., FREELY)` deliberately throw until production network and consensus parameters are finalised. The startup path therefore remains fail-closed.
- The production-chain classification introduced in the M1 workstream is explicit. A future FREELY production parameter object must set `IsProductionChain() == true`, `IsTestChain() == false`, and `IsMockableChain() == false`. It must not inherit Bitcoin mainnet history-specific assumptions.
- The Bitcoin CLI `-netinfo` chain-label switch previously omitted `ChainType::FREELY`; it now returns the explicit label `freely`.
- The RPC bind help text and default describe loopback addresses (127.0.0.1 and ::1). A remote RPC listener requires explicit `-rpcallowip` and `-rpcbind` configuration. Do not add remote RPC defaults for FREELY.
- The upstream P2P default is `DEFAULT_LISTEN = true`. Explicit `-bind` or `-whitebind` also implies listening. Therefore, P2P must be treated as a production launch gate, not assumed safe merely because RPC defaults to loopback.
- No public RPC/P2P listener is introduced by this workstream. FREELY still cannot initialise its chain parameters and must fail before node networking starts.

## 2. ChainType::MAIN audit findings

### 2.1 Expected mainnet references

`src/init.cpp` and `src/bitcoin-cli.cpp` instantiate `CreateBaseChainParams(ChainType::MAIN)` and `CreateChainParams(..., ChainType::MAIN)` while constructing static help/default descriptions. These are not runtime selection of the user's active chain. Preserve the upstream help generation pattern; add FREELY help values only after approved base parameters exist.

### 2.2 CLI chain summary

The `ChainToString()` switch used by the CLI network summary had explicit cases for MAIN, TESTNET, SIGNET and REGTEST, but not FREELY. A FREELY selection could reach the assertion instead of displaying a chain label. The FREELY case has been added. The core-chain CI workflow now builds the `bitcoin-cli` target as well as `bitcoind` and `test_bitcoin`, so this translation unit is covered by the focused build.

### 2.3 Production/test classification

The M1 branch introduced explicit `m_is_test_chain` and `m_is_production_chain` flags. Existing Bitcoin mainnet is production; built-in test chains are test chains. When FREELY parameters are eventually implemented, set classification explicitly:
- production: true;
- test chain: false;
- mockable: false.

Do not infer production status from `ChainType::MAIN`. Preserve the M1 guard in `src/init.cpp` that rejects `-testactivationheight` and `-vbparams` on every production chain.

### 2.4 Network magic dispatch

`GetNetworkForMagic()` currently recognises only the built-in Bitcoin network magics. It intentionally does not return FREELY while no approved FREELY message-start bytes exist. When network identity is approved, add the FREELY mapping and tests for all built-in identities plus FREELY; reject every collision. Do not guess a production magic.

## 3. RPC safety

The upstream RPC argument documentation specifies loopback defaults (127.0.0.1 and ::1). `-rpcbind` is ignored unless `-rpcallowip` is also supplied. The help text warns against exposing RPC to untrusted networks.

Acceptance requirements before any FREELY activation:
1. Keep RPC bound to loopback by default.
2. Do not add `-rpcallowip`, wildcard `-rpcbind`, or public REST defaults.
3. Require explicit, separately reviewed configuration for any remote RPC.
4. Verify authentication, cookie permissions, firewall assumptions and RPC allowlists.
5. Keep RPC disabled or local-only during all private development tests.

This audit does not change global Bitcoin RPC behaviour.

## 4. P2P and outbound networking

The upstream `DEFAULT_LISTEN` constant is true. `-bind` and `-whitebind` can soft-set listening on. If a FREELY parameter object were introduced without an explicit policy, an operator could start a publicly listening P2P node using ordinary upstream defaults.

Acceptance requirements before any FREELY activation:
1. Keep the FREELY selector fail-closed until the owner separately approves network activation.
2. Before creating a FREELY parameter object, add a chain-specific explicit listener policy and regression tests. Do not change Bitcoin mainnet/testnet defaults.
3. Ensure `-listen=0` disables NAT-PMP, address discovery, onion listening and inbound I2P acceptance through the existing parameter interaction.
4. Reject or clearly gate explicit `-bind`, `-whitebind`, onion and inbound I2P settings for a non-activated FREELY network.
5. Do not add DNS seeds, fixed seeds, public peer discovery or deployment in this PR.

The current fail-closed exception occurs before P2P initialisation; this is the present safety barrier, not proof that a future FREELY node will be private by default.

## 5. Data-directory isolation

The selected chain name is used by the base-parameter/config selection path to form a chain-specific data directory. The FREELY base-parameter factory currently throws, so no FREELY data directory is selected yet. Once approved parameters exist, retain a dedicated `freely` data-directory suffix and test that it cannot resolve to Bitcoin mainnet, testnet, signet or regtest storage.

## 6. Verification requirements

Before this audit can be marked fully verified:
- compile `bitcoind`, `bitcoin-cli` and `test_bitcoin`;
- run `chaintype_tests`, `validation_tests` and `pow_tests`;
- add a binary-level test proving `-chain=freely` exits with the expected fail-closed error;
- add CLI chain-label coverage where practical;
- test RPC loopback defaults and P2P listener suppression in the eventual FREELY parameter integration;
- test data-directory separation;
- test all network magic values for uniqueness.

## 7. Current status

| Item | Status |
|---|---|
| FREELY selector registered | Implemented |
| Base and consensus factories fail closed | Implemented |
| Production-only deployment override guard | Implemented on M1 base |
| CLI `-netinfo` FREELY label | Implemented; build pending |
| RPC default source audit | Documented |
| P2P default source audit | Documented; launch gate identified |
| FREELY network magic | Not assigned; correctly absent |
| FREELY production data directory | Not activated |
| Binary-level fail-closed startup test | Pending |
| Runtime RPC/P2P policy tests | Pending until FREELY parameter object exists |

No production network identity, genesis block, DNS seed, public listener, or deployment is selected or activated by this work.
