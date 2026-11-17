# FREELY retarget implementation — deterministic test vectors

**Status:** engineering test contract; not runtime consensus code  
**Created:** 16 November 2026  
**Pinned source:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`  
**Branch:** `freely/retarget-test-vectors`  
**Policy:** owner-approved production retarget policy, 16 November 2026

## Purpose and scope

These vectors translate the approved production retarget policy into deterministic expected values for tests of Bitcoin Core v32.1 `CalculateNextWorkRequired`. They use a deliberately synthetic, self-contained parameter set so the arithmetic can be tested before FREELY's production `powLimit`, genesis `nBits` and genesis block are chosen.

**The synthetic values below are not proposed FREELY production parameters.** They must not be copied into a FREELY chain-parameter object or used to mine/deploy a network.

## Fixed policy inputs

| Parameter | Test value | Meaning |
|---|---:|---|
| Target spacing | 600 seconds | Approved |
| Retarget interval | 2,016 blocks | Approved |
| Target timespan | 1,209,600 seconds | 2,016 × 600 |
| Lower clamp | 302,400 seconds | Target timespan / 4 |
| Upper clamp | 4,838,400 seconds | Target timespan × 4 |
| Minimum-difficulty exception | Disabled | Approved for production |
| No-retargeting | Disabled | Approved for production |
| BIP94 | Disabled in this synthetic test | Still an unresolved FREELY owner decision |
| Synthetic powLimit | compact `0x207fffff` | Test-only |
| Synthetic previous `nBits` | `0x1f7fffff` | Test-only |

## Exact expected vectors

The v32.1 algorithm calculates:

1. `actual_timespan = last_block_time - first_block_time`.
2. Clamp it to [302,400, 4,838,400].
3. Decode previous `nBits = 0x1f7fffff` into the integer target.
4. Multiply the target by the clamped timespan.
5. Divide by 1,209,600 using integer arithmetic.
6. Cap at synthetic `powLimit = 0x207fffff`.
7. Encode the result using Bitcoin compact-target encoding.

| Case | Supplied elapsed seconds | Clamped seconds | Expected compact `nBits` |
|---|---:|---:|---:|
| Just below lower clamp | 302,399 | 302,400 | `0x1f1fffff` |
| Exactly lower clamp | 302,400 | 302,400 | `0x1f1fffff` |
| Normal target period | 1,209,600 | 1,209,600 | `0x1f7fffff` |
| Exactly upper clamp | 4,838,400 | 4,838,400 | `0x2001ffff` |
| Just above upper clamp | 4,838,401 | 4,838,400 | `0x2001ffff` |

These outputs were independently calculated using integer arithmetic and compact-target encode/decode logic. They are fixed regression expectations, not values recomputed by calling the C++ function under test.

## Required C++ regression coverage

Add tests in `src/test/pow_tests.cpp` (or a dedicated FREELY test file after chain type integration) that:

- Construct `Consensus::Params` explicitly; do not obtain or mutate Bitcoin MAIN parameters as a proxy for FREELY.
- Set the synthetic target timespan, target spacing, synthetic powLimit, `fPowNoRetargeting=false`, `fPowAllowMinDifficultyBlocks=false`, and `enforce_BIP94=false`.
- Set `CBlockIndex::nBits` to `0x1f7fffff` and use first/last timestamps whose differences match each vector.
- Assert exact equality with every expected compact `nBits` value above.
- Test the one-second-below and one-second-above clamp cases to catch off-by-one errors.
- Verify that when no-retargeting is enabled in a separate test-only parameter instance, `CalculateNextWorkRequired` returns the prior `nBits` unchanged; this is a generic upstream algorithm test, not a FREELY production setting.
- Verify that a non-boundary production height with minimum difficulty disabled carries forward the previous block's `nBits` through `GetNextWorkRequired`.
- Test boundary selection separately with a linked `CBlockIndex` ancestry so the first retarget uses the correct period-start timestamp (height 0) and last-block timestamp (height 2015) for the block at height 2016.
- Test compact-target negative, zero, overflow and above-powLimit rejection using the existing `DeriveTarget` / `CheckProofOfWork` interfaces.
- Keep BIP94-specific expected vectors separate and do not mark them FREELY requirements until the owner decides whether to adopt BIP94.

## Boundary-height interpretation

For a 2,016-block period, the first retarget is calculated for candidate block height 2,016. The preceding tip is height 2,015. Under the v32.1 non-BIP94 path, the first timestamp is taken from ancestor height:

`2015 - (2016 - 1) = 0`.

The measured interval is therefore the timestamp difference between blocks 0 and 2,015, not a fabricated timestamp at height 2,016. The same period-start selection repeats at later retarget boundaries.


## Additional executable regression coverage

The C++ test suite now supplements the five arithmetic vectors with:

- A linked 2,016-block ancestry fixture that calls `GetNextWorkRequired` at candidate height 2,016 and proves the first timestamp comes from ancestor height 0. Its timestamp arrangement makes an off-by-one choice of height 1 produce a different compact target.
- A non-retarget boundary test confirming that, with minimum-difficulty blocks disabled, the prior compact target is carried forward unchanged.
- Direct `DeriveTarget` rejection tests for negative, zero, overflowing and above-`powLimit` compact targets, alongside a valid target.

All target limits and compact values in these tests remain synthetic fixtures. They exercise the upstream PoW machinery and approved retarget arithmetic without choosing FREELY's production `powLimit`, genesis `nBits`, or BIP94 policy.

## Executable independent arithmetic checker

The repository now includes `contrib/freely/check_retarget_vectors.py`, a standard-library-only Python checker that independently decodes and encodes compact targets using integer arithmetic. It verifies all five clamp/scaling vectors and the height-2,016 ancestor-selection trap.

Run it with:

```sh
python3 contrib/freely/check_retarget_vectors.py
```

The focused GitHub Actions workflow runs this checker before configuring and compiling the C++ unit-test executable. A successful script run is useful arithmetic validation, but it does not replace the C++ build or `pow_tests` result.

## Safety and integration gates

- These vectors test the approved clamp/scaling policy and upstream algorithm semantics only.
- They do not select a production `powLimit`, genesis `nBits`, nonce, genesis hash, network magic or ports.
- They do not resolve BIP94/time-warp mitigation or timestamp/MTP policy.
- No production chain parameter may be activated from the synthetic fixture.
- Before merging a C++ test PR: run targeted `pow_tests`, `validation_tests`, relevant full unit/functional suites, and current-head CI; inspect all failures.
- Before runtime activation: require frozen production parameters, independent vector review and the standing PR merge gates.

## Independent arithmetic check

For synthetic previous target `T = decode_compact(0x1f7fffff)`, the unrounded mathematical target before compact encoding is:

- Lower clamp: `T × 302400 / 1209600 = T / 4`.
- Normal period: `T × 1209600 / 1209600 = T`.
- Upper clamp: `T × 4838400 / 1209600 = 4T`.

The compact encodings in the table include the expected truncation/normalization of Bitcoin's compact target format. Test assertions must compare the encoded 32-bit values exactly.

## Next implementation step

Implement these deterministic fixtures as C++ regression tests on a dedicated branch, run the focused PoW test suite, and open a draft PR. Keep this work separate from the monitored M1 branch and do not introduce any FREELY production parameter values.
