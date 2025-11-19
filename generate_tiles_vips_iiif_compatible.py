#!/usr/bin/env python3
"""Generate IIIF static tiles using pyvips compatible with iiif_static.py output"""
import sys
import os
import json
import math
import pyvips

def generate_iiif_tiles(source_file, output_dir, identifier, tile_size=256):
    """Generate IIIF Image API 2.0 Level 0 tiles using vips, matching iiif_static.py pattern"""

    print(f"Loading image: {source_file}")
    image = pyvips.Image.new_from_file(source_file, access='random')

    width = image.width
    height = image.height

    print(f"Image size: {width} x {height}")
    print(f"Output directory: {output_dir}")
    print(f"Identifier: {identifier}")
    print(f"Tile size: {tile_size}")

    os.makedirs(output_dir, exist_ok=True)

    tile_count = 0

    # Calculate maximum tile size level (power of 2)
    max_tile_level = 0
    max_dim = max(width, height)
    while (tile_size * (2 ** max_tile_level)) < max_dim:
        max_tile_level += 1

    print(f"Max tile level: {max_tile_level}")

    # Generate tiles at multiple region sizes
    # Start from largest regions and work down to smallest
    for level in range(max_tile_level, -1, -1):
        region_size = tile_size * (2 ** level)
        print(f"\nGenerating tiles for region size {region_size}x{region_size}...")

        # For regions larger than image height, generate full-height tiles
        if region_size > height:
            # Generate full-height tiles at region_size width intervals
            x = 0
            while x < width:
                w = min(region_size, width - x)
                h = height

                # Extract and resize tile
                tile = image.crop(x, 0, w, h)
                scale_factor = tile_size / max(w, h)
                if scale_factor < 1.0:
                    tile = tile.resize(scale_factor)

                # Create IIIF path
                region_dir = f"{x},0,{w},{h}"
                tile_dir = os.path.join(output_dir, region_dir, f"{tile_size},", "0")
                os.makedirs(tile_dir, exist_ok=True)

                tile_path = os.path.join(tile_dir, "default.jpg")
                tile.write_to_file(tile_path, Q=90)

                tile_count += 1
                if tile_count % 100 == 0:
                    print(f"  Generated {tile_count} tiles...")

                x += region_size
        else:
            # Generate square or rectangular regions at this size
            y = 0
            while y < height:
                x = 0
                while x < width:
                    w = min(region_size, width - x)
                    h = min(region_size, height - y)

                    # Extract and resize tile
                    tile = image.crop(x, y, w, h)
                    scale_factor = tile_size / max(w, h)
                    if scale_factor < 1.0:
                        tile = tile.resize(scale_factor)

                    # Create IIIF path
                    region_dir = f"{x},{y},{w},{h}"
                    tile_dir = os.path.join(output_dir, region_dir, f"{tile_size},", "0")
                    os.makedirs(tile_dir, exist_ok=True)

                    tile_path = os.path.join(tile_dir, "default.jpg")
                    tile.write_to_file(tile_path, Q=90)

                    tile_count += 1
                    if tile_count % 100 == 0:
                        print(f"  Generated {tile_count} tiles...")

                    x += region_size
                y += region_size

    print(f"\nTotal tiles generated: {tile_count}")

    # Calculate scale factors for info.json
    max_scale = 1
    max_dimension = max(width, height)
    while max_dimension / (2 ** max_scale) > tile_size:
        max_scale += 1
    scale_factors = [2 ** i for i in range(max_scale + 1)]

    # Calculate sizes array
    sizes = []
    for scale in scale_factors:
        sizes.append({
            "width": width // scale,
            "height": height // scale
        })

    # Generate info.json
    info = {
        "@context": "http://iiif.io/api/image/2/context.json",
        "@id": f"https://iiif.lab.hi.u-tokyo.ac.jp/{identifier}",
        "protocol": "http://iiif.io/api/image",
        "width": width,
        "height": height,
        "sizes": sizes,
        "profile": [
            "http://iiif.io/api/image/2/level0.json",
            {
                "formats": ["jpg"],
                "qualities": ["default"]
            }
        ],
        "tiles": [
            {
                "width": tile_size,
                "height": tile_size,
                "scaleFactors": scale_factors
            }
        ]
    }

    info_path = os.path.join(output_dir, "info.json")
    with open(info_path, 'w') as f:
        json.dump(info, f, indent=2)

    print(f"Created info.json: {info_path}")

    # Create full/max/0/default.jpg
    full_dir = os.path.join(output_dir, "full", "max", "0")
    os.makedirs(full_dir, exist_ok=True)

    max_scale_factor = scale_factors[-1]
    full_image = image.resize(1.0 / max_scale_factor)
    full_path = os.path.join(full_dir, "default.jpg")
    full_image.write_to_file(full_path, Q=90)

    print(f"Created full image: {full_path}")

    # Create full/{width},/0/default.jpg for each size in sizes array
    print("\nGenerating full-image tiles at each size...")
    for size_info in sizes:
        size_width = size_info["width"]
        size_height = size_info["height"]

        # Create full/{width},/0/default.jpg
        full_size_dir = os.path.join(output_dir, "full", f"{size_width},", "0")
        os.makedirs(full_size_dir, exist_ok=True)

        # Calculate scale factor to reach this size
        scale_factor = size_width / width
        scaled_image = image.resize(scale_factor)

        full_size_path = os.path.join(full_size_dir, "default.jpg")
        scaled_image.write_to_file(full_size_path, Q=90)

        # Also create full/{width},{height}/0/default.jpg for completeness
        full_size_wh_dir = os.path.join(output_dir, "full", f"{size_width},{size_height}", "0")
        os.makedirs(full_size_wh_dir, exist_ok=True)

        full_size_wh_path = os.path.join(full_size_wh_dir, "default.jpg")
        scaled_image.write_to_file(full_size_wh_path, Q=90)

        print(f"  Created full/{size_width},/0/default.jpg and full/{size_width},{size_height}/0/default.jpg")

    print("\nTile generation completed successfully!")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: generate_tiles_vips_iiif_compatible.py <source_file> <output_dir> <identifier>")
        sys.exit(1)

    source_file = sys.argv[1]
    output_dir = sys.argv[2]
    identifier = sys.argv[3]

    generate_iiif_tiles(source_file, output_dir, identifier)
