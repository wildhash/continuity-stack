"""
World Model Module
Implements lightweight belief state tracking and updates
"""
from typing import Dict, List, Any
from datetime import datetime
from .types import (
    WorldModel, WorldEntity, WorldRelation, WorldConstraint,
    WorldHypothesis, WorldEvent
)


def create_empty_world_model() -> WorldModel:
    """Create an empty world model"""
    return WorldModel(
        entities=[],
        relations=[],
        constraints=[],
        hypotheses=[],
        timeline=[]
    )


def update_world_model(
    current_model: WorldModel,
    observation: Dict[str, Any],
    tool_results: List[Dict[str, Any]],
    reflection: Dict[str, Any]
) -> WorldModel:
    """
    Update world model based on observations, tool results, and reflection
    Returns new world model
    """
    # Start with current model
    new_model = WorldModel(
        entities=current_model.entities.copy(),
        relations=current_model.relations.copy(),
        constraints=current_model.constraints.copy(),
        hypotheses=current_model.hypotheses.copy(),
        timeline=current_model.timeline.copy()
    )
    
    # Add timeline event for this update
    new_model.timeline.append(WorldEvent(
        timestamp=datetime.now().isoformat(),
        event="world_model_update",
        refs=[]
    ))
    
    # Extract entities from observation
    if "task_type" in observation:
        task_entity_id = f"task_{observation.get('task_type')}"
        if not any(e.id == task_entity_id for e in new_model.entities):
            new_model.entities.append(WorldEntity(
                id=task_entity_id,
                type="task",
                attributes={
                    "task_type": observation.get("task_type"),
                    "observed_at": datetime.now().isoformat()
                }
            ))
    
    # Extract constraints from reflection
    if "lessons_learned" in reflection:
        for lesson in reflection["lessons_learned"]:
            # Convert lesson to constraint
            if "validation" in lesson.lower():
                constraint_id = f"constraint_validation_{len(new_model.constraints)}"
                if not any(c.description == lesson for c in new_model.constraints):
                    new_model.constraints.append(WorldConstraint(
                        type="task",
                        description=lesson,
                        enforced=True
                    ))
    
    # Extract hypotheses from tool results
    for result in tool_results:
        if result.get("status") == "success":
            # Create hypothesis about tool effectiveness
            hypothesis = WorldHypothesis(
                claim=f"Tool {result.get('tool')} is effective for this task type",
                confidence=0.8,
                evidence_refs=[result.get("tool", "unknown")]
            )
            new_model.hypotheses.append(hypothesis)
    
    return new_model


def summarize_world_model(world_model: WorldModel) -> str:
    """
    Generate a human-readable summary of the world model
    Used for prompting and planning
    """
    summary_parts = []
    
    # Entities
    if world_model.entities:
        entity_summary = f"Entities ({len(world_model.entities)}): "
        entity_types = {}
        for entity in world_model.entities:
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
        entity_summary += ", ".join([f"{count} {type_}" for type_, count in entity_types.items()])
        summary_parts.append(entity_summary)
    
    # Relations
    if world_model.relations:
        summary_parts.append(f"Relations: {len(world_model.relations)} connections")
    
    # Constraints
    if world_model.constraints:
        constraint_summary = "Active Constraints:\n"
        for constraint in world_model.constraints[-5:]:  # Last 5
            constraint_summary += f"  - [{constraint.type}] {constraint.description}\n"
        summary_parts.append(constraint_summary.rstrip())
    
    # Hypotheses
    if world_model.hypotheses:
        high_confidence = [h for h in world_model.hypotheses if h.confidence > 0.7]
        if high_confidence:
            hypothesis_summary = f"High-confidence hypotheses ({len(high_confidence)}):\n"
            for hyp in high_confidence[-3:]:  # Last 3
                hypothesis_summary += f"  - {hyp.claim} (confidence: {hyp.confidence:.2f})\n"
            summary_parts.append(hypothesis_summary.rstrip())
    
    # Timeline
    if world_model.timeline:
        summary_parts.append(f"Timeline events: {len(world_model.timeline)}")
    
    if not summary_parts:
        return "World model is empty"
    
    return "\n".join(summary_parts)


def add_entity(world_model: WorldModel, entity_id: str, entity_type: str, attributes: Dict[str, Any] = None) -> WorldModel:
    """
    Add or update an entity in the world model
    NOTE: This function mutates world_model in-place and returns it for chaining
    """
    # Check if entity exists
    for entity in world_model.entities:
        if entity.id == entity_id:
            # Update existing entity
            entity.type = entity_type
            if attributes:
                entity.attributes.update(attributes)
            return world_model
    
    # Add new entity
    world_model.entities.append(WorldEntity(
        id=entity_id,
        type=entity_type,
        attributes=attributes or {}
    ))
    
    return world_model


def add_relation(world_model: WorldModel, from_id: str, to_id: str, relation_type: str, metadata: Dict[str, Any] = None) -> WorldModel:
    """
    Add a relation between entities
    NOTE: This function mutates world_model in-place and returns it for chaining
    """
    world_model.relations.append(WorldRelation(
        from_id=from_id,
        to_id=to_id,
        type=relation_type,
        metadata=metadata or {}
    ))
    
    return world_model


def add_constraint(world_model: WorldModel, constraint_type: str, description: str, enforced: bool = True) -> WorldModel:
    """
    Add a constraint to the world model
    NOTE: This function mutates world_model in-place and returns it for chaining
    """
    # Avoid duplicates
    if not any(c.description == description for c in world_model.constraints):
        world_model.constraints.append(WorldConstraint(
            type=constraint_type,
            description=description,
            enforced=enforced
        ))
    
    return world_model


def get_relevant_constraints(world_model: WorldModel, task_type: str) -> List[WorldConstraint]:
    """Get constraints relevant to a task type"""
    relevant = []
    
    for constraint in world_model.constraints:
        # Simple keyword matching
        if task_type.lower() in constraint.description.lower() or constraint.type == "task":
            relevant.append(constraint)
    
    return relevant
