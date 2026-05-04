#!/usr/bin/env python3
"""
Download official PDF specs for survey equipment and convert to images.
"""

import os
import subprocess
import sys
from pathlib import Path

# Equipment specs to download
EQUIPMENT_PDFS = {
    # Kongsberg EM2040C
    "kongsberg-em2040c": {
        "url": "https://www.kongsberg.com/maritime/products/mapping-systems/em-2040c/",
        "fallback_urls": [
            "https://www.kongsberg.com/globalassets/maritime/km-products/product-documents/em-2040c-datasheet.pdf",
            "https://www.kongsberg.com/maritime/support/product-downloads/?pid=EM-2040C"
        ],
        "filename": "kongsberg-em2040c-specs.pdf"
    },
    # Exail Octans V
    "exail-octans-v": {
        "url": "https://www.exail.com/product/octans-motion-sensor/",
        "fallback_urls": [
            "https://www.exail.com/sites/default/files/2023-11/OCTANS.pdf",
            "https://www.exail.com/system/files/2024-01/octans-datasheet.pdf"
        ],
        "filename": "exail-octans-v-specs.pdf"
    },
    # MGB Ukko Gen2
    "mgb-ukko": {
        "url": "https://mgb-tech.com/product/ukko/",
        "fallback_urls": [
            "https://mgb-tech.com/download/ukko-datasheet.pdf"
        ],
        "filename": "mgb-ukko-specs.pdf"
    },
    # Valeport SWIFT
    "valeport-swift": {
        "url": "https://www.valeport.co.uk/product/swiift-svp/",
        "fallback_urls": [
            "https://www.valeport.co.uk/wp-content/uploads/2023/05/SWiFT-SVP-Datasheet.pdf",
            "https://www.valeport.co.uk/downloads/SWiFT-SVP.pdf"
        ],
        "filename": "valeport-swift-specs.pdf"
    },
    # Valeport Mini SVS
    "valeport-minisvs": {
        "url": "https://www.valeport.co.uk/product/mini-svs/",
        "fallback_urls": [
            "https://www.valeport.co.uk/wp-content/uploads/2023/05/Mini-SVS-Datasheet.pdf"
        ],
        "filename": "valeport-minisvs-specs.pdf"
    },
    # MGB Tari
    "mgb-tari": {
        "url": "https://mgb-tech.com/product/tari/",
        "fallback_urls": [
            "https://mgb-tech.com/download/tari-datasheet.pdf"
        ],
        "filename": "mgb-tari-specs.pdf"
    },
    # QINSy
    "qinsy": {
        "url": "https://qps.nl/products/qinsy/",
        "fallback_urls": [
            "https://qps.nl/wp-content/uploads/2023/01/Qinsy-Brochure.pdf"
        ],
        "filename": "qinsy-specs.pdf"
    },
    # BeamworX AutoClean
    "beamworx-autoclean": {
        "url": "https://beamworx.com/products/autoclean/",
        "fallback_urls": [
            "https://beamworx.com/wp-content/uploads/2023/01/AutoClean-Brochure.pdf"
        ],
        "filename": "beamworx-autoclean-specs.pdf"
    },
    # Starfish 990F
    "starfish-990f": {
        "url": "https://www.bathyswath.com/product/starfish-990f/",
        "fallback_urls": [
            "https://www.bathyswath.com/wp-content/uploads/2023/05/StarFish-990F-Datasheet.pdf"
        ],
        "filename": "starfish-990f-specs.pdf"
    },
    # Knudsen Pinger
    "knudsen-pinger": {
        "url": "https://www.knudsenengineering.com/products/sub-bottom-profilers/",
        "fallback_urls": [
            "https://www.knudsenengineering.com/wp-content/uploads/2023/01/Pinger-Datasheet.pdf"
        ],
        "filename": "knudsen-pinger-specs.pdf"
    },
    # Geometrics G-882X
    "geometrics-g882x": {
        "url": "https://www.geometrics.com/product/g-882-marine-magnetometer/",
        "fallback_urls": [
            "https://www.geometrics.com/wp-content/uploads/2023/01/G-882X-Datasheet.pdf"
        ],
        "filename": "geometrics-g882x-specs.pdf"
    }
}

OUTPUT_DIR = Path("/home/raspberry/.openclaw/workspace/missions/2026-05-LAGOS-HARBOR-GABON/reports/method-statements/images/equipment-specs")

def download_pdf(name, info):
    """Try to download PDF from multiple URLs."""
    output_file = OUTPUT_DIR / info["filename"]
    
    if output_file.exists():
        print(f"  ✅ Already exists: {info['filename']}")
        return True
    
    # Try fallback URLs first (direct PDF links)
    for url in info.get("fallback_urls", []):
        try:
            print(f"  🔄 Trying: {url}")
            result = subprocess.run(
                ["curl", "-L", "-o", str(output_file), "-s", "-w", "%{http_code}", url],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and os.path.exists(output_file):
                size = os.path.getsize(output_file)
                if size > 1000:  # At least 1KB
                    print(f"  ✅ Downloaded: {info['filename']} ({size:,} bytes)")
                    return True
                else:
                    os.remove(output_file)
        except Exception as e:
            print(f"  ❌ Failed: {e}")
    
    print(f"  ❌ Could not download: {info['filename']}")
    return False

def convert_pdf_to_images(pdf_file):
    """Convert PDF pages to PNG images."""
    if not pdf_file.exists():
        return []
    
    base_name = pdf_file.stem
    output_pattern = OUTPUT_DIR / f"{base_name}-page%d.png"
    
    try:
        # Use pdftoppm or ImageMagick
        result = subprocess.run(
            ["pdftoppm", "-png", "-r", "150", str(pdf_file), str(OUTPUT_DIR / base_name)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Find generated images
            images = sorted(OUTPUT_DIR.glob(f"{base_name}-*.png"))
            print(f"  ✅ Converted to {len(images)} images")
            return images
    except FileNotFoundError:
        # Try ImageMagick
        try:
            result = subprocess.run(
                ["convert", "-density", "150", str(pdf_file), str(output_pattern)],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                images = sorted(OUTPUT_DIR.glob(f"{base_name}-page*.png"))
                print(f"  ✅ Converted to {len(images)} images")
                return images
        except FileNotFoundError:
            print(f"  ❌ No PDF converter available (pdftoppm or ImageMagick)")
    
    return []

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("DOWNLOADING EQUIPMENT SPECIFICATIONS")
    print("=" * 70)
    
    downloaded = []
    failed = []
    
    for name, info in EQUIPMENT_PDFS.items():
        print(f"\n📄 {name}")
        if download_pdf(name, info):
            downloaded.append(name)
        else:
            failed.append(name)
    
    print("\n" + "=" * 70)
    print("CONVERTING PDFs TO IMAGES")
    print("=" * 70)
    
    converted = []
    for name in downloaded:
        pdf_file = OUTPUT_DIR / EQUIPMENT_PDFS[name]["filename"]
        print(f"\n🖼️  {name}")
        images = convert_pdf_to_images(pdf_file)
        if images:
            converted.append((name, images))
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Downloaded: {len(downloaded)}/{len(EQUIPMENT_PDFS)}")
    print(f"Converted: {len(converted)}/{len(downloaded)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print(f"  Failed items: {', '.join(failed)}")
    
    # List all generated images
    all_images = sorted(OUTPUT_DIR.glob("*.png"))
    print(f"\nTotal images: {len(all_images)}")
    for img in all_images:
        size = os.path.getsize(img)
        print(f"  {img.name} ({size:,} bytes)")

if __name__ == "__main__":
    main()
