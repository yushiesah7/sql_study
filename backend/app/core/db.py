"""
PostgreSQL接続管理
"""
import asyncio
import asyncpg
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class Database:
    """データベース接続管理クラス"""
    
    def __init__(self):
        """
        未初期化の接続プールでDatabaseインスタンスを初期化する。
        """
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """
        設定を使用してPostgreSQLデータベースへの接続プールを確立する。
        
        例外:
            DatabaseError: 接続プールが作成できない場合。
        """
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=settings.DB_POOL_SIZE,
                max_inactive_connection_lifetime=settings.DB_POOL_TIMEOUT,
                timeout=10,
                command_timeout=settings.SQL_EXECUTION_TIMEOUT
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise DatabaseError(
                message="データベース接続エラー",
                error_code="DATABASE_CONNECTION",
                detail=str(e)
            )
    
    async def disconnect(self) -> None:
        """
        データベース接続プールが存在する場合、それを閉じる。
        """
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def acquire(self):
        """
        非同期コンテキストマネージャとしてプールからデータベース接続を非同期で取得する。
        
        戻り値:
            非同期コンテキスト内で使用するアクティブなデータベース接続。
        
        例外:
            DatabaseError: 接続プールが初期化されていない場合。
        """
        if not self.pool:
            raise DatabaseError(
                message="データベースプールが初期化されていません",
                error_code="DATABASE_NOT_INITIALIZED",
                detail="Database.connect()を先に実行してください"
            )
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_select(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        SQL SELECTクエリを非同期で実行し、結果を辞書のリストとして返す。
        
        引数:
            query (str): 実行するSQL SELECT文。
            timeout (Optional[float]): クエリの完了を待機する最大時間（秒）。
        
        戻り値:
            List[Dict[str, Any]]: 各行が辞書として表現されるクエリ結果。
        
        例外:
            DatabaseError: タイムアウトが発生した場合、SQL構文が無効な場合、またはその他の実行エラーが発生した場合。
        """
        try:
            async with self.acquire() as conn:
                # タイムアウト設定
                if timeout:
                    rows = await asyncio.wait_for(
                        conn.fetch(query, *args),
                        timeout=timeout
                    )
                else:
                    rows = await conn.fetch(query, *args)
                
                # 結果を辞書形式に変換
                return [dict(row) for row in rows]
                
        except asyncio.TimeoutError:
            raise DatabaseError(
                message="SQL実行タイムアウト",
                error_code="DATABASE_TIMEOUT",
                detail=f"制限時間: {timeout}秒"
            )
        except asyncpg.PostgresSyntaxError as e:
            raise DatabaseError(
                message="SQL構文エラー",
                error_code="DATABASE_SYNTAX",
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise DatabaseError(
                message="SQL実行エラー",
                error_code="DATABASE_EXECUTION",
                detail=str(e)
            )
    
    async def execute(self, query: str, *args) -> Any:
        """
        CREATEやDROPなどの任意のSQLコマンドを実行する。
        
        引数:
        	query (str): 実行するSQLコマンド。
        	*args: SQLコマンドに渡すパラメータ。
        
        戻り値:
        	SQL実行の結果、通常はステータス文字列。
        
        例外:
        	DatabaseError: 何らかの理由で実行が失敗した場合。
        """
        try:
            async with self.acquire() as conn:
                result = await conn.execute(query, *args)
                return result
        except Exception as e:
            logger.error(f"Database execute error: {e}")
            raise DatabaseError(
                message="SQL実行エラー",
                error_code="DATABASE_EXECUTION",
                detail=str(e)
            )
    
    async def get_table_schemas(self) -> List[Dict[str, Any]]:
        """
        publicスキーマ内のすべてのベーステーブルのスキーマ情報を取得する。
        
        戻り値:
            各テーブルのテーブル名、タイプ、コメント、および列メタデータ（名前、データ型、NULL許可、デフォルト値、最大長）のリストを含む辞書のリスト。
        """
        query = """
        SELECT 
            t.table_name,
            t.table_type,
            obj_description(pgc.oid, 'pg_class') as table_comment
        FROM information_schema.tables t
        JOIN pg_class pgc ON pgc.relname = t.table_name
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name;
        """
        
        tables = await self.execute_select(query)
        
        # 各テーブルのカラム情報を取得
        for table in tables:
            column_query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = $1
            ORDER BY ordinal_position;
            """
            
            columns = await self.execute_select(
                column_query, 
                table['table_name']
            )
            table['columns'] = columns
        
        return tables
    
    async def drop_all_tables(self) -> None:
        """
        外部キー制約を一時的に無効にして、publicスキーマ内のすべてのテーブルを削除する。
        
        開発用途のみを意図している。操作中は外部キーチェックが無効にされ、カスケード削除を可能にし、その後復元される。操作が失敗した場合はDatabaseErrorが発生する。
        """
        try:
            async with self.acquire() as conn:
                # 外部キー制約を一時的に無効化
                await conn.execute("SET session_replication_role = 'replica';")
                
                # 全テーブル削除
                tables = await conn.fetch(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
                )
                
                for table in tables:
                    await conn.execute(f"DROP TABLE IF EXISTS {table['tablename']} CASCADE;")
                
                # 外部キー制約を再有効化
                await conn.execute("SET session_replication_role = 'origin';")
                
                logger.info(f"Dropped {len(tables)} tables")
                
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise DatabaseError(
                message="テーブル削除エラー",
                error_code="DATABASE_DROP_TABLE_ERROR",
                detail=str(e)
            )
    
    async def check_health(self) -> bool:
        """
        簡単なクエリを実行してデータベース接続が正常かどうかを確認する。
        
        戻り値:
            bool: データベースに到達可能で応答する場合True、そうでなければFalse。
        """
        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


# グローバルデータベースインスタンス
db = Database()