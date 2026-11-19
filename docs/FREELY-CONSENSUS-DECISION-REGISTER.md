# FREELY consensus decision register

**Date:** 17 November 2026  
**Status:** All four protocol parameter areas were explicitly approved by the owner on 18 November 2026. The genesis nonce, final transaction/Merkle commitment and block hash remain derived and uncomputed; implementation, compatibility tests, security review and activation gates remain incomplete.  
**Related:** [Consensus specification](FREELY-CONSENSUS-SPECIFICATION.md) · [Chain-selection audit](FREELY-CHAIN-SELECTION-AUDIT.md)

This register separates agreed policy from recommendations and unresolved decisions. No value in the recommendation column is activated by this document.

## A. Monetary policy and genesis accounting

| Decision | Current agreement / recommendation | Status |
|---|---|---|
| Ticker and decimals | FLY; 8 decimals | Agreed |
| Initial subsidy | 50 FLY | Agreed |
| Halving | Every 210,000 blocks; integer right shift | Agreed |
| Hard ceiling | 21,000,000 FLY | Agreed |
| Scheduled issuance | 20,999,999.9769 FLY including height-zero schedule | Agreed arithmetic |
| Genesis coinbase | Permanently unspendable; included in scheduled issuance accounting | **Owner-approved 17 Nov 2026** |
| Spendable supply statement | Scheduled issuance: 20,999,999.9769 FLY; maximum spendable scheduled subsidy: 20,999,949.9769 FLY | **Owner-approved accounting convention 17 Nov 2026** |
| Fees | Preserve upstream fee accounting and coinbase limit = subsidy + fees | Recommended |

Rationale: the conventional genesis output is not inserted into the spendable UTXO set. Making it spendable would require a deliberate consensus deviation and could undermine the no-premine statement unless carefully disclosed.

## B. Proof of work and difficulty

| Parameter | Recommendation | Reason / condition |
|---|---|---|
| Hash | SHA-256d | Agreed |
| Target spacing | 600 seconds | Agreed |
| Retarget interval | 2,016 blocks | Agreed |
| Target timespan | 1,209,600 seconds (14 days) | Derived from agreed spacing and interval |
| Retarget algorithm | Reuse pinned upstream v32.1 `GetNextWorkRequired` / `CalculateNextWorkRequired` semantics | **Owner-approved 16 Nov 2026** |
| Retarget clamp | Clamp elapsed timespan to ¼×–4× target timespan (302,400–4,838,400 seconds) | **Owner-approved 16 Nov 2026** |
| Minimum-difficulty blocks | Disabled on production FREELY | **Owner-approved 16 Nov 2026** |
| No-retargeting | Disabled on production FREELY | **Owner-approved 16 Nov 2026** |
| BIP94 time-warp mitigation | Enable from genesis (`enforce_BIP94 = true`): first-period target base plus first-block timestamp bound (previous block time − 600 seconds) | **Owner-approved 17 Nov 2026; both code paths and dedicated tests required before activation** |
| PoW limit | Do not select a numeric target until initial mining model and attack assumptions are reviewed | This is a consensus-critical ceiling and genesis target constraint |
| Genesis nBits | Must encode a target no easier than the approved PoW limit | Cannot be chosen independently |
| Timestamp validity | Preserve upstream median-time-past and future-time checks; document any additional rules | Avoid needless divergence |

Important security limitation: a 600-second target does not guarantee a 600-second block interval. Actual timing depends on total honest hash rate and difficulty. A low-hashrate public chain is exposed to rented or redirected SHA-256 hash power, majority attacks and reorganizations. A high initial difficulty can stall; an easy one does not create security.

## C. Script rules and soft-fork activation

**Owner-approved policy (17 Nov 2026):** established Bitcoin script and consensus features should be active from the start of FREELY, subject to a per-feature Bitcoin Core v32.1 compatibility audit and tests. Future consensus upgrades must use a controlled, documented activation process. This policy does not authorize copying Bitcoin mainnet historical heights, hashes, exception blocks, BIP9 timestamps or warning heights.

| Feature / rule | FREELY candidate treatment | Compatibility gate |
|---|---|---|
| P2SH (BIP16) | Enforce from genesis | Verify script-flag path; no Bitcoin historical exception copied |
| BIP34 coinbase height | Enforce from first post-genesis block (height 1); genesis is constructed/validated by its dedicated path | Verify genesis special handling and BIP34 hash semantics |
| CLTV (BIP65) | Enforce from first post-genesis block | Boundary and invalid-script tests |
| Strict DER signatures (BIP66) | Enforce from first post-genesis block | Signature-encoding tests |
| CSV / relative locktime (BIP68/112/113) | Enforce from first post-genesis block | Sequence-lock and MTP tests |
| SegWit witness script rules (BIP141/143) | Unconditional from genesis in v32.1; SegwitHeight=1 for block witness commitments and BIP147 NULLDUMMY | Verify script flags, witness commitment and data-handling boundaries |
| Taproot / Tapscript (BIP341/342) | Unconditional from genesis in v32.1 script flags | Verify key-path and script-path vectors; no historical exceptions copied |
| Version-bits deployments | No historical Bitcoin deployment schedule copied; future changes controlled individually | Each future deployment needs bit, period, threshold, start/timeout, min height and tests |
| Historical script exceptions | None copied from Bitcoin mainnet | Any exception requires a FREELY-specific justification and explicit review |

