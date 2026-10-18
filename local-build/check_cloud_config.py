#!/usr/bin/env python3
"""Check saved or normalized cloud config without compiling or changing it."""
import argparse
from pathlib import Path
import re
import sys

EXPECTED = {
    "CONFIG_LOCALVERSION": '"-deb13-cloud-bbrv3"',
    "CONFIG_LOCALVERSION_AUTO": "n",
    "CONFIG_MODULES": "y",
    "CONFIG_TCP_CONG_BBR": "m",
    "CONFIG_DEFAULT_TCP_CONG": '"cubic"',
    "CONFIG_DEFAULT_NET_SCH": '"fq_codel"',
    "CONFIG_DEBUG_INFO": "y",
    "CONFIG_DEBUG_INFO_NONE": "n",
    "CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT": "y",
    "CONFIG_DEBUG_INFO_BTF": "y",
    "CONFIG_DEBUG_INFO_BTF_MODULES": "y",
    "CONFIG_RUST": "y",
    "CONFIG_BPF": "y",
    "CONFIG_BPF_SYSCALL": "y",
    "CONFIG_BPF_JIT": "y",
    "CONFIG_BPF_LSM": "y",
    "CONFIG_MODULE_SIG": "y",
    "CONFIG_MODULE_SIG_ALL": "y",
    "CONFIG_MODULE_SIG_KEY": '"certs/signing_key.pem"',
    "CONFIG_SYSTEM_TRUSTED_KEYS": '""',
    "CONFIG_SYSTEM_REVOCATION_LIST": "n",
    "CONFIG_VIRTIO_PCI": "y",
    "CONFIG_VIRTIO_BLK": "m",
    "CONFIG_VIRTIO_NET": "m",
    "CONFIG_EXT4_FS": "y",
}


def parse_config(text):
    values = {}
    for line in text.splitlines():
        if line.startswith("CONFIG_") and "=" in line:
            name, value = line.split("=", 1)
            values[name] = value
        else:
            match = re.fullmatch(r"# (CONFIG_\w+) is not set", line)
            if match:
                values[match.group(1)] = "n"
    return values


def validate(values):
    return [
        f"{name}: expected {expected}, got {values.get(name, '<missing>')}"
        for name, expected in EXPECTED.items()
        if values.get(name) != expected
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config", nargs="?", type=Path,
        default=Path(__file__).with_name("debian13-cloud-amd64-bbrv3.config"),
    )
    args = parser.parse_args()
    try:
        errors = validate(parse_config(args.config.read_text()))
    except OSError as error:
        print(error, file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print("Check toolchain/dependencies; do not silently drop BTF or Rust.", file=sys.stderr)
        return 1
    print(f"PASS: {args.config}")
    print("Cloud config retains BTF, module BTF, Rust and virtio support.")
    print("BBR is a module; Debian's cubic/fq_codel defaults are preserved.")
    print("Static config check only, not a build or runtime validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
