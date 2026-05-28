import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/useAuthStore";

/** Tab 类型 */
type AuthTab = "login" | "register";

/**
 * 用户认证页面 — 登录/注册双 Tab。
 *
 * 功能：
 * - Tab 切换（登录 / 注册）
 * - 邮箱格式前端校验
 * - 密码强度校验（≥8位 + 字母 + 数字）
 * - 确认密码一致性校验
 * - 错误提示 + loading 态
 * - 登录成功后自动跳转首页
 */
export function AuthPage() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const storeLoading = useAuthStore((s) => s.loading);
  const storeError = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);

  const [tab, setTab] = useState<AuthTab>("login");

  // 表单字段
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  // 本地校验错误
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // 登录成功后跳转
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // 切换 Tab 时清除错误
  const handleTabChange = (newTab: AuthTab) => {
    setTab(newTab);
    clearError();
    setFieldErrors({});
  };

  /** 前端表单校验 */
  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!email.trim()) {
      errors.email = "请输入邮箱";
    } else if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)) {
      errors.email = "邮箱格式无效";
    }

    if (!password) {
      errors.password = "请输入密码";
    } else if (password.length < 8) {
      errors.password = "密码长度至少 8 位";
    } else if (!/[a-zA-Z]/.test(password)) {
      errors.password = "密码必须包含至少一个字母";
    } else if (!/\d/.test(password)) {
      errors.password = "密码必须包含至少一个数字";
    }

    if (tab === "register") {
      if (!confirmPassword) {
        errors.confirmPassword = "请确认密码";
      } else if (password !== confirmPassword) {
        errors.confirmPassword = "两次输入的密码不一致";
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /** 提交表单 */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validate()) return;

    if (tab === "login") {
      await login(email, password);
    } else {
      await register(
        email,
        password,
        confirmPassword,
        displayName || undefined,
      );
    }
  };

  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* 标题 */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-500/20">
            <span className="text-2xl font-extrabold text-primary-400">DP</span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            {tab === "login" ? "欢迎回来" : "创建账号"}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {tab === "login" ? "登录以同步收藏数据" : "注册以开始同步收藏数据"}
          </p>
        </div>

        {/* Tab 切换 */}
        <div className="mb-6 flex rounded-lg border border-slate-700 bg-slate-800/50 p-1">
          <button
            onClick={() => handleTabChange("login")}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === "login"
                ? "bg-primary-500 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            登录
          </button>
          <button
            onClick={() => handleTabChange("register")}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === "register"
                ? "bg-primary-500 text-white"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            注册
          </button>
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 全局错误 */}
          {storeError && (
            <div className="rounded-lg border border-red-700/50 bg-red-900/20 px-4 py-3 text-sm text-red-300">
              {storeError}
            </div>
          )}

          {/* 邮箱 */}
          <div>
            <label
              htmlFor="auth-email"
              className="mb-1.5 block text-sm font-medium text-slate-300"
            >
              邮箱
            </label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              className={`w-full rounded-lg border bg-slate-800/50 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                fieldErrors.email ? "border-red-500" : "border-slate-700"
              }`}
              style={{ minHeight: 48 }}
            />
            {fieldErrors.email && (
              <p className="mt-1 text-xs text-red-400">{fieldErrors.email}</p>
            )}
          </div>

          {/* 显示名称（仅注册） */}
          {tab === "register" && (
            <div>
              <label
                htmlFor="auth-display-name"
                className="mb-1.5 block text-sm font-medium text-slate-300"
              >
                显示名称（可选）
              </label>
              <input
                id="auth-display-name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="你的昵称"
                autoComplete="name"
                className="w-full rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                style={{ minHeight: 48 }}
              />
            </div>
          )}

          {/* 密码 */}
          <div>
            <label
              htmlFor="auth-password"
              className="mb-1.5 block text-sm font-medium text-slate-300"
            >
              密码
            </label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={tab === "register" ? "至少 8 位，含字母和数字" : "输入密码"}
              autoComplete={tab === "login" ? "current-password" : "new-password"}
              className={`w-full rounded-lg border bg-slate-800/50 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                fieldErrors.password ? "border-red-500" : "border-slate-700"
              }`}
              style={{ minHeight: 48 }}
            />
            {fieldErrors.password && (
              <p className="mt-1 text-xs text-red-400">{fieldErrors.password}</p>
            )}
          </div>

          {/* 确认密码（仅注册） */}
          {tab === "register" && (
            <div>
              <label
                htmlFor="auth-confirm-password"
                className="mb-1.5 block text-sm font-medium text-slate-300"
              >
                确认密码
              </label>
              <input
                id="auth-confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="再次输入密码"
                autoComplete="new-password"
                className={`w-full rounded-lg border bg-slate-800/50 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                  fieldErrors.confirmPassword ? "border-red-500" : "border-slate-700"
                }`}
                style={{ minHeight: 48 }}
              />
              {fieldErrors.confirmPassword && (
                <p className="mt-1 text-xs text-red-400">
                  {fieldErrors.confirmPassword}
                </p>
              )}
            </div>
          )}

          {/* 记住我（仅登录） */}
          {tab === "login" && (
            <div className="flex items-center">
              <input
                id="auth-remember"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 rounded border-slate-600 bg-slate-700 text-primary-500 focus:ring-primary-500"
              />
              <label
                htmlFor="auth-remember"
                className="ml-2 text-sm text-slate-400"
              >
                记住我
              </label>
            </div>
          )}

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={storeLoading}
            className="w-full rounded-lg bg-primary-500 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50"
            style={{ minHeight: 48 }}
          >
            {storeLoading ? (
              <span className="inline-flex items-center gap-2">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                {tab === "login" ? "登录中..." : "注册中..."}
              </span>
            ) : tab === "login" ? (
              "登录"
            ) : (
              "注册"
            )}
          </button>

          {/* 底部提示 */}
          <p className="text-center text-xs text-slate-500">
            {tab === "login" ? (
              <>
                还没有账号？{" "}
                <button
                  type="button"
                  onClick={() => handleTabChange("register")}
                  className="text-primary-400 hover:text-primary-300"
                >
                  立即注册
                </button>
              </>
            ) : (
              <>
                已有账号？{" "}
                <button
                  type="button"
                  onClick={() => handleTabChange("login")}
                  className="text-primary-400 hover:text-primary-300"
                >
                  去登录
                </button>
              </>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}
