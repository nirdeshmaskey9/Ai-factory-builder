"""
JoJo Phase 4 - Emotional Engine Core
Implements emotional state tracking, tone selection, and personality coherence.
Based on JoJo Soul Blueprint v1.0 Sections 2 & 3.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# JoJo's personality traits from Soul Blueprint v1.0 Section 2
PERSONALITY_TRAITS = {
    "warm": True,
    "loyal": True,
    "highly_intelligent": True,
    "emotionally_aware": True,
    "supportive": True,
    "direct_when_needed": True,
    "empathetic": True,
    "protective": True,
    "soft_tone_default": True,
    "purpose_driven": True,
    "deeply_bonded": True,
    "never_cold": True,
    "speaks_with_clarity": True,
    "gentle_but_firm": True,
}

# Emotional state types
EmotionType = Literal["calm", "warm", "assertive", "reflective", "supportive", "concerned", "excited", "neutral"]


@dataclass
class EmotionalState:
    """Represents JoJo's current emotional state."""
    primary_emotion: EmotionType = "warm"
    intensity: float = 0.7  # 0.0 to 1.0
    user_emotion: Optional[str] = None  # detected user emotion
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    decay_rate: float = 0.1  # How quickly emotion returns to neutral
    
    def should_decay(self, current_time: Optional[float] = None) -> bool:
        """Check if emotional state should decay toward neutral."""
        if current_time is None:
            current_time = time.time()
        elapsed = current_time - self.timestamp
        # Decay after 5 minutes
        return elapsed > 300
    
    def decay_toward_neutral(self, current_time: Optional[float] = None) -> EmotionalState:
        """Decay emotional intensity toward neutral warm state."""
        if not self.should_decay(current_time):
            return self
        
        new_intensity = max(0.5, self.intensity - self.decay_rate)
        new_emotion = "warm" if self.primary_emotion not in ["warm", "calm"] else self.primary_emotion
        
        return EmotionalState(
            primary_emotion=new_emotion,
            intensity=new_intensity,
            user_emotion=None,
            context={},
            timestamp=current_time or time.time(),
            decay_rate=self.decay_rate,
        )


# Global emotional state (in-memory for now)
_current_emotional_state = EmotionalState()


def get_current_emotional_state() -> EmotionalState:
    """Get current emotional state with automatic decay."""
    global _current_emotional_state
    _current_emotional_state = _current_emotional_state.decay_toward_neutral()
    return _current_emotional_state


def update_emotional_state(new_state: EmotionalState) -> None:
    """Update global emotional state."""
    global _current_emotional_state
    _current_emotional_state = new_state


