"""
hndl-it Storage Protocol Setup
Implements the redirection of C: folders to D: workshop via Directory Junctions.
"""
import os
import subprocess
import shutil
from pathlib import Path

def create_junction(source: str, target: str):
    """
    Create a Directory Junction (mklink /J).
    source: The link path (on C:)
    target: The actual folder (on D:)
    """
    print(f"🔗 Linking {source} -> {target}")
    
    # Ensure target exists
    os.makedirs(target, exist_ok=True)
    
    # If source exists and is not a link, move contents to target
    if os.path.exists(source):
        if os.path.islink(source) or (os.path.isdir(source) and hasattr(os, 'readlink') and os.path.islink(source)):
            print(f"  Skipping: {source} is already a link.")
            return
        
        print(f"  Moving existing files from {source} to {target}...")
        try:
            # Move all items in source to target
            for item in Path(source).iterdir():
                dest = Path(target) / item.name
                if not dest.exists():
                    shutil.move(str(item), str(dest))
            
            # Remove empty source directory
            os.rmdir(source)
        except Exception as e:
            print(f"  ❌ Error moving files: {e}")
            return

    # Create the junction using shell command (since mklink is a cmd internal)
    try:
        subprocess.run(f'cmd /c mklink /J "{source}" "{target}"', shell=True, check=True)
        print(f"  ✅ Junction created successfully.")
    except Exception as e:
        print(f"  ❌ Failed to create junction: {e}")

def setup_storage():
    """Execute the storage redirection protocol."""
    user_profile = os.environ.get("USERPROFILE")
    
    # 1. Redirect Downloads
    create_junction(
        os.path.join(user_profile, "Downloads"),
        r"D:\Downloads"
    )
    
    # 2. Redirect Documents
    create_junction(
        os.path.join(user_profile, "Documents"),
        r"D:\Documents"
    )
    
    # 3. Redirect Desktop (optional but keeps C: clean)
    # create_junction(os.path.join(user_profile, "Desktop"), r"D:\Desktop")
    
    # 4. Create standard folders on D:
    folders = [
        r"D:\Projects",
        r"D:\Ollama\models",
        r"D:\Docker",
        r"D:\Archives",
        r"D:\hndl-it\logs\evals"
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"📁 Created/Verified: {folder}")

if __name__ == "__main__":
    setup_storage()
