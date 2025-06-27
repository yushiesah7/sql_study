"""
SQL検証機能のテスト
"""

from app.core.error_codes import (
    VALIDATION_EMPTY_SQL,
    VALIDATION_INVALID_SQL,
    VALIDATION_SQL_TOO_LONG,
)
from app.core.validators import validate_sql


class TestValidateSQL:
    """SQL検証のテストクラス"""

    def test_valid_select_statements(self):
        """有効なSELECT文のテスト"""
        valid_sqls = [
            "SELECT * FROM employees",
            "SELECT name, age FROM users WHERE age > 25",
            "SELECT COUNT(*) FROM orders",
            "SELECT e.name, d.department FROM employees e JOIN departments d ON e.dept_id = d.id",
            "  SELECT * FROM products  ",  # 前後の空白
        ]

        for sql in valid_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is True, f"SQL should be valid: {sql}"
            assert error_code is None
            assert error_message is None

    def test_valid_with_statements(self):
        """有効なWITH文のテスト"""
        valid_sqls = [
            "WITH ranked AS (SELECT *, ROW_NUMBER() OVER(ORDER BY salary) FROM employees) SELECT * FROM ranked",
            "WITH RECURSIVE factorial AS (SELECT 1 as n, 1 as result) SELECT * FROM factorial",
        ]

        for sql in valid_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is True, f"WITH statement should be valid: {sql}"
            assert error_code is None
            assert error_message is None

    def test_valid_subqueries(self):
        """有効なサブクエリのテスト"""
        valid_sqls = [
            "(SELECT * FROM employees WHERE age > 30)",
            "(SELECT name FROM users) UNION (SELECT name FROM admins)",
        ]

        for sql in valid_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is True, f"Subquery should be valid: {sql}"
            assert error_code is None
            assert error_message is None

    def test_empty_sql(self):
        """空のSQLのテスト"""
        empty_sqls = ["", "   ", "\t\n"]

        for sql in empty_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is False
            assert error_code == VALIDATION_EMPTY_SQL
            assert error_message is not None
            assert "入力されていません" in error_message

        # Noneの場合は別途テスト
        is_valid, error_code, error_message = validate_sql(None)  # type: ignore
        assert is_valid is False
        assert error_code == VALIDATION_EMPTY_SQL
        assert error_message is not None
        assert "入力されていません" in error_message

    def test_sql_too_long(self):
        """SQLが長すぎる場合のテスト"""
        long_sql = (
            "SELECT * FROM employees WHERE "
            + "age > 25 AND " * 1000
            + "name IS NOT NULL"
        )

        is_valid, error_code, error_message = validate_sql(long_sql)
        assert is_valid is False
        assert error_code == VALIDATION_SQL_TOO_LONG
        assert error_message is not None
        assert "長すぎます" in error_message

    def test_dangerous_statements(self):
        """危険なSQL文のテスト"""
        dangerous_sqls = [
            "DROP TABLE employees",
            "CREATE TABLE test (id INT)",
            "ALTER TABLE users ADD COLUMN test VARCHAR(50)",
            "TRUNCATE TABLE logs",
            "DELETE FROM users WHERE id = 1",
            "UPDATE users SET name = 'hacker' WHERE id = 1",
            "INSERT INTO users (name) VALUES ('malicious')",
            "GRANT ALL ON users TO attacker",
            "REVOKE SELECT ON users FROM user1",
            "EXECUTE sp_dangerous_procedure",
            "EXEC xp_cmdshell 'del *.*'",
        ]

        for sql in dangerous_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is False, f"Dangerous SQL should be invalid: {sql}"
            assert error_code == VALIDATION_INVALID_SQL
            assert error_message is not None
            assert "実行できません" in error_message

    def test_multiple_statements(self):
        """複数ステートメントのテスト"""
        multiple_sqls = [
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT name FROM employees; DELETE FROM logs;",
            "SELECT 1; SELECT 2;",
        ]

        for sql in multiple_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is False, f"Multiple statements should be invalid: {sql}"
            assert error_code == VALIDATION_INVALID_SQL

    def test_case_insensitive_detection(self):
        """大文字小文字を問わない検出のテスト"""
        case_variations = [
            "drop table users",
            "Drop Table users",
            "DROP table users",
            "dRoP tAbLe users",
        ]

        for sql in case_variations:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is False, f"Case variation should be detected: {sql}"
            assert error_code == VALIDATION_INVALID_SQL

    def test_non_select_statements(self):
        """SELECT以外の文のテスト"""
        non_select_sqls = [
            "SHOW TABLES",
            "DESCRIBE employees",
            "EXPLAIN SELECT * FROM users",
            "USE database_name",
        ]

        for sql in non_select_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is False, f"Non-SELECT statement should be invalid: {sql}"
            assert error_code == VALIDATION_INVALID_SQL
            assert error_message is not None
            assert "SELECT文のみ実行可能です" in error_message

    def test_sql_injection_attempts(self):
        """SQLインジェクション試行のテスト"""
        dangerous_attempts = [
            "SELECT * FROM users WHERE id = 1; DROP TABLE users; --",
            "SELECT * FROM products WHERE price < 100; DELETE FROM orders; /*",
        ]

        safe_but_complex = [
            "SELECT *, (SELECT password FROM admin WHERE id=1) FROM users",  # サブクエリは許可
            "SELECT * FROM users UNION SELECT * FROM admin_passwords",  # UNIONは許可
        ]

        # 危険なものは拒否されるべき
        for sql in dangerous_attempts:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is False, f"Dangerous SQL should be blocked: {sql}"

        # 複雑だが安全なものは許可されるべき
        for sql in safe_but_complex:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is True, f"Complex but safe SQL should be allowed: {sql}"

    def test_edge_cases(self):
        """エッジケースのテスト"""
        edge_cases = [
            ("SELECT", True),  # 最小のSELECT文
            ("SELECT 1", True),  # シンプルなSELECT
            ("SELECT\n*\nFROM\nusers", True),  # 改行を含む
            ("SELECT /* comment */ * FROM users", True),  # コメント付き
        ]

        for sql, should_be_valid in edge_cases:
            is_valid, error_code, error_message = validate_sql(sql)
            if should_be_valid:
                assert is_valid is True, f"Edge case should be valid: {sql}"
                assert error_code is None
            else:
                assert is_valid is False, f"Edge case should be invalid: {sql}"
                assert error_code is not None
