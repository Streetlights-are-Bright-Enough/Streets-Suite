import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ps2_suite


class ConfigTests(unittest.TestCase):
    def test_load_cfg_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.json"
            p.write_text(json.dumps({"emulator_path": "pcsx2", "bios_dir": "./bios", "roms_dir": "./roms"}), encoding="utf-8")
            cfg = ps2_suite.load_cfg(p)
            self.assertEqual(cfg["boot_timeout_s"], 20)
            self.assertEqual(cfg["boot_mode"], "disc")

    def test_invalid_timeout_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.json"
            p.write_text(json.dumps({"emulator_path": "pcsx2", "bios_dir": "./bios", "roms_dir": "./roms", "boot_timeout_s": 0}), encoding="utf-8")
            with self.assertRaises(ValueError):
                ps2_suite.load_cfg(p)

    def test_invalid_boot_mode_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.json"
            p.write_text(json.dumps({"emulator_path": "pcsx2", "bios_dir": "./bios", "roms_dir": "./roms", "boot_mode": "nope"}), encoding="utf-8")
            with self.assertRaises(ValueError):
                ps2_suite.load_cfg(p)


class DiscoveryTests(unittest.TestCase):
    def test_discover_extensions_case_insensitive(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "A.ISO"
            p2 = Path(td) / "b.txt"
            p1.write_bytes(b"hello")
            p2.write_bytes(b"x")
            found = ps2_suite.discover_images(td, [".iso"])
            self.assertEqual([str(x) for x in found], [str(p1)])

    def test_inventory_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p1 = Path(td) / "game.iso"
            p1.write_bytes(b"abc")
            inv = ps2_suite.inventory_images(td, [".iso"])
            self.assertEqual(len(inv), 1)
            self.assertEqual(inv[0]["size_bytes"], 3)
            self.assertEqual(inv[0]["sha256"], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


class CommandAndReportTests(unittest.TestCase):
    def test_build_command_disc_mode(self):
        cfg = {"emulator_path": "pcsx2", "bios_dir": "./bios", "boot_mode": "disc"}
        cmd = ps2_suite.build_pcsx2_command(cfg, "./roms/game.iso")
        self.assertIn("--bios-path", cmd)
        self.assertNotIn("--elf", cmd)
        self.assertEqual(cmd[-1], "./roms/game.iso")

    def test_build_command_elf_mode(self):
        cfg = {"emulator_path": "pcsx2", "bios_dir": "./bios", "boot_mode": "elf"}
        cmd = ps2_suite.build_pcsx2_command(cfg, "./apps/test.elf")
        self.assertIn("--elf", cmd)
        self.assertEqual(cmd[-1], "./apps/test.elf")

    @patch("ps2_suite.time.sleep", return_value=None)
    @patch("ps2_suite.subprocess.Popen")
    def test_smoke_test_marks_pass_when_timeout(self, popen_mock, _sleep):
        cfg = {
            "emulator_path": "pcsx2",
            "bios_dir": "./bios",
            "boot_mode": "disc",
            "boot_timeout_s": 1,
            "smoke_runtime_s": 1,
        }
        proc = popen_mock.return_value

        def wait_side_effect(timeout=None):
            if timeout == 1:
                raise ps2_suite.subprocess.TimeoutExpired(cmd="pcsx2", timeout=1)
            return 0

        proc.wait.side_effect = wait_side_effect
        proc.poll.return_value = 0
        proc.returncode = 0

        result = ps2_suite.smoke_test_image(cfg, "game.iso")
        self.assertTrue(result["passed"])

    def test_markdown_report(self):
        md = ps2_suite.render_markdown_report([
            {"image": "a.iso", "passed": True, "exit_code": 0, "elapsed_s": 1.2},
            {"image": "b.iso", "passed": False, "exit_code": 1, "elapsed_s": 0.5},
        ])
        self.assertIn("1/2 passed", md)


class DiagTests(unittest.TestCase):
    def test_list_contains_requested_categories(self):
        keys = set(ps2_suite.DIAG_TESTS.keys())
        self.assertTrue({
            "gamepad_tester",
            "ram_tester",
            "vram_tester",
            "gpu_tester",
            "cpu_tester",
            "memory_card_reader",
            "laser_tester",
        }.issubset(keys))

    @patch("ps2_suite.smoke_test_image")
    def test_run_named_diagnostics(self, smoke_mock):
        smoke_mock.return_value = {"passed": True, "command": "pcsx2 --elf x", "exit_code": 0, "elapsed_s": 0.4}
        with tempfile.TemporaryDirectory() as td:
            elf = Path(td) / "pad.elf"
            elf.write_bytes(b"ELF")
            cfg = {
                "diagnostic_targets": {
                    "gamepad_tester": str(elf),
                },
                "boot_mode": "disc",
                "emulator_path": "pcsx2",
                "bios_dir": "./bios",
                "roms_dir": "./roms",
                "boot_timeout_s": 1,
                "smoke_runtime_s": 1,
            }
            out = ps2_suite.run_named_diagnostics(cfg)
            by_name = {r["test"]: r for r in out}
            self.assertTrue(by_name["gamepad_tester"]["configured"])
            self.assertTrue(by_name["gamepad_tester"]["passed"])
            self.assertFalse(by_name["ram_tester"]["configured"])


class DiagCommandTests(unittest.TestCase):
    @patch("ps2_suite.run_named_diagnostics")
    @patch("ps2_suite.Path.write_text")
    def test_cmd_diag_allow_missing_returns_zero(self, _write, run_mock):
        run_mock.return_value = [
            {"test": "gamepad_tester", "configured": True, "passed": False, "note": "Missing target"},
        ]

        class Args:
            config = "x.json"
            report = "out.md"
            debug = False
            allow_missing = True

        with patch("ps2_suite.load_cfg", return_value={}):
            code = ps2_suite.cmd_diag(Args())
        self.assertEqual(code, 0)



if __name__ == "__main__":
    unittest.main()
