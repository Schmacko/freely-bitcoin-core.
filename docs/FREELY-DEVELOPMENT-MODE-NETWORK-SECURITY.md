# FREELY development-mode network security

**Status:** Implemented as a gated development feature; exact-head CI is pending. This is not a production launch authorization or a security certification.

**Source baseline:** Bitcoin Core v32.1 fork
**Scope:** offline local development, loopback-only private-node development, P2P/RPC exposure controls, runtime peer-addition policy, and regression-test registration.

This document supersedes the earlier pre-candidate source audit for current FREELY startup behavior. It describes code-level restrictions; it is not an OS sandbox and does not protect against a local administrator deliberately changing firewall rules, forwarding ports, or running external proxy software.

## 1. Startup gate

Normal FREELY startup remains fail-closed. `CreateChainParams(..., ChainType::FREELY)` requires exactly one of:

- `-freelydev=1`: isolated offline development.
- `-freelyprivate=1`: loopback-only private development.

If neither or both are selected, startup is rejected. The candidate chain parameters are marked as production, not test or mockable. This prevents test-only activation overrides from being treated as production consensus configuration.

These modes do not activate a public network, authorize deployment, or enable production mining.

## 2. Offline development mode

The offline mode requires:

- `-listen=0` and exactly one `-connect=0` setting.
- No `-bind` or `-whitebind` listeners.
- `-discover=0`, `-dnsseed=0`, `-natpmp=0`, `-upnp=0`, and `-listenonion=0`.
- No `-addnode`, `-seednode`, proxy, onion, I2P, Tor, or external-IP configuration.
- No custom RPC bind or RPC allowlist; RPC retains the upstream loopback-only defaults.
- No ZMQ publish endpoints.

The runtime `addnode` RPC rejects peer additions in offline mode. The mode therefore cannot initiate or accept ordinary P2P connections through the configured node networking paths.

## 3. Loopback-only private development

The loopback mode is intentionally narrower than a LAN private network. It is limited to peers on the same host.

It requires:

- P2P listening enabled.
- At least one explicit `-bind`, and every bind must be a literal `127.0.0.1` or `[::1]` address, optionally with a port.
- Exactly one `-connect=0` setting, preventing automatic outbound peer discovery.
- No `-whitebind`, external discovery, DNS seeding, NAT-PMP, UPnP, onion listener, external IP, proxy, overlay network, seed node, or configured external peer.
- No custom RPC bind or allowlist; RPC remains loopback-only.
- No ZMQ publish endpoints.

The runtime `addnode` RPC permits only a single numeric loopback address. Hostnames, non-loopback IPv4/IPv6 addresses, IPv4-mapped IPv6 spellings, and lookalike host strings are rejected. The regtest-only `addconnection` RPC is not a FREELY bypass.

This mode is suitable for multiple local processes on one machine. It is not a LAN testnet, public testnet, or mainnet configuration.

## 4. External network side effects

Both development modes reject UPnP and NAT-PMP. Disabling P2P listening alone is not treated as sufficient isolation: port-mapping services can create router-side effects independently of the node's intended listener policy.

Both modes also reject DNS discovery, address discovery, onion/I2P/Tor configuration, external peer lists, and ZMQ publish endpoints. The loopback mode still allows explicit same-host P2P connections through the guarded RPC path.

## 5. Regression coverage

The Bitcoin Core functional test runner registers the following FREELY tests:

| Test | Purpose |
|---|---|
| `feature_freely_startup.py` | Normal startup without development authorization remains fail-closed |
| `feature_freely_development_startup.py` | Missing/conflicting modes and UPnP rejection in both modes |
| `feature_freely_offline_startup.py` | Offline genesis access, zero peers, and RPC peer-addition rejection |
| `feature_freely_loopback_network.py` | Two local nodes communicate only through loopback |
| `feature_freely_offline_wallet.py` | Wallet address formats, offline signing, and restart recovery; registered in the extended suite and run by wallet-enabled CI |

The candidate workflow runs the four startup/network tests alongside C++ chain-parameter, genesis, proof-of-work, validation, and Python genesis-header checks. The separate wallet workflow builds a wallet-enabled node and runs the offline wallet test.

Registration matters: the functional runner only executes named tests present in its script lists. The FREELY tests are now explicitly registered so focused workflow invocations cannot silently omit them.

## 6. Remaining limitations and launch gates

