# FREELY protocol parameter approval package

**Version:** 1.0  
**Date:** 18 November 2026  
**Status:** exact engineering proposal for owner review — NOT APPROVED, NOT ACTIVATED  
**Repository baseline:** Bitcoin Core v32.1, pinned source commit `f0de87f040621468b956f01f526a43a010310501`  
**Related:** [Consensus specification](FREELY-CONSENSUS-SPECIFICATION.md) · [Decision register](FREELY-CONSENSUS-DECISION-REGISTER.md) · [Network parameters draft](FREELY-NETWORK-PARAMETERS-DRAFT.md) · [PoW candidate model](FREELY-POW-CANDIDATE-MODEL.md)

> **Safety boundary:** This document proposes values only. It does not change runtime chain parameters, generate an activated production genesis, expose RPC/P2P, deploy miners, create seeds, or authorise a testnet/mainnet launch. Existing fail-closed startup behaviour must remain until the owner approves the final values and the implementation passes review and tests.

## 1. Executive proposal

The following is the recommended conservative Bitcoin-compatible baseline for owner review:

| Decision area | Proposed value | Approval status |
|---|---|---|
| PoW limit and genesis difficulty | `powLimit = 00000000ffff0000000000000000000000000000000000000000000000000000`; genesis `nBits = 0x1d00ffff` | **Awaiting owner approval** |
| Network identity | Magic `f4 e5 f3 f4`; P2P `29333`; RPC `29332`; data directory `freely`; custom Base58/BIP32 versions; HRP `fly` | **Awaiting owner approval** |
| Genesis candidate | Header time `1794960000`; version 1; previous hash zero; Merkle root `a8058c7e22bbe89ea3c3e3f3b78f43173724a4bfc56fc8a976139a6015d9fb37`; `nBits=0x1d00ffff`; nonce found by deterministic PoW search | **Awaiting owner approval; nonce/hash not yet mined** |
| Script activation | BIP34/BIP66/BIP65/CSV/SegWit at height 1; BIP34 hash zero; P2SH/Witness/Taproot validation from genesis; no Bitcoin historical exceptions; test dummy deployment never active | **Awaiting owner approval** |

These recommendations retain the already-approved 50 FLY subsidy, 210,000-block halving, 600-second target spacing, 2,016-block retarget interval, 14-day timespan, ¼–4× elapsed-time clamp, BIP94 from genesis, no minimum-difficulty exception, and no-retargeting disabled.

## 2. Proposal 1 — PoW limit and genesis difficulty

### Exact proposed values

| Parameter | Proposed value |
|---|---:|
| Algorithm | SHA-256d (double SHA-256) |
| `powLimit` | `00000000ffff0000000000000000000000000000000000000000000000000000` |
| Genesis `nBits` | `0x1d00ffff` |
| Decoded genesis target | `00000000ffff0000000000000000000000000000000000000000000000000000` |
| Initial relative difficulty | Approximately 1.0 against the conventional Bitcoin difficulty-1 target |
| Target spacing | 600 seconds |
| Retarget interval | 2,016 blocks |
| Target timespan | 1,209,600 seconds |
| Actual-timespan clamp | 302,400 to 4,838,400 seconds |
| Minimum-difficulty blocks | Disabled |
| No-retargeting | Disabled |
| BIP94 | Enabled from genesis |

The compact target `0x1d00ffff` decodes to the proposed `powLimit` exactly. Genesis therefore starts at the easiest target the production chain will permit. The target is the same conventional difficulty-1 reference used by Bitcoin mainnet; this is a mathematical starting point, not an inheritance of Bitcoin's hashrate or security.

### Security and operating implications

