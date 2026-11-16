# FREELY consensus specification — engineering baseline

**Status:** working specification; retarget/minimum-difficulty policy owner-approved on 16 November 2026; not activation-ready.  
**Date:** 16 November 2026  
**Source baseline:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`.  
**Branch:** `freely/consensus-specification`  
**Purpose:** turn agreed monetary and block-production rules into an auditable implementation contract, while explicitly isolating unresolved consensus choices. This document does not activate a chain, choose a genesis block, or authorise a public network.

## 1. Consensus rules already agreed

| Rule | Agreed value |
|---|---:|
| Chain | Independent FREELY UTXO chain |
| Native unit | FLY |
| Base units | 100,000,000 per FLY |
| Initial block subsidy | 5,000,000,000 base units (50 FLY) |
| Subsidy halving interval | 210,000 blocks |
| Scheduled subsidy formula | Integer right shift |
| Hard money ceiling | 2,100,000,000,000,000 base units (21,000,000 FLY) |
| Block target spacing | 600 seconds |
| Difficulty adjustment interval | 2,016 blocks |
| Proof-of-work hash | SHA-256d |
| Premine / founder allocation / ICO | None |

All consensus monetary values MUST use integer base units. Floating-point values MUST NOT be used in consensus calculations, serialization, validation or tests.

## 2. Exact subsidy rule

For block height h >= 0:

`halvings = floor(h / 210000)`

`subsidy_base_units(h) = 5000000000 >> halvings`

If `halvings >= 64`, the subsidy is zero. This follows the existing Bitcoin Core integer-shift guard and avoids undefined or implementation-dependent shifts.

Expected boundary vectors:

| Height | Subsidy |
|---:|---:|
| 0 | 50 FLY |
| 209,999 | 50 FLY |
| 210,000 | 25 FLY |
| 419,999 | 25 FLY |
| 420,000 | 12.5 FLY |
| 630,000 | 6.25 FLY |
| 1,260,000 | 0.78125 FLY |
| 6,720,000 | 0.00000001 FLY |
| 6,929,999 | 0.00000001 FLY |
| 6,930,000 | 0 FLY |

The sum of the scheduled subsidy values over all heights, including height zero, is 2,099,999,997,690,000 base units (20,999,999.9769 FLY). This is below the 21,000,000 FLY hard ceiling.

### Genesis accounting — unresolved and important

A conventional Bitcoin-style genesis coinbase is unspendable. If FREELY follows that convention, the height-zero 50 FLY subsidy is part of the mathematical schedule but is not spendable by anyone. The maximum spendable subsidy issuance would then be 2,099,994,997,690,000 base units (20,999,949.9769 FLY), before considering fees and any consensus-specific issuance treatment.

This distinction MUST be resolved explicitly before genesis implementation. The project must not describe the full 20,999,999.9769 FLY schedule as spendable supply if the genesis output is unspendable. No genesis reward or output is assigned by this document.

## 3. Block reward and money range

For each non-genesis block, the total value of coinbase outputs MUST NOT exceed:

`subsidy_base_units(height) + fees_in_base_units`

Existing Bitcoin Core validation logic is the starting point and should be preserved unless a specific FREELY requirement is approved and tested.

The hard ceiling remains 21,000,000 FLY. Before implementation, audit every use of `MAX_MONEY`, `MoneyRange`, coinbase reward checks, wallet amount formatting, RPC amount conversion, fee accounting, and any supply reporting. A change to the ticker alone is not a consensus implementation.

Required invariants:
- Every amount is representable in the existing signed 64-bit `CAmount` type.
- No transaction output, aggregate input/output, fee, subsidy or coinbase total may overflow.
- Reject negative or out-of-range monetary values through the established validation paths.
- Tests compare integer base units, not floating-point FLY strings.

## 4. Proof of work and difficulty

### Owner-approved production retarget policy (16 November 2026)

The project owner has approved the following production policy, based on the dedicated proposal in [FREELY-RETARGET-POLICY-PROPOSAL.md](FREELY-RETARGET-POLICY-PROPOSAL.md):

- SHA-256d proof of work; 600-second target spacing.
- Retarget interval: 2,016 blocks; target timespan: 1,209,600 seconds (14 days).
- Clamp elapsed retarget time to one quarter through four times the target timespan (302,400 to 4,838,400 seconds).
- Disable minimum-difficulty blocks on production FREELY.
- Disable no-retargeting mode on production FREELY.
- Reuse Bitcoin Core v32.1 `GetNextWorkRequired` / `CalculateNextWorkRequired` semantics, including upstream integer arithmetic and compact-target handling, subject to FREELY-specific parameters and tests.
- At non-boundary heights, retain the previous block's `nBits`. At a retarget boundary, use the upstream v32.1 period timestamp selection and clamp/scale procedure. The exact code path and vectors must be confirmed by implementation tests before activation.

This approval resolves the production retarget/clamp/minimum-difficulty/no-retargeting policy only. It does not approve BIP94/time-warp mitigation, a numeric `powLimit`, genesis `nBits`, genesis fields, or any network identity value.

### Still unresolved — consensus-critical

1. Exact `powLimit` and corresponding compact target.
2. Genesis `nBits` (must be compatible with the approved `powLimit`).
3. Whether to adopt BIP94 time-warp mitigation, and its exact activation semantics.
4. Timestamp validity constraints and median-time-past behaviour; preserve upstream rules unless a deliberate change is specified.
5. Compact target decoding, overflow and negative-target rejection vectors must be fixed in the implementation test contract.

Do not copy Bitcoin mainnet's proof-of-work limit or special difficulty flags by default. Do not invent these values merely to make a node compile.

## 5. Script and soft-fork activation policy

The initial FREELY activation state for every buried deployment and version-bits deployment is not yet decided.

Before a production parameter object is implemented, create a deployment matrix containing:
- deployment name and BIP / specification;
- whether the rule is active from genesis or activated later;
- start time, timeout, signalling bit, threshold, period and minimum activation height where applicable;
- buried deployment heights and associated hashes where applicable;
- test coverage for activation boundaries and invalid blocks.

Never copy Bitcoin mainnet activation heights, deployment timestamps, checkpoints or activation hashes without a chain-specific justification and explicit approval. The regtest-only `-test` override must remain regtest-only. Test activation overrides must be rejected on every production chain, not just Bitcoin MAIN.

## 6. Chain identity and genesis

All of the following remain provisional or unresolved and MUST NOT be activated from the candidate draft without review:
- chain selector and config-section name;
- P2P message-start bytes;
- P2P and RPC ports;
- Base58 public-key, script and private-key prefixes;
- extended public/private key versions;
- Bech32/Bech32m HRP;
- genesis timestamp/message, transaction, output script, version, time, `nBits`, nonce, Merkle root and block hash;
- proof-of-work limit and all activation assumptions;
- DNS and fixed seeds;
- checkpoints, minimum chainwork, assume-valid and AssumeUTXO metadata.

Genesis construction procedure:
1. Approve the exact timestamp/message and genesis output treatment.
2. Freeze all genesis header fields and the PoW limit.
3. Generate the block with Bitcoin Core's serialization and hashing code.
4. Independently recompute the transaction ID, Merkle root, header hash and proof-of-work validity.
5. Commit reproducible generation instructions and test vectors.
6. Only then hard-code the verified values and assert them in tests.

No guessed nonce, hash, Merkle root, address prefix or network magic is acceptable.

## 7. Test contract

### Monetary tests
- Check all subsidy vectors in section 2.
- Check the exact cumulative scheduled issuance in integer base units.
- Separately test the spendable issuance accounting chosen for genesis.
- Test height boundaries immediately before, at and after every halving.
- Test zero subsidy after height 6,930,000.
- Test coinbase reward plus fees, overpayment rejection, negative values and overflow/range cases.

### Proof-of-work tests
- Valid and invalid targets at and around `powLimit`.
- Compact target decoding edge cases.
- Retarget at the first applicable boundary and several later boundaries.
- Clamp lower and upper bounds.
- Timestamp edge cases and median-time-past.
- Minimum-difficulty and no-retargeting policy, once selected.
- Regression vectors generated independently.

### Network and regression tests
- Chain selector parsing and string round-trip.
- Unique data directory and RPC port.
- P2P magic mapping and isolation.
- Base58, extended-key and Bech32/Bech32m encoding/decoding.
- Exact genesis hash, Merkle root and proof of work.
- Existing Bitcoin mainnet, testnet, testnet4, signet and regtest behaviour unchanged.
- Production chain rejects test-only startup overrides.
- Private multi-node development network remains isolated from Bitcoin peers.

## 8. Decisions required before implementation can proceed safely

| Decision | Current state | Why it matters |
|---|---|---|
| Genesis coinbase / height-zero issuance accounting | Open | Determines spendable issuance and supply description |
| PoW limit and genesis target | Open | Defines valid block difficulty from genesis |
| Retarget algorithm / clamp / production flags | **Owner-approved policy; implementation and tests pending** | Consensus compatibility; different rules split the chain |
| Minimum difficulty policy | **Owner-approved: disabled on production FREELY** | Changes block validity |
| No-retargeting mode | **Owner-approved: disabled on production FREELY** | Changes block validity |
| Time-warp mitigation | Open | Changes block validity and security |
| Buried deployments / script rules | Open | Defines valid transaction and block rules |
| Version-bits schedule | Open | Defines future consensus transitions |
| Network identity candidates | Provisional | Prevents accidental peer/address collisions |
| Genesis timestamp/message and output | Open | Defines unique genesis commitment |

These choices should be reviewed together as a single consensus parameter sheet. They are not safely delegated to defaults or copied from Bitcoin mainnet.

## 9. Implementation sequence

1. Keep the currently monitored M1 PR unchanged until its CI runs reach terminal states.
2. Review this specification and resolve the open decisions.
3. Implement a separate, narrowly scoped chain-type and base-parameter patch only when its identity and production/test classification are safe.
4. Implement FREELY consensus parameters, genesis and tests in a separate patch.
5. Run targeted validation tests, the full upstream test suite, platform CI and sanitizers.
6. Run only a private, isolated development network after the genesis and network parameters are frozen.
7. Obtain independent consensus/security review before any public testnet or mainnet proposal.

## 10. Security and release boundary

A SHA-256d fork does not inherit Bitcoin's hash rate or security. A low-hashrate independent chain may be vulnerable to majority-hash attacks, reorganization, double-spending and censorship.

This specification authorises no public testnet, mainnet, mining deployment, wallet distribution, exchange listing, token sale or paid infrastructure. Those require separate explicit approval. No PR is merged by this document.

## 11. Source references

- Bitcoin Core v32.1 pinned commit: `f0de87f040621468b956f01f526a43a010310501`.
- `src/validation.cpp`: subsidy calculation and coinbase reward validation.
- `src/consensus/params.h`: proof-of-work and deployment parameter fields.
- `src/consensus/amount.h`: `CAmount`, `COIN`, `MAX_MONEY`.
- `src/kernel/chainparams.cpp`: network parameters and genesis construction.
- `src/init.cpp`: startup option restrictions and activation overrides.
- FREELY architecture plan: `docs/FREELY-NETWORK-ARCHITECTURE.md`.
- Provisional network parameter sheet: `docs/FREELY-NETWORK-PARAMETERS-DRAFT.md`.


## Decision register

See [FREELY consensus decision register](FREELY-CONSENSUS-DECISION-REGISTER.md) for recommended defaults and unresolved owner decisions. All recommendations remain provisional until explicitly reviewed and approved.

## 12. Specification completeness and implementation acceptance — 16 November 2026

### 12.1 Completion statement

The FREELY consensus specification package is complete as an **implementation contract and decision-controlled draft**. Every consensus domain required before implementation is identified, its known rules are stated, its unresolved choices are explicitly registered, and the required tests and activation gates are defined.

**Specification coverage: 100% (document deliverable). Consensus freeze: not complete.** A complete specification can identify a blocked owner decision without inventing a value. It is not safe to claim the production consensus is frozen while those decisions remain open.

### 12.2 Authoritative parameter status

| Domain | Defined rule / value | Status |
|---|---|---|
| Native asset | FLY, 8 decimals, integer base units | Approved |
| Monetary ceiling | 21,000,000 FLY | Approved |
| Initial subsidy | 50 FLY | Approved |
| Halving | Every 210,000 blocks; integer right shift | Approved |
| Scheduled issuance | 20,999,999.9769 FLY | Arithmetic verified |
| Genesis spendability | Conventional unspendable genesis recommended | Owner confirmation pending |
| PoW hash | SHA-256d | Approved |
| Target spacing | 600 seconds | Approved |
| Retarget interval | 2,016 blocks | Approved |
| Retarget timespan | 1,209,600 seconds | Derived |
| Retarget clamp | 302,400–4,838,400 seconds | Owner-approved |
| Minimum difficulty | Disabled in production | Owner-approved |
| No-retargeting | Disabled in production | Owner-approved |
| Retarget algorithm | Pinned v32.1 integer/compact-target semantics | Owner-approved |
| Numeric powLimit | Not selected | Owner decision pending |
| Genesis nBits and genesis commitment | Not selected | Depends on powLimit/genesis decisions |
| BIP94/time-warp mitigation | Not selected | Owner decision pending |
| Timestamp/MTP | Preserve v32.1 unless a reviewed change is approved | Baseline rule |
| Script/soft-fork activation matrix | Required matrix and test format defined; individual activation states open | Owner decision pending |
| Chain/network identity | Fields and collision requirements enumerated | Owner decision pending |
| Chain-history shortcuts | No Bitcoin history-specific assumptions copied | Approved safety rule |

### 12.3 Exact monetary boundary correction

The subsidy vectors include both sides of the final one-base-unit era:
- Height 6,719,999: 2 base units.
- Height 6,720,000: 1 base unit.
- Height 6,929,999: 1 base unit.
- Height 6,930,000: 0 base units.

All tests and cumulative issuance calculations MUST use integer base units. The total scheduled issuance remains 2,099,999,997,690,000 base units. The spendable issuance total is conditional on the genesis output convention and must not be conflated with the schedule.

### 12.4 Retarget test contract cross-reference

The approved policy is covered by the dedicated deterministic vector contract in FREELY-RETARGET-TEST-VECTORS.md. That document specifies exact lower/upper clamp and normal-period compact-target expectations, one-second boundary cases, first retarget at candidate height 2,016 using timestamps at heights 0 and 2,015, non-boundary carry-forward, compact target negative/zero/overflow/above-limit rejection, and separate BIP94 vectors pending a decision.

The synthetic test powLimit and nBits are fixtures only, never FREELY production values.

### 12.5 Script and deployment matrix template

Before a FREELY parameter object is frozen, the implementation decision sheet must contain one row for every upstream buried deployment and version-bits deployment considered for FREELY:

| Required field | Required content |
|---|---|
| Rule identifier | BIP / deployment name and upstream source |
| Rule class | Buried deployment, version-bits deployment, policy-only, or unsupported |
| Initial state | Active from genesis, scheduled activation, or deliberately unsupported |
| Activation parameters | Exact height or start/timeout/bit/threshold/period/minimum height as applicable |
| Historical dependencies | Required block hash, exception, chain history, or none |
| Compatibility impact | Blocks/transactions accepted or rejected differently |
| Tests | Before/at/after activation and invalid-block cases |
| Approval | Owner decision and independent review reference |

No Bitcoin MAIN activation height, hash, exception or deployment timestamp is presumed valid for FREELY. The matrix is a required deliverable; its individual consensus values remain open until reviewed.

### 12.6 Final pre-implementation gates

- [x] Monetary rule and exact integer issuance formula documented.
- [x] Subsidy boundary and cumulative issuance vectors documented.
- [x] Production retarget policy owner-approved and specified.
- [x] PoW validation interfaces and invalid-target cases specified.
- [x] Genesis and network identity dependencies enumerated.
- [x] Script/deployment matrix structure defined.
- [x] Regression, integration, private-network and independent-review gates defined.
- [x] Public launch, mining deployment and paid infrastructure explicitly excluded absent separate approval.
- [ ] Owner confirms genesis coinbase spendability convention.
- [ ] Owner approves numeric powLimit and initial difficulty model after security review.
- [ ] Owner decides BIP94/time-warp mitigation.
- [ ] Owner approves the script/deployment activation matrix.
- [ ] Owner approves final identity and genesis commitment after collision/reproducibility checks.

**Release rule:** do not enable production FREELY chain parameters, generate a production genesis commitment, or expose a public network while any consensus-critical gate above remains unresolved. Completing this specification document does not waive those gates.
