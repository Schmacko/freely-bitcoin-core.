# FREELY network parameters — provisional engineering draft

- **Status:** proposal only; not activated in code and not approved as final network identity.
- **Date:** 15 November 2026
- **Upstream baseline:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`
- **Purpose:** provide a concrete, reviewable starting point for the dedicated FREELY chain implementation while keeping launch-sensitive values visibly provisional.

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

## 2A. Detailed consensus specification

See the separate [FREELY consensus specification](FREELY-CONSENSUS-SPECIFICATION.md) for the exact subsidy formula, integer issuance tests, genesis accounting distinction, proof-of-work decision list, deployment matrix and required validation vectors. This document remains a candidate network identity sheet; none of its proposed identifiers is final or activated.

## 3. Consensus parameters — agreed versus unresolved

| Parameter | Proposed value | Status |
|---|---:|---|
| Subsidy | 50 FLY | Agreed |
| Halving interval | 210,000 blocks | Agreed |
| Target spacing | 600 seconds | Agreed |
| Target timespan | 1,209,600 seconds (14 days) | Derived from agreed spacing × interval |
| Retarget interval | 2,016 blocks | Agreed |
| PoW algorithm | SHA-256d | Agreed |
| PoW limit | TBD | Requires difficulty/security analysis |
| Genesis `nBits` | TBD | Must be consistent with selected PoW limit |
| Retarget algorithm / clamp | v32.1 semantics; ¼×–4× clamp; owner-approved 16 Nov 2026 | Runtime integration and exact regression vectors pending |
| Minimum-difficulty blocks | Disabled for production | Owner-approved 16 Nov 2026; runtime parameter test pending |
| No-retargeting | Disabled for production | Owner-approved 16 Nov 2026; runtime parameter test pending |
| Versionbits deployments | TBD | Do not copy Bitcoin activation schedules blindly |
| Buried deployment heights | TBD | Review each upstream consensus rule |
| Checkpoints | None initially | Only add independently verified FREELY checkpoints |
| Minimum chain work | Zero/empty initially where supported | Revisit after real chain history exists |
| Assume-valid | Empty/null initially where supported | Never copy Bitcoin's value |
| DNS/fixed seeds | None initially | No seed infrastructure exists |

The 600-second target and 2,016-block interval imply a 14-day target timespan. The production retarget algorithm, ¼×–4× clamp, disabled minimum-difficulty exception and enabled retargeting are owner-approved (16 Nov 2026), but runtime integration and tests remain pending. These choices do not define the initial difficulty or make a low-hashrate chain secure.

## 4. Genesis block requirements

The genesis block is not yet generated. Do not invent or hard-code a nonce, hash, Merkle root or timestamp.

Before generation, decide and document:

1. A durable genesis timestamp and neutral coinbase message.
2. The exact genesis version and initial compact target.
3. A provably unspendable genesis coinbase output (for example, a zero-value `OP_RETURN` commitment), so no founder receives spendable genesis funds.
4. The proof-of-work limit and initial difficulty policy.
5. A deterministic generator using Bitcoin Core's own serialization and hash functions.

Required independent checks:

- Recompute the serialized header and double-SHA-256 hash independently.
- Verify the Merkle root and coinbase transaction bytes.
- Verify the hash satisfies the selected target.
- Add fixed test vectors and startup assertions.
- Verify no genesis output is spendable and no premine is created.

## 5. Development and test-network policy

- The production chain selector `freely` must be a distinct chain type, not an alias of Bitcoin MAIN or REGTEST.
- A private local test profile must be clearly separated from production consensus and network identity.
- Do not create a public FREELY testnet, DNS seed, public mining pool or public bootstrap node as part of this draft.
- Never allow regtest-only controls (instant mining, mock time or test activation overrides) to affect FREELY production.
- Keep all candidate ports and identifiers isolated from Bitcoin mainnet, testnet, testnet4, signet and regtest.

## 6. Required implementation tests

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

## 7. Security and launch caveats

SHA-256d compatibility does not give FREELY Bitcoin's accumulated hashpower. A new low-hashrate chain may be vulnerable to majority-hash attacks, reorganizations, censorship and double-spends. A 600-second target does not solve this.

Before any public testnet or mainnet proposal, the project needs:
- A defensible initial difficulty and retarget design.
- Independent consensus and security review.
- Reproducible builds and release-signing arrangements.
- Node monitoring, peer infrastructure and incident response.
- Wallet key/address interoperability testing.
- Legal and operational review appropriate to the intended distribution and use.

No public launch, mining deployment, exchange listing, token sale or paid infrastructure is authorized by this document.

## 8. Next engineering sequence

1. Finish the production/test classification audit, including all direct MAIN-only and REGTEST-only startup checks.
2. Add `ChainType::FREELY` and its string parsing/formatting.
3. Add unique base chain parameters and command-line/help integration.
4. Add a dedicated FREELY parameter class, with all candidate values clearly isolated.
5. Implement and independently verify the genesis block.
6. Add the network identity, genesis, monetary, difficulty and startup-policy tests.
7. Run the complete relevant upstream test suites and platform CI.
8. Keep all work in unmerged pull requests until review and explicit owner approval.

## 9. References

- [Bitcoin Core v32.1 release notes](https://bitcoincore.org/en/releases/32.1/)
- [Bitcoin Core v32.1 source tag](https://github.com/bitcoin/bitcoin/tree/v32.1)
- [FREELY network architecture plan](https://github.com/Schmacko/freely-bitcoin-core./blob/freely/network-architecture/docs/FREELY-NETWORK-ARCHITECTURE.md)
- [FREELY M1 test run](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43662943218)
