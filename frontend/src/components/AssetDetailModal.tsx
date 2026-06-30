import React, { useState } from 'react';
import { Asset } from '../types/assets';
import { createEvaluation } from '../api/evolution';
import { PromptEvolutionPanel } from './PromptEvolutionPanel';

interface AssetDetailModalProps {
  asset: Asset | null;
  onClose: () => void;
}

export const AssetDetailModal: React.FC<AssetDetailModalProps> = ({ asset, onClose }) => {
  const [showEvolution, setShowEvolution] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [score, setScore] = useState(5);
  const [feedback, setFeedback] = useState('');

  if (!asset) return null;

  const imageUrl = asset.file_url || asset.thumbnail_path;

  const formatBytes = (bytes?: number) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const handleCopyId = (id: number) => {
    navigator.clipboard.writeText(id.toString());
  };

  const submitEvaluation = async () => {
    if (!asset.prompt_version_id) return alert('No prompt version associated with this asset.');
    try {
      await createEvaluation(asset.id, asset.prompt_version_id, score, feedback);
      alert('Evaluation submitted successfully!');
      setEvaluating(false);
    } catch (err) {
      alert('Failed to submit evaluation.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col md:flex-row overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Left: Image Preview */}
        <div className="flex-1 bg-gray-100 flex items-center justify-center p-4 relative overflow-auto">
          {imageUrl ? (
            <img src={imageUrl} alt={asset.title || 'Preview'} className="max-w-full max-h-[80vh] object-contain shadow-sm" />
          ) : (
            <div className="text-gray-500">No Preview Available</div>
          )}
        </div>

        {/* Right: Details Panel */}
        <div className="w-full md:w-80 bg-white border-l border-gray-200 flex flex-col overflow-y-auto p-6 space-y-6">
          <div className="flex justify-between items-start">
            <h2 className="text-xl font-bold text-gray-800 break-words">{asset.title || 'Untitled Asset'}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-1"
              title="Close"
            >
              ❌
            </button>
          </div>

          <div className="space-y-4 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Asset ID</span>
                <span className="font-mono bg-gray-50 px-2 py-1 rounded border">{asset.id}</span>
              </div>
              <button 
                onClick={() => handleCopyId(asset.id)}
                className="text-blue-500 hover:text-blue-600 text-xs px-2 py-1 border border-blue-200 rounded"
              >
                Copy ID
              </button>
            </div>

            {asset.description && (
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Description</span>
                <p className="whitespace-pre-wrap">{asset.description}</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Type</span>
                <span>{asset.asset_type || 'Unknown'}</span>
              </div>
              <div>
                <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Source</span>
                <span>{asset.source || 'Unknown'}</span>
              </div>

              {asset.width && asset.height && (
                <div>
                  <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Dimensions</span>
                  <span>{asset.width} × {asset.height}</span>
                </div>
              )}

              {asset.file_size && (
                <div>
                  <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Size</span>
                  <span>{formatBytes(asset.file_size)}</span>
                </div>
              )}
            </div>
            
            {/* Traceability Fields */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Traceability</h3>
              <div className="space-y-2">
                {asset.task_id && (
                  <div className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span className="text-gray-500">Task ID</span>
                    <span className="font-mono">{asset.task_id}</span>
                  </div>
                )}
                {asset.task_chain_id && (
                  <div className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span className="text-gray-500">Chain ID</span>
                    <span className="font-mono">{asset.task_chain_id}</span>
                  </div>
                )}
                {asset.prompt_version_id && (
                  <div className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span className="text-gray-500">Prompt Version</span>
                    <span className="font-mono">{asset.prompt_version_id}</span>
                  </div>
                )}
                {!asset.task_id && !asset.task_chain_id && !asset.prompt_version_id && (
                  <div className="text-gray-400 text-xs italic">No traceability data available.</div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-gray-100">
              <span className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Created At</span>
              <span>{new Date(asset.created_at).toLocaleString()}</span>
            </div>

            {asset.prompt_version_id && (
              <div className="pt-4 mt-4 border-t border-gray-200 flex flex-col gap-2">
                {evaluating ? (
                  <div className="bg-gray-50 p-3 rounded border border-gray-200 flex flex-col gap-2">
                    <h4 className="text-sm font-bold">Evaluate Generation</h4>
                    <div className="flex items-center gap-2">
                      <span className="text-sm">Score:</span>
                      <input type="number" min="1" max="10" value={score} onChange={e => setScore(Number(e.target.value))} className="border px-2 py-1 w-16 text-sm" />
                    </div>
                    <textarea value={feedback} onChange={e => setFeedback(e.target.value)} placeholder="Feedback..." className="border p-2 text-sm w-full" rows={2} />
                    <div className="flex gap-2">
                      <button onClick={submitEvaluation} className="bg-blue-600 text-white px-3 py-1 rounded text-sm">Submit</button>
                      <button onClick={() => setEvaluating(false)} className="bg-gray-300 px-3 py-1 rounded text-sm">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <button onClick={() => setEvaluating(true)} className="flex-1 bg-white border border-blue-600 text-blue-600 py-2 rounded font-semibold hover:bg-blue-50 transition-colors">
                      ⭐ 评价结果
                    </button>
                    <button onClick={() => setShowEvolution(true)} className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 rounded font-semibold hover:from-blue-700 hover:to-indigo-700 transition-colors shadow-sm">
                      ✨ 优化 Prompt
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {showEvolution && asset.prompt_version_id && (
        <PromptEvolutionPanel 
          baseVersionId={asset.prompt_version_id} 
          onClose={() => setShowEvolution(false)} 
        />
      )}
    </div>
  );
};