- Expected work at this target is approximately **4,295,032,833 SHA-256d hashes per block**.
- At 10 MH/s, the statistical mean block interval is approximately 429.5 seconds (7.16 minutes); at 100 MH/s, 42.95 seconds; at 1 GH/s, 4.30 seconds; at 1 TH/s, 0.0043 seconds. These are mathematical expectations, not measured FREELY mining rates or guarantees.
- The chosen target avoids regtest-like near-instant mining. It is nevertheless a very low difficulty by modern SHA-256 ASIC standards.
- A new chain with little honest hashrate remains vulnerable to majority-hash attacks, deep reorganisations, censorship and double-spends. An attacker can redirect or rent SHA-256 capacity; using Bitcoin's algorithm does not import Bitcoin's accumulated work.
- The first 2,016 blocks have no production minimum-difficulty escape hatch. If committed honest hashrate is insufficient, block production can stall. The retarget cannot help until the first adjustment boundary.
- Difficulty 1 is a conservative compatibility baseline, not a claim that the chain is economically secure. A launch security review must compare committed honest hashrate with plausible attacker capacity and cost.

### Compact-target and retarget test vectors

All targets below are unsigned 256-bit integers. Compact values are encoded using Bitcoin Core's `SetCompact/GetCompact` rules, including sign, zero and overflow handling.

| Test | Input | Expected result |
|---|---|---|
| Decode production genesis bits | `0x1d00ffff` | Exact target equals `powLimit` above |
| Decode quarter target | `0x1c3fffc0` | `000000003fffc000000000000000000000000000000000000000000000000000` |
| Candidate height 2,015 | Non-boundary block | Carry forward previous block's `nBits` unchanged |
| Candidate height 2,016; elapsed 302,399 s | Clamp elapsed to 302,400 s | New bits `0x1c3fffc0` |
| Candidate height 2,016; elapsed 302,400 s | Lower clamp boundary | New bits `0x1c3fffc0` |
| Candidate height 2,016; elapsed 1,209,600 s | Exact target timespan | New bits `0x1d00ffff` |
| Candidate height 2,016; elapsed 4,838,400 s | Upper clamp boundary | New bits `0x1d00ffff` (capped at powLimit) |
| Candidate height 2,016; elapsed 4,838,401 s | Clamp elapsed to 4,838,400 s | New bits `0x1d00ffff` (capped at powLimit) |
| Negative compact target | `0x1d80ffff` | Reject |
| Zero after compact decoding | `0x01000001` | Reject |
| Compact overflow | `0x23010000` | Reject |
| Target above powLimit | `0x1e00ffff` | Reject |
| PoW boundary | Hash value equal to target | Accept |
| PoW boundary | Hash value target + 1 | Reject |

**BIP94 period-base regression vector:** for a synthetic later period, set the first block's `nBits=0x1c00ffff`, the final block's `nBits=0x1b00ffff`, and elapsed time to exactly 1,209,600 seconds. The next retarget must use the first block's target and return `0x1c00ffff`, not the final block's `0x1b00ffff`. The production implementation must also enforce the approved boundary timestamp rule: at a retarget boundary, the new block timestamp cannot be more than 600 seconds earlier than its parent and must exceed median-time-past.

## 3. Proposal 2 — unique network identity

### Exact proposed values

| Field | Proposed value |
|---|---|
| Canonical chain selector | `freely` |
| Data-directory suffix | `freely` |
| P2P message-start bytes | `f4 e5 f3 f4` |
| P2P default TCP port | `29333` |
| RPC default TCP port | `29332` |
| P2PKH Base58 version bytes | `46 4c` |
| P2SH Base58 version bytes | `46 53` |
| WIF Base58 version bytes | `46 57` |
| BIP32 extended public version | `04 46 4c 59` (`0x04464c59`) |
| BIP32 extended private version | `04 46 4c 5a` (`0x04464c5a`) |
| Bech32 / Bech32m HRP | `fly` |
| DNS seeds | Empty at initial configuration |
| Fixed seeds | Empty at initial configuration |

The two-byte Base58 versions deliberately avoid reusing Bitcoin's one-byte mainnet/testnet prefixes and reduce accidental address-format collisions with other common networks. The custom BIP32 versions preserve the four-byte extended-key field. Wallet import/export, descriptors, QR/address display and recovery tests must all use the same values.

### Security and operational implications

