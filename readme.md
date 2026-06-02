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
- **MediaInfo CLI** (specifically the CLI version, e.g., `mediainfo_CLI` or `mediainfo`)

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