"""
エラーレスポンスビルダー
"""

from datetime import UTC, datetime
from typing import Any


class ErrorResponseBuilder:
    """エラーレスポンスの構築"""

    @staticmethod
    def build(
        error_code: str,
        message: str,
        detail: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        統一されたエラーレスポンスを構築
        """
        response: dict[str, Any] = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }

        if detail:
            response["error"]["detail"] = detail

        if data:
            response["error"]["data"] = data

        return response
