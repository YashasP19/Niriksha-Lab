export type Severity = "low" | "medium" | "high";

export interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface DetectedDefect {
  defect_type: string;
  severity: Severity;
  description: string;
  bounding_box: BoundingBox;
}

export interface AnalysisResult {
  defects: DetectedDefect[];
  total_defects: number;
  template_image: string;
  annotated_image: string;
  diff_summary: string;
}

export interface TemplateStatus {
  exists: boolean;
  image: string | null;
}
