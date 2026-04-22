import pytest
import xml.etree.ElementTree as ET
import os
from split_clips import split_at_timecodes

@pytest.fixture
def complex_project(tmp_path):
    """Creates a dummy Kdenlive project with multiple tracks."""
    project_path = tmp_path / "complex_project.kdenlive"
    root = ET.Element("mlt", version="7.32.0")
    ET.SubElement(root, "profile", frame_rate_num="25", frame_rate_den="1")
    ET.SubElement(root, "producer", id="p1", resource="video.mp4")
    
    # Track 1: 10 second clip (250 frames)
    pl1 = ET.SubElement(root, "playlist", id="pl1")
    # 'in' is a reserved keyword, use dictionary for attributes
    ET.SubElement(pl1, "entry", {"producer": "p1", "in": "0", "out": "249"})
    
    # Track 2: Same 10 second clip (grouped/linked)
    pl2 = ET.SubElement(root, "playlist", id="pl2")
    ET.SubElement(pl2, "entry", {"producer": "p1", "in": "0", "out": "249"})
    
    tree = ET.ElementTree(root)
    tree.write(project_path)
    return str(project_path)

def test_split_at_4_seconds(complex_project):
    """Test splitting at 4000ms (100 frames)."""
    # 4000ms at 25fps = 100 frames
    # Split should happen after 100 frames. 
    # Original (0-249) becomes (0-99) and (100-249)
    split_at_timecodes(complex_project, [4000])
    
    tree = ET.parse(complex_project)
    root = tree.getroot()
    
    for pl_id in ["pl1", "pl2"]:
        pl = root.find(f"playlist[@id='{pl_id}']")
        entries = pl.findall("entry")
        assert len(entries) == 2
        
        # First half
        assert entries[0].get("in") == "0"
        assert entries[0].get("out") == "99"
        
        # Second half
        assert entries[1].get("in") == "100"
        assert entries[1].get("out") == "249"

def test_multiple_splits(complex_project):
    """Test multiple split points."""
    # Split at 2s (50f) and 6s (150f)
    split_at_timecodes(complex_project, [2000, 6000])
    
    tree = ET.parse(complex_project)
    root = tree.getroot()
    pl = root.find("playlist[@id='pl1']")
    entries = pl.findall("entry")
    
    assert len(entries) == 3
    # 0-49, 50-149, 150-249
    assert entries[0].get("out") == "49"
    assert entries[1].get("in") == "50"
    assert entries[1].get("out") == "149"
    assert entries[2].get("in") == "150"

def test_split_outside_range(complex_project):
    """Test split timecode outside of any clip."""
    # Split at 20s (project is only 10s)
    split_at_timecodes(complex_project, [20000])
    
    tree = ET.parse(complex_project)
    root = tree.getroot()
    pl = root.find("playlist[@id='pl1']")
    assert len(pl.findall("entry")) == 1
