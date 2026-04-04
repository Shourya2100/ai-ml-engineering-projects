from fastapi import HTTPException


def bad_request(detail: str) -> HTTPException:
    raise HTTPException(status_code=400, detail=detail)


def not_found(detail: str) -> HTTPException:
    raise HTTPException(status_code=404, detail=detail)


def server_error(detail: str) -> HTTPException:
    raise HTTPException(status_code=500, detail=detail)
