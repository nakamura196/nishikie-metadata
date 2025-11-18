#!/usr/bin/env python3
"""Generate IIIF static tiles using pyvips (much faster than PIL)"""
import sys
import os
import json
import math
import pyvips

def generate_iiif_tiles(source_file, output_dir, identifier, tile_size=256):
    """Generate IIIF Image API 2.0 Level 0 tiles using vips"""

    print(f"Loading image: {source_file}")
    image = pyvips.Image.new_from_file(source_file, access='sequential')

    width = image.width
    height = image.height

    print(f"Image size: {width} x {height}")
    print(f"Output directory: {output_dir}")
    print(f"Identifier: {identifier}")
    print(f"Tile size: {tile_size}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Calculate scale factors
    max_dimension = max(width, height)
    max_scale = 1
    while max_dimension / (2 ** max_scale) > tile_size:
        max_scale += 1

    scale_factors = [2 ** i for i in range(max_scale + 1)]
    print(f"Scale factors: {scale_factors}")

    tile_count = 0

    # Generate tiles for each scale factor
    for scale in scale_factors:
        scale_width = width // scale
        scale_height = height // scale

        if scale_width == 0 or scale_height == 0:
            continue

        print(f"\nGenerating tiles for scale {scale} ({scale_width}x{scale_height})...")

        # Resize image for this scale
        scaled_image = image.resize(1.0 / scale)

        # Calculate number of tiles
        cols = math.ceil(scale_width / tile_size)
        rows = math.ceil(scale_height / tile_size)

        # Generate tiles
        for row in range(rows):
            for col in range(cols):
                # Coordinates in scaled image
                x_scaled = col * tile_size
                y_scaled = row * tile_size
                w_scaled = min(tile_size, scale_width - x_scaled)
                h_scaled = min(tile_size, scale_height - y_scaled)

                # Extract tile
                tile = scaled_image.crop(x_scaled, y_scaled, w_scaled, h_scaled)

                # Calculate coordinates in original full-size image
                x_full = x_scaled * scale
                y_full = y_scaled * scale
                w_full = w_scaled * scale
                h_full = h_scaled * scale

                # Create IIIF-compliant directory structure: {x},{y},{w},{h}/{size},/0/default.jpg
                region_dir = f"{x_full},{y_full},{w_full},{h_full}"
                tile_dir = os.path.join(output_dir, region_dir, f"{tile_size},", "0")
                os.makedirs(tile_dir, exist_ok=True)

                # Save tile
                tile_path = os.path.join(tile_dir, "default.jpg")
                tile.write_to_file(tile_path, Q=90)

                tile_count += 1

                if tile_count % 100 == 0:
                    print(f"  Generated {tile_count} tiles...")

    print(f"\nTotal tiles generated: {tile_count}")

    # Generate info.json
    info = {
        "@context": "http://iiif.io/api/image/2/context.json",
        "@id": f"https://iiif.lab.hi.u-tokyo.ac.jp/{identifier}",
        "protocol": "http://iiif.io/api/image",
        "width": width,
        "height": height,
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

    # Use the lowest resolution for the full image
    max_scale_factor = scale_factors[-1]
    full_image = image.resize(1.0 / max_scale_factor)
    full_path = os.path.join(full_dir, "default.jpg")
    full_image.write_to_file(full_path, Q=90)

    print(f"Created full image: {full_path}")
    print("\nTile generation completed successfully!")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: generate_tiles_vips.py <source_file> <output_dir> <identifier>")
        sys.exit(1)

    source_file = sys.argv[1]
    output_dir = sys.argv[2]
    identifier = sys.argv[3]

    generate_iiif_tiles(source_file, output_dir, identifier)
