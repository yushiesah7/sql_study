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
        """
        エラーコード、メッセージ、タイムスタンプを含む標準化されたエラーレスポンス辞書を構築する。
        
        引数:
            error_code (str): エラータイプの識別子。
            message (str): エラーを説明する記述的メッセージ。
            detail (Optional[str]): 利用可能な場合、エラーに関する追加詳細。
            data (Optional[Dict[str, Any]]): 提供される場合、エラーに関連する補足データ。
        
        戻り値:
            Dict[str, Any]: コード、メッセージ、タイムスタンプ、オプションで詳細とデータを含むエラーレスポンスを表す辞書。
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