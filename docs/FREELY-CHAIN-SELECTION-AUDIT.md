# FREELY chain-selection and consensus integration audit

**Date:** 16 November 2026
**Source:** Bitcoin Core v32.1 fork, branch `freely/m1-consensus`
**Pinned upstream:** `f0de87f040621468b956f01f526a43a010310501`
**Status:** static source audit; no runtime code changes in this document.

## Executive result

The fork contains explicit production/test classification scaffolding. PR #8 now adds `ChainType::FREELY`, canonical name parsing/serialization and help registration, plus fail-closed guards in the base-parameter and consensus-parameter factories. The public startup selectors are covered by regression-test code and deliberately throw before global chain/config parameters can be selected. The owner has now approved the production network identity and consensus parameter baseline, but a FREELY parameter object and verified genesis commitment are still absent. This is selector scaffolding, not a runnable node; remaining work spans kernel parameters, network-magic dispatch, genesis integration and tests.

## 1. Chain selector integration points

| File | Existing integration | Required FREELY work |
|---|---|---|
| `src/util/chaintype.h` | `ChainType::FREELY` is now present (PR #8) | Selector enum is implemented; retain exhaustive handling and compile/test verification |
| `src/util/chaintype.cpp` | Canonical `freely` parser/serializer mapping is present (PR #8) | Preserve exact round-trip and noncanonical-name rejection tests |
| `src/chainparamsbase.h` | `LIST_CHAIN_NAMES` now advertises `freely` (PR #8) | Keep the advertised selector fail-closed until approved base parameters exist |
| `src/chainparamsbase.cpp` | `CreateBaseChainParams(FREELY)` deliberately throws (PR #8) | Replace the guard only with a reviewed unique data-dir suffix and approved RPC port |
| `src/chainparams.cpp` | `CreateChainParams(FREELY)` deliberately throws (PR #8) | Add a dedicated FREELY factory only after consensus and identity decisions are approved; never route through MAIN/TESTNET |
| `src/kernel/chainparams.h` | No FREELY parameter class or production instance exists | Add a dedicated class with explicit production classification after the blocked values are approved |
| `src/kernel/chainparams.cpp` | No FREELY class, magic, genesis, seeds or address prefixes are assigned | Add an isolated FREELY class without copying Bitcoin mainnet identity or history assumptions |

The selector is not complete until CLI parsing, config-section selection, base datadir/RPC parameters, full chain-parameter construction and RPC-reported chain name all agree.

## 2. Production/test safety

The fork currently has:
- `CChainParams::IsTestChain()` backed by explicit `m_is_test_chain`, default false.
- `CChainParams::IsProductionChain()` backed by explicit `m_is_production_chain`, default false.
- Existing Bitcoin MAIN sets production true.
- Existing Bitcoin testnet, testnet4, signet and regtest set test-chain true.
- `src/init.cpp` rejects `-testactivationheight` and `-vbparams` whenever `IsProductionChain()` is true.

Required for FREELY:
1. Set `m_is_production_chain = true` in the FREELY production parameter constructor.
2. Leave `m_is_test_chain = false`.
3. Add tests asserting FREELY is production and not a test chain.
4. Verify both test-only activation overrides fail on FREELY.
5. Keep regtest-only `-test=<option>` handling restricted to regtest.
6. Test all existing Bitcoin chain classifications remain unchanged.

Do not make production status depend on an implicit "not test" default. The two classifications are separate security properties.

## 3. Monetary policy and amount range

Source audit findings:
- `src/consensus/amount.h` defines `CAmount` in integer base units, `COIN = 100,000,000`, `MAX_MONEY = 21,000,000 * COIN` and `MoneyRange`.
- FREELY's agreed 8 decimals and 21m hard ceiling match these existing constants. No change to `COIN` or `MAX_MONEY` is currently indicated.
- `src/validation.cpp` implements `GetBlockSubsidy(height, consensusParams)` using `50 * COIN` and `nSubsidyHalvingInterval`, with a zero guard at 64 halvings.
- Coinbase reward validation compares total coinbase output against fees plus the subsidy returned by that function.

Implications:
- FREELY must set `nSubsidyHalvingInterval = 210000` in its own consensus params.
- The current 50-coin initial subsidy already matches the agreed policy; do not add a redundant fork-specific subsidy implementation without a reason.
- Tests must call the actual subsidy function with FREELY params and check the full boundary vectors and cumulative integer issuance.
- Audit all `MAX_MONEY` / `MoneyRange` uses and wallet/RPC amount serialization before changing denomination or range constants.
- Owner-approved accounting (17 November 2026): the height-zero 50 FLY subsidy remains included in scheduled issuance, while the genesis coinbase is permanently unspendable and excluded from spendable supply. The current candidate generator models a 50 FLY OP_RETURN output; its exact transaction and header commitment remain candidate-only until final genesis parameters are approved.

## 4. Consensus parameters that must be explicitly set

`Consensus::Params` contains fields that must be reviewed for a production chain:
- genesis hash;
- subsidy halving interval;
- script-flag exceptions;
- buried activation heights and associated BIP34 hash;
- minimum BIP9 warning height;
- each version-bits deployment's bit, start, timeout, period, threshold and minimum activation height;
- proof-of-work limit;
- minimum-difficulty policy;
- BIP94/time-warp mitigation;
- no-retargeting flag;
- target spacing and target timespan;
- minimum chainwork and assume-valid;
- signet fields (must be disabled for FREELY).

Do not inherit Bitcoin MAIN values by copying the constructor. In particular, Bitcoin's activation heights/hashes, script exceptions, mainnet powLimit, chainwork, assume-valid, genesis, seed data and AssumeUTXO snapshots are tied to Bitcoin's history and must not be carried over as if they applied to FREELY.

For an initial independent chain, unsupported AssumeUTXO, assume-valid, minimum-chainwork and checkpoint shortcuts should remain absent/neutral until valid FREELY history exists and the security implications are reviewed.

## 5. Genesis construction

The current kernel source has a helper that builds the genesis coinbase and Merkle root. Its default timestamp and output key are Bitcoin's historical message/key. The source comment also documents the genesis output as unspendable because it was never inserted into the UTXO database.

Required steps:
1. Finalise the timestamp/message and verify the candidate coinbase serialization against the owner-approved unspendable-genesis rule; do not make the genesis reward spendable.
2. Decide genesis version, time, PoW limit and compact `nBits`.
3. Generate nonce and block hash with the real serialization/hash code.
4. Independently recompute txid, Merkle root, header hash and target comparison.
5. Assert the exact values in tests.
6. Ensure FREELY genesis is not Bitcoin's genesis and cannot be confused with another network.
7. Do not invent or hard-code a nonce/hash/Merkle root before the generation and independent verification steps.

## 6. Network identity

The earlier draft candidates were superseded by the owner-approved baseline. Before runtime use, verify the approved values against source and test vectors:
- 4-byte P2P message-start collision resistance and encoding;
- P2P, RPC and Tor port availability/collision;
- data-directory suffix and config-section name;
- Base58 address and WIF prefix collision risk;
- BIP32 public/private version uniqueness and wallet compatibility;
- Bech32/Bech32m HRP uniqueness;
- peer magic mapping and network isolation;
- no Bitcoin DNS/fixed seeds or peer databases reused.

The network identity should be frozen as one versioned sheet and tested as a set, not selected field-by-field during implementation.

## 7. Test plan before enabling `-chain=freely`

### Selector and startup
- parse `-chain=freely`;
- round-trip `ChainTypeToString` / `ChainTypeFromString`;
- help text lists FREELY only after factory exists;
- base data directory and RPC port are unique;
- startup reports FREELY chain name;
- production overrides `-testactivationheight` and `-vbparams` are rejected;
- regtest debug overrides remain regtest-only.

### Chain identity
- exact message-start bytes and `GetNetworkForMagic` mapping;
- no collisions with all existing Bitcoin chain types;
- Base58, WIF, BIP32 and Bech32/Bech32m round-trip vectors;
- separate data directory and peer isolation.

### Consensus/genesis
- exact genesis header, txid, Merkle root and hash;
- genesis PoW meets the approved limit;
- subsidy boundary and cumulative issuance;
- coinbase overpayment rejected;
- retarget boundaries, clamping and timestamp rules;
- all active script/deployment rules and invalid-block vectors.

### Regression
- unchanged Bitcoin mainnet, testnet, testnet4, signet and regtest tests;
- all existing upstream validation tests;
- targeted FREELY tests;
- full functional tests and platform CI.

## 8. Safe implementation sequence

1. Finish the current CI verification on the current M1 PR head; avoid changing that head while its workflows run.
2. Resolve the consensus decisions and freeze a reviewed parameter sheet.
3. Extend PR #8's fail-closed selector with approved base parameters; keep the factory throwing until the required identity fields are reviewed.
4. Implement the FREELY parameter factory with explicit production classification and no genesis shortcuts.
5. Add chain-selection and startup guard tests.
6. Implement the approved genesis and identity, then exact tests.
7. Implement/enable the final consensus settings and all edge-case tests.
8. Build node, CLI and wallet; run full tests and private multi-node network.
9. Obtain independent review before any public-network proposal.

## 9. Current audit conclusion

**Safe to prepare now:** completion of the base-parameter/factory design, startup guard tests, the acceptance matrix and the decision sheet for unresolved fields. The selector enum, parser/serializer, help registration and fail-closed factory guards are already present in PR #8.

**Not safe to activate yet:** a FREELY parameter object, network magic, ports, address prefixes, genesis, PoW limit, activation heights, minimum chainwork, assume-valid, seeds or any public network.

No code changes or network launch are authorised by this audit.

## 10. M1 integration reconciliation and audit closure — 16 November 2026

The M1 production/test-classification work has been checked against the architecture contract and the current M1 branch source.

### Verified on the M1 branch

- IsTestChain() reads the explicit m_is_test_chain member.
- IsProductionChain() reads the explicit m_is_production_chain member.
- Bitcoin MAIN is explicitly marked production.
- TESTNET, TESTNET4, SIGNET and REGTEST are explicitly marked test chains.
- src/init.cpp rejects -testactivationheight and -vbparams when IsProductionChain() is true.
- -test=<option> remains REGTEST-only.
- The REGTEST-only stale-fee-estimate exception remains scoped to REGTEST.
- PR #8 now supplies the FREELY chain enum, canonical parser/serializer and help entry; both parameter factories still fail closed, and no FREELY parameter object or runtime network identity exists.

### Chain-selection integration call-site checklist

- [x] src/util/chaintype.h/.cpp: `ChainType::FREELY` and canonical string mapping added in PR #8.
- [x] src/chainparamsbase.h/.cpp: `freely` help entry and fail-closed base factory guard added in PR #8.
- [x] src/chainparams.cpp: fail-closed FREELY parameter-factory guard added in PR #8.
- [x] src/test/chaintype_tests.cpp: selector-entrypoint fail-closed regression test added; current-head C++ execution is pending.
- [x] src/kernel/chainparams.h/.cpp: kernel parameter class, classification and magic lookup integration points identified.
- [x] src/init.cpp: startup setup, production overrides, REGTEST-only options and stale-fee-estimate guard inspected.
- [x] Existing Bitcoin chain classification invariants and required regression coverage specified.
- [x] Identity, genesis, deployment and history-dependent fields explicitly blocked until approved.
- [ ] Current-head C++ compilation and test confirmation.
- [ ] Runtime FREELY parameter object and network-isolation tests.
- [ ] Full wallet/RPC/GUI/networking call-site regression after implementation.

### Audit conclusion

The static chain-selection audit and implementation hand-off are complete. The remaining unchecked items are runtime implementation and integration tests, not missing audit documentation. This branch is therefore **100% complete as a static audit deliverable**, while FREELY runtime chain selection remains unimplemented and must be tracked in the core implementation roadmap.

No candidate identity value, genesis field, port, magic, address prefix, PoW limit or activation height is approved by this audit.

## 11. Direct source verification follow-up — 18 November 2026

The following call sites were re-opened on the current PR #8 implementation branch at head `5f8fa282ea0675c41c2a5aa21db36d5e1bf47744`. This supplements the earlier static audit with direct source verification.

### Verified selector and network-magic behavior

- `src/chainparamsbase.cpp`: `CreateBaseChainParams` has an explicit `ChainType::FREELY` case that throws. There is no fallback to MAIN.
- `src/chainparams.cpp`: `CreateChainParams` has an explicit `ChainType::FREELY` case that throws. There is no fallback to MAIN.
- `src/kernel/chainparams.cpp`: `GetNetworkForMagic` currently obtains and compares only MAIN, TESTNET, TESTNET4, REGTEST and SIGNET message-start values. It has no FREELY case because no FREELY message magic or parameter object exists yet.
- The FREELY mapping must be added to `GetNetworkForMagic` in the same reviewed change that introduces the approved FREELY message magic. Add a positive FREELY mapping test and negative collision/unknown-magic tests; do not insert a provisional magic value now.
- The current signet magic is derived from its challenge at runtime. A future FREELY collision test must use the actual approved FREELY magic and compare against the configured signet challenge, not a guessed constant.

### Verified production/test classification defaults

- `src/kernel/chainparams.h`: `m_is_test_chain` and `m_is_production_chain` both default to false. Production status is therefore not inferred from the absence of test status.
- `src/kernel/chainparams.cpp`: MAIN explicitly sets `m_is_production_chain = true`; TESTNET, TESTNET4, SIGNET and REGTEST explicitly set `m_is_test_chain = true`.
- No FREELY parameter constructor exists, so FREELY is not yet classified at runtime. Its future production constructor must explicitly set `m_is_production_chain = true` and explicitly preserve `m_is_test_chain = false`. Add a test that asserts both properties.
- `src/init.cpp`: `-testactivationheight` and `-vbparams` are rejected whenever `IsProductionChain()` is true. The generic `-test=<option>` override remains restricted to `ChainType::REGTEST`, and stale fee-estimate acceptance is also restricted to REGTEST.

### Mainnet assumptions and safe interpretation

- The `ChainType::MAIN` references used to construct default startup/help parameters are explicit Bitcoin defaults, not FREELY selection fallbacks. They must remain the defaults unless a separate product decision changes the default chain; FREELY must always be selected explicitly.
- The chain-parameter factories are exhaustive for the currently declared chain types and explicitly reject FREELY. Preserve this fail-closed behavior until the complete FREELY parameter set is reviewed.
- The kernel's MAIN constructor contains Bitcoin-history-specific script exceptions, activation heights/hashes, genesis, proof-of-work limit, chainwork/assume-valid, seeds, AssumeUTXO data and transaction-history estimates. These must not be inherited by a FREELY constructor.
- The audit has not established that every `ChainType::MAIN` comparison across every source file is harmless. Before enabling FREELY, perform a repository-wide source search on the exact integration commit and review each occurrence in networking, RPC, wallet, GUI, tests and initialization. In particular, avoid changing a MAIN-only behavior to a broad non-test/production behavior without checking whether it is Bitcoin-specific.

### Integration acceptance checklist

- [x] Base-parameter factory has an explicit fail-closed FREELY case.
- [x] Consensus-parameter factory has an explicit fail-closed FREELY case.
- [x] Current network-magic mapping and missing FREELY mapping identified.
- [x] Production/test classification defaults and explicit assignments verified.
- [x] Production startup override guards and REGTEST-only overrides verified.
- [ ] Repository-wide `ChainType::MAIN` call-site audit on the final integration commit.
- [ ] FREELY production/test classification regression test after parameter class exists.
- [ ] FREELY magic mapping and collision regression tests after magic is approved.
- [ ] Current-head C++ tests pass.

**Conclusion:** the reviewed selector paths fail closed rather than silently selecting Bitcoin MAIN. The main remaining selector integration gaps are the deliberately absent FREELY parameter class, network-magic registration and repository-wide call-site verification on the final integration commit. No production identity value is selected by this audit.


## 12. Owner-approved identity and consensus values — 18 November 2026

The approved exact values are maintained in [FREELY-APPROVED-PROTOCOL-PARAMETERS.md](FREELY-APPROVED-PROTOCOL-PARAMETERS.md). The approved network magic is `fa c3 b7 d1`; P2P/RPC ports are 49444/49445; Base58 prefixes are 55/117/183; extended-key versions are `04464c59/04666c79`; and Bech32 HRP is `fly`. PoW and genesis values are also approved as recorded in that baseline.

This audit's source finding remains unchanged: `GetNetworkForMagic` does not yet map FREELY, and the full FREELY consensus factory still throws. The next implementation must add the approved magic to kernel network lookup, test collisions against every built-in network including configured signet, instantiate a dedicated production parameter object, and retain fail-closed startup until the derived genesis nonce/hash and full regression evidence are verified. No Bitcoin MAIN historical checkpoints, assume-valid values, chainwork or activation exceptions may be copied.
