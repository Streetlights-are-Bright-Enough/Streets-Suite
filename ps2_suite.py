#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

DEFAULT_EXTS = [".iso", ".chd", ".cso", ".bin", ".gz"]
DIAG_TESTS = {
    "gamepad_tester": "Controller input / button matrix",
    "ram_tester": "Main RAM read/write pattern check",
    "vram_tester": "GS VRAM pattern check",
    "gpu_tester": "GS rendering pipeline check",
    "cpu_tester": "EE core instruction/stability check",
    "memory_card_reader": "MC0/MC1 read/write test",
    "laser_tester": "Optical drive read/seek test",
}


def load_cfg(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg.setdefault("memcards_dir", "./memcards")
    cfg.setdefault("save_states_dir", "./savestates")
    cfg.setdefault("boot_timeout_s", 20)
    cfg.setdefault("smoke_runtime_s", 8)
    cfg.setdefault("image_extensions", list(DEFAULT_EXTS))
    cfg.setdefault("boot_mode", "disc")  # disc | elf
    cfg.setdefault("diagnostic_targets", {})

    need = ["emulator_path", "bios_dir", "roms_dir"]
    missing = [k for k in need if not cfg.get(k)]
    if missing:
        raise ValueError("missing: " + ", ".join(missing))
    if cfg["boot_timeout_s"] <= 0 or cfg["smoke_runtime_s"] <= 0:
        raise ValueError("timeouts must be > 0")
    if not cfg["image_extensions"]:
        raise ValueError("image_extensions empty")
    if cfg["boot_mode"] not in {"disc", "elf"}:
        raise ValueError("boot_mode must be disc or elf")
    if not isinstance(cfg["diagnostic_targets"], dict):
        raise ValueError("diagnostic_targets must be an object")
    return cfg


def discover_images(roms_dir, exts):
    root = Path(roms_dir)
    if not root.exists():
        return []
    cooked = set()
    for e in exts:
        e = e.lower()
        if not e.startswith("."):
            e = "." + e
        cooked.add(e)

    out = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in cooked:
            out.append(p)
    out.sort()
    return out


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def inventory_images(roms_dir, exts):
    rows = []
    for img in discover_images(roms_dir, exts):
        rows.append(
            {
                "path": str(img),
                "size_bytes": img.stat().st_size,
                "sha256": file_sha256(img),
            }
        )
    return rows


def build_pcsx2_command(cfg, image_path):
    cmd = [
        cfg["emulator_path"],
        "--nogui",
        "--bios",
        "--bios-path",
        cfg["bios_dir"],
        "--fullscreen",
    ]

    if cfg.get("boot_mode", "disc") == "elf":
        cmd += ["--elf", image_path]
    else:
        cmd += [image_path]
    return cmd


def smoke_test_image(cfg, image_path):
    cmd = build_pcsx2_command(cfg, image_path)
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    passed = False
    try:
        p.wait(timeout=cfg["boot_timeout_s"])
    except subprocess.TimeoutExpired:
        passed = True

    if p.poll() is None:
        time.sleep(cfg["smoke_runtime_s"])
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=3)

    return {
        "image": image_path,
        "command": " ".join(cmd),
        "passed": passed,
        "exit_code": -1 if p.returncode is None else p.returncode,
        "elapsed_s": round(time.time() - t0, 2),
    }


def run_named_diagnostics(cfg):
    results = []
    targets = cfg.get("diagnostic_targets", {})
    for test_name, description in DIAG_TESTS.items():
        target = targets.get(test_name)
        if not target:
            results.append(
                {
                    "test": test_name,
                    "description": description,
                    "configured": False,
                    "passed": False,
                    "note": "No target configured",
                }
            )
            continue

        p = Path(target)
        if not p.exists():
            results.append(
                {
                    "test": test_name,
                    "description": description,
                    "configured": True,
                    "passed": False,
                    "note": f"Missing target: {target}",
                }
            )
            continue

        mode = "elf" if p.suffix.lower() == ".elf" else "disc"
        run_cfg = dict(cfg)
        run_cfg["boot_mode"] = mode
        boot = smoke_test_image(run_cfg, str(p))

        results.append(
            {
                "test": test_name,
                "description": description,
                "configured": True,
                "passed": bool(boot["passed"]),
                "note": f"{mode} boot, exit={boot['exit_code']}",
                "command": boot["command"],
                "elapsed_s": boot["elapsed_s"],
            }
        )
    return results


