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
The following commit records the BBR port, config and documentation. The
cloud-bbrv3 branch then selects the official cloud configuration from the
matching Debian linux-config-7.2 package. Cloud and generic flavours share
this same Debian source; no extra TCP changes are needed just for the flavour.
No claim of upstream history or official Debian/Google release status is intended.

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

This branch uses config.amd64_none_cloud-amd64.xz from Debian linux-config-7.2
7.2.9-1~bpo13+1. Its unmodified, decompressed copy is tracked alongside the
custom configuration. SHA256:
7507099cdcba1b1477078222b31fb1b13d8be1f2b9e20c411939e7a0cf91f484.

Only four configuration values differ from that official cloud input:

- CONFIG_LOCALVERSION="-deb13-cloud-bbrv3".
- CONFIG_MODULE_SIG_KEY="certs/signing_key.pem" (generate a local key).
- CONFIG_SYSTEM_TRUSTED_KEYS="" (no distribution certificate file dependency).
- CONFIG_MODULE_SIG_ALL=y (sign modules during modules_install).

Preserve official debug info, BTF, module BTF, Rust, virtio and cloud driver
choices. No localmodconfig or additional driver pruning is used. BBR remains
a module and still uses the congestion-control name "bbr". Official build-time
cubic/fq_codel defaults are retained. No running sysctl is changed.

The generic main branch previously disabled debug info, BTF and Rust to fit
the small VPS. That configuration is not used here. Lack of BTF on that old
variant coincided with a systemd bpf-restrict-fs load error; enabling BTF here
is not by itself proof that the error is resolved without a new boot test.
This is not Debian's signed Secure Boot kernel. No private key is committed.

## Validation boundaries

For this cloud branch, only static source/config checks are performed:

- Reverse application check for the saved BBR patch.
- Configuration input hash, allowed-difference and critical-feature tests.
- Configuration checker rejects BTF or Rust silently disappearing.
- Whitespace and repository-artifact checks.

There is no cloud build, link, modpost, package, module-load or boot test yet.
The expected cloud release is 7.2.9-deb13-cloud-bbrv3. Configuration normalization
must be performed on the build machine with the real BTF/Rust dependencies;
it has not been simulated using fake tools on the original VPS.

Earlier validation of this same TCP port with the generic configuration:

- Individual compilation of tcp_bbr.o, tcp_input.o, tcp_output.o, tcp_timer.o,
  tcp.o, tcp_cong.o and bpf_tcp_ca.o with GCC 14.
- The original VPS full build was stopped for migration; the user later built
  the generic image on another machine and uploaded the image package.
- That generic image was installed and booted on the original VPS. The running
  release was 7.2.9-deb13-bbrv3; tcp_bbr module metadata and a fresh loopback
  TCP_CC_INFO query both reported BBR version 3.

These generic results do not establish that the new cloud configuration builds
or boots correctly. Loss/reordering/ECN tests, sustained traffic, regressions,
performance and cloud reboot-recovery tests remain outstanding. Experimental.

The verifier checks byte offset 39 (bbr_version) of this tree's extended BBR
TCP_CC_INFO layout on a fresh loopback connection. It checks version only,
not network correctness or performance.
