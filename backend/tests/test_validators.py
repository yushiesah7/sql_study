"""
SQL検証機能のテスト
"""
import pytest
from app.core.validators import validate_sql
from app.core.error_codes import (
    VALIDATION_EMPTY_SQL,
    VALIDATION_SQL_TOO_LONG,
    VALIDATION_INVALID_SQL
)


class TestValidateSQL:
    """SQL検証のテストクラス"""
    
    def test_valid_select_statements(self):
        """
        Tests that various valid SELECT SQL statements are accepted by the validator.
        
        Verifies that simple and complex SELECT queries, including those with whitespace padding, are recognized as valid with no error code or message.
        """
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
        """
        Tests that valid SQL statements using WITH and WITH RECURSIVE clauses are accepted by the validator without errors.
        """
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
        """
        Tests that valid SQL subqueries, including those using UNION, are accepted as valid by the SQL validator.
        """
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
        """
        Tests that empty or whitespace-only SQL inputs, including None, are rejected as invalid.
        
        Verifies that the validator returns False, the VALIDATION_EMPTY_SQL error code, and an error message indicating no input was provided.
        """
        empty_sqls = ["", "   ", "\t\n", None]
        
        for sql in empty_sqls:
            is_valid, error_code, error_message = validate_sql(sql)
            assert is_valid is False
            assert error_code == VALIDATION_EMPTY_SQL
            assert "入力されていません" in error_message
    
    def test_sql_too_long(self):
        """
        Tests that excessively long SQL statements are rejected as invalid.
        
        Verifies that when a SQL statement exceeds the allowed length, `validate_sql` returns `False`, the `VALIDATION_SQL_TOO_LONG` error code, and an appropriate error message.
        """
        long_sql = "SELECT * FROM employees WHERE " + "age > 25 AND " * 1000 + "name IS NOT NULL"
        
        is_valid, error_code, error_message = validate_sql(long_sql)
        assert is_valid is False
        assert error_code == VALIDATION_SQL_TOO_LONG
        assert "長すぎます" in error_message
    
    def test_dangerous_statements(self):
        """
        Test that dangerous SQL statements such as DROP, CREATE, ALTER, TRUNCATE, DELETE, UPDATE, INSERT, GRANT, REVOKE, and EXECUTE are correctly identified as invalid by the SQL validator.
        
        Ensures that each dangerous command is rejected with the appropriate error code and message.
        """
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
            assert "実行できません" in error_message
    
    def test_multiple_statements(self):
        """
        Tests that SQL inputs containing multiple statements separated by semicolons are rejected as invalid.
        
        Ensures that the validator returns `False` with the `VALIDATION_INVALID_SQL` error code for each multi-statement input.
        """
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
        """
        Test that dangerous SQL commands are detected regardless of letter casing.
        
        Verifies that variations in capitalization of forbidden commands like "DROP TABLE" are correctly identified as invalid SQL statements.
        """
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
        """
        Tests that non-SELECT SQL statements are rejected by the validator with the appropriate error code and message.
        """
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
            assert "SELECT文のみ実行可能です" in error_message
    
    def test_sql_injection_attempts(self):
        """
        Tests that SQL injection attempts combining valid and dangerous commands are rejected, while complex but safe SQL statements such as subqueries and UNIONs are accepted.
        """
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
        """
        Tests that the SQL validator correctly handles edge cases such as minimal SELECT statements, queries with literals, newlines, and comments, ensuring they are accepted as valid.
        """
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