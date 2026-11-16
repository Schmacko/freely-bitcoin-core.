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

- The dedicated M1 validation workflow has passed on earlier revisions; the latest revision is awaiting a fresh run after the Windows CI checkout-path fix. Keep the PR unmerged until current-head CI results and code review are available.
- The latest revision `68829ade95abd4f632f350d78afccb9db04a0ef5` has two new Actions runs: general CI is queued and the dedicated M1 workflow is pending. Do not claim this revision has compiled until those runs finish.
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


## 9. Verified progress update — 15 November 2026

### Gate A result: passed

The dedicated FREELY M1 GitHub Actions run completed successfully:

- Workflow: `FREELY M1 consensus tests`.
- Run: [43662943218](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43662943218).
- Tested commit: `cd00a88a3bd60ee1831e3877518390643864846b`.
- Job: `validation-tests`.
- Result: all workflow steps completed successfully.
- The workflow configured the v32.1 source tree, built the `test_bitcoin` executable, and ran CTest with `-R '^validation_tests$'`.

This verifies the C++ test binary builds and the selected validation test suite passes for that commit. It is not a full platform matrix, sanitizer run, full upstream test suite, security audit, or FREELY node build. The runtime chain implementation is still absent.

### Source audit — exact integration points

A read-only audit of the pinned v32.1 source confirmed the following integration map:

| File | Current upstream behaviour | Required FREELY work |
|---|---|---|
| `src/util/chaintype.h` | Enum contains MAIN, TESTNET, SIGNET, REGTEST and TESTNET4 | Add a distinct FREELY production enum value |
| `src/util/chaintype.cpp` | String conversion and parsing enumerate existing chains | Add canonical `freely` round-trip and invalid-name tests |
| `src/chainparamsbase.h` | Allowed chain names omit FREELY | Add `freely` to the allowed-name list |
| `src/chainparamsbase.cpp` | Base data directory and RPC port are selected by exhaustive switch | Add unique FREELY data-directory suffix and RPC port |
| `src/kernel/chainparams.h` | Chain parameters expose chain type, genesis, magic, ports and address encodings | Add a dedicated FREELY parameter factory/options surface only where needed |
| `src/kernel/chainparams.cpp` | Constructors define each Bitcoin network; magic lookup maps known networks | Add a separate FREELY parameter class and unique message magic; never mutate Bitcoin constructors |
| `src/chainparams.cpp` | `CreateChainParams` is an exhaustive chain-type switch | Add FREELY construction |
| `src/init.cpp` | Help/default setup creates each current network; startup has direct MAIN/REGTEST/SIGNET comparisons | Add FREELY to setup and audit each special-case semantically |

### Startup policy findings

The source audit found two particularly important direct checks in `src/init.cpp`:

1. Around line 1186, `-testactivationheight` and `-vbparams` are blocked only when the selected chain is exactly `ChainType::MAIN`. A future FREELY production chain would bypass that guard unless it is changed to use an explicit production-chain policy.
2. Around line 1171, `-test=<option>` is restricted to REGTEST. This should remain a regtest-only facility; FREELY must not be added to this exception.

Other chain-specific logic also needs review:
- `-acceptstalefeeestimates` currently has a REGTEST-only exception.
- Testnet3 deprecation logging is specifically tied to TESTNET and should not be generalized.
- Signet magic logging is specifically tied to SIGNET.
- `GetNetworkForMagic` in `src/kernel/chainparams.cpp` must map FREELY's unique magic without collisions.
- `CreateBaseChainParams`, `CreateChainParams`, and all enum-to-string/parser switches must remain exhaustive.

### Classification correction status

The M1 PR changes `CChainParams::IsTestChain()` from the old implicit rule “anything other than MAIN is a test chain” to an explicit `m_is_test_chain` flag, and adds `IsProductionChain()` with MAIN explicitly marked as production. Existing Bitcoin test networks set the test flag true. Regression tests check all five existing Bitcoin chain classifications and the production flag.

This correction is compiled and covered by the passing M1 validation test run. It does not yet add `ChainType::FREELY`, nor does it solve the separate MAIN-only startup guard described above. Those remain implementation requirements.

### Next implementation gate

Proceed with a narrowly scoped chain-selection patch only after the complete FREELY parameter sheet is defined. The chain type, data-directory and RPC plumbing can be prepared independently, but a selectable production chain must not be left with Bitcoin's genesis, network magic, address prefixes, activation assumptions or test-only startup behaviour. Keep the new chain private and unlaunched until all values and tests are independently reviewed.


## 10. Progress update — 15 November 2026 (CI path correction)

The previous full CI attempt exposed a Windows checkout failure before compilation. The runner attempted to create a nested checkout directory whose name repeated the repository name, including its trailing period:

`D:\\a\\freely-bitcoin-core.\\freely-bitcoin-core.`

