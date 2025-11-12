import logging
from fastapi import APIRouter, HTTPException
from ai_factory.models import DispatchRequest, DispatchResponse, ErrorResponse
from ai_factory.services.planner_service import planner

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/planner", tags=["planner"])


@router.post("/dispatch", response_model=DispatchResponse, responses={400: {"model": ErrorResponse}})
def dispatch(req: DispatchRequest) -> DispatchResponse:
    """
    Accepts a prompt and task_type and returns a structured plan (stubbed).
    """
    try:
        logger.debug("Dispatch received: %s", req.model_dump())
        resp = planner.plan(req.prompt, req.task_type)
        return resp
    except ValueError as ve:
        logger.exception("Validation error")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Unexpected error in dispatch")
        raise HTTPException(status_code=500, detail="Internal planner error")
