# FREELY network architecture plan (draft)

- **Status:** design only; all four protocol parameter areas are owner-approved, but no runtime production parameters or network identity are activated.
- **Pinned upstream:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`.
- **Purpose:** define a safe implementation sequence for an independent FREELY UTXO chain while preserving Bitcoin's existing networks.

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

The FREELY production name and data-directory suffix `freely` are approved. Whether a separate public test chain is needed remains an open owner decision. Never make FREELY an alias for `MAIN` or `REGTEST`.

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

The source-level chain-selection patch can now use the owner-approved identity and consensus baseline in `FREELY-APPROVED-PROTOCOL-PARAMETERS.md`. The approved PoW limit, genesis target, message magic, ports, prefixes and activation matrix are no longer open parameter choices. The derived genesis transaction/Merkle commitment and nonce/hash, runtime integration and exact-head tests remain outstanding. Do not expose a selectable production chain until those gates pass.


## 12. Progress update — 16 November 2026 (consensus specification)

A separate documentation branch, `freely/consensus-specification`, now contains a testable engineering baseline:

- [FREELY consensus specification](FREELY-CONSENSUS-SPECIFICATION.md).
- [Independent integer subsidy/specification check](../scripts/verify-freely-consensus-spec.py).
- Specification commit: `41f418e9f1fc662f66b83a4da4b5040d0a9c2cee`.
- Arithmetic check commit: `1b5a830ae5c4f805f45e3459ce77ee4efd7201ec`.

The specification formalizes the agreed integer subsidy formula, boundary vectors, issuance ceiling, reward/fee rule and test contract. It also highlights an accounting point that must be settled before genesis implementation: a conventional unspendable genesis coinbase means the height-zero 50 FLY is included in scheduled subsidy arithmetic but is not spendable. The owner approved the permanently unspendable genesis output convention; scheduled issuance remains 20,999,999.9769 FLY and the spendable subsidy total under that convention is 20,999,949.9769 FLY.

The proof-of-work limit, genesis target, retarget policy, BIP94, network identity and initial activation matrix were owner-approved on 18 November 2026. The derived genesis commitment, implementation, source compatibility tests and independent security review remain incomplete. No production consensus object is selected by this documentation work.

The Windows checkout and no-wallet image failures were reproduced in CI logs and are now addressed in draft PR #9. The revised workflow is queued for current-head validation; do not infer CI success from this documentation commit.


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

On head `3c48e0fc2f3433a946ed29326c3c5233f4d826a3`, both Windows native jobs completed checkout, build and test successfully. The general CI `No wallet` job failed twice because Docker received HTTP 429 from `mirror.gcr.io/ubuntu:24.04`; this was an external image-registry failure, not a compiler error. See [general CI #34](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43782087333) and [M1 tests #16](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/43782087351).

A later run on 17 November exposed a separate default-checkout failure on Windows: `D:\\a\\freely-bitcoin-core.\\freely-bitcoin-core.` did not exist. Draft PR #9 now addresses both CI issues by cloning Windows jobs under `RUNNER_TEMP`, deriving vcpkg cache keys from that temporary checkout, and using `ubuntu:24.04` for the no-wallet container. Current-head validation is queued; neither fix is yet claimed as CI-passed.


## 15. Architecture completion sprint — 16 November 2026

This section supersedes stale status statements in earlier historical notes where they conflict with the current project state. It records the architecture as a design deliverable; it does not claim that FREELY runtime code has been implemented.

### 15.1 Definition of architecture completion

The Network Architecture phase is considered 100% complete when the following are documented, internally consistent, traceable to the pinned v32.1 source, and covered by a test/acceptance matrix:

1. Chain-selection and classification contract.
2. Base-chain parameter contract and isolation requirements.
3. Kernel consensus/network parameter ownership.
4. Startup, CLI, RPC, wallet and GUI integration points.
5. Network identity inventory and collision/approval gates.
6. Genesis construction and reproducibility procedure.
7. Upgrade, activation, compatibility and regression strategy.
8. Test matrix, implementation sequencing, threat boundaries and release gates.

A 100% architecture score means the design is ready for implementation. It does **not** mean the chain type, genesis, network identifiers, consensus constants, wallet, node or network are implemented or launch-ready.

### 15.2 Canonical chain-selection contract

The eventual production selector is the distinct canonical name `freely`, represented by a dedicated `ChainType::FREELY`. It must never alias `MAIN`, `REGTEST`, `SIGNET` or either Bitcoin testnet. A public FREELY test chain is a separate future decision; it is not implied by this production selector.

Required invariants:

- `ChainTypeToString(ChainType::FREELY)` returns exactly `freely`.
- `ChainTypeFromString("freely")` returns exactly `ChainType::FREELY`.
- Parsing and serialization round-trip for every chain type; unknown names fail closed.
- `-chain=freely` selects FREELY in both daemon and CLI.
- The config section and data directory are isolated from all Bitcoin networks and from each other.
- Every exhaustive switch over `ChainType` handles FREELY explicitly.
- `GetNetworkForMagic` recognizes only FREELY's approved, unique four-byte message magic.
- Existing Bitcoin network behaviour and identifiers remain unchanged.

### 15.3 Production/test classification contract

Do not infer production status from “not MAIN”. The implementation must use explicit classification with tests for every chain.

| Network | Production | Test-only | Mockable time |
|---|---:|---:|---:|
| Bitcoin MAIN | Yes | No | No |
| Bitcoin TESTNET / TESTNET4 | No | Yes | No, unless upstream explicitly says otherwise |
| Bitcoin SIGNET | No | Yes | No, unless upstream explicitly says otherwise |
| Bitcoin REGTEST | No | Yes | Yes |
| FREELY | Yes | No | No |
| FREELY public test chain | Not defined | Not defined | Not defined |

The FREELY production row is a required target, not a claim that the enum exists today. The separate public test-chain row remains deliberately undefined until approved.

Production classification must protect production networks from test-only consensus overrides. In particular:
- `-testactivationheight` and `-vbparams` must be rejected for **all** production chains, including FREELY.
- `-test=<option>` remains REGTEST-only.
- Do not broaden REGTEST-only exceptions (including fast-prune or mock-time behaviour) to FREELY.
- Keep testnet deprecation messages and signet-specific options scoped to their own networks.

### 15.4 Parameter ownership and isolation map

| Layer | Owner / source files | Required FREELY behaviour |
|---|---|---|
| Name and enum | `src/util/chaintype.h/.cpp` | Dedicated enum, canonical parse/string conversion |
| Shared CLI/RPC base | `src/chainparamsbase.h/.cpp` | Unique data-dir suffix and RPC port; allowed-name/help updates |
| Kernel identity and consensus | `src/kernel/chainparams.h/.cpp` | Dedicated immutable parameter object; unique magic, P2P port, address encodings, genesis and consensus |
| Parameter construction | `src/chainparams.h/.cpp` | Exhaustive FREELY factory and parameter selection |
| Startup and safety guards | `src/init.cpp` plus callers | Production-aware guards; no test-only overrides |
| Network lookup | `GetNetworkForMagic` and protocol consumers | Unique magic mapping; no collisions |
| Wallet/address presentation | wallet, GUI and RPC network-dependent code | FREELY prefixes and HRP only; no Bitcoin address ambiguity |
| Tests | `src/test`, functional tests and CI workflows | Round-trip, isolation, regression, startup and end-to-end checks |

The existing `freely/network-architecture` branch is a documentation branch pinned to upstream v32.1. Its checked-in source files still show upstream behaviour (including the old `IsTestChain() { return m_chain_type != ChainType::MAIN; }` implementation). The explicit classification work described in the M1 PR is on a separate implementation branch and must be integrated/reconciled before code implementation. Do not treat this documentation branch's source snapshot as proof that M1 has been merged.

### 15.5 Network identity registry and approval gate

The implementation must maintain one authoritative parameter registry, with each field marked as one of: **approved**, **derived**, **provisional**, or **blocked pending owner decision**.

| Parameter | Required uniqueness / rule | Current decision |
|---|---|---|
| Chain name | Canonical `freely` | Approved |
| Production/test classification | Production, not test/mockable | Approved as design target |
| P2P message magic | Unique four bytes; no collision with Bitcoin networks | Blocked: value not assigned |
| P2P port | Dedicated, documented and collision-checked | Blocked: value not assigned |
| RPC port | Dedicated, documented and collision-checked | Blocked: value not assigned |
| Data directory | Dedicated FREELY suffix | Requirement approved; exact suffix can be `freely` |
| Base58 prefixes | Unique public-key, script and secret-key values | Blocked: values not assigned |
| Extended-key versions | Unique public/private versions | Blocked: values not assigned |
| Bech32 HRP | Unique human-readable prefix | Blocked: value not assigned |
| Genesis timestamp/message | Durable and approved | Blocked |
| Genesis output script | Unspendable; no founder allocation | Rule approved; exact script blocked |
| Genesis `nBits` and nonce | Must satisfy approved `powLimit`; reproducibly generated | Blocked |
| `powLimit` | Numeric FREELY-specific consensus limit | Blocked |
| Difficulty retarget | 600 s spacing; 2,016 interval; 14-day timespan; clamp 1/4–4x | Approved |
| Minimum difficulty | Disabled for production | Approved |
| No-retargeting | Disabled for production | Approved |
| BIP94/time-warp mitigation | Explicit production choice and vectors | Blocked |
| DNS/fixed seeds | Empty until controlled infrastructure exists | Approved |
| Assume-valid / minimum chainwork | No Bitcoin mainnet values copied | Approved rule; initial values must be conservative |
| Versionbits / buried activations | FREELY-specific reviewed activation matrix | Blocked |

No blocked value may be filled with a plausible-looking placeholder in executable consensus code. A value becoming approved requires an explicit owner decision recorded in the parameter registry and corresponding test vectors.

### 15.6 Genesis and consensus safety contract

- Preserve Bitcoin Core v32.1 serialization, block-header hashing and proof-of-work validation paths unless a separately reviewed requirement justifies a change.
- Generate the genesis block using the upstream serialization and hash routines.
- Independently reproduce and verify header bytes, Merkle root, block hash and proof-of-work result.
- The genesis coinbase output must be unspendable and must not constitute a premine or founder allocation.
- Document separately the scheduled height-zero subsidy and the spendable issuance total under the unspendable-genesis convention.
- Do not activate a selectable production network until `powLimit`, genesis `nBits`, genesis data, activation matrix and the remaining production consensus decisions are complete and tested.
- Do not copy Bitcoin checkpoints, assume-valid hashes, chainwork assumptions or seed infrastructure.

### 15.7 Acceptance matrix

| Test group | Minimum acceptance evidence |
|---|---|
| Chain type | Parse/string round-trip; unknown-name rejection; all switches compile |
| Classification | Explicit production/test/mockable assertions for every chain |
| Startup guards | FREELY rejects test activation overrides and test-only flags |
| Base isolation | Distinct data directory, config section and RPC port |
| P2P isolation | Unique magic, port and network lookup; collision tests |
| Address isolation | Base58, extended-key and Bech32 prefixes are distinct |
| Genesis | Exact hash, Merkle root, header fields and PoW assertions |
| Consensus | Subsidy, money range, powLimit, target decoding and retarget vectors |
| Regression | Existing Bitcoin mainnet/testnet/testnet4/signet/regtest tests unchanged |
| Functional | Private isolated FREELY node startup, mining and restart only after parameter approval |
| Compatibility | Wallet/RPC/GUI network selection cannot silently select Bitcoin MAIN |
| Security | Independent review of consensus and chain separation before public exposure |

### 15.8 Implementation sequence and parallel work

The architecture work can proceed in parallel with documentation/test preparation:
1. Reconcile M1 explicit production classification with the architecture branch.
2. Complete a repository-wide inventory of chain-type switches, MAIN comparisons, network magic lookup, address encoding and startup guards.
3. Create a machine-readable parameter registry with approval status; keep blocked values out of runtime code.
4. Prepare the chain-type/base-parameter implementation patch only after its safe defaults and tests are specified.
5. Implement kernel parameters and genesis only after the blocked consensus/identity decisions are approved.
6. Run the acceptance matrix and preserve existing Bitcoin regression behaviour.
7. Keep all network exposure and launch actions behind separate explicit approval.

### 15.9 Current architecture sprint checklist

- [x] Define what 100% architecture completion means, separately from implementation and launch.
- [x] Specify canonical FREELY chain type and isolation invariants.
- [x] Specify explicit production/test classification and test-only startup guard behaviour.
- [x] Map source-file ownership and integration responsibilities.
- [x] Inventory network identity fields and mark unresolved values as blocked.
- [x] Specify genesis reproducibility and no-premine constraints.
- [x] Define architecture acceptance tests and implementation gates.
- [ ] Reconcile the M1 implementation branch with this architecture plan.
- [ ] Complete repository-wide call-site inventory and verify every chain-type switch/guard.
- [ ] Record the final architecture review and cross-document consistency check.

**Completion rule:** the phase can be scored 100% when the remaining two audit/reconciliation tasks are completed and the architecture is signed off as implementation-ready. The blocked parameter values are separate owner decisions for the later consensus/network-identity gate; they must not be guessed merely to inflate this phase score.



## 16. Repository-wide integration-point verification — 16 November 2026

The architecture sprint reconciled the M1 production-classification patch with the chain architecture and checked the principal chain-selection source files on `freely/m1-consensus` (the current M1 PR head at the time of review).

### Verified current M1 integration

- `CChainParams::IsTestChain()` reads the explicit `m_is_test_chain` flag.
- `CChainParams::IsProductionChain()` reads the explicit `m_is_production_chain` flag.
- Bitcoin MAIN explicitly sets production; TESTNET, TESTNET4, SIGNET and REGTEST explicitly set test-chain.
- `src/init.cpp` rejects `-testactivationheight` and `-vbparams` through `IsProductionChain()`.
- `-test=<option>` remains restricted to REGTEST.
- `-acceptstalefeeestimates` retains its REGTEST-only exception.
- PR #8 now adds `ChainType::FREELY`, canonical parsing/serialization, help registration and fail-closed guards in both parameter factories; selector-entrypoint regression tests are written, with C++ execution still pending.
- No FREELY parameter class, genesis, production network identity, magic, ports, address prefixes, seeds or activation matrix exists yet.

### Verified chain-selection call sites

| File / location | Current verified behaviour | Required when FREELY is implemented |
|---|---|---|
| `src/init.cpp` setup around lines 484–493 | Constructs base and kernel parameter objects for MAIN, TESTNET, TESTNET4, SIGNET and REGTEST | Add FREELY base and kernel objects to help/default setup |
| `src/init.cpp` around line 971 | Signet-specific option path checks SIGNET | Keep signet-only behaviour scoped to SIGNET |
| `src/init.cpp` around lines 1171–1191 | `-test` is REGTEST-only; production override guard uses `IsProductionChain()` | Preserve these guards; test FREELY production rejection |
| `src/init.cpp` around line 1957 | Stale fee estimates exception is REGTEST-only | Do not extend to FREELY |
| `src/chainparams.cpp` around lines 135–160 | The switch now has a FREELY branch that throws until parameters are finalized | Replace the fail-closed guard with a dedicated FREELY factory only after consensus and identity decisions are approved |
| `src/chainparamsbase.cpp` around lines 42–53 | The FREELY base-parameter branch deliberately throws pending final identity | Replace the guard only with an isolated data-dir suffix and approved, collision-checked RPC port |
| `src/util/chaintype.cpp` around lines 14–43 | Both chain-to-string and string-to-chain switches now include canonical `freely` mapping | Keep round-trip, unknown-name and exhaustive handling tests |
| `src/kernel/chainparams.cpp` around lines 729–746 | `GetNetworkForMagic` maps the five Bitcoin network magic values | Add FREELY only with an approved unique four-byte magic |
| `src/kernel/chainparams.cpp` network constructors | MAIN, SIGNET and REGTEST assign their own chain types and network values | Add an independent FREELY constructor; do not clone Bitcoin MAIN identity or history |

This is a targeted integration-point audit of the chain-selection surfaces and direct comparisons found in the principal startup/parameter files. It is not a claim that every network-dependent call site across all wallet, GUI, RPC, networking and validation files has already been changed; those are implementation-time searches and regression checks in the acceptance matrix.

### Cross-document reconciliation

- The M1 PR #1 is the source of truth for the explicit production/test classification patch; it remains separate and unmerged until its current-head CI and review gates pass.
- The chain-selection audit in PR #3 provides the deeper monetary, consensus and genesis integration analysis.
- The architecture plan now consolidates the chain selector, base parameter, kernel parameter, startup guard, identity registry, genesis and acceptance contracts.
- The retarget and PoW audit/PRs remain separate sources for detailed difficulty behaviour; the agreed production retarget policy is recorded in the architecture contract.
- No contradictory production identity values are introduced by this architecture document.

### Architecture phase exit review

- [x] M1 classification design reconciled with the architecture contract.
- [x] Principal chain-selection switches and startup guards inspected on the M1 branch.
- [x] Integration ownership and required FREELY extension points documented.
- [x] Network identity and consensus values not yet approved remain explicitly blocked, not guessed.
- [x] Acceptance matrix and safe implementation sequence defined.
- [x] Cross-document ownership and dependency boundaries recorded.

**Architecture phase status: 100% — design and implementation contract complete.** This score applies only to the Network Architecture roadmap phase. Runtime implementation, parameter approval, consensus activation, security review, private-network validation and launch remain separate roadmap phases and are not complete.

## 17. Canonical documentation reconciliation — 18 November 2026

This section is authoritative where it supersedes earlier historical status statements in this document. The detailed architecture contract above is retained; the newer consensus decisions and implementation evidence below take precedence over earlier "unresolved" or pending descriptions.

### 17.1 Owner-approved consensus decisions

- Genesis coinbase spendability: **approved unspendable**. The genesis reward is included in scheduled subsidy accounting but is not spendable. The parameter manifest must state `coinbase_spendable: false`.
- BIP94/time-warp mitigation: **approved enabled from genesis**, subject to exact-head C++ and functional regression tests. The parameter manifest must state `bip94_enabled: true`.
- Production retarget policy: **approved** — 600-second target spacing, 2,016-block interval, 1,209,600-second target timespan, previous-period ancestry semantics, 1/4–4x elapsed-time clamp, minimum-difficulty disabled and no-retargeting disabled.
- Monetary policy: 50 FLY initial subsidy, 210,000-block halvings, integer base-unit arithmetic, 21m hard ceiling, no premine/founder allocation/ICO.

### 17.2 Still blocked pending owner approval

The following implementation/launch gates remain; do not confuse them with unapproved parameter choices:
- Generate and independently verify the genesis transaction ID, Merkle root, nonce and block hash.
- Implement the approved network magic/ports/address prefixes/HRP in the dedicated C++ parameter object and network dispatch.
- Verify the approved script activation matrix against pinned v32.1 and add exact-head C++/functional tests.
- Decide separately whether a public test-chain identity is needed; no public testnet/mainnet or launch settings are authorized.

The approved candidate values are final parameter selections for implementation. Derived genesis outputs still require deterministic generation and independent verification; this approval does not activate or launch the production chain.

### 17.3 Canonical source-of-truth documents and branches

The reconciled documentation workstream uses these ownership rules:

| Subject | Canonical source |
|---|---|
| Detailed consensus rules, owner decisions and issuance verification | `freely/consensus-specification` — PR #2 |
| Detailed chain-selection source audit | Updated `FREELY-CHAIN-SELECTION-AUDIT.md` from PR #3 |
| Architecture contract, integration map and acceptance matrix | This document, incorporating the detailed architecture sections from PR #7 |
| Network identity and genesis candidate registry | `FREELY-NETWORK-PARAMETERS-DRAFT.md` on PR #2 |
| Executable subsidy checker and candidate generators | PR #2 scripts and focused specification workflow |
| Runtime selector implementation | PR #8, currently fail-closed |
| Wallet/node readiness | PR #11, based on current PR #8 head |

The older overlapping copies in PR #7 are not independent competing consensus authorities. This reconciled branch carries the latest consensus specification and parameter draft from PR #2, the current selector audit from PR #3, and preserves the architecture-specific integration and acceptance material from PR #7.

### 17.4 Current implementation facts

- PR #8 currently has the canonical FREELY enum, parser/serializer, help entry and explicit fail-closed base/consensus factory cases.
- PR #8 does not yet contain a FREELY parameter class, approved magic mapping, production genesis or runtime chain.
- The source-level audit has verified the missing FREELY `GetNetworkForMagic` mapping and the requirement to explicitly mark the eventual FREELY parameter object as production.
- PR #11 has been refreshed against the current PR #8 head; its wallet and node workflow remains queued/unverified.
- PR #1's M1 focused test workflow command was repaired. Its exact-head focused and inherited CI runs remain queued; no current-head test pass is claimed.
- PR #10's Python preflight has expanded regression coverage, but its latest exact-head workflow remains queued; no pass is claimed.

### 17.5 Integration and release boundary

A documentation reconciliation does not authorize activation. Keep FREELY startup fail-closed until all blocked production values are approved, implemented and tested. Do not reuse Bitcoin mainnet history, seeds, chainwork, AssumeUTXO snapshots, genesis, activation exceptions or network identifiers. Do not expose public RPC/P2P, deploy miners, publish a testnet or launch mainnet without the separate approvals already required by the project.

**Reconciliation status:** the approved policy and source-of-truth ownership are now explicit. Runtime implementation, current-head CI, security review and network activation remain separate incomplete phases.


## 17. Owner-approved parameter baseline — 18 November 2026

The four protocol proposal areas are approved. The authoritative values are recorded in [FREELY-APPROVED-PROTOCOL-PARAMETERS.md](FREELY-APPROVED-PROTOCOL-PARAMETERS.md). The approved identity is magic `fa c3 b7 d1`, P2P/RPC `49444/49445`, data directory `freely`, Base58 `55/117/183`, extended-key versions `04464c59/04666c79`, and Bech32 HRP `fly`. Approved PoW values are SHA-256d, powLimit `00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff`, genesis nBits `0x1d00ffff`, 600-second spacing, 2,016-block interval, 14-day timespan, 1/4–4x clamp, minimum difficulty disabled, no-retargeting disabled and BIP94 enabled from genesis.

The approved genesis candidate uses timestamp 1,794,960,000, version 1, coinbase message `FREELY FLY genesis 2026-11-18`, and a 50 FLY permanently unspendable OP_RETURN output. The nonce and final block hash remain derived and unverified. Script activation is height 1 for BIP34, BIP65, BIP66, CSV and SegWit; Taproot/witness-v1 must follow the v32.1 script-flag architecture; TESTDUMMY remains NEVER_ACTIVE.

This approval resolves parameter-selection gates but not implementation, C++ validation, independent security review or release readiness. The current runtime selector deliberately fails closed; there is still no complete FREELY `CChainParams` object, genesis commitment, network-magic dispatch integration or production/test functional validation. No public network or deployment is authorized.
