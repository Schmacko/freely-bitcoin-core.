# FREELY production-readiness gate

## Status and scope

**Current status: BLOCKED — production readiness is not established.**

This document defines the evidence required before FREELY can be considered ready for a public production network. It is an engineering gate, not authorization to launch. It deliberately separates work that can be completed now from owner-controlled decisions and from evidence that requires a functioning FREELY chain.

All four owner-controlled protocol parameter areas were explicitly approved on 18 November 2026 and are pinned in docs/FREELY-APPROVED-PROTOCOL-PARAMETERS.md and contrib/freely/network-safety.json. The approved PoW limit, genesis nBits, non-genesis network identity, genesis template and activation matrix are pinned. The derived nonce and block hash are independently reproduced candidate outputs, but remain pending explicit owner sign-off as the final production genesis identity; the manifest labels them `candidate_pending_owner_approval`. The standalone C++ miner push-triggered workflow passed on current miner head `8e81ea9fbf9c0b079bad1d14e8383cd36a4912b5`; its PR-triggered verification and full CI remain queued/in progress. The current preflight head `24c4ebfe873bf30043fdb5b329b10143962b4fb0` has queued/in-progress workflows, not a new pass. Production startup must remain fail-closed until integrated C++ candidate parameters, exact-head node tests, wallet/security evidence and release gates are complete.

## Gate rules

1. A gate is not complete because a document exists. It needs implementation evidence and passing tests.
2. A workflow being queued, skipped, cancelled, or absent is not a pass.
3. Evidence must identify the exact commit SHA tested.
4. A test on Bitcoin regtest validates the test harness or upstream behavior; it does not prove FREELY production parameters or a live FREELY network.
5. Synthetic fixtures are for testing validators only and must never be promoted into production configuration.
6. No production launch, mining deployment, public RPC/P2P exposure, DNS seed publication, or genesis activation is authorized by this checklist.
7. Any missing or ambiguous consensus parameter, any mismatch in the derived genesis commitment, or any missing required implementation/release evidence blocks the production gate.

## Production gates and acceptance evidence

### G0 — Owner-approved protocol parameters

**Status: APPROVED — implementation and verification remain in progress.**

The owner explicitly approved all four proposal areas on 18 November 2026. The canonical exact values are recorded in `docs/FREELY-APPROVED-PROTOCOL-PARAMETERS.md` and `contrib/freely/network-safety.json`.

Already approved:
- SHA-256d; `powLimit=00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff`; genesis `nBits=0x1d00ffff`.
- 600-second spacing; 2,016-block retarget interval; 1,209,600-second timespan; 1/4–4× clamp; minimum-difficulty and no-retargeting disabled; BIP94 enabled from genesis.
- P2P magic `fa c3 b7 d1`; P2P/RPC ports 49444/49445; `freely` data directory/config section; approved Base58/WIF/BIP32 prefixes and Bech32 HRP `fly`.
- Genesis version 1, timestamp 1,794,960,000, approved coinbase message/output script, 50 FLY unspendable coinbase.
- BIP34, BIP65, BIP66, CSV and SegWit at height 1; TESTDUMMY disabled with the approved version-bits settings.

Derived candidate-genesis evidence now present (the final nonce/hash owner sign-off and full G0 gate remain IN PROGRESS):
- Historical miner workflow [44910736974](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44910736974) passed on earlier head `865026e755239bf0a89e7a5b91513f896bb9858a`. On current miner head `8e81ea9fbf9c0b079bad1d14e8383cd36a4912b5`, push-triggered candidate verification [45204029247](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204029247) passed; PR-triggered verification [45204041280](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204041280) is queued and full CI [45204040649](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204040649) is in progress.
- Historical network-safety preflight [44899513446](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44899513446) passed on earlier head `e7019df06a72c8ec37922eca34d6f4cbeefc207f`. Current preflight head `24c4ebfe873bf30043fdb5b329b10143962b4fb0` has run [45204530104](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204530104) queued and full CI [45204530112](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204530112) in progress.
- The same preflight run intentionally confirmed the production evidence ledger remains BLOCKED at 0/9 gates. This is the expected safe result, not a failed preflight.
- The manifest pins the derived nonce/hash as candidate-only, alongside the approved coinbase/Merkle commitment, and independently rebuilds the coinbase and 80-byte header.

