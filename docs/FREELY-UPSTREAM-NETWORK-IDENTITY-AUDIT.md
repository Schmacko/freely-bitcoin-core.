# FREELY upstream network-identity audit

**Reviewed source:** Bitcoin Core v32.1, pinned fork base `f0de87f040621468b956f01f526a43a010310501`
**Reviewed implementation context:** `freely/m1-consensus` and `freely/core-chain-implementation`
**Status:** static source audit; no production identifiers or runtime parameters assigned.

## Findings

The FREELY chain selector exists in the implementation branch, but the base-parameter and consensus-parameter factories deliberately throw. There is no runnable FREELY `CChainParams` object, no genesis commitment, and no approved network identity. The fail-closed behavior must remain until the owner decisions are complete.

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

The current FREELY factory guards mean those properties are not yet active or runtime-tested.

## Validator coverage

The companion `contrib/freely/check_network_safety.py` checks:
- built-in Bitcoin message magic values (except challenge-derived signet magic);
- all built-in Bitcoin P2P/RPC TCP ports, including cross-role port collisions;
- Bitcoin data-directory suffixes and config-section identity;
- mainnet and test-network Base58/WIF/BIP32 prefixes;
- Bitcoin Bech32 HRPs;
- Bitcoin mainnet genesis hash;
- genesis compact-target validity and relation to the declared `powLimit`;
- required owner-approved settings and fail-closed omissions.

This script validates a manifest. It does not inspect the C++ binary or prove that C++ consumes the manifest. Runtime collision checks and source-level regression tests remain mandatory.

## Remaining owner decisions

1. Numeric production `powLimit` and initial difficulty.
2. Final network identity values after collision checks.
3. Final genesis timestamp/message and block commitment.
4. Exact script activation parameters after compatibility tests.

No production parameter, seed, deployment, public testnet or mainnet launch is authorized by this audit.


### Data-directory path constraint

The manifest's `network.data_directory` field is restricted to one portable path component (letters, digits, underscore and hyphen). It must not contain either POSIX or Windows path separators, drive syntax, UNC syntax, or dot segments. The preflight enforces this independent of the host operating system.
