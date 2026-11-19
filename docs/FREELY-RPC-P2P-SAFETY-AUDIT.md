# FREELY RPC, P2P and chain-selection safety audit

**Status:** source audit and fail-closed design review  
**Source baseline:** Bitcoin Core v32.1 fork, FREELY core-chain implementation branch  
**Date:** 17 November 2026  
**Scope:** chain selection, RPC binding defaults, P2P listener defaults, data-directory isolation, CLI chain reporting, and network-magic dispatch.

This document records source-level findings. It does not claim that a FREELY node is runnable, that a public service is safe, or that a FREELY network has been activated.

## 1. Executive findings

- `-chain=freely` is registered. `CreateBaseChainParams(FREELY)` now exposes the approved CLI data-directory/RPC identity; `CreateChainParams(..., FREELY)` still throws until the derived genesis commitment and CChainParams integration are verified. Full node startup therefore remains fail-closed.
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

`GetNetworkForMagic()` now recognises the owner-approved FREELY magic `fa c3 b7 d1` on the dependent PR #13 branch. The mapping is a message-to-chain classification only; it does not construct FREELY CChainParams or enable P2P startup. The preflight checks collision against Bitcoin mainnet, testnet3, testnet4, regtest and default signet; custom signet challenges still require runtime collision validation.

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

The selected chain name is used by the base-parameter/config selection path to form a chain-specific data directory. The base-parameter factory now returns the approved `freely` data-directory suffix and RPC port 49445 for CLI/config selection. Full node startup still stops in the consensus factory. The eventual CChainParams must preserve the separate identity and test the data directory against Bitcoin mainnet, testnet, signet and regtest storage.

## 6. Verification requirements

Before this audit can be marked fully verified:
- compile `bitcoind`, `bitcoin-cli` and `test_bitcoin`;
- run `chaintype_tests`, `validation_tests` and `pow_tests`;
- run the new binary-level `feature_freely_startup.py` test proving `-chain=freely` exits with the expected fail-closed error;
- add CLI chain-label coverage where practical;
- test RPC loopback defaults and P2P listener suppression in the eventual FREELY parameter integration;
- test data-directory separation;
- test all network magic values for uniqueness.

## 7. Current status

| Item | Status |
|---|---|
| FREELY selector registered | Implemented |
| Base factory exposes approved CLI identity; consensus factory remains fail-closed | Implemented |
| Production-only deployment override guard | Implemented on M1 base |
| CLI `-netinfo` FREELY label | Implemented; build pending |
| RPC default source audit | Documented |
| P2P default source audit | Documented; launch gate identified |
| FREELY network magic | Owner-approved `fa c3 b7 d1`; lookup added in PR #13; CChainParams/P2P activation still gated |
| FREELY base data directory | Approved suffix `freely` is available to CLI; full node activation remains blocked |
| Binary-level fail-closed startup test | Implemented; current-head CI queued |
| Runtime RPC/P2P policy tests | Pending until FREELY parameter object exists |

The production network identity values are owner-approved and recorded in the canonical parameter baseline, but no production CChainParams, verified genesis commitment, DNS seed, public listener, or deployment is activated by this work.


## Startup regression hardening — 18 November 2026

The binary-level `feature_freely_startup.py` test now invokes `bitcoind -chain=freely` without `-listen=0`. This is deliberate: Bitcoin Core v32.1's upstream `DEFAULT_LISTEN` is true, so the test verifies that FREELY's unresolved-parameter guard stops startup before the normal P2P listener path, rather than relying on a test-supplied setting that suppresses listening.

The focused workflow was triggered for the updated PR #8 head `a20399d39086c75dc895442e78130fb95993c747` (run [44211275120](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44211275120)). The job was still queued at the latest inspection. This is implemented test coverage, not a verified runtime pass.


## 8. Extended startup and exposure source audit — 18 November 2026

This section records a fresh read of the current PR #8 source files (src/init.cpp, src/chainparams.cpp, src/chainparamsbase.cpp, src/chainparamsbase.h, src/net.cpp and src/rpc/server.cpp). It is a source audit, not a runtime test.

### 8.1 Mainnet references in startup argument registration

SetupServerArgs() constructs CreateBaseChainParams(ChainType::MAIN) and CreateChainParams(argsman, ChainType::MAIN) to populate upstream argument help/default descriptions. The active chain is selected later from args.GetChainType() in the normal startup path. These MAIN constructions are help/default metadata, not a fallback that silently changes a selected FREELY node into Bitcoin mainnet.

The FREELY base factory returns only the approved CLI identity; the FREELY consensus factory throws. The latter remains the decisive guard: bitcoind cannot obtain consensus parameters and cannot proceed to normal node initialisation.

### 8.2 Test-only startup overrides

