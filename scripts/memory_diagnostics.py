#!/usr/bin/env python3
"""
Memory Diagnostics Script
Tests memory persistence, retrieval, and identity recall.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_factory.memory.memory_agent import search_memories, store_memory, stats
from ai_factory.memory.memory_db import init_db, SessionLocal, MemoryEntry, select, and_
from ai_factory.memory.identity_seeder import seed_identity_memories, verify_identity_memories


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_memory_storage():
    """Test that memory can be stored and retrieved."""
    print_section("TEST 1: Memory Storage")
    
    # Store a test memory
    test_id = store_memory(
        run_id=None,
        goal="test_memory_persistence",
        summary="This is a test memory to verify persistence works.",
        tags=["test", "diagnostics"],
        score=0.5,
    )
    print(f"✅ Stored test memory with ID: {test_id}")
    
    # Retrieve it
    results = search_memories("test_memory_persistence", limit=5)
    found = any(m.get("goal") == "test_memory_persistence" for m in results)
    
    if found:
        print("✅ Test memory retrieved successfully")
    else:
        print("❌ Test memory NOT found after storage")
    
    return found


def test_identity_recall():
    """Test that identity memories can be recalled."""
    print_section("TEST 2: Identity Memory Recall")
    
    test_queries = [
        ("Who am I?", "Nirdesh"),
        ("When was I born?", "July 8, 2001"),
        ("Where was I born?", "Kathmandu"),
        ("Which country am I from?", "Nepal"),
        ("What is my name?", "Nirdesh Maskey"),
    ]
    
    all_passed = True
    for query, expected_keyword in test_queries:
        results = search_memories(query, limit=5)
        found_text = " ".join([m.get("summary", "") for m in results]).lower()
        
        if expected_keyword.lower() in found_text:
            print(f"✅ '{query}' → Found '{expected_keyword}'")
        else:
            print(f"❌ '{query}' → Missing '{expected_keyword}'")
            print(f"   Results: {[m.get('summary')[:50] for m in results[:2]]}")
            all_passed = False
    
    return all_passed


def test_similarity_search():
    """Test semantic similarity search."""
    print_section("TEST 3: Similarity Search")
    
    test_phrases = [
        "birthday",
        "birthplace",
        "Nepal",
        "Nirdesh Maskey",
        "Kathmandu",
    ]
    
    for phrase in test_phrases:
        results = search_memories(phrase, limit=3)
        print(f"  '{phrase}': {len(results)} results")
        if results:
            print(f"    Top: {results[0].get('summary')[:60]}...")


def print_all_memories():
    """Print all stored memories."""
    print_section("ALL STORED MEMORIES")
    
    init_db()
    with SessionLocal() as session:
        all_memories = session.scalars(
            select(MemoryEntry).where(MemoryEntry.deleted == 0).order_by(MemoryEntry.created_at.desc())
        ).all()
        
        print(f"Total memories: {len(all_memories)}\n")
        
        for mem in all_memories[:20]:  # Show first 20
            print(f"  [{mem.id}] {mem.goal}")
            print(f"      {mem.summary[:80]}...")
            print(f"      Tags: {mem.tags}, Score: {mem.score}")
            print()


def check_database_files():
    """Check that database files exist."""
    print_section("DATABASE FILES CHECK")
    
    db_path = project_root / "data" / "memory.db"
    chroma_path = project_root / "data" / "app-internal" / "chroma"
    
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"✅ SQLite DB exists: {db_path} ({size:,} bytes)")
    else:
        print(f"❌ SQLite DB missing: {db_path}")
    
    if chroma_path.exists():
        print(f"✅ ChromaDB directory exists: {chroma_path}")
    else:
        print(f"⚠️  ChromaDB directory missing: {chroma_path}")


def main():
    """Run all diagnostics."""
    print("\n" + "="*60)
    print("  JOJO MEMORY DIAGNOSTICS")
    print("="*60)
    
    # Initialize database
    init_db()
    print("\n✅ Database initialized")
    
    # Check files
    check_database_files()
    
    # Seed identity memories
    print_section("SEEDING IDENTITY MEMORIES")
    seed_result = seed_identity_memories()
    print(f"Created: {seed_result['created']}, Existing: {seed_result['existing']}, Total: {seed_result['total']}")
    
    # Verify identity memories
    print_section("VERIFYING IDENTITY MEMORIES")
    verify_result = verify_identity_memories()
    print(f"Verified: {len(verify_result['verified'])}/{len(verify_result['verified']) + len(verify_result['missing'])}")
    if verify_result['missing']:
        print(f"⚠️  Missing: {verify_result['missing']}")
    
    # Print search test results
    print("\nSearch Test Results:")
    for query, result in verify_result['search_tests'].items():
        status = "✅" if result['found'] else "❌"
        print(f"  {status} '{query}': {result['results_count']} results")
    
    # Run tests
    storage_ok = test_memory_storage()
    identity_ok = test_identity_recall()
    test_similarity_search()
    
    # Print stats
    print_section("MEMORY STATISTICS")
    stats_data = stats()
    print(f"Total memories: {stats_data.get('total', 0)}")
    print(f"Recent (7 days): {stats_data.get('recent', 0)}")
    
    # Print all memories
    print_all_memories()
    
    # Summary
    print_section("SUMMARY")
    if storage_ok and identity_ok:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
    
    return 0 if (storage_ok and identity_ok) else 1


if __name__ == "__main__":
    sys.exit(main())

