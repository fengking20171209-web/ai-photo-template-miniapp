export interface AssetMetadata {
  [key: string]: any;
}

export interface Asset {
  id: number;
  task_id?: number;
  task_chain_id?: number;
  prompt_version_id?: number;
  asset_type: string;
  mime_type?: string;
  title?: string;
  description?: string;
  file_url?: string;
  thumbnail_path?: string;
  width?: number;
  height?: number;
  file_size?: number;
  metadata_json?: AssetMetadata;
  source?: string;
  is_favorite: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
}

export interface AssetListResponse {
  items: Asset[];
  total: number;
  page: number;
  size: number;
}

export interface AssetQueryParams {
  page?: number;
  size?: number;
  asset_type?: string;
  is_favorite?: boolean;
  is_deleted?: boolean;
  task_id?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  recent_days?: number;
}
