import React from 'react';
import { EvolutionCandidate } from '../types/evolution';

interface Props {
  candidate: EvolutionCandidate;
  onPromote: (id: number) => void;
  onReject: (id: number) => void;
  onCompare: (candidate: EvolutionCandidate) => void;
}

export const PromptCandidateCard: React.FC<Props> = ({ candidate, onPromote, onReject, onCompare }) => {
  return (
    <div className="border rounded p-4 shadow-sm bg-white flex flex-col gap-3">
      <div className="flex justify-between items-center">
        <span className="text-sm font-semibold bg-blue-100 text-blue-800 px-2 py-1 rounded">Strategy: {candidate.strategy}</span>
        <span className={`text-xs px-2 py-1 rounded ${candidate.status === 'promoted' ? 'bg-green-100 text-green-800' : candidate.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
          {candidate.status.toUpperCase()}
        </span>
      </div>
      <p className="text-gray-700 font-mono text-sm break-words whitespace-pre-wrap">{candidate.variant_text}</p>
      {candidate.status === 'pending' && (
        <div className="flex gap-2 mt-auto">
          <button className="flex-1 bg-green-500 text-white py-1 rounded text-sm hover:bg-green-600" onClick={() => onPromote(candidate.id)}>Promote</button>
          <button className="flex-1 bg-red-500 text-white py-1 rounded text-sm hover:bg-red-600" onClick={() => onReject(candidate.id)}>Reject</button>
          <button className="flex-1 bg-blue-500 text-white py-1 rounded text-sm hover:bg-blue-600" onClick={() => onCompare(candidate)}>Compare</button>
        </div>
      )}
    </div>
  );
};
