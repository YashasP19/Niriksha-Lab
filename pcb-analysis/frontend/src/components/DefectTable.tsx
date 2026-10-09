import type { DetectedDefect } from "../types";

interface Props {
  defects: DetectedDefect[];
}

const severityColors: Record<string, string> = {
  low: "#22c55e",
  medium: "#eab308",
  high: "#ef4444",
};

export default function DefectTable({ defects }: Props) {
  if (defects.length === 0) {
    return <p style={{ color: "#94a3b8", padding: 16 }}>No defects detected.</p>;
  }

  return (
    <div style={{ overflowX: "auto" }}>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 14,
        }}
      >
        <thead>
          <tr
            style={{
              borderBottom: "2px solid #334155",
              textAlign: "left",
            }}
          >
            <th style={{ padding: "10px 12px" }}>Type</th>
            <th style={{ padding: "10px 12px" }}>Severity</th>
            <th style={{ padding: "10px 12px" }}>Description</th>
            <th style={{ padding: "10px 12px" }}>Location</th>
          </tr>
        </thead>
        <tbody>
          {defects.map((d, i) => (
            <tr
              key={i}
              style={{ borderBottom: "1px solid #1e293b" }}
            >
              <td style={{ padding: "10px 12px", fontWeight: 600 }}>
                {d.defect_type}
              </td>
              <td style={{ padding: "10px 12px" }}>
                <span
                  style={{
                    color: severityColors[d.severity] ?? "#94a3b8",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    fontSize: 12,
                  }}
                >
                  {d.severity}
                </span>
              </td>
              <td style={{ padding: "10px 12px", maxWidth: 300 }}>
                {d.description}
              </td>
              <td style={{ padding: "10px 12px", fontSize: 12, color: "#94a3b8" }}>
                ({d.bounding_box.x_min}, {d.bounding_box.y_min}) - ({d.bounding_box.x_max}, {d.bounding_box.y_max})
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
