# FREELY network architecture plan (draft)

**Status:** design only; no runtime code or network identity is activated.  
**Pinned upstream:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`.  
**Purpose:** define a safe implementation sequence for an independent FREELY UTXO chain while preserving Bitcoin's existing networks.

## 1. Non-negotiable project rules

- FREELY is an independent chain with native UTXO coins, not a token deployed on another chain.
- Proof of work is SHA-256d (Bitcoin Core's existing double-SHA-256 block-header hash and proof-of-work validation path).
- Monetary policy: 50 FLY initial subsidy; 210,000-block halving interval; 100,000,000 base units per FLY; 21,000,000 FLY hard ceiling; no premine, founder allocation, ICO, or initial sale.
- Target block spacing: 600 seconds; retarget interval: 2,016 blocks. Retarget boundary behaviour, proof-of-work limit and minimum-difficulty rules must be specified and tested before activation.
- Consensus money arithmetic stays integer-only. Preserve upstream range checks and transaction/script validation unless a documented FREELY requirement justifies a change.
- Do not modify Bitcoin mainnet, testnet, signet or regtest parameters to make them resemble FREELY.
- Do not invent or activate network identifiers, genesis values, seed endpoints or launch settings in this design document.
- No public mainnet, public testnet, mining deployment, wallet distribution or launch is authorised by this document.

## 2. Proposed chain-selection architecture

Add an explicit FREELY chain type rather than aliasing an existing Bitcoin chain:

- `ChainType::FREELY` for the eventual FREELY production network.
- Consider a separate `ChainType::FREELY_TEST` only if a persistent public test network is approved. A private local development/regtest profile should remain clearly separate from production consensus and network identity.

The final names and whether a separate public test chain is needed remain open decisions. Never make FREELY an alias for `MAIN` or `REGTEST`.

The following upstream surfaces must be updated consistently:

1. `src/util/chaintype.h` and `src/util/chaintype.cpp`: enum, string conversion and parsing.
2. `src/chainparamsbase.h` and `src/chainparamsbase.cpp`: unique data-directory name, RPC port, chain selection option/help and allowed chain-name list.
3. `src/kernel/chainparams.h` and `src/kernel/chainparams.cpp`: immutable consensus/network parameters, genesis construction, message-start bytes, address encodings, Bech32 HRP, seed lists and chain metadata.
4. `src/chainparams.cpp` and `src/chainparams.h`: construction and selection of the FREELY parameter object.
5. `src/init.cpp`: startup help/default descriptions and every branch that currently special-cases `ChainType::MAIN`, `TESTNET`, `SIGNET` or `REGTEST`.
6. All other exhaustive `ChainType` switches and comparisons discovered by repository-wide search. Compilation is expected to expose some missed switches, but it is not a substitute for a semantic audit.

### Important classification issue

In v32.1, `CChainParams::IsTestChain()` currently returns true for every chain type except `MAIN`. A production FREELY network must not accidentally inherit test-chain semantics merely because its enum is distinct. Before implementation, define explicit production/test classification and audit all call sites of `IsTestChain()`, `IsMockableChain()`, and direct `ChainType::MAIN` comparisons.

### Existing network fields that require independent FREELY values

- Chain type string and config section.
- Data-directory suffix.
- P2P message-start magic (four bytes).
- P2P listening port and RPC port.
- Base58 public-key, script and secret-key prefixes.
- Extended public/private key prefixes.
- Bech32/Bech32m human-readable prefix.
- Genesis block and expected genesis hash / Merkle root.
- Proof-of-work limit, target spacing, target timespan, retarget interval and special difficulty flags.
- DNS/fixed seeds (remain empty until real, controlled infrastructure exists).
- Chain transaction metadata and assume-valid / minimum-chainwork values (must not be copied from Bitcoin; initially use conservative empty/zero values where the upstream field permits it).

No value in the list above is assigned in this draft.

## 3. Consensus configuration

The FREELY parameter object must set and test at least:

| Parameter | Agreed target | Implementation note |
|---|---:|---|
| Initial subsidy | 50 FLY | 5,000,000,000 base units |
| Halving interval | 210,000 blocks | Integer right-shift schedule |
| Monetary precision | 8 decimals | 100,000,000 base units / FLY |
| Hard supply ceiling | 21,000,000 FLY | Existing upstream `MAX_MONEY` is 21m * COIN; verify all paths |
| Target block spacing | 600 seconds | Confirm all timestamp/retarget assumptions |
| Retarget interval | 2,016 blocks | 14-day target timespan at 600 seconds |
| PoW hash | SHA-256d | Retain upstream block-header hash and PoW checks |

Bitcoin's integer subsidy schedule yields a maximum scheduled issuance of 2,099,999,997,690,000 base units (20,999,999.9769 FLY), below the hard ceiling. The genesis coinbase must not create spendable premine funds; its exact construction and treatment must be explicit and tested.

Before consensus code is activated, separately specify: `powLimit`, initial compact target (`nBits`), retarget clamping/rounding edge cases, timestamp constraints, minimum-difficulty behaviour, versionbits deployments/activation heights, buried deployments, checkpoints, assume-valid and minimum-chainwork. Do not inherit Bitcoin mainnet activation heights, checkpoints or chainwork assumptions without a FREELY-specific justification.

## 4. Genesis construction procedure

1. Agree a unique, non-political, durable genesis timestamp/message and the intended coinbase output script.
2. Choose the genesis time, version, initial target and nonce under the agreed proof-of-work limit.
3. Generate the genesis block using the upstream block/transaction serialization and hash routines.
4. Independently recompute and cross-check the block hash, Merkle root, serialized header and proof-of-work result using a second implementation or independent reviewer.
5. Hard-code the verified values only after the reproducible generation procedure and test vectors are committed.
6. Add assertions and tests for the exact genesis hash, Merkle root, header fields and proof of work.

A genesis nonce/hash must never be guessed or copied from Bitcoin. The genesis block's coinbase output is not a founder allocation; ensure it is unspendable and document its treatment in the issuance accounting.

## 5. Required tests before considering a development network usable

- Chain-name parsing and string round-trip.
- Base parameters: data directory, RPC port and config-section isolation.
- Distinct P2P magic and `GetNetworkForMagic` mapping.
- Distinct Base58 and Bech32 prefixes; no accidental Bitcoin address encoding.
- Genesis hash, Merkle root and proof-of-work assertions.
- Subsidy boundary tests and full integer cumulative issuance test.
- Retarget tests at interval boundaries, including clamping, timestamp and compact-target edge cases.
- Proof-of-work limit and invalid-target rejection tests.
- Coinbase reward / fee accounting and no-premine checks.
- Existing Bitcoin mainnet, testnet, signet and regtest regression suites unchanged.
- End-to-end isolated node startup and block generation on a private development network, after all identity values have been approved.

## 6. Implementation sequence and gates

**Gate A — current:** compile and run the M1 monetary-policy test patch. Do not treat source review or a Python arithmetic check as a successful C++ build.

**Gate B — architecture implementation:** after Gate A passes, add the chain type and base parameter plumbing in a separate reviewed patch. Keep all new identity fields explicitly provisional and do not enable a public network.

**Gate C — consensus/genesis:** only after the user approves the complete parameter sheet, implement consensus parameters and a reproducibly generated genesis block. Add the tests above.

**Gate D — private development network:** run isolated nodes and regression tests with no public seeds or public launch. Verify chain separation and reorg/validation behaviour.

**Gate E — public launch:** requires independent security review, operational infrastructure, legal review where relevant, and explicit user approval. No launch is implied or authorised by the earlier gates.

## 7. Current blockers and known source-review findings

- The M1 PR's C++ test and dedicated Actions workflow have not yet completed; keep the PR unmerged until actual CI results and code review are available.
- The existing GitHub Actions runs were still queued/pending at the last status check. Do not claim the C++ patch has compiled.
- `src/kernel/chainparams.cpp` currently contains Bitcoin's mainnet genesis, message-start bytes, Base58 prefixes and Bech32 HRP; these must not be reused for FREELY.
- `src/chainparamsbase.cpp` currently maps each chain type to its own data directory and RPC port.
- `src/init.cpp` constructs parameter objects for help/default descriptions and includes direct chain-type special cases. These need explicit review for a new production chain.
- `CChainParams::IsTestChain()` currently equates “not MAIN” with “test”; this needs an explicit policy before a new chain type is introduced.
- No runtime consensus changes are included in this architecture-plan branch.

## 8. References

- Bitcoin Core v32.1 source pin: `f0de87f040621468b956f01f526a43a010310501`.
- `src/util/chaintype.h`, `src/util/chaintype.cpp`.
- `src/chainparamsbase.h`, `src/chainparamsbase.cpp`.
- `src/kernel/chainparams.h`, `src/kernel/chainparams.cpp`.
- `src/chainparams.h`, `src/chainparams.cpp`.
- `src/init.cpp`.
