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

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from src.common.objects.enhanced_llentry import EnhancedLLEntry


class BaseAgent(ABC):
    """
    Base class for all AI agents in the Personal Archive system.
    
    Provides common functionality including logging, error handling,
    and standardized interfaces for agent coordination.
    """
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Unique identifier for this agent
            config: Optional configuration dictionary
        """
        self.agent_name = agent_name
        self.config = config or {}
        self.logger = logging.getLogger(f"agents.{agent_name}")
        self.processing_history: List[Dict[str, Any]] = []
        
        # Agent state
        self.is_initialized = False
        self.last_activity = None
        
    def initialize(self) -> bool:
        """
        Initialize the agent. Must be called before processing.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self._initialize_agent()
            self.is_initialized = True
            self.logger.info(f"Agent {self.agent_name} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize agent {self.agent_name}: {e}")
            return False
    
    @abstractmethod
    def _initialize_agent(self) -> None:
        """
        Agent-specific initialization logic.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Main processing method for the agent.
        Must be implemented by subclasses.
        
        Args:
            input_data: Data to be processed by this agent
            context: Optional context information from other agents
            
        Returns:
            Processed output data
        """
        pass
    
    def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data before processing.
        Can be overridden by subclasses for specific validation.
        
        Args:
            input_data: Data to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        return input_data is not None
    
    def log_processing(self, input_data: Any, output_data: Any, 
                      processing_time: float, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log processing activity for debugging and monitoring.
        
        Args:
            input_data: Input that was processed
            output_data: Output that was generated
            processing_time: Time taken for processing in seconds
            context: Optional context information
        """
        log_entry = {
            'timestamp': datetime.now(),
            'agent': self.agent_name,
            'processing_time': processing_time,
            'input_type': type(input_data).__name__,
            'output_type': type(output_data).__name__,
            'context': context or {}
        }
        
        self.processing_history.append(log_entry)
        self.last_activity = datetime.now()
        
        self.logger.debug(f"Processed {log_entry['input_type']} -> {log_entry['output_type']} "
                         f"in {processing_time:.3f}s")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the agent.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            'agent_name': self.agent_name,
            'is_initialized': self.is_initialized,
            'last_activity': self.last_activity,
            'total_processed': len(self.processing_history),
            'config': self.config
        }
    
    def reset(self) -> None:
        """
        Reset the agent state and clear processing history.
        """
        self.processing_history.clear()
        self.last_activity = None
        self.logger.info(f"Agent {self.agent_name} reset")
    
    def _ensure_initialized(self) -> None:
        """
        Ensure the agent is initialized before processing.
        Raises RuntimeError if not initialized.
        """
        if not self.is_initialized:
            raise RuntimeError(f"Agent {self.agent_name} must be initialized before processing")
    
    def _safe_process(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Safely execute the process method with error handling and logging.
        
        Args:
            input_data: Data to process
            context: Optional context
            
        Returns:
            Processed output or None if processing failed
        """
        self._ensure_initialized()
        
        if not self.validate_input(input_data):
            self.logger.warning(f"Invalid input data for agent {self.agent_name}")
            return None
        
        start_time = datetime.now()
        
        try:
            output = self.process(input_data, context)
            processing_time = (datetime.now() - start_time).total_seconds()
            self.log_processing(input_data, output, processing_time, context)
            return output
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Processing failed in agent {self.agent_name}: {e}")
            self.log_processing(input_data, None, processing_time, 
                              {**(context or {}), 'error': str(e)})
            return None