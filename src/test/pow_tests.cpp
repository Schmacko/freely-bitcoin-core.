// Copyright (c) 2015-present The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chain.h>
#include <chainparams.h>
#include <pow.h>
#include <test/util/random.h>
#include <test/util/common.h>
#include <test/util/setup_common.h>
#include <util/chaintype.h>

#include <boost/test/unit_test.hpp>

BOOST_FIXTURE_TEST_SUITE(pow_tests, BasicTestingSetup)

/* Test calculation of next difficulty target with no constraints applying */
BOOST_AUTO_TEST_CASE(get_next_work)
{
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    int64_t nLastRetargetTime = 1261130161; // Block #30240
    CBlockIndex pindexLast;
    pindexLast.nHeight = 32255;
    pindexLast.nTime = 1262152739;  // Block #32255
    pindexLast.nBits = 0x1d00ffff;

    // Here (and below): expected_nbits is calculated in
    // CalculateNextWorkRequired(); redoing the calculation here would be just
    // reimplementing the same code that is written in pow.cpp. Rather than
    // copy that code, we just hardcode the expected result.
    unsigned int expected_nbits = 0x1d00d86aU;
    BOOST_CHECK_EQUAL(CalculateNextWorkRequired(&pindexLast, nLastRetargetTime, chainParams->GetConsensus()), expected_nbits);
    BOOST_CHECK(PermittedDifficultyTransition(chainParams->GetConsensus(), pindexLast.nHeight+1, pindexLast.nBits, expected_nbits));
}

/* Test the constraint on the upper bound for next work */
BOOST_AUTO_TEST_CASE(get_next_work_pow_limit)
{
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    int64_t nLastRetargetTime = 1231006505; // Block #0
    CBlockIndex pindexLast;
    pindexLast.nHeight = 2015;
    pindexLast.nTime = 1233061996;  // Block #2015
    pindexLast.nBits = 0x1d00ffff;
    unsigned int expected_nbits = 0x1d00ffffU;
    BOOST_CHECK_EQUAL(CalculateNextWorkRequired(&pindexLast, nLastRetargetTime, chainParams->GetConsensus()), expected_nbits);
    BOOST_CHECK(PermittedDifficultyTransition(chainParams->GetConsensus(), pindexLast.nHeight+1, pindexLast.nBits, expected_nbits));
}

/* Test the constraint on the lower bound for actual time taken */
BOOST_AUTO_TEST_CASE(get_next_work_lower_limit_actual)
{
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    int64_t nLastRetargetTime = 1279008237; // Block #66528
    CBlockIndex pindexLast;
    pindexLast.nHeight = 68543;
    pindexLast.nTime = 1279297671;  // Block #68543
    pindexLast.nBits = 0x1c05a3f4;
    unsigned int expected_nbits = 0x1c0168fdU;
    BOOST_CHECK_EQUAL(CalculateNextWorkRequired(&pindexLast, nLastRetargetTime, chainParams->GetConsensus()), expected_nbits);
    BOOST_CHECK(PermittedDifficultyTransition(chainParams->GetConsensus(), pindexLast.nHeight+1, pindexLast.nBits, expected_nbits));
    // Test that reducing nbits further would not be a PermittedDifficultyTransition.
    unsigned int invalid_nbits = expected_nbits-1;
    BOOST_CHECK(!PermittedDifficultyTransition(chainParams->GetConsensus(), pindexLast.nHeight+1, pindexLast.nBits, invalid_nbits));
}

/* Test the constraint on the upper bound for actual time taken */
BOOST_AUTO_TEST_CASE(get_next_work_upper_limit_actual)
{
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    int64_t nLastRetargetTime = 1263163443; // NOTE: Not an actual block time
    CBlockIndex pindexLast;
    pindexLast.nHeight = 46367;
    pindexLast.nTime = 1269211443;  // Block #46367
    pindexLast.nBits = 0x1c387f6f;
    unsigned int expected_nbits = 0x1d00e1fdU;
    BOOST_CHECK_EQUAL(CalculateNextWorkRequired(&pindexLast, nLastRetargetTime, chainParams->GetConsensus()), expected_nbits);
    BOOST_CHECK(PermittedDifficultyTransition(chainParams->GetConsensus(), pindexLast.nHeight+1, pindexLast.nBits, expected_nbits));
    // Test that increasing nbits further would not be a PermittedDifficultyTransition.
    unsigned int invalid_nbits = expected_nbits+1;
    BOOST_CHECK(!PermittedDifficultyTransition(chainParams->GetConsensus(), pindexLast.nHeight+1, pindexLast.nBits, invalid_nbits));
}