The table is an implementation proposal under the approved policy, not proof that these rules are already active in FREELY. Exact parameter values and special cases must be confirmed against the pinned source before implementation. Height 0 remains the dedicated genesis block; the first ordinary block is height 1.

## D. Chain history shortcuts and bootstrapping

| Field | Recommendation for initial FREELY |
|---|---|
| Checkpoints | None |
| Minimum chainwork | Zero / unset until a real FREELY history exists |
| Assume-valid | Null / genesis-only equivalent; do not copy Bitcoin hash |
| AssumeUTXO snapshots | None until independently generated and validated from FREELY history |
| DNS seeds | None for private development; add only with independent operator agreement |
| Fixed seeds | None for private development |
| Chain transaction statistics | Empty / neutral until valid chain history exists |
| Header-sync commitments | Do not copy Bitcoin history-specific values |

These are not merely performance settings. Chainwork, assume-valid, checkpoints and AssumeUTXO data are security-sensitive and must correspond to actual FREELY blocks.

## E. Network identity

The provisional candidates in the network parameter draft must be checked as a set before activation:
- chain selector and config section;
- data directory suffix;
- P2P magic bytes;
- P2P, RPC and Tor ports;
- Base58 P2PKH, P2SH and WIF prefixes;
- extended public/private key versions;
- Bech32/Bech32m HRP.

**Recommendation:** use no public seeds and no public peer discovery during private development. Use explicitly configured local peers and separate data directories. Before any public testnet, collision-check every identity value and publish the frozen sheet.

## F. Protocol behaviour to preserve unless a change is justified

The default implementation strategy should preserve Bitcoin Core v32.1's established transaction, script, serialization, block weight, sigops, mempool policy, P2P protocol and wallet architecture. A new native coin does not require rewriting those systems.

Every proposed deviation must include:
1. exact behaviour change;
2. consensus or policy classification;
3. attack/compatibility rationale;
4. unit and functional tests;
5. independent review.

## G. Decisions still requiring owner approval

1. Approve a numeric production `powLimit` and initial difficulty only after the candidate model, expected honest hash rate, attacker-cost assumptions and chain-stall risks are reviewed.
2. Approve final network identity values after candidate collision checks; candidate generation and validation are authorised, not final activation.
3. Approve the exact genesis timestamp/message and output-script construction after all dependent fields are fixed.
4. Approve the final per-feature activation parameters after the v32.1 compatibility audit and test evidence are reviewed.

Resolved by owner on 17 Nov 2026: genesis reward is permanently unspendable and included in scheduled issuance accounting; BIP94 is to be enabled from genesis subject to testing; established Bitcoin script features are to be active from the start subject to compatibility verification; candidate network identity and genesis commitment generation/verification are authorised. No production activation or public launch is authorised.


## H. Owner decision record — 16 November 2026

The owner explicitly approved the FREELY production retarget policy proposed in [FREELY-RETARGET-POLICY-PROPOSAL.md](../freely/retarget-policy/docs/FREELY-RETARGET-POLICY-PROPOSAL.md) / PR #5:

- 600-second target spacing; 2,016-block interval; 1,209,600-second target timespan.
- Clamp actual elapsed timespan to ¼×–4× the target timespan.
- Production minimum-difficulty exception disabled.
- Production no-retargeting mode disabled.
- Reuse pinned Bitcoin Core v32.1 retarget calculation semantics, implemented and tested with FREELY-specific parameters.

This is a consensus-policy approval, not activation in runtime code. All four parameter proposal areas, including numeric PoW values, network identity and the initial script matrix, were owner-approved on 18 November 2026. The derived genesis nonce/hash and C++/functional verification remain outstanding. No public testnet or mainnet is authorised.


## I. Owner decision record — 17 November 2026

The owner explicitly approved the following bounded decisions and authorisations:

- Genesis coinbase reward: permanently unspendable; the 50 FLY height-zero subsidy remains included in scheduled issuance accounting. Scheduled issuance is 20,999,999.9769 FLY; maximum spendable scheduled subsidy under this convention is 20,999,949.9769 FLY.
- Proof of work: benchmark candidate `powLimit` / initial difficulty scenarios and present a recommendation. No numeric production value is approved yet.
- Time-warp mitigation: enable BIP94 from genesis (`enforce_BIP94 = true`), subject to source audit and dedicated tests.
- Script rules: established Bitcoin script features are intended to be active from the start, subject to pinned-v32.1 compatibility verification; future soft forks require controlled activation.
- Network identity: generate and collision-check candidate identity values and generate/independently verify a candidate genesis commitment. Final production values and activation are not approved.

