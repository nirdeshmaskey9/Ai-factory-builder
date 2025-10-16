from ai_factory.services.orchestrator_service import success_threshold


def test_adaptive_threshold_variation(monkeypatch):
    monkeypatch.setattr(
        "ai_factory.services.evaluator_v2_service.get_average_reward", lambda: 0.2
    )
    assert abs(success_threshold() - 0.45) < 0.01

    monkeypatch.setattr(
        "ai_factory.services.evaluator_v2_service.get_average_reward", lambda: 0.7
    )
    assert abs(success_threshold() - 0.65) < 0.01

    monkeypatch.setattr(
        "ai_factory.services.evaluator_v2_service.get_average_reward", lambda: 0.5
    )
    assert abs(success_threshold() - 0.55) < 0.01

