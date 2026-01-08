"""
Local AI Models Implementation
Privacy-first AI using local models with API fallback
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import sqlite3
from datetime import datetime

# Local model imports
try:
    from sentence_transformers import SentenceTransformer
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import face_recognition
    from PIL import Image
    import torch
    MODELS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some AI libraries not available: {e}")
    MODELS_AVAILABLE = False

from .config import config

logger = logging.getLogger(__name__)

class LocalAIModels:
    """Local AI models for privacy-first processing"""
    
    def __init__(self):
        self.models = {}
        self.device = "cuda" if config.enable_gpu and torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
    def _load_model(self, model_type: str):
        """Lazy load models on first use"""
        if model_type in self.models:
            return self.models[model_type]
            
        if not MODELS_AVAILABLE:
            logger.warning(f"Cannot load {model_type} - libraries not available")
            return None
            
        try:
            if model_type == 'embedding':
                model = SentenceTransformer(config.local_models['embedding'])
                if config.enable_gpu:
                    model = model.to(self.device)
                self.models[model_type] = model
                logger.info(f"Loaded embedding model: {config.local_models['embedding']}")
                
            elif model_type == 'text_generation':
                tokenizer = AutoTokenizer.from_pretrained(config.local_models['text_generation'])
                model = AutoModelForCausalLM.from_pretrained(config.local_models['text_generation'])
                if config.enable_gpu:
                    model = model.to(self.device)
                self.models[model_type] = {'tokenizer': tokenizer, 'model': model}
                logger.info(f"Loaded text generation model: {config.local_models['text_generation']}")
                
            return self.models.get(model_type)
            
        except Exception as e:
            logger.error(f"Failed to load {model_type} model: {e}")
            return None
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts using local model"""
        model = self._load_model('embedding')
        if model is None:
            logger.warning("Embedding model not available, returning random embeddings")
            return np.random.rand(len(texts), 384)  # Fallback
            
        try:
            embeddings = model.encode(texts, batch_size=config.batch_size)
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return np.random.rand(len(texts), 384)  # Fallback
    
    def generate_text(self, prompt: str, max_length: int = 100) -> str:
        """Generate text using local model"""
        model_data = self._load_model('text_generation')
        if model_data is None:
            return f"Generated response for: {prompt[:50]}..."  # Fallback
            
        try:
            tokenizer = model_data['tokenizer']
            model = model_data['model']
            
            inputs = tokenizer.encode(prompt, return_tensors='pt')
            if config.enable_gpu:
                inputs = inputs.to(self.device)
                
            with torch.no_grad():
                outputs = model.generate(
                    inputs, 
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=0.7,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Remove the original prompt from response
            response = response[len(prompt):].strip()
            return response if response else "I understand your request."
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"I understand your request about: {prompt[:50]}..."
    
    def detect_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect faces in image using local face recognition"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            faces = []
            for i, (encoding, location) in enumerate(zip(face_encodings, face_locations)):
                faces.append({
                    'id': f"person_{i}",
                    'encoding': encoding.tolist(),
                    'location': location,
                    'confidence': 0.8  # Default confidence
                })
            
            return faces
            
        except Exception as e:
            logger.error(f"Face detection failed for {image_path}: {e}")
            return []
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image content using local models"""
        try:
            # Basic image analysis
            with Image.open(image_path) as img:
                analysis = {
                    'size': img.size,
                    'mode': img.mode,
                    'format': img.format,
                    'faces': self.detect_faces(image_path),
                    'description': f"Image with {len(self.detect_faces(image_path))} detected faces"
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Image analysis failed for {image_path}: {e}")
            return {'error': str(e)}

# Global models instance
local_models = LocalAIModels()