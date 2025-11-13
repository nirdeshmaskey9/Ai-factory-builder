"""
Phase 4 Tests - Emotion Engine
Basic tests to verify emotion engine functions work correctly.
"""

import pytest
from ai_factory.emotion import emotion_engine


def test_analyze_emotion_returns_dict():
    """Test that analyze_emotion returns expected structure."""
    result = emotion_engine.analyze_emotion("I feel stressed")
    
    assert isinstance(result, dict)
    assert "user_emotion" in result
    assert "suggested_emotion" in result
    assert "intensity" in result
    assert isinstance(result["intensity"], (int, float))


def test_analyze_emotion_detects_stress():
    """Test that stress keywords are detected."""
    result = emotion_engine.analyze_emotion("I'm very anxious and overwhelmed")
    
    assert result["user_emotion"] in ["stressed", "anxious", "overwhelmed"]
    assert result["suggested_emotion"] in ["supportive", "concerned"]


def test_analyze_emotion_detects_excitement():
    """Test that excitement keywords are detected."""
    result = emotion_engine.analyze_emotion("I'm so excited and happy!")
    
    assert result["user_emotion"] in ["excited", "happy"]
    assert result["suggested_emotion"] in ["excited", "warm"]


def test_get_emotional_context_returns_dict():
    """Test that get_emotional_context returns expected structure."""
    result = emotion_engine.get_emotional_context("Hello, how are you?")
    
    assert isinstance(result, dict)
    assert "emotional_state" in result
    assert "tone_instruction" in result
    assert "user_emotion" in result
    assert isinstance(result["tone_instruction"], str)


def test_select_emotional_tone_returns_string():
    """Test that select_emotional_tone returns a string."""
    tone = emotion_engine.select_emotional_tone("warm", 0.7)
    
    assert isinstance(tone, str)
    assert len(tone) > 0


def test_apply_personality_filter_preserves_good_content():
    """Test that personality filter preserves good content."""
    input_text = "I understand your concern. Let me help you."
    result = emotion_engine.apply_personality_filter(input_text)
    
    assert "understand" in result
    assert "help" in result
    assert isinstance(result, str)


def test_apply_personality_filter_removes_cold_phrases():
    """Test that personality filter softens cold phrases."""
    input_text = "I apologize for the inconvenience."
    result = emotion_engine.apply_personality_filter(input_text)
    
    # Should be softened, not contain "apologize"
    assert "apologize" not in result.lower()


def test_get_current_emotional_state():
    """Test that get_current_emotional_state returns EmotionalState."""
    state = emotion_engine.get_current_emotional_state()
    
    assert hasattr(state, "primary_emotion")
    assert hasattr(state, "intensity")
    assert hasattr(state, "user_emotion")


def test_emotional_state_decay():
    """Test that emotional state can decay."""
    import time
    
    # Create a state from 10 minutes ago
    old_state = emotion_engine.EmotionalState(
        primary_emotion="excited",
        intensity=1.0,
        timestamp=time.time() - 600
    )
    
    assert old_state.should_decay()
    decayed = old_state.decay_toward_neutral()
    assert decayed.intensity <= old_state.intensity


def test_emotion_summary_for_logs():
    """Test that emotion summary returns expected structure."""
    summary = emotion_engine.get_emotion_summary_for_logs()
    
    assert isinstance(summary, dict)
    assert "primary_emotion" in summary
    assert "intensity" in summary
    assert "user_emotion" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

