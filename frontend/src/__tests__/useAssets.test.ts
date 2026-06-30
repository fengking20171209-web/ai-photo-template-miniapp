// @vitest-environment jsdom  
import { renderHook, act } from '@testing-library/react';
import { useAssets } from '../hooks/useAssets';
import { assetApi } from '../api/assets';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the API client
vi.mock('../api/assets', () => ({
  assetApi: {
    listAssets: vi.fn(),
    favoriteAsset: vi.fn(),
    unfavoriteAsset: vi.fn(),
    deleteAsset: vi.fn(),
    restoreAsset: vi.fn(),
  }
}));

describe('useAssets Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch assets on initial render', async () => {
    const mockItems = [{ id: 1, file_url: '/test.jpg', is_favorite: false, is_deleted: false }];
    (assetApi.listAssets as any).mockResolvedValue({
      items: mockItems,
      total: 1,
      page: 1,
      size: 20
    });

    const { result } = renderHook(() => useAssets());

    expect(result.current.loading).toBe(true);
    
    // Wait for the async effect to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.items).toEqual(mockItems);
    expect(result.current.total).toBe(1);
  });

  it('should toggle favorite optimistic update', async () => {
    const mockItems = [{ id: 1, file_url: '/test.jpg', is_favorite: false, is_deleted: false }];
    (assetApi.listAssets as any).mockResolvedValue({ items: mockItems, total: 1, page: 1, size: 20 });
    (assetApi.favoriteAsset as any).mockResolvedValue({ ...mockItems[0], is_favorite: true });

    const { result } = renderHook(() => useAssets());
    
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.items[0].is_favorite).toBe(false);

    // Toggle favorite
    await act(async () => {
      await result.current.toggleFavorite(result.current.items[0] as any);
    });

    expect(assetApi.favoriteAsset).toHaveBeenCalledWith(1);
    expect(result.current.items[0].is_favorite).toBe(true);
  });

  it('should handle optimistic soft delete', async () => {
    const mockItems = [{ id: 1, file_url: '/test.jpg', is_favorite: false, is_deleted: false }];
    (assetApi.listAssets as any).mockResolvedValue({ items: mockItems, total: 1, page: 1, size: 20 });
    (assetApi.deleteAsset as any).mockResolvedValue();

    const { result } = renderHook(() => useAssets());
    
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    expect(result.current.items[0].is_deleted).toBe(false);

    // Delete
    await act(async () => {
      await result.current.deleteAsset(1);
    });

    expect(assetApi.deleteAsset).toHaveBeenCalledWith(1);
    expect(result.current.items[0].is_deleted).toBe(true);
  });

  it('should handle bulk favorite logic', async () => {
    const mockItems = [
      { id: 1, is_favorite: false, is_deleted: false, created_at: '2026-06-23T00:00:00Z' },
      { id: 2, is_favorite: false, is_deleted: false, created_at: '2026-06-23T00:00:00Z' }
    ];
    (assetApi.listAssets as any).mockResolvedValue({ items: mockItems, total: 2, page: 1, size: 20 });
    (assetApi.favoriteAsset as any).mockResolvedValue({});
    
    const { result } = renderHook(() => useAssets());
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Select items
    act(() => {
      result.current.toggleSelection(1);
      result.current.toggleSelection(2);
    });

    expect(result.current.selectedIds.size).toBe(2);

    // Bulk favorite
    await act(async () => {
      await result.current.bulkFavorite(true);
    });

    expect(assetApi.favoriteAsset).toHaveBeenCalledTimes(2);
    expect(result.current.items[0].is_favorite).toBe(true);
    expect(result.current.items[1].is_favorite).toBe(true);
  });

  it('should handle sorting order correctly', async () => {
    const mockItems = [
      { id: 1, created_at: '2026-06-21T00:00:00Z' },
      { id: 2, created_at: '2026-06-22T00:00:00Z' }
    ];
    (assetApi.listAssets as any).mockResolvedValue({ items: mockItems, total: 2, page: 1, size: 20 });
    
    const { result } = renderHook(() => useAssets());
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    // Default sortDesc = true, so newest first (id: 2 then id: 1)
    expect(result.current.groupedItems[0].assets[0].id).toBe(2);

    // Change sort order
    act(() => {
      result.current.setSortDesc(false);
    });

    // Oldest first (id: 1 then id: 2)
    expect(result.current.groupedItems[0].assets[0].id).toBe(1);
  });
});