- The message-start bytes are distinct from the fixed Bitcoin mainnet (`f9 be b4 d9`), testnet3 (`0b 11 09 07`), testnet4 (`1c 16 3f 28`) and regtest (`fa bf b5 da`) values. Signet's message start is challenge-derived, so the actual configured signet value must also be checked.
- Ports 29333/29332 are candidates, not a guarantee that a local machine, hosting provider or another application has them free. Verify the IANA registry and local socket availability before any deployment. Keep RPC bound to loopback by default; never expose unauthenticated RPC to the public internet.
- The P2P port is not a security boundary. Firewall rules and node configuration still determine exposure.
- Empty seeds mean there is no bootstrap discovery service at launch. Do not invent or borrow Bitcoin seed hosts. A seed list may be added only after the operator, DNS ownership, service security and availability are reviewed.
- A distinct data-directory suffix prevents accidental reuse of Bitcoin's chainstate and wallet files. It does not replace backup and recovery testing.

### Required network-identity test vectors

1. `GetNetworkForMagic({f4,e5,f3,f4})` returns FREELY; all built-in Bitcoin magics return their original chain types.
2. FREELY magic differs from mainnet, testnet3, testnet4, regtest and the actual signet magic computed from its challenge.
3. P2P and RPC ports are different from one another and from all built-in Bitcoin network defaults; no cross-role port collision is permitted.
4. `-datadir` resolution uses a separate `freely` network directory; relative paths, traversal and Windows drive/UNC edge cases are rejected by the preflight validator.
5. A FREELY P2PKH address encodes/decodes only under prefix `464c`; P2SH only under `4653`; WIF only under `4657`. Bitcoin mainnet/testnet versions must not decode as FREELY.
6. BIP32 public/private extended keys round-trip under `04464c59`/`04464c5a` and are not mistaken for xpub/xprv/tpub/tprv.
7. Witness-v0 addresses use HRP `fly` with Bech32; witness-v1 Taproot addresses use HRP `fly` with Bech32m. Wrong HRPs and wrong checksums are rejected.
8. No DNS or fixed seed is configured until separately reviewed.

The proposed identity is not a global cryptocurrency namespace reservation. Collision checks must be repeated against the actual target environment and current registry data before activation.

## 4. Proposal 3 — deterministic genesis candidate

### Exact candidate fields

| Header / transaction field | Proposed candidate |
|---|---|
| Header version | `1` |
| Previous block hash | 32 zero bytes |
| Header timestamp | `1794960000` (2026-11-18 00:00:00 UTC) |
| Compact target | `0x1d00ffff` |
| Nonce | Start search at `0`; choose the first uint32 nonce whose SHA-256d header hash is no greater than target; if exhausted, increment timestamp and restart |
| Coinbase transaction version | `1` |
| Coinbase output value | `5,000,000,000` base units = 50.00000000 FLY |
| Coinbase output script | `OP_RETURN` plus a 32-byte protocol-manifest commitment |
| Coinbase output spendability | Permanently unspendable; height-zero reward remains included in scheduled issuance accounting |

**Candidate coinbase message (ASCII):**

`FREELY: Freedom Through Decentralisation | 18 Nov 2026`

**Canonical manifest bytes:** ASCII, LF line endings, with one final LF:

```text
FREELY-GENESIS-MANIFEST-V1
chain=freely
ticker=FLY
decimals=8
pow=SHA256d
powLimit=00000000ffff0000000000000000000000000000000000000000000000000000
genesis_nBits=1d00ffff
target_spacing=600
retarget_interval=2016
target_timespan=1209600
retarget_clamp=1/4..4
bip94=1
min_difficulty=0
no_retarget=0
subsidy_base_units=5000000000
halving_interval=210000
genesis_reward_spendable=0
p2p_magic=f4e5f3f4
p2p_port=29333
rpc_port=29332
datadir=freely
p2pkh=464c
p2sh=4653
wif=4657
bip32_pub=04464c59
bip32_priv=04464c5a
bech32_hrp=fly
bip34_height=1
bip34_hash=0000000000000000000000000000000000000000000000000000000000000000
bip66_height=1
bip65_height=1
csv_height=1
segwit_height=1
taproot=always-active
```

The manifest commitment is single SHA-256 of those exact bytes:

`914ec37b42b9e4698e5a952b0187ba1d55fa8409124fb598385ddd1691bb1043`

The exact output script is:

`6a20914ec37b42b9e4698e5a952b0187ba1d55fa8409124fb598385ddd1691bb1043`

The candidate coinbase scriptSig is:

