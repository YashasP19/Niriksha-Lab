import type { ReactNode } from 'react';

export default function PageLayout({ children }: { children: ReactNode }) {
  return (
    <main style={{
      maxWidth: 1280, margin: '0 auto',
      padding: 'var(--space-lg) var(--space-xl) var(--space-2xl)',
      display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)',
    }}>
      {children}
    </main>
  );
}
