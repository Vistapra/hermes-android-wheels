#!/bin/sh
# cibuildwheel before-build hook for the experimental (tier 3) Android builds.
#
# cibuildwheel replaces CFLAGS/LDFLAGS with its own cross values, which only search
# <cross>/python/prefix/{include,lib}. So instead of adding search paths, this script places
# what each build needs inside that prefix.
set -eu

if [ -n "${PYO3_CROSS_LIB_DIR:-}" ]; then
    PREFIX_DIR=$(dirname "$PYO3_CROSS_LIB_DIR")
else
    PREFIX_DIR=$(printf '%s\n' "${CFLAGS:-}" | tr ' ' '\n' | sed -n 's|^-I\(.*/python/prefix\)/include$|\1|p' | head -n 1)
fi
if [ -z "$PREFIX_DIR" ] || [ ! -d "$PREFIX_DIR/include" ]; then
    echo "android_before_build: cannot locate the cross Python prefix" >&2
    env | grep -E '^(CFLAGS|LDFLAGS|PYO3_|PKG_CONFIG|CIBW_HOST)' >&2 || true
    exit 1
fi
echo "android_before_build: prefix=$PREFIX_DIR package=${HNA_PACKAGE:-?} host=${CIBW_HOST_TRIPLET:-?}"

# <Python.h> for C sources compiled by cc-rs (cryptography): the prefix include dir is on the
# search path, the python3.x subdirectory is not.
for dir in "$PREFIX_DIR"/include/python3.*; do
    [ -d "$dir" ] || continue
    for entry in "$dir"/*; do
        ln -sfn "$entry" "$PREFIX_DIR/include/$(basename "$entry")"
    done
done

# Prebuilt native dependencies fetched by fetch_deps.py (libffi; OpenSSL headers).
if [ -n "${DEPS_DIR:-}" ] && [ -d "$DEPS_DIR/include" ]; then
    cp -a "$DEPS_DIR/include/." "$PREFIX_DIR/include/"
    if [ -d "$DEPS_DIR/lib" ]; then
        # Never replace libraries the Python release already ships (libssl_python.so etc.).
        cp -an "$DEPS_DIR/lib/." "$PREFIX_DIR/lib/"
    fi
fi

if [ "${HNA_PACKAGE:-}" = "pillow" ]; then
    sh "$(dirname "$0")/android_build_pillow_deps.sh" "$PREFIX_DIR"
fi
