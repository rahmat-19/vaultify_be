"""HTTP security headers middleware."""

from collections.abc import Awaitable, Callable

from starlette.types import ASGIApp


class SecurityHeadersMiddleware:
    """Add defensive headers to every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict,
        receive: Callable[[], Awaitable[dict]],
        send: Callable[[dict], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        documentation_path = path in {
            "/docs",
            "/docs/oauth2-redirect",
            "/redoc",
            "/openapi.json",
        }
        content_security_policy = (
            b"default-src 'none'; "
            b"script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            b"style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            b"img-src 'self' data: https://fastapi.tiangolo.com; "
            b"font-src 'self' https://cdn.jsdelivr.net; "
            b"connect-src 'self'; frame-ancestors 'none'"
            if documentation_path
            else b"default-src 'none'; frame-ancestors 'none'"
        )

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (b"referrer-policy", b"no-referrer"),
                        (
                            b"permissions-policy",
                            b"camera=(), microphone=(), geolocation=()",
                        ),
                        (b"cache-control", b"no-store"),
                        (
                            b"content-security-policy",
                            content_security_policy,
                        ),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
