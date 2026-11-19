# FREELY Wallet and Node Readiness Plan

## Status

Workstream opened against the current core-chain implementation branch. This is an integration plan, not a claim that FREELY is a runnable network or that wallet tests have passed.

## Safety boundary

- Keep `-chain=freely` fail-closed until the derived genesis nonce/hash are mined and independently verified, the FREELY CChainParams integration is complete, and release evidence gates pass. All four parameter areas are owner-approved; the canonical values are in `docs/FREELY-APPROVED-PROTOCOL-PARAMETERS.md`.
- Do not invent or duplicate parameter values in this workstream. Consume the owner-approved network/address/PoW/activation baseline from `docs/FREELY-APPROVED-PROTOCOL-PARAMETERS.md`; do not add DNS seeds or activate the network.
- Do not expose RPC or P2P services publicly, deploy nodes, mine on a public network, or launch a testnet/mainnet.
- Use Bitcoin Core's existing regtest only as a local test harness. Regtest is not FREELY.
- Preserve Bitcoin Core v32.1 wallet, descriptor, key-management, transaction, persistence, and RPC architecture unless a demonstrated FREELY-specific incompatibility requires a minimal change.
- Use integer base units for consensus and monetary calculations.

## Existing upstream capabilities to retain

The v32.1 source tree already contains the wallet initialization interface, wallet RPC modules, node initialization and RPC server, and functional wallet tests. The first task is to establish which upstream components can be reused without modification and identify chain-parameter assumptions before adding FREELY-specific code.

## Work packages

### WN-1: Node lifecycle and configuration
- Audit startup, shutdown, datadir selection, chain selection, lock handling, configuration parsing, and fail-closed behaviour.
- Verify FREELY cannot silently fall back to Bitcoin mainnet/testnet parameters.
- Add regression tests for unsupported/unfinalized FREELY startup and ensure no global chain parameters are selected on failure.

### WN-2: RPC readiness
- Inventory node and wallet RPCs and their chain-parameter dependencies.
- Define a safe local-only RPC test profile.
- Test node information, blockchain information, network information, wallet loading, and RPC warmup/error paths.
- Do not enable remote/public RPC.

### WN-3: Wallet compatibility
- Retain descriptor-wallet architecture and existing key derivation/storage implementation.
- Audit address encoding, network parameters, extended key prefixes, message signing, URI handling, and output-type defaults.
- Although address/key values are approved, keep FREELY encodings disabled until CChainParams integration, genesis verification, Base58/Bech32 round trips, and wallet tests pass.
- Review wallet encryption, backup, restore, descriptor import/export, and keypool behaviour.

### WN-4: Transaction lifecycle
- Exercise transaction construction, fee estimation, coin selection, signing, broadcast, confirmation, replacement, and reorg handling using local regtest fixtures.
- Confirm wallet amounts use integer satoshi/base-unit semantics and reject out-of-range values.
- FREELY-specific transaction tests must wait for CChainParams integration and a verified genesis commitment; local Bitcoin regtest remains only a harness, not a FREELY network.

### WN-5: Persistence, recovery, and safety
- Test wallet database creation, clean shutdown, restart, backup, restore, corruption handling, and rescan behaviour.
- Verify wallet and node data directories are distinct from Bitcoin network directories.
- Document backup and recovery procedures before any user funds could exist.

### WN-6: Integration and acceptance
- Add focused functional tests and CI coverage.
- Require successful build, wallet tests, node functional tests, RPC tests, and review of all chain-parameter assumptions.
- Keep all PRs draft until current-head CI and technical review pass.

## Initial acceptance gates

1. Existing upstream wallet and node tests remain intact.
2. FREELY chain selection remains fail-closed until the derived genesis commitment is verified and CChainParams/runtime integration passes.
3. No Bitcoin mainnet address or network identity is accepted as a FREELY identity by accident.
4. Local regtest tests are explicitly labelled as harness tests, never as FREELY network tests.
5. RPC defaults remain local-only and no public listener is introduced.
6. Backup/restore and encrypted-wallet regression coverage is documented and tested.
7. No production network activation or deployment is included.

## Dependencies and owner decisions

The workstream can progress on source audits, node lifecycle safety, RPC test design, wallet persistence/recovery tests, and upstream compatibility. FREELY address generation, transaction validation against a live FREELY chain, mining rewards, and production wallet interoperability depend on the CChainParams implementation, independently mined/verified genesis nonce and hash, and successful FREELY-specific encoding/consensus tests. The powLimit, genesis nBits, network identity, and activation matrix are approved, not open owner decisions.

