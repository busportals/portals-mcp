#!/usr/bin/env python3
"""Re-pack GLB files to embed external texture references into the binary buffer.

Some GLB exporters (Unity via UnityGLTF, older Blender plugins, etc.) write external
"uri" texture references instead of embedding image data in the binary buffer. These
files load fine locally but fail on CDNs because the relative paths don't resolve.

This script reads each GLB, finds images with "uri" entries, reads the referenced files,
and embeds them directly into the GLB binary buffer.

Usage:
    python tools/repack_glb_textures.py <input_folder> <output_folder>

When to use:
    If GLB models appear white/grey/untextured after uploading to the Portals CDN,
    run this tool on the original files, then re-upload the repacked output.
"""

import struct
import json
import sys
import os
import math
from pathlib import Path


def repack_glb(input_path: Path, output_path: Path, texture_dir: Path):
    """Re-pack a single GLB to embed external textures."""
    with open(input_path, 'rb') as f:
        # GLB header: magic(4) + version(4) + length(4)
        magic, version, total_length = struct.unpack('<III', f.read(12))
        assert magic == 0x46546C67, f"Not a valid GLB: {input_path}"

        # JSON chunk: length(4) + type(4) + data
        json_chunk_len, json_chunk_type = struct.unpack('<II', f.read(8))
        assert json_chunk_type == 0x4E4F534A, "First chunk must be JSON"
        json_data = json.loads(f.read(json_chunk_len).decode('utf-8'))

        # Binary chunk: length(4) + type(4) + data
        remaining = total_length - 12 - 8 - json_chunk_len
        if remaining > 8:
            bin_chunk_len, bin_chunk_type = struct.unpack('<II', f.read(8))
            assert bin_chunk_type == 0x004E4942, "Second chunk must be BIN"
            bin_data = bytearray(f.read(bin_chunk_len))
        else:
            bin_data = bytearray()

    if 'images' not in json_data:
        # No images — just copy as-is
        import shutil
        shutil.copy2(input_path, output_path)
        return False

    modified = False
    for img in json_data['images']:
        if 'uri' not in img:
            continue

        uri = img['uri']
        # Resolve relative to the GLB's directory first, then try texture_dir
        tex_path = input_path.parent / uri
        if not tex_path.exists():
            tex_path = texture_dir / Path(uri).name
        if not tex_path.exists():
            print(f"  WARNING: Cannot find texture {uri} for {input_path.name}")
            continue

        # Read the texture file
        tex_bytes = tex_path.read_bytes()

        # Determine MIME type
        suffix = tex_path.suffix.lower()
        mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
        mime_type = mime_map.get(suffix, 'image/png')

        # Pad binary buffer to 4-byte alignment
        while len(bin_data) % 4 != 0:
            bin_data.append(0)

        byte_offset = len(bin_data)
        byte_length = len(tex_bytes)

        # Append texture bytes to binary buffer
        bin_data.extend(tex_bytes)

        # Pad again for alignment
        while len(bin_data) % 4 != 0:
            bin_data.append(0)

        # Add a new bufferView
        if 'bufferViews' not in json_data:
            json_data['bufferViews'] = []
        new_view_index = len(json_data['bufferViews'])
        json_data['bufferViews'].append({
            'buffer': 0,
            'byteOffset': byte_offset,
            'byteLength': byte_length
        })

        # Replace uri with bufferView + mimeType
        del img['uri']
        img['bufferView'] = new_view_index
        img['mimeType'] = mime_type

        modified = True
        print(f"  Embedded {uri} ({byte_length} bytes) into {input_path.name}")

    if not modified:
        import shutil
        shutil.copy2(input_path, output_path)
        return False

    # Update buffer size
    if 'buffers' in json_data and len(json_data['buffers']) > 0:
        json_data['buffers'][0]['byteLength'] = len(bin_data)

    # Write the new GLB
    json_bytes = json.dumps(json_data, separators=(',', ':')).encode('utf-8')
    # Pad JSON to 4-byte alignment with spaces
    while len(json_bytes) % 4 != 0:
        json_bytes += b' '

    # Calculate total size
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_data)

    with open(output_path, 'wb') as f:
        # GLB header
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        # JSON chunk
        f.write(struct.pack('<II', len(json_bytes), 0x4E4F534A))
        f.write(json_bytes)
        # BIN chunk
        f.write(struct.pack('<II', len(bin_data), 0x004E4942))
        f.write(bin_data)

    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/repack_glb_textures.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = Path(sys.argv[1])
    output_folder = Path(sys.argv[2])
    output_folder.mkdir(parents=True, exist_ok=True)

    # Look for a Textures subfolder
    texture_dir = input_folder / 'Textures'
    if not texture_dir.exists():
        texture_dir = input_folder

    glb_files = sorted(input_folder.glob('*.glb'))
    print(f"Found {len(glb_files)} GLB files in {input_folder}")

    repacked = 0
    for glb_path in glb_files:
        out_path = output_folder / glb_path.name
        if repack_glb(glb_path, out_path, texture_dir):
            repacked += 1
        else:
            print(f"  {glb_path.name}: no external textures (copied as-is)")

    print(f"\nDone. {repacked}/{len(glb_files)} files re-packed with embedded textures.")
    print(f"Output: {output_folder}")


if __name__ == '__main__':
    main()
