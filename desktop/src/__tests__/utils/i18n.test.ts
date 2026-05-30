import { describe, it, expect } from 'vitest';

describe('i18n Configuration', () => {
  it('has 7 namespaces', async () => {
    const i18n = (await import('../../utils/i18n')).default;

    const namespaces = i18n.options.ns as string[] | undefined;
    // i18next stores ns on the options object when resources are defined
    // With react-i18next, namespaces are derived from the resources
    const resourceLangs = Object.keys(i18n.options.resources || {});
    expect(resourceLangs.length).toBeGreaterThanOrEqual(3);

    // Check zh has all 7 namespaces
    const zhResources = (i18n.options.resources as Record<string, Record<string, unknown>>)?.zh;
    if (zhResources) {
      const ns = Object.keys(zhResources);
      expect(ns).toHaveLength(7);
      expect(ns).toContain('common');
      expect(ns).toContain('trending');
      expect(ns).toContain('detail');
      expect(ns).toContain('auth');
      expect(ns).toContain('settings');
      expect(ns).toContain('search');
      expect(ns).toContain('admin');
    }
  });

  it('has 3 languages available', async () => {
    const i18n = (await import('../../utils/i18n')).default;
    const languages = Object.keys(i18n.options.resources || {});
    expect(languages).toHaveLength(3);
    expect(languages).toContain('zh');
    expect(languages).toContain('en');
    expect(languages).toContain('ja');
  });

  it('detects browser language', async () => {
    const i18n = (await import('../../utils/i18n')).default;
    const detectorOrder = (i18n.options.detection as { order?: string[] })?.order;
    expect(detectorOrder).toBeDefined();
    expect(detectorOrder).toContain('navigator');
  });
});
