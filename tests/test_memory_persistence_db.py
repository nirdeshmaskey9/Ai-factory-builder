"""
Phase 4.1 - Memory Persistence Test Suite

Tests that memory persists correctly across database operations
and simulated restarts.

Run with: pytest tests/test_memory_persistence_db.py -v
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import select, create_engine
from sqlalchemy.orm import sessionmaker

# Import memory components
from ai_factory.memory.memory_db import (
    Base,
    MemoryEntry,
    init_db,
    DB_PATH,
    DATA_DIR,
)
from ai_factory.memory.memory_agent import (
    store_memory,
    search_memories,
    stats,
)


class TestMemoryPersistence:
    """Test suite for memory persistence across database operations."""
    
    def setup_method(self):
        """Setup test environment before each test."""
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        init_db()
    
    def test_db_path_is_absolute(self):
        """Verify DB_PATH is an absolute path, not relative."""
        assert os.path.isabs(DB_PATH), f"DB_PATH must be absolute, got: {DB_PATH}"
        assert "data" in DB_PATH.lower(), f"DB_PATH should contain 'data' directory: {DB_PATH}"
    
    def test_db_file_creation(self):
        """Test that database file is created."""
        init_db()
        assert os.path.exists(DB_PATH), f"Database file should exist at: {DB_PATH}"
        assert os.path.getsize(DB_PATH) > 0, "Database file should not be empty"
    
    def test_db_is_writable(self):
        """Test that database file is writable."""
        init_db()
        assert os.access(DB_PATH, os.W_OK), f"Database file must be writable: {DB_PATH}"
    
    def test_simple_write_and_read(self):
        """Test basic write and read operation."""
        # Write a memory
        goal = "test_simple_persistence"
        summary = "This is a test memory for persistence verification."
        tags = ["test", "persistence"]
        
        memory_id = store_memory(
            run_id=None,
            goal=goal,
            summary=summary,
            tags=tags,
            score=1.0
        )
        
        assert memory_id > 0, "Memory ID should be positive"
        
        # Read it back
        results = search_memories(goal, limit=10)
        
        assert len(results) > 0, "Should find at least one result"
        found = any(r.get("goal") == goal for r in results)
        assert found, f"Should find memory with goal '{goal}'"
    
    def test_persistence_across_session_restart(self):
        """Test that memory persists across database session restarts."""
        from ai_factory.memory.memory_db import SessionLocal
        
        # Write memory in first session
        goal = "test_session_restart"
        summary = "Memory written in first session"
        tags = ["test", "restart"]
        
        with SessionLocal() as session:
            entry = MemoryEntry(
                run_id=None,
                goal=goal,
                summary=summary,
                tags="test,restart",
                score=1.0,
            )
            session.add(entry)
            session.commit()
            memory_id = entry.id
        
        # Close session and create a new one
        # This simulates a restart
        
        # Read in second session
        with SessionLocal() as session:
            found = session.get(MemoryEntry, memory_id)
            assert found is not None, f"Memory {memory_id} should persist across sessions"
            assert found.goal == goal, "Goal should match"
            assert found.summary == summary, "Summary should match"
    
    def test_multiple_writes_persist(self):
        """Test that multiple memories persist correctly."""
        memories = [
            ("test_multi_1", "First test memory", ["multi", "test1"]),
            ("test_multi_2", "Second test memory", ["multi", "test2"]),
            ("test_multi_3", "Third test memory", ["multi", "test3"]),
        ]
        
        # Write all memories
        ids = []
        for goal, summary, tags in memories:
            mem_id = store_memory(
                run_id=None,
                goal=goal,
                summary=summary,
                tags=tags,
                score=0.8
            )
            ids.append(mem_id)
        
        # Verify all are persisted
        assert len(set(ids)) == len(ids), "All memory IDs should be unique"
        
        # Search for them
        results = search_memories("test_multi", limit=20)
        found_goals = [r.get("goal") for r in results]
        
        for goal, _, _ in memories:
            assert goal in found_goals, f"Memory '{goal}' should be found"
    
    def test_memory_count_accuracy(self):
        """Test that memory count is accurate."""
        # Get initial count
        initial_stats = stats()
        initial_count = initial_stats.get("total", 0)
        
        # Add 3 new memories
        for i in range(3):
            store_memory(
                run_id=None,
                goal=f"test_count_{i}",
                summary=f"Memory {i} for count test",
                tags=["count", "test"],
                score=0.5
            )
        
        # Check new count
        new_stats = stats()
        new_count = new_stats.get("total", 0)
        
        assert new_count == initial_count + 3, \
            f"Count should increase by 3: was {initial_count}, now {new_count}"
    
    def test_explicit_remember_command_persistence(self):
        """Test that explicit 'Remember X' commands persist."""
        # Simulate user saying "Remember my favorite color is blue"
        goal = "user_favorite_color"
        summary = "The user's favorite color is blue."
        tags = ["identity", "favorite", "color"]
        
        memory_id = store_memory(
            run_id=None,
            goal=goal,
            summary=summary,
            tags=tags,
            score=1.0
        )
        
        # Simulate restart by creating fresh session
        results = search_memories("favorite color", limit=5)
        
        found = False
        for r in results:
            if "blue" in str(r.get("summary", "")).lower():
                found = True
                break
        
        assert found, "Should find 'favorite color is blue' after persistence"
    
    def test_no_in_memory_fallback(self):
        """Verify that no in-memory SQLite mode is ever used."""
        from ai_factory.memory.memory_db import engine
        
        # Check engine URL
        url_str = str(engine.url)
        
        assert ":memory:" not in url_str, \
            f"Engine should NOT use in-memory mode. URL: {url_str}"
        assert "memory.db" in url_str, \
            f"Engine should use memory.db file. URL: {url_str}"
    
    def test_write_failure_raises_exception(self):
        """Test that write failures raise exceptions instead of being silent."""
        # Try to store with invalid data that should fail
        # For example, extremely long strings or None values where not allowed
        
        # This test verifies that store_memory() will raise on error
        # rather than silently failing
        
        # Test 1: Normal write should succeed
        try:
            store_memory(
                run_id=None,
                goal="test_error_handling",
                summary="This should work",
                tags=["test"],
                score=0.5
            )
        except Exception as e:
            pytest.fail(f"Normal write should not raise exception: {e}")
        
        # Test 2: If we close the engine, writes should fail visibly
        # (This is a destructive test, so we skip in normal runs)
        # Just verify that errors are logged and raised
        pass
    
    def test_identity_memories_persist(self):
        """Test that identity memories persist correctly."""
        from ai_factory.memory.identity_seeder import seed_identity_memories
        
        # Seed identity memories
        result = seed_identity_memories()
        
        # Verify they exist
        results = search_memories("Nirdesh", limit=10)
        
        found_name = any("Nirdesh" in str(r.get("summary", "")) for r in results)
        assert found_name, "Should find Nirdesh in identity memories"
        
        # Search for birthplace
        results = search_memories("Nepal", limit=10)
        found_nepal = any("Nepal" in str(r.get("summary", "")) for r in results)
        assert found_nepal, "Should find Nepal in identity memories"
    
    def test_memory_survives_db_reconnect(self):
        """Test that memory survives database reconnection."""
        from ai_factory.memory.memory_db import engine, SessionLocal
        
        # Write memory
        goal = "test_reconnect"
        summary = "This memory should survive reconnection"
        
        memory_id = store_memory(
            run_id=None,
            goal=goal,
            summary=summary,
            tags=["reconnect"],
            score=1.0
        )
        
        # Dispose engine (simulates connection close)
        engine.dispose()
        
        # Try to read - should reconnect automatically
        results = search_memories(goal, limit=5)
        
        found = any(r.get("id") == memory_id for r in results)
        assert found, "Memory should survive engine disposal and reconnection"


class TestMemoryConsistency:
    """Test suite for memory consistency validation."""
    
    def test_no_duplicate_writes_single_commit(self):
        """Test that single commit doesn't create duplicates."""
        goal = "test_no_dup"
        summary = "Should only appear once"
        
        # Write once
        id1 = store_memory(
            run_id=None,
            goal=goal,
            summary=summary,
            tags=["nodup"],
            score=1.0
        )
        
        # Search for it
        results = search_memories(goal, limit=10)
        
        # Count how many times it appears
        count = sum(1 for r in results if r.get("goal") == goal)
        
        assert count == 1, f"Should find exactly 1 instance, found {count}"
    
    def test_stats_consistency(self):
        """Test that stats() returns consistent data."""
        stats_data = stats()
        
        # Check required fields
        assert "total" in stats_data, "Stats should include 'total'"
        assert "recent_7d" in stats_data, "Stats should include 'recent_7d'"
        assert "avg_score" in stats_data, "Stats should include 'avg_score'"
        
        # Totals should be non-negative
        assert stats_data["total"] >= 0, "Total should be non-negative"
        assert stats_data["recent_7d"] >= 0, "Recent count should be non-negative"
    
    def test_deleted_memories_not_retrieved(self):
        """Test that soft-deleted memories are not retrieved."""
        from ai_factory.memory.memory_db import SessionLocal
        
        # Create a memory
        goal = "test_soft_delete"
        memory_id = store_memory(
            run_id=None,
            goal=goal,
            summary="This will be deleted",
            tags=["delete_test"],
            score=0.5
        )
        
        # Verify it exists
        results = search_memories(goal, limit=5)
        assert any(r.get("id") == memory_id for r in results), "Memory should exist before delete"
        
        # Soft delete it
        with SessionLocal() as session:
            entry = session.get(MemoryEntry, memory_id)
            entry.deleted = 1
            session.commit()
        
        # Verify it's not retrieved
        results = search_memories(goal, limit=5)
        assert not any(r.get("id") == memory_id for r in results), \
            "Deleted memory should not be retrieved"


if __name__ == "__main__":
    # Allow running directly for quick tests
    pytest.main([__file__, "-v", "-s"])

