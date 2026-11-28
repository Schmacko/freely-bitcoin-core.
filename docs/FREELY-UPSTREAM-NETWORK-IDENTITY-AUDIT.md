# FREELY upstream network-identity audit

**Reviewed source:** Bitcoin Core v32.1, pinned fork base `f0de87f040621468b956f01f526a43a010310501`
**Reviewed implementation context:** `freely/m1-consensus` and `freely/core-chain-implementation`
**Status:** static v32.1 source audit plus review of the current FREELY candidate integration branches. The approved non-genesis network identity and baseline consensus values are pinned; the derived genesis nonce/hash are independently reproduced candidate outputs pending explicit owner sign-off as final production identity. Normal production chain selection remains fail-closed; candidate C++/functional CI and release evidence are still pending.

## Findings

The original upstream-based audit branch deliberately keeps normal FREELY chain selection fail-closed. Since this audit was first written, PR #20 was closed unmerged. Replacement PR #22 adds `CFreelyCandidateParams`, a derived candidate genesis commitment, base parameters and fixed C++ assertions; PR #21 adds explicit offline-development and loopback-private startup modes but still targets the preserved PR #20 base and requires a deliberate rebase/transplant onto the replacement lineage. The candidate is not production-activated, has no DNS/fixed seeds, and is not reachable through ordinary `CreateChainParams(..., FREELY)` without the guarded development path. All four baseline proposal areas were approved; the derived nonce/hash remain candidate-only and require explicit owner sign-off before final production identity is frozen.

### Existing Bitcoin network identifiers

| Network | P2P magic | P2P port | RPC port | Data-directory suffix | Bech32 HRP |
|---|---|---:|---:|---|---|
| Mainnet | `f9beb4d9` | 8333 | 8332 | empty/root | `bc` |
| Testnet3 | `0b110907` | 18333 | 18332 | `testnet3` | `tb` |
| Testnet4 | `1c163f28` | 48333 | 48332 | `testnet4` | `tb` |
| Signet | derived from challenge | 38333 | 38332 | `signet` | `tb` |
| Regtest | `fabfb5da` | 18444 | 18443 | `regtest` | `bcrt` |

The built-in network values above are read from `src/kernel/chainparams.cpp` and `src/chainparamsbase.cpp`. Signet's magic is challenge-derived; a static preflight cannot enumerate all custom signet challenges. FREELY's final magic must therefore be checked against the actual signet magic during runtime parameter construction and in `GetNetworkForMagic` regression tests.

### Wallet/address identifiers

Mainnet Base58/WIF prefixes are public-key address `0`, script address `5`, secret key `128`, extended public key `0488b21e`, and extended private key `0488ade4`.

Bitcoin test networks use public-key address `111`, script address `196`, secret key `239`, extended public key `043587cf`, and extended private key `04358394`. Testnet3, testnet4, signet and regtest share test-style Base58 extended-key prefixes; their Bech32 HRPs are `tb` except regtest's `bcrt`.

FREELY must not reuse any of these values. Wallet compatibility must be verified with Base58Check, BIP32 extended-key and Bech32/Bech32m round-trip tests.

### C++ integration and safety gates

| Integration point | Current state | Required before enabling FREELY |
|---|---|---|
| `src/util/chaintype.h/.cpp` | `ChainType::FREELY` and canonical `freely` parse/serialize are present | Preserve round-trip and reject noncanonical names |
| `src/chainparamsbase.h` | `freely` is listed in chain help | Keep selector fail-closed |
| `src/chainparamsbase.cpp` | FREELY base factory throws | Add a unique relative data-dir suffix and RPC port only after identity approval |
| `src/chainparams.cpp` | FREELY consensus factory throws | Add a dedicated factory; never alias MAIN, TESTNET or REGTEST |
| `src/kernel/chainparams.cpp` | No FREELY parameter class or network identity | Add explicit magic, P2P port, address identifiers, genesis, consensus and no Bitcoin history shortcuts |
| `GetNetworkForMagic` in `src/kernel/chainparams.cpp` | Maps the existing five networks | Add FREELY and test collisions against every existing network, including the active signet challenge |
| `src/kernel/chainparams.h` | Explicit `m_is_test_chain` and `m_is_production_chain` fields exist on the M1 branch; both default false | FREELY must explicitly set production true and test false; do not rely on defaults |
| `src/init.cpp` | Test activation overrides are blocked on production chains; `-test=<option>` remains regtest-only | Test `-testactivationheight` and `-vbparams` rejection on FREELY |
| `CMainParams` | Contains Bitcoin genesis time, nonce, compact target, subsidy output, mainnet chainwork, assume-valid, seeds and AssumeUTXO history | Do not copy Bitcoin history-specific values into FREELY |

