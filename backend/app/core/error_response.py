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
        Constructs a standardized error response dictionary containing an error code, message, and timestamp.
        
        Parameters:
            error_code (str): The identifier for the error type.
            message (str): A descriptive message explaining the error.
            detail (Optional[str]): Additional details about the error, if available.
            data (Optional[Dict[str, Any]]): Supplementary data relevant to the error, if provided.
        
        Returns:
            Dict[str, Any]: A dictionary representing the error response, including code, message, timestamp, and optionally detail and data.
        """
        response = {
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        if detail:
            response["error"]["detail"] = detail
            
        if data:
            response["error"]["data"] = data
            
        return response