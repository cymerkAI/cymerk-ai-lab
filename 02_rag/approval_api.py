from fastapi import FastAPI, HTTPException

from approval_service import (
    approve_request,
    get_approval,
    list_pending_requests,
    reject_request,
)

app = FastAPI(
    title="Cymerk Approval API",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "approval-api",
    }


@app.get("/approvals/pending")
def pending_approvals():
    return list_pending_requests()


@app.get("/approvals/{approval_id}")
def approval_status(approval_id: str):
    result = get_approval(approval_id)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result,
        )

    return result


@app.post("/approvals/{approval_id}/approve")
def approve(approval_id: str):
    result = approve_request(approval_id)

    if not result["success"]:
        if result["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail=result,
            )

        if result["status"] == "already_resolved":
            raise HTTPException(
                status_code=409,
                detail=result,
            )

        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return result


@app.post("/approvals/{approval_id}/reject")
def reject(approval_id: str):
    result = reject_request(approval_id)

    if not result["success"]:
        if result["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail=result,
            )

        if result["status"] == "already_resolved":
            raise HTTPException(
                status_code=409,
                detail=result,
            )

        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return result
