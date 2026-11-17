# FREELY network-safety preflight

## Purpose

The preflight validator checks a machine-readable FREELY network manifest before production network parameters are finalized. It is intentionally fail-closed: the repository template contains unresolved values, so running the validator against that template must report **BLOCKED** until the owner-approved values are supplied.

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

## What is checked

- FREELY / FLY project identity.
- Presence of the network magic, P2P/RPC ports, data directory, address prefixes, genesis hash, genesis difficulty fields, genesis coinbase-spendability decision, BIP94 decision, and script activation matrix.
- Format and basic range checks for those values.
- Reuse of Bitcoin mainnet message magic, ports, data-directory name, Base58 address/secret/extended-key prefixes, Bech32 HRP, or genesis hash.
- Distinct P2P and RPC ports.
- Positive target spacing and retarget interval, and explicit booleans for min-difficulty and no-retargeting policy.

## Deliberate limitations

A passing result is a manifest consistency check, **not** proof that the C++ chain parameters consume the manifest, that the genesis block is correctly constructed, or that a node is safe to launch. It does not compile or execute Bitcoin Core. Those require separate implementation, integration tests, and code review.

The validator also decodes the genesis compact target and checks that it is positive, non-negative, non-overflowing, and no greater than the declared `powLimit`. Signet message magic is challenge-derived, so its runtime value must also be checked against FREELY when the signet challenge is known. The test fixture uses synthetic values solely to test the validator. They are not proposed FREELY production parameters and must never be copied into production configuration.

## Owner decisions still required

Do not populate production values by guessing. In particular, the following remain owner-controlled:

1. Genesis coinbase spendability/accounting.
2. Numeric `powLimit` and initial difficulty.
3. BIP94/time-warp mitigation.
4. Script and soft-fork activation matrix.
5. Final network magic, ports, address prefixes, data directory, and genesis commitment.

Until the complete, reviewed production configuration exists, FREELY startup must remain fail-closed.
