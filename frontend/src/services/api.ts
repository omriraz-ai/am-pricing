const BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://am-pricing.onrender.com/api/v1";
async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "שגיאת תקשורת" }));
    throw new Error(err.detail || "שגיאה לא ידועה");
  }
  return res.json();
}

// ── פרויקטים ──────────────────────────────────────
export const getProjects = () => req<Project[]>("/projects/");
export const getProject  = (id: string) => req<Project>(`/projects/${id}/`);
export const createProject = (data: ProjectCreate) =>
  req<Project>("/projects/", { method: "POST", body: JSON.stringify(data) });
export const updateProject = (id: string, data: Partial<ProjectCreate>) =>
  req<Project>(`/projects/${id}/`, { method: "PATCH", body: JSON.stringify(data) });
export const deleteProject = (id: string) =>
  req<{ message: string }>(`/projects/${id}/`, { method: "DELETE" });

// עדכון סטטוס עסקי בלבד — פאזה 1
export const updateBusinessStatus = (
  id: string,
  business_status: string,
  is_archived?: boolean,
) =>
  req<Project>(`/projects/${id}/business-status`, {
    method: "PATCH",
    body: JSON.stringify({ business_status, is_archived }),
  });

// ── תמחור ─────────────────────────────────────────
export const calculatePricing = (projectId: string) =>
  req<CalculationResult>("/pricing/calculate", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, override_timeline: false }),
  });

// ── אישור ─────────────────────────────────────────
export const confirmApproval = (projectId: string, notes?: string) =>
  req<{ message: string; final_fee: number; final_fee_per_unit: number }>(
    "/approval/confirm",
    { method: "POST", body: JSON.stringify({ project_id: projectId, notes }) }
  );

// תיקון: השרת שולף את הסכום מה-DB — לא שולחים approved_fee מהלקוח
export const saveToDb = (projectId: string) =>
  req<{ message: string; reference_id: string; approved_fee: number }>(
    "/approval/save-to-db",
    {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        source_label: "הזנה ידנית מאושרת",
      }),
    }
  );

// ── הצעה ──────────────────────────────────────────
export const downloadProposal = async (projectId: string, projectName: string) => {
  const res = await fetch(`${BASE}/proposal/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId }),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error("DOCX download failed:", text);
    throw new Error("שגיאה ביצירת ההצעה");
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `proposal_${projectId}.docx`;

  document.body.appendChild(a);
  a.click();
  a.remove();

  window.URL.revokeObjectURL(url);
};

export const getProposalPreviewUrl = (projectId: string) =>
  `${BASE}/proposal/${projectId}/preview`;

// ── בסיס נתונים ────────────────────────────────────
export const getReferenceProjects = () => req<ReferenceProject[]>("/reference/projects");



// ── טיפוסים ────────────────────────────────────────
export interface Project {
  id: string;
  status: string;
  is_test: boolean;
  is_exception_pricing: boolean;
  exception_pricing_override?: ExceptionPricingOverride;
  business_status: string;
  is_archived: boolean;
  project_name: string;
  client_name: string;
  location_city: string;
  project_type: string;
  num_units: number;
  num_floors_above: number;
  execution_phases: number;
  pricing_mode?: string;
  num_buildings?: number;
  num_floors_underground?: number;
  plot_area_sqm?: number;
  timeline_planning?: number;
  timeline_excavation?: number;
  timeline_underground?: number;
  timeline_above_ground?: number;
  timeline_finishes?: number;
  timeline_handover?: number;
  manual_complexity_multiplier: number;
  manual_override_reason?: string;
  index_type?: string;
  includes_vat: boolean;
  notes_pricing?: string;
  calculation_result?: CalculationResult;
  created_at?: string;
}
export type ExceptionPricingOverride = {
  schedule?: {
    planning?: number;
    excavation?: number;
    underground?: number;
    above_ground?: number;
    finishes?: number;
    handover?: number;
  };
  blended_total?: number;
  blended_per_unit?: number;
};
export interface ProjectCreate {
  project_name: string;
  client_name: string;
  location_city: string;
  project_type: string;
  num_units: number;
  num_floors_above: number;
  execution_phases: number;
  is_test?: boolean;
  is_exception_pricing?: boolean;
  exception_pricing_override?: ExceptionPricingOverride;
  pricing_mode?: string;
  num_buildings?: number;
  num_floors_underground?: number;
  plot_area_sqm?: number;
  timeline_planning?: number;
  timeline_excavation?: number;
  timeline_underground?: number;
  timeline_above_ground?: number;
  timeline_finishes?: number;
  timeline_handover?: number;
  manual_complexity_multiplier?: number;
  manual_override_reason?: string;
  index_type?: string;
  includes_vat?: boolean;
  notes_pricing?: string;
}

export interface PhaseResult {
  phase_name: string;
  months: number;
  base_rate: number;
  adjusted_rate: number;
  phase_total: number;
}

export interface ComparableProject {
  project_name: string;
  location_city: string;
  project_type: string;
  num_units: number;
  num_floors_above?: number;
  execution_phases: number;
  fee_per_unit: number;
  total_fee?: number;
  tier?: string;
  source_type: string;
  similarity_score: number;
  match_level: string;
  score_breakdown: {
    units: number;
    project_type: number;
    city: number;
    floors: number;
    phases: number;
  };
}

export interface CalculationResult {
  tier: string;
  multiplier_project_type: number;
  multiplier_region: number;
  multiplier_phases: number;
  multiplier_manual: number;
  schedule: {
    planning: number;
    excavation: number;
    underground: number;
    above_ground: number;
    finishes: number;
    handover: number;
    total_months: number;
    source_note: string;
  };
  phase_costs: PhaseResult[];
  rules_engine_total: number;
  rules_engine_per_unit: number;
  comparable_projects: ComparableProject[];
  num_comparable_above_threshold: number;
  reference_price_per_unit?: number;
  blended_total: number;
  blended_per_unit: number;
  price_range_low: number;
  price_range_high: number;
  flags: {
    price_status_code: "LOW" | "OK" | "HIGH";
    price_status_label: string;
    recommendation?: string;
    num_comparables: number;
    low_comparables_warning: boolean;
    override_active: boolean;
    override_reason?: string;
    missing_fields: string[];
  };
}

export interface ReferenceProject {
  id: string;
  project_name: string;
  location_city: string;
  project_type: string;
  num_units: number;
  fee_per_unit?: number;
  total_fee?: number;
  tier?: string;
  source_type: string;
}
