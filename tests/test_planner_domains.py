from ai_factory.services.planner_service import create_blueprint
from ai_factory.planner.planner_agent import plan_for_domain


def test_planner_blueprint_web():
    bp = create_blueprint("web", "hello")
    assert bp["name"] == "hello_web"
    assert "pages" in bp


def test_planner_blueprint_cli():
    bp = create_blueprint("cli", "hello")
    assert bp["name"] == "cli_app"
    assert "entry" in bp


def test_planner_blueprint_ml():
    bp = create_blueprint("ml", "hello")
    assert bp["name"] == "ml_project"
    assert "model" in bp


def test_planner_unknown_domain():
    try:
        create_blueprint("unknown", "x")
    except ValueError as e:
        assert "Unknown domain" in str(e)
    else:
        assert False, "expected ValueError"


def test_planner_agent_domains():
    for d in ("web", "cli", "ml", "data", "automation", "desktop"):
        plan = plan_for_domain(d, "goal")
        assert plan["domain"] == d
        assert isinstance(plan.get("steps"), list) and plan["steps"], "steps required"

    try:
        plan_for_domain("unknown", "x")
    except ValueError:
        pass
    else:
        assert False, "expected ValueError"
