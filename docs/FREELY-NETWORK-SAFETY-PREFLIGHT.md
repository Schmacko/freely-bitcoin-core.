# FREELY network-safety preflight

## Purpose

The preflight validator checks a machine-readable FREELY network manifest before production network parameters are finalized. It is intentionally fail-closed: the repository template records the two already approved policy decisions (genesis coinbase permanently unspendable; BIP94 enabled from genesis) while leaving production identity, genesis commitment, numeric proof-of-work parameters and activation values unset, so running the validator against that template must report **BLOCKED**.

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
- Presence of the network magic, P2P/RPC ports, data directory, address prefixes, genesis hash, genesis difficulty fields, genesis coinbase-spendability decision, BIP94 decision, and script activation matrix.
- Format and basic range checks for those values.
- Reuse of Bitcoin mainnet message magic, ports, data-directory name, Base58 address/secret/extended-key prefixes, Bech32 HRP, or genesis hash.
- Distinct P2P and RPC ports.
- Exact owner-approved target spacing (600 seconds), target timespan (1,209,600 seconds), and retarget interval (2,016 blocks), plus explicit booleans for min-difficulty, no-retargeting, and BIP94 policy.
- A compact `nBits` field restricted to its unsigned 32-bit encoding width before compact-target decoding.
- Rejection of the all-zero genesis hash and an empty script-activation-height matrix; synthetic test fixtures are explicitly test-only and do not choose production activation values.

## Deliberate limitations

A passing result is a manifest consistency check, **not** proof that the C++ chain parameters consume the manifest, that the genesis block is correctly constructed, or that a node is safe to launch. It does not compile or execute Bitcoin Core. Those require separate implementation, integration tests, and code review.

The validator also decodes the genesis compact target and checks that it is positive, non-negative, non-overflowing, and no greater than the declared `powLimit`. The default BIP325 signet challenge derives message magic `0a03cf40`, which the validator checks statically. A non-default `-signetchallenge` derives a different value and must be collision-checked at runtime when that custom challenge is configured. The test fixture uses synthetic values solely to test the validator. They are not proposed FREELY production parameters and must never be copied into production configuration.

## Owner decisions still required

Do not populate production values by guessing. In particular, the following remain owner-controlled:

1. Numeric production `powLimit` and initial difficulty, after the candidate model and security assumptions are reviewed.
2. Final network identity values (message magic, ports, address prefixes, data-directory suffix and Bech32 HRP), after collision checks.
3. Final genesis timestamp/message and block commitment, after the dependent consensus values are fixed.
4. Exact runtime script activation parameters, after the v32.1 compatibility matrix and boundary tests are verified.

Until the complete, reviewed production configuration exists, FREELY startup must remain fail-closed.


## Data-directory path safety

The `network.data_directory` value is a single relative directory suffix, not an arbitrary path. The validator accepts a portable name containing letters, digits, underscores and hyphens, and rejects path separators, absolute paths, drive paths, UNC paths, dot segments and traversal. This is deliberately platform-independent so a manifest validated on Linux cannot become unsafe when used on Windows (or vice versa).


The current validator test suite also includes a regression fixture for the default signet magic `0a03cf40`. Non-default signet challenges are dynamic and require a separate runtime collision check; the static manifest validator does not claim to enumerate arbitrary challenge values.
