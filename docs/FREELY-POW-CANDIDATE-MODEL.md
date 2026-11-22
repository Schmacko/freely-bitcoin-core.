# FREELY proof-of-work candidate model

**Date:** 17 November 2026
**Status:** historical scenario analysis; the owner approved powLimit and genesis nBits on 18 November 2026. This model remains mathematical analysis, not a live mining benchmark or security guarantee.
**Upstream reference:** Bitcoin Core v32.1 difficulty-1 target is used only as a mathematical normalization unit, not as a proposed FREELY network parameter.

## 1. Purpose and safety boundary

This model was prepared before the numeric PoW values were approved. The approved baseline is powLimit `00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff` and genesis nBits `0x1d00ffff`; see [FREELY-APPROVED-PROTOCOL-PARAMETERS.md](FREELY-APPROVED-PROTOCOL-PARAMETERS.md). The scenario calculations remain useful for understanding expected SHA-256d work, block intervals and hash-rate sensitivity, but they do not replace measured network hash rate or a security assessment.

This is a deterministic mathematical model, **not a live mining benchmark**, a hashrate measurement, a security guarantee or a production parameter proposal. It does not select a genesis nBits, powLimit, launch date or mining deployment.

## 2. How powLimit and initial difficulty relate

A proof-of-work target is a 256-bit integer. A block hash must be numerically no greater than that target.

- powLimit is the easiest target the chain permits.
- The initial target encoded by genesis nBits must be no easier than powLimit.
- A smaller target means harder mining.
- Initial difficulty may be harder than the minimum difficulty implied by powLimit.

For comparison only, define difficulty 1 using the conventional Bitcoin difficulty-1 reference target:

**0x00000000ffff0000000000000000000000000000000000000000000000000000**

This is a normalization constant for the equations. It is **not** an instruction to copy Bitcoin's production powLimit.

Let D be the dimensionless difficulty relative to that reference. Expected hashes per block are approximately:

**expected_hashes = D × 2^32**

At the agreed 600-second target spacing, the average hash rate needed to produce a block every 10 minutes is approximately:

**required_hashrate = D × 2^32 / 600**

At measured hash rate H, expected block interval is:

**expected_block_seconds = D × 2^32 / H**

The probability of finding at least one block in a window t under a simplified constant-hashrate Poisson model is:

**P(block in t) = 1 − exp(−H × t / (D × 2^32))**

These are expected values, not guarantees. Real hash rates vary, blocks are probabilistic, and compact-target encoding introduces integer rounding.

## 3. Illustrative candidate difficulty levels

The table shows the approximate aggregate SHA-256d hash rate required for a 600-second expected block interval.

| Relative difficulty D | Required aggregate hash rate |
|---:|---:|
| 1 | 7.16 MH/s |
| 16 | 114.53 MH/s |
| 256 | 1.83 GH/s |
| 4,096 | 29.32 GH/s |
| 65,536 | 469.12 GH/s |
| 1,048,576 | 7.51 TH/s |
| 16,777,216 | 120.10 TH/s |

The numbers are deliberately scenarios, not recommendations. For perspective, a single modern SHA-256 ASIC may exceed several of these rates. A difficulty value that appears high compared with a laptop can still be trivially low compared with specialist mining hardware.

## 4. What must be measured before choosing a value

A defensible recommendation needs all of the following:

1. **Honest initial hashrate:** actual hardware and operators willing to mine continuously at launch, not hypothetical global SHA-256 capacity.
2. **Hashrate floor:** the minimum expected honest rate during quiet periods and after miners leave.
3. **Attacker model:** plausible rented, redirected or privately controlled SHA-256 capacity and the cost/time to dominate FREELY's honest work.
4. **Block-stall tolerance:** maximum acceptable expected block interval and the probability of long gaps.
5. **Difficulty transition:** how the approved 2,016-block / 14-day retarget and ¼×–4× clamp respond when the initial estimate is wrong.
6. **Bootstrap plan:** how the first 2,016 blocks are produced without a special minimum-difficulty exception (already approved disabled for production).
7. **BIP94 interaction:** verify the first-block-of-period difficulty reference in v32.1 with BIP94 enabled.
8. **Compact target validity:** encode candidate targets using Core's compact format and reject negative, zero, overflowing or above-limit values.

A target chosen solely to make the first block easy is not a security strategy. An extremely hard initial target can stall the chain; an extremely easy target allows cheap block production and may make majority attacks inexpensive.

## 5. Recommended evaluation procedure

1. Collect a written, non-binding commitment from prospective miners describing hardware model, SHA-256d rate, availability and expected uptime. Do not deploy miners as part of this analysis.
2. Build low/base/high honest-hashrate scenarios from those commitments.
3. Build separate attacker-hashrate scenarios; do not assume the attacker is limited to the honest miner set.
4. Run the companion scripts/model-freely-pow-candidates.py for each candidate difficulty and scenario.
5. Calculate block interval distributions and expected time to reach the first retarget boundary (2,016 blocks).
6. Simulate the approved retarget clamp and BIP94 first-period target behaviour using synthetic fixtures.
7. Have an independent reviewer assess majority-attack economics and the possibility of prolonged stalls.
8. Present the owner with a small number of candidate pairs: minimum permitted difficulty implied by powLimit, initial difficulty / genesis nBits, assumptions, expected block times and attack/stall risks.
9. Obtain a separate explicit owner approval before any production value is written into runtime chain parameters.

## 6. Current decision status

| Item | Status |
|---|---|
| SHA-256d | Approved project design |
| Target spacing | 600 seconds, approved |
| Retarget interval | 2,016 blocks, approved |
| Retarget clamp | ¼×–4×, approved |
| Production minimum-difficulty exception | Disabled, approved |
| Production no-retargeting | Disabled, approved |
| BIP94 | Enabled from genesis, approved subject to tests |
| Numeric powLimit | **Not selected** |
| Initial difficulty / genesis nBits | **Not selected** |
| Honest and attacker hashrate assumptions | **Not yet evidenced** |
| Public mining or launch | Not authorised |

## 7. References and implementation notes

- Bitcoin Core v32.1 src/pow.cpp: GetNextWorkRequired and CalculateNextWorkRequired.
- Bitcoin Core v32.1 src/consensus/params.h: powLimit, target spacing, target timespan, minimum-difficulty, BIP94 and no-retargeting fields.
- FREELY retarget vectors: FREELY-RETARGET-TEST-VECTORS.md.
- FREELY consensus decision register: FREELY-CONSENSUS-DECISION-REGISTER.md.

No candidate in this document is a production setting. Do not hard-code any of these illustrative difficulty levels into FREELY runtime parameters.


## 9. Owner approval update — 18 November 2026

The numeric production `powLimit` and genesis `nBits` are now owner-approved as recorded in the authoritative protocol baseline. This document remains a mathematical model only. It does not establish honest hash rate, attacker cost, mining economics, chain security or expected public block intervals. FREELY does not inherit Bitcoin's accumulated SHA-256d hash power or security.
