import React, { useState } from 'react';
import { useAssets } from '../hooks/useAssets';
import { AssetWaterfall } from './AssetWaterfall';
import { AssetEmptyState } from './AssetEmptyState';
import { AssetErrorState } from './AssetErrorState';
import { AssetDetailModal } from './AssetDetailModal';
import { Asset } from '../types/assets';

export const AssetSidebar: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('all');
  const [filterTaskId, setFilterTaskId] = useState('');
  const [detailAsset, setDetailAsset] = useState<Asset | null>(null);

  const {
    items,
    groupedItems,
    loading,
    error,
    page,
    total,
    size,
    sortDesc,
    selectedIds,
    setPage,
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
    refresh
  } = useAssets({ size: 40 });

  const totalPages = Math.ceil(total / size);

  const handleFilterChange = (type: string) => {
    setFilterType(type);
    const params: any = { is_favorite: undefined, asset_type: undefined, is_deleted: false, recent_days: undefined };
    if (type === 'image') params.asset_type = 'image';
    if (type === 'favorite') params.is_favorite = true;
    if (type === 'recent') params.recent_days = 7;
    if (type === 'deleted') params.is_deleted = true;
    updateParams(params);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 border-l border-gray-200 w-full min-w-[350px]">
      <div className="p-4 bg-white border-b border-gray-200 shadow-sm z-30 sticky top-0 flex flex-col gap-3">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">Assets Gallery</h2>
          <div className="flex gap-2">
            <button onClick={() => setSortDesc(!sortDesc)} className="px-2 py-1 text-sm rounded bg-gray-100 hover:bg-gray-200 border border-gray-200" title="Toggle Sort Order">
              {sortDesc ? '⬇️ Newest' : '⬆️ Oldest'}
            </button>
            <button onClick={refresh} className="p-1 rounded bg-gray-100 hover:bg-gray-200 border border-gray-200" title="Refresh">
              🔄
            </button>
          </div>
        </div>

        <div className="flex gap-2 text-sm overflow-x-auto pb-1 hide-scrollbar">
          {['all', 'image', 'favorite', 'recent', 'deleted'].map(t => (
            <button
              key={t}
              onClick={() => handleFilterChange(t)}
              className={`px-3 py-1 rounded-full whitespace-nowrap border ${filterType === t ? 'bg-blue-100 border-blue-300 text-blue-700 font-medium' : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'}`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex gap-2 text-sm items-center">
          <input
            type="number"
            placeholder="Filter by Task ID"
            className="border border-gray-300 rounded px-3 py-1 flex-1 min-w-[120px] outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
            value={filterTaskId}
            onChange={e => setFilterTaskId(e.target.value)}
            onBlur={() => updateParams({ task_id: filterTaskId ? parseInt(filterTaskId) : undefined })}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                updateParams({ task_id: filterTaskId ? parseInt(filterTaskId) : undefined });
              }
            }}
          />
        </div>

        {selectedIds.size > 0 && (
          <div className="flex items-center justify-between bg-blue-50 border border-blue-200 p-2 rounded animate-fade-in text-sm">
            <div className="flex items-center gap-3">
              <span className="font-semibold text-blue-800">{selectedIds.size} Selected</span>
              <button className="text-blue-600 hover:underline" onClick={selectAll}>Select All</button>
              <button className="text-blue-600 hover:underline" onClick={clearSelection}>Clear</button>
            </div>
            <div className="flex gap-2">
              <button className="bg-white border border-blue-300 px-2 py-1 rounded shadow-sm hover:bg-blue-100 text-blue-700 transition-colors" onClick={() => bulkFavorite(true)}>⭐ Fav</button>
              <button className="bg-white border border-blue-300 px-2 py-1 rounded shadow-sm hover:bg-blue-100 text-blue-700 transition-colors" onClick={() => bulkFavorite(false)}>❌ Unfav</button>
              <button className="bg-red-50 border border-red-300 px-2 py-1 rounded shadow-sm hover:bg-red-100 text-red-700 transition-colors" onClick={bulkDelete}>🗑️ Del</button>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 relative bg-gray-50">
        {loading && items.length === 0 ? (
          <div className="p-8 text-center text-gray-500 flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            Loading assets...
          </div>
        ) : error ? (
          <AssetErrorState error={error} onRetry={refresh} />
        ) : items.length === 0 ? (
          <AssetEmptyState />
        ) : (
          <AssetWaterfall
            groupedItems={groupedItems}
            selectedIds={selectedIds}
            onToggleSelection={toggleSelection}
            onToggleFavorite={toggleFavorite}
            onDelete={deleteAsset}
            onRestore={restoreAsset}
            onClickDetail={setDetailAsset}
          />
        )}
      </div>

      {totalPages > 1 && (
        <div className="p-4 bg-white border-t border-gray-200 flex justify-between items-center z-10">
          <button className="px-4 py-1.5 bg-white border border-gray-300 rounded shadow-sm disabled:opacity-50 hover:bg-gray-50 transition-colors font-medium text-gray-700" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
          <span className="text-sm font-medium text-gray-600 bg-gray-100 px-3 py-1 rounded-full">Page {page} of {totalPages}</span>
          <button className="px-4 py-1.5 bg-white border border-gray-300 rounded shadow-sm disabled:opacity-50 hover:bg-gray-50 transition-colors font-medium text-gray-700" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</button>
        </div>
      )}

      {detailAsset && <AssetDetailModal asset={detailAsset} onClose={() => setDetailAsset(null)} />}
    </div>
  );
};
