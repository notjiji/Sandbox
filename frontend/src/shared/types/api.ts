/** Standard API envelope used by most backend routes. */
export interface ApiEnvelope<T = unknown> {
  success: boolean;
  data: T;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: FieldValidationDetail[] | unknown;
}

export interface FieldValidationDetail {
  field: string;
  message: string;
}

export interface ApiErrorBody {
  success: false;
  error: ApiErrorDetail;
}

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface ApiRequestOptions {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  auth?: boolean;
  /** Pass null to skip sending X-Organization-ID (e.g. invite accept). */
  organizationId?: string | null;
}

export type ValidationErrors = Record<string, string>;

export interface PaginatedItems<T> {
  items: T[];
  total: number;
  page?: number;
  limit?: number;
}
