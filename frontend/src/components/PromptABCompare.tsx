import React from 'react';
import { EvolutionCandidate } from '../types/evolution';

interface Props {
  baseText: string;
  candidate: EvolutionCandidate;
  onClose: () => void;
}

export const PromptABCompare: React.FC<Props> = ({ baseText, candidate, onClose }) => {
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[80vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-xl font-bold">A/B Compare</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800 text-xl">&times;</button>
        </div>
        <div className="flex flex-col md:flex-row flex-1 overflow-hidden">
          <div className="flex-1 p-4 border-r flex flex-col">
            <h3 className="font-bold text-gray-700 mb-2">Base Version</h3>
            <div className="flex-1 overflow-auto bg-gray-50 p-4 font-mono text-sm border rounded">
              {baseText}
            </div>
          </div>
          <div className="flex-1 p-4 flex flex-col">
            <h3 className="font-bold text-blue-700 mb-2">Variant (Strategy: {candidate.strategy})</h3>
            <div className="flex-1 overflow-auto bg-blue-50 p-4 font-mono text-sm border border-blue-200 rounded">
              {candidate.variant_text}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
