# FREELY proof-of-work and difficulty-adjustment source audit

**Date:** 16 November 2026  
**Source baseline:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`  
**Branch:** `freely/pow-difficulty-audit`  
**Status:** documentation-only source audit; no runtime code changes and no consensus parameters selected.

## 1. Executive result

Bitcoin Core v32.1 already provides the core SHA-256d proof-of-work validation and retarget machinery needed as an implementation starting point. FREELY does not need a new hashing algorithm or a replacement difficulty engine merely to use 600-second target spacing and a 2,016-block adjustment interval.

However, the interval and spacing alone do not define a complete consensus rule. FREELY must explicitly freeze the proof-of-work limit, genesis compact target, retarget semantics, timestamp rules, minimum-difficulty policy, BIP94/time-warp mitigation, and all boundary/error cases. Reusing upstream code is not the same as reusing Bitcoin mainnet parameters or inheriting Bitcoin's security.

## 2. Exact upstream implementation map

### `src/consensus/params.h`

The consensus parameter structure includes:
- `powLimit`;
- `fPowAllowMinDifficultyBlocks`;
- `enforce_BIP94`;
- `fPowNoRetargeting`;
- `nPowTargetSpacing`;
- `nPowTargetTimespan`;
- `DifficultyAdjustmentInterval()`, calculated as integer division of target timespan by target spacing.

For FREELY's agreed values:
- target spacing = 600 seconds;
- target timespan = 2,016 × 600 = 1,209,600 seconds;
- the resulting interval is exactly 2,016.

**Required invariant:** target timespan must be a positive exact multiple of target spacing, and the derived interval must equal the approved 2,016. Add a chain-parameter sanity test so accidental integer truncation cannot silently change the interval.

### `src/pow.cpp`: `GetNextWorkRequired`

The upstream algorithm:
1. Derives the compact proof-of-work limit from `params.powLimit`.
2. If the next block is not at an adjustment boundary, normally returns the previous block's `nBits`.
3. If minimum-difficulty blocks are enabled, a block arriving more than twice the target spacing after its predecessor may use the PoW limit; subsequent blocks walk backward over special minimum-difficulty blocks to recover the last non-special target.
4. At an adjustment boundary, selects the first block of the preceding difficulty period using height `last_height - (interval - 1)`.
5. Calls `CalculateNextWorkRequired` using the last block time and first block time.

For an interval of 2,016, the first adjustment for a chain starting at height zero occurs when constructing block 2,016, using the timestamps of blocks 2,015 and 0.

### `src/pow.cpp`: `CalculateNextWorkRequired`

The upstream algorithm:
1. Returns the previous target unchanged if `fPowNoRetargeting` is enabled.
2. Calculates actual timespan as last-block timestamp minus first-block timestamp.
3. Clamps actual timespan to one quarter through four times the target timespan.
4. Uses the previous block's compact target as the starting target, except when `enforce_BIP94` is enabled; then it uses the first block's target in the period.
5. Multiplies the target by actual timespan, divides by target timespan using integer arithmetic, clamps to `powLimit`, and serializes back to compact `nBits`.

With FREELY's 14-day target timespan, the ordinary clamp range would be 3.5 to 56 days. This is a direct consequence of the upstream factor-of-four rule, not a separate FREELY decision.

The BIP94 path preserves the period-start difficulty instead of allowing a minimum-difficulty exception at the end of a period to distort the next retarget. The exact policy and activation must be deliberately selected for FREELY; it must not be assumed from the 600-second/2,016-block values.

### `src/pow.cpp`: target decoding and proof-of-work validation

`DeriveTarget` rejects compact targets that are negative, zero, overflow the target representation, or exceed `powLimit`. `CheckProofOfWorkImpl` then rejects a block hash numerically greater than the decoded target.

The production chain must use the normal proof-of-work check. The simplified check in `CheckProofOfWork` is a fuzz-determinism facility and is not a production consensus mode.

### `src/pow.cpp`: `PermittedDifficultyTransition`

This helper checks that a retarget does not move beyond the permitted factor-of-four range and that non-boundary blocks retain the expected target. It returns true immediately when minimum-difficulty blocks are enabled. Tests must therefore exercise the production policy with minimum difficulty disabled if that is the selected FREELY rule.

This helper is useful for header-sync plausibility checks and regression tests; it does not replace full block proof-of-work validation.

## 3. Consensus decisions that remain open

The following values or policies are not determined by the agreed 600-second spacing and 2,016-block interval:

| Parameter / policy | Current state | Why it must be frozen |
|---|---|---|
| `powLimit` | Open | Sets the easiest valid target and maximum target-derived block work |
| Genesis `nBits` | Open | Must be valid under the selected `powLimit` and genesis hash |
| First retarget boundary | Upstream behaviour understood; FREELY tests pending | Off-by-one errors create permanent chain divergence |
| Factor-of-four clamp | Upstream default behaviour; owner confirmation pending | Changes valid block targets |
| Minimum-difficulty blocks | Open; recommendation is disabled on production | Permitting them can enable easy-block manipulation and recovery edge cases |
| No-retargeting | Open; recommendation is disabled on production | A production chain with no retargeting can become unstable as hash rate changes |
| BIP94 | Open; merits adoption review | Changes the target source used at retarget and mitigates a time-warp vector |
| Timestamp constraints / MTP | Preserve upstream unless a deliberate change is specified | Timestamp validity is consensus-critical and interacts with difficulty |
| Compact target edge cases | Upstream implementation identified; FREELY vectors pending | Negative, zero, overflow and over-limit values must be rejected |
| Genesis proof of work | Open until genesis parameters are frozen | A guessed nonce/hash cannot be treated as a valid genesis commitment |

No Bitcoin mainnet `powLimit`, genesis `nBits`, activation height, chainwork assumption, checkpoint, or timestamp exception should be copied without an explicit chain-specific justification.

## 4. Recommended implementation policy for review

These are engineering recommendations, not approved consensus decisions:

1. Preserve the v32.1 proof-of-work and retarget implementation initially; avoid an unnecessary fork of the algorithm.
2. Set FREELY's target spacing and timespan explicitly to 600 and 1,209,600 seconds.
3. Disable minimum-difficulty blocks on the FREELY production chain.
4. Disable no-retargeting on the FREELY production chain.
5. Evaluate enabling BIP94 from genesis, after checking all affected code paths and tests against the intended security model.
6. Select `powLimit` and genesis `nBits` together, based on the intended initial mining model and a realistic security analysis. A very easy target may make initial block production convenient but does not provide meaningful economic security.
7. Preserve upstream timestamp and median-time-past rules unless a documented, tested reason requires a change.
8. Keep regtest-only shortcuts isolated from FREELY production parameters.

The project must not select an arbitrary target merely to make local mining easy. A private regtest can provide convenient development mining without weakening production consensus parameters.

## 5. Required FREELY test matrix

### Parameter sanity
- target spacing is exactly 600 seconds;
- target timespan is exactly 1,209,600 seconds;
- derived difficulty interval is exactly 2,016;
- target timespan is divisible by target spacing with no remainder;
- `powLimit` is non-zero and its compact representation is valid;
- genesis `nBits` is positive, non-zero, non-overflowing and no easier than the approved `powLimit`;
- retarget arithmetic cannot overflow its 256-bit intermediate under the selected parameter bounds.

### Retarget boundaries
- blocks 1 through 2,015 preserve the prior target under production policy;
- block 2,016 calculates the first retarget from blocks 0 and 2,015;
- test exact target results for timespans below, at and above the lower clamp;
- test exact target results below, at and above the upper clamp;
- test integer division/rounding and compact encoding at boundary values;
- repeat for later periods, including unusual timestamps and changing prior targets.

### Minimum difficulty and BIP94
- production FREELY does not accept the minimum-difficulty exception if disabled;
- test a timestamp more than 2 × spacing after the previous block;
- test target recovery after a sequence of easy blocks on a test-only chain;
- if BIP94 is enabled, prove that retarget uses the period-start target and add vectors where the final block has a special minimum target;
- verify no test-only difficulty flags leak into production.

### Target and PoW validation
- valid target at the limit;
- zero target rejected;
- negative compact target rejected;
- compact overflow rejected;
- target above `powLimit` rejected;
- hash equal to target accepted by the established comparison semantics;
- hash above target rejected;
- malformed genesis `nBits` rejected by sanity checks.

### Regression and integration
- existing Bitcoin MAIN, TESTNET, TESTNET4, SIGNET and REGTEST PoW tests remain unchanged;
- FREELY parameter sanity test added once chain parameters exist;
- FREELY-specific retarget vectors are independently calculated and reviewed;
- targeted `pow_tests` and full validation tests pass;
- full upstream functional suite and platform CI pass;
- private multi-node nodes agree on identical block validity and retarget boundaries.

## 6. Suggested source-level implementation sequence

1. Keep the current monitored M1 PR head unchanged until its CI has terminal results.
2. Resolve and record the PoW owner decisions in the consensus decision register.
3. Add FREELY-specific parameter construction only after chain identity and genesis parameters are frozen.
4. Add parameter sanity assertions and FREELY PoW unit tests.
5. Reuse upstream algorithm unless a specifically approved consensus change is required.
6. Run targeted PoW tests, validation tests and full platform CI.
7. Only after genesis and network identity are frozen, test a private isolated multi-node chain.

## 7. Security interpretation

SHA-256d compatibility does not confer Bitcoin's hash rate, mining economics, decentralization, or attack resistance. With insufficient independent hash power, an otherwise correct implementation can still be reorganized or attacked. A low initial target is not a substitute for a credible security model.

A private development network is suitable for engineering validation. It is not evidence that a public production network is secure.

## 8. Source references

- `src/consensus/params.h`: consensus fields and derived difficulty interval.
- `src/pow.cpp`: `GetNextWorkRequired`, `CalculateNextWorkRequired`, `PermittedDifficultyTransition`, `DeriveTarget`, `CheckProofOfWork`.
- `src/pow.h`: public PoW interfaces and transition-check contract.
- `src/test/pow_tests.cpp`: upstream PoW tests and chain-parameter sanity checks.
- Pinned source: Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`.

## 9. Scope and approval boundary

This is a static source audit only. It does not select final consensus parameters, change runtime code, create genesis, start mining, deploy nodes, or launch any network. All consensus-critical owner decisions remain open until explicitly approved.
