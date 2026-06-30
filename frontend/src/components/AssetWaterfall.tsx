import React from 'react';
import { Asset } from '../types/assets';
import { AssetCard } from './AssetCard';
import { GroupedAssets } from '../hooks/useAssets';

interface AssetWaterfallProps {
  groupedItems: GroupedAssets[];
  selectedIds: Set<number>;
  onToggleSelection: (id: number) => void;
  onToggleFavorite: (asset: Asset) => void;
  onDelete: (id: number) => void;
  onRestore: (id: number) => void;
  onClickDetail?: (asset: Asset) => void;
}

export const AssetWaterfall: React.FC<AssetWaterfallProps> = ({ 
  groupedItems,
  selectedIds,
  onToggleSelection,
  onToggleFavorite, 
  onDelete, 
  onRestore,
  onClickDetail
}) => {
  if (groupedItems.length === 0) {
    return null;
  }

  return (
    <div className="p-4 flex flex-col gap-8">
      {groupedItems.map(group => (
        <div key={group.date} className="asset-group">
          {/* Timeline Group Header */}
          <div className="sticky top-0 z-20 bg-gray-50/90 backdrop-blur-sm py-2 mb-4 border-b border-gray-200">
            <h3 className="text-lg font-bold text-gray-700">{group.date}</h3>
          </div>
          
          {/* Group Content */}
          <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
            {group.assets.map(asset => (
              <div key={asset.id} className="break-inside-avoid">
                <AssetCard 
                  asset={asset}
                  isSelected={selectedIds.has(asset.id)}
                  onToggleSelection={onToggleSelection}
                  onToggleFavorite={onToggleFavorite} 
                  onDelete={onDelete} 
                  onRestore={onRestore}
                  onClickDetail={onClickDetail}
                />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
