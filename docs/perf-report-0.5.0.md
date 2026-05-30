# DevPulse Phase 5 — 性能压测报告

> **版本**: 0.5.0  
> **日期**: 待手动执行  
> **压测工具**: wrk 4.x  
> **报告状态**: ⚠️ 待手动执行 — 性能数字为占位符

---

## 测试环境

| 项目 | 详情 |
|------|------|
| **CPU** | TBD (建议记录: 型号 / 核心数 / 频率) |
| **内存** | TBD (建议记录: 总量 / 可用) |
| **操作系统** | TBD (建议记录: `uname -a` 输出) |
| **Python 版本** | TBD (`python --version`) |
| **uvicorn 版本** | TBD (`uvicorn --version`) |
| **数据库** | SQLite (devpulse.db) |
| **后端启动命令** | `cd backend && uvicorn devpulse.main:app --host 0.0.0.0 --port 8000` |
| **wrk 版本** | TBD (`wrk --version`) |
| **网络** | localhost 回环 |

---

## 场景 1: Health 端点 (1000 并发)

### 压测命令

```bash
wrk -t4 -c1000 -d30s http://localhost:8000/health
```

### 通过标准

| 指标 | 目标 |
|------|------|
| Errors | **0** |
| P99 延迟 | **< 100ms** |

### 实测结果

> ⚠️ 待手动执行 — 请在服务运行后执行上方命令并填入结果。

```
Running 30s test @ http://localhost:8000/health
  4 threads and 1000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     TBD ms   TBD ms   TBD ms   TBD%
    Req/Sec     TBD      TBD      TBD      TBD%
  Latency Distribution
     50%    TBD ms
     75%    TBD ms
     90%    TBD ms
     99%    TBD ms
  TBD requests in 30.00s, TBD MB read
  Socket errors: connect TBD, read TBD, write TBD, timeout TBD
Requests/sec:   TBD
Transfer/sec:   TBD MB
```

### 结论

- [ ] 通过 / [ ] 未通过
- 备注: TBD

---

## 场景 2: Trending 列表 (500 并发)

### 压测命令

```bash
wrk -t4 -c500 -d30s http://localhost:8000/api/v1/repos/trending
```

### 通过标准

| 指标 | 目标 |
|------|------|
| 5xx 错误 | **0** |
| P99 延迟 | **< 1000ms (1s)** |

### 实测结果

> ⚠️ 待手动执行 — 请在服务运行后执行上方命令并填入结果。

```
Running 30s test @ http://localhost:8000/api/v1/repos/trending
  4 threads and 500 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     TBD ms   TBD ms   TBD ms   TBD%
    Req/Sec     TBD      TBD      TBD      TBD%
  Latency Distribution
     50%    TBD ms
     75%    TBD ms
     90%    TBD ms
     99%    TBD ms
  TBD requests in 30.00s, TBD MB read
  Socket errors: connect TBD, read TBD, write TBD, timeout TBD
  Non-2xx or 3xx responses: TBD
Requests/sec:   TBD
Transfer/sec:   TBD MB
```

### 结论

- [ ] 通过 / [ ] 未通过
- 备注: TBD

---

## 场景 3: 推荐端点 (100 并发)

### 压测命令

```bash
wrk -t2 -c100 -d30s http://localhost:8000/api/v1/repos/recommended
```

### 通过标准

| 指标 | 目标 |
|------|------|
| 5xx 错误 | **0** |
| P99 延迟 | **< 2000ms (2s)** |

### 实测结果

> ⚠️ 待手动执行 — 请在服务运行后执行上方命令并填入结果。

```
Running 30s test @ http://localhost:8000/api/v1/repos/recommended
  2 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     TBD ms   TBD ms   TBD ms   TBD%
    Req/Sec     TBD      TBD      TBD      TBD%
  Latency Distribution
     50%    TBD ms
     75%    TBD ms
     90%    TBD ms
     99%    TBD ms
  TBD requests in 30.00s, TBD MB read
  Socket errors: connect TBD, read TBD, write TBD, timeout TBD
  Non-2xx or 3xx responses: TBD
Requests/sec:   TBD
Transfer/sec:   TBD MB
```

### 结论

- [ ] 通过 / [ ] 未通过
- 备注: TBD

---

## 结论与建议

### 总体评估

| 场景 | 并发数 | P99 目标 | P99 实测 | 错误数 | 结果 |
|------|--------|----------|----------|--------|------|
| Health | 1000 | < 100ms | TBD | TBD | ⬜ |
| Trending | 500 | < 1s | TBD | TBD | ⬜ |
| Recommended | 100 | < 2s | TBD | TBD | ⬜ |

### 性能瓶颈分析

> ⚠️ 待手动执行后填写。

### 优化建议

> ⚠️ 待手动执行后填写。常见优化方向：
> - 数据库查询优化 (添加索引、减少 N+1)
> - 缓存策略 (Redis / 内存缓存)
> - 连接池调优
> - 异步 I/O 优化
> - CDN / 静态资源优化

### 后续行动计划

1. 在生产环境配置下重新执行压测
2. 对比 Phase 4 (0.4.0) 的性能基线
3. 针对瓶颈进行专项优化
4. 建立 CI/CD 中的性能回归检测

---

## 执行方式

### 一键执行

```bash
# 确保后端服务运行中
cd backend && uvicorn devpulse.main:app --host 0.0.0.0 --port 8000 &

# 执行压测脚本
bash scripts/perf-test.sh
```

### 手动逐场景执行

```bash
# 场景 1
wrk -t4 -c1000 -d30s http://localhost:8000/health

# 场景 2
wrk -t4 -c500 -d30s http://localhost:8000/api/v1/repos/trending

# 场景 3
wrk -t2 -c100 -d30s http://localhost:8000/api/v1/repos/recommended
```

---

> **注意**: 本报告为模板文档，所有 "TBD" 标记需在 `wrk` 实际运行后替换为真实数据。