BOOST_AUTO_TEST_CASE(CheckProofOfWork_test_negative_target)
{
    const auto consensus = CreateChainParams(*m_node.args, ChainType::MAIN)->GetConsensus();
    uint256 hash;
    unsigned int nBits;
    nBits = UintToArith256(consensus.powLimit).GetCompact(true);
    hash = uint256{1};
    BOOST_CHECK(!CheckProofOfWork(hash, nBits, consensus));
}

BOOST_AUTO_TEST_CASE(CheckProofOfWork_test_overflow_target)
{
    const auto consensus = CreateChainParams(*m_node.args, ChainType::MAIN)->GetConsensus();
    uint256 hash;
    unsigned int nBits{~0x00800000U};
    hash = uint256{1};
    BOOST_CHECK(!CheckProofOfWork(hash, nBits, consensus));
}

BOOST_AUTO_TEST_CASE(CheckProofOfWork_test_too_easy_target)
{
    const auto consensus = CreateChainParams(*m_node.args, ChainType::MAIN)->GetConsensus();
    uint256 hash;
    unsigned int nBits;
    arith_uint256 nBits_arith = UintToArith256(consensus.powLimit);
    nBits_arith *= 2;
    nBits = nBits_arith.GetCompact();
    hash = uint256{1};
    BOOST_CHECK(!CheckProofOfWork(hash, nBits, consensus));
}

BOOST_AUTO_TEST_CASE(CheckProofOfWork_test_biger_hash_than_target)
{
    const auto consensus = CreateChainParams(*m_node.args, ChainType::MAIN)->GetConsensus();
    uint256 hash;
    unsigned int nBits;
    arith_uint256 hash_arith = UintToArith256(consensus.powLimit);
    nBits = hash_arith.GetCompact();
    hash_arith *= 2; // hash > nBits
    hash = ArithToUint256(hash_arith);
    BOOST_CHECK(!CheckProofOfWork(hash, nBits, consensus));
}

BOOST_AUTO_TEST_CASE(CheckProofOfWork_test_zero_target)
{
    const auto consensus = CreateChainParams(*m_node.args, ChainType::MAIN)->GetConsensus();
    uint256 hash;
    unsigned int nBits;
    arith_uint256 hash_arith{0};
    nBits = hash_arith.GetCompact();
    hash = ArithToUint256(hash_arith);
    BOOST_CHECK(!CheckProofOfWork(hash, nBits, consensus));
}

BOOST_AUTO_TEST_CASE(GetBlockProofEquivalentTime_test)
{
    const auto chainParams = CreateChainParams(*m_node.args, ChainType::MAIN);
    std::vector<CBlockIndex> blocks(10000);
    for (int i = 0; i < 10000; i++) {
        blocks[i].pprev = i ? &blocks[i - 1] : nullptr;
        blocks[i].nHeight = i;
        blocks[i].nTime = 1269211443 + i * chainParams->GetConsensus().nPowTargetSpacing;
        blocks[i].nBits = 0x207fffff; /* target 0x7fffff000... */
        blocks[i].nChainWork = i ? blocks[i - 1].nChainWork + GetBlockProof(blocks[i - 1]) : arith_uint256(0);
    }

    for (int j = 0; j < 1000; j++) {
        CBlockIndex *p1 = &blocks[m_rng.randrange(10000)];
        CBlockIndex *p2 = &blocks[m_rng.randrange(10000)];
        CBlockIndex *p3 = &blocks[m_rng.randrange(10000)];

        int64_t tdiff = GetBlockProofEquivalentTime(*p1, *p2, *p3, chainParams->GetConsensus());
        BOOST_CHECK_EQUAL(tdiff, p1->GetBlockTime() - p2->GetBlockTime());
    }
}

