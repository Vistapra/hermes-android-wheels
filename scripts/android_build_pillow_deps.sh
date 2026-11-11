#!/bin/sh
# Pillow needs zlib and libjpeg where its setup.py looks: the cross Python prefix.
#   zlib          - part of Android itself; copy the NDK's header and link stub.
#   libjpeg-turbo - built here as a static, position-independent library.
set -eu
PREFIX_DIR="$1"
TRIPLET="${CIBW_HOST_TRIPLET:?CIBW_HOST_TRIPLET not set}"
API="${ANDROID_API_LEVEL:-24}"
SYSROOT="$(dirname "$CC")/../sysroot"

cp "$SYSROOT/usr/include/zlib.h" "$SYSROOT/usr/include/zconf.h" "$PREFIX_DIR/include/"
cp "$SYSROOT/usr/lib/$TRIPLET/$API/libz.so" "$PREFIX_DIR/lib/"

JPEG_VERSION=3.2.1
JPEG_SHA256=c27ad72a68da151177929aa969ae773a2da5ac2af9ce946079314fdac8cece7f
WORK="$(mktemp -d)"
curl -fsSL -o "$WORK/jpeg.tar.gz" \
    "https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/$JPEG_VERSION/libjpeg-turbo-$JPEG_VERSION.tar.gz"
echo "$JPEG_SHA256  $WORK/jpeg.tar.gz" | sha256sum -c -
tar -xzf "$WORK/jpeg.tar.gz" -C "$WORK"

# NEON on arm64 needs no assembler; x86_64 SIMD would need nasm, so it is left off there.
SIMD=ON
[ "$TRIPLET" = "x86_64-linux-android" ] && SIMD=OFF

cmake -S "$WORK/libjpeg-turbo-$JPEG_VERSION" -B "$WORK/build" \
    -DCMAKE_TOOLCHAIN_FILE="$CMAKE_TOOLCHAIN_FILE" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX_DIR" \
    -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DENABLE_SHARED=OFF -DENABLE_STATIC=ON \
    -DWITH_TURBOJPEG=OFF -DWITH_SIMD="$SIMD"
cmake --build "$WORK/build" --parallel "${CPU_COUNT:-2}"
cmake --install "$WORK/build"
ls -l "$PREFIX_DIR/lib/libjpeg.a" "$PREFIX_DIR/include/jpeglib.h"
