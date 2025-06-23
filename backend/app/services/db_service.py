"""
データベース操作サービス
"""
import logging
from typing import List, Dict, Any, Optional
from app.core.db import Database
from app.core.exceptions import DatabaseError
from app.core.error_codes import (
    DB_CONNECTION_ERROR,
    DB_EXECUTION_ERROR,
    DB_SCHEMA_ERROR
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """データベース操作サービスクラス"""
    
    def __init__(self, db: Database):
        """
        Initialize the DatabaseService with a Database instance.
        """
        self.db = db
    
    async def initialize_system_schema(self):
        """
        Initialize the system schema and create the problems table if they do not exist.
        
        Raises:
            DatabaseError: If schema or table initialization fails.
        """
        try:
            # app_systemスキーマ作成
            await self.db.execute("""
                CREATE SCHEMA IF NOT EXISTS app_system
            """)
            
            # problemsテーブル作成
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS app_system.problems (
                    id SERIAL PRIMARY KEY,
                    theme VARCHAR(255) NOT NULL,
                    difficulty VARCHAR(20) NOT NULL,
                    correct_sql TEXT NOT NULL,
                    expected_result JSONB NOT NULL,
                    hint TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    table_schemas JSONB NOT NULL
                )
            """)
            
            logger.info("System schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system schema: {e}")
            raise DatabaseError(
                message="システムスキーマの初期化に失敗しました",
                error_code=DB_SCHEMA_ERROR,
                detail=str(e)
            )
    
    async def drop_all_user_tables(self):
        """
        Drops all user-created tables in the public schema.
        
        Raises:
            DatabaseError: If table deletion fails.
        """
        try:
            # publicスキーマのテーブル一覧を取得
            tables = await self.db.fetch_all("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            
            if tables:
                table_names = [table['table_name'] for table in tables]
                
                # CASCADEで全削除
                for table_name in table_names:
                    await self.db.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
                
                logger.info(f"Dropped {len(table_names)} user tables: {table_names}")
            
        except Exception as e:
            logger.error(f"Failed to drop user tables: {e}")
            raise DatabaseError(
                message="ユーザーテーブルの削除に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e)
            )
    
    async def execute_sql_statements(self, sql_statements: List[str]):
        """
        Executes a list of SQL statements sequentially.
        
        Parameters:
            sql_statements (List[str]): List of SQL statements to execute.
        
        Raises:
            DatabaseError: If execution of any SQL statement fails.
        """
        try:
            for sql in sql_statements:
                if sql.strip():
                    await self.db.execute(sql)
            
            logger.info(f"Executed {len(sql_statements)} SQL statements")
            
        except Exception as e:
            logger.error(f"Failed to execute SQL statements: {e}")
            raise DatabaseError(
                message="SQL文の実行に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e)
            )
    
    async def get_table_schemas(self) -> List[Dict[str, Any]]:
        """
        Retrieve the schema details of all base tables in the public schema.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the table name and a list of column definitions with type, nullability, primary key, and foreign key information.
        
        Raises:
            DatabaseError: If retrieval of table schemas fails.
        """
        try:
            # テーブル一覧を取得
            tables = await self.db.fetch_all("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            schemas = []
            for table in tables:
                table_name = table['table_name']
                
                # カラム情報を取得
                columns = await self.db.fetch_all("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                    ORDER BY ordinal_position
                """, table_name)
                
                # 主キー情報を取得
                primary_keys = await self.db.fetch_all("""
                    SELECT column_name
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.table_constraints tc 
                        ON kcu.constraint_name = tc.constraint_name
                    WHERE tc.table_schema = 'public' 
                    AND tc.table_name = $1
                    AND tc.constraint_type = 'PRIMARY KEY'
                """, table_name)
                
                pk_columns = {pk['column_name'] for pk in primary_keys}
                
                # 外部キー情報を取得
                foreign_keys = await self.db.fetch_all("""
                    SELECT 
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.key_column_usage kcu
                    JOIN information_schema.constraint_column_usage ccu
                        ON kcu.constraint_name = ccu.constraint_name
                    JOIN information_schema.table_constraints tc
                        ON kcu.constraint_name = tc.constraint_name
                    WHERE tc.table_schema = 'public'
                    AND tc.table_name = $1
                    AND tc.constraint_type = 'FOREIGN KEY'
                """, table_name)
                
                fk_dict = {
                    fk['column_name']: {
                        'table': fk['foreign_table_name'],
                        'column': fk['foreign_column_name']
                    }
                    for fk in foreign_keys
                }
                
                # カラム情報を整形
                formatted_columns = []
                for col in columns:
                    column_info = {
                        'name': col['column_name'],
                        'type': col['data_type'].upper(),
                        'nullable': col['is_nullable'] == 'YES',
                        'is_primary_key': col['column_name'] in pk_columns
                    }
                    
                    if col['column_name'] in fk_dict:
                        column_info['foreign_key'] = fk_dict[col['column_name']]
                    
                    formatted_columns.append(column_info)
                
                schemas.append({
                    'table_name': table_name,
                    'columns': formatted_columns
                })
            
            return schemas
            
        except Exception as e:
            logger.error(f"Failed to get table schemas: {e}")
            raise DatabaseError(
                message="テーブル構造の取得に失敗しました",
                error_code=DB_SCHEMA_ERROR,
                detail=str(e)
            )
    
    async def execute_select_query(self, sql: str, timeout: int = 5) -> List[Dict[str, Any]]:
        """
        Executes a SELECT SQL query with a specified timeout and returns the results as a list of dictionaries.
        
        Parameters:
            sql (str): The SELECT SQL query to execute.
            timeout (int, optional): The maximum number of seconds to wait for the query to complete. Defaults to 5.
        
        Returns:
            List[Dict[str, Any]]: The query results, where each row is represented as a dictionary.
        
        Raises:
            DatabaseError: If the query execution fails.
        """
        try:
            # タイムアウト付きで実行
            result = await self.db.fetch_all(sql, timeout=timeout)
            
            # 辞書形式に変換
            return [dict(row) for row in result]
            
        except Exception as e:
            logger.error(f"Failed to execute SELECT query: {e}")
            raise DatabaseError(
                message="SELECT文の実行に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e)
            )
    
    async def save_problem(
        self,
        theme: str,
        difficulty: str,
        correct_sql: str,
        expected_result: List[Dict[str, Any]],
        table_schemas: List[Dict[str, Any]],
        hint: Optional[str] = None
    ) -> int:
        """
        Save a new problem record to the database and return its unique ID.
        
        Parameters:
            theme (str): The theme or category of the problem.
            difficulty (str): The difficulty level of the problem.
            correct_sql (str): The correct SQL statement for the problem.
            expected_result (List[Dict[str, Any]]): The expected result set for the problem.
            table_schemas (List[Dict[str, Any]]): The table schemas relevant to the problem.
            hint (Optional[str]): An optional hint for solving the problem.
        
        Returns:
            int: The ID of the newly saved problem.
        
        Raises:
            DatabaseError: If saving the problem fails.
        """
        try:
            result = await self.db.fetch_one("""
                INSERT INTO app_system.problems 
                (theme, difficulty, correct_sql, expected_result, table_schemas, hint)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, theme, difficulty, correct_sql, expected_result, table_schemas, hint)
            
            problem_id = result['id']
            logger.info(f"Saved problem with ID: {problem_id}")
            return problem_id
            
        except Exception as e:
            logger.error(f"Failed to save problem: {e}")
            raise DatabaseError(
                message="問題の保存に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e)
            )
    
    async def get_problem(self, problem_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a problem record by its ID from the system problems table.
        
        Parameters:
            problem_id (int): The unique identifier of the problem to retrieve.
        
        Returns:
            dict: A dictionary containing the problem's details if found, or None if no such problem exists.
        
        Raises:
            DatabaseError: If retrieval from the database fails.
        """
        try:
            result = await self.db.fetch_one("""
                SELECT id, theme, difficulty, correct_sql, expected_result, 
                       table_schemas, hint, created_at
                FROM app_system.problems 
                WHERE id = $1
            """, problem_id)
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get problem {problem_id}: {e}")
            raise DatabaseError(
                message="問題の取得に失敗しました",
                error_code=DB_EXECUTION_ERROR,
                detail=str(e)
            )