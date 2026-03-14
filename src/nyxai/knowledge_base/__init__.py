"""NyxAI Knowledge Base module.

This module provides knowledge base capabilities for storing and
retrieving historical incidents and solutions.
"""

from nyxai.knowledge_base.incident_kb import IncidentKnowledgeBase, IncidentRecord

__all__ = [
    "IncidentKnowledgeBase",
    "IncidentRecord",
]
