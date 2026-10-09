import { useEffect } from 'react';
import { useOrchestrationStore } from '../../stores/orchestrationStore';

export default function Header() {
  const {
    models, selectedModel, isRunning, backendAvailable,
    fetchModels, setSelectedModel,
    runDemo, runCustom, loadDemo,
  } = useOrchestrationStore();

  useEffect(() => { fetchModels(); }, [fetchModels]);

  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '16px 36px',
      background: 'linear-gradient(135deg, #faf8f4 0%, #f0ebe0 100%)',
      borderBottom: '1px solid var(--border)',
      position: 'sticky', top: 0, zIndex: 100,
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
        <span style={{
          fontSize: '1.75rem', fontWeight: 800, letterSpacing: '-0.03em',
          background: 'linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #7c3aed 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          Niriksha Lab
        </span>
        <span style={{
          fontSize: '0.8125rem', fontWeight: 500, letterSpacing: '0.06em',
          textTransform: 'uppercase',
          background: 'linear-gradient(90deg, var(--text-muted) 0%, var(--border-active) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          HW Verification
        </span>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          fontSize: '0.6875rem',
          color: backendAvailable ? 'var(--success)' : 'var(--warning)',
          fontWeight: 600,
        }}>
          <span style={{
            width: 5, height: 5, borderRadius: '50%',
            background: backendAvailable ? 'var(--success)' : 'var(--warning)',
          }} />
          {backendAvailable ? 'Connected' : 'Offline'}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        {models && (
          <select
            value={selectedModel ?? ''}
            onChange={(e) => setSelectedModel(e.target.value)}
            style={{ fontSize: '0.8125rem', padding: '8px 12px' }}
          >
            {models.available_models.map((m) => (
              <option key={m.name} value={m.name}>
                {m.display_name || m.name}
                {m.name === models.recommended_model ? ' (rec.)' : ''}
              </option>
            ))}
          </select>
        )}

        <button className="btn" disabled={isRunning} onClick={loadDemo}
          style={{ padding: '8px 16px', fontSize: '0.8125rem' }}
        >
          Load Demo
        </button>
        <button className="btn btn-accent" disabled={isRunning} onClick={runDemo}
          style={{ padding: '8px 24px', fontSize: '0.875rem' }}
        >
          {isRunning ? (
            <><Spinner /> Analyzing...</>
          ) : 'Run Demo'}
        </button>
        <button className="btn" disabled={isRunning || !backendAvailable} onClick={runCustom}
          title={!backendAvailable ? 'Requires backend connection' : ''}
          style={{ padding: '8px 16px', fontSize: '0.8125rem' }}
        >
          Run Custom
        </button>
      </div>
    </header>
  );
}

function Spinner() {
  return (
    <span style={{
      display: 'inline-block', width: 16, height: 16,
      border: '2px solid rgba(255,255,255,0.3)',
      borderTopColor: '#fff', borderRadius: '50%',
      animation: 'spin-ring 0.8s linear infinite',
    }} />
  );
}
