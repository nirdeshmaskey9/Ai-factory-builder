"""
Identity Memory Seeder
Ensures core identity memories exist in the database.
Runs on startup to guarantee JoJo always has access to user identity.
"""

from __future__ import annotations

from typing import List, Dict, Optional
from sqlalchemy import select, and_
from ai_factory.memory.memory_agent import store_memory, search_memories
from ai_factory.memory.memory_db import SessionLocal, MemoryEntry, init_db


# Core identity memories that must always exist
IDENTITY_MEMORIES = [
    {
        "goal": "user_full_name",
        "summary": "The user's full name is Nirdesh Maskey.",
        "tags": ["identity", "name", "user", "core"],
        "score": 1.0,
    },
    {
        "goal": "user_birthdate",
        "summary": "Nirdesh was born on July 8, 2001.",
        "tags": ["identity", "birthdate", "birth", "core"],
        "score": 1.0,
    },
    {
        "goal": "user_birthplace",
        "summary": "Nirdesh was born in Kathmandu, Nepal.",
        "tags": ["identity", "birthplace", "birth", "core", "location"],
        "score": 1.0,
    },
    {
        "goal": "user_country",
        "summary": "Nirdesh is from Nepal.",
        "tags": ["identity", "country", "location", "core"],
        "score": 1.0,
    },
    {
        "goal": "user_current_location",
        "summary": "Nirdesh currently lives in Milwaukee, Wisconsin, USA.",
        "tags": ["identity", "location", "current", "core"],
        "score": 0.9,
    },
    {
        "goal": "user_profession",
        "summary": "Nirdesh is a Filmmaker, Video Editor, Photographer, and AI Creator.",
        "tags": ["identity", "profession", "work", "core"],
        "score": 0.9,
    },
    {
        "goal": "user_education",
        "summary": "Nirdesh is a student at Milwaukee Area Technical College (MATC).",
        "tags": ["identity", "education", "student", "core"],
        "score": 0.9,
    },
]


def seed_identity_memories() -> Dict[str, int]:
    """
    Ensure all core identity memories exist in the database.
    Only creates memories that don't already exist (by goal).
    Commits once at the end.
    
    Returns:
        Dict with counts: {"inserted": int, "skipped": int, "errors": int, "total": int}
    """
    init_db()
    inserted = 0
    skipped = 0
    errors = 0
    
    with SessionLocal() as session:
        for mem in IDENTITY_MEMORIES:
            try:
                # Check if memory with this goal already exists
                existing_mem = session.scalars(
                    select(MemoryEntry).where(
                        and_(
                            MemoryEntry.goal == mem["goal"],
                            MemoryEntry.deleted == 0
                        )
                    ).limit(1)
                ).first()
                
                if existing_mem:
                    skipped += 1
                else:
                    # Create the memory directly in this session
                    from ai_factory.memory.memory_agent import _norm_tags
                    new_entry = MemoryEntry(
                        run_id=None,
                        goal=str(mem["goal"]).strip(),
                        summary=str(mem["summary"]).strip(),
                        tags=_norm_tags(mem["tags"]),
                        score=mem["score"],
                    )
                    session.add(new_entry)
                    inserted += 1
            except Exception as e:
                errors += 1
                try:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to seed identity memory {mem.get('goal', 'unknown')}: {e}")
                except Exception:
                    pass
        
        # Commit once at the end
        try:
            session.commit()
        except Exception as e:
            errors += 1
            try:
                import logging
                logging.getLogger(__name__).error(f"Failed to commit identity memories: {e}")
                session.rollback()
            except Exception:
                pass
    
    return {
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "total": len(IDENTITY_MEMORIES),
    }


def verify_identity_memories() -> Dict[str, any]:
    """
    Verify that identity memories exist and can be retrieved.
    
    Returns:
        Dict with verification results
    """
    results = {
        "verified": [],
        "missing": [],
        "search_tests": {},
    }
    
    # Test searches for each identity aspect
    test_queries = [
        ("full name", "user_full_name"),
        ("birthdate", "user_birthdate"),
        ("birthplace", "user_birthplace"),
        ("country", "user_country"),
        ("Nirdesh", "user_full_name"),
        ("Nepal", "user_country"),
        ("July 8", "user_birthdate"),
        ("Kathmandu", "user_birthplace"),
    ]
    
    for query, expected_goal in test_queries:
        found = search_memories(query, limit=5)
        found_goals = [m.get("goal") for m in found]
        results["search_tests"][query] = {
            "found": expected_goal in found_goals,
            "results_count": len(found),
            "top_result": found[0].get("goal") if found else None,
        }
    
    # Check if all identity memories exist
    from sqlalchemy import and_
    with SessionLocal() as session:
        for mem in IDENTITY_MEMORIES:
            existing = session.scalars(
                select(MemoryEntry).where(
                    and_(
                        MemoryEntry.goal == mem["goal"],
                        MemoryEntry.deleted == 0
                    )
                ).limit(1)
            ).first()
            
            if existing:
                results["verified"].append(mem["goal"])
            else:
                results["missing"].append(mem["goal"])
    
    return results

