from typing import Any
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class GenericResponse(BaseModel):
    code: int
    message: str | None
    data: Any

    def to_json_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.code, content=self.model_dump())
