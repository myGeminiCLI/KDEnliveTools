import xml.etree.ElementTree as ET
import os
import sys

def split_at_timecodes(project_path, timecodes_ms):
    """
    Splits clips on the Kdenlive project timeline at given timecodes (ms).
    """
    if not os.path.exists(project_path):
        raise FileNotFoundError(f"Project not found: {project_path}")

    tree = ET.parse(project_path)
    root = tree.getroot()

    # Get FPS for ms to frames conversion
    profile = root.find("profile")
    if profile is not None:
        fps_num = float(profile.get("frame_rate_num", 25))
        fps_den = float(profile.get("frame_rate_den", 1))
        fps = fps_num / fps_den
    else:
        fps = 25.0

    def ms_to_frames(ms):
        return int((ms / 1000.0) * fps)

    # Sort timecodes descending to avoid split offset issues 
    # (though splitting in place usually doesn't shift frames, 
    # it's cleaner to process multiple splits if they were ripple-style)
    # For a simple cut, any order works if we don't change absolute positions.
    sorted_frames = sorted([ms_to_frames(t) for t in timecodes_ms], reverse=True)

    for split_frame in sorted_frames:
        # Find all playlists (tracks) in the tractor
        # Kdenlive usually puts tracks in playlists and then those in a tractor
        playlists = root.findall("playlist")
        
        for playlist in playlists:
            current_frame = 0
            entries = playlist.findall("entry")
            
            for i, entry in enumerate(entries):
                in_val = int(entry.get("in", 0))
                out_val = int(entry.get("out", 0))
                duration = out_val - in_val + 1
                
                # Check if the split point falls inside this entry
                if current_frame < split_frame < current_frame + duration:
                    # Calculate split point relative to entry's internal 'in' point
                    relative_split = split_frame - current_frame
                    
                    # Split the entry into two
                    original_out = entry.get("out")
                    
                    # New 'out' for first half
                    new_out_first = in_val + relative_split - 1
                    entry.set("out", str(new_out_first))
                    
                    # Create second half entry
                    new_in_second = in_val + relative_split
                    # Insert after the current entry
                    new_entry = ET.Element("entry", {
                        "producer": entry.get("producer"),
                        "in": str(new_in_second),
                        "out": original_out
                    })
                    # Copy properties if any
                    for prop in entry.findall("property"):
                        new_prop = ET.SubElement(new_entry, "property", name=prop.get("name"))
                        new_prop.text = prop.text
                    
                    playlist.insert(list(playlist).index(entry) + 1, new_entry)
                    
                    # Since we split one, we don't need to check other entries 
                    # in THIS playlist for the SAME split point (unless clips overlap, 
                    # which shouldn't happen in a standard Kdenlive track)
                    break
                
                current_frame += duration

    tree.write(project_path, encoding="utf-8", xml_declaration=True)
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 split_clips.py <project.kdenlive> <time_ms1> [time_ms2...]")
        sys.exit(1)
    
    proj = sys.argv[1]
    times = [int(t) for t in sys.argv[2:]]
    try:
        split_at_timecodes(proj, times)
        print(f"Successfully split clips at {times} ms")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
