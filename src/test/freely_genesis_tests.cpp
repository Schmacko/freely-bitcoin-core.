// Copyright (c) 2026-present The FREELY contributors
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <consensus/amount.h>
#include <consensus/merkle.h>
#include <primitives/block.h>
#include <primitives/transaction.h>
#include <script/script.h>
#include <test/util/setup_common.h>

#include <boost/test/unit_test.hpp>

#include <string>
#include <utility>
#include <vector>

BOOST_FIXTURE_TEST_SUITE(freely_genesis_tests, BasicTestingSetup)

BOOST_AUTO_TEST_CASE(approved_genesis_coinbase_transaction_and_merkle_root)
{
    // This independently fixes the approved coinbase transaction and Merkle
    // root. The mined block nonce/hash are verified in chaintype_tests; normal
    // production chain selection remains disabled until explicit authorization.
    constexpr char MESSAGE[] = "FREELY FLY genesis 2026-11-18";
    const std::vector<unsigned char> payload{
        'F', 'R', 'E', 'E', 'L', 'Y', ' ', 'F', 'L', 'Y', ' ', 'G', 'E', 'N', 'E', 'S', 'I', 'S',
    };
    const CScript output_script = CScript() << OP_RETURN << payload;
    BOOST_CHECK(output_script.IsUnspendable());

    CMutableTransaction tx;
    tx.version = 1;
    tx.vin.resize(1);
    tx.vin[0].prevout.SetNull();
    tx.vin[0].scriptSig = CScript() << 486604799 << CScriptNum(4)
                                    << std::vector<unsigned char>(MESSAGE, MESSAGE + sizeof(MESSAGE) - 1);
    tx.vin[0].nSequence = 0xffffffff;
    tx.vout.emplace_back(50 * COIN, output_script);

    const CTransactionRef coinbase = MakeTransactionRef(std::move(tx));
    BOOST_CHECK_EQUAL(coinbase->vout.size(), 1U);
    BOOST_CHECK_EQUAL(coinbase->vout[0].nValue, 50 * COIN);
    BOOST_CHECK_EQUAL(coinbase->GetHash().GetHex(),
                      "c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1");

    CBlock candidate;
    candidate.nVersion = 1;
    candidate.nTime = 1'794'960'000;
    candidate.nBits = 0x1d00ffff;
    candidate.hashPrevBlock.SetNull();
    candidate.vtx.push_back(coinbase);

    bool mutated{false};
    candidate.hashMerkleRoot = BlockMerkleRoot(candidate, &mutated);
    BOOST_CHECK(!mutated);
    BOOST_CHECK_EQUAL(candidate.hashMerkleRoot.GetHex(),
                      "c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1");
}

BOOST_AUTO_TEST_SUITE_END()
