# BBRv3 local port: design notes and validation boundary

## Inputs

- Debian linux-source-7.2 7.2.9-1~bpo13+1 (Debian patches already applied).
- Google BBR v3 commit `90210de4b779d40496dee0b89081780eeddf2a60`.
- Google branch base: Linux 6.13.7, commit
  `648e04a805652f513af04b47035cde896addf9b0`.
- Original Google tcp_bbr.c SHA256:
  `04ba1e8b436b88eb0716f3d2a64a9be5a5d946ba3169a590d7bb533c320bdc51`.
- Debian original source archive SHA256:
  `29f9eafc0826dcc54ff9ace28a326c265f4752c22f57a87027446b5353451f25`.

The first repository commit imports the full Debian source snapshot. Its root
.gitignore is adjusted to remove Debian packaging's ignore-everything rule.
The following commit records the BBR port, config and documentation. No claim
of upstream history or official Debian/Google release status is intended.

## Changes

- Use Google's BBRv3 algorithm and its loss/inflight/rate-sampling prerequisites.
- Rate sampling no longer lives in a separate tcp_rate.c in this Debian source;
  adapt those changes to tcp_input.c and tcp_output.c instead.
- Enlarge CC private storage; extend BBR diagnostics with its algorithm version.
- Record transmit-time inflight/loss snapshots, maintain them across skb
  split/merge, expose individual lost-skb events, and pass TLP recovery state.
- Broaden application-limited checks in ACK and timer handling.
- Preserve the existing min_tso_segs callback for other algorithms, adding the
  optional BBR tso_segs callback instead of replacing the old interface.
- Dispatch BBR TX_START through the newer dedicated cwnd_event_tx_start callback.
- Avoid newer Accurate ECN bit allocations: use bits 5/6 for BBR-specific TCP
  ECN state and bit 5 for the CC CE-events flag.
- Resolve optional low-latency route indication at BBR initialization. The
  Google DCTCP-style ECN path is restricted to RFC3168 mode and explicitly
  marked routes; it is not enabled for AccECN mode. No ECN sysctl or route
  feature is enabled by the config or these build instructions.
- Do not reuse Google's TCPI_OPT_ECN_LOW=128: Debian already assigns that bit
  to TCPI_OPT_TFO_CHILD. Omit that optional tcp_info diagnostic while retaining
  BBR's separate extended congestion-control diagnostic.

This is a local compatibility adaptation, not proof of semantic correctness
under every loss/reordering/ECN condition. Those paths require runtime tests.

## Configuration

The saved config starts from Debian's config-7.2.6+deb13-amd64. Most hardware
and software features are retained; localmodconfig was not used. Main changes:

- CONFIG_LOCALVERSION="-deb13-bbrv3"; automatic Git suffix disabled.
- BBR remains a module and still uses the congestion-control name "bbr".
- Disable debug info, BTF and Rust to fit a small build VPS.
- Clear distribution certificate paths; keep module signing with a local key.
- No kernel installation, bootloader edits or runtime sysctl changes performed.

Disabling BTF reduces BPF CO-RE/observability functionality; disabling Rust
removes Rust-dependent drivers. This is not Debian's signed Secure Boot kernel.

## Validation completed

- `git diff --check`.
- Individual compilation of tcp_bbr.o, tcp_input.o, tcp_output.o, tcp_timer.o,
  tcp.o, tcp_cong.o and bpf_tcp_ca.o with the saved config and GCC 14.
- Kernel release resolves to 7.2.9-deb13-bbrv3.
- The diagnostic verifier on the old official kernel sees only the old 20-byte
  BBR info structure and correctly does not claim BBRv3.

## Not completed

The original full build was manually stopped to move to another build machine.
The full compile/link/modpost and binary packaging are not yet validated.
No custom kernel was installed or booted. Module loading, diagnostic version 3,
loss/reordering/ECN tests, sustained traffic, regressions, performance and reboot
recovery tests remain to be performed. Treat this tree as experimental.

The verifier checks byte offset 39 (bbr_version) of this tree's extended BBR
TCP_CC_INFO layout on a fresh loopback connection. It checks version only,
not network correctness or performance.
