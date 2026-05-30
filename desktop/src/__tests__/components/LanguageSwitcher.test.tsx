import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// ── Re-mock react-i18next at test-file level (overrides setup.ts mock) ──
const mockChangeLanguage = vi.fn();
const mockUseTranslation = vi.fn();

vi.mock('react-i18next', () => ({
  useTranslation: () => mockUseTranslation(),
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}));

import { LanguageSwitcher } from '../../components/LanguageSwitcher';

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseTranslation.mockReturnValue({
      t: (key: string) => key,
      i18n: {
        language: 'zh',
        changeLanguage: mockChangeLanguage,
        exists: () => true,
      },
    });
  });

  it('renders all 3 language options (ZH/EN/JA)', () => {
    render(<LanguageSwitcher />);

    expect(screen.getByText('中文')).toBeInTheDocument();
    expect(screen.getByText('English')).toBeInTheDocument();
    expect(screen.getByText('日本語')).toBeInTheDocument();
  });

  it('calls changeLanguage on select', async () => {
    const user = userEvent.setup();
    render(<LanguageSwitcher />);

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 'en');

    expect(mockChangeLanguage).toHaveBeenCalledWith('en');
  });
});