def render_markdown_report(results):
    lines = ["# PS2 Test Report", "", "| Image | Passed | Exit Code | Elapsed (s) |", "|---|---:|---:|---:|"]
    pass_count = 0
    for r in results:
        ok = bool(r.get("passed"))
        if ok:
            pass_count += 1
        lines.append(f"| {r['image']} | {'✅' if ok else '❌'} | {r['exit_code']} | {r['elapsed_s']} |")
    lines.append("")
    lines.append(f"**Summary:** {pass_count}/{len(results)} passed")
    return "\n".join(lines)


def render_diag_report(results):
    lines = ["# PS2 Hardware-Oriented Diagnostic Report", "", "| Test | Configured | Passed | Notes |", "|---|---:|---:|---|"]
    ok_count = 0
    configured = 0
    for r in results:
        if r["configured"]:
            configured += 1
        if r["passed"]:
            ok_count += 1
        lines.append(f"| {r['test']} | {'✅' if r['configured'] else '❌'} | {'✅' if r['passed'] else '❌'} | {r['note']} |")
    lines.append("")
    lines.append(f"**Summary:** {ok_count}/{len(results)} passing, {configured}/{len(results)} configured")
    return "\n".join(lines)


def cmd_validate(args):
    load_cfg(args.config)
    print("Config OK")
    return 0


def cmd_inventory(args):
    cfg = load_cfg(args.config)
    print(json.dumps(inventory_images(cfg["roms_dir"], cfg["image_extensions"]), indent=2))
    return 0


def cmd_smoke(args):
    cfg = load_cfg(args.config)
    images = discover_images(cfg["roms_dir"], cfg["image_extensions"])
    if not images:
        print("No PS2 images found")
        return 1

    results = []
    for img in images:
        results.append(smoke_test_image(cfg, str(img)))

    report = render_markdown_report(results)
    Path(args.report).write_text(report, encoding="utf-8")
    print(f"Wrote report: {args.report}")

    for r in results:
        if not r["passed"]:
            return 2
    return 0


def cmd_list_tests(_args):
    print(json.dumps(DIAG_TESTS, indent=2))
    return 0


def cmd_diag(args):
    cfg = load_cfg(args.config)
    results = run_named_diagnostics(cfg)
    report = render_diag_report(results)
    Path(args.report).write_text(report, encoding="utf-8")
    print(f"Wrote report: {args.report}")

    if args.debug:
        for r in results:
            print(f"[{r['test']}] configured={r['configured']} passed={r['passed']} note={r['note']}")

    if args.allow_missing:
        return 0

    # strict mode: nonzero if any configured test failed OR nothing configured
    if not any(r["configured"] for r in results):
        return 1
    for r in results:
        if r["configured"] and not r["passed"]:
            return 2
    return 0


def parser():
    p = argparse.ArgumentParser(description="ps2 suite")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("validate-config")
    a.add_argument("--config", required=True)
    a.set_defaults(func=cmd_validate)

    b = sub.add_parser("inventory")
    b.add_argument("--config", required=True)
    b.set_defaults(func=cmd_inventory)

    c = sub.add_parser("smoke")
    c.add_argument("--config", required=True)
    c.add_argument("--report", default="ps2_report.md")
    c.set_defaults(func=cmd_smoke)

    d = sub.add_parser("list-tests")
    d.set_defaults(func=cmd_list_tests)

    e = sub.add_parser("diag")
    e.add_argument("--config", required=True)
    e.add_argument("--report", default="ps2_diag_report.md")
    e.add_argument("--debug", action="store_true", help="Print per-test status details")
    e.add_argument("--allow-missing", action="store_true", help="Return success even when tests are missing/failing (sanity check mode)")
    e.set_defaults(func=cmd_diag)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
