interface Props {
  label: string;
  confidence: number;
  x: number;
  y: number;
}

export default function BboxTooltip({ label, confidence, x, y }: Props) {
  return (
    <div style={{
      position: 'absolute', left: x, top: y - 38,
      background: 'rgba(44,36,22,0.9)', backdropFilter: 'blur(8px)',
      color: '#fff', padding: '6px 12px', borderRadius: 6,
      fontSize: '0.8125rem', fontWeight: 500, whiteSpace: 'nowrap',
      pointerEvents: 'none', zIndex: 10, transform: 'translateX(-50%)',
      border: '1px solid rgba(255,255,255,0.15)',
    }}>
      {label} <span style={{ color: '#93c5fd' }}>({Math.round(confidence * 100)}%)</span>
    </div>
  );
}
