"""Download prebuilt Android native libraries (headers + libs) for one target into <dest>.

usage: fetch_deps.py <triplet> <dest-dir> <release-tag> [<release-tag> ...]
   e.g. fetch_deps.py aarch64-linux-android /tmp/deps libffi-3.4.4-3

Source: https://github.com/beeware/cpython-android-source-deps - the same builds the official
CPython Android releases link against (libffi, OpenSSL as libssl_python.so / libcrypto_python.so).
"""
import pathlib
import sys
import tarfile
import urllib.request

triplet, dest, tags = sys.argv[1], pathlib.Path(sys.argv[2]).resolve(), sys.argv[3:]
dest.mkdir(parents=True, exist_ok=True)
BASE = "https://github.com/beeware/cpython-android-source-deps/releases/download"
for tag in tags:
    url = f"{BASE}/{tag}/{tag}-{triplet}.tar.gz"
    archive = dest.parent / f"{tag}-{triplet}.tar.gz"
    with urllib.request.urlopen(url) as resp:
        archive.write_bytes(resp.read())
    with tarfile.open(archive, "r:gz") as tf:
        for m in tf.getmembers():
            parts = pathlib.PurePosixPath(m.name).parts
            if m.name.startswith("/") or ".." in parts:
                sys.exit(f"unsafe archive member {m.name!r} in {url}")
            if m.issym() or m.islnk():
                link = pathlib.PurePosixPath(m.linkname)
                if link.is_absolute() or ".." in link.parts:
                    sys.exit(f"unsafe link {m.name!r} -> {m.linkname!r} in {url}")
        tf.extractall(dest)
    print(f"{tag} ({triplet}) -> {dest}")
