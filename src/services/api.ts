/**
 * API Client — DilCare Backend Integration
 * Connects to Django REST backend at /api/v1/
 */
import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Change this to your machine's IP when testing on a physical device
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

// ─── Token Management ──────────────────────────────────────────────
const TOKEN_KEYS = { access: 'dilcare_access', refresh: 'dilcare_refresh' };

export const tokenManager = {
    async getAccess(): Promise<string | null> {
        return AsyncStorage.getItem(TOKEN_KEYS.access);
    },
    async getRefresh(): Promise<string | null> {
        return AsyncStorage.getItem(TOKEN_KEYS.refresh);
    },
    async setTokens(access: string, refresh: string) {
        await AsyncStorage.multiSet([
            [TOKEN_KEYS.access, access],
            [TOKEN_KEYS.refresh, refresh],
        ]);
    },
    async clear() {
        await AsyncStorage.multiRemove([TOKEN_KEYS.access, TOKEN_KEYS.refresh]);
    },
    async isLoggedIn(): Promise<boolean> {
        const token = await AsyncStorage.getItem(TOKEN_KEYS.access);
        return !!token;
    },
};

// ─── API instance ──────────────────────────────────────────────────
const api = axios.create({ baseURL: API_BASE_URL, timeout: 15000 });

// Request interceptor — attach JWT
api.interceptors.request.use(async (config) => {
    const token = await tokenManager.getAccess();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Response interceptor — auto-refresh on 401
api.interceptors.response.use(
    (res) => res,
    async (error: AxiosError) => {
        const original = error.config as AxiosRequestConfig & { _retry?: boolean };
        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;
            const refreshToken = await tokenManager.getRefresh();
            if (refreshToken) {
                try {
                    const { data } = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
                        refresh: refreshToken,
                    });
                    await tokenManager.setTokens(data.access, data.refresh || refreshToken);
                    if (original.headers) {
                        original.headers.Authorization = `Bearer ${data.access}`;
                    }
                    return api(original);
                } catch {
                    await tokenManager.clear();
                }
            }
        }
        return Promise.reject(error);
    }
);

// ─── Helper ────────────────────────────────────────────────────────
function extractError(err: any): string {
    if (err?.response?.data) {
        const d = err.response.data;
        if (typeof d === 'string') return d;
        if (d.detail) return d.detail;
        if (d.error) return d.error;
        if (d.non_field_errors) return d.non_field_errors.join(', ');
        // field-level errors
        const msgs = Object.values(d).flat().join(', ');
        if (msgs) return msgs;
    }
    return err?.message || 'Something went wrong';
}

// ════════════════════════════════════════════════════════════════════
// AUTH SERVICE
// ════════════════════════════════════════════════════════════════════
export const authService = {
    async register(email: string, password: string, name?: string, family_name?: string) {
        try {
            const { data } = await api.post('/auth/register/', {
                email, password, password_confirm: password, name: name || '',
                family_name: family_name || '',
            });
            if (data.tokens) {
                await tokenManager.setTokens(data.tokens.access, data.tokens.refresh);
            }
            return { data, error: null };
        } catch (err: any) {
            return { data: null, error: extractError(err) };
        }
    },

    async login(email: string, password: string) {
        try {
            const { data } = await api.post('/auth/login/', { email, password });
            await tokenManager.setTokens(data.access, data.refresh);
            return { data, error: null };
        } catch (err: any) {
            return { data: null, error: extractError(err) };
        }
    },

    async logout() {
        try {
            const refresh = await tokenManager.getRefresh();
            if (refresh) await api.post('/auth/logout/', { refresh });
        } catch { }
        await tokenManager.clear();
    },
};

// ════════════════════════════════════════════════════════════════════
// USER SERVICE
// ════════════════════════════════════════════════════════════════════
export const userService = {
    getProfile: () => api.get('/user/profile/'),
    updateProfile: (data: any) => api.patch('/user/profile/', data),
    getSettings: () => api.get('/user/settings/'),
    updateSettings: (data: any) => api.patch('/user/settings/', data),
    changePassword: (current: string, newPwd: string) =>
        api.post('/user/change-password/', {
            current_password: current,
            new_password: newPwd,
            new_password_confirm: newPwd,
        }),
    getLinkCode: () => api.get('/user/link-code/'),
    regenerateLinkCode: () => api.post('/user/link-code/regenerate/'),
};

// ════════════════════════════════════════════════════════════════════
// FAMILY SERVICE
// ════════════════════════════════════════════════════════════════════
export const familyService = {
    getMyFamily: () => api.get('/family/'),
    createFamily: (name: string) => api.post('/family/create/', { name }),
    joinFamily: (invite_code: string, nickname?: string) =>
        api.post('/family/join/', { invite_code, nickname }),
    leaveFamily: () => api.post('/family/leave/'),
    removeMember: (memberId: number) => api.post(`/family/remove/${memberId}/`),
    regenerateCode: () => api.post('/family/regenerate-code/'),
    getMemberHealth: (memberId: number) => api.get(`/family/members/${memberId}/health/`),
    getPlan: () => api.get('/family/plan/'),
    upgradePlan: (plan: 'free' | 'plus' | 'premium') => api.post('/family/upgrade/', { plan }),
};

