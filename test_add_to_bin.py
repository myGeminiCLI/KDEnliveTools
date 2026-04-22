import pytest
import os
import mlt7
from add_to_bin import add_file_to_kdenlive_bin
import subprocess

@pytest.fixture
def dummy_media(tmp_path):
    """Creates a dummy media file for testing."""
    media_file = tmp_path / "test_media.wav"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
        "-t", "1", str(media_file)
    ], check=True, capture_output=True)
    return str(media_file)

@pytest.fixture
def project_file(tmp_path):
    """Creates a path for a dummy project file."""
    return str(tmp_path / "test_project.kdenlive")

def test_add_file_to_bin_success(project_file, dummy_media):
    """Test successful addition of a file to a new project."""
    assert add_file_to_kdenlive_bin(project_file, dummy_media) is True
    assert os.path.exists(project_file)
    
    with open(project_file, 'r') as f:
        content = f.read()
        # MLT XML stores the resource path in the producer's property
        assert os.path.basename(dummy_media) in content

def test_add_file_to_existing_project(project_file, dummy_media, tmp_path):
    """Test adding a file to an existing project."""
    media2 = tmp_path / "media2.wav"
    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", 
        "-t", "1", str(media2)
    ], check=True, capture_output=True)
    
    add_file_to_kdenlive_bin(project_file, dummy_media)
    add_file_to_kdenlive_bin(project_file, str(media2))
    
    with open(project_file, 'r') as f:
        content = f.read()
        assert os.path.basename(dummy_media) in content
        assert os.path.basename(str(media2)) in content

def test_file_not_found():
    """Test that it raises FileNotFoundError for missing media."""
    with pytest.raises(FileNotFoundError):
        add_file_to_kdenlive_bin("proj.kdenlive", "non_existent.mp4")

def test_mlt_producer_invalid(tmp_path, project_file):
    """Test handling of invalid media files."""
    invalid_media = tmp_path / "invalid.txt"
    invalid_media.write_text("not a video")
    
    # We expect a ValueError because the file is not a valid media file
    with pytest.raises(ValueError):
        add_file_to_kdenlive_bin(project_file, str(invalid_media))
