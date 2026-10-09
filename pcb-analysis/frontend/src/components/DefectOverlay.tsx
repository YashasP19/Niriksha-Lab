interface Props {
  annotatedImageBase64: string;
  originalImageUrl?: string;
}

export default function DefectOverlay({ annotatedImageBase64 }: Props) {
  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <img
        src={`data:image/png;base64,${annotatedImageBase64}`}
        alt="Annotated PCB"
        style={{ maxWidth: "100%", borderRadius: 8, border: "1px solid #334155" }}
      />
    </div>
  );
}
