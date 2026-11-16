# FREELY consensus decision register

**Date:** 16 November 2026  
**Status:** Recommendations for review only — not approved parameters.  
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
| Genesis coinbase | **Recommend conventional unspendable genesis output**, matching Bitcoin's no-premine convention | Owner confirmation required |
| Spendable supply statement | If genesis reward is unspendable, state maximum scheduled subsidy spendable as 20,999,949.9769 FLY; do not advertise scheduled total as spendable | Conditional on genesis choice |
| Fees | Preserve upstream fee accounting and coinbase limit = subsidy + fees | Recommended |

Rationale: the conventional genesis output is not inserted into the spendable UTXO set. Making it spendable would require a deliberate consensus deviation and could undermine the no-premine statement unless carefully disclosed.

## B. Proof of work and difficulty

| Parameter | Recommendation | Reason / condition |
|---|---|---|
| Hash | SHA-256d | Agreed |
| Target spacing | 600 seconds | Agreed |
| Retarget interval | 2,016 blocks | Agreed |
| Target timespan | 1,209,600 seconds (14 days) | Derived from agreed spacing and interval |
| Retarget algorithm | Reuse the pinned upstream v32.1 algorithm and integer semantics; document exact boundary/clamp behaviour | Avoid an unnecessary bespoke algorithm |
| Minimum-difficulty blocks | **Recommend disabled on production FREELY** | Prevents opportunistic difficulty drops; may mean slow blocks at low hashrate |
| No-retargeting | **Recommend disabled on production FREELY** | Production difficulty must adapt |
| BIP94 time-warp mitigation | **Recommend enabling after code-path review and dedicated tests** | Adds timestamp protection at retarget boundaries; confirm exact semantics in v32.1 |
| PoW limit | Do not select a numeric target until initial mining model and attack assumptions are reviewed | This is a consensus-critical ceiling and genesis target constraint |
| Genesis nBits | Must encode a target no easier than the approved PoW limit | Cannot be chosen independently |
| Timestamp validity | Preserve upstream median-time-past and future-time checks; document any additional rules | Avoid needless divergence |

Important security limitation: a 600-second target does not guarantee a 600-second block interval. Actual timing depends on total honest hash rate and difficulty. A low-hashrate public chain is exposed to rented or redirected SHA-256 hash power, majority attacks and reorganizations. A high initial difficulty can stall; an easy one does not create security.

## C. Script rules and soft-fork activation

**Recommendation:** create a chain-specific activation matrix before writing FREELY parameters. Do not copy Bitcoin mainnet activation heights, hashes, exception blocks, BIP9 timestamps or warning heights.

The review should decide for each supported rule:
- active from genesis, activated later, or deliberately unsupported;
- exact consensus flag and height/time semantics;
- any deployment bit, threshold, period, start, timeout and minimum activation height;
- test vectors for blocks immediately before and after activation.

A new chain has no inherited Bitcoin history to justify historical activation heights. Whether modern script rules are active from genesis must be an explicit, independently reviewed decision.

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

1. Confirm unspendable genesis coinbase and corresponding spendable-supply wording.
2. Review and approve a production PoW limit / initial difficulty based on the security and mining model.
3. Approve minimum-difficulty disabled and no-retargeting disabled for production.
4. Review and approve BIP94/time-warp mitigation semantics.
5. Approve the chain-specific script activation matrix.
6. Approve final network identity values after collision checks.
7. Approve genesis timestamp/message and output script after all dependent fields are fixed.

No consensus or network identity parameter is final until the complete sheet is internally consistent, independently reviewed and approved. No public testnet or mainnet launch is authorised.
