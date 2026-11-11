"""Emit the GitHub Actions job matrix (one job per package and Android ABI) from packages.json."""
import json
import pathlib

cfg = json.loads(pathlib.Path(__file__).resolve().parent.parent.joinpath("packages.json").read_text())
include = []
for pkg in cfg["packages"]:
    for arch in cfg["archs"]:
        include.append({
            "name": pkg["name"],
            "version": pkg["version"],
            "tier": pkg["tier"],
            "experimental": pkg["tier"] >= 3,
            "rust": bool(pkg.get("rust")),
            "arch": arch["arch"],
            "triplet": arch["triplet"],
            "rust_target": arch["rust_target"],
            "deps": " ".join(pkg.get("deps", [])),
            "environment": pkg.get("environment", ""),
            "config_settings": pkg.get("config_settings", ""),
            "prepare": bool(pkg.get("prepare")),
            "before_all": pkg.get("before_all", ""),
        })
print("include=" + json.dumps(include, separators=(",", ":")))
