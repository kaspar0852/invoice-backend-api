import json
from fastapi.routing import APIRoute
from fastapi.responses import Response, JSONResponse
from fastapi import Request
from typing import Callable, Coroutine, Any


class StandardAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            response = await original_route_handler(request)

            path = request.url.path
            if path == "/openapi.json" or path.endswith("/openapi.json"):
                return response

            if isinstance(response, Response) and response.media_type == "application/json":
                if 200 <= response.status_code < 300:
                    try:
                        body = json.loads(response.body)
                        wrapped_body = {
                            "success": True,
                            "status": response.status_code,
                            "result": body
                        }
                        headers = dict(response.headers)
                        headers.pop("content-length", None)
                        return JSONResponse(
                            content=wrapped_body,
                            status_code=response.status_code,
                            headers=headers
                        )
                    except Exception:
                        pass
            return response

        return custom_route_handler
