import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api, ApiError } from '../utils/api-client';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('getTrending', () => {
    it('should make correct API call with default parameters', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          code: 0,
          message: 'success',
          data: [],
        }),
      };
      mockFetch.mockResolvedValue(mockResponse);

      await api.getTrending();

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/repos/trending?since=weekly&language=&source=github&page=1&page_size=25',
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
    });

    it('should handle API errors', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
      });

      await expect(api.getTrending()).rejects.toThrow('API error: Not Found');
    });
  });

  describe('getRepo', () => {
    it('should encode owner/repo correctly', async () => {
      const mockResponse = {
        ok: true,
        json: vi.fn().mockResolvedValue({
          code: 0,
          message: 'success',
          data: { full_name: 'microsoft/graphrag' },
        }),
      };
      mockFetch.mockResolvedValue(mockResponse);

      await api.getRepo('microsoft', 'graphrag');

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/repos/microsoft%2Fgraphrag',
        {
          headers: { 'Content-Type': 'application/json' },
        }
      );
    });
  });

  describe('ApiError', () => {
    it('should create error with status and message', () => {
      const error = new ApiError(404, 'Not Found');
      expect(error.status).toBe(404);
      expect(error.message).toBe('Not Found');
      expect(error.name).toBe('ApiError');
    });
  });
});