The current mainnet constructor calls `CreateGenesisBlock(1231006505, 2083236893, 0x1d00ffff, 1, 50 * COIN)`, asserts Bitcoin's genesis hash and Merkle root, and installs Bitcoin mainnet seeds and history-specific chainwork/assume-valid data. Those are Bitcoin-specific commitments, not reusable FREELY defaults.

### Startup classification

The M1 branch explicitly marks Bitcoin MAIN as production and TESTNET, TESTNET4, SIGNET and REGTEST as test chains. `src/init.cpp` checks `IsProductionChain()` before allowing `-testactivationheight` or `-vbparams`; `-test=<option>` is independently restricted to REGTEST.

When the FREELY parameter class is eventually implemented, it must explicitly set:
- `m_is_production_chain = true`;
- `m_is_test_chain = false`;
- `m_is_mockable_chain = false`.

The candidate parameter class now explicitly sets those properties. Normal production selection still throws until separate owner launch authorization; the guarded development modes add network isolation but are not an OS sandbox.

## Validator coverage

The companion `contrib/freely/check_network_safety.py` checks:
- built-in Bitcoin message magic values (except challenge-derived signet magic);
- all built-in Bitcoin P2P/RPC TCP ports, including cross-role port collisions;
- Bitcoin data-directory suffixes and config-section identity;
- mainnet and test-network Base58/WIF/BIP32 prefixes;
- Bitcoin Bech32 HRPs;
- Bitcoin mainnet genesis hash;
- genesis compact-target validity and relation to the declared `powLimit`;
- independent coinbase serialization, txid/Merkle root, 80-byte header SHA256d, derived nonce/hash and proof-of-work verification;
- required owner-approved settings and fail-closed omissions.

This script validates a manifest. It does not inspect the C++ binary or prove that C++ consumes the manifest. Runtime collision checks and source-level regression tests remain mandatory.

## Owner approvals and remaining engineering gates

All four protocol-parameter proposal areas were explicitly approved on 18 November 2026. The approved `powLimit`, genesis `nBits`, BIP94/time-warp policy, non-genesis network magic/ports/address identity and activation matrix are pinned in the canonical approved-parameter document. The manifest separately marks the derived genesis nonce/hash as candidate-only; explicit owner sign-off on that final commitment remains outstanding.

The candidate genesis commitment is independently reproduced; the derived nonce/hash are not final owner-approved identity:
- Approved coinbase txid / Merkle root: `c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1`.
- Candidate nonce (pending owner sign-off): `2238688522`.
- Candidate block hash (pending owner sign-off): `0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78`.

Evidence:
- Current miner head `8e81ea9fbf9c0b079bad1d14e8383cd36a4912b5`: push-triggered candidate verification [45204029247](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204029247) passed; PR-triggered verification [45204041280](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204041280) is queued and full CI [45204040649](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204040649) is in progress.
- Current preflight head `24c4ebfe873bf30043fdb5b329b10143962b4fb0`: preflight [45204530104](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204530104) is queued and full CI [45204530112](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45204530112) is in progress; no new-head pass is claimed.
- Replacement candidate PR #22 head `92239197131c5d0dbbf6f77fbb30760facb18460`: focused core-chain workflow [45203933162](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45203933162) is pending and full CI [45203932853](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45203932853) is in progress.
- PR #21 offline-wallet and private-node workflows [45202770106](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45202770106) and [45202770188](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/45202770188) are in progress; its base lineage remains unresolved.

No production parameter, seed, deployment, public testnet or mainnet launch is authorized by this audit.


### Data-directory path constraint

The manifest's `network.data_directory` field is restricted to one portable path component (letters, digits, underscore and hyphen). It must not contain either POSIX or Windows path separators, drive syntax, UNC syntax, or dot segments. The preflight enforces this independent of the host operating system.


## Current candidate integration status — 21 November 2026

- Candidate base/consensus values are implemented on PR #20 head `fb8f9efa5e817e5bafd635139e5386240ea05b67`; its focused candidate workflow is queued.
- PR #21 adds fail-closed offline and loopback-private modes plus C++ network-boundary regressions; its current focused security, offline-wallet and candidate workflows are queued on head `87c34cf244dfeb3ffaa1eceb60f15970c2189d45`.
- PR #17's core-chain workflow passed on its exact head `c237f42435ce24360586228aa702f62905b14c9f`, including build of `test_bitcoin`, 4/4 selected C++ suites, 11/11 nonce-helper tests and the fail-closed startup functional test. This predates candidate CChainParams and is not evidence for PR #20/#21.
- PR #11's wallet workflow exposed a missing `bitcoin-wallet` build target; the workflow now builds `bitcoind`, `bitcoin-cli` and `bitcoin-wallet`, and its corrected exact-head run is pending.
- PR #6's expanded retarget boundary and compact-target tests are awaiting focused PoW CI.

Production startup remains fail-closed. The standalone miner/preflight passes do not establish integrated node readiness, wallet readiness, independent security review or launch authorization.