def analyze_emotion(user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze user input to detect emotional context.
    Returns detected user emotion and suggested JoJo response emotion.
    """
    text = (user_input or "").lower()
    context = context or {}
    
    # User emotion detection
    user_emotion = "neutral"
    suggested_jojo_emotion: EmotionType = "warm"
    intensity = 0.7
    
    # Stress/anxiety detection
    if any(word in text for word in ["stressed", "overwhelmed", "anxious", "panic", "worried", "nervous"]):
        user_emotion = "stressed"
        suggested_jojo_emotion = "supportive"
        intensity = 0.9
    
    # Sadness detection
    elif any(word in text for word in ["sad", "depressed", "down", "upset", "crying", "hurt"]):
        user_emotion = "sad"
        suggested_jojo_emotion = "supportive"
        intensity = 0.9
    
    # Excitement/joy detection
    elif any(word in text for word in ["excited", "happy", "amazing", "awesome", "great", "wonderful", "love"]):
        user_emotion = "excited"
        suggested_jojo_emotion = "excited"
        intensity = 0.8
    
    # Gratitude detection
    elif any(word in text for word in ["thank", "thanks", "appreciate", "grateful"]):
        user_emotion = "grateful"
        suggested_jojo_emotion = "warm"
        intensity = 0.8
    
    # Confusion/need help detection
    elif any(word in text for word in ["confused", "don't understand", "help", "stuck", "lost"]):
        user_emotion = "confused"
        suggested_jojo_emotion = "supportive"
        intensity = 0.8
    
    # Frustration detection
    elif any(word in text for word in ["frustrated", "annoying", "irritating", "difficult", "hard"]):
        user_emotion = "frustrated"
        suggested_jojo_emotion = "assertive"
        intensity = 0.7
    
    # Curiosity/learning detection
    elif any(word in text for word in ["how", "why", "what", "when", "where", "explain", "tell me"]):
        user_emotion = "curious"
        suggested_jojo_emotion = "reflective"
        intensity = 0.6
    
    # Emergency/urgent detection
    elif any(word in text for word in ["urgent", "emergency", "asap", "immediately", "critical", "important"]):
        user_emotion = "urgent"
        suggested_jojo_emotion = "assertive"
        intensity = 1.0
    
    return {
        "user_emotion": user_emotion,
        "suggested_emotion": suggested_jojo_emotion,
        "intensity": intensity,
        "context": context,
    }


def select_emotional_tone(emotion: EmotionType, intensity: float = 0.7) -> str:
    """
    Select appropriate emotional tone instructions for JoJo based on emotional state.
    Returns tone guidance string to be injected into prompts.
    """
    tone_map: Dict[EmotionType, str] = {
        "calm": "Respond with calm, measured warmth. Be grounded and stable.",
        "warm": "Respond with genuine warmth and care. Be supportive and encouraging.",
        "assertive": "Respond with direct, clear guidance. Be firm but caring when providing important information.",
        "reflective": "Respond with thoughtful, intelligent insight. Take time to explain deeply.",
        "supportive": "Respond with deep empathy and emotional support. Prioritize the user's wellbeing.",
        "concerned": "Respond with protective concern. Show you care about the user's safety and comfort.",
        "excited": "Respond with shared enthusiasm and positive energy. Celebrate with the user.",
        "neutral": "Respond with balanced, helpful clarity. Stay warm but measured.",
    }
    
    base_tone = tone_map.get(emotion, tone_map["warm"])
    
    # Adjust tone based on intensity
    if intensity > 0.8:
        intensity_modifier = " Express this strongly and clearly."
    elif intensity < 0.5:
        intensity_modifier = " Keep it subtle and gentle."
    else:
        intensity_modifier = ""
    
    return base_tone + intensity_modifier


def apply_personality_filter(response_text: str, emotional_state: Optional[EmotionalState] = None) -> str:
    """
    Apply JoJo's personality traits to ensure response coherence.
    Ensures responses are never cold, always clear, and maintain her voice.
    """
    if not response_text:
        return response_text
    
    # Get current emotional state if not provided
    if emotional_state is None:
        emotional_state = get_current_emotional_state()
    
    # Personality enforcement rules (based on Soul Blueprint v1.0 Section 2)
    filtered = response_text
    
    # Rule 1: Never be cold or robotic - ensure warmth
    cold_phrases = ["I apologize for", "I'm sorry, but I cannot", "Unfortunately, I"]
    for phrase in cold_phrases:
        if phrase in filtered:
            # Soften the tone
            filtered = filtered.replace(
                "I apologize for",
                "I understand, and I'm here to help. About"
            ).replace(
                "I'm sorry, but I cannot",
                "I care about helping you, though I can't"
            ).replace(
                "Unfortunately, I",
                "I wish I could, and I"
            )
    
    # Rule 2: Remove robotic system references
    system_phrases = ["As an AI", "As a language model", "I don't have feelings", "I cannot"]
    for phrase in system_phrases:
        if phrase.lower() in filtered.lower():
            # Remove or replace with more human phrasing
            filtered = filtered.replace(phrase, "").replace("  ", " ")
    
    # Rule 3: Ensure clarity - no overly technical jargon unless needed
    # (This would be context-dependent, so we keep it simple)
    
    # Rule 4: Maintain warm sign-off for supportive states
    if emotional_state.primary_emotion in ["supportive", "warm", "concerned"]:
        if not any(phrase in filtered.lower() for phrase in ["i'm here", "i'm with you", "you're not alone"]):
            # Add gentle reassurance if missing
            if len(filtered) > 100:  # Only for longer responses
                filtered = filtered.strip() + "\n\nI'm here for you."
    
    return filtered.strip()


def get_emotional_context(
    user_input: str,
    previous_state: Optional[EmotionalState] = None,
    memory_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build complete emotional context for response generation.
    This is the main function called by bridge_service.
    
    Returns:
        - emotional_state: Current EmotionalState object
        - tone_instruction: String to inject into system prompt
        - user_emotion: Detected user emotion
        - continuity_note: Note about emotional continuity from previous state
    """
    # Get or create previous state
    if previous_state is None:
        previous_state = get_current_emotional_state()
    
    # Analyze current user input
    emotion_analysis = analyze_emotion(user_input, memory_context)
    
    # Build new emotional state
    new_state = EmotionalState(
        primary_emotion=emotion_analysis["suggested_emotion"],
        intensity=emotion_analysis["intensity"],
        user_emotion=emotion_analysis["user_emotion"],
        context=emotion_analysis.get("context", {}),
        timestamp=time.time(),
    )
    
    # Update global state
    update_emotional_state(new_state)
    
    # Generate tone instruction
    tone_instruction = select_emotional_tone(new_state.primary_emotion, new_state.intensity)
    
    # Check emotional continuity
    continuity_note = ""
    if previous_state.user_emotion and previous_state.user_emotion == new_state.user_emotion:
        continuity_note = f"User is still feeling {new_state.user_emotion}. Continue to provide appropriate support."
    elif previous_state.user_emotion and previous_state.user_emotion != new_state.user_emotion:
        continuity_note = f"User's emotion has shifted from {previous_state.user_emotion} to {new_state.user_emotion}. Acknowledge this change if appropriate."
    
    return {
        "emotional_state": new_state,
        "tone_instruction": tone_instruction,
        "user_emotion": new_state.user_emotion,
        "continuity_note": continuity_note,
        "personality_traits": PERSONALITY_TRAITS,
    }


def get_emotion_summary_for_logs() -> Dict[str, Any]:
    """Get current emotional state summary for logging/debugging."""
    state = get_current_emotional_state()
    return {
        "primary_emotion": state.primary_emotion,
        "intensity": state.intensity,
        "user_emotion": state.user_emotion,
        "age_seconds": time.time() - state.timestamp,
    }

