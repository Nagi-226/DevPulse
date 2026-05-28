import { create } from "zustand";
import type { Repo, StarPoint } from "../types";
import { api } from "../utils/api-client";

interface RepoDetailState {
  repo: Repo | null;
  loading: boolean;
  error: string | null;
  useApi: boolean;

  /** 收藏状态 */
  isFavorite: boolean;
  /** Star 趋势数据 */
  starHistory: StarPoint[];
  starHistoryLoading: boolean;

  fetchRepo: (owner: string, repoName: string) => Promise<void>;
  /** 切换收藏状态 */
  toggleFavorite: () => Promise<boolean>;
  /** 获取 Star 历史趋势 */
  fetchStarHistory: (owner: string, repoName: string) => Promise<void>;
  setUseApi: (useApi: boolean) => void;
}

/** 详情页 Mock 数据 */
const MOCK_REPOS: Repo[] = [
  {
    id: 1,
    full_name: "microsoft/graphrag",
    owner: "microsoft",
    name: "graphrag",
    description:
      "A modular graph-based Retrieval-Augmented Generation (RAG) system that uses LLM-generated knowledge graphs to enhance query-focused summarization.",
    language: "Python",
    topics: ["rag", "knowledge-graph", "llm", "nlp", "graph-neural-networks"],
    total_stars: 24500,
    stars_since: 3200,
    forks: 2100,
    forks_since: 180,
    open_issues: 42,
    created_at: "2024-03-15T00:00:00Z",
    updated_at: "2026-05-25T00:00:00Z",
    url: "https://github.com/microsoft/graphrag",
    trending_rank: 1,
    trending_since: "weekly",
    readme_summary:
      "微软开源的 GraphRAG 项目，通过知识图谱增强大语言模型的检索增强生成能力，显著提升复杂问答场景下的准确性和可解释性。",
    key_points: [
      "基于 LLM 自动构建知识图谱",
      "支持全局摘要与局部检索混合查询",
      "模块化设计，可灵活替换各组件",
    ],
    tags: ["知识图谱", "RAG", "微软"],
  },
  {
    id: 2,
    full_name: "meta-llama/llama-models",
    owner: "meta-llama",
    name: "llama-models",
    description:
      "Official inference code and model weights for Llama 4 models by Meta — state-of-the-art open-source large language models.",
    language: "Python",
    topics: ["llm", "transformers", "meta", "open-source", "inference"],
    total_stars: 98000,
    stars_since: 5600,
    forks: 15200,
    forks_since: 420,
    open_issues: 128,
    created_at: "2023-02-24T00:00:00Z",
    updated_at: "2026-05-27T00:00:00Z",
    url: "https://github.com/meta-llama/llama-models",
    trending_rank: 2,
    trending_since: "weekly",
    readme_summary:
      "Meta 发布的 Llama 4 系列开源大模型，涵盖多模态理解与生成能力，在多项基准测试中达到 SOTA 水平。",
    key_points: [
      "多模态架构，支持文本+图像理解",
      "开源权重，允许商业使用",
      "提供微调与部署工具链",
    ],
    tags: ["大语言模型", "Meta", "开源"],
  },
];

/** Mock Star 历史数据 */
const MOCK_STAR_HISTORY: StarPoint[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (29 - i));
  return {
    date: date.toISOString().slice(0, 10),
    stars: 20000 + Math.floor(i * 150) + Math.floor(Math.random() * 200),
  };
});

export const useRepoDetailStore = create<RepoDetailState>((set, get) => ({
  repo: null,
  loading: false,
  error: null,
  useApi: true,
  isFavorite: false,
  starHistory: [],
  starHistoryLoading: false,

  fetchRepo: async (owner: string, repoName: string) => {
    const { useApi } = get();
    set({ loading: true, error: null, repo: null });

    try {
      if (useApi) {
        const response = await api.getRepo(owner, repoName);
        const repo = response as unknown as Repo;
        set({
          repo,
          loading: false,
          isFavorite: repo.is_favorited ?? false,
        });
      } else {
        await new Promise((resolve) => setTimeout(resolve, 500));
        const found = MOCK_REPOS.find(
          (r) => r.owner === owner && r.name === repoName,
        );
        if (found) {
          set({ repo: found, loading: false });
        } else {
          set({ error: `未找到项目 ${owner}/${repoName}`, loading: false });
        }
      }
    } catch {
      if (useApi) {
        const found = MOCK_REPOS.find(
          (r) => r.owner === owner && r.name === repoName,
        );
        if (found) {
          set({
            repo: found,
            loading: false,
            error: "API 连接失败，已切换到离线数据",
          });
        } else {
          set({
            error: `API 连接失败，且未找到离线数据 ${owner}/${repoName}`,
            loading: false,
          });
        }
      } else {
        set({ error: "获取项目详情失败，请重试", loading: false });
      }
    }
  },

  toggleFavorite: async () => {
    const { repo, isFavorite } = get();
    if (!repo) return false;

    const fullName = repo.full_name;
    try {
      if (isFavorite) {
        await api.unstarRepo(fullName);
        set({ isFavorite: false });
      } else {
        await api.starRepo(fullName);
        set({ isFavorite: true });
      }
      return true;
    } catch {
      set({ error: isFavorite ? "取消收藏失败" : "收藏失败" });
      return false;
    }
  },

  fetchStarHistory: async (owner: string, repoName: string) => {
    const { useApi } = get();
    set({ starHistoryLoading: true });

    try {
      if (useApi) {
        const response = await api.getStarHistory(`${owner}/${repoName}`);
        const items = (response as unknown as { items: { history: StarPoint[] }[] }).items;
        if (items && items.length > 0) {
          set({ starHistory: items[0].history ?? [], starHistoryLoading: false });
        } else {
          set({ starHistory: [], starHistoryLoading: false });
        }
      } else {
        await new Promise((resolve) => setTimeout(resolve, 600));
        set({ starHistory: MOCK_STAR_HISTORY, starHistoryLoading: false });
      }
    } catch {
      set({ starHistory: [], starHistoryLoading: false });
    }
  },

  setUseApi: (useApi: boolean) => set({ useApi }),
}));
