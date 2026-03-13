from fastapi import HTTPException


class AppException(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


class NotFoundException(AppException):
    def __init__(self, resource: str, identifier: int):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} with id {identifier} not found",
            status_code=404
        )
