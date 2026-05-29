import { useEffect } from "react";

interface SEOHeadProps {
  title: string;
  description: string;
  canonical?: string;
  ogImage?: string;
  lang?: string;
}

/** 动态 SEO meta 标签组件 */
export function SEOHead({
  title,
  description,
  canonical,
  ogImage,
  lang = "zh-CN",
}: SEOHeadProps) {
  useEffect(() => {
    document.title = `${title} — DevPulse`;
    document.documentElement.lang = lang;

    const setMeta = (name: string, content: string, property = false) => {
      const attr = property ? "property" : "name";
      let el = document.querySelector(`meta[${attr}="${name}"]`);
      if (!el) {
        el = document.createElement("meta");
        el.setAttribute(attr, name);
        document.head.appendChild(el);
      }
      el.setAttribute("content", content);
    };

    setMeta("description", description);
    setMeta("og:title", `${title} — DevPulse`, true);
    setMeta("og:description", description, true);

    if (canonical) {
      let link = document.querySelector('link[rel="canonical"]');
      if (!link) {
        link = document.createElement("link");
        link.setAttribute("rel", "canonical");
        document.head.appendChild(link);
      }
      link.setAttribute("href", canonical);
    }

    if (ogImage) {
      setMeta("og:image", ogImage, true);
    }

    return () => {
      // Cleanup handled by next page load
    };
  }, [title, description, canonical, ogImage, lang]);

  return null;
}