Remaining G0 evidence:
- Complete exact-head C++ candidate integration tests for `CFreelyCandidateParams`, including fixed genesis hash/PoW and manifest-to-C++ parameter equality. Replacement candidate PR #22 head `92239197131c5d0dbbf6f77fbb30760facb18460` has focused core-chain workflow [45203933162](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45203933162) pending and full CI [45203932853](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45203932853) in progress.
- Complete custom signet challenge-derived magic collision tests on the integrated candidate head.
- Reconcile PR #21's dependency on closed-unmerged PR #20 with replacement candidate PR #22 before merge.
- Obtain explicit owner sign-off for the derived candidate nonce and block hash as the final production genesis identity; otherwise keep them candidate-only and do not activate production.
- Obtain passing full CI and startup/functional tests on the integrated candidate branch; a standalone miner/preflight pass is not a node build.

Acceptance:
- The approved baseline and candidate genesis commitment are machine-validated and independently reproduced; the derived nonce/hash still require explicit owner sign-off as final production identity.
- The integrated C++ `CChainParams` and manifest agree value-for-value on the exact candidate head.
- C++ genesis, chain selection, proof-of-work, retarget, signet-collision and fail-closed startup tests pass on that exact head.
- No collision with built-in Bitcoin networks, including default/custom signet magic, is present.
- The remaining implementation/release evidence for G0 is complete before marking the gate PASS.

### G1 — Consensus implementation

Required:
- Subsidy and halving schedule verified using integer base units only.
- Retarget implementation and boundary rules verified against the approved 2,016-block / 1,209,600-second policy.
- BIP94 enabled from genesis and first-block-of-period behavior tested.
- Genesis coinbase remains unspendable; accounting documents scheduled versus spendable supply.
- Chainwork, target validation, compact encoding, reorg and block validity behavior reviewed against Bitcoin Core v32.1.
- No test-only override can alter production consensus.

Acceptance:
- Relevant C++ unit and functional tests pass on exact candidate commit.
- Boundary, malformed-input, overflow and regression tests pass.
- Independent source review finds no unresolved consensus-critical issue.

### G2 — Network identity and chain selection

Required:
- Explicit FREELY chain selection; no fallback to MAIN or any other chain.
- FREELY explicitly classified as production, not test.
- Unique P2P magic, ports, data directory, address formats and Bech32 HRP.
- `GetNetworkForMagic` registration and collision tests, including signet challenge-derived magic.
- Wallet key/address encoders use the active FREELY chain parameters.

Acceptance:
- Automated source and runtime tests cover selection, serialization, magic mapping and collision cases.
- Starting FREELY with missing or invalid parameters fails closed before network activity.
- No silent MAIN defaults or Bitcoin mainnet identity leaks.

### G3 — RPC and P2P security

Required:
- RPC binds to loopback by default; remote access requires explicit, documented operator configuration.
- Authentication is mandatory for any non-loopback RPC listener; cookie/auth handling and file permissions are verified.
- No wildcard public RPC listener in default configuration.
- P2P listen/bind behavior, outbound peers, seed configuration, peer limits and bans are reviewed.
- Firewall and port exposure guidance is documented.
- Debug, profiling and unsafe test options cannot silently become production defaults.
- Sensitive credentials and tokens are never logged.

Acceptance:
- Automated config/startup tests for loopback defaults, authentication, invalid credentials, bind addresses and unsafe combinations.
- External security review of RPC/P2P threat model and configuration.
- No critical/high unresolved findings.

### G4 — Wallet safety and recovery

Required:
- Wallet creation, encryption, unlock/lock, backup, restore and rescan paths verified.
- Descriptor and key import/export behavior reviewed for FREELY address parameters.
- Transaction creation, fee handling, signing, broadcast and reorg recovery tested.
- Wallet database corruption and interrupted shutdown/restart behavior tested.
- Backup instructions explain seed/private-key custody and offline recovery.

Acceptance:
- Wallet-enabled build and relevant functional tests pass on exact commit.
- Backup is restored successfully into a clean data directory in an isolated test.
- No testnet/regtest/Bitcoin address-prefix leakage in FREELY wallet output.

### G5 — Build, release and supply-chain integrity

Required:
- Reproducible documented build environment and pinned dependency/toolchain versions.
- Linux build; supported platform builds; wallet-enabled and wallet-disabled configurations.
- Compiler warnings, sanitizers, static analysis and dependency checks.
- Release artifacts are traceable to signed/tagged source commits and checksums.
- Release notes, upgrade/downgrade policy and data migration behavior documented.

