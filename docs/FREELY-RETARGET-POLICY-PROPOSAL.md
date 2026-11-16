# FREELY production retarget and minimum-difficulty policy

**Date:** 16 November 2026  
**Source baseline:** Bitcoin Core v32.1, commit `f0de87f040621468b956f01f526a43a010310501`  
**Status:** Proposed consensus specification for owner review. This document does not activate parameters or change runtime code.

## 1. Decision summary

This proposal resolves the retarget/minimum-difficulty item using the existing Bitcoin Core v32.1 retarget implementation, with the FREELY values already agreed by the project:

| Setting | Proposed FREELY production value |
|---|---:|
| Hash algorithm | SHA-256d |
| Target block spacing | 600 seconds |
| Target timespan | 1,209,600 seconds (14 days) |
| Adjustment interval | 2,016 blocks |
| Retarget clamp | ¼× to 4× target timespan |
| Minimum-difficulty exception | Disabled |
| No-retargeting mode | Disabled |
| Retarget algorithm | v32.1 `GetNextWorkRequired` / `CalculateNextWorkRequired` semantics |
| PoW limit | Not selected here; separate consensus decision |
| BIP94 time-warp mitigation | Not selected here; separate consensus decision |

The corresponding production parameter values are:

```cpp
consensus.nPowTargetSpacing = 600;
consensus.nPowTargetTimespan = 1'209'600;
consensus.fPowAllowMinDifficultyBlocks = false;
consensus.fPowNoRetargeting = false;
```

These are proposed FREELY production settings only. Regtest and other explicitly classified test chains may retain test-only conveniences. Test-chain settings must never be inherited by the FREELY production chain.

## 2. Exact retarget rule

Let:

- (I = 2016), the adjustment interval;
- (S = 600) seconds, target spacing;
- (T = I \times S = 1,209,600) seconds, target timespan;
- (L) be the approved FREELY proof-of-work limit;
- (Q_{old}) be the previous block's decoded target;
- (t_0) be the header timestamp of the first block in the completed period;
- (t_{last}) be the header timestamp of the last block in that period.

For a candidate block at height (h):

1. If (h \bmod I \ne 0), its required `nBits` is exactly the previous block's `nBits`. There is no minimum-difficulty exception on production FREELY.
2. If (h \bmod I = 0), use the previous completed period: first block height (h-I), last block height (h-1).
3. Compute raw elapsed time using the two block-header timestamps:
   `actual = t_last - t_0`.
4. Clamp elapsed time:
   `actual_clamped = min(max(actual, T/4), 4*T)`.
   For FREELY, the permitted clamp interval is 302,400 seconds (3.5 days) through 4,838,400 seconds (56 days).
5. Decode the previous block's `nBits` as (Q_{old}), using the established compact-target decoder.
6. Calculate with integer arithmetic:
   `Q_new = floor(Q_old * actual_clamped / T)`.
7. Clamp the result to the approved PoW limit:
   `Q_new = min(Q_new, L)`.
8. Encode the target using the upstream compact-target encoding to obtain the required `nBits`.

The first retarget is therefore for block height 2,016 and uses timestamps from blocks 0 and 2,015. The target remains unchanged for blocks 1 through 2,015.

### Important details

- Preserve the upstream integer arithmetic and compact encoding; do not use floating point.
- The multiplication/division order and compact rounding are consensus-critical. Reuse the pinned implementation rather than writing a mathematically similar replacement.
- Invalid compact targets (negative, zero, overflow, or above `powLimit`) remain invalid under upstream `DeriveTarget` / proof-of-work validation.
- The calculated target may never exceed `powLimit`.
- Upstream timestamp validity rules, including median-time-past and future-time checks, remain in force. The retarget calculation itself uses the period endpoint header timestamps, not MTP values.
- The upstream `PermittedDifficultyTransition` factor-of-four check should be exercised in FREELY tests and kept consistent with the retarget rule.

## 3. Minimum difficulty and retargeting modes

For production FREELY:

- `fPowAllowMinDifficultyBlocks = false`: a delayed block does not receive an easier target merely because it arrived more than 2 × 600 seconds after its predecessor.
- `fPowNoRetargeting = false`: difficulty is recalculated at every 2,016-block boundary.
- Between boundaries, the previous target is carried forward unchanged.

