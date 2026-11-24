# FREELY chain-parameter candidate status

**Status:** reviewed implementation candidate for regression tests only
**Source baseline:** Bitcoin Core v32.1
**Production activation:** not authorized

## Scope

This branch consolidates the FREELY chain-parameter candidate and its regression coverage on top of the FREELY chain-selector and genesis/network workstream. It makes the approved design baseline testable without enabling ordinary FREELY production startup or launching a network.

## Owner-approved design baseline — 18 November 2026

On 18 November 2026, the project owner explicitly approved the four design proposals covering proof of work/difficulty, network identity, the genesis template, and the script activation matrix. The approved design baseline is:

- SHA-256d UTXO proof of work; 8 decimal places and integer-only consensus money.
- Initial subsidy 50 FLY; 210,000-block halving; no premine, founder allocation or ICO.
- Target spacing 600 seconds; target timespan 1,209,600 seconds; 2,016-block adjustment interval; 1/4–4x retarget clamp; minimum-difficulty blocks disabled; production retargeting enabled.
- Approved `powLimit`: `00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff`.
- Approved genesis initial difficulty encoding: `nBits = 0x1d00ffff`.
- BIP94 time-warp mitigation enabled from genesis.
- Approved network identity: message magic `fa c3 b7 d1`; P2P port `49444`; RPC port `49445`; P2PKH prefix `55`; P2SH prefix `117`; WIF prefix `183`; extended public/private prefixes `04464c59` / `04666c79`; Bech32 HRP `fly`.
- Approved genesis template timestamp `1794960000`, one-transaction coinbase/Merkle commitment `c28adb462751d49bfd4ab13451f8f2801634f28d333d1493e93b6077dd6cdfa1`, and a 50 FLY genesis reward that is permanently unspendable and remains included in scheduled issuance accounting.
- Approved activation matrix: BIP34, BIP65, BIP66, CSV and SegWit active at height 1; P2SH and Taproot active from genesis.

These are owner-approved design parameters, not permission to activate a production network. The scheduled subsidy total remains 20,999,999.9769 FLY.

## Remaining genesis-identity approval

The candidate implementation uses nonce `2238688522` and derives block hash `0000000000e43054a010a58bde94ce509904f40f697fb874eedd426755cc2f78`. These derived nonce/hash values are regression candidates only; the owner has not approved them as the final production genesis identity. Final nonce/hash sign-off and a separate production-launch authorization remain outstanding.

## Startup and mode boundary in this branch

- `CChainParams::FreelyCandidate()` is exposed for regression tests and offline parameter inspection.
- `CreateChainParams(..., ChainType::FREELY)` still throws. Ordinary FREELY chain selection and production startup remain fail-closed.
- This PR branch does **not** include the offline-development or loopback-private startup modes. Those changes are currently isolated in PR #21, which still targets the closed, unmerged PR #20 candidate branch and must be reconciled onto this PR's candidate base before integration.
- The candidate object does not configure DNS/fixed seeds, launch a listener, activate a public network or authorize mining deployment.

## Regression coverage

The candidate implementation is accompanied by:

- exhaustive chain-type and network-magic tests;
- genesis header and coinbase/Merkle regression checks;
- integer-only monetary schedule and subsidy-cap tests;
- compact-target and retarget-boundary vectors using clearly synthetic fixtures where appropriate;
- a BIP94 timestamp-boundary functional regression on upstream regtest, not on a launched FREELY network;
- startup tests that preserve the production fail-closed boundary.

The focused GitHub Actions workflow and the full Bitcoin Core CI matrix must both complete successfully on the exact branch head before any merge decision. Queued, pending, skipped, cancelled or infrastructure-failed jobs are not validation passes.

## Release restrictions

This branch does not authorize final genesis nonce/hash activation, DNS or fixed seeds, public testnet/mainnet launch, mining deployment, paid infrastructure, deployment or public network exposure. It does not imply inherited Bitcoin hashpower or security.
