# Migration Guide: v1.2-master – Universal Builder MVP

This release introduces a domain-aware, modular builder pipeline while preserving backward compatibility with v1.x micro-apps.

Key changes:
- Domain detection: `ai_factory/core/domain_detector.py`
- Modular builders: `ai_factory/builders/{web,cli,ml}` with templates under `ai_factory/templates/{domain}/`
- Factory route: `POST /factory/create` defined in `ai_factory/orchestrator/factory_routes.py`
- Evaluator suites: `ai_factory/evaluator/suites/*.py` and `EvaluationRunner`
- Compatibility adapter: `ai_factory/compat/v1_adapter.py`
- Build outputs: `builds/<build_id>/{manifest.json,inputs/,outputs/,logs/}`
- Master ADR logs: `deployments/factory_master_log_<timestamp>.md`

Versioning:
- Root `VERSION` now set to `1.2-master`.
- `/factory/info` reports `version` from `VERSION`.

Notes:
- Existing watchdog, PID tracking, and env validation are preserved.
- No v1 templates were modified; v2 additions are isolated.

