"""Make every extension module in an Android wheel depend on libpython.

usage: repair_android_wheel.py <wheel> <libpython-soname>     e.g. ... libpython3.14.so

Android loads extension modules with local symbol visibility, so an extension that uses the
CPython C API must name libpython in DT_NEEDED or the dynamic linker cannot resolve Py* symbols
("cannot locate symbol _Py_DecRef"). PyO3's abi3 builds leave that dependency out. Upstream
hermes-agent repairs its Termux wheels the same way (scripts/termux/python_linkage.py).
Wheels that are already linked are left byte-for-byte untouched.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

wheel = pathlib.Path(sys.argv[1]).resolve()
libpython = sys.argv[2]
readelf = shutil.which("llvm-readelf") or shutil.which("readelf")
if not readelf or not shutil.which("patchelf"):
    sys.exit("readelf and patchelf are required")

work = pathlib.Path(tempfile.mkdtemp(prefix="wheel-link-"))
subprocess.run([sys.executable, "-m", "wheel", "unpack", "-d", str(work), str(wheel)], check=True,
               stdout=subprocess.DEVNULL)
root = next(p for p in work.iterdir() if p.is_dir())

patched = []
for so in sorted(root.rglob("*.so")):
    needed = subprocess.check_output(["patchelf", "--print-needed", str(so)], text=True).split()
    if any(name.startswith("libpython") for name in needed):
        continue
    symbols = subprocess.check_output([readelf, "--dyn-syms", "--wide", str(so)], text=True)
    uses_c_api = any(" UND " in line and line.split()[-1].startswith(("Py", "_Py"))
                     for line in symbols.splitlines())
    if not uses_c_api:
        continue
    subprocess.run(["patchelf", "--add-needed", libpython, str(so)], check=True)
    after = subprocess.check_output(["patchelf", "--print-needed", str(so)], text=True).split()
    if libpython not in after:
        sys.exit(f"patchelf did not add {libpython} to {so}")
    patched.append(str(so.relative_to(root)))

if patched:
    wheel.unlink()
    subprocess.run([sys.executable, "-m", "wheel", "pack", "-d", str(wheel.parent), str(root)], check=True,
                   stdout=subprocess.DEVNULL)
    if not wheel.exists():
        sys.exit(f"repacked wheel has a different name than {wheel.name}")
    print(f"{wheel.name}: linked {libpython} into {', '.join(patched)}")
else:
    print(f"{wheel.name}: already linked, unchanged")
shutil.rmtree(work, ignore_errors=True)
