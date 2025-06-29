// Define more specific context types
export interface CheckAnswerContext {
  problem_id: number;
  user_sql: string;
}

export type UniversalContext = CheckAnswerContext | Record<string, unknown>;

export interface UniversalRequest {
  prompt?: string;
  context?: UniversalContext;
}

export interface UniversalResponse {
  success: boolean;
  message: string;
  data?: Record<string, unknown>;
}

export interface CreateTablesRequest {
  prompt?: string;
  context?: Record<string, unknown>;
}

export interface CreateTablesResponse {
  success: boolean;
  theme: string;
  message?: string;
  tables?: string[];
  details?: Record<string, unknown>;
}

export interface GenerateProblemRequest {
  prompt?: string;
  context?: Record<string, unknown>;
}

export interface GenerateProblemResponse {
  problem_id: number;
  difficulty: 'easy' | 'medium' | 'hard';
  expected_result: Record<string, unknown>[];
  hint?: string;
  created_at: string;
}

export interface CheckAnswerRequest {
  sql: string;
  problem_id: number;
}

export interface CheckAnswerResponse {
  is_correct: boolean;
  message: string;
  user_result?: Record<string, unknown>[];
  expected_result?: Record<string, unknown>[];
  error_type?: 'syntax' | 'logic' | 'none';
  error_message?: string;
  hint?: string;
  execution_time: number;
}

export interface TableSchemasResponse {
  tables: TableSchema[];
  total_count: number;
}

export interface TableSchema {
  table_name: string;
  columns: ColumnInfo[];
  sample_data?: Record<string, unknown>[];
}

export interface ColumnInfo {
  column_name: string;
  data_type: string;
  is_nullable: boolean;
  column_default?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  services: Record<string, boolean>;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    detail?: string;
    timestamp: string;
  };
}

export interface AppState {
  tables: TableSchema[];
  currentProblem: GenerateProblemResponse | null;
  lastCheckResult: CheckAnswerResponse | null;
  isLoading: boolean;
  error: string | null;
}
