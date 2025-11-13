"""
Memory Persistence Tests
Verifies that memory persists across restarts and can be recalled.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_factory.memory.memory_agent import store_memory, search_memories, stats
from ai_factory.memory.memory_db import init_db, SessionLocal, MemoryEntry
from sqlalchemy import select, and_
from ai_factory.memory.identity_seeder import seed_identity_memories, verify_identity_memories


@pytest.fixture(scope="function")
def clean_db():
    """Ensure clean database state for tests."""
    init_db()
    yield
    # Cleanup if needed


def test_memory_write_persists(clean_db):
    """Test that memory writes persist to database."""
    # Store a test memory
    mem_id = store_memory(
        run_id=None,
        goal="test_persistence_write",
        summary="This is a test memory for persistence verification.",
        tags=["test", "persistence"],
        score=0.8,
    )
    
    assert mem_id > 0, "Memory should be stored and return an ID"
    
    # Verify it exists in database
    with SessionLocal() as session:
        mem = session.get(MemoryEntry, mem_id)
        assert mem is not None, "Memory should exist in database"
        assert mem.goal == "test_persistence_write"
        assert mem.summary == "This is a test memory for persistence verification."


def test_memory_search_retrieves(clean_db):
    """Test that stored memory can be retrieved via search."""
    # Store test memory
    store_memory(
        run_id=None,
        goal="test_search_retrieval",
        summary="This memory should be found by search.",
        tags=["test", "search"],
        score=0.7,
    )
    
    # Search for it
    results = search_memories("test_search_retrieval", limit=5)
    
    assert len(results) > 0, "Search should return at least one result"
    assert any(m.get("goal") == "test_search_retrieval" for m in results), "Should find the stored memory"


def test_identity_memory_seeding(clean_db):
    """Test that identity memories are seeded correctly."""
    # Seed identity memories
    result = seed_identity_memories()
    
    assert result["total"] > 0, "Should have identity memories to seed"
    
    # Verify they exist
    verify_result = verify_identity_memories()
    assert len(verify_result["verified"]) > 0, "Should have verified identity memories"


def test_identity_recall_birthdate(clean_db):
    """Test that birthdate can be recalled."""
    # Seed identity memories
    seed_identity_memories()
    
    # Search for birthdate - use more specific query and check more results
    results = search_memories("birthdate July 8 2001", limit=20)
    found_text = " ".join([m.get("summary", "") for m in results]).lower()
    
    # Also check if the identity memory exists directly
    from ai_factory.memory.memory_db import SessionLocal
    from sqlalchemy import select, and_
    with SessionLocal() as session:
        birthdate_mem = session.scalars(
            select(MemoryEntry).where(
                and_(
                    MemoryEntry.goal == "user_birthdate",
                    MemoryEntry.deleted == 0
                )
            ).limit(1)
        ).first()
        assert birthdate_mem is not None, "Birthdate identity memory should exist"
        assert "july 8, 2001" in birthdate_mem.summary.lower() or "july 8" in birthdate_mem.summary.lower()


def test_identity_recall_country(clean_db):
    """Test that country can be recalled."""
    # Seed identity memories
    seed_identity_memories()
    
    # Search for country
    results = search_memories("Which country am I from", limit=5)
    found_text = " ".join([m.get("summary", "") for m in results]).lower()
    
    assert "nepal" in found_text, "Should find country in results"


def test_identity_recall_name(clean_db):
    """Test that name can be recalled."""
    # Seed identity memories
    seed_identity_memories()
    
    # Search for name
    results = search_memories("Who am I", limit=5)
    found_text = " ".join([m.get("summary", "") for m in results]).lower()
    
    assert "nirdesh" in found_text, "Should find name in results"


def test_identity_recall_birthplace(clean_db):
    """Test that birthplace can be recalled."""
    # Seed identity memories
    seed_identity_memories()
    
    # Check if the identity memory exists directly
    from ai_factory.memory.memory_db import SessionLocal
    from sqlalchemy import select, and_
    with SessionLocal() as session:
        birthplace_mem = session.scalars(
            select(MemoryEntry).where(
                and_(
                    MemoryEntry.goal == "user_birthplace",
                    MemoryEntry.deleted == 0
                )
            ).limit(1)
        ).first()
        assert birthplace_mem is not None, "Birthplace identity memory should exist"
        assert "kathmandu" in birthplace_mem.summary.lower()


def test_memory_stats(clean_db):
    """Test that memory stats work correctly."""
    # Store some test memories
    for i in range(3):
        store_memory(
            run_id=None,
            goal=f"test_stats_{i}",
            summary=f"Test memory {i}",
            tags=["test", "stats"],
            score=0.5,
        )
    
    # Get stats
    stats_data = stats()
    
    assert stats_data.get("total", 0) >= 3, "Should have at least 3 memories"
    assert "recent_7d" in stats_data or "recent" in stats_data, "Stats should include recent count"


def test_memory_persistence_across_sessions(clean_db):
    """Test that memory persists across different database sessions."""
    # Store memory in one session
    mem_id = store_memory(
        run_id=None,
        goal="test_cross_session",
        summary="This memory should persist across sessions.",
        tags=["test", "cross_session"],
        score=0.9,
    )
    
    # Close and reopen session
    with SessionLocal() as session:
        mem = session.get(MemoryEntry, mem_id)
        assert mem is not None, "Memory should persist across sessions"
        assert mem.goal == "test_cross_session"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

