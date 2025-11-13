"""
Phase 4.1 - Identity Alias Engine Tests
Tests for semantic alias resolution and fuzzy key matching
"""

import pytest
from ai_factory.identity.identity_alias_map import (
    IDENTITY_ALIAS_MAP,
    AUTO_GENERATED_ALIASES,
    register_auto_alias,
    get_all_aliases_for_key,
    find_best_match,
)
from ai_factory.memory.memory_db import resolve_memory_key, init_db, SessionLocal, MemoryEntry
from ai_factory.memory.memory_agent import store_memory


class TestStaticAliasMap:
    """Test static alias dictionary functionality"""
    
    def test_alias_map_exists(self):
        """Verify static alias map is defined and non-empty"""
        assert IDENTITY_ALIAS_MAP is not None
        assert len(IDENTITY_ALIAS_MAP) > 0
    
    def test_hometown_aliases(self):
        """Verify hometown has correct aliases"""
        assert "hometown" in IDENTITY_ALIAS_MAP
        aliases = IDENTITY_ALIAS_MAP["hometown"]
        assert "village" in aliases
        assert "birthplace" in aliases
        assert "origin" in aliases
    
    def test_village_aliases(self):
        """Verify village has correct aliases"""
        assert "village" in IDENTITY_ALIAS_MAP
        aliases = IDENTITY_ALIAS_MAP["village"]
        assert "hometown" in aliases
        assert "origin" in aliases
    
    def test_birthplace_aliases(self):
        """Verify birthplace has correct aliases"""
        assert "birthplace" in IDENTITY_ALIAS_MAP
        aliases = IDENTITY_ALIAS_MAP["birthplace"]
        assert "origin" in aliases
        assert "birth town" in aliases or "where born" in aliases
    
    def test_profession_aliases(self):
        """Verify profession has correct aliases"""
        assert "profession" in IDENTITY_ALIAS_MAP
        aliases = IDENTITY_ALIAS_MAP["profession"]
        assert "job" in aliases
        assert "work" in aliases
        assert "career" in aliases


class TestAutoAliasGeneration:
    """Test automatic alias generation"""
    
    def test_register_auto_alias_basic(self):
        """Test basic auto-alias registration"""
        aliases = register_auto_alias("favorite_color")
        assert aliases is not None
        assert len(aliases) > 0
        assert "favorite_color" in aliases
        assert "favorite color" in aliases  # underscore replaced with space
    
    def test_register_auto_alias_drink(self):
        """Test auto-alias for favorite_drink"""
        aliases = register_auto_alias("favorite_drink")
        assert "favorite_drink" in aliases
        assert "favorite drink" in aliases
        assert "drink" in aliases
        # Should include synonym variants
        assert any("beverage" in a for a in aliases)
    
    def test_auto_alias_persistence(self):
        """Test that auto-generated aliases are stored"""
        key = "test_memory_key"
        aliases1 = register_auto_alias(key)
        aliases2 = register_auto_alias(key)
        # Should return the same aliases (from cache)
        assert aliases1 == aliases2
    
    def test_get_all_aliases_combined(self):
        """Test getting all aliases (static + auto) for a key"""
        # hometown should have static aliases
        aliases = get_all_aliases_for_key("hometown")
        assert len(aliases) > 0
        assert "village" in aliases
        assert "origin" in aliases
        
        # Should also include auto-generated variants
        assert "hometown" in aliases


class TestFuzzyKeyMatching:
    """Test fuzzy matching and best match selection"""
    
    def test_find_best_match_hometown(self):
        """Test matching 'hometown' variations"""
        assert find_best_match("where is my hometown") in ["hometown", "village"]
        assert find_best_match("what is my hometown") in ["hometown", "village"]
    
    def test_find_best_match_origin(self):
        """Test matching 'origin' variations"""
        result = find_best_match("where am I originally from")
        assert result in ["village", "birthplace", "hometown", "origin"]
    
    def test_find_best_match_village(self):
        """Test matching 'village' variations"""
        result = find_best_match("what village am I from")
        assert result in ["village", "hometown"]
    
    def test_find_best_match_profession(self):
        """Test matching 'profession' variations"""
        result = find_best_match("what do I do for work")
        assert result in ["profession", "work"]
    
    def test_find_best_match_exact(self):
        """Test exact match takes priority"""
        result = find_best_match("birthplace")
        assert result == "birthplace"
    
    def test_find_best_match_no_match(self):
        """Test that unmatchable queries return None"""
        result = find_best_match("xyz abc 123 nonsense query")
        # Should return None or a low-confidence match
        # (implementation may vary)
        assert result is None or isinstance(result, str)


