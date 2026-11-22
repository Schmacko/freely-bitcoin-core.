"""Independent arithmetic cross-check for the FREELY monetary specification.

This is a documentation/specification check, not a substitute for the C++
consensus implementation or its validation tests.
"""

from __future__ import annotations

COIN = 100_000_000
INITIAL_SUBSIDY = 50 * COIN
HALVING_INTERVAL = 210_000
MAX_MONEY = 21_000_000 * COIN
EXPECTED_SCHEDULED_ISSUANCE = 2_099_999_997_690_000
EXPECTED_SPENDABLE_IF_GENESIS_REWARD_IS_UNSPENDABLE = (
    EXPECTED_SCHEDULED_ISSUANCE - INITIAL_SUBSIDY
)


def subsidy(height: int) -> int:
    if height < 0:
        raise ValueError("block height cannot be negative")
    halvings = height // HALVING_INTERVAL
    if halvings >= 64:
        return 0
    return INITIAL_SUBSIDY >> halvings


def scheduled_issuance_including_genesis() -> int:
    # Each subsidy era has HALVING_INTERVAL blocks, including height zero.
    total = 0
    for halvings in range(64):
        era_subsidy = INITIAL_SUBSIDY >> halvings
        if era_subsidy == 0:
            break
        total += era_subsidy * HALVING_INTERVAL
    return total


def main() -> None:
    vectors = {
        0: 5_000_000_000,
        209_999: 5_000_000_000,
        210_000: 2_500_000_000,
        419_999: 2_500_000_000,
        420_000: 1_250_000_000,
        630_000: 625_000_000,
        1_260_000: 78_125_000,
        6_509_999: 4,
        6_510_000: 2,
        6_719_999: 2,
        6_720_000: 1,
        6_929_999: 1,
        6_930_000: 0,
    }
    for height, expected in vectors.items():
        actual = subsidy(height)
        assert actual == expected, (
            f"height {height}: expected {expected}, got {actual}"
        )

    total = scheduled_issuance_including_genesis()
    assert total == EXPECTED_SCHEDULED_ISSUANCE, (
        f"scheduled issuance mismatch: {total}"
    )
    assert total <= MAX_MONEY, "scheduled issuance exceeds hard money ceiling"

    spendable_if_genesis_unspendable = total - subsidy(0)
    assert (
        spendable_if_genesis_unspendable
        == EXPECTED_SPENDABLE_IF_GENESIS_REWARD_IS_UNSPENDABLE
    )

    print("PASS: all subsidy boundary vectors match.")
    print(f"PASS: scheduled issuance including height zero = {total} base units.")
    print(
        "PASS: spendable subsidy if genesis reward is unspendable = "
        f"{spendable_if_genesis_unspendable} base units."
    )
    print(f"PASS: hard ceiling = {MAX_MONEY} base units.")


if __name__ == "__main__":
    main()
