# FREELY chain-parameter candidate status

**Status:** engineering candidate for isolated development and regression testing only  
**Source baseline:** Bitcoin Core v32.1  
**Production activation:** not authorized

## Scope

This branch consolidates the FREELY chain-parameter candidate and its regression coverage on top of the FREELY chain-selector and genesis/network workstream. It is intended to make the implementation reviewable and testable without enabling a production network.

The approved project baseline currently includes:

- 8 decimal places and integer-only consensus money;
- an initial block subsidy of 50 FLY;
- a 210,000-block halving interval;
- 600-second target spacing and a 2,016-block difficulty interval;
- no premine, founder allocation or ICO.

These facts do not by themselves authorize the remaining production consensus or identity parameters.

## Candidate-only boundary

The derived genesis nonce and hash in the implementation are regression candidates, not the final production network identity. They require explicit owner sign-off before production use.

The exact production decisions for powLimit, genesis commitments, initial difficulty, BIP94/time-warp policy, activation matrix and final network identity must be reviewed and explicitly approved. This document does not infer or approve those values.

Normal FREELY chain selection remains fail-closed. The candidate is exposed only through the explicit offline-development and loopback-private modes, which apply network isolation checks. Loopback-private mode is intended for same-host development; it is not a public or LAN testnet.

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

This branch does not authorize production genesis activation, DNS or fixed seeds, public testnet/mainnet launch, mining deployment, paid infrastructure, deployment or public network exposure. It does not imply inherited Bitcoin hashpower or security.
