# FREELY Wallet and Node Readiness Plan

## Status

Workstream opened against the current core-chain implementation branch. This is an integration plan, not a claim that FREELY is a runnable network or that wallet tests have passed.

## Safety boundary

- Keep `-chain=freely` fail-closed until the owner-approved production consensus and network parameters are implemented.
- Do not assign FREELY address prefixes, Bech32 HRP, ports, message magic, genesis, powLimit, seeds, or activation heights in this workstream.
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
- Keep FREELY address/key encodings disabled until their values are approved.
- Review wallet encryption, backup, restore, descriptor import/export, and keypool behaviour.

### WN-4: Transaction lifecycle
- Exercise transaction construction, fee estimation, coin selection, signing, broadcast, confirmation, replacement, and reorg handling using local regtest fixtures.
- Confirm wallet amounts use integer satoshi/base-unit semantics and reject out-of-range values.
- FREELY-specific transaction tests must wait for approved consensus parameters and an operational chain.

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
2. FREELY chain selection remains fail-closed while production parameters are unresolved.
3. No Bitcoin mainnet address or network identity is accepted as a FREELY identity by accident.
4. Local regtest tests are explicitly labelled as harness tests, never as FREELY network tests.
5. RPC defaults remain local-only and no public listener is introduced.
6. Backup/restore and encrypted-wallet regression coverage is documented and tested.
7. No production network activation or deployment is included.

## Dependencies and owner decisions

The workstream can progress on source audits, node lifecycle safety, RPC test design, wallet persistence/recovery tests, and upstream compatibility. FREELY address generation, transaction validation against a live FREELY chain, mining rewards, and production wallet interoperability depend on the unresolved genesis, powLimit, activation matrix, and network identity decisions.

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

**Implication:** the upstream wallet/address architecture is reusable without a FREELY-specific address encoder. The eventual FREELY parameter object must nevertheless provide unique, reviewed Base58 prefixes, extended-key prefixes, and Bech32 HRP before address generation or wallet interoperability can be enabled. No values are assigned by this audit.

**Validation boundary:** existing `key_io_tests` exercise Bitcoin mainnet, testnet, signet, and regtest vectors. They cannot validate FREELY until FREELY parameters exist. Current wallet CI is upstream compatibility coverage only; it is not a FREELY address-format test.

## Dependency review: pull-request integration order (18 November 2026)

The live GitHub branch comparison and changed-file lists show the following integration relationships. All PRs remain drafts; this is a dependency assessment, not approval to merge.

| PR | Branch / scope | Dependency and integration finding |
|---|---|---|
| #1 | `freely/m1-consensus` | Foundation for #8. Based directly on `freely/upstream-v32.1`. Contains shared `.github/workflows/ci.yml` and CI image changes. |
| #8 | `freely/core-chain-implementation` | Correctly based on #1's current head. Current comparison: 12 commits ahead, 0 behind. Must follow #1 in integration order. |
| #11 | `freely/wallet-node-readiness` | Targets the current #8 head `5f8fa282ea0675c41c2a5aa21db36d5e1bf47744`. Current comparison: PR #11 head `24800203855264f0b490ec80a602389754a0be81` is 5 commits ahead and 0 behind. Its two changed files (wallet readiness workflow and this document) do not overlap with PR #8. Recheck this relationship if #8 advances and rerun wallet CI on the resulting head. |
| #2 | `freely/consensus-specification` | Independent of code integration, but shares consensus/network specification documents and verifier script with #7. Reconcile duplicate edits before either is merged. |
| #7 | `freely/network-architecture` | Overlaps #2 on `FREELY-CONSENSUS-SPECIFICATION.md`, `FREELY-NETWORK-ARCHITECTURE.md`, `FREELY-NETWORK-PARAMETERS-DRAFT.md`, and `verify-freely-consensus-spec.py`; also overlaps #3 on `FREELY-CHAIN-SELECTION-AUDIT.md`. Resolve by selecting a canonical source or rebasing/retargeting; do not merge both blindly. |
| #3 | `freely/chain-selection-audit` | Documentation overlap with #7 on `FREELY-CHAIN-SELECTION-AUDIT.md`; reconcile content. |
| #9 | `freely/ci-windows-safe` | Overlaps #1 on `.github/workflows/ci.yml` and `ci/test/00_setup_env_native_nowallet.sh`. Consolidate the Windows-safe checkout and push-trigger changes into one reviewed CI change; avoid duplicate competing merges. |
| #6 | `freely/retarget-test-vectors` | Adds `src/test/pow_tests.cpp` and focused retarget/BIP94 coverage; currently separate from #1/#8. Validate against the same v32.1 base and integrate after reviewing consensus semantics. |
| #10 | `freely/network-safety-preflight` | Separate tooling/docs workstream; no changed-file overlap with #1/#8/#11. Its production manifest intentionally remains unset and fail-closed. |
| #4/#5 | PoW audit / retarget policy | Documentation-only workstreams; use them as review inputs for #6 and the eventual consensus implementation, not as independently activated production settings. |

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
