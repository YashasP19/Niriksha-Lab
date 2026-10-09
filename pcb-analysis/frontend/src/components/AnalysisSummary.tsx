import type { AnalysisResult } from "../types";

interface Props {
  result: AnalysisResult;
}

export default function AnalysisSummary({ result }: Props) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: 16,
        marginBottom: 24,
      }}
    >
      <div
        style={{
          background: "#1e293b",
          borderRadius: 10,
          padding: 20,
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 36, fontWeight: 700 }}>
          {result.total_defects}
        </div>
        <div style={{ color: "#94a3b8", fontSize: 14 }}>Total Defects</div>
      </div>

      <div
        style={{
          background: "#1e293b",
          borderRadius: 10,
          padding: 20,
          gridColumn: "1 / -1",
        }}
      >
        <div style={{ color: "#94a3b8", fontSize: 12, marginBottom: 6 }}>
          DIFF SUMMARY
        </div>
        <div style={{ fontSize: 14, lineHeight: 1.6 }}>
          {result.diff_summary}
        </div>
      </div>
    </div>
  );
}
