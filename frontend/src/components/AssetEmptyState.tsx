import React from 'react';

export const AssetEmptyState: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-gray-500 h-full min-h-[300px]">
      <div className="text-4xl mb-4">📭</div>
      <h3 className="text-lg font-medium text-gray-700">No Assets Found</h3>
      <p className="text-sm mt-2">Try adjusting your filters or generating some new content.</p>
    </div>
  );
};
