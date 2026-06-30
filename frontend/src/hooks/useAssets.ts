import { useState, useEffect, useCallback, useMemo } from 'react';
import { Asset, AssetQueryParams } from '../types/assets';
import { assetApi } from '../api/assets';

export interface GroupedAssets {
  date: string;
  assets: Asset[];
}

export function useAssets(initialParams: AssetQueryParams = {}) {
  const [items, setItems] = useState<Asset[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(initialParams.page || 1);
  const [size, setSize] = useState(initialParams.size || 20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const [params, setParams] = useState<AssetQueryParams>(initialParams);

  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  // Sorting state (desc by default)
  const [sortDesc, setSortDesc] = useState(true);

  const fetchAssets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await assetApi.listAssets({ ...params, page, size });
      setItems(response.items);
      setTotal(response.total);
      setSelectedIds(new Set()); // clear selection on fetch
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [params, page, size]);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const updateParams = (newParams: Partial<AssetQueryParams>) => {
    setParams(prev => ({ ...prev, ...newParams }));
    setPage(1); // reset to first page on filter change
  };

  const toggleFavorite = async (asset: Asset) => {
    const isCurrentlyFavorite = asset.is_favorite;
    // Optimistic update
    setItems(prev => prev.map(a => a.id === asset.id ? { ...a, is_favorite: !isCurrentlyFavorite } : a));
    
    try {
      if (isCurrentlyFavorite) {
        await assetApi.unfavoriteAsset(asset.id);
      } else {
        await assetApi.favoriteAsset(asset.id);
      }
    } catch (err) {
      // Revert on failure
      setItems(prev => prev.map(a => a.id === asset.id ? { ...a, is_favorite: isCurrentlyFavorite } : a));
      console.error('Failed to toggle favorite', err);
    }
  };

  const deleteAsset = async (id: number) => {
    // Optimistic update
    setItems(prev => prev.map(a => a.id === id ? { ...a, is_deleted: true } : a));
    
    try {
      await assetApi.deleteAsset(id);
    } catch (err) {
      // Revert on failure
      setItems(prev => prev.map(a => a.id === id ? { ...a, is_deleted: false } : a));
      console.error('Failed to delete asset', err);
    }
  };

  const restoreAsset = async (id: number) => {
    setItems(prev => prev.map(a => a.id === id ? { ...a, is_deleted: false } : a));
    
    try {
      await assetApi.restoreAsset(id);
    } catch (err) {
      setItems(prev => prev.map(a => a.id === id ? { ...a, is_deleted: true } : a));
      console.error('Failed to restore asset', err);
    }
  };

  // Bulk operations
  const toggleSelection = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAll = () => setSelectedIds(new Set(items.map(i => i.id)));
  const clearSelection = () => setSelectedIds(new Set());

  const bulkFavorite = async (favorite: boolean) => {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;

    // Optimistic
    setItems(prev => prev.map(a => ids.includes(a.id) ? { ...a, is_favorite: favorite } : a));

    try {
      const results = await Promise.allSettled(
        ids.map(id => favorite ? assetApi.favoriteAsset(id) : assetApi.unfavoriteAsset(id))
      );
      const hasErrors = results.some(r => r.status === 'rejected');
      if (hasErrors) {
        console.error('Bulk favorite partial or complete failure', results.filter(r => r.status === 'rejected'));
        fetchAssets();
      }
    } catch (err) {
      console.error('Bulk favorite error', err);
      fetchAssets();
    }
  };

  const bulkDelete = async () => {
    const ids = Array.from(selectedIds);
    if (!ids.length) return;

    // Optimistic
    setItems(prev => prev.map(a => ids.includes(a.id) ? { ...a, is_deleted: true } : a));
    setSelectedIds(new Set());

    try {
      const results = await Promise.allSettled(ids.map(id => assetApi.deleteAsset(id)));
      const hasErrors = results.some(r => r.status === 'rejected');
      if (hasErrors) {
        console.error('Bulk delete partial or complete failure', results.filter(r => r.status === 'rejected'));
        fetchAssets();
      }
    } catch (err) {
      console.error('Bulk delete error', err);
      fetchAssets();
    }
  };

  // Derived state: grouped items
  const groupedItems = useMemo(() => {
    // 1. Sort items
    const sorted = [...items].sort((a, b) => {
      const timeA = new Date(a.created_at).getTime();
      const timeB = new Date(b.created_at).getTime();
      return sortDesc ? timeB - timeA : timeA - timeB;
    });

    // 2. Group by date (YYYY-MM-DD)
    const groups: { [key: string]: Asset[] } = {};
    for (const asset of sorted) {
      // Assuming created_at is valid ISO string
      let dateKey = 'Unknown Date';
      if (asset.created_at) {
        const d = new Date(asset.created_at);
        if (!isNaN(d.getTime())) {
          dateKey = d.toISOString().split('T')[0];
        }
      }
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(asset);
    }

    const result = Object.keys(groups).map(date => ({
      date,
      assets: groups[date]
    }));

    return result.sort((a, b) => {
      if (a.date === 'Unknown Date') return 1;
      if (b.date === 'Unknown Date') return -1;
      return sortDesc ? b.date.localeCompare(a.date) : a.date.localeCompare(b.date);
    });
  }, [items, sortDesc]);

  return {
    items,
    groupedItems,
    total,
    page,
    size,
    loading,
    error,
    params,
    sortDesc,
    selectedIds,
    setPage,
    setSize,
    setSortDesc,
    updateParams,
    toggleFavorite,
    deleteAsset,
    restoreAsset,
    toggleSelection,
    selectAll,
    clearSelection,
    bulkFavorite,
    bulkDelete,
    refresh: fetchAssets
  };
}