Acceptance:
- Required CI matrix passes on exact release candidate SHA.
- Release artifact checksums and source provenance are published.
- No unreviewed or unexplained dependency changes.

### G6 — Operations, observability and recovery

Required:
- Data-directory isolation, permissions, disk-space behavior and safe shutdown.
- Logs expose useful operational errors without secrets.
- Crash recovery, database verification, reindex and rescan procedures documented and tested.
- Node health metrics and alert thresholds defined.
- Backup, restore, incident response and upgrade/rollback runbooks prepared.
- Resource requirements and expected bandwidth/storage are measured.

Acceptance:
- Repeatable operational test on isolated infrastructure.
- Recovery from forced shutdown and corrupted test data demonstrated.
- Operator runbooks independently reviewed.

### G7 — Mining and economic/security assumptions

Required:
- Block template, coinbase construction, subsidy, fees and payout behavior verified.
- Mining RPC/stratum/miner integration reviewed if provided.
- Hashrate assumptions and low-hashrate attack exposure documented.
- 51% attack, reorg, selfish mining, eclipse, double-spend and censorship risks assessed.
- No implication that Bitcoin hashpower/security is inherited.

Acceptance:
- End-to-end mining and block acceptance tests on an isolated FREELY test network.
- Independent security review of economic attack assumptions.
- No production mining rollout before explicit owner approval.

### G8 — Independent security review and launch authorization

Required:
- Independent review of consensus, networking, wallet, RPC, build/release and operations.
- Threat model and findings register with severity, owner and remediation.
- Critical/high findings resolved and retested.
- Launch plan, monitoring, incident response and rollback plan.
- Explicit owner authorization for production genesis/network activation and launch.

Acceptance:
- Written independent audit outcome.
- All critical/high findings closed or explicitly risk-accepted by the owner.
- Separate explicit launch authorization. This document does not provide it.

## Evidence ledger template

For every gate, record:
- Gate ID and status: NOT STARTED / IN PROGRESS / BLOCKED / PASS.
- Exact commit SHA tested.
- Workflow URL and conclusion.
- Test names and logs.
- Reviewer and date.
- Open findings and owner.
- Whether the evidence is unit, functional, integration, operational or independent-audit evidence.

A gate may be marked PASS only when all its acceptance evidence exists. Do not calculate production readiness by averaging incomplete gates: report the gate states and blockers.

## Work that can proceed before owner decisions

The following can be advanced without selecting production parameters:
- Source audits for chain selection, RPC/P2P defaults, wallet chain-parameter use and unsafe test-option guards.
- Test harnesses and negative tests for incomplete/invalid production configuration.
- CI path coverage, reproducible build documentation, static analysis and dependency inventory.
- Operational runbooks and backup/recovery test design.
- Threat model and independent-audit preparation.
- Release gate automation that refuses to pass while required evidence or owner-approved values are missing.

## Current blockers

1. Exact-head candidate C++ integration CI: PR #20 candidate workflow is queued; the derived genesis commitment has standalone C++/Python verification but the integrated `CFreelyCandidateParams` build and regression suite are not yet proven.
2. Retarget boundary/compact-target additions on PR #6 have a new exact head and are awaiting focused PoW CI.
3. Private-node startup/security and BIP94 functional regressions on PR #21 are queued; the new C++ guard tests have not yet passed CI.
4. Wallet-enabled workflow on PR #11 previously failed because `bitcoin-wallet` was not built; the workflow was corrected to build that target and the new exact-head run is pending.
5. Full cross-platform CI and wallet/node acceptance evidence remain incomplete; queued/cancelled CI is not a pass.
6. Independent security review, operational/recovery evidence and separate explicit production launch authorization remain outstanding.
7. Final owner approval of the derived genesis nonce and block hash is still required before freezing the production network identity.

The approved baseline values for `powLimit`, genesis `nBits`, timestamp/coinbase template, non-genesis network identity, BIP94 policy and activation matrix are fixed. The derived nonce and block hash remain candidate-only pending explicit owner sign-off; do not treat them as final production identity or activate them.

## Current conclusion

FREELY can make real progress on engineering readiness now, but it is not safe to describe the project as production-ready. Keep production readiness **BLOCKED** until all gates above have evidence and all owner-controlled decisions have been approved. The objective is a verifiable release gate, not a cosmetic percentage.
