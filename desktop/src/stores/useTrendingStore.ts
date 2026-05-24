import { create } from "zustand";
import type { Repo } from "../types";
import { api } from "../utils/api-client";

/** Trending 页面状态接口 */
interface TrendingState {
  repos: Repo[];
  loading: boolean;
  error: string | null;
  language: string;
  since: "daily" | "weekly" | "monthly";
  useApi: boolean;

  /** 获取 Trending 数据（先尝试 API，失败后降级到 Mock） */
  fetchTrending: () => Promise<void>;
  setLanguage: (lang: string) => void;
  setSince: (since: "daily" | "weekly" | "monthly") => void;
  setUseApi: (useApi: boolean) => void;
}

/** 10 个 AI/ML 领域的 mock 项目数据 */
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
  {
    id: 3,
    full_name: "langchain-ai/langchain",
    owner: "langchain-ai",
    name: "langchain",
    description:
      "Build context-aware reasoning applications with LangChain's composable tools and pre-built chains for LLM orchestration.",
    language: "Python",
    topics: ["llm", "agents", "orchestration", "rag", "ai"],
    total_stars: 102000,
    stars_since: 1800,
    forks: 16500,
    forks_since: 120,
    url: "https://github.com/langchain-ai/langchain",
    trending_rank: 3,
    trending_since: "weekly",
    readme_summary:
      "LangChain 是构建 LLM 应用的最主流框架，提供链式调用、Agent 协作、工具集成等能力，生态丰富。",
    key_points: [
      "LCEL 声明式链式调用语法",
      "LangGraph 支持有状态多 Agent 协作",
      "超过 700 个集成组件",
    ],
    tags: ["LLM框架", "Agent", "工具链"],
  },
  {
    id: 4,
    full_name: "NVIDIA/TensorRT-LLM",
    owner: "NVIDIA",
    name: "TensorRT-LLM",
    description:
      "NVIDIA's official library for optimizing LLM inference on GPUs — supports quantization, tensor parallelism, and in-flight batching.",
    language: "C++",
    topics: ["inference", "optimization", "cuda", "nvidia", "llm"],
    total_stars: 18200,
    stars_since: 950,
    forks: 2400,
    forks_since: 95,
    url: "https://github.com/NVIDIA/TensorRT-LLM",
    trending_rank: 4,
    trending_since: "weekly",
    readme_summary:
      "NVIDIA 官方 LLM 推理加速库，通过量化、张量并行和 inflight batching 大幅提升 GPU 推理吞吐。",
    key_points: [
      "支持 FP8/INT4/INT8 量化推理",
      "Tensor Parallelism 多卡并行",
      "与 Triton Inference Server 深度集成",
    ],
    tags: ["推理加速", "NVIDIA", "GPU"],
  },
  {
    id: 5,
    full_name: "huggingface/transformers",
    owner: "huggingface",
    name: "transformers",
    description:
      "State-of-the-art machine learning for PyTorch, TensorFlow, and JAX — thousands of pretrained models for text, vision, and audio.",
    language: "Python",
    topics: ["nlp", "deep-learning", "pytorch", "tensorflow", "transformers"],
    total_stars: 138000,
    stars_since: 1200,
    forks: 27500,
    forks_since: 85,
    url: "https://github.com/huggingface/transformers",
    trending_rank: 5,
    trending_since: "weekly",
    readme_summary:
      "Hugging Face Transformers 是 NLP/CV/音频领域最广泛使用的预训练模型库，支持 PyTorch/TF/JAX 三框架。",
    key_points: [
      "超过 30 万预训练模型可直接调用",
      "统一的 AutoModel API 跨架构使用",
      "活跃社区，日更新模型",
    ],
    tags: ["预训练模型", "HuggingFace", "多模态"],
  },
  {
    id: 6,
    full_name: "ollama/ollama",
    owner: "ollama",
    name: "ollama",
    description:
      "Get up and running with large language models locally — run Llama, Mistral, Gemma, and other models with a single command.",
    language: "Go",
    topics: ["llm", "local", "inference", "docker", "cli"],
    total_stars: 115000,
    stars_since: 4200,
    forks: 9000,
    forks_since: 350,
    url: "https://github.com/ollama/ollama",
    trending_rank: 6,
    trending_since: "weekly",
    readme_summary:
      "Ollama 让本地运行大模型变得极其简单，一条命令即可拉起 Llama/Mistral/Gemma 等模型，深受开发者喜爱。",
    key_points: [
      "一键下载运行数百种模型",
      "兼容 OpenAI API 的本地服务",
      "支持 GPU 加速与量化",
    ],
    tags: ["本地推理", "CLI工具", "开发者工具"],
  },
  {
    id: 7,
    full_name: "deepseek-ai/DeepSeek-V3",
    owner: "deepseek-ai",
    name: "DeepSeek-V3",
    description:
      "Official implementation of DeepSeek-V3 — a strong Mixture-of-Experts language model with 671B total parameters and 37B activated.",
    language: "Python",
    topics: ["llm", "moe", "inference", "deepseek", "transformers"],
    total_stars: 58000,
    stars_since: 7800,
    forks: 5200,
    forks_since: 680,
    url: "https://github.com/deepseek-ai/DeepSeek-V3",
    trending_rank: 7,
    trending_since: "weekly",
    readme_summary:
      "DeepSeek-V3 采用 MoE 架构，671B 总参数仅激活 37B，在代码和数学推理上达到 GPT-4o 级别性能，训练成本极低。",
    key_points: [
      "MoE 架构，推理成本极低",
      "代码/数学能力对标 GPT-4o",
      "完全开源权重",
    ],
    tags: ["MoE", "DeepSeek", "国产模型"],
  },
  {
    id: 8,
    full_name: "Aider-AI/aider",
    owner: "Aider-AI",
    name: "aider",
    description:
      "AI pair programming in your terminal — aider lets you pair program with LLMs to edit code in your local git repositories.",
    language: "Python",
    topics: ["ai", "coding", "llm", "pair-programming", "cli"],
    total_stars: 28000,
    stars_since: 2100,
    forks: 2600,
    forks_since: 180,
    url: "https://github.com/Aider-AI/aider",
    trending_rank: 8,
    trending_since: "weekly",
    readme_summary:
      "Aider 是终端里的 AI 结对编程工具，直接与本地 Git 仓库交互，支持多模型切换和自动 commit。",
    key_points: [
      "终端内 AI 辅助编码",
      "自动 Git 管理变更",
      "支持 Claude/GPT/DeepSeek 等模型",
    ],
    tags: ["AI编程", "CLI", "开发工具"],
  },
  {
    id: 9,
    full_name: "CopilotKit/CopilotKit",
    owner: "CopilotKit",
    name: "CopilotKit",
    description:
      "React UI + elegant infrastructure for AI Copilots — build in-app AI chatbots, AI textareas, and AI-powered app interactions.",
    language: "TypeScript",
    topics: ["react", "copilot", "ai", "chatbot", "frontend"],
    total_stars: 19200,
    stars_since: 1600,
    forks: 2100,
    forks_since: 150,
    url: "https://github.com/CopilotKit/CopilotKit",
    trending_rank: 9,
    trending_since: "weekly",
    readme_summary:
      "CopilotKit 为 React 应用提供即插即用的 AI Copilot 能力，包括聊天组件、AI 文本框和应用内智能交互。",
    key_points: [
      "React 原生 AI Copilot 组件",
      "支持自定义 Agent 与工具调用",
      "与 LangChain/LlamaIndex 集成",
    ],
    tags: ["React", "Copilot", "前端AI"],
  },
  {
    id: 10,
    full_name: "anthropics/courses",
    owner: "anthropics",
    name: "courses",
    description:
      "Anthropic's official educational courses on prompting, tool use, and building with Claude — includes hands-on exercises and best practices.",
    language: "Jupyter Notebook",
    topics: ["claude", "prompt-engineering", "education", "anthropic", "ai"],
    total_stars: 16500,
    stars_since: 2800,
    forks: 1800,
    forks_since: 240,
    url: "https://github.com/anthropics/courses",
    trending_rank: 10,
    trending_since: "weekly",
    readme_summary:
      "Anthropic 官方出品的 Claude 使用教程，涵盖提示工程、工具调用、RAG 等实战内容，附带 Jupyter Notebook 练习。",
    key_points: [
      "官方 Prompt Engineering 最佳实践",
      "工具调用与函数调用实战",
      "RAG 与知识库构建教程",
    ],
    tags: ["教程", "Claude", "Prompt工程"],
  },
];

