"""
AI Service Manager for Personal Archive System

This module manages all AI services including:
- Local LLM integration for narrative generation
- Multimodal model support for enhanced image understanding
- Embedding generation for semantic search
- Text-to-speech integration
- Model fallback and error handling
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify
from dataclasses import dataclass
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AIServiceConfig:
    """Configuration for AI services"""
    local_llm_model: str = "microsoft/DialoGPT-medium"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    tts_model: str = "espnet/kan-bayashi_ljspeech_vits"
    multimodal_model: str = "openai/clip-vit-base-patch32"
    model_dir: str = "/app/models"
    batch_size: int = 32
    max_memory_gb: int = 4
    enable_gpu: bool = False

class AIServiceManager:
    """Manages all AI services for the Personal Archive System"""
    
    def __init__(self, config: AIServiceConfig):
        self.config = config
        self.app = Flask(__name__)
        self.services = {}
        self.model_cache = {}
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes for AI services"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'services': list(self.services.keys()),
                'models_loaded': list(self.model_cache.keys())
            })
        
        @self.app.route('/api/ai/generate_narrative', methods=['POST'])
        def generate_narrative():
            """Generate narrative from memories"""
            try:
                data = request.get_json()
                memories = data.get('memories', [])
                mode = data.get('mode', 'chronological')
                
                narrative_service = self.get_service('narrative')
                if not narrative_service:
                    return jsonify({'error': 'Narrative service not available'}), 503
                
                result = narrative_service.generate_narrative(memories, mode)
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error generating narrative: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/generate_embeddings', methods=['POST'])
        def generate_embeddings():
            """Generate embeddings for semantic search"""
            try:
                data = request.get_json(force=True)
                texts = data.get('texts', [])
                
                embedding_service = self.get_service('embeddings')
                if not embedding_service:
                    return jsonify({'error': 'Embedding service not available'}), 503
                
                embeddings = embedding_service.generate_embeddings(texts)
                return jsonify({'embeddings': embeddings})
                
            except (ValueError, TypeError) as e:
                # JSON parsing errors
                return jsonify({'error': 'Invalid JSON in request body'}), 400
            except Exception as e:
                logger.error(f"Error generating embeddings: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/analyze_image', methods=['POST'])
        def analyze_image():
            """Analyze image with multimodal understanding"""
            try:
                data = request.get_json()
                image_path = data.get('image_path')
                context = data.get('context', '')
                
                multimodal_service = self.get_service('multimodal')
                if not multimodal_service:
                    return jsonify({'error': 'Multimodal service not available'}), 503
                
                analysis = multimodal_service.analyze_image(image_path, context)
                return jsonify(analysis)
                
            except Exception as e:
                logger.error(f"Error analyzing image: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/synthesize_speech', methods=['POST'])
        def synthesize_speech():
            """Convert text to speech"""
            try:
                data = request.get_json()
                text = data.get('text', '')
                narrator_style = data.get('narrator_style', 'neutral')
                
                tts_service = self.get_service('tts')
                if not tts_service:
                    return jsonify({'error': 'TTS service not available'}), 503
                
                audio_path = tts_service.synthesize_speech(text, narrator_style)
                return jsonify({'audio_path': audio_path})
                
            except Exception as e:
                logger.error(f"Error synthesizing speech: {e}")
                return jsonify({'error': str(e)}), 500
    
    def initialize_services(self):
        """Initialize all AI services"""
        logger.info("Initializing AI services...")
        
        # Initialize services in order of dependency
        services_to_init = [
            ('embeddings', self._init_embedding_service),
            ('multimodal', self._init_multimodal_service),
            ('narrative', self._init_narrative_service),
            ('tts', self._init_tts_service)
        ]
        
        for service_name, init_func in services_to_init:
            try:
                logger.info(f"Initializing {service_name} service...")
                service = init_func()
                if service:
                    self.services[service_name] = service
                    logger.info(f"✓ {service_name} service initialized")
                else:
                    logger.warning(f"⚠ {service_name} service initialization failed")
            except Exception as e:
                logger.error(f"✗ Failed to initialize {service_name} service: {e}")
    
    def _init_embedding_service(self):
        """Initialize embedding service"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer(
                self.config.embedding_model,
                cache_folder=self.config.model_dir
            )
            
            class EmbeddingService:
                def __init__(self, model):
                    self.model = model
                
                def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
                    embeddings = self.model.encode(texts, batch_size=self.config.batch_size)
                    return embeddings.tolist()
            
            return EmbeddingService(model)
            
        except ImportError:
            logger.warning("sentence-transformers not available, embedding service disabled")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            return None
    
    def _init_multimodal_service(self):
        """Initialize multimodal service"""
        try:
            from transformers import CLIPProcessor, CLIPModel
            from PIL import Image
            
            model = CLIPModel.from_pretrained(
                self.config.multimodal_model,
                cache_dir=self.config.model_dir
            )
            processor = CLIPProcessor.from_pretrained(
                self.config.multimodal_model,
                cache_dir=self.config.model_dir
            )
            
            class MultimodalService:
                def __init__(self, model, processor):
                    self.model = model
                    self.processor = processor
                
                def analyze_image(self, image_path: str, context: str = '') -> Dict[str, Any]:
                    try:
                        image = Image.open(image_path)
                        
                        # Generate image description
                        inputs = self.processor(
                            text=[context] if context else ["a photo"],
                            images=image,
                            return_tensors="pt",
                            padding=True
                        )
                        
                        outputs = self.model(**inputs)
                        logits_per_image = outputs.logits_per_image
                        probs = logits_per_image.softmax(dim=1)
                        
                        return {
                            'description': f"Image analysis with context: {context}",
                            'confidence': float(probs.max()),
                            'features': outputs.image_embeds.detach().numpy().tolist()[0][:10]  # First 10 features
                        }
                    except Exception as e:
                        return {'error': str(e)}
            
            return MultimodalService(model, processor)
            
        except ImportError:
            logger.warning("transformers/PIL not available, multimodal service disabled")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize multimodal service: {e}")
            return None
    
    def _init_narrative_service(self):
        """Initialize narrative generation service"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            tokenizer = AutoTokenizer.from_pretrained(
                self.config.local_llm_model,
                cache_dir=self.config.model_dir
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.config.local_llm_model,
                cache_dir=self.config.model_dir
            )
            
            class NarrativeService:
                def __init__(self, model, tokenizer):
                    self.model = model
                    self.tokenizer = tokenizer
                
                def generate_narrative(self, memories: List[Dict], mode: str) -> Dict[str, Any]:
                    try:
                        # Create prompt based on memories and mode
                        prompt = self._create_narrative_prompt(memories, mode)
                        
                        inputs = self.tokenizer.encode(prompt, return_tensors='pt')
                        
                        with torch.no_grad():
                            outputs = self.model.generate(
                                inputs,
                                max_length=inputs.shape[1] + 200,
                                num_return_sequences=1,
                                temperature=0.7,
                                do_sample=True,
                                pad_token_id=self.tokenizer.eos_token_id
                            )
                        
                        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                        narrative = generated_text[len(prompt):].strip()
                        
                        return {
                            'narrative': narrative,
                            'mode': mode,
                            'memory_count': len(memories)
                        }
                    except Exception as e:
                        return {'error': str(e)}
                
                def _create_narrative_prompt(self, memories: List[Dict], mode: str) -> str:
                    """Create a prompt for narrative generation"""
                    if mode == 'chronological':
                        prompt = "Create a chronological story from these memories:\n"
                    elif mode == 'thematic':
                        prompt = "Create a thematic story connecting these memories:\n"
                    elif mode == 'people-centered':
                        prompt = "Create a story focused on the people in these memories:\n"
                    else:
                        prompt = "Create a story from these memories:\n"
                    
                    for i, memory in enumerate(memories[:5]):  # Limit to 5 memories
                        prompt += f"{i+1}. {memory.get('text', '')[:100]}...\n"
                    
                    prompt += "\nStory:"
                    return prompt
            
            return NarrativeService(model, tokenizer)
            
        except ImportError:
            logger.warning("transformers not available, narrative service disabled")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize narrative service: {e}")
            return None
    
    def _init_tts_service(self):
        """Initialize text-to-speech service"""
        try:
            # For now, return a mock TTS service
            # In production, this would use a real TTS library
            
            class TTSService:
                def synthesize_speech(self, text: str, narrator_style: str = 'neutral') -> str:
                    # Mock implementation - in production would generate actual audio
                    logger.info(f"TTS: Synthesizing speech for text length {len(text)} with style {narrator_style}")
                    return f"/app/MyData/app_data/audio/mock_audio_{hash(text)}.wav"
            
            return TTSService()
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")
            return None
    
    def get_service(self, service_name: str):
        """Get a service by name"""
        return self.services.get(service_name)
    
    def run(self, host='0.0.0.0', port=8086):
        """Run the AI service manager"""
        logger.info("Starting AI Service Manager...")
        
        # Initialize services in a separate thread
        init_thread = threading.Thread(target=self.initialize_services)
        init_thread.daemon = True
        init_thread.start()
        
        # Start Flask app
        self.app.run(host=host, port=port, debug=False)

def main():
    """Main entry point"""
    config = AIServiceConfig(
        local_llm_model=os.getenv('LOCAL_LLM_MODEL', 'microsoft/DialoGPT-medium'),
        embedding_model=os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
        tts_model=os.getenv('TTS_MODEL', 'espnet/kan-bayashi_ljspeech_vits'),
        multimodal_model=os.getenv('MULTIMODAL_MODEL', 'openai/clip-vit-base-patch32'),
        model_dir=os.getenv('AI_MODEL_DIR', '/app/models'),
        batch_size=int(os.getenv('AI_PROCESSING_BATCH_SIZE', '32')),
        max_memory_gb=int(os.getenv('AI_MAX_MEMORY_GB', '4')),
        enable_gpu=os.getenv('ENABLE_GPU', 'false').lower() == 'true'
    )
    
    manager = AIServiceManager(config)
    manager.run()

if __name__ == '__main__':
    main()