- The loopback restriction is a software configuration guard, not an OS-level network namespace or firewall.
- RPC remains available on loopback for development; local processes with access to the RPC credentials can invoke the node's allowed RPC methods.
- A local administrator can deliberately add external forwarding or proxy processes outside the node. Do not treat these modes as a hardened hostile-host sandbox.
- No DNS seeds or fixed seeds are configured.
- No public RPC/P2P exposure, public testnet/mainnet launch, mining deployment, or production genesis activation is authorized.
- Exact-head CI, complete code review, independent security review, and explicit launch authorization remain required before any production activation.

A queued, pending, skipped, cancelled, or infrastructure-failed workflow is not a passing result. This document records intended controls and test registration, not a claim that the current CI has passed.


## 7. Additional startup-guard regressions — 21 November 2026

The `feature_freely_development_startup.py` functional test now checks negative startup cases for both modes, in addition to the missing/conflicting-mode and UPnP cases above.

Offline-development cases reject:
- overriding the required `-connect=0`;
- configured `-addnode`;
- configured proxy use;
- custom/non-loopback RPC binding.

Loopback-private cases reject:
- a non-loopback `-bind`;
- any `-whitebind`;
- overriding the required `-connect=0`;
- configured external peers;
- a remote RPC allowlist.

The test explicitly supplies complete mode arguments for each attempted startup, so it does not rely on arguments from the initial test-node process. The test framework's `connect=0` configuration is also overridden in the negative cases to verify that a command-line value cannot weaken the guard.

A new workflow, `.github/workflows/freely-private-node-security-tests.yml`, builds `bitcoind`, `bitcoin-cli` and `test_bitcoin`, runs `chaintype_tests`, `freely_genesis_tests`, `pow_tests` and `validation_tests`, then runs the development-startup, offline-startup and loopback-network functional tests. It triggers for the dedicated private-node branch and for PRs targeting `freely/chainparams-candidate-integration`.

Implementation commits:
- `c6cec89e92d93666959d832d8724f90e305db787`: add startup guard regression cases.
- `e0fa6a1373a13bd38956a5deeb767d45c9189b31`: add focused security workflow.

The latest exact-head workflow is queued; no compile or functional-test pass is claimed for these additions yet. These tests do not activate production parameters or expose a public network.


## 8. Expanded C++ startup-guard coverage — 21 November 2026

Two table-driven C++ regression tests were added to `chaintype_tests`:

- `freely_loopback_private_mode_rejects_peer_and_overlay_configuration` verifies that configured addnode/seednode peers, proxies, onion/I2P/Tor services, Tor credentials, and remote RPC allowlists cannot be used in loopback-private mode.
- `freely_loopback_private_mode_rejects_external_discovery_and_listener_overrides` verifies that address discovery, DNS seeding, NAT-PMP, UPnP and onion listening cannot be re-enabled, and that disabling the required P2P listener is rejected.

These tests exercise `CreateChainParams` directly with isolated `ArgsManager` instances. They complement the functional startup tests and run in the existing `chaintype_tests` target. The focused workflow path filter now includes `src/test/chaintype_tests.cpp`, ensuring future changes to these guards trigger the security workflow.

Commits:
- `d257fc2d31144cb91b3feb543c236b3fd063a39f`: add private-mode peer/overlay and discovery guard tests.
- `ba1c0a85716d8a102a5db93dafc0a4ada6b8898b`: trigger focused security CI for chain-type test changes.

The new exact-head workflow has not yet completed. No build or test pass is claimed for these additions.


## 9. BIP94 timestamp-boundary functional regression — 21 November 2026

The integrated private-node test branch now carries `test/functional/feature_bip94.py` and registers it in `test/functional/test_runner.py`. The focused security workflow runs it alongside FREELY startup/offline/loopback tests.

The test uses Bitcoin Core's existing regtest-only `-test=bip94` switch, not FREELY chain selection. It builds the regtest 144-block difficulty period, submits a boundary block 601 seconds earlier than its parent while keeping it above median-time-past, and expects the BIP94-specific `time-timewarp-attack` rejection. It then verifies that the exact 600-second grace boundary is accepted.

This functional test exercises the shared v32.1 timestamp rule. It does not substitute for the production 2,016-block FREELY retarget-base C++ test, which is covered separately in `pow_tests`, and it does not enable or launch a FREELY network.

Commits:
- `d577a2a57f56569c9f59835443c990ee01498ddb`: add BIP94 functional regression.
- `1895c7ed35db19295b0062b4e45b5e7bf06c99cc`: register test in functional runner.
- `d928e41586951bd7fec424f575d6114e3d1088fc`: include test in focused private-node CI.

The updated exact-head workflow has not yet completed; no new BIP94 functional pass is claimed.
