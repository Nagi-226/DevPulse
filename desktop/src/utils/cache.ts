import Dexie, { type EntityTable } from "dexie";

/** Trending 缓存条目 */
interface TrendingCacheEntry {
  id?: number; // Dexie 自增主键
  since: string;
  language: string;
  data: unknown; // JSON 序列化的响应数据
  cached_at: number; // 毫秒时间戳
}

/** 详情缓存条目 */
interface DetailCacheEntry {
  fullName: string; // 主键，如 "microsoft/graphrag"
  data: unknown;
  cached_at: number;
}

/** 缓存 TTL（毫秒）= 7 天 */
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

/**
 * DevPulse IndexedDB 数据库。
 *
 * 包含 trending_cache（按 since+language 存储 Trending 列表）
 * 和 detail_cache（按 fullName 存储仓库详情）。
 */
class DevPulseDB extends Dexie {
  trendingCache!: EntityTable<TrendingCacheEntry, "id">;
  detailCache!: EntityTable<DetailCacheEntry, "fullName">;

  constructor() {
    super("DevPulseCache");
    this.version(1).stores({
      trending_cache: "++id, since, language, cached_at",
      detail_cache: "fullName, cached_at",
    });
  }
}

const db = new DevPulseDB();

/** 检查缓存是否已过期 */
function isExpired(cachedAt: number): boolean {
  return Date.now() - cachedAt > CACHE_TTL_MS;
}

// ── Trending 缓存 ────────────────────────────────────────

/**
 * 获取 Trending 缓存数据。
 * 如果缓存不存在或已过期，返回 null。
 */
export async function getTrendingCache(
  since: string,
  language: string,
): Promise<unknown | null> {
  try {
    const entry = await db.trendingCache
      .where({ since, language })
      .reverse()
      .sortBy("cached_at");

    if (entry.length === 0) return null;
    if (isExpired(entry[0].cached_at)) {
      // 清理过期缓存
      await db.trendingCache
        .where({ since, language })
        .delete();
      return null;
    }
    return entry[0].data;
  } catch {
    return null;
  }
}

/**
 * 写入 Trending 缓存。
 * 先删除同 since+language 的旧条目再插入新数据。
 */
export async function setTrendingCache(
  since: string,
  language: string,
  data: unknown,
): Promise<void> {
  try {
    await db.trendingCache.where({ since, language }).delete();
    await db.trendingCache.add({
      since,
      language,
      data,
      cached_at: Date.now(),
    });
  } catch {
    // 缓存写入失败不抛异常
  }
}

// ── Detail 缓存 ──────────────────────────────────────────

/**
 * 获取仓库详情缓存。
 * 如果缓存不存在或已过期，返回 null。
 */
export async function getDetailCache(
  fullName: string,
): Promise<unknown | null> {
  try {
    const entry = await db.detailCache.get(fullName);
    if (!entry) return null;
    if (isExpired(entry.cached_at)) {
      await db.detailCache.delete(fullName);
      return null;
    }
    return entry.data;
  } catch {
    return null;
  }
}

/**
 * 写入仓库详情缓存。
 */
export async function setDetailCache(
  fullName: string,
  data: unknown,
): Promise<void> {
  try {
    await db.detailCache.put({
      fullName,
      data,
      cached_at: Date.now(),
    });
  } catch {
    // 缓存写入失败不抛异常
  }
}

/** 清除所有过期缓存 */
export async function cleanExpiredCache(): Promise<void> {
  const cutoff = Date.now() - CACHE_TTL_MS;
  try {
    await db.trendingCache.where("cached_at").below(cutoff).delete();
    await db.detailCache.where("cached_at").below(cutoff).delete();
  } catch {
    // 清理失败不抛异常
  }
}

/** 获取缓存统计信息 */
export async function getCacheStats(): Promise<{
  trendingCount: number;
  detailCount: number;
}> {
  try {
    const trendingCount = await db.trendingCache.count();
    const detailCount = await db.detailCache.count();
    return { trendingCount, detailCount };
  } catch {
    return { trendingCount: 0, detailCount: 0 };
  }
}

/** 清除所有缓存 */
export async function clearAllCache(): Promise<void> {
  try {
    await db.trendingCache.clear();
    await db.detailCache.clear();
  } catch {
    // 清理失败不抛异常
  }
}
