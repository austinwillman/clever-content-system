#!/bin/sh
set -eu

if [ "$#" -ne 3 ]; then
  echo "Usage: verify-image.sh <image-path> <expected-width> <expected-height>" >&2
  exit 64
fi

image_path=$1
expected_width=$2
expected_height=$3

if [ ! -f "$image_path" ]; then
  echo "Image not found: $image_path" >&2
  exit 66
fi

case $expected_width in
  ''|*[!0-9]*)
    echo "Expected width must be a positive integer: $expected_width" >&2
    exit 64
    ;;
esac

case $expected_height in
  ''|*[!0-9]*)
    echo "Expected height must be a positive integer: $expected_height" >&2
    exit 64
    ;;
esac

if [ "$expected_width" -eq 0 ] || [ "$expected_height" -eq 0 ]; then
  echo "Expected dimensions must be greater than zero" >&2
  exit 64
fi

if ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffprobe is required but was not found" >&2
  exit 69
fi

dimensions=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height \
  -of csv=s=x:p=0 "$image_path")
expected="${expected_width}x${expected_height}"

if [ "$dimensions" != "$expected" ]; then
  echo "FAIL dimensions: expected $expected, got $dimensions" >&2
  exit 1
fi

codec=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name \
  -of default=noprint_wrappers=1:nokey=1 "$image_path")

bytes=$(wc -c < "$image_path" | tr -d ' ')

echo "PASS dimensions: $dimensions"
echo "Codec: $codec"
echo "Bytes: $bytes"
echo "Visual QA still required: exact copy, official logo, source fidelity, safe region, contrast, and phone-size readability"
