#!/usr/bin/env python3
"""Independent integer-only checker for FREELY's synthetic retarget test vectors.

These fixtures validate the approved 2,016-block / 600-second retarget arithmetic.
They are not production FREELY powLimit or genesis parameters.
"""

TARGET_SPACING = 600
RETARGET_INTERVAL = 2_016
TARGET_TIMESPAN = TARGET_SPACING * RETARGET_INTERVAL
MIN_TIMESPAN = TARGET_TIMESPAN // 4
MAX_TIMESPAN = TARGET_TIMESPAN * 4
SYNTHETIC_POW_LIMIT_COMPACT = 0x1E7FFFFF
SYNTHETIC_PREVIOUS_BITS = 0x1D7FFFFF


def decode_compact(compact: int) -> int:
    """Decode a positive, non-overflowing Bitcoin compact target."""
    size = compact >> 24
    word = compact & 0x007FFFFF
    negative = word != 0 and (compact & 0x00800000) != 0
    overflow = word != 0 and (
        size > 34 or (word > 0xFF and size > 33) or (word > 0xFFFF and size > 32)
    )
    if negative or overflow or word == 0:
        raise ValueError(f"invalid compact target: 0x{compact:08x}")
    if size <= 3:
        target = word >> (8 * (3 - size))
    else:
        target = word << (8 * (size - 3))
    # A non-zero mantissa can still decode to zero for compact exponents 0..3.
    # Match Bitcoin Core's SetCompact validity checks by rejecting that target.
    if target == 0:
        raise ValueError(f"zero compact target: 0x{compact:08x}")
    return target


def encode_compact(target: int) -> int:
    """Encode a positive target using Bitcoin's compact representation."""
    if target <= 0:
        raise ValueError("target must be positive")
    size = (target.bit_length() + 7) // 8
    if size <= 3:
        compact = target << (8 * (3 - size))
    else:
        compact = target >> (8 * (size - 3))
    if compact & 0x00800000:
        compact >>= 8
        size += 1
    return (size << 24) | (compact & 0x007FFFFF)


def calculate_next_bits(elapsed_seconds: int) -> int:
    previous_target = decode_compact(SYNTHETIC_PREVIOUS_BITS)
    pow_limit = decode_compact(SYNTHETIC_POW_LIMIT_COMPACT)
    actual = max(MIN_TIMESPAN, min(MAX_TIMESPAN, elapsed_seconds))
    next_target = (previous_target * actual) // TARGET_TIMESPAN
    next_target = min(next_target, pow_limit)
    return encode_compact(next_target)


def main() -> None:
    assert TARGET_TIMESPAN == 1_209_600
    assert MIN_TIMESPAN == 302_400
    assert MAX_TIMESPAN == 4_838_400

    # Compact-target edge cases: reject zero, negative, overflow and values
    # whose non-zero mantissa truncates to a zero target after exponent shifting.
    invalid_compacts = (
        0x00000000,  # zero mantissa
        0x01800001,  # negative target
        0x23010000,  # exponent overflow
        0x01000001,  # non-zero mantissa truncates to zero
    )
    for compact in invalid_compacts:
        try:
            decode_compact(compact)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid compact target accepted: 0x{compact:08x}")

    assert encode_compact(decode_compact(SYNTHETIC_PREVIOUS_BITS)) == SYNTHETIC_PREVIOUS_BITS
    try:
        encode_compact(0)
    except ValueError:
        pass
    else:
        raise AssertionError("zero target unexpectedly encoded")

    vectors = (
        (302_399, 0x1D1FFFFF),
        (302_400, 0x1D1FFFFF),
        (1_209_600, 0x1D7FFFFF),
        (4_838_400, 0x1E01FFFF),
        (4_838_401, 0x1E01FFFF),
    )
    for elapsed, expected in vectors:
        actual = calculate_next_bits(elapsed)
        assert actual == expected, (
            f"elapsed={elapsed}: expected 0x{expected:08x}, got 0x{actual:08x}"
        )

    # The first retarget at candidate height 2,016 must measure from height 0
    # to height 2,015. Measuring from height 1 is the deliberate off-by-one trap.
    correct_period_bits = calculate_next_bits(402_500 - 100_000)
    wrong_ancestor_bits = calculate_next_bits(402_500 - 101_000)
    assert correct_period_bits == 0x1D2002B5
    assert wrong_ancestor_bits == 0x1D1FFFFF
    assert correct_period_bits != wrong_ancestor_bits

    print("FREELY synthetic retarget vectors: PASS (5 clamp/scaling cases + 2,016-block boundary)")
    print("Compact target edge cases: PASS (zero, negative, overflow, truncated-zero, round-trip)")
    print("Production powLimit/genesis parameters: NOT selected by this checker")


if __name__ == "__main__":
    main()
