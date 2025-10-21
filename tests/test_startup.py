from pathlib import Path


def test_directories_exist():
    for p in (Path('builds'), Path('deployments'), Path('logs'), Path('tests')):
        assert p.exists(), f"missing {p}"


def test_env_loaded():
    # .env may or may not exist; just ensure code can read env without crashing
    from ai_factory.config import settings
    assert hasattr(settings, 'host')

