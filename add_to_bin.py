import mlt7
import os
import sys
import xml.etree.ElementTree as ET

def add_file_to_kdenlive_bin(project_path, media_file):
    """
    Adds a media file to the Kdenlive project bin.
    Uses MLT for validation and XML manipulation for project structure.
    """
    if not os.path.exists(media_file):
        raise FileNotFoundError(f"Media file not found: {media_file}")

    # Use MLT to validate the media file
    mlt7.Factory.init()
    profile = mlt7.Profile()
    test_producer = mlt7.Producer(profile, media_file)
    
    # Stricter validation
    is_valid_media = True
    service = test_producer.get("mlt_service")
    
    if not test_producer.is_valid():
        is_valid_media = False
    elif test_producer.get_length() <= 0:
        is_valid_media = False
    elif service in ["loader", "qtext", "color"]:
        # Exclude generic or placeholder services that might accidentally 
        # match non-media files or are not intended for simple bin addition
        is_valid_media = False

    if not is_valid_media:
        raise ValueError(f"Invalid media file: {media_file}")

    # Initialize or load the XML project
    if os.path.exists(project_path) and os.path.getsize(project_path) > 0:
        tree = ET.parse(project_path)
        root = tree.getroot()
    else:
        root = ET.Element("mlt", version="7.32.0")
        tree = ET.ElementTree(root)

    # In Kdenlive, bin items are 'producer' elements
    existing_ids = [p.get("id") for p in root.findall("producer")]
    new_id = f"producer{len(existing_ids)}"
    while new_id in existing_ids:
        new_id = f"producer{len(existing_ids) + 1}"

    new_p = ET.SubElement(root, "producer", id=new_id)
    ET.SubElement(new_p, "property", name="resource").text = os.path.abspath(media_file)
    ET.SubElement(new_p, "property", name="kdenlive:folderid").text = "-1"
    
    playlist = root.find("playlist[@id='main_bin']")
    if playlist is None:
        playlist = ET.SubElement(root, "playlist", id="main_bin")
    
    ET.SubElement(playlist, "entry", producer=new_id)

    tree.write(project_path, encoding="utf-8", xml_declaration=True)
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 add_to_bin.py <project.kdenlive> <media_file>")
        sys.exit(1)
    
    proj = sys.argv[1]
    media = sys.argv[2]
    try:
        add_file_to_kdenlive_bin(proj, media)
        print(f"Successfully added {media} to {proj}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
