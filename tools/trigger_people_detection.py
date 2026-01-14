#!/usr/bin/env python3
"""
Trigger People Detection Processing
Processes photos to detect faces and create person profiles
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_services.people_intelligence import people_service

async def main():
    """Trigger face detection on all available photos"""
    print("🔍 Starting People Detection Processing...")
    
    # Get all photos from the photos directory
    photos_dir = Path("./MyData/photos")
    if not photos_dir.exists():
        print("❌ Photos directory not found")
        return
    
    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    photo_paths = []
    
    for file_path in photos_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            photo_paths.append(str(file_path))
    
    print(f"📸 Found {len(photo_paths)} photos to process")
    
    if not photo_paths:
        print("❌ No photos found for processing")
        return
    
    print(f"🎯 Processing {len(photo_paths)} photo paths...")
    for path in photo_paths:
        print(f"   📷 {path}")
    
    # Trigger face detection
    try:
        face_detections = await people_service.detect_faces(photo_paths)
        print(f"✅ Face detection completed!")
        print(f"   🔍 Processed {len(face_detections)} photos")
        
        # Get updated people count
        people = await people_service.get_all_people()
        print(f"   👥 Detected {len(people)} unique people")
        
        # Show people details
        for person in people:
            print(f"      Person {person.id}: {person.photo_count} photos, strength {person.relationship_strength:.2f}")
        
        # Get service status
        status = people_service.get_service_status()
        print(f"\n📊 Service Status:")
        print(f"   People: {status['statistics']['total_people']}")
        print(f"   Face Detections: {status['statistics']['total_face_detections']}")
        print(f"   Relationships: {status['statistics']['total_relationships']}")
        
    except Exception as e:
        print(f"❌ Face detection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())