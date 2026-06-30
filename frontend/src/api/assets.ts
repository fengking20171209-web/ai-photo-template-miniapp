import { Asset, AssetListResponse, AssetQueryParams } from '../types/assets';

// Use environment variable or relative path
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export const assetApi = {
  async listAssets(params?: AssetQueryParams): Promise<AssetListResponse> {
    const url = new URL(`${BASE_URL}/assets`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          url.searchParams.append(key, String(value));
        }
      });
    }
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to fetch assets');
    return res.json();
  },

  async getAsset(id: number): Promise<Asset> {
    const res = await fetch(`${BASE_URL}/assets/${id}`);
    if (!res.ok) throw new Error('Failed to fetch asset');
    return res.json();
  },

  async listTaskAssets(taskId: number): Promise<Asset[]> {
    // Some APIs might put it under /tasks/{id}/assets or use the query param on /assets
    // We will use the query param approach since it's supported by listAssets, but let's have a dedicated call if needed.
    // The backend in Phase 3A might not have a dedicated task endpoint, let's use /assets?task_id=...
    const url = new URL(`${BASE_URL}/assets`, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
    url.searchParams.append('task_id', String(taskId));
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to fetch task assets');
    const data: AssetListResponse = await res.json();
    return data.items;
  },

  async favoriteAsset(id: number): Promise<Asset> {
    const res = await fetch(`${BASE_URL}/assets/${id}/favorite`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to favorite asset');
    return res.json();
  },

  async unfavoriteAsset(id: number): Promise<Asset> {
    const res = await fetch(`${BASE_URL}/assets/${id}/favorite`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to unfavorite asset');
    return res.json();
  },

  async deleteAsset(id: number): Promise<void> {
    const res = await fetch(`${BASE_URL}/assets/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete asset');
  },

  async restoreAsset(id: number): Promise<Asset> {
    const res = await fetch(`${BASE_URL}/assets/${id}/restore`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to restore asset');
    return res.json();
  }
};