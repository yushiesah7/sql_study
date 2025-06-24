"""
エラーレスポンスビルダー
"""
from typing import Dict, Any, Optional
from datetime import datetime


class ErrorResponseBuilder:
    """エラーレスポンスの構築"""
    
    @staticmethod
    def build(
        error_code: str,
        message: str,
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        統一されたエラーレスポンスを構築
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if detail:
            response["error"]["detail"] = detail
            
        if data:
            response["error"]["data"] = data
            
        return response