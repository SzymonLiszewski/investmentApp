import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  dispatchLogout,
} from './client';

describe('api client', () => {
  const storage = {};

  beforeEach(() => {
    vi.stubGlobal('localStorage', {
      getItem: (key) => storage[key] ?? null,
      setItem: (key, value) => {
        storage[key] = value;
      },
      removeItem: (key) => {
        delete storage[key];
      },
    });
    storage.access = 'access-token';
    storage.refresh = 'refresh-token';
  });

  describe('getAccessToken', () => {
    it('returns access token from localStorage', () => {
      expect(getAccessToken()).toBe('access-token');
    });
    it('returns null when no access token', () => {
      delete storage.access;
      expect(getAccessToken()).toBeNull();
    });
  });

  describe('getRefreshToken', () => {
    it('returns refresh token from localStorage', () => {
      expect(getRefreshToken()).toBe('refresh-token');
    });
    it('returns null when no refresh token', () => {
      delete storage.refresh;
      expect(getRefreshToken()).toBeNull();
    });
  });

  describe('clearTokens', () => {
    it('removes access and refresh from localStorage', () => {
      clearTokens();
      expect(getAccessToken()).toBeNull();
      expect(getRefreshToken()).toBeNull();
    });
  });

  describe('dispatchLogout', () => {
    it('clears tokens and dispatches auth:logout event', () => {
      const listener = vi.fn();
      window.addEventListener('auth:logout', listener);
      dispatchLogout();
      expect(getAccessToken()).toBeNull();
      expect(getRefreshToken()).toBeNull();
      expect(listener).toHaveBeenCalledTimes(1);
      window.removeEventListener('auth:logout', listener);
    });
  });
});
