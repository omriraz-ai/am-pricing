"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getProject, calculatePricing, confirmApproval, saveToDb,
  downloadProposal, updateProject, updateBusinessStatus,
  Project, CalculationResult, ExceptionPricingOverride,
} from "@/services/api";

const fmt    = (n?: number) => n?.toLocaleString("he-IL", { maximumFractionDigits: 0 }) ?? "—";
const fmtILS = (n?: number) => n ? `${fmt(n)} ₪` : "—";

const BUSINESS_STATUS_OPTIONS = [
  { value: "בטיפול",   label: "בטיפול"    },
  { value: "הוגש",     label: "הוגש"      },
  { value: "זכינו",    label: "זכינו ✓"   },
  { value: "לא_זכינו", label: "לא זכינו"  },
  { value: "הסתיים",   label: "הסתיים"    },
];

const BUSINESS_STATUS_COLORS: Record<string, { color: string; bg: string }> = {
  "בטיפול":   { color: "#2E75B6", bg: "#eff6ff" },
  "הוגש":     { color: "#7c3aed", bg: "#f5f3ff" },
  "זכינו":    { color: "#16a34a", bg: "#f0fdf4" },
  "לא_זכינו": { color: "#dc2626", bg: "#fef2f2" },
  "הסתיים":   { color: "#6b7280", bg: "#f3f4f6" },
};

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject]       = useState<Project | null>(null);
  const [loading, setLoading]       = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [approving, setApproving]   = useState(false);
  const [saving, setSaving]         = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [updatingTest, setUpdatingTest]     = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [error, setError]           = useState("");
  const [showSaveConfirm, setShowSaveConfirm] = useState(false);
  const [overrideDraft, setOverrideDraft] = useState<ExceptionPricingOverride>({});
  const [savingOverride, setSavingOverride] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);

  const reload = () =>
    getProject(id).then(setProject).catch(() => setError("שגיאה בטעינה"));

  useEffect(() => {
    reload().finally(() => setLoading(false));
  }, [id]);
  useEffect(() => {
  const currentCalc = project?.calculation_result;

  if (!project?.is_exception_pricing || !currentCalc) return;

  setOverrideDraft(project.exception_pricing_override || {
    schedule: {
      planning: currentCalc.schedule.planning,
      excavation: currentCalc.schedule.excavation,
      underground: currentCalc.schedule.underground,
      above_ground: currentCalc.schedule.above_ground,
      finishes: currentCalc.schedule.finishes,
      handover: currentCalc.schedule.handover,
    },
    blended_total: currentCalc.blended_total,
    blended_per_unit: currentCalc.blended_per_unit,
  });
}, [project?.id, project?.is_exception_pricing, project?.calculation_result, project?.exception_pricing_override]);

  // ── טסט ────────────────────────────────────────────
  const handleToggleTest = async (newValue: boolean) => {
    setUpdatingTest(true); setError("");
    try {
      const updated = await updateProject(id, { is_test: newValue });
      setProject(updated);
    } catch (e: any) { setError(e.message); }
    finally { setUpdatingTest(false); }
  };

  // ── סטטוס עסקי ─────────────────────────────────────
  const handleStatusChange = async (newStatus: string) => {
    setUpdatingStatus(true); setError("");
    const shouldArchive = newStatus === "הסתיים";
    try {
      const updated = await updateBusinessStatus(id, newStatus, shouldArchive ? true : undefined);
      setProject(updated);
    } catch (e: any) { setError(e.message); }
    finally { setUpdatingStatus(false); }
  };

  // ── תמחור ───────────────────────────────────────────
  const handleCalculate = async () => {
    setCalculating(true); setError("");
    try {
      const result = await calculatePricing(id);
      setProject(prev => prev ? { ...prev, calculation_result: result, status: "calculated" } : prev);
    } catch (e: any) { setError(e.message); }
    finally { setCalculating(false); }
  };

  // ── אישור ───────────────────────────────────────────
  const handleApprove = async () => {
    if (!confirm("לאשר את ההצעה ולהמשיך ליצירת המסמך?")) return;
    setApproving(true); setError("");
    try {
      await confirmApproval(id);
      await reload();
      setShowSaveConfirm(true);
    } catch (e: any) { setError(e.message); }
    finally { setApproving(false); }
  };

  // ── שמירה לבסיס ────────────────────────────────────
  const handleSaveToDb = async () => {
    setSaving(true);
    try {
      // השרת שולף את הסכום מה-DB — לא שולחים fee מהלקוח
      await saveToDb(id);
      await reload();
      setShowSaveConfirm(false);
    } catch (e: any) { setError(e.message); }
    finally { setSaving(false); }
  };

  // ── הורדת DOCX ─────────────────────────────────────
  const handleDownload = async () => {
    if (!project) return;
    setDownloading(true);
    try { await downloadProposal(id, project.project_name); }
    catch (e: any) { setError(e.message); }
    finally { setDownloading(false); }
  };

  // ── render ──────────────────────────────────────────
  if (loading) return (
    <div className="container" style={{ textAlign: "center", paddingTop: 80 }}>
      <span className="spinner" />
    </div>
  );
  if (!project) return (
    <div className="container">
      <div className="alert alert-error">פרויקט לא נמצא</div>
    </div>
  );
  const setOverrideSchedule = (field: keyof NonNullable<ExceptionPricingOverride["schedule"]>, value: string) => {
  setOverrideDraft(prev => ({
    ...prev,
    schedule: {
      ...(prev.schedule || {}),
      [field]: value === "" ? undefined : Number(value),
    },
  }));
};

