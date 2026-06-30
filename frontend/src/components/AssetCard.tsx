import React from 'react';
import { Asset } from '../types/assets';

interface AssetCardProps {
  asset: Asset;
  isSelected?: boolean;
  onToggleSelection?: (id: number) => void;
  onToggleFavorite: (asset: Asset) => void;
  onDelete: (id: number) => void;
  onRestore: (id: number) => void;
  onClickDetail?: (asset: Asset) => void;
}

export const AssetCard: React.FC<AssetCardProps> = ({ 
  asset, 
  isSelected, 
  onToggleSelection, 
  onToggleFavorite, 
  onDelete, 
  onRestore,
  onClickDetail 
}) => {
  const imageUrl = asset.file_url || asset.thumbnail_path;
  
  const handleCopy = (text?: string | number) => {
    if (text) {
      navigator.clipboard.writeText(String(text));
    }
  };

  if (asset.is_deleted) {
    return (
      <div className="asset-card deleted border p-4 rounded shadow-sm opacity-50 relative flex flex-col items-center justify-center h-48 bg-gray-50">
        <span>Asset Deleted</span>
        <button className="mt-2 bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600" onClick={() => onRestore(asset.id)}>
          Restore
        </button>
      </div>
    );
  }

  return (
    <div className={`asset-card border rounded shadow-sm overflow-hidden relative group transition-all duration-200 ${isSelected ? 'ring-2 ring-blue-500 border-transparent' : 'hover:shadow-md'}`}>
      
      {/* Checkbox for bulk selection */}
      {onToggleSelection && (
        <div className={`absolute top-2 left-2 z-10 transition-opacity ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
          <input 
            type="checkbox" 
            className="w-5 h-5 cursor-pointer accent-blue-500"
            checked={!!isSelected}
            onChange={() => onToggleSelection(asset.id)}
            aria-label="Select asset"
          />
        </div>
      )}

      {/* Image / Thumbnail */}
      <div 
        className="cursor-pointer relative bg-gray-100" 
        onClick={() => onClickDetail && onClickDetail(asset)}
      >
        {imageUrl ? (
          <img src={imageUrl} alt={asset.title || 'Asset'} className="w-full h-auto object-cover block" loading="lazy" />
        ) : (
          <div className="w-full h-48 flex items-center justify-center text-gray-500">
            No Image
          </div>
        )}
      </div>
      
      {/* Action buttons overlay */}
      <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <button 
          className="bg-white/90 p-1.5 rounded-full shadow hover:bg-white transition-colors"
          onClick={() => onToggleFavorite(asset)}
          title={asset.is_favorite ? 'Unfavorite' : 'Favorite'}
        >
          {asset.is_favorite ? '⭐' : '☆'}
        </button>
        <button 
          className="bg-red-500/90 text-white p-1.5 rounded-full shadow hover:bg-red-600 transition-colors px-2.5"
          onClick={() => onDelete(asset.id)}
          title="Delete"
        >
          🗑
        </button>
      </div>

      {/* Basic Info */}
      <div className="p-3 bg-white flex flex-col gap-1.5 text-sm">
        <div className="font-semibold truncate text-gray-800" title={asset.title}>{asset.title || 'Untitled'}</div>
        <div className="flex justify-between text-xs text-gray-500">
          {asset.task_id ? (
            <span 
              className="cursor-pointer hover:text-blue-500 bg-gray-100 px-1.5 py-0.5 rounded" 
              onClick={() => handleCopy(asset.task_id)}
              title="Click to copy Task ID"
            >
              Task: {asset.task_id}
            </span>
          ) : <span />}
          {asset.prompt_version_id && (
            <span 
              className="cursor-pointer hover:text-blue-500 bg-gray-100 px-1.5 py-0.5 rounded" 
              onClick={() => handleCopy(asset.prompt_version_id)}
              title="Click to copy Prompt Version ID"
            >
              Prompt: {asset.prompt_version_id}
            </span>
          )}
        </div>
        {/* Extra dimensions if present */}
        {(asset.width && asset.height) && (
          <div className="text-xs text-gray-400 mt-1">
            {asset.width} x {asset.height}
          </div>
        )}
      </div>
    </div>
  );
};
