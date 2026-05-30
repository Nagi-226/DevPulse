import '@testing-library/jest-dom';

// ── Mock react-i18next ──────────────────────────
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'zh',
      changeLanguage: vi.fn(),
      exists: () => true,
    },
  }),
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}));

// ── Mock react-router-dom ───────────────────────
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...(actual as object),
    useParams: () => ({}),
    useNavigate: () => vi.fn(),
    Link: ({ children, to, ...props }: { children: React.ReactNode; to: string; [key: string]: unknown }) => {
      // Use createElement to avoid JSX in .ts file
      return React.createElement('a', { href: to, ...props }, children);
    },
  };
});

// ── Import React for Link mock above ────────────
import React from 'react';
