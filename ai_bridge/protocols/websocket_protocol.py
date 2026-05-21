from __future__ import annotations


class WebSocketProtocol:
    """Placeholder adapter for projects that provide a websocket transport."""

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint

    def is_configured(self) -> bool:
        return bool(self.endpoint)
