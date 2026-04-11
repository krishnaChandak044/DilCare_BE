/**
 * DilCare Design System — Exact DilcareGit Colors
 * Source: index.css HSL variables + tailwind.config.ts
 *
 * PRIMARY = Deep Blue   hsl(217,91%,60%) → #3b82f6
 * ACCENT  = Emerald     hsl(160,84%,39%) → #0d9669
 * SUCCESS = Green       hsl(142,76%,36%) → #15803d
 * WARNING = Amber       hsl(38,92%,50%)  → #f59e0b
 * DANGER  = Red         hsl(0,84%,60%)   → #ef4444
 * CALM    = Purple      hsl(280,65%,60%) → #9b59b6
 */
export const Colors = {
    // ── Core palette (exact web matches) ──────────────────────────
    primary: '#3b82f6',        // blue-500  — main CTA, links, active states
    primaryDark: '#2563eb',    // blue-600  — hover, secondary CTA
    primaryLight: '#dbeafe',   // blue-100  — badges, light backgrounds
    primaryBg: '#eff6ff',      // blue-50   — card tints

    accent: '#059669',         // emerald-600
    accentLight: '#d1fae5',    // emerald-100

    purple: '#9333ea',         // purple-600 — used in gradients with primary
    purpleLight: '#f3e8ff',    // purple-50
    purpleMid: '#8b5cf6',      // violet-500

    // ── Status colors ────────────────────────────────────────────
    success: '#15803d',        // green-700
    successBg: '#f0fdf4',      // green-50
    successBadge: '#dcfce7',   // green-100

    warning: '#f59e0b',        // amber-500
    warningBg: '#fffbeb',      // amber-50
    warningBadge: '#fef3c7',   // amber-100

    danger: '#ef4444',         // red-500
    dangerBg: '#fef2f2',       // red-50
    dangerBadge: '#fee2e2',    // red-100

    // ── Neutrals (exact Tailwind gray/slate) ─────────────────────
    background: '#f8fafc',     // slate-50  — page bg
    surface: '#ffffff',        // white     — card bg
    card: '#ffffff',

    foreground: '#0f172a',     // slate-900 — headings, primary text
    text: '#0f172a',           // slate-900
    textSecondary: '#475569',  // slate-600
    textMuted: '#94a3b8',      // slate-400
    textWhite: '#ffffff',

    border: '#e2e8f0',         // slate-200
    borderLight: '#f1f5f9',    // slate-100
    input: '#e2e8f0',          // same as border

    // ── Feature-specific (from BottomNav + page headers) ─────────
    medicine: '#3b82f6',       // blue-500  (same as primary in web)
    medicineBg: '#eff6ff',     // blue-50

    steps: '#f97316',          // orange-500
    stepsBg: '#fff7ed',        // orange-50

    bmi: '#9333ea',            // purple-600
    bmiBg: '#faf5ff',          // purple-50

    health: '#16a34a',         // green-600
    healthDark: '#059669',     // emerald-600 — hero gradient end
    healthBg: '#f0fdf4',       // green-50

    wellness: '#8b5cf6',       // violet-500
    wellnessBg: '#f5f3ff',     // violet-50

    emergency: '#ef4444',      // red-500
    emergencyBg: '#fef2f2',    // red-50

    water: '#0ea5e9',          // sky-500
    waterBg: '#f0f9ff',        // sky-50

    community: '#3b82f6',      // same as primary

    ai: '#8b5cf6',             // violet-500
    aiBg: '#f5f3ff',           // violet-50

    doctor: '#3b82f6',         // blue-500 (medicine-blue in web)
    doctorBg: '#eff6ff',       // blue-50

    // ── Premium shadow (from index.css) ──────────────────────────
    shadowColor: 'rgba(15, 23, 42, 0.08)',
    shadowLg: 'rgba(15, 23, 42, 0.12)',
};

// ── Gradients (exact web CSS) ──────────────────────────────────
export const Gradients = {
    // Login / Signup header
    header: ['#61dafbaa', '#646cffaa', '#5915a7'] as const,

    // Primary button (from-blue-500 to-purple-600)
    primaryButton: ['#3b82f6', '#9333ea'] as const,

    // Health tracker hero (from-green-600 to-emerald-600)
    healthHero: ['#16a34a', '#059669'] as const,

    // Dashboard subtle bg (from-primary/20 via-white to-accent/20)
    dashboardBg: ['rgba(59,130,246,0.08)', '#ffffff', 'rgba(5,150,105,0.08)'] as const,

    // Card overlay (from-blue-500/5 to-purple-500/5)
    cardOverlay: ['rgba(59,130,246,0.05)', 'rgba(147,51,234,0.05)'] as const,

    // Medicine pill gradient (indigo)
    medicine: ['#6366f1', '#4f46e5'] as const,

    // Step tracker
    steps: ['#fb923c', '#f97316'] as const,

    // Water tracker
    water: ['#38bdf8', '#0284c7'] as const,

    // BMI / Purple
    bmi: ['#8b5cf6', '#6d28d9'] as const,

    // SOS
    sos: ['#ef4444', '#dc2626'] as const,

    // Success / health insight
    success: ['#16a34a', '#059669'] as const,
};

// ── Spacing & Radius ───────────────────────────────────────────
export const Radius = {
    sm: 8,        // calc(0.75rem - 4px)
    md: 10,       // calc(0.75rem - 2px)
    lg: 12,       // 0.75rem = default --radius
    xl: 16,       // rounded-xl
    '2xl': 20,    // rounded-2xl (buttons, cards in web)
    '3xl': 24,    // rounded-3xl (form cards in web)
    full: 9999,
};

// ── Shadows (from index.css .shadow-premium) ───────────────────
export const Shadows = {
    sm: {
        shadowColor: '#0f172a',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.04,
        shadowRadius: 4,
        elevation: 1,
    },
    md: {
        shadowColor: '#0f172a',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.06,
        shadowRadius: 12,
        elevation: 3,
    },
    premium: {
        shadowColor: '#0f172a',
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.08,
        shadowRadius: 32,
        elevation: 6,
    },
    premiumLg: {
        shadowColor: '#0f172a',
        shadowOffset: { width: 0, height: 16 },
        shadowOpacity: 0.12,
        shadowRadius: 64,
        elevation: 10,
    },
};
