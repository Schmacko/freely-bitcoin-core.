# FREELY network parameters — provisional engineering draft

**Status:** candidate-generation and validation authorised 17 November 2026; values remain provisional, not activated in code and not approved as final network identity.  
**Date:** 15 November 2026  
**Upstream baseline:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`  
**Purpose:** provide a concrete, reviewable starting point for the dedicated FREELY chain implementation while keeping launch-sensitive values visibly provisional.

> **Revision note — 18 November 2026:** This document preserves the earlier provisional candidates for historical traceability. The current exact-value proposal is [FREELY Protocol Parameter Approval Package](FREELY-PROTOCOL-PARAMETER-APPROVAL.md). Where values differ, that approval package supersedes the candidate tables below. Neither document activates production parameters; explicit owner approval and implementation validation remain mandatory.

## 1. Fixed project decisions

These values were already agreed for the project and are not provisional:

| Parameter | Value |
|---|---:|
| Chain name | FREELY |
| Native ticker | FLY |
| Consensus model | UTXO |
| Proof of work | SHA-256d |
| Initial block subsidy | 50 FLY |
| Base units | 100,000,000 per FLY |
| Halving interval | 210,000 blocks |
| Hard money ceiling | 21,000,000 FLY |
| Scheduled total issuance | 20,999,999.9769 FLY |
| Target block spacing | 600 seconds |
| Retarget interval | 2,016 blocks |
| Premine / founder allocation | None |
| ICO / initial token sale | None |

## 2. Candidate network identity

The following are engineering candidates, not final values. They must be checked against other chains and tested for correct address/network isolation before any public release.

| Field | Candidate | Reason / validation required |
|---|---|---|
| Chain selector | `-chain=freely` | Clear, unique canonical name |
| Data-directory suffix | `freely` | Separate node data from Bitcoin and other FREELY profiles |
| P2P magic bytes | `46 4c 59 31` (ASCII `FLY1`) | Easy to identify; still needs collision review |
| P2P port | `19444` | Candidate non-default port; check host/firewall conflicts |
| RPC port | `19443` | Separate local RPC endpoint; never expose unauthenticated RPC publicly |
| P2PKH prefix | `35` decimal | Candidate Base58Check version byte; verify resulting address format |
| P2SH prefix | `50` decimal | Candidate Base58Check version byte; verify distinctness |
| WIF prefix | `186` decimal | Candidate private-key export prefix; verify wallet interoperability |
| BIP32 public version | `0x04464c59` | Candidate extended public-key version; test serialization and display |
| BIP32 private version | `0x04464c5a` | Candidate extended private-key version; test serialization and display |
| Bech32 / Bech32m HRP | `fly` | Human-readable address prefix candidate |
| DNS seeds | Empty initially | Do not publish placeholder or third-party endpoints |
| Fixed seeds | Empty initially | Add only after infrastructure exists and is reviewed |

Do not distribute addresses, private keys, wallet backups or software using these candidate prefixes until the values have been finalized and end-to-end tested.

## 3. Consensus parameters — agreed versus unresolved

| Parameter | Proposed value | Status |
|---|---:|---|
| Subsidy | 50 FLY | Agreed |
| Halving interval | 210,000 blocks | Agreed |
| Target spacing | 600 seconds | Agreed |
| Target timespan | 1,209,600 seconds (14 days) | Derived from agreed spacing × interval |
| Retarget interval | 2,016 blocks | Agreed |
| PoW algorithm | SHA-256d | Agreed |
| PoW limit | TBD | Candidate modelling authorised; numeric production value not approved |
| Genesis `nBits` | TBD | Must be consistent with selected PoW limit; not approved |
| Retarget clamp and rounding | Upstream v32.1; ¼×–4× elapsed-time clamp | Owner-approved 16 Nov 2026; implementation tests pending |
| Minimum-difficulty blocks | Disabled for production | Owner-approved; runtime parameter test pending |
| No-retargeting | Disabled for production | Owner-approved; runtime parameter test pending |
| Versionbits deployments | TBD | Do not copy Bitcoin activation schedules blindly |
| Buried deployment heights | TBD | Review each upstream consensus rule |
| Checkpoints | None initially | Only add independently verified FREELY checkpoints |
| Minimum chain work | Zero/empty initially where supported | Revisit after real chain history exists |
| Assume-valid | Empty/null initially where supported | Never copy Bitcoin's value |
| DNS/fixed seeds | None initially | No seed infrastructure exists |

The 600-second target and 2,016-block interval imply a 14-day target timespan. They do not by themselves define the initial difficulty or make a low-hashrate chain secure.

## 4. Genesis block requirements

The owner has approved the height-zero 50 FLY genesis reward as permanently unspendable while remaining included in scheduled issuance accounting. The genesis block is not yet generated. Candidate generation and independent verification are authorised, but no candidate hash or field is final. Do not hard-code a nonce, hash, Merkle root or timestamp as a production value.

Candidate generation must record and test:

1. Candidate timestamp and neutral coinbase message (final wording remains subject to approval).
2. Candidate genesis version and compact target, constrained by the still-unapproved `powLimit`.
3. A permanently unspendable genesis output and explicit proof that the genesis coinbase is not spendable from the UTXO set.
4. The approved monetary schedule and exact 50 FLY height-zero accounting treatment.
5. A deterministic generator using Bitcoin Core's own serialization and hash functions, plus an independent second implementation/check.

Required independent checks:

- Recompute the serialized header and double-SHA-256 hash independently.
- Verify the Merkle root and coinbase transaction bytes.
- Verify the hash satisfies the selected target.
- Add fixed test vectors and startup assertions.
- Verify no genesis output is spendable and no premine is created.

## 5. Approved consensus decisions — 17 November 2026

- Genesis coinbase reward: unspendable permanently; included in scheduled issuance. Spendable scheduled subsidy total is 20,999,949.9769 FLY.
- BIP94: enabled from genesis (`enforce_BIP94 = true`), subject to exact v32.1 source review and dedicated retarget/time-warp tests.
- Script features: established Bitcoin rules are intended active from the start, subject to the activation matrix and compatibility tests. Future soft forks use controlled activation.
- PoW candidate modelling and candidate network/genesis identity generation are authorised. Numeric production `powLimit`, initial difficulty, final identity values and final genesis fields are not approved.

## 6. Development and test-network policy

- The production chain selector `freely` must be a distinct chain type, not an alias of Bitcoin MAIN or REGTEST.
- A private local test profile must be clearly separated from production consensus and network identity.
- Do not create a public FREELY testnet, DNS seed, public mining pool or public bootstrap node as part of this draft.
- Never allow regtest-only controls (instant mining, mock time or test activation overrides) to affect FREELY production.
- Keep all candidate ports and identifiers isolated from Bitcoin mainnet, testnet, testnet4, signet and regtest.

## 7. Required implementation tests

- Chain selector parses as `freely` and round-trips to the same name.
- FREELY data directory and RPC port are unique.
- P2P magic is distinct and correctly recognized by `GetNetworkForMagic`.
- Base58 and extended-key versions do not decode as Bitcoin mainnet/testnet keys.
- Bech32 HRP is `fly` and address encodings are correctly isolated.
- Genesis hash, Merkle root, header fields and proof of work match fixed vectors.
- Production chain is not classified as a test or mockable chain.
- Test-only startup arguments are rejected on FREELY production.
- Existing Bitcoin networks retain their original parameters and regression behaviour.
- Monetary subsidy and cumulative issuance tests pass using FREELY's actual parameter object.
- Retarget, invalid target, timestamp and proof-of-work boundary tests pass.
- Two isolated local nodes can connect, validate blocks and reject a different chain's genesis.

## 8. Security and launch caveats

SHA-256d compatibility does not give FREELY Bitcoin's accumulated hashpower. A new low-hashrate chain may be vulnerable to majority-hash attacks, reorganizations, censorship and double-spends. A 600-second target does not solve this.

Before any public testnet or mainnet proposal, the project needs:
- A defensible initial difficulty and retarget design.
- Independent consensus and security review.
- Reproducible builds and release-signing arrangements.
- Node monitoring, peer infrastructure and incident response.
- Wallet key/address interoperability testing.
- Legal and operational review appropriate to the intended distribution and use.

No public launch, mining deployment, exchange listing, token sale or paid infrastructure is authorized by this document.

## 9. Next engineering sequence

1. Finish the production/test classification audit, including all direct MAIN-only and REGTEST-only startup checks.
2. Add `ChainType::FREELY` and its string parsing/formatting.
3. Add unique base chain parameters and command-line/help integration.
4. Add a dedicated FREELY parameter class, with all candidate values clearly isolated.
5. Implement and independently verify the genesis block.
6. Add the network identity, genesis, monetary, difficulty and startup-policy tests.
7. Run the complete relevant upstream test suites and platform CI.
8. Keep all work in unmerged pull requests until review and explicit owner approval.

## 10. References

- [Bitcoin Core v32.1 release notes](https://bitcoincore.org/en/releases/32.1/)
- [Bitcoin Core v32.1 source tag](https://github.com/bitcoin/bitcoin/tree/v32.1)
- [FREELY network architecture plan](https://github.com/Schmacko/freely-bitcoin-core./blob/freely/network-architecture/docs/FREELY-NETWORK-ARCHITECTURE.md)
- [FREELY M1 test run](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43662943218)


## 11. Candidate identity review status — 17 November 2026

The existing candidate sheet is authorised for static collision review only. A preliminary comparison against the built-in Bitcoin mainnet, testnet3, testnet4, signet (where its magic is known), and regtest identities shows the candidate values are distinct from the fixed Bitcoin values encoded in the current FREELY preflight validator: `FLY1` magic; P2P/RPC ports 19444/19443; Base58 prefixes 35/50/186; extended-key versions `04464c59`/`04464c5a`; Bech32 HRP `fly`; data-directory suffix `freely`. This is **not** a global cryptocurrency registry check, does not establish local port availability, and does not make the values final. Signet magic depends on its challenge and must be checked for the actual configured challenge. The candidate values must remain out of production runtime configuration until full validation and explicit final approval.

## 12. Proof-of-work candidate modelling

See [FREELY PoW Candidate Model](FREELY-POW-CANDIDATE-MODEL.md). The model translates candidate difficulty levels into expected SHA-256d work and expected block intervals at specified hashrates. It is a mathematical planning tool, not a live mining benchmark and not a security guarantee. A real recommendation requires a declared honest-hashrate assumption, a plausible attacker-hashrate/cost model, and a block-stall tolerance. No production `powLimit` or genesis `nBits` is selected by the model.


## 13. Provisional genesis coinbase candidate — 17 November 2026

The owner authorised generation and verification of candidate genesis material. A reproducible candidate coinbase transaction has been constructed using the previously suggested message:

**Candidate message (not final):** FREELY — Freedom Through Decentralisation

**Candidate output:** 50.00000000 FLY to the single-byte OP_RETURN script (hex `6a`). The output is provably unspendable. The height-zero reward remains included in the scheduled issuance accounting, as approved by the owner.

**Candidate coinbase transaction ID / single-transaction Merkle root:**

`f489a4267153fef618863eeeeb202862ca1742cfc32574fd508afa500fb83ce1`

The candidate transaction uses version 1, a null prevout, max sequence, the standard Bitcoin genesis-style coinbase script prefix, and a single 50 FLY OP_RETURN output. The candidate message is UTF-8 encoded. The timestamp in the block header is intentionally unset.

The generator `scripts/generate-freely-genesis-candidate.py`:
- serializes the candidate transaction deterministically;
- verifies its serialization routine against Bitcoin's known genesis coinbase transaction ID before producing FREELY output;
- emits the candidate transaction bytes, txid and Merkle root;
- leaves block time, nBits, nonce and full block hash unset.

**Important:** this is a candidate coinbase transaction and Merkle root, not a valid or final FREELY genesis block. The message wording has not been finally approved; the numeric powLimit and genesis nBits are still unresolved; the block header hash cannot be frozen or verified against proof of work yet. Do not use this candidate in runtime parameters, wallets or a public network.


### Candidate block-header verification tool — 17 November 2026

The candidate generator now also accepts explicit `--time`, `--n-bits`, `--nonce` and `--pow-limit` inputs together. It serializes the 80-byte Bitcoin-style header, decodes compact target values with negative/zero/overflow checks, verifies target <= supplied powLimit, calculates SHA-256d and checks the header hash against the target. It emits the header bytes, candidate block hash and decoded target only when the proof-of-work check succeeds.

A deterministic `--self-test-header` fixture exercises both a valid and invalid nonce using synthetic regtest-like test-only values (`nBits=0x207fffff`, synthetic `powLimit=7fff...ffff`, timestamp 1,700,000,000). The expected fixture hash is fixed in the script. These synthetic values are never selected as FREELY production parameters. The focused specification workflow now py-compiles the generator and runs both the candidate transaction self-check and the synthetic header/PoW fixture. Until CI executes successfully, this is implemented but unverified.
