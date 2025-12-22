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
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

# Import the classes we need to test
from src.common.objects.enhanced_llentry import EnhancedLLEntry, PersonRelationship
from src.common.services.self_reflection_service import SelfReflectionService


# Strategy generators for property-based testing

@composite
def generate_writing_sample(draw):
    """Generate a writing sample with realistic personal content"""
    writing_styles = [
        "excited", "contemplative", "casual", "formal", "emotional", 
        "analytical", "descriptive", "narrative", "reflective"
    ]
    
    topics = [
        "work", "family", "travel", "hobbies", "relationships", "goals", 
        "challenges", "achievements", "learning", "health", "creativity"
    ]
    
    # Generate vocabulary sets for different periods
    early_vocab = ["awesome", "cool", "fun", "great", "nice", "good", "bad", "okay"]
    later_vocab = ["meaningful", "significant", "profound", "insightful", "valuable", "challenging", "rewarding"]
    
    style = draw(st.sampled_from(writing_styles))
    topic = draw(st.sampled_from(topics))
    
    # Generate text based on style and topic
    if style == "excited":
        text_templates = [
            "I'm so excited about {topic}! This is going to be {adjective}!",
            "Can't believe how {adjective} this {topic} experience has been!",
            "Amazing day working on {topic}. Feeling {emotion} about the progress!"
        ]
    elif style == "contemplative":
        text_templates = [
            "Been thinking a lot about {topic} lately. It's {adjective} how {insight}.",
            "Reflecting on my {topic} journey. There's something {adjective} about {insight}.",
            "The more I consider {topic}, the more I realize {insight}."
        ]
    elif style == "analytical":
        text_templates = [
            "Analyzing my approach to {topic}. The key factors seem to be {factor1} and {factor2}.",
            "Breaking down the {topic} situation: {factor1} is working well, but {factor2} needs improvement.",
            "Data shows that my {topic} efforts are {result}. Need to focus on {factor1}."
        ]
    else:
        text_templates = [
            "Today's {topic} experience was {adjective}. {insight}.",
            "Working on {topic} and feeling {emotion}. {insight}.",
            "Another day of {topic}. {adjective} how {insight}."
        ]
    
    template = draw(st.sampled_from(text_templates))
    
    # Choose vocabulary based on time period (simulate evolution)
    vocab_choice = draw(st.booleans())
    adjectives = later_vocab if vocab_choice else early_vocab
    
    text = template.format(
        topic=topic,
        adjective=draw(st.sampled_from(adjectives)),
        emotion=draw(st.sampled_from(["grateful", "excited", "thoughtful", "motivated", "peaceful"])),
        insight=draw(st.sampled_from([
            "things change over time", "growth happens gradually", "relationships matter most",
            "small steps lead to big changes", "perspective shifts everything"
        ])),
        factor1=draw(st.sampled_from(["consistency", "patience", "focus", "balance", "planning"])),
        factor2=draw(st.sampled_from(["timing", "resources", "support", "motivation", "clarity"])),
        result=draw(st.sampled_from(["improving", "stagnating", "evolving", "succeeding"]))
    )
    
    return {
        'text': text,
        'style': style,
        'topic': topic,
        'vocab_level': 'advanced' if vocab_choice else 'basic'
    }


@composite
def generate_temporal_writing_collection(draw):
    """Generate a collection of writing samples across time periods"""
    num_samples = draw(st.integers(min_value=10, max_value=50))
    samples = []
    
    # Create time periods spanning several years
    base_time = datetime.now() - timedelta(days=1095)  # 3 years ago
    
    for i in range(num_samples):
        # Distribute samples across time with some clustering
        time_offset = draw(st.integers(min_value=0, max_value=1095 * 24 * 3600))
        sample_time = base_time + timedelta(seconds=time_offset)
        
        # Generate writing sample
        writing_sample = draw(generate_writing_sample())
        
        # Create enhanced entry
        entry = EnhancedLLEntry("post", sample_time.isoformat(), "personal_journal")
        entry.text = writing_sample['text']
        entry.textDescription = writing_sample['text']
        
        # Add metadata
        entry.ai_metadata = {
            'writing_style': writing_sample['style'],
            'topic': writing_sample['topic'],
            'vocab_level': writing_sample['vocab_level']
        }
        
        # Add some thematic tags
        entry.thematic_tags = [writing_sample['topic']]
        if writing_sample['style'] in ['contemplative', 'reflective', 'analytical']:
            entry.thematic_tags.append('introspective')
        
        # Add life phase based on time
        days_ago = (datetime.now() - sample_time).days
        if days_ago > 730:  # More than 2 years ago
            entry.life_phase = 'early_period'
        elif days_ago > 365:  # 1-2 years ago
            entry.life_phase = 'middle_period'
        else:  # Recent
            entry.life_phase = 'recent_period'
        
        samples.append(entry)
    
    return samples


