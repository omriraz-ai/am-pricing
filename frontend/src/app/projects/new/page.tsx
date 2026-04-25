"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createProject, ProjectCreate } from "@/services/api";

const PROJECT_TYPES = ["מגורים", "עירוב שימושים", "מגדל", "פינוי בינוי", "הריסה ובנייה", "מסחרי", "ציבורי"];
const INDEX_TYPES   = ["תשומות בניה", "צרכן", "ללא"];

export default function NewProjectPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<Partial<ProjectCreate>>({
    execution_phases: 1,
    manual_complexity_multiplier: 1.0,
    index_type: "תשומות בניה",
    includes_vat: false,
    is_test: false,
    is_exception_pricing: false,
  });
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<any>(null);
  const [selectedRowIndex, setSelectedRowIndex] = useState<number | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importMessage, setImportMessage] = useState("");

  const set = (field: keyof ProjectCreate, val: unknown) =>
    setForm((prev) => ({ ...prev, [field]: val }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!form.project_name || !form.client_name || !form.location_city ||
        !form.project_type || !form.num_units || !form.num_floors_above) {
      setError("יש למלא את כל שדות החובה");
      return;
    }

    // ולידציה: override מכפיל חייב לכלול סיבה
    const mult = form.manual_complexity_multiplier ?? 1.0;
    if (Math.abs(mult - 1.0) > 0.001 && !form.manual_override_reason?.trim()) {
      setError("שינית את מכפיל המורכבות — יש למלא את שדה 'סיבת שינוי מכפיל'");
      return;
    }

    setLoading(true);
    try {
      const created = await createProject(form as ProjectCreate);
      router.push(`/projects/${created.id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const isOverrideActive = Math.abs((form.manual_complexity_multiplier ?? 1.0) - 1.0) > 0.001;

const applyRowToForm = (row: any) => {
  setForm((prev) => ({
    ...prev,
    project_name: row["Project Name"] || row["שם הפרויקט"] || prev.project_name,
    client_name: row["Client"] || row["יזם"] || prev.client_name,
    location_city: row["City"] || row["יישוב"] || prev.location_city,
    num_units: row["Unit Count"] || row["מס' יח\"ד"] || prev.num_units,
    num_floors_above: row["FLOORS"] || row["מספר קומות מעל הקרקע"] || prev.num_floors_above,
    plot_area_sqm: row["TOTAL AREA"] || row["שטח בנוי"] || prev.plot_area_sqm,
  }));
};

const handleFilePreview = async () => {
  if (!importFile) return;

  setImportLoading(true);
  setImportMessage("");

  const formData = new FormData();
  formData.append("file", importFile);

  const isPdf = importFile.name.toLowerCase().endsWith(".pdf");
  const endpoint = isPdf ? "pdf-preview" : "excel-preview";

  const res = await fetch(`http://127.0.0.1:8000/api/v1/import/${endpoint}`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  console.log("FILE PREVIEW:", data);  
  setImportPreview(data);

  if (data.detected_fields) {
  console.log("DETECTED:", data.detected_fields);

  setForm((prev) => ({
    ...prev,
    project_name: data.detected_fields.project_name ?? prev.project_name,
    client_name: data.detected_fields.client_name ?? prev.client_name,
    location_city: data.detected_fields.city ?? prev.location_city,
    num_units: data.detected_fields.units ?? prev.num_units,
    num_floors_above: data.detected_fields.floors ?? prev.num_floors_above,
    plot_area_sqm: data.detected_fields.area ?? prev.plot_area_sqm,
  }));
}
  setImportMessage("הנתונים זוהו ומולאו בטופס. מומלץ לבדוק לפני יצירת הפרויקט.");
  setImportLoading(false);
};

  return (
  <div className="container" style={{ maxWidth: 800 }}>
    <h1 className="page-title">פרויקט חדש</h1>

    {/* 👇 card של Import */}
    <div className="card" style={{ marginBottom: 16 }}>
      <h2 className="section-title">ייבוא מאקסל</h2>

      <input
        type="file"
        accept=".xlsx,.pdf"
        onChange={(e) => setImportFile(e.target.files?.[0] || null)}
      />

      <button
  type="button"
  className="btn btn-primary"
  onClick={handleFilePreview}
  disabled={importLoading}
>
  {importLoading ? "טוען..." : "בדוק קובץ"}
</button>
    </div>
  {importMessage && (
  <div className="alert alert-success" style={{ marginBottom: 16 }}>
    ✅ {importMessage}
  </div>
)}

    {/* 👇 card נפרד */}
    {importPreview?.preview?.columns && (
  <div className="card" style={{ marginBottom: 16 }}>
    <h2 className="section-title">תצוגה מקדימה</h2>

    <table>
      <thead>
        <tr>
          <th>בחירה</th>
          {importPreview.preview.columns.map((col: string) => (
            <th key={col}>{col}</th>
          ))}
        </tr>
      </thead>

      <tbody>
        {importPreview.preview.sample_rows.map((row: any, index: number) => (
          <tr
            key={index}
            style={{
              backgroundColor: selectedRowIndex === index ? "#dbeafe" : "transparent",
            }}
          >
            <td>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  applyRowToForm(row);
                  setSelectedRowIndex(index);
                }}
              >
                בחר
              </button>
            </td>

            {importPreview.preview.columns.map((col: string) => (
              <td key={col}>{String(row[col] ?? "")}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)}



    {/* 👇 ממשיך הטופס שלך */}

      {/* באנר פרויקט טסט */}
      {form.is_test && (
        <div style={{
          background: "#fef3c7",
          border: "2px dashed #d97706",
          borderRadius: 8,
          padding: "10px 16px",
          marginBottom: 16,
          display: "flex",
          alignItems: "center",
          gap: 8,
          color: "#92400e",
          fontWeight: 600,
          fontSize: 14,
        }}>
          🧪 פרויקט טסט — לא יישמר לבסיס הנתונים. ניתן לחשב, לאשר ולהפיק מסמך לבדיקה בלבד.
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit}>

        {/* ── פרטי פרויקט ── */}
        <div className="card">
          <h2 className="section-title">פרטי פרויקט</h2>
          <div className="grid-2">
            <div className="form-group">
              <label>שם פרויקט <span className="required">*</span></label>
              <input value={form.project_name || ""} onChange={e => set("project_name", e.target.value)} placeholder="FOREST ירושלים" />
            </div>
            <div className="form-group">
              <label>שם לקוח / חברה <span className="required">*</span></label>
              <input value={form.client_name || ""} onChange={e => set("client_name", e.target.value)} />
            </div>
            <div className="form-group">
              <label>עיר <span className="required">*</span></label>
              <input value={form.location_city || ""} onChange={e => set("location_city", e.target.value)} placeholder="ירושלים" />
            </div>
            <div className="form-group">
              <label>סוג פרויקט <span className="required">*</span></label>
              <select value={form.project_type || ""} onChange={e => set("project_type", e.target.value)}>
                <option value="">בחר סוג...</option>
                {PROJECT_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>

          {/* Checkbox פרויקט טסט */}
          <div style={{
            marginTop: 16,
            paddingTop: 14,
            borderTop: "1px solid #f3f4f6",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}>
            <input
              type="checkbox"
              id="is_test"
              checked={form.is_test || false}
              onChange={e => set("is_test", e.target.checked)}
              style={{ width: 17, height: 17, cursor: "pointer", accentColor: "#d97706" }}
            />
            <label htmlFor="is_test" style={{ cursor: "pointer", fontWeight: 600, fontSize: 14, margin: 0 }}>
              🧪 פרויקט טסט
            </label>
            <span style={{ color: "#9ca3af", fontSize: 13 }}>— לא יישמר לבסיס הנתונים</span>
          </div>
        
         
        <div style={{
  marginTop: 10,
  display: "flex",
  alignItems: "center",
  gap: 10,
}}>
  <input
    type="checkbox"
    id="is_exception_pricing"
    checked={form.is_exception_pricing || false}
    onChange={e => set("is_exception_pricing", e.target.checked)}
    style={{ width: 17, height: 17, cursor: "pointer", accentColor: "#dc2626" }}
  />
  <label htmlFor="is_exception_pricing" style={{ cursor: "pointer", fontWeight: 600, fontSize: 14, margin: 0 }}>
    ⚠️ תמחור חריג
  </label>
  <span style={{ color: "#9ca3af", fontSize: 13 }}>— לא ייכנס לבסיס הנתונים הייחוסי</span>
</div>
</div>

        {/* ── נתוני בינוי ── */}
        <div className="card">
          <h2 className="section-title">נתוני בינוי</h2>
          <div className="grid-3">
            <div className="form-group">
              <label>מספר יח"ד <span className="required">*</span></label>
              <input type="number" min={1} value={form.num_units || ""} onChange={e => set("num_units", +e.target.value)} />
            </div>
            <div className="form-group">
              <label>קומות עיליות <span className="required">*</span></label>
              <input type="number" min={1} value={form.num_floors_above || ""} onChange={e => set("num_floors_above", +e.target.value)} />
            </div>
            <div className="form-group">
              <label>קומות מרתף</label>
              <input type="number" min={0} step={0.5} value={form.num_floors_underground || ""} onChange={e => set("num_floors_underground", +e.target.value)} />
            </div>
            <div className="form-group">
              <label>מספר מבנים</label>
              <input type="number" min={1} value={form.num_buildings || ""} onChange={e => set("num_buildings", +e.target.value)} />
            </div>
            <div className="form-group">
              <label>שלבי ביצוע <span className="required">*</span></label>
              <select value={form.execution_phases || 1} onChange={e => set("execution_phases", +e.target.value)}>
                <option value={1}>שלב אחד</option>
                <option value={2}>2 שלבים</option>
                <option value={3}>3 שלבים</option>
              </select>
            </div>
            <div className="form-group">
              <label>שטח מגרש (מ"ר)</label>
              <input type="number" value={form.plot_area_sqm || ""} onChange={e => set("plot_area_sqm", +e.target.value)} />
            </div>
          </div>
        </div>

        {/* ── לוח זמנים ידני (אופציונלי) ── */}
        <div className="card">
          <h2 className="section-title">לוח זמנים (חודשים) — אופציונלי</h2>
          <div className="alert alert-info">
            אם לא תמלא — המערכת תחשב אוטומטית לפי גודל הפרויקט ובסיס הנתונים.
          </div>
          <div className="grid-3">
            {[
              ["timeline_planning",     "תכנון ורישוי"],
              ["timeline_excavation",   "חפירה ודיפון"],
              ["timeline_underground",  "שלד תת\"ק"],
              ["timeline_above_ground", "שלד עילי"],
              ["timeline_finishes",     "גמרים / מעטפת"],
              ["timeline_handover",     "מסירות / טופס 4"],
            ].map(([field, label]) => (
              <div className="form-group" key={field}>
                <label>{label}</label>
                <input
                  type="number" min={0}
                  value={(form as any)[field] || ""}
                  onChange={e => set(field as keyof ProjectCreate, +e.target.value || undefined)}
                  placeholder="אוטומטי"
                />
              </div>
            ))}
          </div>
        </div>

        {/* ── תנאים מסחריים ── */}
        <div className="card">
          <h2 className="section-title">תנאים מסחריים</h2>
          <div className="grid-3">
            <div className="form-group">
              <label>סוג מדד הצמדה</label>
              <select value={form.index_type || "תשומות בניה"} onChange={e => set("index_type", e.target.value)}>
                {INDEX_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>כולל מע"מ</label>
              <select value={form.includes_vat ? "כן" : "לא"} onChange={e => set("includes_vat", e.target.value === "כן")}>
                <option>לא</option>
                <option>כן</option>
              </select>
            </div>
            <div className="form-group">
              <label>מכפיל מורכבות ידני</label>
              <input
                type="number" min={0.5} max={2} step={0.05}
                value={form.manual_complexity_multiplier ?? 1}
                onChange={e => set("manual_complexity_multiplier", +e.target.value)}
              />
              <span style={{ fontSize: 12, color: "#9ca3af" }}>ברירת מחדל: 1.0</span>
            </div>
          </div>

          {/* שדה סיבת override — מופיע רק כשהמכפיל שונה מ-1.0 */}
          {isOverrideActive && (
            <div className="form-group" style={{ marginTop: 8 }}>
              <label>
                סיבת שינוי מכפיל <span className="required">*</span>
              </label>
              <input
                value={form.manual_override_reason || ""}
                onChange={e => set("manual_override_reason", e.target.value)}
                placeholder="לדוגמה: מורכבות גיאוטכנית גבוהה, תנאי קרקע מיוחדים..."
              />
              {!form.manual_override_reason?.trim() && (
                <span className="error">שדה חובה כאשר המכפיל שונה מ-1.0</span>
              )}
            </div>
          )}

          <div className="form-group" style={{ marginTop: 8 }}>
            <label>הערות מסחריות</label>
            <textarea rows={3} value={form.notes_pricing || ""} onChange={e => set("notes_pricing", e.target.value)} placeholder="כולל ליווי בדק..." />
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
          <a href="/" className="btn btn-ghost">ביטול</a>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> : "צור פרויקט"}
          </button>
        </div>

      </form>
    </div>
  );
}