These approvals authorise reversible documentation, candidate modelling, code review, tests and non-production tooling only. They do not authorise production parameter activation, public network exposure, mining deployment, paid services or launch.


## J. Pinned-v32.1 script compatibility audit — 17 November 2026

Targeted source inspection of `src/validation.cpp` confirms P2SH, witness and Taproot script flags are unconditional in `GetBlockScriptFlags`, except for explicit historical hash exceptions. FREELY must not copy Bitcoin mainnet exceptions. BIP66/DERSIG, BIP65/CLTV and CSV are controlled by buried-deployment heights; BIP147 NULLDUMMY is controlled by SegwitHeight; BIP34 coinbase-height enforcement is controlled separately. The current candidate is height 1 for these height-controlled rules, with BIP30 duplicate-coinbase protection retained and no historical BIP34 hash copied. Witness data download/validation paths also use SegwitHeight and require boundary tests. These are source-audited candidates, not yet compiled or validated in a FREELY parameter object.


## K. BIP94 complete-rule clarification — 17 November 2026

The BIP94 approval covers both the period-start retarget base and the time-warp timestamp bound. At candidate heights divisible by 2,016 (excluding genesis), the block timestamp must be at least the previous block timestamp minus 600 seconds and must still exceed median-time-past. PR #6 now adds (1) a C++ test for first-block-of-period target selection at a 2,016-block interval and (2) a regtest functional test at the test chain's 144-block interval that rejects a 601-second backward timestamp and accepts the exact 600-second boundary. CI and full FREELY runtime validation remain pending.


## L. Exact protocol parameter proposals — 18 November 2026

A consolidated exact-value proposal has been prepared in [FREELY-PROTOCOL-PARAMETER-APPROVAL.md](FREELY-PROTOCOL-PARAMETER-APPROVAL.md). It proposes (1) the Bitcoin difficulty-1 `powLimit` and matching genesis `nBits`, (2) a unique FREELY network identity, (3) a timestamped genesis coinbase/manifest commitment candidate, and (4) a height-1 script activation matrix compatible with Bitcoin Core v32.1.

**Status: proposed only; no owner approval recorded.** No proposed value has been copied into FREELY production runtime parameters. The genesis nonce and final header hash remain outputs of a deterministic PoW search and are not fabricated. The owner must approve or amend the four proposals; approval still does not itself authorise launch or public network exposure.


## L. Consolidated owner approval — 18 November 2026

This section supersedes earlier statements in this register that numeric production PoW parameters, final network identity, genesis candidate fields or the initial script activation matrix remained unapproved. The exact authoritative baseline is [FREELY-APPROVED-PROTOCOL-PARAMETERS.md](FREELY-APPROVED-PROTOCOL-PARAMETERS.md).

### Approved PoW and retarget parameters

- SHA-256d; `powLimit=00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff`.
- Genesis `nBits=0x1d00ffff`; its decoded target is slightly smaller/harder than `powLimit`, not equal to it.
- 600-second target spacing; 2,016-block interval; 1,209,600-second timespan.
- Clamp 302,400–4,838,400 seconds; minimum-difficulty exception disabled; no-retargeting disabled; BIP94 enabled from genesis.

### Approved network identity

- Message magic `fa c3 b7 d1`; P2P 49444; RPC 49445; data-directory/config suffix `freely`.
- P2PKH 55; P2SH 117; WIF 183.
- Extended public/private key versions `04464c59` / `04666c79`; Bech32 HRP `fly`.

### Approved genesis candidate

- Version 1; timestamp 1,794,960,000 (2026-11-18 00:00:00 UTC); previous hash all zeroes.
- Coinbase message `FREELY FLY genesis 2026-11-18`; 50 FLY output to `6a12465245454c5920464c592047454e45534953`.
- Genesis coinbase permanently unspendable; no premine or founder allocation.
- Nonce, transaction ID, Merkle root and final block hash are derived outputs. They must be generated by the pinned Core serialization/hash implementation, independently reproduced and checked against proof of work before they can be frozen.

### Approved initial script/deployment policy

- BIP34, BIP65, BIP66, CSV and SegWit height-controlled rules: height 1.
- Taproot/witness-v1 behavior: verify against the v32.1 script-flag architecture; no separate buried-height field exists in `Consensus::Params`.
- TESTDUMMY: bit 28, NEVER_ACTIVE, NO_TIMEOUT, minimum activation height 0, threshold 1,815/2,016, period 2,016.
- No Bitcoin-mainnet historical activation hashes, checkpoints or script exceptions are copied.

These approvals authorize reversible implementation, deterministic candidate generation, tests and independent review. They do not authorize genesis activation in a released node, mining deployment, public RPC/P2P exposure, DNS seeds, public testnet/mainnet, paid infrastructure or launch. Startup remains fail-closed until implementation and evidence gates pass.