## Progress reporting

Report separately:
- code written;
- code compiled;
- tests executed and passed;
- changes merged;
- remaining parameter-dependent work.

Do not count documentation or test plans as completed runtime wallet/node functionality.

## First implementation increment: wallet-enabled regression CI

A dedicated GitHub Actions workflow, `.github/workflows/freely-wallet-node-readiness.yml`, builds the fork with wallet support enabled and runs existing Bitcoin Core v32.1 functional tests in isolated local-regtest fixtures.

Coverage includes:
- wallet backup and restore;
- wallet encryption and startup;
- wallet creation and basic wallet lifecycle;
- exported watch-only recovery;
- descriptor creation, import and rescan;
- transaction creation and send;
- wallet recovery across reorganisation;
- multiwallet isolation;
- Taproot compatibility;
- keypool and hierarchical deterministic wallet behaviour;
- blockchain and network RPC regression;
- configuration, initialization and controlled-abort behaviour.

This is an upstream compatibility gate using isolated local regtest fixtures. It is **not** a test of a live FREELY chain, production addresses, FREELY consensus parameters, or public network connectivity. The workflow does not deploy a node or expose RPC/P2P services.

The workflow enables SQLite-backed wallet support, unlike the core-chain plumbing workflow which configures `ENABLE_WALLET=OFF`. It builds the node/CLI before invoking the functional test runner.

### Validation status

- Expanded workflow committed: pending GitHub Actions execution.
- Wallet-enabled C++ build: not yet verified.
- Functional test results: not yet verified.
- No FREELY-specific wallet address or production transaction support is claimed.

## Source audit: address and extended-key network separation

Reviewed against the pinned v32.1 implementation on 18 November 2026:

- `src/key_io.cpp` builds Base58 P2PKH/P2SH addresses from the active `CChainParams` prefixes.
- SegWit address encoding uses `CChainParams::Bech32HRP()`; decoding explicitly rejects a different HRP.
- Private-key WIF encoding/decoding uses the active `SECRET_KEY` prefix.
- Extended public and private key encoding/decoding use the active `EXT_PUBLIC_KEY` and `EXT_SECRET_KEY` prefixes.
- Wallet address RPCs route through `EncodeDestination` and `DecodeDestination`, so they inherit the active chain parameters rather than hard-coding Bitcoin mainnet address formats.

**Implication:** the upstream wallet/address architecture is reusable without a FREELY-specific address encoder. The approved FREELY parameter object must use the unique Base58 prefixes, extended-key versions, and Bech32 HRP recorded in the canonical approved-parameter document. This source audit does not itself enable FREELY address generation.

**Validation boundary:** existing `key_io_tests` exercise Bitcoin mainnet, testnet, signet, and regtest vectors. They cannot validate FREELY until FREELY parameters exist. Current wallet CI is upstream compatibility coverage only; it is not a FREELY address-format test.

## Dependency review: pull-request integration order (18 November 2026)

The live GitHub branch comparison and changed-file lists show the following integration relationships. All PRs remain drafts; this is a dependency assessment, not approval to merge.

