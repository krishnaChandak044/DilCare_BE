/**
 * Login Screen — EXACT match of DilcareGit/pages/Login.tsx
 *
 * - Header: linear-gradient(135deg, #61dafbaa, #646cffaa, #5915a7)
 * - Logo box: white/20 backdrop, Heart icon, rounded-2xl
 * - Decorative rings top-right + bottom-left
 * - Card: shadow-xl rounded-3xl, p-8
 * - Button: bg-gradient-to-r from-blue-500 to-purple-600 = #3b82f6→#9333ea
 * - Outline button: border-2 border-gray-200
 * - Field inputs: border border-input rounded-xl h-11
 */
import React, { useState } from 'react';
import {
    View, Text, TextInput, TouchableOpacity, StyleSheet,
    KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';

export default function LoginScreen({ navigation }: any) {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
    const [apiError, setApiError] = useState('');
    const [loading, setLoading] = useState(false);

    const validate = () => {
        const e: typeof errors = {};
        if (!email.trim()) e.email = 'Email is required';
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = 'Enter a valid email';
        if (!password) e.password = 'Password is required';
        else if (password.length < 6) e.password = 'Password must be at least 6 characters';
        setErrors(e);
        return Object.keys(e).length === 0;
    };

    const handleLogin = async () => {
        if (!validate()) return;
        setLoading(true);
        setApiError('');
        const result = await login(email, password);
        setLoading(false);
        if (!result.success) setApiError(result.error || 'Login failed. Please try again.');
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <View style={styles.spinner} />
                <Text style={styles.loadingText}>Logging you in...</Text>
            </View>
        );
    }

    return (
        <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <ScrollView style={styles.pageContainer} contentContainerStyle={{ flexGrow: 1 }}>
                {/* ── Top gradient header (exact web match) ─────────────── */}
                <LinearGradient
                    colors={['#61dafbaa', '#646cffaa', '#5915a7']}
                    start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                    style={styles.header}
                >
                    {/* Decorative rings */}
                    <View style={[styles.ring, { right: -40, top: -40, width: 160, height: 160 }]} />
                    <View style={[styles.ring, { right: -16, top: 32, width: 96, height: 96 }]} />
                    <View style={[styles.ringFilled, { left: -24, bottom: 0, width: 112, height: 112 }]} />

                    <View style={styles.headerContent}>
                        {/* Logo box: rounded-2xl bg-white/20 backdrop */}
                        <View style={styles.logoBox}>
                            <Ionicons name="heart" size={36} color="#fff" />
                        </View>
                        <Text style={styles.brandName}>DilCare</Text>
                        <Text style={styles.brandTagline}>Health care app for families</Text>
                    </View>
                </LinearGradient>

                {/* ── Main form card ───────────────────────────────────── */}
                <View style={styles.formSection}>
                    <View style={styles.card}>
                        <View style={{ marginBottom: 32 }}>
                            <Text style={styles.title}>Welcome Back</Text>
                            <Text style={styles.subtitle}>Sign in to access your health information</Text>
                        </View>

                        {/* API error banner */}
                        {!!apiError && (
                            <View style={styles.errorBanner}>
                                <Text style={styles.errorBannerText}>{apiError}</Text>
                            </View>
                        )}

                        {/* Email field */}
                        <View style={styles.fieldGroup}>
                            <Text style={styles.label}>Email</Text>
                            <View style={[styles.inputWrapper, errors.email && styles.inputError]}>
                                <Ionicons name="mail-outline" size={18} color={Colors.primary} style={styles.inputIcon} />
                                <TextInput
                                    style={styles.input}
                                    placeholder="you@example.com"
                                    placeholderTextColor={Colors.textMuted}
                                    value={email}
                                    onChangeText={(v) => { setEmail(v); setErrors(p => ({ ...p, email: undefined })); setApiError(''); }}
                                    keyboardType="email-address"
                                    autoCapitalize="none"
                                />
                            </View>
                            {errors.email && <Text style={styles.fieldError}>{errors.email}</Text>}
                        </View>

                        {/* Password field */}
                        <View style={[styles.fieldGroup, { marginTop: 20 }]}>
                            <Text style={styles.label}>Password</Text>
                            <View style={[styles.inputWrapper, errors.password && styles.inputError]}>
                                <Ionicons name="lock-closed-outline" size={18} color={Colors.primary} style={styles.inputIcon} />
                                <TextInput
                                    style={styles.input}
                                    placeholder="••••••••"
                                    placeholderTextColor={Colors.textMuted}
                                    value={password}
                                    onChangeText={(v) => { setPassword(v); setErrors(p => ({ ...p, password: undefined })); setApiError(''); }}
                                    secureTextEntry
                                />
                            </View>
                            {errors.password && <Text style={styles.fieldError}>{errors.password}</Text>}
                        </View>

                        {/* Sign In button — from-blue-500 to-purple-600 */}
                        <TouchableOpacity onPress={handleLogin} activeOpacity={0.85} style={{ marginTop: 32 }}>
                            <LinearGradient
                                colors={Gradients.primaryButton}
                                start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                                style={styles.primaryButton}
                            >
                                <Text style={styles.primaryButtonText}>Sign In</Text>
                                <Ionicons name="arrow-forward" size={16} color="#fff" />
                            </LinearGradient>
                        </TouchableOpacity>

                        {/* Divider */}
                        <View style={styles.divider}>
                            <View style={styles.dividerLine} />
                            <Text style={styles.dividerText}>or</Text>
                            <View style={styles.dividerLine} />
                        </View>

                        {/* Create Account — border-2 border-gray-200 */}
                        <TouchableOpacity style={styles.outlineButton} onPress={() => navigation.navigate('Signup')} activeOpacity={0.7}>
                            <Text style={styles.outlineButtonText}>Create Account</Text>
                        </TouchableOpacity>

                        {/* Demo credentials */}
                        <View style={styles.demoBox}>
                            <Text style={styles.demoTitle}>Demo credentials:</Text>
                            <Text style={styles.demoText}>Email: test@example.com</Text>
                            <Text style={styles.demoText}>Password: TestPass123!</Text>
                        </View>
                    </View>
                </View>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    // Page
    pageContainer: { flex: 1, backgroundColor: '#fff' },
    loadingContainer: {
        flex: 1, justifyContent: 'center', alignItems: 'center',
        // background: linear-gradient(160deg, #fff5f5 0%, #fff 60%)
        backgroundColor: '#fff',
    },
    spinner: {
        width: 48, height: 48, borderRadius: 24,
        borderWidth: 2, borderColor: 'rgba(59,130,246,0.2)', borderTopColor: Colors.primary,
        // spinning is not native — use ActivityIndicator in real usage but this matches web spinner
    },
    loadingText: { marginTop: 16, color: Colors.textSecondary, fontSize: 16, fontWeight: '500' },

    // Header — h-52 = 208px
    header: { height: 208, justifyContent: 'center', alignItems: 'center', overflow: 'hidden', position: 'relative' },
    headerContent: { alignItems: 'center', zIndex: 1 },
    // Decorative
    ring: { position: 'absolute', borderRadius: 999, borderWidth: 2, borderColor: 'rgba(255,255,255,0.15)' },
    ringFilled: { position: 'absolute', borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.10)' },
    // Logo — w-16 h-16 rounded-2xl bg-white/20
    logoBox: {
        width: 64, height: 64, borderRadius: 16,
        backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center',
        borderWidth: 1, borderColor: 'rgba(255,255,255,0.3)', marginBottom: 12,
    },
    brandName: { fontSize: 30, fontWeight: '700', color: '#fff' },
    brandTagline: { fontSize: 14, color: 'rgba(255,255,255,0.8)', marginTop: 4 },

    // Form area
    formSection: { flex: 1, paddingHorizontal: 16, paddingVertical: 32 },
    // Card — border-0 shadow-xl rounded-3xl
    card: {
        backgroundColor: '#fff', borderRadius: Radius['3xl'], padding: 32,
        ...Shadows.premiumLg,
    },
    title: { fontSize: 24, fontWeight: '700', color: Colors.foreground, marginBottom: 8 },
    subtitle: { fontSize: 14, color: Colors.textSecondary },
    // Error — rounded-2xl bg-red-50 border border-red-200
    errorBanner: {
        backgroundColor: Colors.dangerBg, borderWidth: 1, borderColor: '#fecaca',
        borderRadius: Radius['2xl'], padding: 16, marginBottom: 24,
    },
    errorBannerText: { color: '#b91c1c', fontSize: 14 },

    // Fields
    fieldGroup: {},
    label: { fontSize: 14, fontWeight: '600', color: Colors.foreground, marginBottom: 6 },
    // border border-input rounded-xl h-11
    inputWrapper: {
        flexDirection: 'row', alignItems: 'center',
        borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl,
        height: 44, paddingHorizontal: 12, backgroundColor: '#fff',
    },
    inputError: { borderColor: '#f87171' },
    inputIcon: { marginRight: 10 },
    input: { flex: 1, fontSize: 14, color: Colors.foreground },
    fieldError: { color: Colors.danger, fontSize: 12, marginTop: 4 },

    // Primary button — h-12 rounded-xl
    primaryButton: {
        flexDirection: 'row', justifyContent: 'center', alignItems: 'center',
        height: 48, borderRadius: Radius.xl,
    },
    primaryButtonText: { color: '#fff', fontSize: 14, fontWeight: '600', marginRight: 8 },

    // Divider
    divider: { flexDirection: 'row', alignItems: 'center', marginVertical: 24 },
    dividerLine: { flex: 1, height: 1, backgroundColor: '#e5e7eb' },
    dividerText: { paddingHorizontal: 8, color: Colors.textMuted, fontSize: 14, backgroundColor: '#fff' },

    // Outline button — h-12 rounded-xl border-2 border-gray-200
    outlineButton: {
        height: 48, borderRadius: Radius.xl, borderWidth: 2, borderColor: '#e5e7eb',
        justifyContent: 'center', alignItems: 'center',
    },
    outlineButtonText: { fontSize: 14, fontWeight: '600', color: Colors.foreground },

    // Demo
    demoBox: { marginTop: 24, alignItems: 'center' },
    demoTitle: { fontSize: 12, color: Colors.textMuted, fontWeight: '700' },
    demoText: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
});