src/chainparams.cpp parses -testactivationheight and -vbparams through HandleDeploymentArgs(). The argument declarations in src/chainparamsbase.cpp mark these options DEBUG_ONLY; the M1 production-chain guard in src/init.cpp must also remain in place so a future production FREELY chain cannot be modified by test overrides merely because a debug build accepts the option.

The -test=<option> handler in src/init.cpp explicitly rejects use unless chainparams.GetChainType() == ChainType::REGTEST. Preserve this restriction. FREELY must not inherit regtest's mockability or test-only consensus controls.

### 8.3 RPC exposure findings

The source declares loopback RPC bind defaults in its help text and documents that -rpcbind is ignored unless -rpcallowip is also supplied. This is a safe upstream default, but it is not a FREELY-specific enforcement mechanism. A future FREELY activation review must test the effective socket bindings, cookie authentication, allowlist and firewall assumptions. Never treat a documentation default as a substitute for a socket-level test.

### 8.4 P2P exposure findings

The source declares DEFAULT_LISTEN as true. It also has parameter interactions that disable discovery, onion listening and inbound I2P acceptance when listening is disabled. Those interactions are useful but do not make an unconfigured production chain safe automatically: explicit bind options and other network settings must be reviewed at activation time.

The current test feature_freely_startup.py intentionally supplies only -chain=freely and leaves upstream listening defaults untouched. The expected fail-closed error must occur before P2P startup. The focused test run is still queued; no runtime pass is claimed.

### 8.5 Network identity and peer discovery

src/chainparamsbase.h includes freely in the accepted chain-name list; the base factory exposes the approved RPC port 49445 and data-directory suffix `freely`. PR #13 adds `fa c3 b7 d1` to GetNetworkForMagic(). No FREELY DNS seeds or fixed seeds are configured in this implementation stage.

### 8.6 Required follow-up before parameter activation

- Add chain-specific FREELY listener defaults and tests before constructing live FREELY parameters.
- Test RPC sockets and P2P sockets at runtime, including explicit bind/allowlist adversarial cases.
- Test the data-directory suffix and cookie path against every built-in chain.
- Keep the approved FREELY message-start mapping and static built-in collision tests; add runtime validation for custom signet challenge magic before any future network activation.
- Add explicit tests that production FREELY rejects -testactivationheight, -vbparams and every regtest-only -test option.
- Inspect every new ChainType switch when the selector evolves; keep FREELY cases exhaustive.

Audit conclusion: no remaining inappropriate active-chain fallback to Bitcoin MAIN was identified in the inspected startup path. The remaining MAIN references in SetupServerArgs() are static help/default construction. This conclusion is limited to the inspected files and must not be described as a repository-wide exhaustive grep. Runtime RPC/P2P policy and network-identity tests remain blocked on approved FREELY parameters.


## 9. Owner-approved identity and message-magic registration — 19 November 2026

The owner approved the four protocol parameter proposal areas on 18 November. The canonical identity includes:
- message magic `fa c3 b7 d1`;
- P2P port 49444 and RPC port 49445;
- data-directory/config section `freely`;
- P2PKH 55, P2SH 117, WIF 183;
- extended public/private versions `04464c59` / `04666c79`;
- Bech32 HRP `fly`.

The base-chain-parameter layer exposes only the approved CLI data-directory and RPC port. The consensus factory deliberately continues to throw until the approved genesis candidate's nonce/hash are mined and independently reproduced and the CChainParams implementation is reviewed.

PR #13 adds the approved message magic to `GetNetworkForMagic()` and tests that it maps to `ChainType::FREELY`, while an unknown magic remains rejected. This does not enable a FREELY P2P listener, create production CChainParams, or launch a network.

The focused core-chain workflow executes `chaintype_tests`, `freely_genesis_tests`, `validation_tests` and `pow_tests`. The chain-type suite now checks:
- the approved FREELY magic maps to `ChainType::FREELY`;
- an unknown magic is rejected;
- all five built-in Bitcoin network magics still map to MAIN, TESTNET, TESTNET4, SIGNET and REGTEST respectively.

The workflow was source-reviewed and repaired after three defects were found:
- the CTest regular expression lacked its closing quote and end anchor;
- the startup functional-test step was duplicated;
- the source-tree functional runner was used even though CMake generates `build/test/config.ini`; the workflow now invokes `build/test/functional/test_runner.py`, matching the corrected wallet workflow.
- shell commands were flattened to single lines to avoid fragile line-continuation escaping.

The code/test revision immediately before this documentation-only refresh was `8574cd61d619be519d56b4277cb61197b32f5bbf`. The workflow file and C++ test source were fetched back from that exact revision and inspected. No focused workflow run was yet visible for that revision; no C++ build or test pass is claimed. The documentation update does not change code, but the resulting PR head still requires current-head CI before merge.

Static identity collision checks include the pinned v32.1 default BIP325 signet magic. A custom `-signetchallenge` derives a different magic and must be checked at runtime before any future network activation.
