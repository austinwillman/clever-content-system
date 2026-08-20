#!/bin/sh
set -eu

if [ "$#" -ne 2 ]; then
  echo "Usage: analyze-video.sh <video-path> <output-directory>" >&2
  exit 64
fi

video_path=$1
output_dir=$2

if [ ! -f "$video_path" ]; then
  echo "Video not found: $video_path" >&2
  exit 66
fi

if ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffprobe is required but was not found" >&2
  exit 69
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required but was not found" >&2
  exit 69
fi

mkdir -p "$output_dir"

ffprobe -v error \
  -show_entries format=filename,duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json "$video_path" > "$output_dir/metadata.json"

duration=$(ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$video_path")

interval=$(awk -v duration="$duration" 'BEGIN {
  value = duration / 12;
  if (value < 0.25) value = 0.25;
  printf "%.3f", value;
}')

ffmpeg -hide_banner -loglevel error -y -i "$video_path" \
  -vf "fps=1/$interval,scale=270:-1,tile=4x3" \
  -frames:v 1 "$output_dir/contact-sheet.jpg"

echo "$output_dir/metadata.json"
echo "$output_dir/contact-sheet.jpg"
