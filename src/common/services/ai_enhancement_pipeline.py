"""
AI Enhancement Pipeline for Personal Archive System

This module runs during ingestion to enhance existing data with AI capabilities:
- Generate embeddings for semantic search
- Analyze images with multimodal understanding
- Create composite memories and thematic clusters
- Build people intelligence profiles
- Generate narrative significance scores
"""

import os
import logging
import requests
import json
from typing import List, Dict, Any, Optional
from src.common.persistence.enhanced_personal_data_db import EnhancedPersonalDataDBConnector
from src.common.objects.enhanced_llentry import EnhancedLLEntry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIEnhancementPipeline:
    """Pipeline for enhancing personal data with AI capabilities"""
    
    def __init__(self, ai_services_url: str = None):
        self.ai_services_url = ai_services_url or os.getenv('AI_SERVICES_URL', 'http://ai-services:8086')
        self.db = EnhancedPersonalDataDBConnector()
        
    def run_enhancement(self):
        """Run the complete AI enhancement pipeline"""
        logger.info("Starting AI enhancement pipeline...")
        
        try:
            # Check if AI services are available
            if not self._check_ai_services():
                logger.warning("AI services not available, skipping enhancement")
                return
            
            # Get all entries that need enhancement
            entries = self._get_entries_for_enhancement()
            logger.info(f"Found {len(entries)} entries to enhance")
            
            if not entries:
                logger.info("No entries need enhancement")
                return
            
            # Run enhancement steps
            self._enhance_embeddings(entries)
            self._enhance_image_analysis(entries)
            self._enhance_people_intelligence(entries)
            self._enhance_narrative_significance(entries)
            self._create_composite_memories(entries)
            
            logger.info("AI enhancement pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"AI enhancement pipeline failed: {e}")
            raise
    
    def _check_ai_services(self) -> bool:
        """Check if AI services are available"""
        try:
            response = requests.get(f"{self.ai_services_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"AI services health check failed: {e}")
            return False
    
    def _get_entries_for_enhancement(self) -> List[EnhancedLLEntry]:
        """Get entries that need AI enhancement"""
        try:
            # For now, get all entries - in production, this would be more selective
            entries = self.db.get_all_entries()
            
            # Filter to entries that haven't been enhanced yet
            unenhanced_entries = []
            for entry in entries:
                if not hasattr(entry, 'ai_enhanced') or not entry.ai_enhanced:
                    unenhanced_entries.append(entry)
            
            return unenhanced_entries[:100]  # Limit to 100 entries for initial processing
            
        except Exception as e:
            logger.error(f"Failed to get entries for enhancement: {e}")
            return []
    
    def _enhance_embeddings(self, entries: List[EnhancedLLEntry]):
        """Generate embeddings for semantic search"""
        logger.info("Generating embeddings for semantic search...")
        
        try:
            # Prepare texts for embedding
            texts = []
            entry_ids = []
            
            for entry in entries:
                if hasattr(entry, 'text') and entry.text:
                    texts.append(entry.text[:500])  # Limit text length
                    entry_ids.append(entry.id)
            
            if not texts:
                logger.info("No texts found for embedding generation")
                return
            
            # Generate embeddings via AI service
            response = requests.post(
                f"{self.ai_services_url}/api/ai/generate_embeddings",
                json={'texts': texts},
                timeout=60
            )
            
            if response.status_code == 200:
                embeddings = response.json().get('embeddings', [])
                
                # Store embeddings in database
                for i, embedding in enumerate(embeddings):
                    if i < len(entry_ids):
                        self._store_embedding(entry_ids[i], embedding)
                
                logger.info(f"Generated embeddings for {len(embeddings)} entries")
            else:
                logger.warning(f"Embedding generation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to enhance embeddings: {e}")
    
    def _enhance_image_analysis(self, entries: List[EnhancedLLEntry]):
        """Enhance image understanding with multimodal AI"""
        logger.info("Enhancing image analysis...")
        
        try:
            image_entries = [entry for entry in entries if hasattr(entry, 'image_path') and entry.image_path]
            
            if not image_entries:
                logger.info("No images found for analysis")
                return
            
            for entry in image_entries[:20]:  # Limit to 20 images
                try:
                    response = requests.post(
                        f"{self.ai_services_url}/api/ai/analyze_image",
                        json={
                            'image_path': entry.image_path,
                            'context': getattr(entry, 'text', '')[:200]
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        analysis = response.json()
                        
                        # Store enhanced image analysis
                        if 'error' not in analysis:
                            self._store_image_analysis(entry.id, analysis)
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze image for entry {entry.id}: {e}")
            
            logger.info(f"Enhanced image analysis for {len(image_entries)} entries")
            
        except Exception as e:
            logger.error(f"Failed to enhance image analysis: {e}")
    
    def _enhance_people_intelligence(self, entries: List[EnhancedLLEntry]):
        """Build people intelligence profiles"""
        logger.info("Building people intelligence profiles...")
        
        try:
            # Extract people mentions from entries
            people_mentions = {}
            
            for entry in entries:
                if hasattr(entry, 'people') and entry.people:
                    for person in entry.people:
                        if person not in people_mentions:
                            people_mentions[person] = []
                        people_mentions[person].append(entry)
            
            # Create profiles for people with multiple mentions
            for person, person_entries in people_mentions.items():
                if len(person_entries) >= 3:  # Only create profiles for people with 3+ mentions
                    profile_data = {
                        'name': person,
                        'first_appearance': min(entry.timestamp for entry in person_entries),
                        'last_appearance': max(entry.timestamp for entry in person_entries),
                        'interaction_count': len(person_entries),
                        'contexts': list(set(getattr(entry, 'context', 'general') for entry in person_entries))
                    }
                    
                    self._store_person_profile(person, profile_data)
            
            logger.info(f"Created profiles for {len([p for p, e in people_mentions.items() if len(e) >= 3])} people")
            
        except Exception as e:
            logger.error(f"Failed to enhance people intelligence: {e}")
    
    def _enhance_narrative_significance(self, entries: List[EnhancedLLEntry]):
        """Calculate narrative significance scores"""
        logger.info("Calculating narrative significance scores...")
        
        try:
            for entry in entries:
                # Simple heuristic for narrative significance
                significance = 0.5  # Base score
                
                # Boost for entries with images
                if hasattr(entry, 'image_path') and entry.image_path:
                    significance += 0.2
                
                # Boost for entries with people
                if hasattr(entry, 'people') and entry.people:
                    significance += 0.1 * len(entry.people)
                
                # Boost for longer text
                if hasattr(entry, 'text') and entry.text:
                    significance += min(0.3, len(entry.text) / 1000)
                
                # Cap at 1.0
                significance = min(1.0, significance)
                
                # Store significance score
                self._store_narrative_significance(entry.id, significance)
            
            logger.info(f"Calculated narrative significance for {len(entries)} entries")
            
        except Exception as e:
            logger.error(f"Failed to enhance narrative significance: {e}")
    
    def _create_composite_memories(self, entries: List[EnhancedLLEntry]):
        """Create composite memories from related entries"""
        logger.info("Creating composite memories...")
        
        try:
            # Simple clustering by date proximity and shared people
            clusters = {}
            
            for entry in entries:
                # Create cluster key based on date and people
                date_key = entry.timestamp.strftime('%Y-%m-%d') if hasattr(entry, 'timestamp') else 'unknown'
                people_key = ','.join(sorted(getattr(entry, 'people', [])))
                cluster_key = f"{date_key}_{people_key}"
                
                if cluster_key not in clusters:
                    clusters[cluster_key] = []
                clusters[cluster_key].append(entry)
            
            # Create composite memories for clusters with multiple entries
            composite_count = 0
            for cluster_key, cluster_entries in clusters.items():
                if len(cluster_entries) >= 2:
                    composite_data = {
                        'theme': f"Memories from {cluster_key.split('_')[0]}",
                        'constituent_memory_ids': [entry.id for entry in cluster_entries],
                        'temporal_span': (
                            min(entry.timestamp for entry in cluster_entries),
                            max(entry.timestamp for entry in cluster_entries)
                        ),
                        'significance_score': sum(getattr(entry, 'narrative_significance', 0.5) for entry in cluster_entries) / len(cluster_entries)
                    }
                    
                    self._store_composite_memory(cluster_key, composite_data)
                    composite_count += 1
            
            logger.info(f"Created {composite_count} composite memories")
            
        except Exception as e:
            logger.error(f"Failed to create composite memories: {e}")
    
    def _store_embedding(self, entry_id: str, embedding: List[float]):
        """Store embedding for an entry"""
        try:
            # Store in database - simplified implementation
            embedding_json = json.dumps(embedding)
            self.db.execute_write(
                "UPDATE personal_data SET embeddings = ? WHERE id = ?",
                (embedding_json, entry_id)
            )
        except Exception as e:
            logger.error(f"Failed to store embedding for {entry_id}: {e}")
    
    def _store_image_analysis(self, entry_id: str, analysis: Dict[str, Any]):
        """Store image analysis for an entry"""
        try:
            # Store in database - simplified implementation
            analysis_json = json.dumps(analysis)
            self.db.execute_write(
                "UPDATE personal_data SET ai_metadata = ? WHERE id = ?",
                (analysis_json, entry_id)
            )
        except Exception as e:
            logger.error(f"Failed to store image analysis for {entry_id}: {e}")
    
    def _store_person_profile(self, person: str, profile_data: Dict[str, Any]):
        """Store person profile"""
        try:
            # Store in person_profiles table
            self.db.add_or_replace("person_profiles", {
                'id': person.replace(' ', '_').lower(),
                'name': person,
                **profile_data
            }, "id")
        except Exception as e:
            logger.error(f"Failed to store person profile for {person}: {e}")
    
    def _store_narrative_significance(self, entry_id: str, significance: float):
        """Store narrative significance score"""
        try:
            self.db.execute_write(
                "UPDATE personal_data SET narrative_significance = ? WHERE id = ?",
                (significance, entry_id)
            )
        except Exception as e:
            logger.error(f"Failed to store narrative significance for {entry_id}: {e}")
    
    def _store_composite_memory(self, cluster_key: str, composite_data: Dict[str, Any]):
        """Store composite memory"""
        try:
            self.db.add_or_replace("composite_memories", {
                'id': cluster_key,
                **composite_data
            }, "id")
        except Exception as e:
            logger.error(f"Failed to store composite memory for {cluster_key}: {e}")

def main():
    """Main entry point for AI enhancement pipeline"""
    pipeline = AIEnhancementPipeline()
    pipeline.run_enhancement()

if __name__ == '__main__':
    main()