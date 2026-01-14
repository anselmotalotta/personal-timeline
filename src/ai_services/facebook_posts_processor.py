"""
Facebook Posts Timeline Processor
Processes Facebook posts data for timeline visualization
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class FacebookPost:
    """Individual Facebook post matching design document specification"""
    id: str
    content: str
    timestamp: datetime
    post_type: str  # 'status', 'photo', 'video', 'link'
    media_files: List[str]
    reactions: Dict[str, int]
    comments_count: int
    location: Optional[str]
    tagged_people: List[str]

@dataclass
class TimelineData:
    """Timeline data for chart visualization"""
    date: str
    post_count: int
    has_media_count: int

@dataclass
class TimelineStats:
    """Timeline statistics matching design document specification"""
    date: str
    post_count: int
    media_count: int
    reaction_count: int
    post_types: Dict[str, int]

@dataclass
class ProcessingResult:
    """Result of Facebook data processing operation"""
    success: bool
    total_posts: int
    processed_posts: int
    stored_posts: int
    skipped_posts: int
    errors: List[str]

class FacebookProcessor:
    """Processes Facebook posts for timeline visualization"""
    
    def __init__(self, data_path: str = "./MyData"):
        self.data_path = Path(data_path)
        self.db_path = self.data_path / "facebook_timeline.db"
        self._init_database()
        
    def _init_database(self):
        """Initialize Facebook timeline database with schema matching design document"""
        with sqlite3.connect(self.db_path) as conn:
            # Create facebook_posts table with complete schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facebook_posts (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    post_type TEXT NOT NULL,
                    media_files TEXT,  -- JSON array of media file paths
                    reactions TEXT,    -- JSON object of reaction counts
                    comments_count INTEGER DEFAULT 0,
                    location TEXT,
                    tagged_people TEXT,  -- JSON array of tagged person names
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS timeline_cache (
                    date TEXT PRIMARY KEY,
                    post_count INTEGER NOT NULL,
                    has_media_count INTEGER NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create data source tracking table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_source_info (
                    id INTEGER PRIMARY KEY,
                    data_path TEXT NOT NULL,
                    last_processed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_posts INTEGER DEFAULT 0,
                    source_file TEXT,
                    is_current BOOLEAN DEFAULT 1
                )
            """)
            
            # Create indexes for performance as specified in design document
            # Use IF NOT EXISTS and check if columns exist first
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_facebook_posts_timestamp ON facebook_posts(timestamp)")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not create timestamp index: {e}")
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_facebook_posts_type ON facebook_posts(post_type)")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not create post_type index: {e}")
            
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_date ON facebook_posts(date(timestamp))")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not create date index: {e}")
                
            # Verify table structure
            cursor = conn.execute("PRAGMA table_info(facebook_posts)")
            columns = [row[1] for row in cursor.fetchall()]
            logger.info(f"Facebook posts table columns: {columns}")
    
    def _check_data_path_changed(self) -> bool:
        """Check if the data path has changed since last processing"""
        current_data_path = str(self.data_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT data_path, source_file FROM data_source_info 
                WHERE is_current = 1 
                ORDER BY last_processed DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if not result:
                logger.info("No previous data source found - first time processing")
                return True
                
            last_data_path, last_source_file = result
            
            # Check if data path changed
            if last_data_path != current_data_path:
                logger.info(f"Data path changed from {last_data_path} to {current_data_path}")
                return True
                
            # Check if source file still exists
            possible_files = [
                self.data_path / "your_facebook_activity" / "posts" / "your_posts__check_ins__photos_and_videos_1.json",
                self.data_path / "facebook_processed" / "posts.json",
                self.data_path / "facebook" / "posts.json"
            ]
            
            current_source_file = None
            for file_path in possible_files:
                if file_path.exists():
                    current_source_file = str(file_path)
                    break
            
            if current_source_file != last_source_file:
                logger.info(f"Source file changed from {last_source_file} to {current_source_file}")
                return True
                
            return False
    
    def _archive_old_data(self):
        """Archive old data when data path changes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_db_path = self.data_path / f"facebook_timeline_archive_{timestamp}.db"
        
        try:
            # Copy current database to archive
            import shutil
            if self.db_path.exists():
                shutil.copy2(self.db_path, archive_db_path)
                logger.info(f"Archived old database to {archive_db_path}")
            
            # Mark old data source as not current
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE data_source_info SET is_current = 0")
                
            # Clear old data
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM facebook_posts")
                conn.execute("DELETE FROM timeline_cache")
                logger.info("Cleared old Facebook posts data")
                
        except Exception as e:
            logger.error(f"Failed to archive old data: {e}")
    
    def _record_data_source(self, source_file: str, total_posts: int):
        """Record the current data source information"""
        current_data_path = str(self.data_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO data_source_info (data_path, source_file, total_posts, is_current)
                VALUES (?, ?, ?, 1)
            """, (current_data_path, source_file, total_posts))
    
    def process_facebook_data(self) -> ProcessingResult:
        """
        Process Facebook posts from JSON file and store in database
        Returns processing statistics
        """
        # Check if data path has changed and archive old data if needed
        if self._check_data_path_changed():
            logger.info("Data path changed - archiving old data and starting fresh")
            self._archive_old_data()
        
        # Try multiple possible locations for Facebook posts data
        possible_files = [
            self.data_path / "your_facebook_activity" / "posts" / "your_posts__check_ins__photos_and_videos_1.json",
            self.data_path / "facebook_processed" / "posts.json",  # Fallback to processed data
            self.data_path / "facebook" / "posts.json"  # Fallback to sample data
        ]
        
        posts_file = None
        for file_path in possible_files:
            if file_path.exists():
                posts_file = file_path
                logger.info(f"Found Facebook posts file: {posts_file}")
                break
        
        if not posts_file:
            logger.error(f"Facebook posts file not found in any of these locations: {possible_files}")
            return ProcessingResult(
                success=False,
                total_posts=0,
                processed_posts=0,
                stored_posts=0,
                skipped_posts=0,
                errors=[f"Posts file not found in any expected location"]
            )
        
        try:
            with open(posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different Facebook export formats
            if isinstance(data, list):
                # Real Facebook export format - direct array
                posts_data = data
                logger.info(f"Processing real Facebook export data with {len(posts_data)} posts")
            elif isinstance(data, dict) and 'posts_v2' in data:
                # Sample/processed format
                posts_data = data.get('posts_v2', [])
                logger.info(f"Processing sample Facebook data with {len(posts_data)} posts")
            else:
                logger.warning("Unknown Facebook data format")
                return ProcessingResult(
                    success=False,
                    total_posts=0,
                    processed_posts=0,
                    stored_posts=0,
                    skipped_posts=0,
                    errors=["Unknown Facebook data format"]
                )
            
            if not posts_data:
                logger.warning("No posts found in Facebook data")
                return ProcessingResult(
                    success=False,
                    total_posts=0,
                    processed_posts=0,
                    stored_posts=0,
                    skipped_posts=0,
                    errors=["No posts found in Facebook data"]
                )
            
            processed_posts = []
            errors = []
            skipped_posts = 0
            post_counter = 0  # Add counter for unique ID generation
            
            for i, post_data in enumerate(posts_data):
                try:
                    post = self._parse_facebook_post(post_data, post_counter)
                    if post:
                        processed_posts.append(post)
                        post_counter += 1
                    else:
                        skipped_posts += 1
                        errors.append(f"Failed to parse post at index {i}: missing required data")
                except Exception as e:
                    logger.warning(f"Failed to parse post at index {i}: {e}")
                    skipped_posts += 1
                    errors.append(f"Failed to parse post at index {i}: {str(e)}")
            
            # Store posts in database
            stored_count = self._store_posts(processed_posts)
            
            # Update timeline cache
            self._update_timeline_cache()
            
            # Record the data source for future reference
            self._record_data_source(str(posts_file), len(posts_data))
            
            return ProcessingResult(
                success=True,
                total_posts=len(posts_data),
                processed_posts=len(processed_posts),
                stored_posts=stored_count,
                skipped_posts=skipped_posts,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Failed to process Facebook posts: {e}")
            return ProcessingResult(
                success=False,
                total_posts=0,
                processed_posts=0,
                stored_posts=0,
                skipped_posts=0,
                errors=[f"Failed to process Facebook posts: {str(e)}"]
            )
    
    def _parse_facebook_post(self, post_data: Dict[str, Any], counter: int = 0) -> Optional[FacebookPost]:
        """Parse individual Facebook post from JSON data according to design specification"""
        try:
            timestamp = post_data.get('timestamp')
            if not timestamp:
                return None
            
            # Convert timestamp to datetime
            post_datetime = datetime.fromtimestamp(timestamp)
            
            # Extract post content
            content = ""
            data_array = post_data.get('data', [])
            if data_array and isinstance(data_array, list):
                for data_item in data_array:
                    if isinstance(data_item, dict) and 'post' in data_item:
                        content = data_item['post']
                        break
            
            # If no content found in data array, content remains empty string
            
            # Extract media files
            media_files = []
            attachments = post_data.get('attachments', [])
            for attachment in attachments:
                if isinstance(attachment, dict) and 'data' in attachment:
                    for data_item in attachment['data']:
                        if isinstance(data_item, dict) and 'media' in data_item:
                            media = data_item['media']
                            if isinstance(media, dict) and 'uri' in media:
                                media_files.append(media['uri'])
            
            # Determine post type based on content and attachments
            post_type = self._determine_post_type(content, media_files, attachments)
            
            # Extract reactions (if available in data)
            reactions = {}
            reactions_data = post_data.get('reactions', {})
            if isinstance(reactions_data, dict):
                reactions = reactions_data
            
            # Extract comments count (if available)
            comments_count = 0
            comments_data = post_data.get('comments', [])
            if isinstance(comments_data, list):
                comments_count = len(comments_data)
            
            # Extract location (if available)
            location = None
            place_data = post_data.get('place')
            if isinstance(place_data, dict) and 'name' in place_data:
                location = place_data['name']
            
            # Extract tagged people (if available)
            tagged_people = []
            tags_data = post_data.get('tags', [])
            if isinstance(tags_data, list):
                for tag in tags_data:
                    if isinstance(tag, dict) and 'name' in tag:
                        tagged_people.append(tag['name'])
            
            # Generate unique ID using timestamp, content, media, and counter to avoid collisions
            id_content = f"{timestamp}_{content[:50]}_{len(media_files)}_{len(tagged_people)}_{counter}"
            post_id = hashlib.md5(id_content.encode()).hexdigest()[:12]
            
            return FacebookPost(
                id=post_id,
                content=content,
                timestamp=post_datetime,
                post_type=post_type,
                media_files=media_files,
                reactions=reactions,
                comments_count=comments_count,
                location=location,
                tagged_people=tagged_people
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse post data: {e}")
            return None
    
    def _determine_post_type(self, content: str, media_files: List[str], attachments: List[Dict]) -> str:
        """Determine post type based on content and attachments"""
        if not content and not media_files:
            return 'status'
        
        # Check for video files
        for media_file in media_files:
            if any(ext in media_file.lower() for ext in ['.mp4', '.mov', '.avi', '.mkv']):
                return 'video'
        
        # Check for photo files
        if media_files:
            return 'photo'
        
        # Check for links in attachments
        for attachment in attachments:
            if isinstance(attachment, dict) and 'data' in attachment:
                for data_item in attachment['data']:
                    if isinstance(data_item, dict) and 'external_context' in data_item:
                        return 'link'
        
        # Default to status
        return 'status'
    
    def _store_posts(self, posts: List[FacebookPost]) -> int:
        """Store posts in database, avoiding duplicates"""
        stored_count = 0
        
        with sqlite3.connect(self.db_path) as conn:
            for post in posts:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO facebook_posts 
                        (id, content, timestamp, post_type, media_files, reactions, 
                         comments_count, location, tagged_people, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        post.id,
                        post.content,
                        post.timestamp.isoformat(),
                        post.post_type,
                        json.dumps(post.media_files),
                        json.dumps(post.reactions),
                        post.comments_count,
                        post.location,
                        json.dumps(post.tagged_people),
                        datetime.now().isoformat()
                    ))
                    stored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to store post {post.id}: {e}")
        
        return stored_count
    
    def _update_timeline_cache(self):
        """Update timeline cache with aggregated data"""
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing cache
            conn.execute("DELETE FROM timeline_cache")
            
            # Aggregate posts by date
            cursor = conn.execute("""
                SELECT 
                    date(timestamp) as date,
                    COUNT(*) as post_count,
                    SUM(CASE WHEN json_array_length(media_files) > 0 THEN 1 ELSE 0 END) as has_media_count
                FROM facebook_posts 
                GROUP BY date(timestamp)
                ORDER BY date
            """)
            
            for row in cursor.fetchall():
                conn.execute("""
                    INSERT INTO timeline_cache (date, post_count, has_media_count)
                    VALUES (?, ?, ?)
                """, row)
    
    def get_timeline_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[TimelineData]:
        """Get timeline data for chart visualization"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT date, post_count, has_media_count FROM timeline_cache"
            params = []
            
            if start_date and end_date:
                query += " WHERE date BETWEEN ? AND ?"
                params = [start_date, end_date]
            elif start_date:
                query += " WHERE date >= ?"
                params = [start_date]
            elif end_date:
                query += " WHERE date <= ?"
                params = [end_date]
            
            query += " ORDER BY date"
            
            cursor = conn.execute(query, params)
            
            return [
                TimelineData(
                    date=row['date'],
                    post_count=row['post_count'],
                    has_media_count=row['has_media_count']
                )
                for row in cursor.fetchall()
            ]
    
    def get_posts_for_date(self, target_date: str) -> List[FacebookPost]:
        """Get all posts for a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute("""
                SELECT id, content, timestamp, post_type, media_files, reactions, 
                       comments_count, location, tagged_people, created_at
                FROM facebook_posts 
                WHERE date(timestamp) = ?
                ORDER BY timestamp DESC
            """, (target_date,))
            
            posts = []
            for row in cursor.fetchall():
                posts.append(FacebookPost(
                    id=row['id'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    post_type=row['post_type'],
                    media_files=json.loads(row['media_files']),
                    reactions=json.loads(row['reactions']),
                    comments_count=row['comments_count'],
                    location=row['location'],
                    tagged_people=json.loads(row['tagged_people'])
                ))
            
            return posts
    
    def get_timeline_stats(self) -> TimelineStats:
        """Get overall timeline statistics matching design document specification"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get basic stats for a specific date (using most recent date as example)
            cursor = conn.execute("""
                SELECT 
                    date(timestamp) as date,
                    COUNT(*) as post_count,
                    SUM(json_array_length(media_files)) as media_count,
                    SUM(json_extract(reactions, '$.like') + 
                        json_extract(reactions, '$.love') + 
                        json_extract(reactions, '$.wow') + 
                        json_extract(reactions, '$.haha') + 
                        json_extract(reactions, '$.sad') + 
                        json_extract(reactions, '$.angry')) as reaction_count,
                    json_group_object(post_type, type_count) as post_types
                FROM (
                    SELECT 
                        timestamp,
                        media_files,
                        reactions,
                        post_type,
                        COUNT(*) as type_count
                    FROM facebook_posts
                    GROUP BY post_type
                ) 
                GROUP BY date(timestamp)
                ORDER BY date DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            
            if not row:
                return TimelineStats(
                    date='',
                    post_count=0,
                    media_count=0,
                    reaction_count=0,
                    post_types={}
                )
            
            # Parse post_types JSON
            post_types = {}
            if row['post_types']:
                try:
                    post_types = json.loads(row['post_types'])
                except:
                    post_types = {}
            
            return TimelineStats(
                date=row['date'] or '',
                post_count=row['post_count'] or 0,
                media_count=row['media_count'] or 0,
                reaction_count=row['reaction_count'] or 0,
                post_types=post_types
            )
    
    def force_reimport_data(self) -> ProcessingResult:
        """Force a complete re-import of Facebook data, archiving old data first"""
        logger.info("Forcing complete re-import of Facebook data")
        
        # Always archive old data and start fresh
        self._archive_old_data()
        
        # Process the data
        return self.process_facebook_data()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status for health monitoring"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) as total_posts FROM facebook_posts")
                total_posts = cursor.fetchone()[0]
                
                # Get current data source info
                cursor = conn.execute("""
                    SELECT data_path, source_file, last_processed, total_posts 
                    FROM data_source_info 
                    WHERE is_current = 1 
                    ORDER BY last_processed DESC 
                    LIMIT 1
                """)
                source_info = cursor.fetchone()
            
            status = {
                "service": "facebook_posts_timeline",
                "status": "active",
                "database_accessible": True,
                "statistics": {
                    "total_posts": total_posts
                },
                "database_path": str(self.db_path)
            }
            
            if source_info:
                status["data_source"] = {
                    "data_path": source_info[0],
                    "source_file": source_info[1],
                    "last_processed": source_info[2],
                    "total_posts_in_source": source_info[3]
                }
            
            return status
        except Exception as e:
            return {
                "service": "facebook_posts_timeline",
                "status": "error",
                "database_accessible": False,
                "error": str(e)
            }

# Global service instance - lazy initialization to avoid startup crashes
_facebook_posts_processor = None

def get_facebook_posts_processor():
    """Get the global FacebookProcessor instance with lazy initialization"""
    global _facebook_posts_processor
    if _facebook_posts_processor is None:
        try:
            _facebook_posts_processor = FacebookProcessor()
            logger.info("Facebook posts processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Facebook posts processor: {e}")
            # Return a mock processor that handles errors gracefully
            _facebook_posts_processor = MockFacebookProcessor()
    return _facebook_posts_processor

class MockFacebookProcessor:
    """Mock processor for when initialization fails"""
    
    def get_service_status(self):
        return {
            "service": "facebook_posts_timeline",
            "status": "error",
            "database_accessible": False,
            "error": "Facebook processor initialization failed"
        }
    
    def get_timeline_data(self, start_date=None, end_date=None):
        return []
    
    def get_posts_for_date(self, target_date):
        return []
    
    def get_timeline_stats(self):
        from .facebook_posts_processor import TimelineStats
        return TimelineStats(
            date='',
            post_count=0,
            media_count=0,
            reaction_count=0,
            post_types={}
        )
    
    def process_facebook_data(self):
        from .facebook_posts_processor import ProcessingResult
        return ProcessingResult(
            success=False,
            total_posts=0,
            processed_posts=0,
            stored_posts=0,
            skipped_posts=0,
            errors=["Facebook processor not initialized"]
        )

# Backward compatibility
facebook_posts_processor = get_facebook_posts_processor()

# Alias for backward compatibility
FacebookPostsProcessor = FacebookProcessor