This avoids the testnet-style minimum-difficulty escape hatch and avoids a permanently fixed target. It does **not** guarantee fast block production: if honest SHA-256d hash rate falls substantially, blocks can become very slow until the next retarget. That is an expected consequence of the chosen rule, not a reason to silently enable minimum difficulty.

For local regtest, developers may use the upstream test-chain settings to make testing practical. Those settings must be isolated by explicit chain classification and covered by a regression test proving production FREELY has both flags disabled.

## 4. Why this is the recommended baseline

1. It reuses a mature, pinned, auditable implementation instead of introducing a bespoke difficulty algorithm.
2. It gives a precise and deterministic 14-day adjustment period based on the agreed 10-minute target and 2,016-block interval.
3. The factor-of-four clamp bounds each adjustment to a maximum fourfold easier or harder target change.
4. Disabling minimum difficulty prevents individual delayed blocks from temporarily using the easiest permitted target.
5. Keeping retargeting enabled allows difficulty to respond to sustained hash-rate changes.

This is a conservative implementation choice, not a claim that the legacy retarget algorithm is immune to timestamp manipulation or time-warp attacks. The separate BIP94 decision must be reviewed before production consensus is frozen.

## 5. Required regression tests before runtime activation

Add FREELY-specific tests for:

### Parameter invariants
- `nPowTargetSpacing == 600`;
- `nPowTargetTimespan == 1'209'600`;
- `DifficultyAdjustmentInterval() == 2016`;
- `nPowTargetTimespan % nPowTargetSpacing == 0`;
- `fPowAllowMinDifficultyBlocks == false`;
- `fPowNoRetargeting == false`.

### Height and boundary behaviour
- Candidate heights 1–2,015 retain the prior `nBits`.
- Candidate height 2,016 retargets using blocks 0 and 2,015.
- Later boundaries use exactly the immediately preceding 2,016-block period.
- No off-by-one use of height 2,014 or 2,016 as a period endpoint.

### Clamp and arithmetic vectors
- Raw timespans below, equal to, and above 302,400 seconds.
- Raw timespans below, equal to, and above 4,838,400 seconds.
- Exact expected compact targets at both clamp limits.
- Integer truncation and compact-encoding rounding.
- A result above `powLimit` is capped exactly at `powLimit`.
- Retargeting responds correctly to faster and slower periods.

### Minimum difficulty and test-chain isolation
- A production block timestamp more than 1,200 seconds after its predecessor does not trigger a minimum-difficulty target.
- A production non-boundary block must retain the previous `nBits`.
- Test-chain minimum-difficulty behaviour, if retained, remains confined to its own chain parameters.
- Production FREELY cannot be configured with no-retargeting through test-only overrides.

### Validation and integration
- Invalid compact targets are rejected.
- `PermittedDifficultyTransition` agrees with the selected retarget bounds.
- Existing Bitcoin network tests remain unchanged.
- FREELY PoW unit tests, validation tests and full CI pass.
- At least three private FREELY nodes independently accept/reject the same boundary blocks.

## 6. Explicitly outside this decision

This proposal does not choose:

- numeric `powLimit`;
- genesis `nBits`, nonce or hash;
- BIP94 activation or time-warp mitigation policy;
- any timestamp rule different from upstream v32.1;
- minimum chainwork, checkpoints, assume-valid or seed values.

Those require separate decisions and must not be inferred from this proposal.

## 7. Approval and activation boundary

This is a documentation-only proposal. It does not modify `Consensus::Params`, chain parameters, block validation, genesis, mining or network deployment.

After owner approval, the selected policy can be copied into the formal consensus specification. Runtime implementation must wait until the FREELY chain-parameter and genesis work is ready, and must include the regression tests above. No public testnet or mainnet is authorised by this document.

## 8. Pinned source references

- `src/consensus/params.h`: PoW parameter fields and derived adjustment interval.
- `src/pow.cpp`: `GetNextWorkRequired`, `CalculateNextWorkRequired`, `PermittedDifficultyTransition`, `DeriveTarget` and `CheckProofOfWorkImpl`.
- `src/pow.h`: PoW interface contracts.
- Bitcoin Core v32.1 pinned commit: `f0de87f040621468b956f01f526a43a010310501`.
