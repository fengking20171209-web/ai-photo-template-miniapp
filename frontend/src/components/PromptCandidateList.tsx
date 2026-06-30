import React from 'react';
import { EvolutionCandidate } from '../types/evolution';
import { PromptCandidateCard } from './PromptCandidateCard';

interface Props {
  candidates: EvolutionCandidate[];
  onPromote: (id: number) => void;
  onReject: (id: number) => void;
  onCompare: (candidate: EvolutionCandidate) => void;
}

export const PromptCandidateList: React.FC<Props> = ({ candidates, onPromote, onReject, onCompare }) => {
  if (!candidates || candidates.length === 0) {
    return <div className="text-gray-500 text-center py-4">No candidates available.</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {candidates.map(c => (
        <PromptCandidateCard 
          key={c.id} 
          candidate={c} 
          onPromote={onPromote} 
          onReject={onReject} 
          onCompare={onCompare} 
        />
      ))}
    </div>
  );
};
