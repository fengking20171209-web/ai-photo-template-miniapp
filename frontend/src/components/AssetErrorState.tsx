import React from 'react';

interface AssetErrorStateProps {
  error: Error;
  onRetry: () => void;
}

export const AssetErrorState: React.FC<AssetErrorStateProps> = ({ error, onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-red-500 h-full min-h-[300px]">
      <div className="text-4xl mb-4">⚠️</div>
      <h3 className="text-lg font-medium text-red-700">Failed to Load Assets</h3>
      <p className="text-sm mt-2 text-red-600">{error.message}</p>
      <button 
        className="mt-4 px-4 py-2 bg-red-100 text-red-700 hover:bg-red-200 rounded transition-colors"
        onClick={onRetry}
      >
        Retry
      </button>
    </div>
  );
};
