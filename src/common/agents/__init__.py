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

"""
AI Agent Framework for Personal Archive System

This module provides the AI agent framework that coordinates content selection,
narrative generation, curation, sequencing, and quality control for the
AI-Augmented Personal Archive system.
"""

from .base_agent import BaseAgent
from .archivist_agent import ArchivistAgent
from .narrative_agent import NarrativeAgent
from .editor_agent import EditorAgent
from .director_agent import DirectorAgent
from .critic_agent import CriticAgent
from .agent_coordinator import AgentCoordinator

__all__ = [
    'BaseAgent',
    'ArchivistAgent', 
    'NarrativeAgent',
    'EditorAgent',
    'DirectorAgent',
    'CriticAgent',
    'AgentCoordinator'
]