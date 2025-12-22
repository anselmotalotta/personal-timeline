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

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .base_agent import BaseAgent
from .archivist_agent import ArchivistAgent
from .narrative_agent import NarrativeAgent
from .editor_agent import EditorAgent
from .director_agent import DirectorAgent
from .critic_agent import CriticAgent
from src.common.objects.enhanced_llentry import EnhancedLLEntry, Story, Chapter


class AgentCoordinator:
    """
    The Agent Coordinator orchestrates the collaboration between all AI agents
    to ensure high-quality, safe, and well-organized content generation.
    
    This class implements the agent workflow defined in the requirements:
    1. Archivist selects relevant material
    2. Editor filters and organizes content
    3. Narrative creates stories from selected content
    4. Director sequences and paces the final output
    5. Critic ensures quality, safety, and grounding
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Agent Coordinator with all agents.
        
        Args:
            config: Optional configuration for agents
        """
        self.config = config or {}
        self.logger = logging.getLogger("agents.coordinator")
        
        # Initialize all agents
        self.archivist = ArchivistAgent(self.config.get('archivist', {}))
        self.narrative = NarrativeAgent(self.config.get('narrative', {}))
        self.editor = EditorAgent(self.config.get('editor', {}))
        self.director = DirectorAgent(self.config.get('director', {}))
        self.critic = CriticAgent(self.config.get('critic', {}))
        
        # Coordination parameters
        self.max_iterations = self.config.get('max_iterations', 3)
        self.quality_threshold = self.config.get('quality_threshold', 0.7)
        self.require_critic_approval = self.config.get('require_critic_approval', True)
        
        # Workflow tracking
        self.workflow_history: List[Dict[str, Any]] = []
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize all agents in the coordination system.
        
        Returns:
            True if all agents initialized successfully
        """
        agents = [
            ('archivist', self.archivist),
            ('narrative', self.narrative),
            ('editor', self.editor),
            ('director', self.director),
            ('critic', self.critic)
        ]
        
        initialization_results = {}
        
        for agent_name, agent in agents:
            try:
                success = agent.initialize()
                initialization_results[agent_name] = success
                if not success:
                    self.logger.error(f"Failed to initialize {agent_name} agent")
            except Exception as e:
                self.logger.error(f"Exception initializing {agent_name} agent: {e}")
                initialization_results[agent_name] = False
        
        # Check if all agents initialized successfully
        all_initialized = all(initialization_results.values())
        
        if all_initialized:
            self.is_initialized = True
            self.logger.info("All agents initialized successfully")
        else:
            failed_agents = [name for name, success in initialization_results.items() if not success]
            self.logger.error(f"Failed to initialize agents: {failed_agents}")
        
        return all_initialized
    
    def generate_story(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a story using the full agent workflow.
        
        Args:
            request: Story generation request containing:
                - available_memories: List of EnhancedLLEntry objects
                - query: Optional search query
                - theme: Optional thematic focus
                - narrative_mode: Story type (chronological, thematic, etc.)
                - max_results: Maximum memories to include
                
        Returns:
            Dictionary containing the generated story and workflow metadata
        """
        if not self.is_initialized:
            raise RuntimeError("Agent coordinator must be initialized before generating stories")
        
        workflow_start = datetime.now()
        workflow_id = f"story_{int(workflow_start.timestamp())}"
        
        self.logger.info(f"Starting story generation workflow {workflow_id}")
        
        try:
            # Step 1: Archivist selects relevant memories
            self.logger.info("Step 1: Archivist selecting relevant memories")
            selected_memories = self._run_archivist_selection(request, workflow_id)
            
            if not selected_memories:
                return self._create_error_result("No memories selected by archivist", workflow_id)
            
            # Step 2: Editor filters and organizes selected memories
            self.logger.info("Step 2: Editor filtering and organizing memories")
            filtered_memories = self._run_editor_filtering(selected_memories, request, workflow_id)
            
            if not filtered_memories:
                return self._create_error_result("No memories passed editor filtering", workflow_id)
            
            # Step 3: Narrative agent creates story
            self.logger.info("Step 3: Narrative agent creating story")
            initial_story = self._run_narrative_generation(filtered_memories, request, workflow_id)
            
            if not initial_story or not initial_story.chapters:
                return self._create_error_result("Failed to generate story", workflow_id)
            
            # Step 4: Director sequences and paces the story
            self.logger.info("Step 4: Director optimizing story sequence and pacing")
            directed_story = self._run_director_optimization(initial_story, request, workflow_id)
            
            # Step 5: Critic reviews and approves final story
            self.logger.info("Step 5: Critic reviewing final story")
            final_story, approval_result = self._run_critic_review(directed_story, request, workflow_id)
            
            # Create final result
            workflow_end = datetime.now()
            workflow_duration = (workflow_end - workflow_start).total_seconds()
            
            result = {
                'success': True,
                'story': final_story,
                'workflow_id': workflow_id,
                'workflow_duration': workflow_duration,
                'critic_approval': approval_result,
                'memories_processed': len(request.get('available_memories', [])),
                'memories_selected': len(selected_memories),
                'memories_filtered': len(filtered_memories),
                'chapters_generated': len(final_story.chapters) if final_story else 0,
                'workflow_steps': self._get_workflow_steps(workflow_id)
            }
            
            self.logger.info(f"Story generation workflow {workflow_id} completed successfully "
                           f"in {workflow_duration:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Story generation workflow {workflow_id} failed: {e}")
            return self._create_error_result(f"Workflow failed: {str(e)}", workflow_id)
    
    def generate_gallery(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a curated gallery using agent coordination.
        
        Args:
            request: Gallery generation request
            
        Returns:
            Dictionary containing the generated gallery and metadata
        """
        if not self.is_initialized:
            raise RuntimeError("Agent coordinator must be initialized before generating galleries")
        
        workflow_start = datetime.now()
        workflow_id = f"gallery_{int(workflow_start.timestamp())}"
        
        self.logger.info(f"Starting gallery generation workflow {workflow_id}")
        
        try:
            # Step 1: Archivist selects relevant memories
            selected_memories = self._run_archivist_selection(request, workflow_id)
            
            if not selected_memories:
                return self._create_error_result("No memories selected for gallery", workflow_id)
            
            # Step 2: Editor filters and organizes
            filtered_memories = self._run_editor_filtering(selected_memories, request, workflow_id)
            
            # Step 3: Director sequences for gallery presentation
            sequenced_memories = self._run_director_sequencing(filtered_memories, request, workflow_id)
            
            # Step 4: Critic reviews selection
            final_memories, approval_result = self._run_critic_memory_review(sequenced_memories, request, workflow_id)
            
            # Create gallery result
            workflow_end = datetime.now()
            workflow_duration = (workflow_end - workflow_start).total_seconds()
            
            result = {
                'success': True,
                'memories': final_memories,
                'workflow_id': workflow_id,
                'workflow_duration': workflow_duration,
                'critic_approval': approval_result,
                'memories_processed': len(request.get('available_memories', [])),
                'memories_selected': len(final_memories),
                'workflow_steps': self._get_workflow_steps(workflow_id)
            }
            
            self.logger.info(f"Gallery generation workflow {workflow_id} completed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Gallery generation workflow {workflow_id} failed: {e}")
            return self._create_error_result(f"Gallery workflow failed: {str(e)}", workflow_id)
    
    def _run_archivist_selection(self, request: Dict[str, Any], workflow_id: str) -> List[EnhancedLLEntry]:
        """
        Run the archivist agent to select relevant memories.
        
        Args:
            request: Original request
            workflow_id: Workflow identifier
            
        Returns:
            List of selected memories
        """
        context = {'workflow_id': workflow_id, 'step': 'archivist_selection'}
        
        try:
            selected_memories = self.archivist._safe_process(request, context)
            
            self._log_workflow_step(workflow_id, 'archivist_selection', {
                'input_count': len(request.get('available_memories', [])),
                'output_count': len(selected_memories) if selected_memories else 0,
                'success': selected_memories is not None
            })
            
            return selected_memories or []
            
        except Exception as e:
            self.logger.error(f"Archivist selection failed: {e}")
            self._log_workflow_step(workflow_id, 'archivist_selection', {
                'success': False,
                'error': str(e)
            })
            return []
    
    def _run_editor_filtering(self, memories: List[EnhancedLLEntry], 
                            request: Dict[str, Any], workflow_id: str) -> List[EnhancedLLEntry]:
        """
        Run the editor agent to filter and organize memories.
        
        Args:
            memories: Memories to filter
            request: Original request
            workflow_id: Workflow identifier
            
        Returns:
            List of filtered memories
        """
        context = {'workflow_id': workflow_id, 'step': 'editor_filtering', 'original_request': request}
        
        try:
            filtered_memories = self.editor._safe_process(memories, context)
            
            self._log_workflow_step(workflow_id, 'editor_filtering', {
                'input_count': len(memories),
                'output_count': len(filtered_memories) if filtered_memories else 0,
                'success': filtered_memories is not None
            })
            
            return filtered_memories or []
            
        except Exception as e:
            self.logger.error(f"Editor filtering failed: {e}")
            self._log_workflow_step(workflow_id, 'editor_filtering', {
                'success': False,
                'error': str(e)
            })
            return []
    
    def _run_narrative_generation(self, memories: List[EnhancedLLEntry], 
                                request: Dict[str, Any], workflow_id: str) -> Optional[Story]:
        """
        Run the narrative agent to generate a story.
        
        Args:
            memories: Memories to create story from
            request: Original request
            workflow_id: Workflow identifier
            
        Returns:
            Generated story or None if failed
        """
        context = {'workflow_id': workflow_id, 'step': 'narrative_generation'}
        
        # Prepare narrative request
        narrative_request = {
            'memories': memories,
            'narrative_mode': request.get('narrative_mode', 'chronological'),
            'narrative_style': request.get('narrative_style', 'documentary'),
            'title': request.get('title', '')
        }
        
        try:
            story = self.narrative._safe_process(narrative_request, context)
            
            self._log_workflow_step(workflow_id, 'narrative_generation', {
                'input_memories': len(memories),
                'output_chapters': len(story.chapters) if story else 0,
                'story_title': story.title if story else None,
                'success': story is not None
            })
            
            return story
            
        except Exception as e:
            self.logger.error(f"Narrative generation failed: {e}")
            self._log_workflow_step(workflow_id, 'narrative_generation', {
                'success': False,
                'error': str(e)
            })
            return None
    
    def _run_director_optimization(self, story: Story, request: Dict[str, Any], workflow_id: str) -> Story:
        """
        Run the director agent to optimize story sequence and pacing.
        
        Args:
            story: Story to optimize
            request: Original request
            workflow_id: Workflow identifier
            
        Returns:
            Optimized story
        """
        context = {'workflow_id': workflow_id, 'step': 'director_optimization', 'original_request': request}
        
        try:
            optimized_story = self.director._safe_process(story, context)
            
            self._log_workflow_step(workflow_id, 'director_optimization', {
                'input_chapters': len(story.chapters),
                'output_chapters': len(optimized_story.chapters) if optimized_story else 0,
                'success': optimized_story is not None
            })
            
            return optimized_story or story
            
        except Exception as e:
            self.logger.error(f"Director optimization failed: {e}")
            self._log_workflow_step(workflow_id, 'director_optimization', {
                'success': False,
                'error': str(e)
            })
            return story
    
    def _run_director_sequencing(self, memories: List[EnhancedLLEntry], 
                               request: Dict[str, Any], workflow_id: str) -> List[EnhancedLLEntry]:
        """
        Run the director agent to sequence memories.
        
        Args:
            memories: Memories to sequence
            request: Original request
            workflow_id: Workflow identifier
            
        Returns:
            Sequenced memories
        """
        context = {'workflow_id': workflow_id, 'step': 'director_sequencing', 'original_request': request}
        
        try:
            sequenced_memories = self.director._safe_process(memories, context)
            
            self._log_workflow_step(workflow_id, 'director_sequencing', {
                'input_count': len(memories),
                'output_count': len(sequenced_memories) if sequenced_memories else 0,
                'success': sequenced_memories is not None
            })
            
            return sequenced_memories or memories
            
        except Exception as e:
            self.logger.error(f"Director sequencing failed: {e}")
            self._log_workflow_step(workflow_id, 'director_sequencing', {
                'success': False,
                'error': str(e)
            })
            return memories
    
    def _run_critic_review(self, story: Story, request: Dict[str, Any], 
                         workflow_id: str) -> Tuple[Story, Dict[str, Any]]:
        """
        Run the critic agent to review and approve the story.
        
        Args:
            story: Story to review
            request: Original request
            workflow_id: Workflow identifier
            
        Returns:
            Tuple of (final_story, approval_result)
        """
        context = {'workflow_id': workflow_id, 'step': 'critic_review', 'original_request': request}
        
        try:
            approval_result = self.critic._safe_process(story, context)
            
            if approval_result and approval_result.get('approved', False):
                final_story = story
            else:
                # If not approved, try to fix issues or return original
                final_story = self._attempt_story_fixes(story, approval_result, workflow_id)
            
            self._log_workflow_step(workflow_id, 'critic_review', {
                'approved': approval_result.get('approved', False) if approval_result else False,
                'issues_count': len(approval_result.get('issues', [])) if approval_result else 0,
                'quality_score': approval_result.get('quality_score', 0.0) if approval_result else 0.0,
                'success': approval_result is not None
            })
            
            return final_story, approval_result or {'approved': False, 'issues': ['Critic review failed']}
            
        except Exception as e:
            self.logger.error(f"Critic review failed: {e}")
            self._log_workflow_step(workflow_id, 'critic_review', {
                'success': False,
                'error': str(e)
            })
            return story, {'approved': False, 'issues': [f'Critic review error: {str(e)}']}
    
    def _run_critic_memory_review(self, memories: List[EnhancedLLEntry], 
                                request: Dict[str, Any], workflow_id: str) -> Tuple[List[EnhancedLLEntry], Dict[str, Any]]:
        """
        Run the critic agent to review memory selection.
        
        Args:
            memories: Memories to review
            request: Original request
            workflow_id: Workflow identifier
            
        Returns:
            Tuple of (final_memories, approval_result)
        """
        context = {'workflow_id': workflow_id, 'step': 'critic_memory_review', 'original_request': request}
        
        try:
            approval_result = self.critic._safe_process(memories, context)
            
            if approval_result and approval_result.get('approved', False):
                final_memories = memories
            else:
                # If not approved, return original memories (could implement fixes here)
                final_memories = memories
            
            self._log_workflow_step(workflow_id, 'critic_memory_review', {
                'approved': approval_result.get('approved', False) if approval_result else False,
                'issues_count': len(approval_result.get('issues', [])) if approval_result else 0,
                'quality_score': approval_result.get('quality_score', 0.0) if approval_result else 0.0,
                'success': approval_result is not None
            })
            
            return final_memories, approval_result or {'approved': False, 'issues': ['Memory review failed']}
            
        except Exception as e:
            self.logger.error(f"Critic memory review failed: {e}")
            self._log_workflow_step(workflow_id, 'critic_memory_review', {
                'success': False,
                'error': str(e)
            })
            return memories, {'approved': False, 'issues': [f'Memory review error: {str(e)}']}
    
    def _attempt_story_fixes(self, story: Story, approval_result: Dict[str, Any], workflow_id: str) -> Story:
        """
        Attempt to fix issues identified by the critic.
        
        Args:
            story: Story with issues
            approval_result: Critic's review result
            workflow_id: Workflow identifier
            
        Returns:
            Fixed story (or original if fixes fail)
        """
        if not approval_result or approval_result.get('approved', False):
            return story
        
        issues = approval_result.get('issues', [])
        
        self.logger.info(f"Attempting to fix {len(issues)} issues in story")
        
        try:
            # Simple fixes - in a real implementation, this could be more sophisticated
            fixed_story = story
            
            # Fix empty chapters
            if any('empty' in issue.lower() for issue in issues):
                fixed_story.chapters = [ch for ch in fixed_story.chapters 
                                      if ch.narrative_text and len(ch.narrative_text.strip()) >= 10]
            
            # Fix title if needed
            if any('title' in issue.lower() for issue in issues):
                if not fixed_story.title or len(fixed_story.title.strip()) < 3:
                    fixed_story.title = "Personal Story"
            
            self._log_workflow_step(workflow_id, 'story_fixes', {
                'issues_addressed': len(issues),
                'chapters_after_fix': len(fixed_story.chapters)
            })
            
            return fixed_story
            
        except Exception as e:
            self.logger.error(f"Story fixes failed: {e}")
            return story
    
    def _log_workflow_step(self, workflow_id: str, step_name: str, metadata: Dict[str, Any]) -> None:
        """
        Log a workflow step for tracking and debugging.
        
        Args:
            workflow_id: Workflow identifier
            step_name: Name of the step
            metadata: Step metadata
        """
        step_log = {
            'workflow_id': workflow_id,
            'step_name': step_name,
            'timestamp': datetime.now(),
            'metadata': metadata
        }
        
        self.workflow_history.append(step_log)
    
    def _get_workflow_steps(self, workflow_id: str) -> List[Dict[str, Any]]:
        """
        Get all workflow steps for a specific workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            List of workflow steps
        """
        return [step for step in self.workflow_history if step['workflow_id'] == workflow_id]
    
    def _create_error_result(self, error_message: str, workflow_id: str) -> Dict[str, Any]:
        """
        Create an error result for failed workflows.
        
        Args:
            error_message: Error description
            workflow_id: Workflow identifier
            
        Returns:
            Error result dictionary
        """
        return {
            'success': False,
            'error': error_message,
            'workflow_id': workflow_id,
            'workflow_steps': self._get_workflow_steps(workflow_id)
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents in the coordination system.
        
        Returns:
            Dictionary containing status of all agents
        """
        return {
            'coordinator_initialized': self.is_initialized,
            'agents': {
                'archivist': self.archivist.get_status(),
                'narrative': self.narrative.get_status(),
                'editor': self.editor.get_status(),
                'director': self.director.get_status(),
                'critic': self.critic.get_status()
            },
            'workflow_history_count': len(self.workflow_history),
            'config': self.config
        }
    
    def reset_all_agents(self) -> None:
        """
        Reset all agents and clear workflow history.
        """
        agents = [self.archivist, self.narrative, self.editor, self.director, self.critic]
        
        for agent in agents:
            agent.reset()
        
        self.workflow_history.clear()
        self.logger.info("All agents reset and workflow history cleared")
    
    def validate_request(self, request: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a request before processing.
        
        Args:
            request: Request to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for required fields
        if 'available_memories' not in request:
            issues.append("Missing 'available_memories' field")
        elif not isinstance(request['available_memories'], list):
            issues.append("'available_memories' must be a list")
        elif len(request['available_memories']) == 0:
            issues.append("'available_memories' cannot be empty")
        
        # Validate memory objects
        if 'available_memories' in request:
            for i, memory in enumerate(request['available_memories']):
                if not isinstance(memory, EnhancedLLEntry):
                    issues.append(f"Memory {i} is not an EnhancedLLEntry object")
        
        # Check optional fields
        if 'narrative_mode' in request:
            valid_modes = ['chronological', 'thematic', 'people-centered', 'place-centered']
            if request['narrative_mode'] not in valid_modes:
                issues.append(f"Invalid narrative_mode. Must be one of: {valid_modes}")
        
        if 'max_results' in request:
            if not isinstance(request['max_results'], int) or request['max_results'] < 1:
                issues.append("'max_results' must be a positive integer")
        
        return len(issues) == 0, issues
    
    # Convenience methods for individual agent processing
    
    def process_with_archivist(self, request: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> List[EnhancedLLEntry]:
        """
        Process a request with the Archivist Agent.
        
        Args:
            request: Archivist request
            context: Optional context
            
        Returns:
            List of selected memories
        """
        return self.archivist._safe_process(request, context) or []
    
    def process_with_narrative(self, request: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> Optional[Story]:
        """
        Process a request with the Narrative Agent.
        
        Args:
            request: Narrative request
            context: Optional context
            
        Returns:
            Generated story or None
        """
        return self.narrative._safe_process(request, context)
    
    def process_with_editor(self, input_data: Any, 
                           context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Process input with the Editor Agent.
        
        Args:
            input_data: Data to edit
            context: Optional context
            
        Returns:
            Edited data
        """
        return self.editor._safe_process(input_data, context) or input_data
    
    def process_with_director(self, input_data: Any, 
                             context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Process input with the Director Agent.
        
        Args:
            input_data: Data to direct
            context: Optional context
            
        Returns:
            Directed data
        """
        return self.director._safe_process(input_data, context) or input_data
    
    def process_with_critic(self, input_data: Any, 
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process input with the Critic Agent.
        
        Args:
            input_data: Data to critique
            context: Optional context
            
        Returns:
            Critique result
        """
        return self.critic._safe_process(input_data, context) or {'approved': False, 'issues': ['Critic processing failed']}