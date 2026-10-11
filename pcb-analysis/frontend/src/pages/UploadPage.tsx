import { useState, useEffect } from "react";
import ImageUploader from "../components/ImageUploader";
import DefectOverlay from "../components/DefectOverlay";
import DefectTable from "../components/DefectTable";
import AnalysisSummary from "../components/AnalysisSummary";
import { uploadTemplate, getTemplateStatus, analyzeImage } from "../api/client";
import type { AnalysisResult, TemplateStatus } from "../types";

export default function UploadPage() {
  const [template, setTemplate] = useState<TemplateStatus>({
    exists: false,
    image: null,
  });
  const [templateLoading, setTemplateLoading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTemplateStatus()
      .then(setTemplate)
      .catch(() => {});
  }, []);

  const handleTemplateUpload = async (file: File) => {
    setTemplateLoading(true);
    setError(null);
    try {
      await uploadTemplate(file);
      const status = await getTemplateStatus();
      setTemplate(status);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Template upload failed");
    } finally {
      setTemplateLoading(false);
    }
  };

  const handleTestImage = async (file: File) => {
    setPreview(URL.createObjectURL(file));
    setAnalysis(null);
    setError(null);
    setLoading(true);

    try {
      const result = await analyzeImage(file);
      setAnalysis(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Section 1: Template Upload */}
      <h2 style={{ marginBottom: 16, fontSize: 22 }}>Reference Template</h2>
      <div
        style={{
          border: `2px solid ${template.exists ? "#22c55e" : "#475569"}`,
          borderRadius: 12,
          padding: 20,
          marginBottom: 32,
        }}
      >
        {template.exists && template.image ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 20,
              flexWrap: "wrap",
            }}
          >
            <img
              src={`data:image/png;base64,${template.image}`}
              alt="Template"
              style={{
                maxWidth: 200,
                maxHeight: 150,
                borderRadius: 8,
                border: "1px solid #334155",
              }}
            />
            <div>
              <p style={{ color: "#22c55e", fontWeight: 600, marginBottom: 8 }}>
                Template loaded
              </p>
              <p style={{ color: "#94a3b8", fontSize: 14 }}>
                Upload a new image to replace the current template.
              </p>
            </div>
          </div>
        ) : (
          <p style={{ color: "#94a3b8", marginBottom: 12 }}>
            Upload a known-good Arduino Uno R3 reference image.
          </p>
        )}
        <div style={{ marginTop: template.exists ? 16 : 0 }}>
          <ImageUploader
            onFileSelected={handleTemplateUpload}
            label="template"
          />
        </div>
        {templateLoading && (
          <p style={{ color: "#94a3b8", marginTop: 12 }}>
            Uploading template...
          </p>
        )}
      </div>

      {/* Section 2: Test Image Upload */}
      <h2 style={{ marginBottom: 16, fontSize: 22 }}>Test Image</h2>
      {!template.exists ? (
        <div
          style={{
            padding: 32,
            textAlign: "center",
            color: "#64748b",
            border: "2px dashed #334155",
            borderRadius: 12,
          }}
        >
          Upload a reference template first to enable analysis.
        </div>
      ) : (
        <ImageUploader onFileSelected={handleTestImage} label="test" />
      )}

      {loading && (
        <div
          style={{
            textAlign: "center",
            padding: 48,
            color: "#94a3b8",
          }}
        >
          <div
            style={{
              display: "inline-block",
              width: 32,
              height: 32,
              border: "3px solid #334155",
              borderTopColor: "#3b82f6",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
            }}
          />
          <p style={{ marginTop: 12 }}>
            Analyzing differences with Gemini...
          </p>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {error && (
        <div
          style={{
            marginTop: 20,
            padding: 16,
            background: "#450a0a",
            borderRadius: 8,
            color: "#fca5a5",
          }}
        >
          {error}
        </div>
      )}

      {analysis && (
        <div style={{ marginTop: 24 }}>
          <AnalysisSummary result={analysis} />

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 20,
              marginBottom: 24,
            }}
          >
            <div>
              <h3
                style={{
                  marginBottom: 10,
                  fontSize: 14,
                  color: "#94a3b8",
                }}
              >
                REFERENCE (TEMPLATE)
              </h3>
              <img
                src={`data:image/png;base64,${analysis.template_image}`}
                alt="Reference template"
                style={{
                  maxWidth: "100%",
                  borderRadius: 8,
                  border: "1px solid #22c55e",
                }}
              />
            </div>
            {preview && (
              <div>
                <h3
                  style={{
                    marginBottom: 10,
                    fontSize: 14,
                    color: "#94a3b8",
                  }}
                >
                  TEST IMAGE
                </h3>
                <img
                  src={preview}
                  alt="Test image"
                  style={{
                    maxWidth: "100%",
                    borderRadius: 8,
                    border: "1px solid #334155",
                  }}
                />
              </div>
            )}
            <div>
              <h3
                style={{
                  marginBottom: 10,
                  fontSize: 14,
                  color: "#94a3b8",
                }}
              >
                ANNOTATED
              </h3>
              <DefectOverlay annotatedImageBase64={analysis.annotated_image} />
            </div>
          </div>

          <h3 style={{ marginBottom: 12, fontSize: 16 }}>Detected Defects</h3>
          <DefectTable defects={analysis.defects} />
        </div>
      )}
    </div>
  );
}
