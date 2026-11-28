"""Model FREELY SHA-256d block intervals for candidate difficulty scenarios.

This is a deterministic mathematical model, not a live miner benchmark.
Difficulty is normalized to the conventional difficulty-1 target solely for
comparison; it does not select a FREELY powLimit or genesis nBits.
"""
from __future__ import annotations

import argparse
import math

HASHES_PER_DIFFICULTY_ONE = 2**32
TARGET_SPACING_SECONDS = 600
DEFAULT_DIFFICULTIES = [1, 16, 256, 4096, 65536, 1048576, 16777216]
DEFAULT_HASHRATES = [10_000_000, 100_000_000, 1_000_000_000, 1_000_000_000_000, 100_000_000_000_000]


def required_hashrate(difficulty: int, target_seconds: int = TARGET_SPACING_SECONDS) -> float:
    if difficulty <= 0 or target_seconds <= 0:
        raise ValueError("difficulty and target_seconds must be positive")
    return difficulty * HASHES_PER_DIFFICULTY_ONE / target_seconds


def expected_block_seconds(difficulty: int, hashrate_hs: float) -> float:
    if difficulty <= 0 or hashrate_hs <= 0:
        raise ValueError("difficulty and hashrate must be positive")
    return difficulty * HASHES_PER_DIFFICULTY_ONE / hashrate_hs


def probability_at_least_one_block(difficulty: int, hashrate_hs: float, window_seconds: float) -> float:
    if difficulty <= 0 or hashrate_hs <= 0 or window_seconds < 0:
        raise ValueError("difficulty/hashrate must be positive and window must be non-negative")
    expected_blocks = hashrate_hs * window_seconds / (difficulty * HASHES_PER_DIFFICULTY_ONE)
    return -math.expm1(-expected_blocks)


def format_rate(rate: float) -> str:
    for unit, scale in (("PH/s", 1e15), ("TH/s", 1e12), ("GH/s", 1e9), ("MH/s", 1e6), ("kH/s", 1e3)):
        if rate >= scale:
            return f"{rate / scale:.2f} {unit}"
    return f"{rate:.2f} H/s"


def format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f} s"
    if seconds < 3600:
        return f"{seconds / 60:.2f} min"
    if seconds < 86400:
        return f"{seconds / 3600:.2f} h"
    return f"{seconds / 86400:.2f} days"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--difficulty", type=int, action="append", dest="difficulties",
                        help="relative difficulty scenario; repeat to add scenarios")
    parser.add_argument("--hashrate", type=float, action="append", dest="hashrates",
                        help="measured or assumed aggregate SHA-256d hash rate in H/s; repeat to add scenarios")
    parser.add_argument("--window", type=float, default=600,
                        help="observation window in seconds for block probability (default: 600)")
    args = parser.parse_args()

    difficulties = args.difficulties or DEFAULT_DIFFICULTIES
    hashrates = args.hashrates or DEFAULT_HASHRATES
    if any(value <= 0 for value in difficulties + hashrates) or args.window < 0:
        parser.error("difficulty/hashrate must be positive and --window must be non-negative")

    print("FREELY SHA-256d candidate model — not a mining benchmark or production recommendation")
    print(f"Target spacing: {TARGET_SPACING_SECONDS} seconds")
    print("\nRequired aggregate hash rate for 600-second expected blocks:")
    for difficulty in difficulties:
        print(f"  D={difficulty:,}: {format_rate(required_hashrate(difficulty))}")

    print(f"\nExpected block interval and probability of >=1 block in {args.window:g}s:")
    print("Difficulty | Assumed hash rate | Expected interval | P(>=1 block)")
    for difficulty in difficulties:
        for hashrate in hashrates:
            interval = expected_block_seconds(difficulty, hashrate)
            probability = probability_at_least_one_block(difficulty, hashrate, args.window)
            print(f"{difficulty:>10,} | {format_rate(hashrate):>17} | {format_duration(interval):>16} | {probability:>12.4%}")

    print("\nNo powLimit, genesis nBits or production difficulty has been selected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
