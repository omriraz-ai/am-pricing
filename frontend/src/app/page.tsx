"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getProjects, deleteProject, Project } from "@/services/api";

// ── קבועים ────────────────────────────────────────────────────────────

const TECH_STATUS_LABELS: Record<string, { label: string; cls: string }> = {
  draft:       { label: "טיוטה",       cls: "badge-draft"      },
  calculated:  { label: "מחושב",       cls: "badge-calculated" },
  approved:    { label: "מאושר",       cls: "badge-approved"   },
  saved_to_db: { label: "נשמר בבסיס", cls: "badge-saved"      },
};

const CATEGORIES = [
  { key: "בטיפול",   label: "בטיפול",   color: "#2E75B6", bg: "#eff6ff" },
  { key: "הוגש",     label: "הוגש",     color: "#7c3aed", bg: "#f5f3ff" },
  { key: "זכינו",    label: "זכינו ✓",  color: "#16a34a", bg: "#f0fdf4" },
  { key: "לא_זכינו", label: "לא זכינו", color: "#dc2626", bg: "#fef2f2" },
];

// ── שורת פרויקט ───────────────────────────────────────────────────────

function ProjectRow({
  p,
  onDelete,
}: {
  p: Project;
  onDelete: (id: string, name: string) => void;
}) {
  const st = TECH_STATUS_LABELS[p.status] || { label: p.status, cls: "badge-draft" };
  return (
    <tr>
      <td>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
          <Link href={`/projects/${p.id}`} style={{ color: "#1F3864", fontWeight: 600 }}>
            {p.project_name}
          </Link>
          {p.is_test && (
            <span style={{
              background: "#fef3c7", color: "#92400e",
              fontSize: 11, fontWeight: 700,
              padding: "1px 6px", borderRadius: 4,
              border: "1px solid #d97706",
            }}>
              🧪 טסט
            </span>
          )}
        </div>
        <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 2 }}>
          {p.location_city} | {p.project_type}
        </div>
      </td>
      <td>{p.client_name}</td>
      <td style={{ fontVariantNumeric: "tabular-nums" }}>
        {p.num_units.toLocaleString("he-IL")}
      </td>
      <td><span className={`badge ${st.cls}`}>{st.label}</span></td>
      <td style={{ color: "#9ca3af", fontSize: 13 }}>
        {p.created_at ? new Date(p.created_at).toLocaleDateString("he-IL") : "—"}
      </td>
      <td>
        <div style={{ display: "flex", gap: 6 }}>
          <Link href={`/projects/${p.id}`} className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: 12 }}>
            פתח
          </Link>
          {(p.status === "draft" || p.status === "calculated") && (
            <button
              className="btn btn-danger"
              style={{ padding: "5px 10px", fontSize: 12 }}
              onClick={() => onDelete(p.id, p.project_name)}
            >
              מחק
            </button>
          )}
        </div>
      </td>
    </tr>
  );
}

// ── קטגוריה מתקפלת ────────────────────────────────────────────────────