`04ffff001d010436465245454c593a2046726565646f6d205468726f75676820446563656e7472616c69736174696f6e207c203138204e6f762032303236`

**Candidate serialized coinbase transaction:**

`01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff3e04ffff001d010436465245454c593a2046726565646f6d205468726f75676820446563656e7472616c69736174696f6e207c203138204e6f762032303236ffffffff0100f2052a01000000226a20914ec37b42b9e4698e5a952b0187ba1d55fa8409124fb598385ddd1691bb104300000000`

Expected transaction ID and single-transaction Merkle root:

`a8058c7e22bbe89ea3c3e3f3b78f43173724a4bfc56fc8a976139a6015d9fb37`

### Genesis verification vectors

- Transaction version = 1; one null-prevout coinbase input; sequence = `ffffffff`; one output worth exactly 5,000,000,000 base units; locktime = 0.
- Re-serializing the coinbase bytes and double-SHA-256 hashing them must produce txid `a8058c7e22bbe89ea3c3e3f3b78f43173724a4bfc56fc8a976139a6015d9fb37`.
- A one-transaction genesis block must have that exact Merkle root.
- The header is exactly 80 bytes: version, zero previous hash, Merkle root, timestamp `1794960000`, compact bits `0x1d00ffff`, and mined nonce.
- The final header hash must be independently recomputed by two implementations and satisfy hash-value <= decoded target.
- The OP_RETURN output must never enter the spendable UTXO set. Genesis reward accounting must still match the already-approved issuance schedule.
- Any change to the manifest, message, timestamp, output script, network identity, PoW target or activation matrix requires recomputing the transaction ID/Merkle root and/or header nonce/hash as applicable.

**Important unresolved derivation:** the final nonce and genesis block hash are intentionally not fabricated in this approval package. They are outputs of the deterministic proof-of-work search, not owner-selected policy values. The timestamp is a dated candidate and must be refreshed if the owner wants a later genesis date. The candidate transaction vector above is a proposed new commitment variant and must be added to the repository generator and checked against Bitcoin Core's C++ serialization before it can be accepted as a production genesis.

## 5. Proposal 4 — script and soft-fork activation matrix

The recommendation is to begin with established Bitcoin Core v32.1 script rules, without importing Bitcoin mainnet's historical block-hash exceptions or its historic activation heights.

| Rule | Proposed FREELY activation | Reason |
|---|---:|---|
| P2SH / BIP16 | Active from genesis | v32.1 block script verification keeps P2SH enabled for new blocks |
| Witness / SegWit base rules | Active from genesis in script verification; buried SegWit height = 1 for height-gated block/witness rules | New chain has no historical pre-SegWit blocks; height 1 avoids changing genesis serialization |
| Taproot / BIP340–342 | Active from genesis for script validation | Bitcoin Core v32.1 treats Taproot as always active; no historical Bitcoin exception is copied |
| BIP34 coinbase height | Height 1; `BIP34Hash = uint256(0)` | Genesis remains the special height-zero block; first ordinary block and descendants commit height |
| BIP66 strict DER signatures | Height 1 | Enforce from first ordinary block |
| BIP65 CHECKLOCKTIMEVERIFY | Height 1 | Enforce from first ordinary block |
| BIP68/112/113 CSV rules | Height 1 | Enforce relative locktime rules from first ordinary block |
| BIP147 NULLDUMMY | Height 1, through SegWit activation | v32.1 ties NULLDUMMY to SegwitHeight |
| BIP30 duplicate transaction protection | Retain; no historical exception | Do not import Bitcoin's historical BIP30 exception hashes |
| BIP9 TESTDUMMY | `NEVER_ACTIVE = -2`; timeout `NO_TIMEOUT`; bit 28; period 2,016; threshold 1,815; min activation height 0 | Keep the testing deployment permanently inactive on production |
| Future soft forks | No pre-authorised activation values | Each future rule requires its own compatibility review, start/timeout/minimum height and explicit owner approval |

The `BIP34Hash` zero value is deliberate: it avoids copying Bitcoin's historical activation block hash. At height 1, the coinbase script must encode height 1. The genesis block itself is not retroactively required to use BIP34's height prefix.

