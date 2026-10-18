#!/usr/bin/env python3
"""Source/config tests only; never compile, install or alter a running kernel."""
import hashlib
from pathlib import Path
import unittest

from check_cloud_config import parse_config, validate

HERE = Path(__file__).resolve().parent
OFFICIAL_SHA256 = "7507099cdcba1b1477078222b31fb1b13d8be1f2b9e20c411939e7a0cf91f484"


class CloudConfigTests(unittest.TestCase):
    def setUp(self):
        self.official_path = HERE / "debian13-cloud-amd64.official.config"
        self.official = parse_config(self.official_path.read_text())
        self.config = parse_config((HERE / "debian13-cloud-amd64-bbrv3.config").read_text())

    def test_official_input_hash(self):
        self.assertEqual(hashlib.sha256(self.official_path.read_bytes()).hexdigest(), OFFICIAL_SHA256)

    def test_saved_config_passes(self):
        self.assertEqual(validate(self.config), [])

    def test_only_documented_config_changes(self):
        changed = {
            key for key in self.official.keys() | self.config.keys()
            if self.official.get(key) != self.config.get(key)
        }
        self.assertEqual(changed, {
            "CONFIG_LOCALVERSION", "CONFIG_MODULE_SIG_KEY",
            "CONFIG_SYSTEM_TRUSTED_KEYS", "CONFIG_MODULE_SIG_ALL",
        })

    def test_btf_and_rust_preserved_from_official(self):
        for key in ("CONFIG_DEBUG_INFO_BTF", "CONFIG_DEBUG_INFO_BTF_MODULES", "CONFIG_RUST"):
            with self.subTest(key=key):
                self.assertEqual(self.official[key], "y")
                self.assertEqual(self.config[key], self.official[key])

    def test_disabled_btf_is_rejected(self):
        self.config["CONFIG_DEBUG_INFO_BTF"] = "n"
        self.assertTrue(any("CONFIG_DEBUG_INFO_BTF:" in error for error in validate(self.config)))

    def test_disabled_rust_is_rejected(self):
        self.config["CONFIG_RUST"] = "n"
        self.assertTrue(any("CONFIG_RUST:" in error for error in validate(self.config)))

    def test_generic_kernel_identity_is_rejected(self):
        self.config["CONFIG_LOCALVERSION"] = '"-deb13-bbrv3"'
        self.assertTrue(any("CONFIG_LOCALVERSION:" in error for error in validate(self.config)))

    def test_newer_source_and_cloud_config_match(self):
        makefile = (HERE.parent / "Makefile").read_text()
        fields = {}
        for line in makefile.splitlines():
            if " = " in line:
                name, value = line.split(" = ", 1)
                if name in ("VERSION", "PATCHLEVEL", "SUBLEVEL"):
                    fields[name] = value
        self.assertEqual(fields, {"VERSION": "7", "PATCHLEVEL": "2", "SUBLEVEL": "9"})
        self.assertIn("# Linux/x86 7.2.9 Kernel Configuration", self.official_path.read_text())


if __name__ == "__main__":
    unittest.main()
