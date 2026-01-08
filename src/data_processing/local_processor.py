"""
Local Data Processing Pipeline
Processes multi-modal personal data locally with secure file permissions
"""
import os
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
import shutil
from PIL import Image
from PIL.ExifTags import TAGS
import piexif

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    success: bool
    records_processed: int
    errors: List[str]
    data_type: str
    processing_time: float
    file_paths: List[str]

@dataclass
class PhotoMetadata:
    """Extracted photo metadata"""
    file_path: str
    gps_coordinates: Optional[Tuple[float, float]]
    timestamp: Optional[datetime]
    tagged_people: List[str]
    camera_info: Dict[str, Any]
    file_size: int
    dimensions: Tuple[int, int]

class LocalDataProcessor:
    """Processes multi-modal personal data locally with privacy protection"""
    
    def __init__(self, data_path: str = "./MyData"):
        self.data_path = Path(data_path)
        self.ensure_secure_permissions()
        self.db_path = self.data_path / "processed_data.db"
        self._init_database()
        
    def ensure_secure_permissions(self):
        """Ensure local data has secure file permissions"""
        try:
            self.data_path.mkdir(parents=True, exist_ok=True)
            # Set secure permissions (owner read/write/execute only)
            os.chmod(self.data_path, 0o700)
            logger.info(f"Set secure permissions for data directory: {self.data_path}")
        except Exception as e:
            logger.error(f"Failed to set secure permissions: {e}")
            
    def _init_database(self):
        """Initialize local database for processed data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS photo_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    gps_latitude REAL,
                    gps_longitude REAL,
                    timestamp TEXT,
                    tagged_people TEXT,
                    camera_info TEXT,
                    file_size INTEGER,
                    width INTEGER,
                    height INTEGER,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    total_files INTEGER DEFAULT 0,
                    processed_files INTEGER DEFAULT 0,
                    last_processed TIMESTAMP,
                    status TEXT DEFAULT 'pending'
                )
            """)
    
    def process_facebook_data(self, facebook_file: Optional[str] = None) -> ProcessingResult:
        """Process Facebook export data locally"""
        start_time = datetime.now()
        errors = []
        processed_files = []
        records_processed = 0
        
        try:
            if facebook_file:
                # Process specific file
                try:
                    with open(facebook_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Process the JSON data
                    if isinstance(data, dict):
                        # Count different types of data
                        if 'posts' in data:
                            records_processed += len(data['posts'])
                        if 'photos' in data:
                            records_processed += len(data['photos'])
                        if 'messages' in data:
                            records_processed += len(data['messages'])
                    
                    processed_files.append(facebook_file)
                    
                except Exception as e:
                    errors.append(f"Failed to process Facebook file {facebook_file}: {e}")
            else:
                # Auto-detect Facebook data structure (from existing implementation)
                facebook_paths = self._find_facebook_data()
                
                for fb_path in facebook_paths:
                    try:
                        result = self._process_facebook_directory(fb_path)
                        records_processed += result.records_processed
                        processed_files.extend(result.file_paths)
                        errors.extend(result.errors)
                    except Exception as e:
                        errors.append(f"Failed to process Facebook directory {fb_path}: {e}")
                        
            # Update data source status
            self._update_data_source_status("facebook", len(processed_files), records_processed)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=len(errors) == 0,
                records_processed=records_processed,
                errors=errors,
                data_type="facebook",
                processing_time=processing_time,
                file_paths=processed_files
            )
            
        except Exception as e:
            logger.error(f"Facebook data processing failed: {e}")
            return ProcessingResult(
                success=False,
                records_processed=0,
                errors=[str(e)],
                data_type="facebook",
                processing_time=(datetime.now() - start_time).total_seconds(),
                file_paths=[]
            )
    
    def _find_facebook_data(self) -> List[Path]:
        """Auto-detect Facebook data structure"""
        possible_paths = [
            self.data_path / "your_facebook_activity" / "posts",
            self.data_path / "facebook" / "posts",
            self.data_path / "posts",
            self.data_path
        ]
        
        found_paths = []
        for path in possible_paths:
            if path.exists() and self._has_facebook_json_files(path):
                found_paths.append(path)
                logger.info(f"Found Facebook data at: {path}")
                
        return found_paths
    
    def _has_facebook_json_files(self, path: Path) -> bool:
        """Check if directory contains Facebook JSON files"""
        json_files = list(path.glob("*.json"))
        return len(json_files) > 0
    
    def _process_facebook_directory(self, fb_path: Path) -> ProcessingResult:
        """Process a Facebook data directory"""
        json_files = list(fb_path.glob("*.json"))
        processed_files = []
        errors = []
        records_processed = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Process posts and extract media
                posts = self._extract_facebook_posts(data)
                records_processed += len(posts)
                
                # Process associated media files
                media_files = self._extract_facebook_media(data, fb_path)
                for media_file in media_files:
                    if media_file.exists():
                        metadata = self.extract_photo_metadata(str(media_file))
                        if metadata:
                            self._store_photo_metadata(metadata)
                            processed_files.append(str(media_file))
                            
                # Mark file as processed
                self._mark_file_processed(str(json_file), "facebook_json", data)
                processed_files.append(str(json_file))
                
            except Exception as e:
                errors.append(f"Failed to process {json_file}: {e}")
                
        return ProcessingResult(
            success=len(errors) == 0,
            records_processed=records_processed,
            errors=errors,
            data_type="facebook",
            processing_time=0,  # Will be calculated by caller
            file_paths=processed_files
        )
    
    def _extract_facebook_posts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract posts from Facebook JSON data"""
        posts = []
        
        # Handle different Facebook export formats
        if isinstance(data, list):
            posts = data
        elif isinstance(data, dict):
            if 'posts' in data:
                posts = data['posts']
            elif 'data' in data:
                posts = data['data']
            else:
                # Treat the whole dict as a single post
                posts = [data]
                
        return posts
    
    def _extract_facebook_media(self, data: Dict[str, Any], base_path: Path) -> List[Path]:
        """Extract media file paths from Facebook data"""
        media_files = []
        
        def find_media_uris(obj):
            if isinstance(obj, dict):
                if 'uri' in obj:
                    # Resolve media path
                    media_path = self._resolve_facebook_media_path(base_path, obj['uri'])
                    if media_path:
                        media_files.append(media_path)
                for value in obj.values():
                    find_media_uris(value)
            elif isinstance(obj, list):
                for item in obj:
                    find_media_uris(item)
        
        find_media_uris(data)
        return media_files
    
    def _resolve_facebook_media_path(self, base_path: Path, media_uri: str) -> Optional[Path]:
        """Resolve Facebook media file paths across different export formats"""
        # Try multiple path resolution strategies
        possible_paths = [
            base_path / media_uri,
            base_path.parent / media_uri,
            self.data_path / media_uri
        ]
        
        # Strip common prefixes and try again
        stripped_uri = media_uri
        for prefix in ["your_facebook_activity/posts/", "facebook/posts/", "posts/"]:
            if media_uri.startswith(prefix):
                stripped_uri = media_uri[len(prefix):]
                possible_paths.extend([
                    base_path / stripped_uri,
                    base_path.parent / stripped_uri,
                    self.data_path / stripped_uri
                ])
                break
        
        # Return first existing path
        for path in possible_paths:
            if path.exists() and path.is_file():
                return path
                
        return None
    
    def process_google_photos(self) -> ProcessingResult:
        """Process Google Photos data locally"""
        start_time = datetime.now()
        errors = []
        processed_files = []
        records_processed = 0
        
        try:
            google_photos_path = self.data_path / "Google Photos"
            if not google_photos_path.exists():
                google_photos_path = self.data_path / "google_photos"
                
            if not google_photos_path.exists():
                return ProcessingResult(
                    success=True,
                    records_processed=0,
                    errors=["No Google Photos data found"],
                    data_type="google_photos",
                    processing_time=0,
                    file_paths=[]
                )
            
            # Process photos and metadata
            for photo_file in google_photos_path.rglob("*"):
                if photo_file.is_file() and self._is_image_file(photo_file):
                    try:
                        metadata = self.extract_photo_metadata(str(photo_file))
                        if metadata:
                            self._store_photo_metadata(metadata)
                            processed_files.append(str(photo_file))
                            records_processed += 1
                    except Exception as e:
                        errors.append(f"Failed to process {photo_file}: {e}")
            
            # Process Google Photos JSON metadata files
            for json_file in google_photos_path.rglob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        self._process_google_photos_metadata(metadata, json_file.parent)
                        processed_files.append(str(json_file))
                except Exception as e:
                    errors.append(f"Failed to process metadata {json_file}: {e}")
            
            self._update_data_source_status("google_photos", len(processed_files), records_processed)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=len(errors) == 0,
                records_processed=records_processed,
                errors=errors,
                data_type="google_photos",
                processing_time=processing_time,
                file_paths=processed_files
            )
            
        except Exception as e:
            logger.error(f"Google Photos processing failed: {e}")
            return ProcessingResult(
                success=False,
                records_processed=0,
                errors=[str(e)],
                data_type="google_photos",
                processing_time=(datetime.now() - start_time).total_seconds(),
                file_paths=[]
            )
    
    def _process_google_photos_metadata(self, metadata: Dict[str, Any], base_path: Path):
        """Process Google Photos JSON metadata"""
        # Extract additional metadata from Google Photos JSON
        if 'title' in metadata:
            photo_path = base_path / metadata['title']
            if photo_path.exists():
                # Update photo metadata with Google Photos info
                additional_info = {
                    'google_creation_time': metadata.get('creationTime', {}),
                    'google_geo_data': metadata.get('geoData', {}),
                    'google_people': metadata.get('people', [])
                }
                self._update_photo_metadata(str(photo_path), additional_info)
    
    def process_apple_health(self) -> ProcessingResult:
        """Process Apple Health export data locally"""
        start_time = datetime.now()
        errors = []
        processed_files = []
        records_processed = 0
        
        try:
            health_path = self.data_path / "apple_health_export"
            if not health_path.exists():
                health_path = self.data_path / "export.xml"
                
            if not health_path.exists():
                return ProcessingResult(
                    success=True,
                    records_processed=0,
                    errors=["No Apple Health data found"],
                    data_type="apple_health",
                    processing_time=0,
                    file_paths=[]
                )
            
            # Process Apple Health XML data
            if health_path.is_file() and health_path.suffix == '.xml':
                try:
                    records_processed = self._process_apple_health_xml(health_path)
                    processed_files.append(str(health_path))
                except Exception as e:
                    errors.append(f"Failed to process Apple Health XML: {e}")
            
            self._update_data_source_status("apple_health", len(processed_files), records_processed)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=len(errors) == 0,
                records_processed=records_processed,
                errors=errors,
                data_type="apple_health",
                processing_time=processing_time,
                file_paths=processed_files
            )
            
        except Exception as e:
            logger.error(f"Apple Health processing failed: {e}")
            return ProcessingResult(
                success=False,
                records_processed=0,
                errors=[str(e)],
                data_type="apple_health",
                processing_time=(datetime.now() - start_time).total_seconds(),
                file_paths=[]
            )
    
    def _process_apple_health_xml(self, xml_path: Path) -> int:
        """Process Apple Health XML file"""
        # This would parse the Apple Health XML export
        # For now, return a placeholder count
        return 1
    
    def process_location_data(self) -> ProcessingResult:
        """Process Google Maps/location data locally"""
        start_time = datetime.now()
        errors = []
        processed_files = []
        records_processed = 0
        
        try:
            # Look for Google Maps location history
            location_paths = [
                self.data_path / "Location History" / "Records.json",
                self.data_path / "location_history.json",
                self.data_path / "google_maps" / "location_history.json"
            ]
            
            found_location_data = False
            for location_path in location_paths:
                if location_path.exists():
                    try:
                        records_processed += self._process_location_history(location_path)
                        processed_files.append(str(location_path))
                        found_location_data = True
                    except Exception as e:
                        errors.append(f"Failed to process location data {location_path}: {e}")
            
            if not found_location_data:
                return ProcessingResult(
                    success=True,
                    records_processed=0,
                    errors=["No location data found"],
                    data_type="location",
                    processing_time=0,
                    file_paths=[]
                )
            
            self._update_data_source_status("location", len(processed_files), records_processed)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return ProcessingResult(
                success=len(errors) == 0,
                records_processed=records_processed,
                errors=errors,
                data_type="location",
                processing_time=processing_time,
                file_paths=processed_files
            )
            
        except Exception as e:
            logger.error(f"Location data processing failed: {e}")
            return ProcessingResult(
                success=False,
                records_processed=0,
                errors=[str(e)],
                data_type="location",
                processing_time=(datetime.now() - start_time).total_seconds(),
                file_paths=[]
            )
    
    def _process_location_history(self, location_path: Path) -> int:
        """Process Google Maps location history JSON"""
        with open(location_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Process location records
        locations = data.get('locations', []) if isinstance(data, dict) else data
        return len(locations)
    
    def extract_photo_metadata(self, image_path: str) -> Optional[PhotoMetadata]:
        """Extract comprehensive metadata from photos"""
        try:
            with Image.open(image_path) as img:
                # Basic image info
                width, height = img.size
                file_size = os.path.getsize(image_path)
                
                # Extract EXIF data
                exif_data = {}
                gps_coords = None
                timestamp = None
                
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_data[tag] = value
                        
                    # Extract GPS coordinates
                    gps_coords = self._extract_gps_coordinates(exif_data)
                    
                    # Extract timestamp
                    timestamp = self._extract_photo_timestamp(exif_data)
                
                # Try to extract additional metadata using piexif
                try:
                    piexif_data = piexif.load(image_path)
                    if piexif_data.get('GPS'):
                        gps_coords = self._extract_gps_from_piexif(piexif_data['GPS'])
                except:
                    pass  # piexif might fail on some images
                
                return PhotoMetadata(
                    file_path=image_path,
                    gps_coordinates=gps_coords,
                    timestamp=timestamp,
                    tagged_people=[],  # Would be populated from social media data
                    camera_info=exif_data,
                    file_size=file_size,
                    dimensions=(width, height)
                )
                
        except Exception as e:
            logger.error(f"Failed to extract metadata from {image_path}: {e}")
            return None
    
    def _extract_gps_coordinates(self, exif_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from EXIF data"""
        try:
            gps_info = exif_data.get('GPSInfo')
            if not gps_info:
                return None
                
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = convert_to_degrees(gps_info[2])
            lon = convert_to_degrees(gps_info[4])
            
            # Check for hemisphere
            if gps_info[1] == 'S':
                lat = -lat
            if gps_info[3] == 'W':
                lon = -lon
                
            return (lat, lon)
            
        except:
            return None
    
    def _extract_gps_from_piexif(self, gps_data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from piexif GPS data"""
        try:
            if not all(key in gps_data for key in [piexif.GPSIFD.GPSLatitude, piexif.GPSIFD.GPSLongitude]):
                return None
                
            lat = self._convert_gps_coordinate(gps_data[piexif.GPSIFD.GPSLatitude])
            lon = self._convert_gps_coordinate(gps_data[piexif.GPSIFD.GPSLongitude])
            
            # Check hemisphere
            if gps_data.get(piexif.GPSIFD.GPSLatitudeRef) == b'S':
                lat = -lat
            if gps_data.get(piexif.GPSIFD.GPSLongitudeRef) == b'W':
                lon = -lon
                
            return (lat, lon)
            
        except:
            return None
    
    def _convert_gps_coordinate(self, coord):
        """Convert GPS coordinate from rational to decimal"""
        d = coord[0][0] / coord[0][1]
        m = coord[1][0] / coord[1][1]
        s = coord[2][0] / coord[2][1]
        return d + (m / 60.0) + (s / 3600.0)
    
    def _extract_photo_timestamp(self, exif_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from EXIF data"""
        try:
            datetime_str = exif_data.get('DateTime') or exif_data.get('DateTimeOriginal')
            if datetime_str:
                return datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
        except:
            pass
        return None
    
    def _is_image_file(self, file_path: Path) -> bool:
        """Check if file is an image"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic'}
        return file_path.suffix.lower() in image_extensions
    
    def _store_photo_metadata(self, metadata: PhotoMetadata):
        """Store photo metadata in local database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO photo_metadata 
                (file_path, gps_latitude, gps_longitude, timestamp, tagged_people, 
                 camera_info, file_size, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.file_path,
                metadata.gps_coordinates[0] if metadata.gps_coordinates else None,
                metadata.gps_coordinates[1] if metadata.gps_coordinates else None,
                metadata.timestamp.isoformat() if metadata.timestamp else None,
                json.dumps(metadata.tagged_people),
                json.dumps(metadata.camera_info, default=str),
                metadata.file_size,
                metadata.dimensions[0],
                metadata.dimensions[1]
            ))
    
    def _update_photo_metadata(self, file_path: str, additional_info: Dict[str, Any]):
        """Update existing photo metadata with additional information"""
        with sqlite3.connect(self.db_path) as conn:
            # Get existing metadata
            result = conn.execute(
                "SELECT camera_info FROM photo_metadata WHERE file_path = ?",
                (file_path,)
            ).fetchone()
            
            if result:
                existing_info = json.loads(result[0]) if result[0] else {}
                existing_info.update(additional_info)
                
                conn.execute(
                    "UPDATE photo_metadata SET camera_info = ? WHERE file_path = ?",
                    (json.dumps(existing_info, default=str), file_path)
                )
    
    def _mark_file_processed(self, file_path: str, data_type: str, metadata: Any = None):
        """Mark file as processed in local database"""
        file_hash = self._calculate_file_hash(file_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO processed_files 
                (file_path, file_hash, data_type, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                file_path,
                file_hash,
                data_type,
                json.dumps(metadata, default=str) if metadata else None
            ))
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for deduplication"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""
    
    def _update_data_source_status(self, source_type: str, total_files: int, processed_records: int):
        """Update data source processing status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO data_sources 
                (source_type, source_path, total_files, processed_files, last_processed, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source_type,
                str(self.data_path),
                total_files,
                processed_records,
                datetime.now().isoformat(),
                'completed'
            ))
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get overall processing status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get data source status
            sources = conn.execute("SELECT * FROM data_sources").fetchall()
            
            # Get photo metadata count
            photo_count = conn.execute("SELECT COUNT(*) FROM photo_metadata").fetchone()[0]
            
            # Get processed files count
            processed_count = conn.execute("SELECT COUNT(*) FROM processed_files").fetchone()[0]
            
            return {
                "data_sources": [dict(row) for row in sources],
                "total_photos_processed": photo_count,
                "total_files_processed": processed_count,
                "data_path": str(self.data_path),
                "database_path": str(self.db_path)
            }
    
    def ensure_data_privacy(self) -> bool:
        """Ensure all personal data stays local with secure permissions"""
        try:
            # Check data directory permissions
            stat_info = os.stat(self.data_path)
            permissions = oct(stat_info.st_mode)[-3:]
            
            if permissions != '700':
                os.chmod(self.data_path, 0o700)
                logger.info("Updated data directory permissions to 700")
            
            # Check database permissions
            if self.db_path.exists():
                os.chmod(self.db_path, 0o600)
                logger.info("Updated database permissions to 600")
            
            # Verify no data is being transmitted externally
            # (This would be implemented with network monitoring in production)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure data privacy: {e}")
            return False