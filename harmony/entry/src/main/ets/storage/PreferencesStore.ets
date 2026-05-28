/**
 * DevPulse 鸿蒙本地存储服务
 *
 * 封装 @ohos.data.preferences，替代 IndexedDB（鸿蒙 WebView 不完全支持）。
 * 用于离线缓存周报数据、用户偏好等。
 */

import { dataPreferences } from "@kit.ArkData";
import { hilog } from "@kit.PerformanceAnalysisKit";

const TAG = "PreferencesStore";
const DOMAIN = 0x0001;
const STORE_NAME = "devpulse_store";

export class PreferencesStore {
  private static _instance: PreferencesStore;
  private _prefs: dataPreferences.Preferences | null = null;

  static getInstance(): PreferencesStore {
    if (!PreferencesStore._instance) {
      PreferencesStore._instance = new PreferencesStore();
    }
    return PreferencesStore._instance;
  }

  /**
   * 初始化 Preferences 实例
   */
  private async _ensureInit(): Promise<dataPreferences.Preferences> {
    if (this._prefs) return this._prefs;

    const context = getContext();
    this._prefs = await dataPreferences.getPreferences(context, STORE_NAME);
    return this._prefs;
  }

  /**
   * 存储字符串值
   */
  async setString(key: string, value: string): Promise<void> {
    try {
      const prefs = await this._ensureInit();
      await prefs.put(key, value);
      await prefs.flush();
    } catch (err) {
      hilog.error(DOMAIN, TAG, `setString failed: ${err}`);
    }
  }

  /**
   * 读取字符串值
   */
  async getString(key: string, defaultValue: string = ""): Promise<string> {
    try {
      const prefs = await this._ensureInit();
      return (await prefs.get(key, defaultValue)) as string;
    } catch (err) {
      hilog.error(DOMAIN, TAG, `getString failed: ${err}`);
      return defaultValue;
    }
  }

  /**
   * 存储布尔值
   */
  async setBoolean(key: string, value: boolean): Promise<void> {
    await this.setString(key, String(value));
  }

  /**
   * 读取布尔值
   */
  async getBoolean(key: string, defaultValue: boolean = false): Promise<boolean> {
    const val = await this.getString(key, String(defaultValue));
    return val === "true";
  }

  /**
   * 存储 JSON 对象
   */
  async setObject(key: string, value: object): Promise<void> {
    await this.setString(key, JSON.stringify(value));
  }

  /**
   * 读取 JSON 对象
   */
  async getObject<T extends object>(key: string, defaultValue?: T): Promise<T | null> {
    const val = await this.getString(key, "");
    if (!val) return defaultValue ?? null;
    try {
      return JSON.parse(val) as T;
    } catch {
      return defaultValue ?? null;
    }
  }

  /**
   * 删除指定键
   */
  async remove(key: string): Promise<void> {
    try {
      const prefs = await this._ensureInit();
      await prefs.delete(key);
      await prefs.flush();
    } catch (err) {
      hilog.error(DOMAIN, TAG, `remove failed: ${err}`);
    }
  }

  /**
   * 清除所有数据
   */
  async clearAll(): Promise<void> {
    try {
      const prefs = await this._ensureInit();
      await prefs.clear();
      await prefs.flush();
    } catch (err) {
      hilog.error(DOMAIN, TAG, `clearAll failed: ${err}`);
    }
  }

  /**
   * 缓存周报数据（离线浏览）
   */
  async cacheWeeklyReport(reportId: number, data: object): Promise<void> {
    await this.setObject(`weekly_report_${reportId}`, data);
    // 记录缓存时间
    await this.setString(`weekly_report_${reportId}_cached_at`, new Date().toISOString());
  }

  /**
   * 获取缓存的周报数据
   */
  async getCachedWeeklyReport(reportId: number): Promise<object | null> {
    return await this.getObject(`weekly_report_${reportId}`);
  }

  /**
   * 缓存 Trending 列表
   */
  async cacheTrendingList(since: string, language: string, data: object): Promise<void> {
    const key = `trending_${since}_${language || "all"}`;
    await this.setObject(key, data);
  }

  /**
   * 获取缓存的 Trending 列表
   */
  async getCachedTrendingList(since: string, language: string): Promise<object | null> {
    const key = `trending_${since}_${language || "all"}`;
    return await this.getObject(key);
  }
}
