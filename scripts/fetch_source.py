"""Fetch one package's source exactly as pinned in packages.json and unpack it into <dest>.

usage: fetch_source.py <package-name> <dest-dir>

sdists are verified against the sha256 from upstream's uv.lock before extraction; git sources
are checked out at the pinned commit. Archive members are validated (no absolute paths, no
'..', no links) before anything is written.
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import tarfile
import urllib.request

name, dest = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
root = pathlib.Path(__file__).resolve().parent.parent
pkg = next(p for p in json.loads((root / "packages.json").read_text())["packages"] if p["name"] == name)
dest.mkdir(parents=True, exist_ok=True)
if any(dest.iterdir()):
    sys.exit(f"{dest} is not empty")

if "git" in pkg:
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", pkg["git"]], check=True)
    subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1", "origin", pkg["rev"]], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", "FETCH_HEAD"], check=True)
    head = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if head != pkg["rev"]:
        sys.exit(f"checked out {head}, expected {pkg['rev']}")
    print(f"{name}: git {pkg['rev']}")
    sys.exit(0)

archive = dest.parent / (name + ".tar.gz")
with urllib.request.urlopen(pkg["sdist"]) as resp:
    data = resp.read()
digest = hashlib.sha256(data).hexdigest()
if digest != pkg["sha256"]:
    sys.exit(f"{name}: sha256 mismatch: got {digest}, expected {pkg['sha256']}")
archive.write_bytes(data)

with tarfile.open(archive, "r:gz") as tf:
    members = tf.getmembers()
    tops = {m.name.split("/", 1)[0] for m in members}
    if len(tops) != 1:
        sys.exit(f"{name}: sdist has {len(tops)} top-level entries")
    top = tops.pop()
    for m in members:
        parts = pathlib.PurePosixPath(m.name).parts
        if m.name.startswith("/") or ".." in parts or not (m.isfile() or m.isdir()):
            sys.exit(f"{name}: unsafe archive member {m.name!r}")
    for m in members:
        rel = pathlib.PurePosixPath(m.name).relative_to(top)
        target = dest.joinpath(*rel.parts)
        if m.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with tf.extractfile(m) as src, open(target, "wb") as out:
            out.write(src.read())
        if m.mode & 0o111:
            target.chmod(0o755)
print(f"{name}: sdist {pkg['version']} sha256 ok -> {dest}")