void sanity_check_chainparams(const ArgsManager& args, ChainType chain_type)
{
    const auto chainParams = CreateChainParams(args, chain_type);
    const auto consensus = chainParams->GetConsensus();

    // hash genesis is correct
    BOOST_CHECK_EQUAL(consensus.hashGenesisBlock, chainParams->GenesisBlock().GetHash());

    // target timespan is an even multiple of spacing
    BOOST_CHECK_EQUAL(consensus.nPowTargetTimespan % consensus.nPowTargetSpacing, 0);

    // genesis nBits is positive, doesn't overflow and is lower than powLimit
    arith_uint256 pow_compact;
    bool neg, over;
    pow_compact.SetCompact(chainParams->GenesisBlock().nBits, &neg, &over);
    BOOST_CHECK(!neg);
    BOOST_CHECK(pow_compact != 0);
    BOOST_CHECK(!over);
    BOOST_CHECK(UintToArith256(consensus.powLimit) >= pow_compact);

    // check max target * 4*nPowTargetTimespan doesn't overflow -- see pow.cpp:CalculateNextWorkRequired()
    if (!consensus.fPowNoRetargeting) {
        arith_uint256 targ_max{UintToArith256(uint256{"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"})};
        targ_max /= consensus.nPowTargetTimespan*4;
        BOOST_CHECK(UintToArith256(consensus.powLimit) < targ_max);
    }
}

BOOST_AUTO_TEST_CASE(ChainParams_MAIN_sanity)
{
    sanity_check_chainparams(*m_node.args, ChainType::MAIN);
}

BOOST_AUTO_TEST_CASE(ChainParams_REGTEST_sanity)
{
    sanity_check_chainparams(*m_node.args, ChainType::REGTEST);
}

BOOST_AUTO_TEST_CASE(ChainParams_TESTNET_sanity)
{
    sanity_check_chainparams(*m_node.args, ChainType::TESTNET);
}

BOOST_AUTO_TEST_CASE(ChainParams_TESTNET4_sanity)
{
    sanity_check_chainparams(*m_node.args, ChainType::TESTNET4);
}

BOOST_AUTO_TEST_CASE(ChainParams_SIGNET_sanity)
{
    sanity_check_chainparams(*m_node.args, ChainType::SIGNET);
}

/* FREELY-approved production retarget policy, tested with synthetic targets.
 * Synthetic powLimit and nBits are fixtures only; they are not FREELY network parameters.
 */
