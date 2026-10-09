import { useEffect } from 'react';
import { useOrchestrationStore } from './stores/orchestrationStore';
import Header from './components/layout/Header';
import PageLayout from './components/layout/PageLayout';
import InputPanel from './components/input/InputPanel';
import AgentPipeline from './components/pipeline/AgentPipeline';
import ImageCompare from './components/viewer/ImageCompare';
import SpecDefectPanel from './components/crossref/SpecDefectPanel';
import DiagnosisDashboard from './components/diagnosis/DiagnosisDashboard';

export default function App() {
  const {
    fetchDemoCase, fetchModels,
    result, error, isRunning, agentStatuses, currentAgentName,
  } = useOrchestrationStore();

  useEffect(() => {
    fetchModels();
    fetchDemoCase();
  }, [fetchModels, fetchDemoCase]);

  const allDone = agentStatuses.every((s) => s === 'done');
  const anyActive = agentStatuses.some((s) => s !== 'idle');
  const doneCount = agentStatuses.filter((s) => s === 'done').length;

  return (
    <>
      <Header />
      <PageLayout>
        {/* INPUT - always present, auto-collapses on run */}
        <InputPanel />

        {/* AGENT PIPELINE - visible once running or done */}
        {anyActive && <AgentPipeline />}

        {/* Running indicator */}
        {isRunning && !allDone && (
          <div style={{
            textAlign: 'center', padding: 'var(--space-md) 0',
            animation: 'fadeIn 0.3s ease',
          }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 12,
              padding: '12px 28px', borderRadius: 'var(--radius)',
              background: 'var(--card)',
              border: '1px solid var(--accent-border)',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <span style={{
                display: 'inline-block', width: 18, height: 18,
                border: '2.5px solid var(--border)',
                borderTopColor: 'var(--accent)', borderRadius: '50%',
                animation: 'spin-ring 0.8s linear infinite',
              }} />
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontSize: '0.9375rem', color: 'var(--text)', fontWeight: 600 }}>
                  {currentAgentName || 'Initializing pipeline...'}
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                  Agent {doneCount + 1} of 5 {result ? '-- Processing results' : '-- Waiting for Gemma response'}
                </div>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="card" style={{
            padding: 'var(--space-md)',
            color: 'var(--danger)', fontSize: '0.875rem',
          }}>
            {error}
          </div>
        )}

        {/* Results */}
        {result && allDone && (
          <div style={{
            display: 'flex', flexDirection: 'column',
            gap: 'var(--space-lg)',
            animation: 'fadeUp 0.6s ease',
          }}>
            <ImageCompare />

            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1.8fr',
              gap: 'var(--space-lg)',
            }}>
              <section className="card" style={{ padding: 'var(--space-lg)' }}>
                <SpecDefectPanel />
              </section>
              <section className="card" style={{ padding: 'var(--space-lg)' }}>
                <DiagnosisDashboard />
              </section>
            </div>
          </div>
        )}
      </PageLayout>
    </>
  );
}
