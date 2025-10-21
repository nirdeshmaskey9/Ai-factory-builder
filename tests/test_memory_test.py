from ai_factory.memory.memory_db import init_db, store_evaluation, get_session, EvaluationResult


def test_memory_store_and_read_evaluation():
    init_db()
    build_id = "test_build_123"
    store_evaluation(build_id, "cli", True, "ok", {"k": 1})
    sess = get_session()
    try:
        rows = list(sess.query(EvaluationResult).filter_by(build_id=build_id))
        assert rows, "no rows stored"
        assert rows[-1].summary
    finally:
        sess.close()

