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

import os
import shutil
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import pickle

from src.common.objects.LLEntry_obj import LLEntry
from src.common.objects.enhanced_llentry import EnhancedLLEntry
from src.common.persistence.personal_data_db import PersonalDataDBConnector
from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector


class DatabaseMigrator:
    """Handles migration from legacy database to enhanced AI-focused schema"""
    
    def __init__(self):
        self.os_path_to_data = os.environ.get('APP_DATA_DIR', "personal-data/app_data")
        self.db_path = os.path.join(self.os_path_to_data, "raw_data.db")
        self.backup_path = os.path.join(self.os_path_to_data, f"raw_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    
    def create_backup(self) -> bool:
        """Create a backup of the existing database before migration"""
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.backup_path)
                print(f"Database backup created at: {self.backup_path}")
                return True
            else:
                print("No existing database found, skipping backup")
                return True
        except Exception as e:
            print(f"Failed to create backup: {e}")
            return False
    
    def migrate_to_enhanced_schema(self) -> bool:
        """Migrate existing database to enhanced schema"""
        try:
            # Create backup first
            if not self.create_backup():
                return False
            
            # Initialize enhanced database connector (this will perform the migration)
            enhanced_db = EnhancedPersonalDataDBConnector()
            
            # Verify migration was successful
            if enhanced_db.verify_data_integrity():
                print("Database migration completed successfully")
                return True
            else:
                print("Database migration failed integrity check")
                return False
                
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    def migrate_llentries_to_enhanced(self, batch_size: int = 1000) -> int:
        """Convert existing LLEntry objects to EnhancedLLEntry objects"""
        try:
            db = EnhancedPersonalDataDBConnector()
            
            # Get all entries that haven't been processed yet
            cursor = db.cursor.execute("""
                SELECT id, data FROM personal_data 
                WHERE ai_processed = 0 AND data IS NOT NULL
                ORDER BY id
            """)
            
            processed_count = 0
            batch = []
            
            for row in cursor.fetchall():
                entry_id, pickled_data = row
                
                try:
                    # Unpickle the LLEntry object
                    llentry = pickle.loads(pickled_data)
                    
                    # Convert to EnhancedLLEntry
                    enhanced_entry = EnhancedLLEntry.from_llentry(llentry)
                    enhanced_entry.ai_processed = True
                    enhanced_entry.ai_processing_version = "1.0"
                    
                    # Add to batch
                    batch.append((entry_id, enhanced_entry))
                    
                    if len(batch) >= batch_size:
                        self._process_batch(db, batch)
                        processed_count += len(batch)
                        batch = []
                        print(f"Processed {processed_count} entries...")
                
                except Exception as e:
                    print(f"Failed to process entry {entry_id}: {e}")
                    continue
            
            # Process remaining batch
            if batch:
                self._process_batch(db, batch)
                processed_count += len(batch)
            
            print(f"Migration completed. Processed {processed_count} entries.")
            return processed_count
            
        except Exception as e:
            print(f"Failed to migrate LLEntries: {e}")
            return 0
    
    def _process_batch(self, db: EnhancedPersonalDataDBConnector, batch: List[tuple]):
        """Process a batch of enhanced entries"""
        for entry_id, enhanced_entry in batch:
            try:
                # Update the database with enhanced data
                update_data = {
                    'data': pickle.dumps(enhanced_entry),
                    'ai_processed': 1,
                    'ai_processing_version': enhanced_entry.ai_processing_version,
                    'narrative_significance': enhanced_entry.narrative_significance,
                    'emotional_context': enhanced_entry.to_enhanced_json() if enhanced_entry.emotional_context else None,
                    'life_phase': enhanced_entry.life_phase,
                    'story_potential': enhanced_entry.story_potential,
                    'thematic_tags': enhanced_entry.to_enhanced_json() if enhanced_entry.thematic_tags else None,
                    'ai_metadata': enhanced_entry.to_enhanced_json() if enhanced_entry.ai_metadata else None
                }
                
                # Update the record
                db.cursor.execute("""
                    UPDATE personal_data 
                    SET data = ?, ai_processed = ?, ai_processing_version = ?,
                        narrative_significance = ?, emotional_context = ?, life_phase = ?,
                        story_potential = ?, thematic_tags = ?, ai_metadata = ?
                    WHERE id = ?
                """, (
                    update_data['data'], update_data['ai_processed'], 
                    update_data['ai_processing_version'], update_data['narrative_significance'],
                    update_data['emotional_context'], update_data['life_phase'],
                    update_data['story_potential'], update_data['thematic_tags'],
                    update_data['ai_metadata'], entry_id
                ))
                
            except Exception as e:
                print(f"Failed to update entry {entry_id}: {e}")
                continue
        
        db.con.commit()
    
    def rollback_migration(self) -> bool:
        """Rollback to the backup database if migration fails"""
        try:
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.db_path)
                print(f"Database rolled back from backup: {self.backup_path}")
                return True
            else:
                print("No backup found for rollback")
                return False
        except Exception as e:
            print(f"Rollback failed: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get the current migration status"""
        try:
            db = EnhancedPersonalDataDBConnector()
            
            total_entries = db.count_entries()
            
            # Count processed entries
            processed_result = db.cursor.execute(
                "SELECT COUNT(*) FROM personal_data WHERE ai_processed = 1"
            ).fetchone()
            processed_count = processed_result[0] if processed_result else 0
            
            # Get schema version
            schema_version = db.get_schema_version()
            
            return {
                'schema_version': schema_version,
                'total_entries': total_entries,
                'processed_entries': processed_count,
                'migration_complete': processed_count == total_entries,
                'data_integrity_ok': db.verify_data_integrity()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'migration_complete': False,
                'data_integrity_ok': False
            }


def main():
    """Main migration script"""
    migrator = DatabaseMigrator()
    
    print("Starting database migration to enhanced schema...")
    
    # Perform the migration
    if migrator.migrate_to_enhanced_schema():
        print("Schema migration successful")
        
        # Migrate LLEntry objects to enhanced format
        print("Converting LLEntry objects to enhanced format...")
        processed = migrator.migrate_llentries_to_enhanced()
        
        if processed > 0:
            print(f"Successfully migrated {processed} entries")
            
            # Show final status
            status = migrator.get_migration_status()
            print(f"Migration Status: {status}")
        else:
            print("No entries to migrate or migration failed")
    else:
        print("Schema migration failed")


if __name__ == "__main__":
    main()