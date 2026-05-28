# GUARDRAILS.md — DevPulse 质量门禁标准

> **本文档定义 DevPulse 项目的企业级 CI/CD 门禁体系，基于 ai-dev-guardrails v3.0 五层防御架构。**
> 所有 AI Agent、开发者、Code Reviewer 必须遵守。

---

## 五条铁律

> 源自 ai-dev-guardrails，覆盖所有开发行为。

| # | 铁律 | 含义 | DevPulse 落地方式 |
|---|------|------|-----------------|
| 1 | **不盲从** | 用户指令含技术错误/误解/不合理需求时，先纠正再开工 | 需求评审时 AI Agent 自动检测：如用户要求"复刻 GitHub"→ 拦截并给替代方案 |
| 2 | **不脑补** | 需求模糊时（无边界/无选型/无具体逻辑）先问清楚，不自设前提 | PR 描述不清晰时 AI 自动列出缺失信息并请求补充 |
| 3 | **实事求是** | 明确告知能力边界，不承诺不可交付的内容 | 维护 `boundaries.md` 能力边界表，越界请求自动拒绝 |
| 4 | **可落地** | 所有产出必须可编译、可运行、可测试，无伪代码/TODO 残留 | CI 中 `pytest` / `cargo build` / `npm run build` 失败 = 门禁不通过 |
| 5 | **确认再开工** | 非微任务需先总结理解、标记假设、提议方案、等确认 | 重大架构决策必须有 ADR (Architecture Decision Record)，否则 M3 Gate 1 不通过 |

---

## L0-L5 指令层决策流

```
收到开发指令
    │
    ├─ L0: Planning Audit（规划审计）
    │   用户讨论远期规划时，后台审计逻辑缺口和可行性
    │
    ├─ L1: Minor Ambiguity（轻微模糊）
    │   1-2 个方面模糊但 ≥3 个设计决策可推断 → 标记假设，继续
    │
    ├─ L2: Clear Gap（明显缺口）
    │   ≤2 个设计决策可推断 → **暂停**，列出缺失信息，询问
    │
    ├─ L3: Technical Error（技术错误）
    │   指令包含明确技术误解 → **暂停**，解释问题，提供 3 个替代方案
    │
    ├─ L4: Red Line Violation（踩红线）
    │   请求落入能力边界外 → **坚决拒绝**，解释客观限制，提供降级选项
    │
    └─ L5: Critical Deviation（严重偏离）
        项目轨迹与契约严重偏离（范围膨胀 >50%） → **硬停止**，五步修正流程
```

---

## M1-M9 项目层监控模块

| 模块 | 一句话描述 | DevPulse 映射 |
|------|----------|-------------|
| **M1: Project Contract** | 在项目启动时锁定范围、架构、排除项，建立基线 | 每个 Phase 启动时生成 `contract-{phase}.md` |
| **M2: Scope Dashboard** | 持续追踪累积范围变化，超过 30% 增长则告警 | GitHub Project 看板追踪 feature creep，Sprint 评审自动对比 |
| **M3: Milestone Gates** | 三个强制检查点：架构定稿 / 核心完成 / 扩展入口 | Gate 1: 架构确认后；Gate 2: 0.0.7 前后端联通后；Gate 3: 每次版本扩展 |
| **M4: Planning Audit** | 用户讨论远期规划时后台审计逻辑缺口和可行性 | 需求评审时 AI 自动激活，检测"堆名词"模式 |
| **M5: Deviation Detection** | 检测项目轨迹偏离，分级（Minor/Major/Critical）处理 | 每次 PR 合入前对比 `contract-{phase}.md` |
| **M6: Reliability Gate** | 发布前验证：回归安全 + 迭代健康 | 0.1.0 起每次发布前强制执行，不可跳过 |
| **M7: L5 Defense Core** | 防御"随便"无限循环、技术名词堆砌、频繁方向变更 | 用户连续 3 次"随便"→ 强制锁定默认方案 |
| **M8: Quality Gate** | 五维审计（架构/安全/性能/质量/测试），输出严重等级和量化对比 | 每次版本发布自动运行 `production-code-audit`。**强化门禁：** 必须加载 `.claude/skills/test-driven-development` 确保无测试代码已删除，加载 `.claude/skills/verification-before-completion` 确保所有断言均有新鲜验证证据 |
| **M9: Scope Fidelity Gate** | 检测 Agent 过度工程（SF-L1 到 SF-L4 四级），15 条反过度工程速查 | 每次 PR diff 审查时自动运行必要性测试 |

---

## 反幻觉速查表（15 条）

> 嵌入所有 AI Agent 配置文件（CLAUDE.md / CODEX.md / QWEN.md），作为每次代码生成前的自我检查。

