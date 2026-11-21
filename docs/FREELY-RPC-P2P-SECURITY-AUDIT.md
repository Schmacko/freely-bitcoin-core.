# FREELY RPC and P2P security source audit

## Scope

This is a source-level audit of the Bitcoin Core v32.1 baseline and the current FREELY chain-plumbing branch. It records existing protections and the integration work still required. It is not a penetration test, runtime configuration test, or security certification.

## Findings verified in source

### RPC listener defaults and controls

In `src/init.cpp`:
- The RPC help text documents loopback defaults for `-rpcbind`: IPv4 `127.0.0.1` and IPv6 `::1`.
- The `-rpcbind` option is ignored unless `-rpcallowip` is also supplied.
- The help text explicitly warns against exposing RPC to untrusted networks, including the public internet.
- RPC authentication controls include cookie authentication, `-rpcauth`, and `-rpcuser` / `-rpcpassword`.
- Cookie permissions default to owner-only via umask 0077.
- `-server` defaults to false in the option registration; when disabled, initialization sets the number of RPC bind sockets and RPC client connections to zero.

In `src/rpc/server.cpp`:
- `StopRPC()` deletes the RPC authentication cookie.
- The source-level audit does not by itself prove cookie permissions, secret handling, or all shutdown/error paths are safe under every FREELY data-directory configuration.

### Production/test startup guards

On the current `freely/core-chain-implementation` branch:
- `CChainParams::IsTestChain()` reads the explicit `m_is_test_chain` flag.
- `CChainParams::IsProductionChain()` reads the explicit `m_is_production_chain` flag.
- Both flags default to false in the class declaration. A future FREELY production parameter class must explicitly set production true and test false.
- `src/init.cpp` rejects `-testactivationheight` and `-vbparams` whenever `IsProductionChain()` is true.
- Generic `-test=<option>` handling is restricted to `ChainType::REGTEST`.
- The FREELY factories currently throw rather than construct parameters, so these protections are not yet proof of a runnable FREELY node.

The upstream v32.1 baseline historically used `chain type != MAIN` for `IsTestChain()` and guarded deployment overrides by checking `ChainType::MAIN`. The FREELY workstream's explicit classification flags and production guard are therefore important integration changes; they must remain in the final chain-parameter implementation.

### P2P binding

In `src/net.cpp`, `CConnman::BindListenPort` creates and binds the listening socket and reports bind failures. This is low-level socket behavior, not a complete policy audit. The final FREELY configuration must still prove:
- Unique approved P2P port and magic.
- Correct default bind/listen behavior.
- No accidental reuse of Bitcoin network seeds or identity.
- Safe peer limits and permissions.
- No public network startup before final network parameters and launch authorization exist.

## Required tests before a production candidate

1. Start with FREELY selected but incomplete parameters: initialization must fail before P2P or RPC listeners are created.
2. Start with complete test fixtures in an isolated test harness: verify RPC disabled by default unless explicitly enabled.
3. Verify default RPC listeners are loopback-only; verify `-rpcbind` without `-rpcallowip` does not create a public listener.
4. Verify remote RPC requires an explicit allow rule and valid authentication; test invalid credentials and denied source addresses.
5. Verify cookie creation, owner-only permissions, cleanup on normal shutdown, and cleanup/error behavior.
6. Verify RPC port and P2P port cannot collide with each other or any Bitcoin network's reserved ports.
7. Verify P2P magic, ports, data directory and seeds cannot fall back to Bitcoin MAIN defaults.
8. Verify FREELY is production=true, test=false, mockable=false, and rejects all test-only activation overrides.
9. Verify `-test=<option>` and other regtest-only options cannot be used on FREELY.
10. Verify logs never print RPC passwords, auth hashes, cookie contents or other secrets.

## Status

| Area | Current assessment |
|---|---|
| Upstream RPC loopback default | Source verified |
| RPC authentication mechanisms | Source verified; runtime tests still required |
| RPC cookie cleanup | Source verified; permission/recovery tests still required |
| Production/test classification flags | Present in FREELY chain plumbing; final FREELY parameter class absent |
| Production override guard | Present in FREELY chain plumbing; runtime FREELY test blocked until params exist |
| P2P socket binding | Upstream mechanism reviewed; FREELY policy not integrated |
| FREELY RPC/P2P ports and magic | Owner decision pending |
| External security review | Not performed |

## Conclusion

The existing Bitcoin Core RPC architecture provides useful defaults, but FREELY cannot inherit a production security claim merely by inheriting that code. Final chain parameters, fail-closed startup, exact runtime tests, and independent review remain mandatory. Do not enable public RPC/P2P or launch a public FREELY network on the basis of this audit.
