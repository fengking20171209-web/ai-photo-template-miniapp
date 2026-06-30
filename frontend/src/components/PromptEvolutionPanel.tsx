import React, { useState, useEffect } from 'react';
import { EvolutionRun, EvolutionCandidate } from '../types/evolution';
import { createEvolutionRun, getEvolutionRuns, getCandidates, promoteCandidate, rejectCandidate, getBaseVersion } from '../api/evolution';
import { PromptCandidateList } from './PromptCandidateList';
import { PromptABCompare } from './PromptABCompare';

interface Props {
  baseVersionId: number;
  onClose: () => void;
}

export const PromptEvolutionPanel: React.FC<Props> = ({ baseVersionId, onClose }) => {
  const [runs, setRuns] = useState<EvolutionRun[]>([]);
  const [activeRun, setActiveRun] = useState<EvolutionRun | null>(null);
  const [candidates, setCandidates] = useState<EvolutionCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [compareCandidate, setCompareCandidate] = useState<EvolutionCandidate | null>(null);
  const [baseContent, setBaseContent] = useState<string>('');
  const [promptId, setPromptId] = useState<number | null>(null);

  useEffect(() => {
    init();
  }, []);

  const init = async () => {
    try {
      const version = await getBaseVersion(baseVersionId);
      setBaseContent(version.content);
      setPromptId(version.prompt_id);
      loadRuns(version.prompt_id);
    } catch(err) {
      console.error(err);
    }
  }

  const loadRuns = async (pId: number) => {
    try {
      const runData = await getEvolutionRuns(pId);
      setRuns(runData);
      if (runData.length > 0) {
        selectRun(runData[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const selectRun = async (run: EvolutionRun) => {
    setActiveRun(run);
    try {
      const c = await getCandidates(run.id);
      setCandidates(c);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateRun = async () => {
    if (!promptId) return;
    setLoading(true);
    try {
      const newRun = await createEvolutionRun(promptId, baseVersionId);
      await loadRuns(promptId);
      selectRun(newRun);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePromote = async (id: number) => {
    try {
      await promoteCandidate(id, 'Promoted from UI');
      if (activeRun) selectRun(activeRun); // Refresh
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (id: number) => {
    try {
      await rejectCandidate(id);
      if (activeRun) selectRun(activeRun); // Refresh
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-gray-50 rounded-lg shadow-xl w-full max-w-6xl h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="p-4 bg-white border-b flex justify-between items-center">
          <h2 className="text-xl font-bold">Prompt Evolution Engine</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800 text-xl">&times;</button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar for runs */}
          <div className="w-64 bg-white border-r overflow-y-auto p-4 flex flex-col gap-2">
            <button 
              onClick={handleCreateRun} 
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Generating...' : '+ New Evolution Run'}
            </button>
            <hr className="my-2" />
            <h3 className="font-bold text-sm text-gray-500 uppercase">Previous Runs</h3>
            {runs.map(r => (
              <div 
                key={r.id} 
                onClick={() => selectRun(r)}
                className={`p-2 rounded cursor-pointer border ${activeRun?.id === r.id ? 'bg-blue-50 border-blue-300' : 'bg-gray-50 hover:bg-gray-100'}`}
              >
                <div className="text-sm font-semibold">Run #{r.id}</div>
                <div className="text-xs text-gray-500">{new Date(r.created_at).toLocaleString()}</div>
              </div>
            ))}
            {runs.length === 0 && <div className="text-sm text-gray-400">No previous runs found.</div>}
          </div>

          {/* Main content for candidates */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeRun ? (
              <>
                <div className="mb-4">
                  <h3 className="text-lg font-bold">Candidates for Run #{activeRun.id}</h3>
                  <p className="text-sm text-gray-500">Base Version ID: {activeRun.base_version_id}</p>
                </div>
                <PromptCandidateList 
                  candidates={candidates} 
                  onPromote={handlePromote} 
                  onReject={handleReject} 
                  onCompare={setCompareCandidate} 
                />
              </>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                Select or create a run to view candidates.
              </div>
            )}
          </div>
        </div>
      </div>

      {compareCandidate && (
        <PromptABCompare 
          baseText={baseContent} 
          candidate={compareCandidate} 
          onClose={() => setCompareCandidate(null)} 
        />
      )}
    </div>
  );
};
