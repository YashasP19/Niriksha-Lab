import { useCallback, useState, type DragEvent, type ChangeEvent } from "react";

interface Props {
  onFileSelected: (file: File) => void;
  multiple?: boolean;
  onFilesSelected?: (files: File[]) => void;
  label?: string;
}

export default function ImageUploader({
  onFileSelected,
  multiple,
  onFilesSelected,
  label,
}: Props) {
  const [dragging, setDragging] = useState(false);
  const inputId = `file-input-${label ?? "default"}`;

  const handleFiles = useCallback(
    (files: FileList) => {
      const imageFiles = Array.from(files).filter((f) =>
        f.type.startsWith("image/")
      );
      if (multiple && onFilesSelected) {
        onFilesSelected(imageFiles);
      } else if (imageFiles[0]) {
        onFileSelected(imageFiles[0]);
      }
    },
    [onFileSelected, onFilesSelected, multiple]
  );

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) handleFiles(e.target.files);
    },
    [handleFiles]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${dragging ? "#3b82f6" : "#475569"}`,
        borderRadius: 12,
        padding: 48,
        textAlign: "center",
        cursor: "pointer",
        background: dragging ? "#1e293b" : "#0f172a",
        transition: "all 0.2s",
      }}
      onClick={() => document.getElementById(inputId)?.click()}
    >
      <input
        id={inputId}
        type="file"
        accept="image/*"
        multiple={multiple}
        onChange={handleChange}
        style={{ display: "none" }}
      />
      <p style={{ fontSize: 18, marginBottom: 8 }}>
        {dragging ? "Drop image(s) here" : "Drag & drop image(s) here"}
      </p>
      <p style={{ color: "#94a3b8", fontSize: 14 }}>
        or click to browse files (JPG, PNG, BMP)
      </p>
    </div>
  );
}