function CategorySection({
  label, color, bg, projects, onDelete,
}: {
  label: string; color: string; bg: string;
  projects: Project[];
  onDelete: (id: string, name: string) => void;
}) {
  const [open, setOpen] = useState(true);

  return (
    <div style={{ marginBottom: 16 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: "100%", textAlign: "right",
          background: bg, border: `1px solid ${color}30`,
          borderRadius: open ? "8px 8px 0 0" : 8,
          padding: "10px 16px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          cursor: "pointer",
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontWeight: 700, fontSize: 15, color }}>{label}</span>
          <span style={{
            background: color, color: "#fff",
            fontSize: 12, fontWeight: 700,
            padding: "1px 8px", borderRadius: 10,
          }}>
            {projects.length}
          </span>
        </span>
        <span style={{ color, fontSize: 13 }}>{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        projects.length === 0 ? (
          <div style={{
            border: `1px solid ${color}20`, borderTop: "none",
            borderRadius: "0 0 8px 8px", padding: "14px 20px",
            background: "#fff", color: "#9ca3af", fontSize: 14,
          }}>
            אין פרויקטים בקטגוריה זו
          </div>
        ) : (
          <div style={{
            border: `1px solid ${color}20`, borderTop: "none",
            borderRadius: "0 0 8px 8px", overflow: "hidden", background: "#fff",
          }}>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>שם פרויקט</th>
                    <th>לקוח</th>
                    <th>יח"ד</th>
                    <th>סטטוס</th>
                    <th>תאריך</th>
                    <th>פעולות</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map(p => (
                    <ProjectRow key={p.id} p={p} onDelete={onDelete} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}
    </div>
  );
}

// ── עמוד ראשי ─────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [projects, setProjects]       = useState<Project[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState("");
  const [showArchive, setShowArchive] = useState(false);

  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch(() => setError("שגיאה בטעינת הפרויקטים"))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`למחוק את הפרויקט "${name}"?`)) return;
    try {
      await deleteProject(id);
      setProjects(prev => prev.filter(p => p.id !== id));
    } catch (e: any) { alert(e.message); }
  };

  // מסך פעיל = לא בארכיון; ארכיון = is_archived=true
  const active   = projects.filter(p => !p.is_archived);
  const archived = projects.filter(p => p.is_archived);

  return (
    <div className="container">
      {/* כותרת */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>פרויקטים</h1>
        <Link href="/projects/new" className="btn btn-primary">+ פרויקט חדש</Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div style={{ textAlign: "center", padding: 48 }}>
          <span className="spinner" />
          <p style={{ marginTop: 12, color: "#6b7280" }}>טוען פרויקטים...</p>
        </div>
      ) : (
        <>
          {/* ── קטגוריות פעילות ── */}
          {active.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: 48 }}>
              <p style={{ color: "#6b7280", marginBottom: 16 }}>אין פרויקטים פעילים עדיין</p>
              <Link href="/projects/new" className="btn btn-primary">צור פרויקט ראשון</Link>
            </div>
          ) : (
            CATEGORIES.map(cat => (
              <CategorySection
                key={cat.key}
                label={cat.label}
                color={cat.color}
                bg={cat.bg}
                projects={active.filter(p =>
                  (p.business_status || "בטיפול") === cat.key
                )}
                onDelete={handleDelete}
              />
            ))
          )}

          {/* ── ארכיון ── */}
          <div style={{ marginTop: 32, borderTop: "2px solid #e5e7eb", paddingTop: 20 }}>
            <button
              onClick={() => setShowArchive(o => !o)}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                background: "none", border: "none",
                cursor: "pointer", padding: "4px 0",
              }}
            >
              <span style={{ fontSize: 18 }}>🗄️</span>
              <span style={{ fontWeight: 700, fontSize: 16, color: "#374151" }}>ארכיון</span>
              <span style={{
                background: "#6b7280", color: "#fff",
                fontSize: 12, fontWeight: 700,
                padding: "1px 8px", borderRadius: 10,
              }}>
                {archived.length}
              </span>
              <span style={{ color: "#6b7280", fontSize: 13 }}>
                {showArchive ? "▲ הסתר" : "▼ הצג"}
              </span>
            </button>

            {showArchive && (
              <div style={{ marginTop: 16 }}>
                {archived.length === 0 ? (
                  <p style={{ color: "#9ca3af", fontSize: 14 }}>אין פרויקטים בארכיון</p>
                ) : (
                  <div className="card" style={{ padding: 0 }}>
                    <div className="table-wrapper">
                      <table>
                        <thead>
                          <tr>
                            <th>שם פרויקט</th>
                            <th>לקוח</th>
                            <th>יח"ד</th>
                            <th>סטטוס עסקי</th>
                            <th>תאריך</th>
                            <th>פעולות</th>
                          </tr>
                        </thead>
                        <tbody>
                          {archived.map(p => {
                            const statusLabel = p.business_status === "לא_זכינו" ? "לא זכינו" : (p.business_status || "—");
                            const statusColor = p.business_status === "זכינו" ? "#16a34a" : "#6b7280";
                            return (
                              <tr key={p.id}>
                                <td>
                                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                    <Link href={`/projects/${p.id}`} style={{ color: "#6b7280", fontWeight: 600 }}>
                                      {p.project_name}
                                    </Link>
                                    {p.is_test && (
                                      <span style={{
                                        background: "#fef3c7", color: "#92400e",
                                        fontSize: 11, fontWeight: 700,
                                        padding: "1px 5px", borderRadius: 4,
                                        border: "1px solid #d97706",
                                      }}>
                                        🧪 טסט
                                      </span>
                                    )}
                                  </div>
                                </td>
                                <td style={{ color: "#6b7280" }}>{p.client_name}</td>
                                <td style={{ color: "#6b7280", fontVariantNumeric: "tabular-nums" }}>
                                  {p.num_units.toLocaleString("he-IL")}
                                </td>
                                <td>
                                  <span style={{ fontSize: 13, fontWeight: 600, color: statusColor }}>
                                    {statusLabel}
                                  </span>
                                </td>
                                <td style={{ color: "#9ca3af", fontSize: 13 }}>
                                  {p.created_at ? new Date(p.created_at).toLocaleDateString("he-IL") : "—"}
                                </td>
                                <td>
                                  <Link href={`/projects/${p.id}`} className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: 12 }}>
                                    פתח
                                  </Link>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