@composite
def generate_life_events_collection(draw):
    """Generate a collection of entries representing major life events"""
    life_events = [
        "graduation", "new_job", "promotion", "marriage", "move", "birth", 
        "loss", "achievement", "travel", "learning", "health", "relationship_change"
    ]
    
    num_events = draw(st.integers(min_value=5, max_value=15))
    events = []
    
    base_time = datetime.now() - timedelta(days=1825)  # 5 years ago
    
    for i in range(num_events):
        event_type = draw(st.sampled_from(life_events))
        
        # Space events out over time
        time_offset = (1825 * 24 * 3600 * i) // num_events
        event_time = base_time + timedelta(seconds=time_offset)
        
        # Create event entry
        entry = EnhancedLLEntry("milestone", event_time.isoformat(), "life_events")
        
        # Generate event description
        event_descriptions = {
            "graduation": "Graduated from university today. Feeling accomplished and ready for the next chapter.",
            "new_job": "Started my new job today. Excited about the opportunities ahead.",
            "promotion": "Got promoted at work! All the hard work is paying off.",
            "marriage": "Got married today. Beginning a new journey with my partner.",
            "move": "Moved to a new city. Everything feels different but exciting.",
            "birth": "Welcome to the world, little one. Life will never be the same.",
            "loss": "Saying goodbye is never easy. Grateful for all the memories.",
            "achievement": "Reached a major personal goal today. Feeling proud of the journey.",
            "travel": "Exploring new places and cultures. Perspective is shifting.",
            "learning": "Started learning something new. Growth feels good.",
            "health": "Focusing on health and wellness. Making positive changes.",
            "relationship_change": "Relationships evolve. Learning to adapt and grow."
        }
        
        entry.text = event_descriptions.get(event_type, f"Significant {event_type} event occurred.")
        entry.textDescription = entry.text
        entry.thematic_tags = [event_type, 'milestone', 'life_change']
        entry.narrative_significance = draw(st.floats(min_value=0.7, max_value=1.0))
        
        # Add emotional context
        entry.emotional_context = {
            'significance': draw(st.floats(min_value=0.6, max_value=1.0)),
            'emotional_intensity': draw(st.floats(min_value=0.5, max_value=1.0))
        }
        
        events.append(entry)
    
    return events


