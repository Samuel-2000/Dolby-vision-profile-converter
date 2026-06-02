import subprocess
import pathlib
import json

# =====================================================
# CONFIGURATION (need to have these .exe in the path configuration.) I recommend to put all of them into MKVToolNix folder, and just add MKVToolNix to path.
# =====================================================
MEDIAINFO  = "mediainfo_CLI"    # or full path to your MediaInfo executable (download mediainfo.exe as cli, and then rename it into mediainfo_CLI)
MKVEXTRACT = "mkvextract"       # or full path (in MKVToolNix folder)
MKVMERGE   = "mkvmerge"         # or full path (in MKVToolNix folder)
DOVI_TOOL  = "dovi_tool"        # or full path (download from github and add path to dovi_tool folder)
# =====================================================


def run(cmd):
    """Run a command verbosely and return exit code."""
    print("   CMD:", " ".join(cmd))
    result = subprocess.run(cmd, text=True, capture_output=True)

    if result.stdout.strip():
        print("   STDOUT:", result.stdout.strip())
    if result.stderr.strip():
        print("   STDERR:", result.stderr.strip())

    return result.returncode

def run_complex(cmd, timeout=None):
    """Run a command verbosely and return exit code and output."""
    print("   CMD:", " ".join(cmd))
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            check=False,
            timeout=timeout
        )
        
        if result.stdout:
            # Limit output to avoid flooding console
            output = result.stdout.decode('utf-8', errors='ignore')
            if len(output) > 500:
                print("   STDOUT:", output[:200] + "..." + output[-200:])
            else:
                print("   STDOUT:", output.strip())
        if result.stderr:
            error = result.stderr.decode('utf-8', errors='ignore')
            if len(error) > 500:
                print("   STDERR:", error[:200] + "..." + error[-200:])
            else:
                print("   STDERR:", error.strip())
        
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("   !! Command timed out")
        return -2, b"", b"Timeout expired"
    except Exception as e:
        print(f"   !! Command failed: {e}")
        return -1, b"", str(e).encode()


def get_hdr_format(mkv_file):
    """Return HDR info dict from MediaInfo JSON if Profile 7.x, else None."""
    cmd = [MEDIAINFO, "--Output=JSON", str(mkv_file)]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout)
        video_tracks = [t for t in data['media']['track'] if t['@type'] == 'Video']
        for track in video_tracks:
            hdr_profile = track.get("HDR_Format_Profile", "")
            if "dvhe.07" in hdr_profile.lower():
                hdr_info = {
                    "Format": track.get("HDR_Format", ""),
                    "Version": track.get("HDR_Format_Version", ""),
                    "Profile": hdr_profile,
                    "Level": track.get("HDR_Format_Level", ""),
                    "Settings": track.get("HDR_Format_Settings", "")
                }
                return hdr_info
    except Exception as e:
        print("   !! Failed to parse MediaInfo JSON:", e)
    return None

def get_video_track_id(mkv_file):
    """Extract video track ID from mkv file."""
    cmd = [MKVMERGE, "-i", str(mkv_file)]
    returncode, stdout, stderr = run_complex(cmd, timeout=30)
    
    if returncode != 0:
        return "0"  # Fallback to default
    
    output = stdout.decode('utf-8', errors='ignore')
    for line in output.split('\n'):
        if 'video' in line.lower() and 'track ID' in line:
            # Extract track ID (usually something like "1" or "2")
            parts = line.split(':')
            for part in parts:
                if 'track ID' in part:
                    track_id = part.split()[-1].strip()
                    return track_id
    return "0"

def main():
    mkv_files = sorted(pathlib.Path(".").glob("*.mkv"))

    if not mkv_files:
        print("No MKV files found.")
        return

    print("==============================================")
    print(" Dolby Vision Profile 7 → Profile 8.1 Converter")
    print("==============================================\n")

    for mkv in mkv_files:
        print("----------------------------------------------")
        print(f"Checking file: {mkv.name}")

        hdr_info = get_hdr_format(mkv)
        if not hdr_info:
            print("   -> Not Dolby Vision Profile 7.x, skipping.\n")
            continue

        video_track_id = get_video_track_id(mkv)
        print(f"   Video track ID: {video_track_id}")

        print(f"   HDR info: {hdr_info['Profile']}")
        print("   -> Dolby Vision Profile 7 detected")

        # Movie-specific filenames
        base_name = mkv.stem
        original_file = pathlib.Path(f"{base_name}.hevc")
        temp_file = pathlib.Path(f"{base_name}_p8_temp.hevc")
        final_file = pathlib.Path(f"{base_name}_p8.mkv")

        # Skip movie if final output already exists
        if final_file.exists():
            print(f"   -> Final file already exists: {final_file.name}, skipping movie.\n")
            continue

        # Extract video track if original doesn't exist
        if not temp_file.exists():
            if not original_file.exists():
                print(f"   -> Extracting video track to {original_file.name}...")
                if run([MKVEXTRACT, "tracks", str(mkv), f"{video_track_id}:{original_file}"]) != 0:
                    print("   !! Failed to extract video track, skipping\n")
                    continue
            else:
                print(f"   -> Original video already exists: {original_file.name}")

            # Convert to Profile 8.1 using temp file
            print(f"   -> Converting to Profile 8.1 (temp: {temp_file.name})...")
            cmd = [
                DOVI_TOOL,
                "-m", "2",            # profile 8.1
                "convert",
                "--discard",
                str(original_file),
                "-o", str(temp_file)
            ]
            
            print("   CMD:", " ".join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=False)
            
            if result.returncode != 0:
                print(f"   !! dovi_tool conversion failed. Return code: {result.returncode}")
                if result.stderr:
                    try:
                        print("   STDERR:", result.stderr.decode(errors='ignore').strip())
                    except:
                        print("   STDERR: (could not decode)")
                # Clean up empty temp file if any
                if temp_file.exists() and temp_file.stat().st_size == 0:
                    temp_file.unlink(missing_ok=True)
                continue
            
            # Check if file was created and has content
            if temp_file.exists() and temp_file.stat().st_size > 0:
                print(f"   -> Conversion completed: {temp_file.name} ({temp_file.stat().st_size} bytes)")
                # Delete the extracted P7 video track because it is no longer needed
                if original_file.exists():
                    original_file.unlink(missing_ok=True)
                    print(f"   -> Deleted extracted P7 track: {original_file.name}")
            else:
                print(f"   !! Conversion failed: temp file is empty or doesn't exist")
                continue
        else:
            print(f"   -> Reusing existing temp file: {temp_file.name}")

        # Remux temp file to final MKV
        print(f"   -> Remuxing to {final_file.name}")
        if run([
            MKVMERGE,
            "-o", str(final_file),
            "--no-video", str(mkv),
            str(temp_file)
        ]) != 0:
            print("   !! Remux failed")
        else:
            print(f"   -> DONE: {final_file.name}")
            # Delete original MKV after successful remux
            if mkv.exists():
                mkv.unlink(missing_ok=True)
                print(f"   -> Deleted original file: {mkv.name}")
            # Delete temporary P8 HEVC stream
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
                print(f"   -> Deleted temp file: {temp_file.name}")
        
        print()  # Add blank line for readability

    print("==============================================")
    print(" All files processed.")
    print("==============================================")


if __name__ == "__main__":
    main()