| PR | Branch / scope | Dependency and integration finding |
|---|---|---|
| #1 | `freely/m1-consensus` | Foundation for #8. Based directly on `freely/upstream-v32.1`. Contains shared `.github/workflows/ci.yml` and CI image changes. |
| #8 | `freely/core-chain-implementation` | Correctly based on #1's current head. Current comparison: 12 commits ahead, 0 behind. Must follow #1 in integration order. |
| #11 | `freely/wallet-node-readiness` | Targets current #8 head `3078f79d6452dfccc9a1f4baeb0c0f3f1f635358`. Current comparison: PR #11 head `65c5e697414b75943eea2d8cd76cb756bc8d9981` is 9 commits ahead and 0 behind. Its two files (wallet workflow and this document) do not overlap PR #8. Wallet CI run `44537919886` is queued; no wallet-enabled build or functional test pass is verified. |
| #12 | `freely/reconciled-docs` | Consolidates the current consensus specification, architecture and source audit. PRs #2, #3 and #7 are closed unmerged and superseded by this canonical documentation branch. PR #12 head `c58b0b8772543b1dd417a04c5b703b7f78a095c7`; focused and full CI remain queued. |
| #13 | `freely/network-magic-registration` | Child of #8; adds the approved message-magic lookup and a C++ regression test. Current head `73560540e78fcc9b90754fd22aa33813e1c99ee3`, 5 commits ahead / 0 behind #8. Focused and full CI queued. |
| #2/#3/#7 | Superseded documentation branches | Closed unmerged; do not merge. PR #12 is the canonical reconciliation. |
| #9 | `freely/ci-windows-safe` | Overlaps #1 on `.github/workflows/ci.yml` and `ci/test/00_setup_env_native_nowallet.sh`. Consolidate the Windows-safe checkout and push-trigger changes into one reviewed CI change; avoid duplicate competing merges. |
| #6 | `freely/retarget-test-vectors` | Adds `src/test/pow_tests.cpp` and focused retarget/BIP94 coverage; currently separate from #1/#8. Validate against the same v32.1 base and integrate after reviewing consensus semantics. |
| #10 | `freely/network-safety-preflight` | Independent fail-closed preflight. Approved values are now pinned exactly; only the derived genesis hash/nonce and release evidence remain incomplete. Head `fcf736b5102f9889e3a93dfe238fa138dc54c6d8`; 43 Python test methods are written, but the exact-head workflow is queued. |
| #4/#5 | PoW audit / retarget policy | Documentation workstreams recording the owner-approved PoW policy; use them with #6's executable vectors for C++ integration and review. Approval does not itself activate a network. |

### Recommended integration sequence

1. Review and resolve the shared CI changes between #1 and #9; preserve one canonical CI implementation.
2. Complete #1 consensus and production-classification review, then integrate #1.
3. Integrate #8 on top of #1 and rerun chain-selector/startup tests.
4. Verify #11 remains 0 behind / 5 ahead of the integrated #8 head; if #8 advances first, refresh #11 before running the wallet-enabled build, wallet functional suite, RPC and node functional suite.
5. Reconcile #2/#7/#3 overlapping documents before integrating the consensus/network design package.
6. Review #4/#5 against #6's executable vectors; integrate retarget code only after BIP94/powLimit policy is formally resolved.
7. Integrate #10 after its own validator tests pass; keep production identity values unset until explicit owner decisions.

### CI and review gates

- A branch being ahead/behind or GitHub reporting it mergeable does not establish technical merge readiness.
- Require current-head focused workflow success and relevant general CI success.
- Review complete diffs, upstream compatibility, test logs, conflicts and unresolved review threads.
- Never merge production parameters or activate the network through a documentation/CI integration.
- PR #11's wallet tests exercise upstream regtest behaviour only; no FREELY network test is claimed.



## Live branch comparison refresh — 18 November 2026

The current GitHub compare endpoints show `freely/core-chain-implementation` at `5f8fa282ea0675c41c2a5aa21db36d5e1bf47744` and `freely/wallet-node-readiness` at `24800203855264f0b490ec80a602389754a0be81`. PR #11 is 5 commits ahead and 0 behind PR #8. The earlier note describing a diverged relationship is superseded. The wallet workflow remains queued; this graph comparison does not constitute a build or test pass.


## Live dependency and approval refresh — 19 November 2026

All four protocol parameter proposal areas were approved on 18 November. The canonical values are recorded in `docs/FREELY-APPROVED-PROTOCOL-PARAMETERS.md`; the implementation preflight now checks exact values and exact activation/version-bits maps. The remaining genesis values are derived outputs: nonce and block hash must be mined/reproduced, not selected by another owner vote.

Current branch graph:
- PR #8: `3078f79d6452dfccc9a1f4baeb0c0f3f1f635358`.
- PR #11: `65c5e697414b75943eea2d8cd76cb756bc8d9981`, 9 commits ahead / 0 behind PR #8.
- PR #13: `73560540e78fcc9b90754fd22aa33813e1c99ee3`, 5 commits ahead / 0 behind PR #8; adds `GetNetworkForMagic` registration and expands the focused CTest filter to execute `freely_genesis_tests`.
- PR #12 is the canonical documentation reconciliation; PRs #2, #3 and #7 are closed unmerged.

Current wallet/node workflow:
- Focused wallet/node run [44537919886](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44537919886): queued.
- Full CI run [44537919781](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44537919781): queued.
- Wallet-enabled C++ build and functional tests remain unverified.

The wallet workstream remains upstream-compatibility testing on local regtest only. No FREELY node is selectable, no public RPC/P2P service is exposed, and no launch/deployment is authorized.
