# DevPulse 多端应用构建指南

## 当前状态

- **Phase 1 (Windows 桌面)** ✅ 已完成
  - Tauri 桌面安装包：MSI (3.44MB)、NSIS EXE (2.31MB)、独立 EXE (9.46MB)
  - 路径：`desktop/src-tauri/target/release/bundle/`
- **Phase 2 (Android)** 🔄 进行中
  - Capacitor 集成完成，Android 项目已生成：`desktop/android/`
  - 前端构建成功，已同步到 Android assets
  - 详情页白屏问题已修复（API 数据格式适配）

## 快速启动

### 开发环境
```bash
# 1. 启动后端（Python FastAPI）
cd backend
.\venv\Scripts\activate
python -m devpulse

# 2. 启动前端开发服务器
cd desktop
pnpm dev
```

### 构建 Windows 桌面版
```bash
cd desktop
pnpm tauri build
# 输出：src-tauri/target/release/bundle/
```

### 构建 Android APK
1. 编辑 `.env.production`，设置 `VITE_API_BASE=http://<后端IP>:8000/api/v1`
2. 运行 `scripts\build-android.bat`
3. 用 Android Studio 打开 `android/` 目录，编译 APK

## 多端适配要点

### 1. API 客户端多端化
- **桌面端**：走 Vite 代理 `/api/v1` → `http://127.0.0.1:8000`
- **移动端**：直连后端，通过 `VITE_API_BASE` 环境变量配置
- **代码**：`desktop/src/utils/api-client.ts`

### 2. 路由适配
- **桌面端**：`BrowserRouter`
- **移动端**：`HashRouter`（兼容 file:// 协议）
- **自动检测**：`App.tsx` 根据 `window.Capacitor` 和 `file:` 协议切换

### 3. 构建配置
- **Vite**：`base: "./"` 兼容 Capacitor file:// 协议
- **Capacitor**：`capacitor.config.ts` 配置应用 ID 和 Web 目录

## 文件结构

```
desktop/
├── src/                    # React 前端源码（三端共享）
├── src-tauri/             # Tauri 桌面壳
├── android/               # Capacitor Android 项目
├── capacitor.config.ts    # Capacitor 配置
├── .env.production        # 移动端 API 地址配置
└── scripts/               # 构建脚本
    ├── build-all.bat      # 多平台一键构建
    ├── build-android.bat  # Android 专用构建
    └── dev-android.bat    # Android 开发热重载
```

## 下一步（Phase 2 剩余）

1. **Android APK 编译**：用 Android Studio 或 Gradle 命令行编译 APK
2. **鸿蒙适配（Phase 3）**：ArkUI + WebView 方案
3. **后端部署**：为移动端提供公网可访问的 API 服务

## 常见问题

### 详情页白屏
原因：后端返回扁平对象，前端期望 `{code, message, data}` 包装
解决：`useRepoDetailStore.ts` 第 88 行改为直接使用 `response`

### 移动端无法连接后端
1. 确保后端运行且防火墙开放 8000 端口
2. 修改 `.env.production` 中的 `VITE_API_BASE` 为实际 IP
3. 重新构建前端并同步到 Android

### Capacitor 状态栏适配
已集成：`src/main.tsx` 自动设置 Android 沉浸式状态栏