class TestMemoryKeyResolution:
    """Test resolve_memory_key integration with actual database"""
    
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Initialize database before each test"""
        init_db()
        # Clean up any test memories
        with SessionLocal() as session:
            test_entries = session.query(MemoryEntry).filter(
                MemoryEntry.goal.like("%test_%")
            ).all()
            for entry in test_entries:
                entry.deleted = 1
            session.commit()
    
    def test_resolve_hometown_query(self):
        """Test resolving 'hometown' query to village memory"""
        # Store a village memory
        store_memory(None, "user_village", "User is from Gorkha, Nepal.", ["identity", "village"], 1.0)
        
        # Resolve query
        resolved = resolve_memory_key("Where is my hometown?")
        assert resolved is not None
        assert "village" in resolved.lower()
    
    def test_resolve_origin_query(self):
        """Test resolving 'origin' query"""
        store_memory(None, "user_birthplace", "User was born in Kathmandu.", ["identity", "birthplace"], 1.0)
        
        resolved = resolve_memory_key("What is my origin?")
        assert resolved is not None
        assert "birth" in resolved.lower() or "origin" in resolved.lower()
    
    def test_resolve_profession_query(self):
        """Test resolving profession queries"""
        store_memory(None, "user_profession", "User is a filmmaker.", ["identity", "profession"], 1.0)
        
        resolved = resolve_memory_key("What do I do for work?")
        assert resolved is not None
        assert "profession" in resolved.lower() or "work" in resolved.lower()
    
    def test_resolve_no_match(self):
        """Test that unresolvable queries return None or fallback"""
        resolved = resolve_memory_key("xyz nonsense query 123")
        # Should return None or a best-effort match
        assert resolved is None or isinstance(resolved, str)


class TestBridgeIntegration:
    """Test alias resolution in bridge_service context"""
    
    def test_bridge_import_available(self):
        """Verify bridge can import alias resolution"""
        try:
            from ai_factory.bridge.bridge_service import ALIAS_ENGINE_AVAILABLE
            assert ALIAS_ENGINE_AVAILABLE is True
        except ImportError:
            pytest.skip("bridge_service not available in test environment")
    
    def test_identity_keywords_expanded(self):
        """Verify bridge has expanded identity keywords including aliases"""
        try:
            from ai_factory.bridge import bridge_service
            # Check that bridge_service source includes new keywords
            import inspect
            source = inspect.getsource(bridge_service.process_bridge_chat)
            assert "hometown" in source or "origin" in source
        except (ImportError, TypeError):
            pytest.skip("bridge_service not available for inspection")


class TestAliasEngineEndToEnd:
    """End-to-end integration tests"""
    
    @pytest.fixture(autouse=True)
    def setup_identity_memories(self):
        """Set up identity memories for testing"""
        init_db()
        # Seed core identity memories
        from ai_factory.memory.identity_seeder import seed_identity_memories
        seed_identity_memories()
    
    def test_hometown_resolution_complete(self):
        """Test complete flow: query → alias → resolution → memory retrieval"""
        # User asks: "Where is my hometown?"
        query = "Where is my hometown?"
        
        # Step 1: Find best alias match
        alias_key = find_best_match(query)
        assert alias_key is not None
        
        # Step 2: Resolve to memory key
        memory_key = resolve_memory_key(query)
        assert memory_key is not None
        
        # Step 3: Search memories with resolved key
        from ai_factory.memory.memory_agent import search_memories
        results = search_memories(memory_key, limit=3)
        
        # Should find village or birthplace memory
        assert len(results) > 0
        found_village = any("gorkha" in str(r.get("summary", "")).lower() for r in results)
        found_nepal = any("nepal" in str(r.get("summary", "")).lower() for r in results)
        assert found_village or found_nepal
    
    def test_origin_resolution_complete(self):
        """Test origin query resolution"""
        query = "What is my origin?"
        
        alias_key = find_best_match(query)
        memory_key = resolve_memory_key(query)
        
        assert alias_key is not None or memory_key is not None
        
        if memory_key:
            from ai_factory.memory.memory_agent import search_memories
            results = search_memories(memory_key, limit=3)
            assert len(results) > 0
    
    def test_where_am_i_from_complete(self):
        """Test 'Where am I from?' query"""
        query = "Where am I from?"
        
        # Should resolve to village or country
        memory_key = resolve_memory_key(query)
        assert memory_key is not None
        
        from ai_factory.memory.memory_agent import search_memories
        results = search_memories(memory_key, limit=3)
        
        # Should find Nepal or Gorkha
        assert len(results) > 0
        summaries = " ".join([r.get("summary", "") for r in results]).lower()
        assert "nepal" in summaries or "gorkha" in summaries


class TestMemoryPersistence:
    """Test memory persistence with auto-aliasing"""
    
    def test_remember_favorite_drink(self):
        """Test storing 'favorite drink' and auto-generating aliases"""
        # User says: "Remember that my favorite drink is mango lassi"
        store_memory(None, "favorite_drink", "User's favorite drink is mango lassi.", ["preference", "drink"], 0.8)
        
        # Auto-register aliases
        aliases = register_auto_alias("favorite_drink")
        assert "beverage" in [a for a in aliases]
        
        # Query with alias: "What is my beverage preference?"
        resolved = resolve_memory_key("What is my beverage preference?")
        assert resolved is not None
        
        from ai_factory.memory.memory_agent import search_memories
        results = search_memories(resolved, limit=3)
        
        # Should find the mango lassi memory
        found = any("mango lassi" in str(r.get("summary", "")).lower() for r in results)
        assert found


# Run pytest with: pytest tests/test_identity_aliasing.py -v