/**
 * Zustand store：管理 Trending 列表的数据状态。
 * 默认使用真实 API，失败后自动降级到内置 mock 数据。
 */
export const useTrendingStore = create<TrendingState>((set, get) => ({
  repos: [],
  loading: false,
  error: null,
  language: "all",
  since: "weekly",
  useApi: true,

  fetchTrending: async () => {
    const { since, language, useApi } = get();
    set({ loading: true, error: null });

    try {
      if (useApi) {
        const response = await api.getTrending(since, language === "all" ? "" : language);
        set({ repos: response.data, loading: false });
      } else {
        // Mock 降级
        await new Promise((resolve) => setTimeout(resolve, 800));
        const filtered =
          since === "weekly"
            ? MOCK_REPOS
            : MOCK_REPOS.filter((r) => r.trending_since === since);
        set({ repos: filtered, loading: false });
      }
    } catch {
      // API 失败时降级到 Mock
      if (useApi) {
        const filtered =
          since === "weekly"
            ? MOCK_REPOS
            : MOCK_REPOS.filter((r) => r.trending_since === since);
        set({
          repos: filtered,
          loading: false,
          error: "API 连接失败，已切换到离线数据",
        });
      } else {
        set({ error: "获取 Trending 数据失败，请重试", loading: false });
      }
    }
  },

  setLanguage: (lang: string) => set({ language: lang }),
  setSince: (since: "daily" | "weekly" | "monthly") => {
    set({ since });
    useTrendingStore.getState().fetchTrending();
  },
  setUseApi: (useApi: boolean) => {
    set({ useApi });
    useTrendingStore.getState().fetchTrending();
  },
}));