### Activation test vectors

1. Height 0: genesis is accepted with the proposed genesis coinbase serialization; it is not required to contain a BIP34 height prefix.
2. Height 1: coinbase script begins with the canonical script-number encoding for height 1 (`OP_1`); a missing or incorrect height is rejected.
3. BIP66, BIP65 and CSV checks are inactive for the genesis block and active at height 1.
4. SegWitHeight = 1: witness commitment/block validation and BIP147 NULLDUMMY enforcement are active for height 1 and later.
5. P2SH, Witness and Taproot script verification flags are present for new FREELY blocks from genesis; no Bitcoin historical script-flag exception hashes are copied.
6. BIP30 duplicate transaction protection remains enforced; no mainnet historical duplicate-transaction exceptions are configured.
7. `-testactivationheight` and `-vbparams` must not override FREELY production consensus settings.
8. TESTDUMMY remains NEVER_ACTIVE even after timestamps pass; a future real deployment must use a separately approved deployment identifier and schedule.
9. Existing Bitcoin mainnet, testnet3, testnet4, signet and regtest activation behaviour remains unchanged.

### Compatibility and risk

Activating established script rules at the beginning is simpler than reproducing Bitcoin's historical activation timeline, but it is still a consensus choice: every FREELY node must enforce the same rules. The height-1 recommendation must be tested against the exact v32.1 validation, witness, wallet and functional-test paths before merge. Taproot's always-active behaviour is confirmed in the v32.1 `GetBlockScriptFlags` implementation; this is not a claim that Taproot was activated at height zero on historical Bitcoin.

## 6. Implementation and acceptance plan

Before any candidate is promoted into runtime parameters:

1. Owner approves or edits all four proposals as one coherent protocol configuration.
2. Add exact values to the protocol decision register, keeping proposal and approval columns separate until approval.
3. Extend the network-safety validator and its unit tests for the selected magic, ports, paths, address prefixes and HRP.
4. Extend the genesis generator to support the exact manifest commitment output script and fixed coinbase/header vectors.
5. Add a deterministic nonce-search tool with a bounded uint32 search, timestamp rollover and independent SHA-256d verification.
6. Add C++ tests against the real FREELY `CChainParams` object for powLimit, nBits, BIP94, production/test classification, activation heights and network identity.
7. Run focused consensus, validation, PoW, wallet, RPC/P2P and full upstream CI on the exact PR heads. Queued or pending workflows are not passes.
8. Obtain independent review of the consensus diff and a security review of the initial hashrate/attacker model.
9. Only then prepare a separate activation change. No production launch or public network exposure is implied by approving these candidate values.

## 7. Owner approval record

No approval is recorded by publishing this proposal.

- [ ] Approve Proposal 1 — `powLimit` and genesis `nBits`
- [ ] Approve Proposal 2 — network identity
- [ ] Approve Proposal 3 — genesis candidate fields and commitment (nonce/hash remain deterministic outputs to be generated and independently verified)
- [ ] Approve Proposal 4 — script activation matrix
- [ ] Approve all four proposals together as one configuration

The owner may approve all four, approve selected proposals, or request changes. A partial approval does not permit the unapproved parameters to be filled with guesses. Even after approval, production activation remains a separate engineering step subject to tests, review and the existing launch restrictions.

## 8. Source references

- Bitcoin Core v32.1 release notes: https://bitcoincore.org/en/releases/32.1/
- Bitcoin Core v32.1 `src/kernel/chainparams.cpp`: https://github.com/bitcoin/bitcoin/blob/v32.1/src/kernel/chainparams.cpp
- Bitcoin Core v32.1 `src/pow.cpp`: https://github.com/bitcoin/bitcoin/blob/v32.1/src/pow.cpp
- Bitcoin Core v32.1 `src/validation.cpp`: https://github.com/bitcoin/bitcoin/blob/v32.1/src/validation.cpp
- Bitcoin Core v32.1 `src/consensus/params.h`: https://github.com/bitcoin/bitcoin/blob/v32.1/src/consensus/params.h
- BIP 9 — version bits: https://bips.dev/9/
- IANA service-name and port-number registry: https://www.iana.org/assignments/service-names-port-numbers