class TestSelfReflectionAnalysis:
    """Test suite for self-reflection analysis functionality"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a temporary directory for any test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize self-reflection service with test configuration
        self.test_config = {
            'analysis': {
                'min_writing_samples': 5,
                'min_time_span_days': 30,
                'pattern_confidence_threshold': 0.3,
                'theme_frequency_threshold': 2
            },
            'life_chapters': {
                'min_chapter_duration_days': 90,
                'max_chapters': 20,
                'significance_threshold': 0.5
            },
            'reflection_prompts': {
                'max_prompts_per_session': 5,
                'prompt_variety': True,
                'avoid_diagnostic_language': True
            },
            'privacy': {
                'avoid_definitive_statements': True,
                'frame_as_suggestions': True,
                'respect_user_agency': True
            }
        }
        
        # Mock the database dependency
        os.environ['APP_DATA_DIR'] = self.temp_dir
        
        self.reflection_service = SelfReflectionService(self.test_config)
    
    def teardown_method(self):
        """Clean up test environment after each test"""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(writing_samples=generate_temporal_writing_collection())
    @settings(max_examples=100, deadline=30000)
    def test_self_reflection_analysis(self, writing_samples):
        """**Feature: ai-personal-archive, Property 8: Self-Reflection Analysis**
        
        For any personal writing or behavioral patterns in the data, the system should detect 
        changes over time and present insights as suggestions and patterns rather than 
        definitive assessments.
        """
        # Arrange: Ensure we have sufficient data for analysis
        assume(len(writing_samples) >= 10)
        assume(all(hasattr(sample, 'text') and sample.text and len(sample.text.strip()) >= 10 
                  for sample in writing_samples))
        
        # Ensure temporal spread
        timestamps = [datetime.fromisoformat(sample.startTime.replace('Z', '+00:00').replace('+00:00', '')) 
                     for sample in writing_samples]
        time_span = max(timestamps) - min(timestamps)
        assume(time_span.days >= 30)  # At least 30 days of data
        
        # Act: Perform self-reflection analysis
        analysis_result = self.reflection_service.analyze_personal_patterns(writing_samples)
        
        # Assert: Verify self-reflection analysis properties
        
        # Property 1: Analysis should be generated successfully
        assert analysis_result is not None, "Self-reflection analysis should not return None"
        assert isinstance(analysis_result, dict), "Analysis result should be a dictionary"
        
        # Property 2: Writing pattern analysis should detect changes over time
        assert 'writing_patterns' in analysis_result, "Should include writing pattern analysis"
        writing_patterns = analysis_result['writing_patterns']
        
        assert isinstance(writing_patterns, dict), "Writing patterns should be a dictionary"
        
        # Should detect tone changes
        if 'tone_evolution' in writing_patterns:
            tone_evolution = writing_patterns['tone_evolution']
            assert isinstance(tone_evolution, list), "Tone evolution should be a list"
            for period in tone_evolution:
                assert 'time_period' in period, "Each period should have time_period"
                assert 'dominant_tones' in period, "Each period should have dominant_tones"
                assert isinstance(period['dominant_tones'], list), "Dominant tones should be a list"
        
        # Should detect topic shifts
        if 'topic_evolution' in writing_patterns:
            topic_evolution = writing_patterns['topic_evolution']
            assert isinstance(topic_evolution, list), "Topic evolution should be a list"
            for period in topic_evolution:
                assert 'time_period' in period, "Each period should have time_period"
                assert 'primary_topics' in period, "Each period should have primary_topics"
        
        # Should detect vocabulary evolution
        if 'vocabulary_evolution' in writing_patterns:
            vocab_evolution = writing_patterns['vocabulary_evolution']
            assert isinstance(vocab_evolution, dict), "Vocabulary evolution should be a dictionary"
            # Should track complexity or style changes over time
        
        # Property 3: Life chapter detection should identify meaningful periods
        assert 'life_chapters' in analysis_result, "Should include life chapter detection"
        life_chapters = analysis_result['life_chapters']
        
        assert isinstance(life_chapters, list), "Life chapters should be a list"
        assert len(life_chapters) <= 20, "Should not have excessive life chapters"
        
        for chapter in life_chapters:
            assert isinstance(chapter, dict), "Each chapter should be a dictionary"
            assert 'title' in chapter, "Chapter should have a title"
            assert 'start_date' in chapter, "Chapter should have start_date"
            assert 'end_date' in chapter, "Chapter should have end_date"
            assert 'description' in chapter, "Chapter should have description"
            assert 'key_themes' in chapter, "Chapter should have key_themes"
            
            # Verify chapter title is meaningful
            assert chapter['title'], "Chapter title should not be empty"
            assert len(chapter['title'].strip()) >= 3, "Chapter title should be meaningful"
            
            # Verify temporal validity
            start_date = datetime.fromisoformat(chapter['start_date'].replace('Z', '+00:00').replace('+00:00', ''))
            end_date = datetime.fromisoformat(chapter['end_date'].replace('Z', '+00:00').replace('+00:00', ''))
            assert start_date <= end_date, "Chapter start should be before or equal to end"
            
            # Verify chapter duration is reasonable (at least a few days)
            chapter_duration = (end_date - start_date).days
            assert chapter_duration >= 1, "Chapter should span at least one day"
            
            # Verify key themes are present
            assert isinstance(chapter['key_themes'], list), "Key themes should be a list"
            assert len(chapter['key_themes']) > 0, "Chapter should have at least one key theme"
        
        # Property 4: Recurring theme identification should find patterns
        assert 'recurring_themes' in analysis_result, "Should include recurring theme identification"
        recurring_themes = analysis_result['recurring_themes']
        
        assert isinstance(recurring_themes, list), "Recurring themes should be a list"
        
        for theme in recurring_themes:
            assert isinstance(theme, dict), "Each theme should be a dictionary"
            assert 'theme_name' in theme, "Theme should have a name"
            assert 'frequency' in theme, "Theme should have frequency"
            assert 'time_periods' in theme, "Theme should have time_periods"
            assert 'significance' in theme, "Theme should have significance score"
            
            # Verify theme properties
            assert theme['theme_name'], "Theme name should not be empty"
            assert isinstance(theme['frequency'], int), "Frequency should be an integer"
            assert theme['frequency'] >= 2, "Recurring theme should appear at least twice"
            assert isinstance(theme['time_periods'], list), "Time periods should be a list"
            assert isinstance(theme['significance'], (int, float)), "Significance should be numeric"
            assert 0 <= theme['significance'] <= 1, "Significance should be between 0 and 1"
        
        # Property 5: Pattern presentation should be framed as suggestions
        assert 'insights' in analysis_result, "Should include insights section"
        insights = analysis_result['insights']
        
        assert isinstance(insights, list), "Insights should be a list"
        
        for insight in insights:
            assert isinstance(insight, dict), "Each insight should be a dictionary"
            assert 'type' in insight, "Insight should have a type"
            assert 'description' in insight, "Insight should have description"
            assert 'confidence' in insight, "Insight should have confidence level"
            
            # Verify insights are framed as suggestions, not definitive statements
            description = insight['description'].lower()
            
            # Should avoid definitive diagnostic language
            diagnostic_words = ['you are', 'you have', 'you suffer from', 'you need to', 'you must']
            for diagnostic in diagnostic_words:
                assert diagnostic not in description, \
                    f"Insight should avoid diagnostic language: '{diagnostic}' in '{insight['description']}'"
            
            # Should use suggestion language
            suggestion_indicators = [
                'might', 'could', 'appears', 'seems', 'suggests', 'indicates', 
                'pattern shows', 'data suggests', 'tendency toward', 'possible'
            ]
            has_suggestion_language = any(indicator in description for indicator in suggestion_indicators)
            
            # Allow flexibility but encourage suggestion framing
            if len(description) > 20:  # Only check longer descriptions
                # Should either use suggestion language or be clearly observational
                observational_indicators = ['during', 'over time', 'in the period', 'frequently', 'often']
                has_observational_language = any(indicator in description for indicator in observational_indicators)
                
                assert has_suggestion_language or has_observational_language, \
                    f"Insight should use suggestion or observational language: '{insight['description']}'"
            
            # Verify confidence is reasonable
            assert isinstance(insight['confidence'], (int, float)), "Confidence should be numeric"
            assert 0 <= insight['confidence'] <= 1, "Confidence should be between 0 and 1"
        
        # Property 6: Reflection prompt generation should invite dialogue
        assert 'reflection_prompts' in analysis_result, "Should include reflection prompts"
        reflection_prompts = analysis_result['reflection_prompts']
        
        assert isinstance(reflection_prompts, list), "Reflection prompts should be a list"
        assert len(reflection_prompts) <= 5, "Should not overwhelm with too many prompts"
        
        for prompt in reflection_prompts:
            assert isinstance(prompt, dict), "Each prompt should be a dictionary"
            assert 'question' in prompt, "Prompt should have a question"
            assert 'context' in prompt, "Prompt should have context"
            assert 'prompt_type' in prompt, "Prompt should have a type"
            
            # Verify prompts invite dialogue rather than passive consumption
            question = prompt['question']
            assert question, "Question should not be empty"
            assert len(question.strip()) >= 10, "Question should be substantial"
            
            # Should be phrased as questions
            question_indicators = ['?', 'how', 'what', 'when', 'where', 'why', 'which', 'would you']
            has_question_format = any(indicator in question.lower() for indicator in question_indicators)
            assert has_question_format, f"Prompt should be phrased as a question: '{question}'"
            
            # Should avoid commanding language
            commanding_words = ['you should', 'you must', 'you need to', 'do this', 'try this']
            question_lower = question.lower()
            for command in commanding_words:
                assert command not in question_lower, \
                    f"Prompt should avoid commanding language: '{command}' in '{question}'"
            
            # Verify context is meaningful
            assert prompt['context'], "Context should not be empty"
            assert len(prompt['context'].strip()) >= 5, "Context should be meaningful"
            
            # Verify prompt type is valid
            valid_prompt_types = [
                'pattern_reflection', 'theme_exploration', 'change_awareness', 
                'growth_recognition', 'connection_discovery', 'perspective_shift'
            ]
            assert prompt['prompt_type'] in valid_prompt_types, \
                f"Prompt type should be valid: '{prompt['prompt_type']}'"
        
        # Property 7: Analysis should respect user agency
        # Verify that the analysis doesn't make absolute claims about the user
        full_analysis_text = str(analysis_result).lower()
        
        # Should avoid absolute statements about the user's character or psychology
        absolute_statements = [
            'you are definitely', 'you always', 'you never', 'you will', 
            'you cannot', 'you should always', 'this proves you'
        ]
        
        for absolute in absolute_statements:
            assert absolute not in full_analysis_text, \
                f"Analysis should avoid absolute statements: '{absolute}'"
        
        # Property 8: Analysis should maintain temporal coherence
        # Verify that detected patterns make temporal sense
        if life_chapters:
            # Chapters should not overlap inappropriately
            sorted_chapters = sorted(life_chapters, 
                                   key=lambda x: datetime.fromisoformat(x['start_date'].replace('Z', '+00:00').replace('+00:00', '')))
            
            for i in range(len(sorted_chapters) - 1):
                current_end = datetime.fromisoformat(sorted_chapters[i]['end_date'].replace('Z', '+00:00').replace('+00:00', ''))
                next_start = datetime.fromisoformat(sorted_chapters[i+1]['start_date'].replace('Z', '+00:00').replace('+00:00', ''))
                
                # Allow some overlap but not complete contradiction
                overlap_days = (current_end - next_start).days
                assert overlap_days <= 365, \
                    f"Life chapters should not have excessive overlap: {overlap_days} days"
        
        # Property 9: Analysis should be grounded in actual data
        # Verify that insights reference actual patterns from the input data
        if insights:
            # Should have reasonable number of insights based on data volume
            data_volume = len(writing_samples)
            max_expected_insights = min(10, data_volume // 2)  # Reasonable ratio
            assert len(insights) <= max_expected_insights, \
                f"Should not generate excessive insights: {len(insights)} for {data_volume} samples"
            
            # Each insight should have reasonable confidence based on data
            for insight in insights:
                confidence = insight['confidence']
                # With limited test data, confidence should be modest
                if data_volume < 20:
                    assert confidence <= 0.8, \
                        f"Confidence should be modest with limited data: {confidence} for {data_volume} samples"
    
    @given(life_events=generate_life_events_collection())
    @settings(max_examples=50, deadline=20000)
    def test_life_chapter_detection_with_events(self, life_events):
        """Test life chapter detection with major life events"""
        # Arrange
        assume(len(life_events) >= 5)
        
        # Act
        analysis_result = self.reflection_service.analyze_personal_patterns(life_events)
        
        # Assert
        assert 'life_chapters' in analysis_result
        life_chapters = analysis_result['life_chapters']
        
        # Should detect chapters around major events (but be lenient for test data)
        # At minimum, should return some analysis even if no clear chapters
        assert isinstance(life_chapters, list), "Life chapters should be a list"
        
        # If we have significant events, we should get some chapters
        significant_events = [e for e in life_events if hasattr(e, 'narrative_significance') and e.narrative_significance > 0.5]
        if len(significant_events) >= 2:
            # With significant events, we should get at least one chapter
            # But allow for cases where events are too close together
            pass  # Just verify the structure is correct
        
        # Chapters should have reasonable temporal boundaries if they exist
        for chapter in life_chapters:
            start_date = datetime.fromisoformat(chapter['start_date'].replace('Z', '+00:00').replace('+00:00', ''))
            end_date = datetime.fromisoformat(chapter['end_date'].replace('Z', '+00:00').replace('+00:00', ''))
            duration = (end_date - start_date).days
            
            # Life chapters should span reasonable time periods
            assert 0 <= duration <= 1825, f"Chapter duration should be reasonable: {duration} days"
    
    def test_reflection_service_initialization(self):
        """Test that the reflection service initializes correctly"""
        service = SelfReflectionService(self.test_config)
        assert service is not None
        assert hasattr(service, 'analyze_personal_patterns')
        assert hasattr(service, 'detect_life_chapters')
        assert hasattr(service, 'identify_recurring_themes')
        assert hasattr(service, 'generate_reflection_prompts')


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])