import { create } from "zustand";

const STORAGE_KEY = "devpulse_notification_enabled";

/** 从 localStorage 读取通知开关初始值 */
function readInitialState(): boolean {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored !== null) {
      return stored === "true";
    }
  } catch {
    // localStorage 不可用
  }
  return false;
}

interface NotificationState {
  /** 通知是否开启 */
  enabled: boolean;
  /** 切换开关 */
  toggle: () => void;
}

/**
 * Zustand store：管理推送通知开关。
 * 初始状态从 localStorage 读取，切换时同步写入。
 */
export const useNotificationStore = create<NotificationState>((set, get) => ({
  enabled: readInitialState(),

  toggle: () => {
    const next = !get().enabled;
    try {
      localStorage.setItem(STORAGE_KEY, String(next));
    } catch {
      // localStorage 不可用
    }
    set({ enabled: next });
  },
}));
