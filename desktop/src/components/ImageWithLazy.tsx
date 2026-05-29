import { useState, useRef, useEffect } from "react";

interface ImageWithLazyProps {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
}

/** 图片懒加载包装组件 — IntersectionObserver + loading="lazy" */
export function ImageWithLazy({
  src,
  alt,
  className = "",
  width,
  height,
}: ImageWithLazyProps) {
  const [loaded, setLoaded] = useState(false);
  const [inView, setInView] = useState(false);
  const imgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = imgRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: "200px" },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={imgRef} className={`relative overflow-hidden ${className}`}>
      {!loaded && (
        <div
          className="absolute inset-0 animate-pulse bg-slate-700/30 rounded"
          style={{ width: width || "100%", height: height || 200 }}
        />
      )}
      {inView && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          width={width}
          height={height}
          onLoad={() => setLoaded(true)}
          className={`transition-opacity duration-300 ${
            loaded ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </div>
  );
}
