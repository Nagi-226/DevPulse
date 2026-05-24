import type { Repo, WeeklyReport } from "../types";

const BASE_URL = "/api/v1";

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
  };
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!response.ok) {
    throw new ApiError(response.status, `API error: ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  /** 获取 Trending 仓库列表 */
  getTrending: (since = "weekly", language = "", page = 1, pageSize = 25) =>
    request<Repo[]>(`/repos/trending?since=${since}&language=${language}&page=${page}&page_size=${pageSize}`),

  /** 获取单个仓库详情 */
  getRepo: (owner: string, repo: string) =>
    request<Repo>(`/repos/${encodeURIComponent(owner + "/" + repo)}`),

  /** 获取周报列表 */
  getWeeklyReports: (limit = 10) =>
    request<WeeklyReport[]>(`/repos/weekly-reports?limit=${limit}`),

  /** 获取单个周报 */
  getWeeklyReport: (reportId: number) =>
    request<WeeklyReport>(`/repos/weekly-reports/${reportId}`),

  /** 触发爬虫 */
  triggerCrawl: (language = "", since = "weekly") =>
    request<{ message: string }>(`/repos/crawl?language=${language}&since=${since}`, { method: "POST" }),

  /** 调度器状态 */
  getSchedulerJobs: () =>
    request<Array<{ id: string; name: string; next_run: string | null }>>("/scheduler/jobs"),
};

export { ApiError };