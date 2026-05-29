/** GitHub Trending 项目数据结构 */
export interface Repo {
  id: number;
  /** 完整仓库名，如 "microsoft/graphrag" */
  full_name: string;
  owner: string;
  name: string;
  description: string;
  language: string;
  topics: string[];
  total_stars: number;
  stars_since: number;
  forks: number;
  forks_since: number;
  open_issues?: number;
  created_at?: string;
  updated_at?: string;
  url: string;
  /** 排行榜排名 (1-25) */
  trending_rank: number;
  /** 趋势时间段标识 */
  trending_since: string;
  /** 数据来源 */
  source?: TrendingSource;
  /** LLM 生成的项目摘要 */
  readme_summary?: string;
  /** LLM 提取的核心要点 */
  key_points?: string[];
  /** LLM 打标 */
  tags?: string[];
  /** 当前用户是否已收藏 */
  is_favorited?: boolean;
  /** Phase 4: 置信度评分 */
  confidence_score?: number;
  /** Phase 4: 审核状态 */
  review_status?: "pending" | "approved" | "rejected";
}

/** 数据源类型 */
export type TrendingSource = "github" | "gitlab" | "gitee";

/** 周报数据结构 */
export interface WeeklyReport {
  id: number;
  /** ISO 格式，如 "2026-05-18" */
  week_start: string;
  /** ISO 格式，如 "2026-05-24" */
  week_end: string;
  /** 当周收录项目总数 */
  total_repos: number;
  /** AI 生成的周报概述 */
  overview_text: string;
  /** 数据源过滤 */
  source_filter?: TrendingSource;
}

/** 搜索结果响应 */
export interface SearchResult {
  total: number;
  page: number;
  limit: number;
  items: Repo[];
}

/** 收藏项目 */
export interface FavoriteItem {
  id: number;
  repo_id: number;
  full_name: string;
  owner: string;
  name: string;
  description: string;
  language: string;
  total_stars: number;
  stars_since: number;
  tags: string[];
  created_at: string;
}

/** Star 趋势数据点 */
export interface StarPoint {
  date: string;
  stars: number;
}

/** Star 趋势响应 */
export interface StarHistoryResponse {
  full_name: string;
  history: StarPoint[];
}

/** 编程语言分布统计 */
export interface LanguageStat {
  language: string;
  count: number;
  percentage: number;
}

/** 通知偏好设置 */
export interface NotificationPrefs {
  enabled: boolean;
  trigger_on_weekly_report: boolean;
  trigger_on_crawl_complete: boolean;
}

// ═══════════════════════════════════════════════════════
// 用户认证类型
// ═══════════════════════════════════════════════════════

export interface User {
  id: number;
  email: string;
  display_name?: string;
  role?: string;
  push_enabled: boolean;
  push_weekly_report: boolean;
  push_important_project: boolean;
  fcm_token?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirm_password: string;
  display_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface LanguageOption {
  value: string;
  label: string;
}

// ═══════════════════════════════════════════════════════
// Phase 4: 用户互动类型
// ═══════════════════════════════════════════════════════

/** 评论 */
export interface Comment {
  id: number;
  user_id: number;
  display_name: string;
  content: string;
  parent_id: number | null;
  replies_count: number;
  created_at: string;
  updated_at?: string;
}

/** 点赞信息 */
export interface LikeInfo {
  liked: boolean;
  count: number;
}

/** 互动统计 */
export interface InteractionStats {
  likes_count: number;
  comments_count: number;
}

// ═══════════════════════════════════════════════════════
// Phase 4: 推荐类型
// ═══════════════════════════════════════════════════════

/** 推荐项目 */
export interface RecommendedRepo {
  repo: Repo;
  score: number;
  method: "collaborative" | "content" | "popular" | "popular_fallback";
  reason: string;
}

/** 推荐响应 */
export interface RecommendationResponse {
  items: RecommendedRepo[];
  method: string;
  fallback_level: number;
}

// ═══════════════════════════════════════════════════════
// Phase 4: Admin 类型
// ═══════════════════════════════════════════════════════

/** 管理后台 Dashboard */
export interface DashboardData {
  summary: {
    dau: number;
    page_views: number;
    favorites_count: number;
    llm_cost: number;
  };
  daily_trend: DailyTrend[];
  total_users: number;
  total_repos: number;
}

export interface DailyTrend {
  date: string;
  dau: number;
  page_views: number;
  new_users: number;
  crawl_count: number;
  llm_cost: number;
}

export interface AdminUser {
  id: number;
  email: string;
  display_name?: string;
  role: string;
  is_active: boolean;
  push_enabled: boolean;
  created_at?: string;
}

export interface PendingReview {
  id: number;
  full_name: string;
  owner: string;
  name: string;
  description?: string;
  language?: string;
  readme_summary?: string;
  key_points?: string[];
  confidence_score?: number;
  review_status: string;
  crawled_at?: string;
  summarized_at?: string;
}
