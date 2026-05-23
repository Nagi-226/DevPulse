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
  url: string;
  /** 排行榜排名 (1-25) */
  trending_rank: number;
  /** 趋势时间段标识 */
  trending_since: string;
  /** LLM 生成的项目摘要 */
  readme_summary?: string;
  /** LLM 提取的核心要点 */
  key_points?: string[];
  /** LLM 打标 */
  tags?: string[];
}

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
}