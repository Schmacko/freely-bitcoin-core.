# FREELY network-safety preflight

## Purpose

The preflight validator checks the machine-readable FREELY network manifest against the owner-approved baseline and the independently reproduced genesis candidate. The manifest contains approved non-genesis network identity, PoW/retarget settings, activation matrix and genesis template, plus a candidate nonce/hash explicitly marked `candidate_pending_owner_approval`. A valid manifest reports **PASS** for internal consistency only; the derived nonce/hash are not final owner-approved identity and this is not production launch authorization.

## Run

From the repository root:

```sh
python3 contrib/freely/check_network_safety.py
python3 -m unittest discover -s contrib/freely -p 'test_check_network_safety.py' -v
```

The validator uses only the Python standard library. Exit codes are:

- `0`: manifest passes the checks implemented here.
- `1`: manifest is readable but incomplete or invalid.
- `2`: manifest cannot be read or parsed.

## Source audit

See [FREELY upstream network-identity audit](FREELY-UPSTREAM-NETWORK-IDENTITY-AUDIT.md) for the v32.1 source-derived network identifiers, chain-parameter integration points, production/test classification requirements, and remaining runtime checks.

## What is checked

- FREELY / FLY project identity.
- Presence and exact approved values for network magic, P2P/RPC ports, data directory, address prefixes, genesis template, difficulty fields, coinbase-spendability decision, BIP94 decision and script activation matrix; the derived genesis hash/nonce must remain explicitly candidate-only and independently reproducible.
- Format and basic range checks for those values.
- Reuse of Bitcoin mainnet message magic, ports, data-directory name, Base58 address/secret/extended-key prefixes, Bech32 HRP, or genesis hash.
- Distinct P2P and RPC ports.
- Exact owner-approved target spacing (600 seconds), target timespan (1,209,600 seconds), and retarget interval (2,016 blocks), plus explicit booleans for min-difficulty, no-retargeting, and BIP94 policy.
- A compact `nBits` field restricted to its unsigned 32-bit encoding width before compact-target decoding.
- Independent reconstruction of the 117-byte genesis coinbase serialization, transaction ID/Merkle root, 80-byte header, SHA256d block hash and proof-of-work target; rejection of mismatched derived values.

## Deliberate limitations

A passing result is a manifest consistency check, **not** proof that the C++ chain parameters consume the manifest, that the genesis block is correctly constructed, or that a node is safe to launch. It does not compile or execute Bitcoin Core. Those require separate implementation, integration tests, and code review.

The validator also decodes the genesis compact target and checks that it is positive, non-negative, non-overflowing, and no greater than the declared `powLimit`. The default BIP325 signet challenge derives message magic `0a03cf40`, which the validator checks statically. A non-default `-signetchallenge` derives a different value and must be collision-checked at runtime when that custom challenge is configured. The test fixture uses synthetic values solely to test the validator. They are not proposed FREELY production parameters and must never be copied into production configuration.

## Owner approvals and remaining engineering gates

All four baseline protocol-parameter proposal areas were approved on 18 November 2026. The approved values are pinned in `docs/FREELY-APPROVED-PROTOCOL-PARAMETERS.md`. The manifest pins the derived nonce/hash only as `candidate_pending_owner_approval`; explicit owner sign-off on the final production genesis commitment remains outstanding.

The candidate genesis commitment has been independently reproduced; the derived nonce/hash are not final approved identity:
- Candidate nonce (pending owner sign-off): `2238688522`.
- Coinbase txid / Merkle root: `c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1`.
- Candidate block hash (pending owner sign-off): `0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78`.

Exact-head evidence:
- Network preflight workflow [44899513446](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44899513446) passed on `e7019df06a72c8ec37922eca34d6f4cbeefc207f`: 28 network-safety tests, 17 production-readiness evidence tests, and manifest preflight PASS.
- The workflow also confirmed the production evidence ledger remains BLOCKED at 0/9 gates, as required.
- Standalone C++ miner workflow [44910736974](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44910736974) passed on `865026e755239bf0a89e7a5b91513f896bb9858a`, independently verifying the candidate nonce/hash/header.

Remaining work is integrated C++ CChainParams validation, exact-head core/functional CI, wallet/node/security evidence and separate production launch authorization. Normal FREELY startup must remain fail-closed until those gates are reviewed and explicitly authorized.


## Data-directory path safety

The `network.data_directory` value is a single relative directory suffix, not an arbitrary path. The validator accepts a portable name containing letters, digits, underscores and hyphens, and rejects path separators, absolute paths, drive paths, UNC paths, dot segments and traversal. This is deliberately platform-independent so a manifest validated on Linux cannot become unsafe when used on Windows (or vice versa).


The current validator test suite also includes a regression fixture for the default signet magic `0a03cf40`. Non-default signet challenges are dynamic and require a separate runtime collision check; the static manifest validator does not claim to enumerate arbitrary challenge values.


## Exact-head preflight evidence — 21 November 2026

- Manifest branch head at validation: `e7019df06a72c8ec37922eca34d6f4cbeefc207f`.
- Workflow: [FREELY network safety preflight 44899513446](https://github.com/Schmacko/freely-bitcoin-core./actions/runs/44899513446).
- Job `Python preflight tests`: successful.
- Unit suites: 28 network-safety tests and 17 production-readiness tests passed.
- The manifest validator printed `FREELY network preflight: PASS`.
- The evidence-ledger check printed `FREELY production readiness: BLOCKED` and `Evidence gates passed: 0/9`, which is the intended result until implementation/release evidence and explicit launch authorization exist.

A manifest preflight pass does not establish C++ compilation, integrated node startup, wallet readiness, independent security review or production readiness.
