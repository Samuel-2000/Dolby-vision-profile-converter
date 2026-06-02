# DV7 to DV8 Converter

A Python script that automatically converts **Dolby Vision Profile 7** MKV files to **Profile 8.1** by leveraging MKVToolNix, dovi_tool and MediaInfo.

## What it does

1. Scans the current folder for `.mkv` files.
2. Uses **MediaInfo** to detect Dolby Vision **Profile 7.x** (HDR format `dvhe.07`).
3. Extracts the video track with **mkvextract**.
4. Converts it to **Profile 8.1** using **dovi_tool** (`dovi_tool -m 2 convert --discard`).
5. Remuxes the new video stream with the original audio, subtitles, chapters etc. (everything except the original video) using **mkvmerge**.
6. Cleans up all temporary files and the original MKV after a successful remux.

## Requirements

- **Python 3.6+** (standard library only, no extra packages)
- **MKVToolNix** (provides `mkvmerge` and `mkvextract`)
- **dovi_tool** (the Rust-based Dolby Vision tool)
- **MediaInfo CLI** (specifically the CLI version)

All three external tools must be accessible via your system’s `PATH`, or you can set the full paths directly in the script’s configuration section.

### Recommended setup

1. Download MKVToolNix and add its folder to your `PATH`.
2. Download the MediaInfo CLI executable, rename it to `mediainfo_CLI` (or adjust the script), and place it in the same folder or somewhere on `PATH`.
3. Download `dovi_tool` from [GitHub](https://github.com/quietvoid/dovi_tool), extract it, and add its folder to your `PATH`.

## Usage

1. Place the `dv7_to_dv8.py` script in a folder containing your MKV files.
2. Ensure all required external tools are available.
3. Open a terminal in that folder and run:
   ```bash
   python dv7_to_dv8.py
   ```
4. The script will process every MKV file sequentially and skip any file that already has a `_p8.mkv` output.

> **Important:** This script **deletes the original MKV file** after a successful conversion. Make sure you have a backup if needed, or simply change the script not to delete the original.

## Configuration

If the tools are not in your `PATH`, edit the top of the script:

```python
MEDIAINFO  = "C:/tools/mediainfo_CLI.exe"  # full path
MKVEXTRACT = "C:/tools/mkvextract.exe"
MKVMERGE   = "C:/tools/mkvmerge.exe"
DOVI_TOOL  = "C:/tools/dovi_tool.exe"
```

## Process flow

For each MKV file `movie.mkv`:
- Checks for `movie_p8.mkv` → skip if exists.
- Checks for existing `movie.hevc` (extracted raw video) → if not present, extract video track.
- Checks for existing `movie_p8_temp.hevc` (converted video) → if not present, run `dovi_tool -m 2 convert --discard`.
- Deletes the extracted P7 raw video after successful conversion.
- Muxes: `mkvmerge -o movie_p8.mkv --no-video movie.mkv movie_p8_temp.hevc`
- Deletes the original `movie.mkv` and the temporary P8 stream.


## Notes

- The script assumes the video track ID is correctly detected by parsing `mkvmerge -i` output. If that fails, it defaults to track `0`, which may not work. You can manually set the track ID if needed.
- Only **Profile 7.x** files are processed. Already Profile 8 or other HDR formats are skipped.
- The conversion command discards the EL (enhancement layer) which is appropriate for Profile 8.1 playback compatibility.
- Tested on Windows; should work on Linux/macOS if the tools are available and the paths are adjusted.
