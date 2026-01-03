import os
import shutil
import fnmatch

SOURCE_DIR = "blender_python_reference_4_5"
TARGET_DIR = "selected_blender_docs"

# Define patterns to include
INCLUDE_PATTERNS = [
    "bpy.types.*",
    "bpy.ops.*",
    "bpy.data*",
    "bpy.context*",
    "bpy.props*",
    "bpy.utils*",
    "bpy.app*",
    "bpy.path*",
    "mathutils*",
    "bmesh*"
]

# Define patterns to strictly exclude (even if they match include patterns, though unlikely with the above)
EXCLUDE_PATTERNS = [
    "aud.*",
    "bgl.*",
    "blf.*",
    "gpu.*",
    "freestyle.*",
    "genindex*",
    "search*",
    "index*",
    "_*", # Exclude internal/private modules or static files often starting with _
]

def is_relevant(filename):
    # First check exclusions
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return False
            
    # Then check inclusions
    for pattern in INCLUDE_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True
            
    return False

def main():
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory '{SOURCE_DIR}' not found.")
        return

    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    os.makedirs(TARGET_DIR)

    count = 0
    files = os.listdir(SOURCE_DIR)
    
    print(f"Scanning {len(files)} files in {SOURCE_DIR}...")
    
    for filename in files:
        if is_relevant(filename):
            src_path = os.path.join(SOURCE_DIR, filename)
            dst_path = os.path.join(TARGET_DIR, filename)
            
            # process only files, skip directories mostly unless we want to recurse (which we might not need for this flat list)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
                count += 1
                
    print(f"Successfully copied {count} relevant documentation files to '{TARGET_DIR}'.")

if __name__ == "__main__":
    main()
