import pytest
from fastapi.testclient import TestClient
from ai_factory.main import app


client = TestClient(app)


@pytest.mark.timeout(60)
def test_conversational_chain_coherence():
    """
    This test verifies that JoJo maintains coherent personality, memory,
    and emotional awareness across a multi-turn conversation.
    """

    session_id = "conv-simulation"

    # Turn 1 — establishing emotional tone
    r1 = client.post(
        "/bridge/chat",
        json={
            "user_input": "Hey JoJo, I had a really stressful day today.",
            "session_id": session_id,
        },
    )
    j1 = r1.json()
    assert any(x in j1["response_text"].lower() for x in ["sorry", "stress", "breathe", "rest", "understand"])

    # Turn 2 — testing emotional continuity and recall
    r2 = client.post(
        "/bridge/chat",
        json={
            "user_input": "Thanks for understanding earlier, what do you think I should do to relax?",
            "session_id": session_id,
        },
    )
    j2 = r2.json()
    assert any(x in j2["response_text"].lower() for x in ["relax", "take a break", "walk", "listen", "calm", "sleep"])

    # Turn 3 — testing long-term coherence
    r3 = client.post(
        "/bridge/chat",
        json={
            "user_input": "You’re right, maybe I’ll take a walk. Do you remember what kind of day I had?",
            "session_id": session_id,
        },
    )
    j3 = r3.json()
    assert "stress" in j3["response_text"].lower() or "tough" in j3["response_text"].lower()

    # Turn 4 — self-awareness and empathy reinforcement
    r4 = client.post(
        "/bridge/chat",
        json={
            "user_input": "Thanks JoJo, you actually made me feel a bit better.",
            "session_id": session_id,
        },
    )
    j4 = r4.json()
    assert any(x in j4["response_text"].lower() for x in ["glad", "happy", "you're welcome", "support"])

    print("\n✅ JoJo maintained emotional and contextual coherence across 4 turns.")

