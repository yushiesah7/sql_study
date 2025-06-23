"""
SQL検証関数
"""
import re
from typing import Tuple, Optional
from .error_codes import VALIDATION_EMPTY_SQL, VALIDATION_SQL_TOO_LONG, VALIDATION_INVALID_SQL

# 危険なSQL文のパターン
DANGEROUS_PATTERNS = [
    r'\b(DROP|CREATE|ALTER|TRUNCATE|DELETE|UPDATE|INSERT)\b',
    r'\b(GRANT|REVOKE|EXECUTE|EXEC)\b',
    r';\s*\w+',  # 複数ステートメント
]

# 許可するSQL文のパターン  
ALLOWED_PATTERNS = [
    r'^\s*SELECT\s+',
    r'^\s*WITH\s+.+\s+SELECT\s+',
    r'^\s*\(\s*SELECT\s+',  # サブクエリ
]

def validate_sql(sql: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    SQLの安全性を検証
    
    Returns:
        (is_valid, error_code, error_message)
    """
    if not sql or not sql.strip():
        return False, VALIDATION_EMPTY_SQL, "SQLが入力されていません"
    
    sql_upper = sql.upper().strip()
    
    # 長さチェック
    if len(sql) > 5000:
        return False, VALIDATION_SQL_TOO_LONG, f"SQLが長すぎます（最大5000文字）"
    
    # 危険なパターンチェック
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, sql_upper):
            match = re.search(pattern, sql_upper)
            statement = match.group(1) if match else "不明"
            return False, VALIDATION_INVALID_SQL, f"{statement}文は実行できません"
    
    # 許可パターンチェック
    valid = any(re.match(pattern, sql_upper) for pattern in ALLOWED_PATTERNS)
    if not valid:
        return False, VALIDATION_INVALID_SQL, "SELECT文のみ実行可能です"
    
    return True, None, None