The failure occurred in `actions/checkout`, not in C++ compilation. The repository name was intentionally left unchanged. Instead, all five checkout steps in `.github/workflows/ci.yml` were updated to use `path: .`, checking out directly into the workspace root and avoiding the invalid nested path.

- Fix commit: `68829ade95abd4f632f350d78afccb9db04a0ef5`.
- Updated branch: `freely/m1-consensus`.
- PR: [FREELY M1 #1](https://github.com/Schmacko/freely-bitcoin-core./pull/1).
- General CI run: [43765129757](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43765129757) — queued at the time of this update.
- Dedicated M1 test run: [43765129758](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43765129758) — pending at the time of this update.

The workflow file was read back after the commit; all five checkout steps contain the root path setting. The fix is not considered validated until the new Windows jobs get past checkout and the relevant builds/tests complete.

The earlier targeted M1 validation success remains valid for its own tested revision, but it does not substitute for testing this new head commit. No PR merge or network launch has occurred.

### Current implementation boundary

The next source-level chain-selection patch is still gated on a complete, internally consistent network-parameter specification. The candidate P2P magic, ports, address prefixes and extended-key versions in `FREELY-NETWORK-PARAMETERS-DRAFT.md` remain proposals only. PoW limit, genesis target, activation policy, retarget edge cases and genesis transaction/header data remain unresolved. Do not expose a selectable production chain until those are defined and tested.


## 12. Progress update — 16 November 2026 (consensus specification)

A separate documentation branch, `freely/consensus-specification`, now contains a testable engineering baseline:

- [FREELY consensus specification](FREELY-CONSENSUS-SPECIFICATION.md).
- [Independent integer subsidy/specification check](../scripts/verify-freely-consensus-spec.py).
- Specification commit: `41f418e9f1fc662f66b83a4da4b5040d0a9c2cee`.
- Arithmetic check commit: `1b5a830ae5c4f805f45e3459ce77ee4efd7201ec`.

The specification formalizes the agreed integer subsidy formula, boundary vectors, issuance ceiling, reward/fee rule and test contract. It also highlights an accounting point that must be settled before genesis implementation: a conventional unspendable genesis coinbase means the height-zero 50 FLY is included in scheduled subsidy arithmetic but is not spendable. Under that convention, the spendable subsidy total would be 20,999,949.9769 FLY, not 20,999,999.9769 FLY.

The proof-of-work limit, genesis target, retarget edge behaviour, minimum-difficulty policy, time-warp mitigation, activation matrix and genesis details remain unresolved. No consensus code or network identity has been activated by this documentation work.

The Windows workflow correction is being verified separately on the current M1 PR head. Do not infer CI success from this documentation commit.


## 13. Static chain-selection audit

A dedicated source audit now maps the required chain selector, base parameters, chain factory, production/test classification, monetary range, genesis and consensus integration points. See [FREELY chain-selection and consensus integration audit](FREELY-CHAIN-SELECTION-AUDIT.md) and draft [PR #3](https://github.com/Schmacko/freely-bitcoin-core./pull/3). The audit is documentation-only; it does not activate any chain identity or change runtime behaviour.


## 14. Proof-of-work and difficulty source audit — 16 November 2026

A separate documentation-only branch now records a detailed audit of the pinned v32.1 proof-of-work path:

- [FREELY PoW and difficulty audit](https://github.com/Schmacko/freely-bitcoin-core./blob/freely/pow-difficulty-audit/docs/FREELY-POW-DIFFICULTY-AUDIT.md).
- Draft PR: [#4](https://github.com/Schmacko/freely-bitcoin-core./pull/4).
- Branch: `freely/pow-difficulty-audit`.
- Commit: `f0bdd6e4e5b180ed4cb1d01a7e9681b9d66b05c0`.

The audit confirms that upstream v32.1 already implements the SHA-256d proof-of-work check, compact-target validation, 2,016-block retarget machinery, factor-of-four timespan clamp, optional minimum-difficulty rule and optional BIP94 period-start-target handling. FREELY's agreed 600-second spacing implies a 1,209,600-second (14-day) target timespan.

The audit does not select `powLimit`, genesis `nBits`, minimum-difficulty policy, BIP94 policy or any other open consensus parameter. It makes no runtime code changes and does not enable a chain.

### Current M1 CI observation — 16 November 2026

On head `3c48e0fc2f3433a946ed29326c3c5233f4d826a3`, both affected Windows jobs have successfully completed the Windows-safe checkout and entered build-system generation. The general CI's `No wallet` job failed while Docker attempted to retrieve `mirror.gcr.io/ubuntu:24.04`; the registry returned HTTP 429 (rate limited) on both attempts. This is an external image-registry retrieval failure, not a compiler diagnostic. The Windows builds and the dedicated M1 validation workflow are not yet terminal. See [general CI #34](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43782087333) and [M1 tests #16](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43782087351).

The current M1 branch is being left unchanged while these workflows run.
