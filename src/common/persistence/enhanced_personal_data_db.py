# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sqlite3
import json
import pickle
import os
from pathlib import Path
from sqlite3 import Cursor
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.common.persistence.personal_data_db import PersonalDataDBConnector
from src.common.objects.enhanced_llentry import (
    EnhancedLLEntry, Story, PersonProfile, Gallery, CompositeMemory
)

os_path_to_data = os.environ['APP_DATA_DIR'] if 'APP_DATA_DIR' in os.environ else "personal-data/app_data"


class EnhancedPersonalDataDBConnector(PersonalDataDBConnector):
    """Enhanced database connector with AI-focused tables and migration support"""
    
    # Current schema version for migration tracking
    SCHEMA_VERSION = "2.0"
    
    # Enhanced table definitions
    enhanced_tables = [
        "stories", "person_profiles", "galleries", "composite_memories", 
        "schema_migrations"
    ]
    
    enhanced_ddl = {
        "stories": """CREATE TABLE stories(
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            narrative_mode TEXT NOT NULL,
            source_memory_ids TEXT NOT NULL,  -- JSON array
            created_at TIMESTAMP NOT NULL,
            voice_narration_path TEXT,
            metadata TEXT  -- JSON for additional story metadata
        )""",
        
        "person_profiles": """CREATE TABLE person_profiles(
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            representative_photos TEXT,  -- JSON array
            first_appearance TIMESTAMP NOT NULL,
            last_appearance TIMESTAMP NOT NULL,
            interaction_peaks TEXT,  -- JSON array of timestamps
            shared_contexts TEXT,  -- JSON array
            relationship_evolution TEXT,  -- JSON array
            profile_metadata TEXT  -- JSON for additional profile data
        )""",
        
        "galleries": """CREATE TABLE galleries(
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            memory_ids TEXT NOT NULL,  -- JSON array
            creation_method TEXT NOT NULL,
            semantic_ordering TEXT,  -- JSON array of indices
            created_at TIMESTAMP NOT NULL,
            gallery_metadata TEXT  -- JSON for additional gallery data
        )""",
        
        "composite_memories": """CREATE TABLE composite_memories(
            id TEXT PRIMARY KEY,
            theme TEXT NOT NULL,
            constituent_memory_ids TEXT NOT NULL,  -- JSON array
            narrative_summary TEXT,
            temporal_span_start TIMESTAMP,
            temporal_span_end TIMESTAMP,
            significance_score REAL DEFAULT 0.0,
            composite_metadata TEXT  -- JSON for additional composite data
        )""",
        
        "schema_migrations": """CREATE TABLE schema_migrations(
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL,
            description TEXT
        )"""
    }
    
    # Enhanced indexes for performance
    enhanced_indexes = {
        "stories": [
            'CREATE INDEX "idx_stories_created_at" ON "stories" ("created_at")',
            'CREATE INDEX "idx_stories_narrative_mode" ON "stories" ("narrative_mode")'
        ],
        "person_profiles": [
            'CREATE INDEX "idx_person_profiles_name" ON "person_profiles" ("name")',
            'CREATE INDEX "idx_person_profiles_first_appearance" ON "person_profiles" ("first_appearance")'
        ],
        "galleries": [
            'CREATE INDEX "idx_galleries_creation_method" ON "galleries" ("creation_method")',
            'CREATE INDEX "idx_galleries_created_at" ON "galleries" ("created_at")'
        ],
        "composite_memories": [
            'CREATE INDEX "idx_composite_memories_theme" ON "composite_memories" ("theme")',
            'CREATE INDEX "idx_composite_memories_significance" ON "composite_memories" ("significance_score")'
        ]
    }
    
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EnhancedPersonalDataDBConnector, cls).__new__(cls)
            if not os.path.exists(os_path_to_data):
                print("Path does not exist. Creating", os_path_to_data)
                os.makedirs(os_path_to_data, exist_ok=True)
            cls.instance.con = sqlite3.connect(os.path.join(os_path_to_data, "raw_data.db"))
            cls.instance.cursor = cls.instance.con.cursor()
            cls.instance.setup_tables()
            cls.instance.setup_enhanced_tables()
            cls.instance.migrate_database()
        return cls.instance
    
    def setup_enhanced_tables(self):
        """Set up the enhanced AI-focused tables"""
        for table in self.enhanced_tables:
            lookup_sql = "SELECT name FROM sqlite_master WHERE name='" + table + "'"
            res = self.cursor.execute(lookup_sql)
            if res.fetchone() is None:
                create_sql = self.enhanced_ddl[table]
                print(f"Creating enhanced table: {table}")
                self.execute_write(create_sql)
                
                # Create indexes if they exist for this table
                if table in self.enhanced_indexes:
                    for idx_sql in self.enhanced_indexes[table]:
                        print(f"Creating index for {table}")
                        self.execute_write(idx_sql)
            else:
                print(f"Enhanced table {table} found.")
    
    def migrate_database(self):
        """Perform database migrations to enhance existing data"""
        # Check if migration has already been applied
        try:
            migration_check = self.cursor.execute(
                "SELECT version FROM schema_migrations WHERE version = ?", 
                (self.SCHEMA_VERSION,)
            ).fetchone()
            
            if migration_check:
                print(f"Database already migrated to version {self.SCHEMA_VERSION}")
                return
        except sqlite3.OperationalError:
            # schema_migrations table doesn't exist yet, continue with migration
            pass
        
        print(f"Migrating database to version {self.SCHEMA_VERSION}")
        
        # Add enhanced fields to existing personal_data table
        self._add_enhanced_columns()
        
        # Record the migration
        self.execute_write(
            "INSERT OR REPLACE INTO schema_migrations (version, applied_at, description) VALUES (?, ?, ?)",
            (self.SCHEMA_VERSION, datetime.now().isoformat(), "Added AI-focused enhancements")
        )
        
        print("Database migration completed successfully")
    
    def _add_enhanced_columns(self):
        """Add enhanced columns to existing personal_data table"""
        enhanced_columns = [
            ("narrative_significance", "REAL DEFAULT 0.0"),
            ("emotional_context", "TEXT"),  # JSON
            ("life_phase", "TEXT DEFAULT ''"),
            ("people_relationships", "TEXT"),  # JSON
            ("social_context", "TEXT"),  # JSON
            ("story_potential", "REAL DEFAULT 0.0"),
            ("thematic_tags", "TEXT"),  # JSON
            ("composite_memory_ids", "TEXT"),  # JSON
            ("ai_processed", "INTEGER DEFAULT 0"),
            ("ai_processing_version", "TEXT DEFAULT '1.0'"),
            ("ai_metadata", "TEXT")  # JSON
        ]
        
        for column_name, column_def in enhanced_columns:
            try:
                alter_sql = f"ALTER TABLE personal_data ADD COLUMN {column_name} {column_def}"
                self.execute_write(alter_sql)
                print(f"Added column {column_name} to personal_data table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"Column {column_name} already exists, skipping")
                else:
                    raise e
    
    def get_schema_version(self) -> str:
        """Get the current schema version"""
        try:
            result = self.cursor.execute(
                "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1"
            ).fetchone()
            return result[0] if result else "1.0"
        except sqlite3.OperationalError:
            return "1.0"
    
    def count_entries(self) -> int:
        """Count total entries in personal_data table"""
        result = self.cursor.execute("SELECT COUNT(*) FROM personal_data").fetchone()
        return result[0] if result else 0
    
    def verify_data_integrity(self) -> bool:
        """Verify that data migration preserved all original data"""
        try:
            # Check that all original columns still exist and have data
            original_columns = [
                "id", "source_id", "data_timestamp", "dedup_key", "data",
                "imageFileName", "imageFilePath", "location", "captions", "embeddings"
            ]
            
            for column in original_columns:
                result = self.cursor.execute(f"SELECT COUNT({column}) FROM personal_data").fetchone()
                if result is None:
                    return False
            
            # Check that enhanced columns were added
            enhanced_columns = [
                "narrative_significance", "emotional_context", "life_phase",
                "ai_processed", "ai_processing_version"
            ]
            
            for column in enhanced_columns:
                try:
                    self.cursor.execute(f"SELECT {column} FROM personal_data LIMIT 1")
                except sqlite3.OperationalError:
                    return False
            
            return True
        except Exception as e:
            print(f"Data integrity check failed: {e}")
            return False
    
    # Enhanced data access methods
    
    def add_story(self, story: Story):
        """Add a story to the database"""
        story_data = {
            'id': story.id,
            'title': story.title,
            'narrative_mode': story.narrative_mode,
            'source_memory_ids': json.dumps(story.source_memory_ids),
            'created_at': story.created_at.isoformat(),
            'voice_narration_path': story.voice_narration_path,
            'metadata': json.dumps({'chapters': [chapter.to_dict() for chapter in story.chapters]})
        }
        self.add_or_replace("stories", story_data, "id")
    
    def add_person_profile(self, profile: PersonProfile):
        """Add a person profile to the database"""
        profile_data = {
            'id': profile.id,
            'name': profile.name,
            'representative_photos': json.dumps(profile.representative_photos),
            'first_appearance': profile.first_appearance.isoformat(),
            'last_appearance': profile.last_appearance.isoformat(),
            'interaction_peaks': json.dumps([peak.isoformat() for peak in profile.interaction_peaks]),
            'shared_contexts': json.dumps(profile.shared_contexts),
            'relationship_evolution': json.dumps(profile.relationship_evolution),
            'profile_metadata': json.dumps({})
        }
        self.add_or_replace("person_profiles", profile_data, "id")
    
    def add_gallery(self, gallery: Gallery):
        """Add a gallery to the database"""
        gallery_data = {
            'id': gallery.id,
            'title': gallery.title,
            'description': gallery.description,
            'memory_ids': json.dumps(gallery.memory_ids),
            'creation_method': gallery.creation_method,
            'semantic_ordering': json.dumps(gallery.semantic_ordering),
            'created_at': gallery.created_at.isoformat(),
            'gallery_metadata': json.dumps({})
        }
        self.add_or_replace("galleries", gallery_data, "id")
    
    def add_composite_memory(self, composite: CompositeMemory):
        """Add a composite memory to the database"""
        composite_data = {
            'id': composite.id,
            'theme': composite.theme,
            'constituent_memory_ids': json.dumps(composite.constituent_memory_ids),
            'narrative_summary': composite.narrative_summary,
            'temporal_span_start': composite.temporal_span[0].isoformat(),
            'temporal_span_end': composite.temporal_span[1].isoformat(),
            'significance_score': composite.significance_score,
            'composite_metadata': json.dumps({})
        }
        self.add_or_replace("composite_memories", composite_data, "id")
    
    def get_stories(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve stories from the database"""
        sql = "SELECT * FROM stories ORDER BY created_at DESC"
        if limit:
            sql += f" LIMIT {limit}"
        
        result = self.cursor.execute(sql)
        stories = []
        for row in result.fetchall():
            story_dict = {
                'id': row[0],
                'title': row[1],
                'narrative_mode': row[2],
                'source_memory_ids': json.loads(row[3]),
                'created_at': row[4],
                'voice_narration_path': row[5],
                'chapters': json.loads(row[6])['chapters'] if row[6] else []
            }
            stories.append(story_dict)
        return stories
    
    def get_person_profiles(self) -> List[Dict[str, Any]]:
        """Retrieve person profiles from the database"""
        result = self.cursor.execute("SELECT * FROM person_profiles ORDER BY name")
        profiles = []
        for row in result.fetchall():
            profile_dict = {
                'id': row[0],
                'name': row[1],
                'representative_photos': json.loads(row[2]) if row[2] else [],
                'first_appearance': row[3],
                'last_appearance': row[4],
                'interaction_peaks': json.loads(row[5]) if row[5] else [],
                'shared_contexts': json.loads(row[6]) if row[6] else [],
                'relationship_evolution': json.loads(row[7]) if row[7] else []
            }
            profiles.append(profile_dict)
        return profiles
    
    def get_galleries(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve galleries from the database"""
        sql = "SELECT * FROM galleries ORDER BY created_at DESC"
        if limit:
            sql += f" LIMIT {limit}"
        
        result = self.cursor.execute(sql)
        galleries = []
        for row in result.fetchall():
            gallery_dict = {
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'memory_ids': json.loads(row[3]) if row[3] else [],
                'creation_method': row[4],
                'semantic_ordering': json.loads(row[5]) if row[5] else [],
                'created_at': row[6]
            }
            galleries.append(gallery_dict)
        return galleries