const setOverrideNumber = (field: "blended_total" | "blended_per_unit", value: string) => {
  setOverrideDraft(prev => ({
    ...prev,
    [field]: value === "" ? undefined : Number(value),
  }));
};

const handleSaveExceptionOverride = async () => {
  if (!project?.is_exception_pricing) return;

  setSavingOverride(true);
  setError("");

  try {
    await updateProject(id, {
      exception_pricing_override: overrideDraft,
    });

    const result = await calculatePricing(id);
    setProject(prev => prev ? {
      ...prev,
      exception_pricing_override: overrideDraft,
      calculation_result: result,
      status: "calculated",
    } : prev);
  } catch (e: any) {
    setError(e.message);
  } finally {
    setSavingOverride(false);
  }
};
const handleImportPreview = async () => {
  if (!importFile) return;

  const formData = new FormData();
  formData.append("file", importFile);

  const res = await fetch("http://127.0.0.1:8000/api/v1/import/excel-preview", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  console.log("IMPORT PREVIEW:", data);
};

  const calc  = project.calculation_result;
  const flags = calc?.flags;
  const statusCfg = BUSINESS_STATUS_COLORS[project.business_status] ?? BUSINESS_STATUS_COLORS["בטיפול"];

  return (
    <div className="container">
    <div className="card" style={{ marginBottom: 16 }}>
  <h2 className="section-title">Import Excel</h2>

  <input
    type="file"
    accept=".xlsx"
    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
  />

  <button
    className="btn btn-primary"
    type="button"
    onClick={handleImportPreview}
    style={{ marginRight: 8 }}
  >
    העלה קובץ לבדיקה
  </button>
</div>

      {/* באנר פרויקט טסט */}
      {project.is_test && (
        <div style={{
          background: "#fef3c7", border: "2px dashed #d97706",
          borderRadius: 8, padding: "12px 20px", marginBottom: 16,
          display: "flex", alignItems: "center", gap: 10,
          color: "#92400e", fontWeight: 700, fontSize: 15,
        }}>
          🧪 פרויקט טסט
          <span style={{ fontWeight: 400, fontSize: 13, color: "#b45309" }}>
            — פרויקט טסט לא נשמר לבסיס הנתונים. ניתן לחשב, לאשר ולהפיק מסמך לבדיקה בלבד.
          </span>
        </div>
      )}

      {project.is_exception_pricing && (
  <div style={{
    background: "#fee2e2",
    border: "2px solid #dc2626",
    borderRadius: 8,
    padding: "12px 20px",
    marginBottom: 16,
    display: "flex",
    alignItems: "center",
    gap: 10,
    color: "#7f1d1d",
    fontWeight: 700,
    fontSize: 15,
  }}>
    <span>⚠️ פרויקט בתמחור חריג</span>
    <span style={{ fontWeight: 400, fontSize: 13, color: "#991b1b" }}>
      — פרויקט זה לא נכנס לבסיס הנתונים הייחוסי ואינו משפיע על חישובי עלויות ולו"ז
    </span>
  </div>
)}

      {/* כותרת */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <Link href="/" style={{ color: "#6b7280", fontSize: 13 }}>← חזרה לרשימה</Link>
          <h1 className="page-title" style={{ marginTop: 8, marginBottom: 4 }}>{project.project_name}</h1>
          <p style={{ color: "#6b7280" }}>{project.client_name} | {project.location_city} | {project.project_type}</p>

          {/* Checkbox is_test */}
          <label style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8, cursor: "pointer", fontSize: 13 }}>
            <input
              type="checkbox"
              checked={project.is_test || false}
              disabled={updatingTest}
              onChange={e => handleToggleTest(e.target.checked)}
              style={{ width: 15, height: 15, accentColor: "#d97706" }}
            />
            <span style={{ color: "#b45309", fontWeight: project.is_test ? 700 : 400 }}>
              🧪 פרויקט טסט
            </span>
            {updatingTest && <span style={{ color: "#9ca3af", fontSize: 12 }}>מעדכן...</span>}
          </label>
        </div>

        {/* כפתורי פעולה */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          
          {project.status === "calculated" && (
            <button className="btn btn-success" onClick={handleApprove} disabled={approving}>
              {approving ? "מאשר..." : "✓ אשר ויצר הצעה"}
            </button>
          )}
          {(project.status === "approved" || project.status === "saved_to_db") && (
            <button className="btn btn-primary" onClick={handleDownload} disabled={downloading}>
              {downloading ? "מוריד..." : "הורד הצעה (DOCX)"}
            </button>
          )}
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* שאלת שמירה לבסיס — מותאמת לפרויקט טסט */}
      {showSaveConfirm && (
        project.is_test ? (
          <div className="card" style={{ background: "#fef9c3", border: "2px dashed #d97706" }}>
            <h3 style={{ color: "#92400e", marginBottom: 8 }}>🧪 ההצעה אושרה — מצב טסט</h3>
            <p style={{ marginBottom: 12 }}>
              פרויקט טסט לא נשמר לבסיס הנתונים. ניתן לחשב, לאשר ולהפיק מסמך לבדיקה בלבד.
            </p>
            <p style={{ marginBottom: 16, fontSize: 13, color: "#92400e" }}>
              כדי לשמור פרויקט אמיתי — צור פרויקט חדש ללא סימון "פרויקט טסט".
            </p>
            <button className="btn btn-ghost" onClick={() => setShowSaveConfirm(false)}>סגור</button>
          </div>
        ) : (
          <div className="card" style={{ background: "#f0fdf4", border: "2px solid #22c55e" }}>
            <h3 style={{ color: "#166534", marginBottom: 8 }}>✅ ההצעה אושרה!</h3>
            <p style={{ marginBottom: 16 }}>האם להוסיף את הפרויקט לבסיס הנתונים לצורך שיפור המודל?</p>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-success" onClick={handleSaveToDb} disabled={saving}>
                {saving ? "שומר..." : "☑ כן, הוסף לבסיס הנתונים"}
              </button>
              <button className="btn btn-ghost" onClick={() => setShowSaveConfirm(false)}>לא כעת</button>
            </div>
          </div>
        )
      )}

      <div className="split-layout">
        {/* עמודה ראשית */}
        <div>

          {/* נתוני פרויקט */}
          <div className="card">
            <h2 className="section-title">נתוני הפרויקט</h2>
            <div className="grid-2" style={{ gap: 8 }}>
              {[
                ["מספר יח\"ד", fmt(project.num_units)],
                ["קומות עיליות", project.num_floors_above],
                ["קומות מרתף", project.num_floors_underground ?? "—"],
                ["שלבי ביצוע", project.execution_phases],
                ["מספר מבנים", project.num_buildings ?? "—"],
                ["שטח מגרש", project.plot_area_sqm ? `${fmt(project.plot_area_sqm)} מ"ר` : "—"],
              ].map(([k, v]) => (
                <div key={String(k)} style={{ padding: "8px 0", borderBottom: "1px solid #f3f4f6" }}>
                  <span style={{ color: "#6b7280", fontSize: 13 }}>{k}</span>
                  <span style={{ float: "left", fontWeight: 600 }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* סטטוס עסקי */}
          <div className="card">
            <h2 className="section-title">סטטוס עסקי</h2>
            <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
              <div style={{ flex: 1, minWidth: 180 }}>
                <label style={{ fontSize: 13, color: "#6b7280", display: "block", marginBottom: 6 }}>
                  מצב מול הלקוח
                </label>
                <select
                  value={project.business_status || "בטיפול"}
                  disabled={updatingStatus}
                  onChange={e => handleStatusChange(e.target.value)}
                  style={{
                    width: "100%", padding: "9px 12px",
                    borderRadius: 8, border: "1px solid #d1d5db",
                    fontFamily: "inherit", fontSize: 14,
                    direction: "rtl", background: "#fff",
                    cursor: updatingStatus ? "wait" : "pointer",
                  }}
                >
                  {BUSINESS_STATUS_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {updatingStatus && (
                  <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                )}
                <span style={{
                  background: statusCfg.bg, color: statusCfg.color,
                  border: `1px solid ${statusCfg.color}40`,
                  padding: "5px 14px", borderRadius: 20,
                  fontSize: 13, fontWeight: 700,
                }}>
                  {BUSINESS_STATUS_OPTIONS.find(o => o.value === (project.business_status || "בטיפול"))?.label}
                </span>
              </div>
            </div>
            {project.is_archived && (
              <div className="alert alert-info" style={{ marginTop: 12, fontSize: 13 }}>
                🗄️ פרויקט זה מסומן לארכיון — לא יוצג ברשימה הפעילה.
              </div>
            )}
          </div>

          {/* תוצאות חישוב */}
          {calc && (
            <>
              {/* לוח זמנים */}
              <div className="card">
                <h2 className="section-title">לוח זמנים</h2>
                <table>
                  <thead><tr><th>שלב</th><th>חודשים</th></tr></thead>
                  <tbody>
                    {[
                      ["תכנון ורישוי",     calc.schedule.planning],
                      ["חפירה ודיפון",     calc.schedule.excavation],
                      ["שלד תת\"ק",        calc.schedule.underground],
                      ["שלד עילי",         calc.schedule.above_ground],
                      ["גמרים / מעטפת",   calc.schedule.finishes],
                      ["מסירות / טופס 4", calc.schedule.handover],
                    ].map(([name, months]) => (
                      <tr key={String(name)}><td>{name}</td><td>{months}</td></tr>
                    ))}
                    <tr style={{ fontWeight: 700, background: "#f8faff" }}>
                      <td>סה"כ</td><td>{calc.schedule.total_months} חודשים</td>
                    </tr>
                  </tbody>
                </table>
                <p style={{ fontSize: 12, color: "#9ca3af", marginTop: 8 }}>{calc.schedule.source_note}</p>
              </div>

              {/* תמחור לפי שלב */}
              <div className="card">
                <h2 className="section-title">תמחור לפי שלבים</h2>
                <table>
                  <thead>
                    <tr><th>שלב</th><th>חודשים</th><th>תעריף חודשי</th><th>עלות שלב</th></tr>
                  </thead>
                  <tbody>
                    {calc.phase_costs.map((pc) => (
                      <tr key={pc.phase_name}>
                        <td>{pc.phase_name}</td>
                        <td>{pc.months}</td>
                        <td>{fmtILS(pc.adjusted_rate)}</td>
                        <td style={{ fontWeight: 600 }}>{fmtILS(pc.phase_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* פרויקטים דומים */}
              {calc.comparable_projects.length > 0 && (
                <div className="card">
                  <h2 className="section-title">פרויקטים דומים</h2>
                  <table>
                    <thead>
                      <tr><th>פרויקט</th><th>יח"ד</th><th>₪/יח"ד</th><th>ציון</th><th>התאמה</th></tr>
                    </thead>
                    <tbody>
                      {calc.comparable_projects.map((c) => (
                        <tr key={c.project_name}>
                          <td>
                            <div>{c.project_name}</div>
                            <div style={{ fontSize: 12, color: "#9ca3af" }}>{c.location_city} | {c.project_type}</div>
                          </td>
                          <td>{fmt(c.num_units)}</td>
                          <td>{fmtILS(c.fee_per_unit)}</td>
                          <td>
                            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                              <div style={{ width: 40, height: 6, borderRadius: 3, background: "#e5e7eb", position: "relative", overflow: "hidden" }}>
                                <div style={{
                                  position: "absolute", right: 0, top: 0, bottom: 0,
                                  width: `${c.similarity_score}%`,
                                  background: c.similarity_score >= 80 ? "#16a34a" : c.similarity_score >= 60 ? "#d97706" : "#6b7280",
                                }} />
                              </div>
                              <span style={{ fontSize: 13 }}>{c.similarity_score}</span>
                            </div>
                          </td>
                          <td>
                            <span className={`flag ${c.match_level === "דמיון גבוה" ? "flag-ok" : "flag-warning"}`} style={{ fontSize: 12 }}>
                              {c.match_level}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>

        {/* עמודה צדדית — סיכום */}
        <div>
          {calc ? (
            <div className="card" style={{ position: "sticky", top: 80 }}>
              <h2 className="section-title">סיכום כלכלי</h2>

              {flags && (
                <div className={`flag ${flags.price_status_code === "OK" ? "flag-ok" : flags.price_status_code === "HIGH" ? "flag-high" : "flag-low"}`}
                  style={{ marginBottom: 16, width: "100%" }}>
                  {flags.price_status_label}
                </div>
              )}

              <div style={{ marginBottom: 16 }}>
                <p style={{ color: "#6b7280", fontSize: 13 }}>הצעה מומלצת</p>
                <p className="amount amount-large">{fmtILS(calc.blended_total)}</p>
              </div>

              <div style={{ marginBottom: 12 }}>
                <p style={{ color: "#6b7280", fontSize: 13 }}>מחיר ליח"ד</p>
                <p className="amount amount-medium">{fmtILS(calc.blended_per_unit)}</p>
              </div>

{project.is_exception_pricing && (
  <div style={{
    border: "1px solid #fecaca",
    background: "#fff7f7",
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  }}>
    <h3 style={{ fontSize: 14, fontWeight: 700, color: "#991b1b", marginBottom: 10 }}>
      עריכת תמחור חריג
    </h3>

    <div className="form-group">
      <label>הצעה מומלצת</label>
      <input
        type="number"
        value={overrideDraft.blended_total ?? ""}
        onChange={e => setOverrideNumber("blended_total", e.target.value)}
      />
    </div>

    <div className="form-group">
      <label>מחיר ליח"ד</label>
      <input
        type="number"
        value={overrideDraft.blended_per_unit ?? ""}
        onChange={e => setOverrideNumber("blended_per_unit", e.target.value)}
      />
    </div>

    <div style={{ marginTop: 10 }}>
      <p style={{ fontSize: 13, fontWeight: 700, color: "#991b1b", marginBottom: 8 }}>
        לו"ז ידני
      </p>

      <div className="grid-2">
        <div className="form-group">
          <label>תכנון ורישוי</label>
          <input
            type="number"
            value={overrideDraft.schedule?.planning ?? ""}
            onChange={e => setOverrideSchedule("planning", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>חפירה ודיפון</label>
          <input
            type="number"
            value={overrideDraft.schedule?.excavation ?? ""}
            onChange={e => setOverrideSchedule("excavation", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>שלד תת״ק</label>
          <input
            type="number"
            value={overrideDraft.schedule?.underground ?? ""}
            onChange={e => setOverrideSchedule("underground", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>שלד עילי</label>
          <input
            type="number"
            value={overrideDraft.schedule?.above_ground ?? ""}
            onChange={e => setOverrideSchedule("above_ground", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>גמרים / מעטפת</label>
          <input
            type="number"
            value={overrideDraft.schedule?.finishes ?? ""}
            onChange={e => setOverrideSchedule("finishes", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>מסירות / טופס 4</label>
          <input
            type="number"
            value={overrideDraft.schedule?.handover ?? ""}
            onChange={e => setOverrideSchedule("handover", e.target.value)}
          />
        </div>
      </div>
    </div>

    <button
      className="btn btn-primary"
      type="button"
      onClick={handleSaveExceptionOverride}
      disabled={savingOverride}
      style={{ marginTop: 10, width: "100%" }}
    >
      {savingOverride ? "שומר..." : "שמור תמחור חריג"}
    </button>
  </div>
)}

              <div style={{ background: "#f8faff", padding: 12, borderRadius: 8, marginBottom: 16 }}>
                <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 4 }}>טווח מומלץ</p>
                <p style={{ fontWeight: 600, fontSize: 14 }}>
                  {fmtILS(calc.price_range_low)} – {fmtILS(calc.price_range_high)}
                </p>
                <p style={{ fontSize: 12, color: "#9ca3af" }}>לפי ±10%</p>
              </div>

              {calc.reference_price_per_unit && (
                <div style={{ marginBottom: 12 }}>
                  <p style={{ color: "#6b7280", fontSize: 13 }}>מחיר ייחוס מבסיס</p>
                  <p style={{ fontWeight: 600 }}>{fmtILS(calc.reference_price_per_unit)}</p>
                </div>
              )}

              <div style={{ marginBottom: 12, padding: "10px 0", borderTop: "1px solid #f0f0f0" }}>
                <p style={{ fontSize: 12, color: "#6b7280" }}>Tier: <b>{calc.tier}</b></p>
                <p style={{ fontSize: 12, color: "#6b7280" }}>
                  מכפיל: {calc.multiplier_project_type} × {calc.multiplier_region} × {calc.multiplier_phases}
                </p>
              </div>

              {flags?.low_comparables_warning && (
                <div className="alert alert-warning" style={{ fontSize: 12 }}>
                  ⚠️ מספר נמוך של פרויקטים דומים ({flags.num_comparables}). נדרש שיקול דעת.
                </div>
              )}
              {flags?.recommendation && (
                <div className="alert alert-info" style={{ fontSize: 12 }}>
                  💡 {flags.recommendation}
                </div>
              )}
              {flags?.missing_fields && flags.missing_fields.length > 0 && (
                <div className="alert alert-warning" style={{ fontSize: 12 }}>
                  שדות חסרים: {flags.missing_fields.join(", ")}
                </div>
              )}
            </div>
          ) : (
            <div className="card" style={{ textAlign: "center", padding: 32 }}>
              <p style={{ color: "#6b7280", marginBottom: 16 }}>לחץ "חשב תמחור" לקבלת הצעת מחיר</p>
              <button className="btn btn-primary" onClick={handleCalculate} disabled={calculating}>
                {calculating ? "מחשב..." : "חשב תמחור"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
