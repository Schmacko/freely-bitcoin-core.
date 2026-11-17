# FREELY chain-selection and consensus integration audit

- **Date:** 16 November 2026
- **Source:** Bitcoin Core v32.1 fork, branch `freely/m1-consensus`
- **Pinned upstream:** `f0de87f040621468b956f01f526a43a010310501`
- **Status:** static source audit; no runtime code changes in this document.

## Executive result

The fork contains explicit production/test classification scaffolding. PR #8 now adds `ChainType::FREELY`, canonical name parsing/serialization and help registration, plus fail-closed guards in the base-parameter and consensus-parameter factories. The public startup selectors are covered by regression-test code and deliberately throw before global chain/config parameters can be selected. A FREELY parameter object, production network identity and genesis are still absent. This is selector scaffolding, not a runnable node; the remaining work spans base parameters, consensus, kernel parameters, network identity, genesis and tests.

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
- The height-zero subsidy is mathematically part of scheduled issuance, but the conventional genesis coinbase output is unspendable. The project must decide and document whether genesis has a reward output and how spendable supply is reported.

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
1. Decide timestamp/message and coinbase output script, including whether a reward output is included.
2. Decide genesis version, time, PoW limit and compact `nBits`.
3. Generate nonce and block hash with the real serialization/hash code.
4. Independently recompute txid, Merkle root, header hash and target comparison.
5. Assert the exact values in tests.
6. Ensure FREELY genesis is not Bitcoin's genesis and cannot be confused with another network.
7. Do not invent or hard-code a nonce/hash/Merkle root before the generation and independent verification steps.

## 6. Network identity

Candidate values in the parameter draft are not approved. Before use, verify:
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