// ════════════════════════════════════════════════════════════════════
// HEALTH SERVICE
// ════════════════════════════════════════════════════════════════════
export const healthService = {
    getReadings: (params?: any) => api.get('/health/readings/', { params }),
    addReading: (data: any) => api.post('/health/readings/', data),
    deleteReading: (id: string) => api.delete(`/health/readings/${id}/`),
    getSummary: () => api.get('/health/summary/'),
    getTrends: (params?: any) => api.get('/health/trends/', { params }),
};

// ════════════════════════════════════════════════════════════════════
// MEDICINE SERVICE
// ════════════════════════════════════════════════════════════════════
export const medicineService = {
    getMedicines: () => api.get('/medicine/medicines/'),
    /**
     * POST /medicine/medicines/
     * Required fields: name, schedule_times ("HH:MM" or "HH:MM,HH:MM,...")
     * Optional: dosage, frequency, instructions
     */
    addMedicine: (data: {
        name: string;
        dosage?: string;
        frequency?: string;
        schedule_times?: string;
        instructions?: string;
    }) => api.post('/medicine/medicines/', data),
    deleteMedicine: (id: string) => api.delete(`/medicine/medicines/${id}/`),
    getTodaySchedule: () => api.get('/medicine/today/'),
    /** POST /medicine/intakes/<uuid>/toggle/ — toggles taken↔pending */
    toggleIntake: (intakeId: string, status?: 'taken' | 'pending' | 'missed' | 'skipped') =>
        api.post(`/medicine/intakes/${intakeId}/toggle/`, status ? { status } : {}),
    getSummary: () => api.get('/medicine/summary/'),
    getIntakes: (params?: any) => api.get('/medicine/intakes/', { params }),
};

// ════════════════════════════════════════════════════════════════════
// WATER SERVICE
// ════════════════════════════════════════════════════════════════════
export const waterService = {
    getToday: () => api.get('/water/today/'),
    addGlass: () => api.post('/water/add/'),
    removeGlass: () => api.post('/water/remove/'),
    getHistory: (params?: any) => api.get('/water/history/', { params }),
};

// ════════════════════════════════════════════════════════════════════
// STEPS SERVICE
// ════════════════════════════════════════════════════════════════════
export const stepsService = {
    getToday: () => api.get('/steps/today/'),
    addManual: (steps: number) => api.post('/steps/manual/', { steps }),
    getWeekly: () => api.get('/steps/weekly/'),
    getGoals: () => api.get('/steps/goals/'),
    updateGoals: (data: any) => api.put('/steps/goals/', data),
};

// ════════════════════════════════════════════════════════════════════
// BMI SERVICE
// ════════════════════════════════════════════════════════════════════
export const bmiService = {
    getRecords: () => api.get('/bmi/'),
    addRecord: (data: any) => api.post('/bmi/', data),
    getLatest: () => api.get('/bmi/latest/'),
};

// ════════════════════════════════════════════════════════════════════
// SOS SERVICE
// ════════════════════════════════════════════════════════════════════
export const sosService = {
    getContacts: () => api.get('/sos/contacts/'),
    addContact: (data: any) => api.post('/sos/contacts/', data),
    deleteContact: (id: string) => api.delete(`/sos/contacts/${id}/`),
    triggerSOS: (data?: any) => api.post('/sos/trigger/', data),
    getHistory: () => api.get('/sos/history/'),
};

// ════════════════════════════════════════════════════════════════════
// DOCTOR SERVICE
// ════════════════════════════════════════════════════════════════════
export const doctorService = {
    getDoctors: () => api.get('/doctor/doctors/'),
    addDoctor: (data: any) => api.post('/doctor/doctors/', data),
    deleteDoctor: (id: string) => api.delete(`/doctor/doctors/${id}/`),
    getAppointments: () => api.get('/doctor/appointments/'),
    addAppointment: (data: any) => api.post('/doctor/appointments/', data),
};

// ════════════════════════════════════════════════════════════════════
// GYAAN SERVICE
// ════════════════════════════════════════════════════════════════════
export const gyaanService = {
    getTips: (params?: any) => api.get('/gyaan/tips/', { params }),
    getTip: (id: string) => api.get(`/gyaan/tips/${id}/`),
    toggleFavorite: (id: string) => api.post(`/gyaan/tips/${id}/favorite/`),
};

// ════════════════════════════════════════════════════════════════════
// AI SERVICE
// ════════════════════════════════════════════════════════════════════
export const aiService = {
    sendMessage: (message: string, sessionId?: string) =>
        api.post('/ai/chat/', { message, session_id: sessionId }),
    getSessions: () => api.get('/ai/sessions/'),
    getSession: (id: string) => api.get(`/ai/sessions/${id}/`),
    deleteSession: (id: string) => api.delete(`/ai/sessions/${id}/`),
};

// ════════════════════════════════════════════════════════════════════
// COMMUNITY SERVICE
// ════════════════════════════════════════════════════════════════════
export const communityService = {
    getLeaderboard: () => api.get('/community/leaderboard/'),
    getChallenges: () => api.get('/community/challenges/'),
};

// ════════════════════════════════════════════════════════════════════
// LOCATION SERVICE
// ════════════════════════════════════════════════════════════════════
export const locationService = {
    /** GET /location/family/live/ — returns live locations of all family members */
    getFamilyLiveLocations: () => api.get('/location/family/live/'),
    /** POST /location/share/ — push current user's location */
    shareMyLocation: (data: {
        latitude: number;
        longitude: number;
        speed_kmh?: number;
        battery_level?: number;
    }) => api.post('/location/share/', data),
    /** POST /location/stop/ — stop sharing location */
    stopSharing: () => api.post('/location/stop/'),
};

export default api;
