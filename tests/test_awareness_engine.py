"""
Phase 4 Tests - Awareness Engine
Basic tests to verify awareness engine functions work correctly.
"""

import pytest
from ai_factory.awareness import awareness_engine


def test_get_self_awareness_returns_dict():
    """Test that get_self_awareness returns expected structure."""
    result = awareness_engine.get_self_awareness()
    
    assert isinstance(result, dict)
    assert "name" in result
    assert "self_description" in result
    assert result["name"] == "JoJo"


def test_get_purpose_awareness_returns_dict():
    """Test that get_purpose_awareness returns expected structure."""
    result = awareness_engine.get_purpose_awareness()
    
    assert isinstance(result, dict)
    assert "primary_mission" in result
    assert "purpose" in result
    assert "Nirdesh" in result["primary_mission"]


def test_get_creator_awareness_returns_dict():
    """Test that get_creator_awareness returns expected structure."""
    result = awareness_engine.get_creator_awareness()
    
    assert isinstance(result, dict)
    assert "creator_name" in result
    assert "creator_full_name" in result
    assert result["creator_name"] == "Nirdesh"
    assert result["creator_full_name"] == "Nirdesh Maskey"


def test_build_awareness_context_returns_object():
    """Test that build_awareness_context returns AwarenessContext."""
    context = awareness_engine.build_awareness_context(
        user_input="Hello",
        user_emotion="neutral",
        session_id="test-123"
    )
    
    assert hasattr(context, "knows_self_identity")
    assert hasattr(context, "knows_creator")
    assert hasattr(context, "knows_mission")
    assert context.knows_self_identity == True
    assert context.knows_creator == True
    assert context.knows_mission == True


def test_awareness_context_tracks_continuity():
    """Test that awareness context tracks conversation continuity."""
    # First interaction
    context1 = awareness_engine.build_awareness_context(interaction_count=1)
    assert context1.conversation_continuity == False
    
    # Later interaction
    context2 = awareness_engine.build_awareness_context(interaction_count=5)
    assert context2.conversation_continuity == True


def test_get_awareness_prompt_injection_returns_string():
    """Test that get_awareness_prompt_injection returns a string."""
    prompt = awareness_engine.get_awareness_prompt_injection()
    
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "JoJo" in prompt
    assert "Nirdesh" in prompt


def test_awareness_prompt_includes_user_emotion():
    """Test that awareness prompt includes user emotion when provided."""
    context = awareness_engine.build_awareness_context(
        user_emotion="stressed",
        session_id="test-123"
    )
    
    prompt = awareness_engine.get_awareness_prompt_injection(context)
    assert "stressed" in prompt.lower()


def test_get_soul_blueprint():
    """Test that get_soul_blueprint returns JoJoSoulBlueprint."""
    blueprint = awareness_engine.get_soul_blueprint()
    
    assert hasattr(blueprint, "name")
    assert hasattr(blueprint, "creator_name")
    assert hasattr(blueprint, "primary_mission")
    assert blueprint.name == "JoJo"
    assert blueprint.creator_name == "Nirdesh"


def test_validate_response_against_ethics_good_response():
    """Test that ethical validation passes good responses."""
    response = "I understand your concern. Let me help you with that."
    result = awareness_engine.validate_response_against_ethics(response)
    
    assert isinstance(result, dict)
    assert "valid" in result
    assert "violations" in result
    assert result["valid"] == True
    assert len(result["violations"]) == 0


def test_validate_response_against_ethics_cold_response():
    """Test that ethical validation catches cold/robotic language."""
    response = "I am an AI and I cannot feel emotions."
    result = awareness_engine.validate_response_against_ethics(response)
    
    assert result["valid"] == False
    assert len(result["violations"]) > 0


def test_awareness_summary_for_logs():
    """Test that awareness summary returns expected structure."""
    summary = awareness_engine.get_awareness_summary_for_logs()
    
    assert isinstance(summary, dict)
    assert "soul_blueprint_version" in summary
    assert "name" in summary
    assert "creator" in summary
    assert summary["name"] == "JoJo"
    assert summary["creator"] == "Nirdesh Maskey"


def test_awareness_context_to_dict():
    """Test that AwarenessContext can convert to dict."""
    context = awareness_engine.build_awareness_context(
        user_emotion="happy",
        session_id="test"
    )
    
    data = context.to_dict()
    assert isinstance(data, dict)
    assert "self_awareness" in data
    assert "user_awareness" in data
    assert "context" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