| # | Agent Impulse | Instead, Do This |
|---|--------------|------------------|
| 1 | "I'll just use [trendy tech] because it's popular" | Check project tech stack, match it |
| 2 | "This function probably exists in the API" | Search codebase first, only use verified APIs |
| 3 | "I'll build the whole thing and figure out details later" | Build one module at a time, validate after each |
| 4 | "The user said 'simple' so I'll keep it minimal" | "Simple" is subjective — ask what it means |
| 5 | "I'll add this abstraction for future flexibility" | YAGNI — build what's needed now |
| 6 | "This edge case is unlikely, I'll skip it" | Handle it — "unlikely" in dev = "Tuesday" in production |
| 7 | "I'll generate boilerplate and mark TODOs for later" | TODOs are landmines — implement or flag as out of scope |
| 8 | "This function name is bad, let me rename it" | Not your task — note it, don't change it |
| 9 | "I'll fix this nearby bug while I'm here" | One fix, one PR — don't scope-creep |
| 10 | "I'll add a try-catch just in case" | Will this exception actually occur? If no, don't add |
| 11 | "This should be extracted into a utility" | Used only once? Inline > abstract |
| 12 | "Let me refactor the existing code first" | Refactoring is not the task |
| 13 | "The user probably also needs this feature" | User didn't say it → don't build it |
| 14 | "Let me future-proof this with an abstraction layer" | You are predicting the future — stop |
| 15 | "Let me optimize this path — it's not performant" | Measure first. No measurement = don't optimize |

---

## 复杂度乘法原则（DevPulse 场景）

> **多个技术名词叠加时，复杂度的增长不是加法而是乘法。**

**触发词分级：**

| 等级 | 词汇 | 分数 |
|------|------|------|
| 🔴 Tier 1 | 区块链 / 元宇宙 / AI大模型 / 自动驾驶 / Web3.0 / NFT | 3 分/个 |
| 🟡 Tier 2 | 分布式 / 实时同步 / 高并发 100万+ / 微服务 / 机器学习 | 2 分/个 |
| 🟢 Tier 3 | 云端 / 移动端 / 跨平台 / 多语言 / 国际化 | 1 分/个 |

**响应规则：**
- 总分 ≥ 5 → 🟡 复杂度偏高，建议拆解
- 总分 ≥ 8 → 🔴 远超个人+AI 能力范围，必须降级
- ≥ 3 个独立技术领域 → 🟠 自动触发复杂度拆解流程，无论总分

**DevPulse 示例：**

| 用户需求 | 评分 | 判定 |
|---------|------|------|
| "做一个 GitHub Trending 周报，Windows 桌面 + Android" | T3×2 = 2 分 | 🟢 OK |
| "做一个实时同步 + 高并发百万用户的 GitHub 监控平台 + AI 大模型摘要" | T1×1 + T2×3 = 9 分 | 🔴 拒绝，建议降级 |
| "加上区块链存证 + NFT 徽章 + 分布式爬虫 + 自动驾驶无关" | T1×2 + T2×1 = 8 分 | 🔴 拒绝 |

---

## 30 秒审查测试

> 每次代码交付前自问：

**"另一个开发者能在 30 秒内看懂这个 diff 改了什么、为什么改吗？"**

- 如果否 → diff 太大或触碰了太多不相关文件，拆分或裁剪
- 任何超过 200 行 diff 的 PR 必须附带简要说明
- 任何超过 500 行 diff 的 PR 自动触发 M9 必要性测试

---

## 文件变更审计模式

> 每次开发会话维护如下 mental log：

```
📁 文件变更审计（session-level）:
───────────────────────────────────
REQUEST: [原始用户需求]

Files changed:
  src/xxx.py   ← REQUESTED ✅
  src/yyy.py   ← REQUESTED ✅
  config.json  ← NOT REQUESTED — 理由: "顺手改格式"
               → 如果格式修改不在需求范围内 → REVERT ❌

Scope fidelity: 2/3 files justified (66.7%)
```

**规则：** 当有疑问时，不动多余文件。每个非必要变更必须向用户说明理由。

---

## 门禁执行层级

| 层级 | 触发时机 | 检查内容 | 不可绕过？ |
|------|---------|---------|----------|
| pre-commit | 每次 `git commit` | lint + format + type-check | ✅ 不可绕过 |
| pre-push | 每次 `git push` | unit test + build check | ✅ 不可绕过 |
| PR Review | 每次 Pull Request | M8 五维审计(按需) + M5 偏离检测 + M9 范围忠实度 | 🟡 Reviewer 判断 |
| Pre-Release | 每次版本发布 | M6 Reliability Gate + M8 Quality Gate（全量） | ✅ 不可绕过 |
| Post-Session | 每次开发会话结束 | neat-freak 知识同步 | 🟢 推荐执行 |

---

## 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) — 项目架构总览
- [BUILD.md](./BUILD.md) — 构建与部署指南
- `ai-dev-guardrails` — 完整的五层防御体系说明（E:\AISkills\Nagi_Skills\ai-dev-guardrails）
- `superpowers/*` — TDD/验证/调试/规划/设计/多 Agent 协作 6 大规范套件