BOOST_AUTO_TEST_CASE(freely_retarget_clamp_vectors)
{
    Consensus::Params consensus;
    consensus.nPowTargetSpacing = 600;
    consensus.nPowTargetTimespan = 1'209'600;
    consensus.fPowAllowMinDifficultyBlocks = false;
    consensus.fPowNoRetargeting = false;
    consensus.enforce_BIP94 = false;

    arith_uint256 pow_limit;
    bool negative{false};
    bool overflow{false};
    pow_limit.SetCompact(0x1e7fffffU, &negative, &overflow);
    BOOST_REQUIRE(!negative);
    BOOST_REQUIRE(!overflow);
    consensus.powLimit = ArithToUint256(pow_limit);

    CBlockIndex previous;
    previous.nHeight = 2015;
    previous.nBits = 0x1d7fffffU;

    const auto check_vector = [&](int64_t elapsed, uint32_t expected)
    {
        previous.nTime = elapsed;
        BOOST_CHECK_EQUAL(CalculateNextWorkRequired(&previous, 0, consensus), expected);
    };

    // The values are independently fixed in docs/FREELY-RETARGET-TEST-VECTORS.md.
    check_vector(302'399, 0x1d1fffffU);  // just below lower clamp
    check_vector(302'400, 0x1d1fffffU);  // lower clamp
    check_vector(1'209'600, 0x1d7fffffU); // target timespan
    check_vector(4'838'400, 0x1e01ffffU); // upper clamp
    check_vector(4'838'401, 0x1e01ffffU); // just above upper clamp
}


/* Exercise the FREELY-approved 2,016-block retarget boundary using a synthetic
 * target. The fixture is not a FREELY production powLimit or genesis target.
 */
BOOST_AUTO_TEST_CASE(freely_retarget_boundary_uses_first_block_of_period)
{
    Consensus::Params consensus;
    consensus.nPowTargetSpacing = 600;
    consensus.nPowTargetTimespan = 1'209'600;
    consensus.fPowAllowMinDifficultyBlocks = false;
    consensus.fPowNoRetargeting = false;
    consensus.enforce_BIP94 = false;

    arith_uint256 pow_limit;
    bool negative{false};
    bool overflow{false};
    pow_limit.SetCompact(0x1e7fffffU, &negative, &overflow);
    BOOST_REQUIRE(!negative);
    BOOST_REQUIRE(!overflow);
    consensus.powLimit = ArithToUint256(pow_limit);

    std::vector<CBlockIndex> period(2016);
    for (int height = 0; height < static_cast<int>(period.size()); ++height) {
        period[height].nHeight = height;
        period[height].nBits = 0x1d7fffffU;
        period[height].pprev = height == 0 ? nullptr : &period[height - 1];
    }

    // A 302,500-second span from height 0 gives 0x1f2002b5.
    // Measuring from height 1 instead would clamp 301,500 seconds to
    // 302,400 and produce 0x1f1fffff, so this catches an off-by-one ancestor.
    period.front().nTime = 100'000;
    period[1].nTime = 101'000;
    period.back().nTime = 402'500;

    CBlockHeader candidate;
    BOOST_CHECK_EQUAL(GetNextWorkRequired(&period.back(), &candidate, consensus), 0x1d2002b5U);
}

BOOST_AUTO_TEST_CASE(freely_non_boundary_height_carries_forward_bits)
{
    Consensus::Params consensus;
    consensus.nPowTargetSpacing = 600;
    consensus.nPowTargetTimespan = 1'209'600;
    consensus.fPowAllowMinDifficultyBlocks = false;
    consensus.fPowNoRetargeting = false;
    consensus.enforce_BIP94 = false;

    CBlockIndex previous;
    previous.nHeight = 2016;
    previous.nBits = 0x1d2002b5U;
    CBlockHeader candidate;

    BOOST_CHECK_EQUAL(GetNextWorkRequired(&previous, &candidate, consensus), previous.nBits);
}

BOOST_AUTO_TEST_CASE(freely_derive_target_rejects_invalid_compact_values)
{
    arith_uint256 pow_limit;
    bool negative{false};
    bool overflow{false};
    pow_limit.SetCompact(0x1e7fffffU, &negative, &overflow);
    BOOST_REQUIRE(!negative);
    BOOST_REQUIRE(!overflow);
    const uint256 limit{ArithToUint256(pow_limit)};

    BOOST_CHECK(DeriveTarget(0x1d7fffffU, limit).has_value());
    BOOST_CHECK(!DeriveTarget(arith_uint256{1}.GetCompact(true), limit)); // negative
    BOOST_CHECK(!DeriveTarget(0, limit)); // zero
    BOOST_CHECK(!DeriveTarget(0x01000001U, limit)); // non-zero mantissa truncated to zero
    BOOST_CHECK(!DeriveTarget(0x23000001U, limit)); // overflow
    BOOST_CHECK(!DeriveTarget(0x2100ffffU, limit)); // above powLimit
}


/* BIP94 uses the first block's target as the retarget base. FREELY has
 * minimum-difficulty blocks disabled, but still enables this protection
 * from genesis. The synthetic values are test fixtures only.
 */
BOOST_AUTO_TEST_CASE(freely_bip94_uses_first_block_period_target)
{
    Consensus::Params consensus;
    consensus.nPowTargetSpacing = 600;
    consensus.nPowTargetTimespan = 1'209'600;
    consensus.fPowAllowMinDifficultyBlocks = false;
    consensus.fPowNoRetargeting = false;
    consensus.enforce_BIP94 = true;

    arith_uint256 pow_limit;
    bool negative{false};
    bool overflow{false};
    pow_limit.SetCompact(0x1e7fffffU, &negative, &overflow);
    BOOST_REQUIRE(!negative);
    BOOST_REQUIRE(!overflow);
    consensus.powLimit = ArithToUint256(pow_limit);

    std::vector<CBlockIndex> period(2016);
    for (int height = 0; height < static_cast<int>(period.size()); ++height) {
        period[height].nHeight = height;
        period[height].nBits = 0x1d3fffffU;
        period[height].pprev = height == 0 ? nullptr : &period[height - 1];
    }
    period.front().nBits = 0x1d7fffffU;
    period.front().nTime = 100'000;
    period.back().nTime = 1'309'600; // exactly one target timespan later

    const auto bip94_target = CalculateNextWorkRequired(&period.back(), period.front().nTime, consensus);
    BOOST_CHECK_EQUAL(bip94_target, period.front().nBits);

    consensus.enforce_BIP94 = false;
    const auto legacy_target = CalculateNextWorkRequired(&period.back(), period.front().nTime, consensus);
    BOOST_CHECK_EQUAL(legacy_target, period.back().nBits);
    BOOST_CHECK_NE(bip94_target, legacy_target);
}

BOOST_AUTO_TEST_SUITE_END()
