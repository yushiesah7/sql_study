import {
  type CreateTablesRequest,
  type CreateTablesResponse,
  type GenerateProblemRequest,
  type GenerateProblemResponse,
  type CheckAnswerRequest,
  type CheckAnswerResponse,
  type TableSchemasResponse,
  type HealthResponse,
  type ErrorResponse,
} from '../types/api';

const API_BASE_URL =
  process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8001/api';

class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public errorResponse?: ErrorResponse,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: ErrorResponse | undefined;
    try {
      errorData = (await response.json()) as ErrorResponse;
    } catch {
      // JSONパースに失敗した場合はそのまま進む
    }

    throw new ApiError(
      errorData?.error?.message ?? `HTTP Error: ${response.status}`,
      response.status,
      errorData,
    );
  }

  // 204 No Contentなど、レスポンスボディがない場合の処理
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return undefined as unknown as T;
  }
  
  return response.json() as Promise<T>;
}

export const api = {
  async createTables(
    request: CreateTablesRequest = {},
  ): Promise<CreateTablesResponse> {
    const response = await fetch(`${API_BASE_URL}/create-tables`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    return handleResponse<CreateTablesResponse>(response);
  },

  async generateProblem(
    request: GenerateProblemRequest = {},
  ): Promise<GenerateProblemResponse> {
    const response = await fetch(`${API_BASE_URL}/generate-problem`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    return handleResponse<GenerateProblemResponse>(response);
  },

  async checkAnswer(request: CheckAnswerRequest): Promise<CheckAnswerResponse> {
    const response = await fetch(`${API_BASE_URL}/check-answer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    return handleResponse<CheckAnswerResponse>(response);
  },

  async getTableSchemas(): Promise<TableSchemasResponse> {
    const response = await fetch(`${API_BASE_URL}/table-schemas`);
    return handleResponse<TableSchemasResponse>(response);
  },

  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<HealthResponse>(response);
  },
};

export { ApiError };
