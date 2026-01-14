"""
Property-based tests for Facebook Posts Timeline Processor
**Feature: facebook-posts-timeline**
"""
import json
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings
import pytest

# Import the modules we're testing
import sys
sys.path.append('src')

from ai_services.facebook_posts_processor import FacebookProcessor, FacebookPost, ProcessingResult


class TestFacebookDataParsing:
    """Test Facebook data parsing completeness and robustness"""
    
    @given(st.lists(
        st.fixed_dictionaries({
            'timestamp': st.integers(min_value=946684800, max_value=2147483647),  # 2000-2038 range
            'data': st.lists(
                st.fixed_dictionaries({
                    'post': st.text(min_size=0, max_size=500)
                }),
                min_size=0, max_size=3
            ),
            'attachments': st.lists(
                st.fixed_dictionaries({
                    'data': st.lists(
                        st.fixed_dictionaries({
                            'media': st.fixed_dictionaries({
                                'uri': st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
                            })
                        }),
                        min_size=0, max_size=2
                    )
                }),
                min_size=0, max_size=2
            ),
            'reactions': st.dictionaries(
                st.sampled_from(['like', 'love', 'wow', 'haha', 'sad', 'angry']),
                st.integers(min_value=0, max_value=1000),
                min_size=0, max_size=6
            ),
            'comments': st.lists(
                st.fixed_dictionaries({
                    'comment': st.text(min_size=0, max_size=200)
                }),
                min_size=0, max_size=10
            ),
            'place': st.one_of(
                st.none(),
                st.fixed_dictionaries({
                    'name': st.text(min_size=1, max_size=100)
                })
            ),
            'tags': st.lists(
                st.fixed_dictionaries({
                    'name': st.text(min_size=1, max_size=50)
                }),
                min_size=0, max_size=5
            )
        }),
        min_size=1, max_size=50
    ))
    @settings(max_examples=100, deadline=None)
    def test_facebook_data_parsing_completeness(self, facebook_posts_data):
        """
        **Feature: facebook-posts-timeline, Property 12: Facebook data parsing completeness**
        For any valid Facebook export JSON file, the parsing process should extract all post content, 
        timestamps, and media references without data loss
        **Validates: Requirements 4.1**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup processor with temporary directory
            processor = FacebookProcessor(temp_dir)
            
            # Create Facebook export structure
            facebook_dir = Path(temp_dir) / "facebook"
            facebook_dir.mkdir(parents=True)
            
            # Create posts.json file with generated data
            posts_data = {
                "posts_v2": facebook_posts_data
            }
            
            posts_file = facebook_dir / "posts.json"
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f)
            
            # Process the data
            result = processor.process_facebook_data()
            
            # Verify processing was successful
            assert isinstance(result, ProcessingResult)
            assert result.success == True
            assert result.total_posts == len(facebook_posts_data)
            
            # Verify no data loss - all posts with valid timestamps should be processed
            valid_posts_count = sum(1 for post in facebook_posts_data if post.get('timestamp'))
            assert result.processed_posts == valid_posts_count
            
            # Verify all processed posts are stored in database
            assert result.stored_posts == result.processed_posts
            
            # Verify data completeness by checking database contents
            with sqlite3.connect(processor.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM facebook_posts")
                stored_count = cursor.fetchone()[0]
                assert stored_count == result.processed_posts
                
                # Verify all essential fields are preserved
                cursor = conn.execute("""
                    SELECT id, content, timestamp, post_type, media_files, reactions, 
                           comments_count, location, tagged_people 
                    FROM facebook_posts
                """)
                
                stored_posts = cursor.fetchall()
                assert len(stored_posts) == result.processed_posts
                
                # Verify each stored post has all required fields
                for stored_post in stored_posts:
                    post_id, content, timestamp, post_type, media_files, reactions, comments_count, location, tagged_people = stored_post
                    
                    # Essential fields should not be None
                    assert post_id is not None
                    assert timestamp is not None
                    assert post_type is not None
                    
                    # Verify timestamp can be parsed back to datetime
                    parsed_timestamp = datetime.fromisoformat(timestamp)
                    assert isinstance(parsed_timestamp, datetime)
                    
                    # Verify JSON fields can be parsed
                    if media_files:
                        parsed_media = json.loads(media_files)
                        assert isinstance(parsed_media, list)
                    
                    if reactions:
                        parsed_reactions = json.loads(reactions)
                        assert isinstance(parsed_reactions, dict)
                    
                    if tagged_people:
                        parsed_tags = json.loads(tagged_people)
                        assert isinstance(parsed_tags, list)
                    
                    # Verify post type is valid
                    assert post_type in ['status', 'photo', 'video', 'link']
                    
                    # Verify comments count is non-negative
                    assert comments_count >= 0
            
            # Verify that original data elements are preserved
            # Create a mapping of original posts by their unique characteristics
            original_posts_by_signature = {}
            for i, original_post in enumerate(facebook_posts_data):
                if not original_post.get('timestamp'):
                    continue  # Skip posts without timestamps
                
                # Create a signature for each original post
                original_timestamp = datetime.fromtimestamp(original_post['timestamp'])
                original_content = ""
                if original_post.get('data'):
                    for data_item in original_post['data']:
                        if isinstance(data_item, dict) and 'post' in data_item:
                            original_content = data_item['post']
                            break
                
                # Extract original media count
                original_media_count = 0
                if original_post.get('attachments'):
                    for attachment in original_post['attachments']:
                        if isinstance(attachment, dict) and 'data' in attachment:
                            for data_item in attachment['data']:
                                if isinstance(data_item, dict) and 'media' in data_item:
                                    original_media_count += 1
                
                # Extract original tagged people
                original_tagged = []
                if original_post.get('tags'):
                    for tag in original_post['tags']:
                        if isinstance(tag, dict) and 'name' in tag:
                            original_tagged.append(tag['name'])
                
                signature = (original_timestamp.isoformat(), original_content, original_media_count, len(original_tagged))
                original_posts_by_signature[signature] = original_post
            
            # Now verify each stored post matches an original post
            with sqlite3.connect(processor.db_path) as conn:
                cursor = conn.execute("""
                    SELECT content, timestamp, media_files, reactions, comments_count, location, tagged_people
                    FROM facebook_posts
                    ORDER BY timestamp
                """)
                
                stored_posts = cursor.fetchall()
                
                for stored_post in stored_posts:
                    stored_content, stored_timestamp, stored_media, stored_reactions, stored_comments, stored_location, stored_tags = stored_post
                    
                    # Parse stored data
                    stored_media_list = json.loads(stored_media) if stored_media else []
                    stored_tagged_list = json.loads(stored_tags) if stored_tags else []
                    
                    # Create signature for stored post
                    stored_signature = (stored_timestamp, stored_content, len(stored_media_list), len(stored_tagged_list))
                    
                    # Find matching original post
                    assert stored_signature in original_posts_by_signature, f"No original post found for stored post with signature {stored_signature}"
                    
                    original_post = original_posts_by_signature[stored_signature]
                    
                    # Verify detailed data preservation
                    original_reactions = original_post.get('reactions', {})
                    stored_reactions_dict = json.loads(stored_reactions) if stored_reactions else {}
                    assert stored_reactions_dict == original_reactions
                    
                    # Check comments count preservation
                    original_comments_count = len(original_post.get('comments', []))
                    assert stored_comments == original_comments_count
                    
                    # Check location preservation
                    original_location = None
                    if original_post.get('place') and isinstance(original_post['place'], dict):
                        original_location = original_post['place'].get('name')
                    assert stored_location == original_location


    @given(st.lists(
        st.one_of(
            # Valid posts with proper timestamps
            st.fixed_dictionaries({
                'timestamp': st.integers(min_value=946684800, max_value=2147483647),
                'data': st.lists(
                    st.fixed_dictionaries({
                        'post': st.text(min_size=0, max_size=100)
                    }),
                    min_size=0, max_size=2
                ),
                'attachments': st.lists(st.dictionaries(st.text(), st.just({})), min_size=0, max_size=1),
                'reactions': st.dictionaries(
                    st.sampled_from(['like', 'love', 'wow']),
                    st.integers(min_value=0, max_value=100),
                    min_size=0, max_size=3
                ),
                'comments': st.lists(st.dictionaries(st.text(), st.text()), min_size=0, max_size=3)
            }),
            # Invalid posts (missing timestamp)
            st.fixed_dictionaries({
                'data': st.lists(
                    st.fixed_dictionaries({
                        'post': st.text(min_size=0, max_size=100)
                    }),
                    min_size=0, max_size=2
                ),
                'attachments': st.lists(st.dictionaries(st.text(), st.just({})), min_size=0, max_size=1)
            }),
            # Invalid posts (bad timestamp)
            st.fixed_dictionaries({
                'timestamp': st.one_of(st.text(), st.none()),
                'data': st.lists(
                    st.fixed_dictionaries({
                        'post': st.text(min_size=0, max_size=100)
                    }),
                    min_size=0, max_size=2
                )
            })
        ),
        min_size=3, max_size=10
    ))
    @settings(max_examples=50, deadline=None)
    def test_error_handling_continuity(self, mixed_posts_data):
        """
        **Feature: facebook-posts-timeline, Property 15: Error handling continuity**
        For any Facebook export data containing both valid and invalid posts, the system should 
        process all valid posts while logging errors for invalid ones
        **Validates: Requirements 4.4**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup processor with temporary directory
            processor = FacebookProcessor(temp_dir)
            
            # Create Facebook export structure
            facebook_dir = Path(temp_dir) / "facebook"
            facebook_dir.mkdir(parents=True)
            
            # Create posts.json file with mixed valid/invalid data
            posts_data = {
                "posts_v2": mixed_posts_data
            }
            
            posts_file = facebook_dir / "posts.json"
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f)
            
            # Process the data
            result = processor.process_facebook_data()
            
            # Verify processing was successful overall
            assert isinstance(result, ProcessingResult)
            assert result.success == True
            assert result.total_posts == len(mixed_posts_data)
            
            # Count expected valid posts (those with valid integer timestamps in range)
            valid_posts_count = 0
            for post in mixed_posts_data:
                timestamp = post.get('timestamp')
                if (timestamp is not None and 
                    isinstance(timestamp, int) and 
                    946684800 <= timestamp <= 2147483647):
                    valid_posts_count += 1
            
            # Verify that all valid posts were processed and stored
            assert result.processed_posts == valid_posts_count
            assert result.stored_posts == result.processed_posts
            
            # Verify that invalid posts were skipped
            expected_skipped = len(mixed_posts_data) - valid_posts_count
            assert result.skipped_posts == expected_skipped
            
            # Verify that errors were logged for invalid posts if any exist
            if expected_skipped > 0:
                assert len(result.errors) > 0
            
            # Verify database contains only valid posts
            with sqlite3.connect(processor.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM facebook_posts")
                stored_count = cursor.fetchone()[0]
                assert stored_count == valid_posts_count
                
                # Verify all stored posts have valid data
                if stored_count > 0:
                    cursor = conn.execute("""
                        SELECT timestamp, post_type FROM facebook_posts
                    """)
                    
                    for row in cursor.fetchall():
                        timestamp_str, post_type = row
                        # Verify timestamp can be parsed
                        parsed_timestamp = datetime.fromisoformat(timestamp_str)
                        assert isinstance(parsed_timestamp, datetime)
                        # Verify post type is valid
                        assert post_type in ['status', 'photo', 'video', 'link']
            
            # Verify continuity: processing doesn't stop on errors
            # The total should equal processed + skipped
            assert result.total_posts == result.processed_posts + result.skipped_posts


    @given(st.lists(
        st.one_of(
            # Valid posts
            st.fixed_dictionaries({
                'timestamp': st.integers(min_value=946684800, max_value=2147483647),
                'data': st.lists(
                    st.fixed_dictionaries({
                        'post': st.text(min_size=0, max_size=100)
                    }),
                    min_size=0, max_size=2
                ),
                'attachments': st.lists(st.dictionaries(st.text(), st.just({})), min_size=0, max_size=1)
            }),
            # Invalid posts
            st.fixed_dictionaries({
                'data': st.lists(
                    st.fixed_dictionaries({
                        'post': st.text(min_size=0, max_size=100)
                    }),
                    min_size=0, max_size=2
                )
            })
        ),
        min_size=1, max_size=15
    ))
    @settings(max_examples=50, deadline=None)
    def test_processing_summary_accuracy(self, posts_data):
        """
        **Feature: facebook-posts-timeline, Property 16: Processing summary accuracy**
        For any completed Facebook data processing operation, the returned summary should 
        accurately reflect the number of posts processed and any errors encountered
        **Validates: Requirements 4.5**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup processor with temporary directory
            processor = FacebookProcessor(temp_dir)
            
            # Create Facebook export structure
            facebook_dir = Path(temp_dir) / "facebook"
            facebook_dir.mkdir(parents=True)
            
            # Create posts.json file with test data
            posts_json = {
                "posts_v2": posts_data
            }
            
            posts_file = facebook_dir / "posts.json"
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts_json, f)
            
            # Process the data
            result = processor.process_facebook_data()
            
            # Verify processing result structure
            assert isinstance(result, ProcessingResult)
            assert hasattr(result, 'success')
            assert hasattr(result, 'total_posts')
            assert hasattr(result, 'processed_posts')
            assert hasattr(result, 'stored_posts')
            assert hasattr(result, 'skipped_posts')
            assert hasattr(result, 'errors')
            
            # Verify total posts accuracy
            assert result.total_posts == len(posts_data)
            
            # Count expected valid and invalid posts
            valid_count = 0
            invalid_count = 0
            
            for post in posts_data:
                timestamp = post.get('timestamp')
                if (timestamp is not None and 
                    isinstance(timestamp, int) and 
                    946684800 <= timestamp <= 2147483647):
                    valid_count += 1
                else:
                    invalid_count += 1
            
            # Verify processed posts accuracy
            assert result.processed_posts == valid_count
            
            # Verify skipped posts accuracy
            assert result.skipped_posts == invalid_count
            
            # Verify stored posts accuracy (should equal processed)
            assert result.stored_posts == result.processed_posts
            
            # Verify total consistency
            assert result.total_posts == result.processed_posts + result.skipped_posts
            
            # Verify error reporting accuracy
            if invalid_count > 0:
                # Should have errors for invalid posts
                assert len(result.errors) > 0
                assert result.success == True  # Still successful overall
            else:
                # No invalid posts, should have no errors
                assert len(result.errors) == 0
                assert result.success == True
            
            # Verify database consistency with summary
            with sqlite3.connect(processor.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM facebook_posts")
                db_count = cursor.fetchone()[0]
                assert db_count == result.stored_posts
                assert db_count == result.processed_posts
            
            # Verify success flag accuracy
            assert result.success == True  # Processing should succeed even with some invalid posts


    @given(st.lists(
        st.fixed_dictionaries({
            'timestamp': st.integers(min_value=946684800, max_value=2147483647),  # 2000-2038 range
            'data': st.lists(
                st.fixed_dictionaries({
                    'post': st.text(min_size=0, max_size=300)
                }),
                min_size=0, max_size=2
            ),
            'attachments': st.lists(
                st.fixed_dictionaries({
                    'data': st.lists(
                        st.fixed_dictionaries({
                            'media': st.fixed_dictionaries({
                                'uri': st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc')))
                            })
                        }),
                        min_size=0, max_size=3
                    )
                }),
                min_size=0, max_size=2
            ),
            'reactions': st.dictionaries(
                st.sampled_from(['like', 'love', 'wow', 'haha', 'sad', 'angry']),
                st.integers(min_value=0, max_value=500),
                min_size=0, max_size=6
            ),
            'comments': st.lists(
                st.fixed_dictionaries({
                    'comment': st.text(min_size=0, max_size=150)
                }),
                min_size=0, max_size=8
            ),
            'place': st.one_of(
                st.none(),
                st.fixed_dictionaries({
                    'name': st.text(min_size=1, max_size=80)
                })
            ),
            'tags': st.lists(
                st.fixed_dictionaries({
                    'name': st.text(min_size=1, max_size=40)
                }),
                min_size=0, max_size=4
            )
        }),
        min_size=1, max_size=30
    ))
    @settings(max_examples=100, deadline=None)
    def test_database_storage_integrity(self, facebook_posts_data):
        """
        **Feature: facebook-posts-timeline, Property 14: Database storage integrity**
        For any processed Facebook posts, the data should be stored in the database with 
        indexed timestamps and be retrievable through efficient queries
        **Validates: Requirements 4.3**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup processor with temporary directory
            processor = FacebookProcessor(temp_dir)
            
            # Create Facebook export structure
            facebook_dir = Path(temp_dir) / "facebook"
            facebook_dir.mkdir(parents=True)
            
            # Create posts.json file with generated data
            posts_data = {
                "posts_v2": facebook_posts_data
            }
            
            posts_file = facebook_dir / "posts.json"
            with open(posts_file, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f)
            
            # Process the data
            result = processor.process_facebook_data()
            
            # Verify processing was successful
            assert isinstance(result, ProcessingResult)
            assert result.success == True
            assert result.processed_posts > 0
            assert result.stored_posts == result.processed_posts
            
            # Verify database schema and indexes exist
            with sqlite3.connect(processor.db_path) as conn:
                # Check that facebook_posts table exists with correct schema
                cursor = conn.execute("""
                    SELECT sql FROM sqlite_master 
                    WHERE type='table' AND name='facebook_posts'
                """)
                table_schema = cursor.fetchone()
                assert table_schema is not None
                schema_sql = table_schema[0].lower()
                
                # Verify required columns exist in schema
                required_columns = [
                    'id', 'content', 'timestamp', 'post_type', 'media_files',
                    'reactions', 'comments_count', 'location', 'tagged_people', 'created_at'
                ]
                for column in required_columns:
                    assert column in schema_sql, f"Required column '{column}' missing from schema"
                
                # Verify indexes exist as specified in design document
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND tbl_name='facebook_posts'
                """)
                indexes = [row[0] for row in cursor.fetchall()]
                
                # Check for required indexes
                required_indexes = ['idx_facebook_posts_timestamp', 'idx_facebook_posts_type']
                for index_name in required_indexes:
                    assert index_name in indexes, f"Required index '{index_name}' missing"
                
                # Verify all processed posts are stored with correct data types
                cursor = conn.execute("""
                    SELECT id, content, timestamp, post_type, media_files, reactions, 
                           comments_count, location, tagged_people, created_at
                    FROM facebook_posts
                    ORDER BY timestamp
                """)
                
                stored_posts = cursor.fetchall()
                assert len(stored_posts) == result.stored_posts
                
                # Verify data integrity for each stored post
                for stored_post in stored_posts:
                    post_id, content, timestamp, post_type, media_files, reactions, comments_count, location, tagged_people, created_at = stored_post
                    
                    # Verify primary key constraint
                    assert post_id is not None and len(post_id) > 0
                    
                    # Verify timestamp is stored correctly and can be parsed
                    assert timestamp is not None
                    parsed_timestamp = datetime.fromisoformat(timestamp)
                    assert isinstance(parsed_timestamp, datetime)
                    
                    # Verify post_type is valid
                    assert post_type in ['status', 'photo', 'video', 'link']
                    
                    # Verify JSON fields are properly serialized and can be deserialized
                    if media_files:
                        parsed_media = json.loads(media_files)
                        assert isinstance(parsed_media, list)
                    
                    if reactions:
                        parsed_reactions = json.loads(reactions)
                        assert isinstance(parsed_reactions, dict)
                    
                    if tagged_people:
                        parsed_tags = json.loads(tagged_people)
                        assert isinstance(parsed_tags, list)
                    
                    # Verify integer constraints
                    assert isinstance(comments_count, int) and comments_count >= 0
                    
                    # Verify created_at timestamp exists and is valid
                    assert created_at is not None
                    parsed_created_at = datetime.fromisoformat(created_at)
                    assert isinstance(parsed_created_at, datetime)
                
                # Test efficient querying using indexes
                # Query by timestamp range (should use idx_facebook_posts_timestamp)
                min_timestamp = min(datetime.fromtimestamp(post['timestamp']) for post in facebook_posts_data)
                max_timestamp = max(datetime.fromtimestamp(post['timestamp']) for post in facebook_posts_data)
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM facebook_posts 
                    WHERE timestamp BETWEEN ? AND ?
                """, (min_timestamp.isoformat(), max_timestamp.isoformat()))
                
                range_count = cursor.fetchone()[0]
                assert range_count == result.stored_posts
                
                # Query by post_type (should use idx_facebook_posts_type)
                cursor = conn.execute("""
                    SELECT DISTINCT post_type FROM facebook_posts
                """)
                post_types = [row[0] for row in cursor.fetchall()]
                assert all(pt in ['status', 'photo', 'video', 'link'] for pt in post_types)
                
                # Test retrieval efficiency by querying specific dates
                cursor = conn.execute("""
                    SELECT date(timestamp) as date, COUNT(*) as count
                    FROM facebook_posts 
                    GROUP BY date(timestamp)
                    ORDER BY date
                """)
                
                date_groups = cursor.fetchall()
                total_from_groups = sum(count for date, count in date_groups)
                assert total_from_groups == result.stored_posts
                
                # Verify no data corruption during storage/retrieval round trip
                # Get all posts and verify they can be reconstructed as FacebookPost objects
                cursor = conn.execute("""
                    SELECT id, content, timestamp, post_type, media_files, reactions, 
                           comments_count, location, tagged_people
                    FROM facebook_posts
                """)
                
                for row in cursor.fetchall():
                    post_id, content, timestamp, post_type, media_files, reactions, comments_count, location, tagged_people = row
                    
                    # Reconstruct FacebookPost object to verify data integrity
                    reconstructed_post = FacebookPost(
                        id=post_id,
                        content=content,
                        timestamp=datetime.fromisoformat(timestamp),
                        post_type=post_type,
                        media_files=json.loads(media_files) if media_files else [],
                        reactions=json.loads(reactions) if reactions else {},
                        comments_count=comments_count,
                        location=location,
                        tagged_people=json.loads(tagged_people) if tagged_people else []
                    )
                    
                    # Verify reconstructed object has valid data
                    assert isinstance(reconstructed_post.id, str) and len(reconstructed_post.id) > 0
                    assert isinstance(reconstructed_post.content, str)
                    assert isinstance(reconstructed_post.timestamp, datetime)
                    assert reconstructed_post.post_type in ['status', 'photo', 'video', 'link']
                    assert isinstance(reconstructed_post.media_files, list)
                    assert isinstance(reconstructed_post.reactions, dict)
                    assert isinstance(reconstructed_post.comments_count, int) and reconstructed_post.comments_count >= 0
                    assert reconstructed_post.location is None or isinstance(reconstructed_post.location, str)
                    assert isinstance(reconstructed_post.tagged_people, list)
                
                # Test that database supports concurrent access (basic check)
                # This verifies the database file is properly created and accessible
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                assert integrity_result == "ok", f"Database integrity check failed: {integrity_result}"
                
                # Verify foreign key constraints are properly handled (if any)
                cursor = conn.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                assert len(fk_violations) == 0, f"Foreign key violations found: {fk_violations}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])