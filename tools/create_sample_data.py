#!/usr/bin/env python3
"""
Create sample data for testing functionality
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from PIL import Image, ExifTags
import piexif

def create_sample_data():
    """Create sample data for testing all functionality"""
    print("📊 Creating sample data for testing...")
    
    # Create MyData directory structure
    data_dir = Path("MyData")
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (data_dir / "photos").mkdir(exist_ok=True)
    (data_dir / "facebook").mkdir(exist_ok=True)
    (data_dir / "locations").mkdir(exist_ok=True)
    (data_dir / "app_data").mkdir(exist_ok=True)
    
    # Create sample photos with GPS data
    create_sample_photos(data_dir / "photos")
    
    # Create sample Facebook data
    create_sample_facebook_data(data_dir / "facebook")
    
    # Create sample location data
    create_sample_location_data(data_dir / "locations")
    
    print("✅ Sample data created successfully!")

def create_sample_photos(photos_dir):
    """Create sample photos with GPS metadata"""
    print("📷 Creating sample photos with GPS data...")
    
    # Sample GPS coordinates (New York, Paris, Tokyo)
    locations = [
        {"name": "new_york", "lat": 40.7128, "lon": -74.0060},
        {"name": "paris", "lat": 48.8566, "lon": 2.3522},
        {"name": "tokyo", "lat": 35.6762, "lon": 139.6503},
        {"name": "beach", "lat": 25.7617, "lon": -80.1918},
        {"name": "mountains", "lat": 39.7392, "lon": -104.9903}
    ]
    
    for i, location in enumerate(locations):
        # Create a simple colored image
        img = Image.new('RGB', (800, 600), color=(100 + i*30, 150 + i*20, 200 + i*10))
        
        # Add GPS EXIF data
        exif_dict = {"GPS": {}}
        
        # Convert decimal degrees to GPS format
        lat_deg = int(abs(location["lat"]))
        lat_min = int((abs(location["lat"]) - lat_deg) * 60)
        lat_sec = int(((abs(location["lat"]) - lat_deg) * 60 - lat_min) * 60)
        
        lon_deg = int(abs(location["lon"]))
        lon_min = int((abs(location["lon"]) - lon_deg) * 60)
        lon_sec = int(((abs(location["lon"]) - lon_deg) * 60 - lon_min) * 60)
        
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = [(lat_deg, 1), (lat_min, 1), (lat_sec, 1)]
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = 'N' if location["lat"] >= 0 else 'S'
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = [(lon_deg, 1), (lon_min, 1), (lon_sec, 1)]
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = 'E' if location["lon"] >= 0 else 'W'
        
        # Add timestamp
        exif_dict["0th"] = {}
        exif_dict["Exif"] = {}
        timestamp = (datetime.now() - timedelta(days=i*30)).strftime("%Y:%m:%d %H:%M:%S")
        exif_dict["0th"][piexif.ImageIFD.DateTime] = timestamp
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = timestamp
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save image with EXIF data
        photo_path = photos_dir / f"photo_{location['name']}_{i+1}.jpg"
        img.save(photo_path, "JPEG", exif=exif_bytes)
        
        print(f"   📸 Created {photo_path.name} with GPS: {location['lat']}, {location['lon']}")

def create_sample_facebook_data(facebook_dir):
    """Create sample Facebook export data"""
    print("📘 Creating sample Facebook data...")
    
    # Sample posts data
    posts_data = {
        "posts_v2": [
            {
                "timestamp": int((datetime.now() - timedelta(days=30)).timestamp()),
                "data": [{"post": "Had an amazing day at the beach with friends! 🏖️"}],
                "attachments": [{"data": [{"media": {"uri": "photos/photo_beach_4.jpg"}}]}]
            },
            {
                "timestamp": int((datetime.now() - timedelta(days=60)).timestamp()),
                "data": [{"post": "Exploring the mountains this weekend. Nature is incredible! 🏔️"}],
                "attachments": [{"data": [{"media": {"uri": "photos/photo_mountains_5.jpg"}}]}]
            },
            {
                "timestamp": int((datetime.now() - timedelta(days=90)).timestamp()),
                "data": [{"post": "Coffee in Paris never gets old ☕"}],
                "attachments": [{"data": [{"media": {"uri": "photos/photo_paris_2.jpg"}}]}]
            }
        ]
    }
    
    with open(facebook_dir / "posts.json", "w") as f:
        json.dump(posts_data, f, indent=2)
    
    # Sample photos metadata
    photos_data = {
        "photos": [
            {
                "uri": "photos/photo_beach_4.jpg",
                "creation_timestamp": int((datetime.now() - timedelta(days=30)).timestamp()),
                "media_metadata": {
                    "photo_metadata": {
                        "exif_data": [{"latitude": 25.7617, "longitude": -80.1918}]
                    }
                }
            },
            {
                "uri": "photos/photo_paris_2.jpg", 
                "creation_timestamp": int((datetime.now() - timedelta(days=90)).timestamp()),
                "media_metadata": {
                    "photo_metadata": {
                        "exif_data": [{"latitude": 48.8566, "longitude": 2.3522}]
                    }
                }
            }
        ]
    }
    
    with open(facebook_dir / "photos.json", "w") as f:
        json.dump(photos_data, f, indent=2)
    
    # Sample messages
    messages_data = {
        "messages": [
            {
                "participants": [{"name": "John Doe"}, {"name": "Me"}],
                "messages": [
                    {
                        "sender_name": "John Doe",
                        "timestamp_ms": int((datetime.now() - timedelta(days=5)).timestamp() * 1000),
                        "content": "Hey, want to grab coffee tomorrow?"
                    },
                    {
                        "sender_name": "Me", 
                        "timestamp_ms": int((datetime.now() - timedelta(days=5, hours=1)).timestamp() * 1000),
                        "content": "Sure! How about 3pm at the usual place?"
                    }
                ]
            }
        ]
    }
    
    with open(facebook_dir / "messages.json", "w") as f:
        json.dump(messages_data, f, indent=2)
    
    print("   📘 Created Facebook posts, photos, and messages data")

def create_sample_location_data(locations_dir):
    """Create sample location/GPS data"""
    print("🗺️ Creating sample location data...")
    
    # Sample location history
    location_history = {
        "locations": [
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "latitude": 40.7128,
                "longitude": -74.0060,
                "accuracy": 10,
                "activity": {"type": "STILL", "confidence": 100}
            },
            {
                "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
                "latitude": 25.7617,
                "longitude": -80.1918,
                "accuracy": 15,
                "activity": {"type": "ON_FOOT", "confidence": 85}
            },
            {
                "timestamp": (datetime.now() - timedelta(days=90)).isoformat(),
                "latitude": 48.8566,
                "longitude": 2.3522,
                "accuracy": 8,
                "activity": {"type": "IN_VEHICLE", "confidence": 95}
            }
        ]
    }
    
    with open(locations_dir / "location_history.json", "w") as f:
        json.dump(location_history, f, indent=2)
    
    # Sample places
    places_data = {
        "places": [
            {
                "name": "Favorite Coffee Shop",
                "address": "123 Main St, New York, NY",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "visit_count": 25,
                "last_visit": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "name": "Miami Beach",
                "address": "Miami Beach, FL",
                "latitude": 25.7617,
                "longitude": -80.1918,
                "visit_count": 3,
                "last_visit": (datetime.now() - timedelta(days=30)).isoformat()
            }
        ]
    }
    
    with open(locations_dir / "places.json", "w") as f:
        json.dump(places_data, f, indent=2)
    
    print("   🗺️ Created location history and places data")

if __name__ == "__main__":
    create_sample_data()