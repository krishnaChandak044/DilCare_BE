/**
 * Signup Screen — Full DilcareGit parity with Family Plan Selection
 *
 * Flow: splash → form → plan → family → success
 *
 * Animations:
 *  - Splash: Pulsing rings (like css animate-ping) + bouncing loading dots
 *  - Step transitions: opacity fade
 *  - Progress bar with current step highlight
 */
import React, { useState, useEffect, useRef } from 'react';
import {
    View, Text, TextInput, TouchableOpacity, StyleSheet,
    KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator,
    Animated, Easing,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { familyService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';

type Step = 'splash' | 'form' | 'plan' | 'family' | 'success';

// ── Plan data ──────────────────────────────────────────────────
const PLANS = [
    {
        id: 'free' as const,
        name: 'Free',
        price: 0,
        period: '',
        members: 4,
        color: '#16a34a',
        bgColor: '#f0fdf4',
        icon: 'people' as const,
        badge: 'Most Popular',
        features: ['Up to 4 family members', 'Health tracking for all', 'Medicine reminders', 'Family health dashboard'],
    },
    {
        id: 'plus' as const,
        name: 'Plus',
        price: 99,
        period: '/month',
        members: 6,
        color: '#3b82f6',
        bgColor: '#eff6ff',
        icon: 'star' as const,
        badge: '',
        features: ['Up to 6 family members', 'Everything in Free', 'Priority AI assistant', 'Advanced analytics'],
    },
    {
        id: 'premium' as const,
        name: 'Premium',
        price: 199,
        period: '/month',
        members: 10,
        color: '#9333ea',
        bgColor: '#faf5ff',
        icon: 'diamond' as const,
        badge: 'Best Value',
        features: ['Up to 10 family members', 'Everything in Plus', 'Doctor consultation credits', 'Priority support'],
    },
];

// ── Bouncing Dot Component ──────────────────────────────────────
const BouncingDot = ({ delay }: { delay: number }) => {
    const anim = useRef(new Animated.Value(0)).current;
    useEffect(() => {
        const loop = Animated.loop(
            Animated.sequence([
                Animated.timing(anim, { toValue: 1, duration: 400, delay, easing: Easing.out(Easing.quad), useNativeDriver: true }),
                Animated.timing(anim, { toValue: 0, duration: 400, easing: Easing.in(Easing.quad), useNativeDriver: true }),
                Animated.delay(600),
            ])
        );
        loop.start();
        return () => loop.stop();
    }, []);
    return (
        <Animated.View style={[s.dot, {
            opacity: anim.interpolate({ inputRange: [0, 1], outputRange: [0.4, 1] }),
            transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [0, -8] }) }],
        }]} />
    );
};

// ── Pulsing Ring Component ──────────────────────────────────────
const PulsingRing = ({ size, delay }: { size: number; delay: number }) => {
    const anim = useRef(new Animated.Value(0)).current;
    useEffect(() => {
        const loop = Animated.loop(
            Animated.sequence([
                Animated.delay(delay),
                Animated.timing(anim, { toValue: 1, duration: 2000, easing: Easing.out(Easing.ease), useNativeDriver: true }),
            ])
        );
        loop.start();
        return () => loop.stop();
    }, []);
    return (
        <Animated.View style={{
            position: 'absolute', width: size, height: size, borderRadius: size / 2,
            borderWidth: 2, borderColor: 'rgba(255,255,255,0.2)',
            opacity: anim.interpolate({ inputRange: [0, 1], outputRange: [1, 0] }),
            transform: [{ scale: anim.interpolate({ inputRange: [0, 1], outputRange: [1, 1.8] }) }],
        }} />
    );
};

// ── Progress Bar ────────────────────────────────────────────────
const STEPS = ['Details', 'Plan', 'Family', 'Done'];
const ProgressBar = ({ currentIdx }: { currentIdx: number }) => (
    <View style={s.progressRow}>
        {STEPS.map((label, i) => (
            <React.Fragment key={label}>
                <View style={{ alignItems: 'center' }}>
                    <View style={[s.progressDot,
                    i < currentIdx && { backgroundColor: '#16a34a' },
                    i === currentIdx && { backgroundColor: Colors.primary },
                    ]}>
                        {i < currentIdx
                            ? <Ionicons name="checkmark" size={14} color="#fff" />
                            : <Text style={[s.progressDotText, i > currentIdx && { color: Colors.textMuted }]}>{i + 1}</Text>}
                    </View>
                    <Text style={[s.progressLabel, i <= currentIdx && { color: Colors.primary, fontWeight: '600' }]}>{label}</Text>
                </View>
                {i < STEPS.length - 1 && (
                    <View style={[s.progressLine, i < currentIdx && { backgroundColor: '#16a34a' }, i === currentIdx && { backgroundColor: Colors.primary }]} />
                )}
            </React.Fragment>
        ))}
    </View>
);

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════
export default function SignupScreen({ navigation }: any) {
    const { register } = useAuth();
    const [step, setStep] = useState<Step>('splash');

    // Form state
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errors, setErrors] = useState<any>({});
    const [apiError, setApiError] = useState('');
    const [loading, setLoading] = useState(false);

    // Plan state
    const [selectedPlan, setSelectedPlan] = useState<'free' | 'plus' | 'premium'>('free');

    // Family state
    const [familyChoice, setFamilyChoice] = useState<'create' | 'join' | null>(null);
    const [familyName, setFamilyName] = useState('');
    const [inviteCode, setInviteCode] = useState('');
    const [familyError, setFamilyError] = useState('');

    // Fade animation
    const fadeAnim = useRef(new Animated.Value(0)).current;
    useEffect(() => {
        Animated.timing(fadeAnim, { toValue: 1, duration: 500, useNativeDriver: true }).start();
    }, [step]);

    // Auto-advance splash
    useEffect(() => {
        const t = setTimeout(() => {
            fadeAnim.setValue(0);
            setStep('form');
        }, 2500);
        return () => clearTimeout(t);
    }, []);

    // ── Validation ──
    const validate = () => {
        const e: any = {};
        if (!name.trim()) e.name = 'Name is required';
        if (!email.trim()) e.email = 'Email is required';
        else if (!/\S+@\S+\.\S+/.test(email)) e.email = 'Enter a valid email';
        if (!password) e.password = 'Password is required';
        else if (password.length < 8) e.password = 'Min 8 characters';
        setErrors(e);
        return Object.keys(e).length === 0;
    };

    // ── Form Submit → go to Plan ──
    const handleFormSubmit = () => {
        if (!validate()) return;
        fadeAnim.setValue(0);
        setStep('plan');
    };

    // ── Plan Submit → go to Family ──
    const handlePlanSubmit = () => {
        fadeAnim.setValue(0);
        setStep('family');
    };

    // ── Family Submit → Register + Create/Join ──
    const handleFamilySubmit = async () => {
        setFamilyError('');
        setLoading(true);

        if (familyChoice === 'create') {
            if (!familyName.trim()) { setFamilyError('Family name is required'); setLoading(false); return; }

            // Register with family_name — atomically creates family
            const result = await register(email, password, name, familyName.trim());
            if (!result.success) {
                setApiError(result.error || 'Registration failed');
                setLoading(false);
                fadeAnim.setValue(0);
                setStep('form');
                return;
            }
            setLoading(false);
            fadeAnim.setValue(0);
            setStep('success');

        } else if (familyChoice === 'join') {
            if (inviteCode.length !== 6) { setFamilyError('Enter a 6-character invite code'); setLoading(false); return; }

            // Register without family, then join
            const result = await register(email, password, name);
            if (!result.success) {
                setApiError(result.error || 'Registration failed');
                setLoading(false);
                fadeAnim.setValue(0);
                setStep('form');
                return;
            }
            try {
                await familyService.joinFamily(inviteCode.toUpperCase());
            } catch (err: any) {
                setFamilyError(err?.response?.data?.error || 'Invalid invite code');
                setLoading(false);
                return;
            }
            setLoading(false);
            fadeAnim.setValue(0);
            setStep('success');
        }
    };

    // ── Skip family → Register without family ──
    const handleSkipFamily = async () => {
        setLoading(true);
        const result = await register(email, password, name);
        setLoading(false);
        if (!result.success) {
            setApiError(result.error || 'Registration failed');
            fadeAnim.setValue(0);
            setStep('form');
            return;
        }
        fadeAnim.setValue(0);
        setStep('success');
    };

    // ═══════════════════════════════════════════════════════════
    // SPLASH
    // ═══════════════════════════════════════════════════════════
    if (step === 'splash') {
        return (
            <LinearGradient colors={['#61dafb', '#646cff', '#5915a7']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.splashContainer}>
                <View style={s.splashRings}>
                    <PulsingRing size={160} delay={0} />
                    <PulsingRing size={128} delay={300} />
                    <View style={s.splashLogo}>
                        <Ionicons name="heart" size={48} color="#fff" />
                    </View>
                </View>
                <Text style={s.splashBrand}>DilCare</Text>
                <Text style={s.splashTagline}>YOUR HEART, OUR PRIORITY</Text>
                <View style={s.loadingDots}>
                    <BouncingDot delay={0} />
                    <BouncingDot delay={200} />
                    <BouncingDot delay={400} />
                </View>
            </LinearGradient>
        );
    }

    // ═══════════════════════════════════════════════════════════
    // SUCCESS
    // ═══════════════════════════════════════════════════════════
    if (step === 'success') {
        return (
            <Animated.View style={[s.successContainer, { opacity: fadeAnim }]}>
                <View style={s.successCircle}>
                    <Ionicons name="checkmark-circle" size={64} color="#16a34a" />
                </View>
                <Text style={s.successTitle}>You're all set!</Text>
                <Text style={s.successSubtitle}>
                    Account created successfully.{'\n'}Welcome to the DilCare family 💖
                </Text>
                <Text style={s.successPlanBadge}>
                    {selectedPlan === 'free' ? '🆓 Free Plan' : selectedPlan === 'plus' ? '⭐ Plus Plan' : '💎 Premium Plan'}
                    {' — '}Up to {PLANS.find(p => p.id === selectedPlan)!.members} members
                </Text>
            </Animated.View>
        );
    }

    // ═══════════════════════════════════════════════════════════
    // PLAN SELECTION
    // ═══════════════════════════════════════════════════════════
    if (step === 'plan') {
        return (
            <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
                <ScrollView style={{ flex: 1, backgroundColor: '#fff' }} contentContainerStyle={{ flexGrow: 1 }}>
                    <LinearGradient colors={['#61dafbaa', '#646cffaa', '#5915a7']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.smallHeader}>
                        <Ionicons name="heart" size={28} color="#fff" />
                        <Text style={s.smallBrand}>DilCare</Text>
                        <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13, marginTop: 2 }}>Choose your family plan</Text>
                    </LinearGradient>

                    <View style={{ paddingHorizontal: 16, paddingVertical: 20, marginTop: -16 }}>
                        <View style={s.card}>
                            <ProgressBar currentIdx={1} />
                            <Text style={s.cardTitle}>Select Your Plan</Text>
                            <Text style={s.cardSubtitle}>Free plan includes 4 family members. Need more? Upgrade anytime.</Text>

                            <View style={{ gap: 12, marginTop: 16 }}>
                                {PLANS.map(plan => {
                                    const selected = selectedPlan === plan.id;
                                    return (
                                        <TouchableOpacity
                                            key={plan.id}
                                            onPress={() => setSelectedPlan(plan.id)}
                                            activeOpacity={0.8}
                                            style={[s.planCard, selected && { borderColor: plan.color, borderWidth: 2, backgroundColor: plan.bgColor }]}
                                        >
                                            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                                                <View style={[s.planIcon, { backgroundColor: plan.bgColor }]}>
                                                    <Ionicons name={plan.icon as any} size={22} color={plan.color} />
                                                </View>
                                                <View style={{ flex: 1, marginLeft: 12 }}>
                                                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                                                        <Text style={[s.planName, { color: plan.color }]}>{plan.name}</Text>
                                                        {plan.badge ? (
                                                            <View style={[s.planBadge, { backgroundColor: plan.color }]}>
                                                                <Text style={s.planBadgeText}>{plan.badge}</Text>
                                                            </View>
                                                        ) : null}
                                                    </View>
                                                    <Text style={s.planMembers}>{plan.members} family members</Text>
                                                </View>
                                                <View style={{ alignItems: 'flex-end' }}>
                                                    <Text style={[s.planPrice, { color: plan.color }]}>
                                                        {plan.price === 0 ? 'Free' : `₹${plan.price}`}
                                                    </Text>
                                                    {plan.period ? <Text style={s.planPeriod}>{plan.period}</Text> : null}
                                                </View>
                                            </View>

                                            {selected && (
                                                <View style={{ marginTop: 4 }}>
                                                    {plan.features.map((f, i) => (
                                                        <View key={i} style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }}>
                                                            <Ionicons name="checkmark-circle" size={14} color={plan.color} />
                                                            <Text style={s.planFeature}>{f}</Text>
                                                        </View>
                                                    ))}
                                                </View>
                                            )}

                                            {/* Radio indicator */}
                                            <View style={[s.radioOuter, selected && { borderColor: plan.color }]}>
                                                {selected && <View style={[s.radioInner, { backgroundColor: plan.color }]} />}
                                            </View>
                                        </TouchableOpacity>
                                    );
                                })}
                            </View>

                            <TouchableOpacity onPress={handlePlanSubmit} activeOpacity={0.85} style={{ marginTop: 24 }}>
                                <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.primaryBtn}>
                                    <Text style={s.primaryBtnText}>Continue</Text>
                                    <Ionicons name="arrow-forward" size={16} color="#fff" />
                                </LinearGradient>
                            </TouchableOpacity>

                            <TouchableOpacity onPress={() => { fadeAnim.setValue(0); setStep('form'); }} style={{ marginTop: 12 }}>
                                <Text style={{ textAlign: 'center', color: Colors.primary, fontSize: 14 }}>← Back</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </ScrollView>
            </Animated.View>
        );
    }

    // ═══════════════════════════════════════════════════════════
    // FAMILY STEP
    // ═══════════════════════════════════════════════════════════
    if (step === 'family') {
        return (
            <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
                <ScrollView style={{ flex: 1, backgroundColor: '#fff' }} contentContainerStyle={{ flexGrow: 1 }}>
                    <LinearGradient colors={['#61dafbaa', '#646cffaa', '#5915a7']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.smallHeader}>
                        <Ionicons name="heart" size={28} color="#fff" />
                        <Text style={s.smallBrand}>DilCare</Text>
                        <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13, marginTop: 2 }}>Set up your family</Text>
                    </LinearGradient>

                    <View style={{ paddingHorizontal: 16, paddingVertical: 20, marginTop: -16 }}>
                        <View style={s.card}>
                            <ProgressBar currentIdx={2} />

                            <View style={{ alignItems: 'center', marginBottom: 24 }}>
                                <Ionicons name="people" size={48} color={Colors.primary} />
                                <Text style={[s.cardTitle, { textAlign: 'center', marginTop: 12 }]}>Connect with Family</Text>
                                <Text style={[s.cardSubtitle, { textAlign: 'center' }]}>
                                    Create a family group or join an existing one
                                </Text>
                            </View>

                            {!!familyError && <View style={s.errorBanner}><Text style={s.errorText}>{familyError}</Text></View>}

                            {!familyChoice && (
                                <View style={{ gap: 14 }}>
                                    <TouchableOpacity style={s.choiceCard} onPress={() => setFamilyChoice('create')} activeOpacity={0.7}>
                                        <View style={[s.choiceIcon, { backgroundColor: Colors.primaryBg }]}>
                                            <Ionicons name="add-circle" size={28} color={Colors.primary} />
                                        </View>
                                        <View style={{ flex: 1 }}>
                                            <Text style={s.choiceTitle}>Create Family</Text>
                                            <Text style={s.choiceDesc}>Start a new family group and invite members</Text>
                                        </View>
                                        <Ionicons name="chevron-forward" size={20} color={Colors.textMuted} />
                                    </TouchableOpacity>

                                    <TouchableOpacity style={s.choiceCard} onPress={() => setFamilyChoice('join')} activeOpacity={0.7}>
                                        <View style={[s.choiceIcon, { backgroundColor: '#dbeafe' }]}>
                                            <Ionicons name="link" size={28} color="#3b82f6" />
                                        </View>
                                        <View style={{ flex: 1 }}>
                                            <Text style={s.choiceTitle}>Join Family</Text>
                                            <Text style={s.choiceDesc}>Enter an invite code to join an existing family</Text>
                                        </View>
                                        <Ionicons name="chevron-forward" size={20} color={Colors.textMuted} />
                                    </TouchableOpacity>

                                    <TouchableOpacity onPress={handleSkipFamily} disabled={loading} style={{ marginTop: 4 }}>
                                        {loading
                                            ? <ActivityIndicator color={Colors.primary} />
                                            : <Text style={{ textAlign: 'center', color: Colors.textMuted, fontSize: 15 }}>Skip for now</Text>}
                                    </TouchableOpacity>
                                </View>
                            )}

                            {familyChoice === 'create' && (
                                <View>
                                    <Text style={s.fieldLabel}>Family Name</Text>
                                    <View style={s.inputWrapper}>
                                        <Ionicons name="people-outline" size={18} color={Colors.primary} style={s.inputIcon} />
                                        <TextInput style={s.input} placeholder="e.g. Sharma Family" placeholderTextColor={Colors.textMuted} value={familyName} onChangeText={setFamilyName} />
                                    </View>

                                    <TouchableOpacity onPress={handleFamilySubmit} disabled={loading} activeOpacity={0.85} style={{ marginTop: 20 }}>
                                        <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.primaryBtn}>
                                            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.primaryBtnText}>Create Family & Sign Up</Text>}
                                        </LinearGradient>
                                    </TouchableOpacity>
                                    <TouchableOpacity onPress={() => setFamilyChoice(null)} style={{ marginTop: 16 }}>
                                        <Text style={{ textAlign: 'center', color: Colors.primary, fontSize: 14 }}>← Back</Text>
                                    </TouchableOpacity>
                                </View>
                            )}

                            {familyChoice === 'join' && (
                                <View>
                                    <Text style={s.fieldLabel}>Invite Code</Text>
                                    <View style={s.inputWrapper}>
                                        <Ionicons name="key-outline" size={18} color={Colors.primary} style={s.inputIcon} />
                                        <TextInput
                                            style={[s.input, { letterSpacing: 4, fontWeight: '700', fontSize: 20, textAlign: 'center' }]}
                                            placeholder="X7K9P2" placeholderTextColor={Colors.textMuted}
                                            value={inviteCode} onChangeText={(v) => setInviteCode(v.toUpperCase().slice(0, 6))}
                                            maxLength={6} autoCapitalize="characters"
                                        />
                                    </View>

                                    <TouchableOpacity onPress={handleFamilySubmit} disabled={loading} activeOpacity={0.85} style={{ marginTop: 20 }}>
                                        <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.primaryBtn}>
                                            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.primaryBtnText}>Join Family & Sign Up</Text>}
                                        </LinearGradient>
                                    </TouchableOpacity>
                                    <TouchableOpacity onPress={() => setFamilyChoice(null)} style={{ marginTop: 16 }}>
                                        <Text style={{ textAlign: 'center', color: Colors.primary, fontSize: 14 }}>← Back</Text>
                                    </TouchableOpacity>
                                </View>
                            )}

                            <TouchableOpacity onPress={() => { fadeAnim.setValue(0); setStep('plan'); }} style={{ marginTop: 16 }}>
                                <Text style={{ textAlign: 'center', color: Colors.textMuted, fontSize: 13 }}>← Back to Plans</Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </ScrollView>
            </Animated.View>
        );
    }

    // ═══════════════════════════════════════════════════════════
    // FORM STEP
    // ═══════════════════════════════════════════════════════════
    return (
        <Animated.View style={{ flex: 1, opacity: fadeAnim }}>
            <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
                <ScrollView style={{ flex: 1, backgroundColor: '#fff' }} contentContainerStyle={{ flexGrow: 1 }}>
                    <LinearGradient colors={['#61dafbaa', '#646cffaa', '#5915a7']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={s.smallHeader}>
                        <Ionicons name="heart" size={28} color="#fff" />
                        <Text style={s.smallBrand}>DilCare</Text>
                        <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13, marginTop: 2 }}>Create your health profile</Text>
                    </LinearGradient>

                    <View style={{ paddingHorizontal: 16, paddingVertical: 20, marginTop: -16 }}>
                        <View style={s.card}>
                            <ProgressBar currentIdx={0} />
                            <Text style={s.cardTitle}>Create Your Account</Text>

                            {!!apiError && <View style={s.errorBanner}><Text style={s.errorText}>{apiError}</Text></View>}

                            {/* Name */}
                            <Text style={s.fieldLabel}>Full Name *</Text>
                            <View style={[s.inputWrapper, errors.name && s.inputError]}>
                                <Ionicons name="person-outline" size={18} color={Colors.primary} style={s.inputIcon} />
                                <TextInput style={s.input} placeholder="Rajesh Kumar" placeholderTextColor={Colors.textMuted}
                                    value={name} onChangeText={(v) => { setName(v); setErrors((p: any) => ({ ...p, name: undefined })); }} />
                            </View>
                            {errors.name && <Text style={s.fieldError}>{errors.name}</Text>}

                            {/* Email */}
                            <Text style={[s.fieldLabel, { marginTop: 14 }]}>Email Address *</Text>
                            <View style={[s.inputWrapper, errors.email && s.inputError]}>
                                <Ionicons name="mail-outline" size={18} color={Colors.primary} style={s.inputIcon} />
                                <TextInput style={s.input} placeholder="you@email.com" placeholderTextColor={Colors.textMuted}
                                    value={email} onChangeText={(v) => { setEmail(v); setErrors((p: any) => ({ ...p, email: undefined })); setApiError(''); }}
                                    keyboardType="email-address" autoCapitalize="none" />
                            </View>
                            {errors.email && <Text style={s.fieldError}>{errors.email}</Text>}

                            {/* Password */}
                            <Text style={[s.fieldLabel, { marginTop: 14 }]}>Password *</Text>
                            <View style={[s.inputWrapper, errors.password && s.inputError]}>
                                <Ionicons name="lock-closed-outline" size={18} color={Colors.primary} style={s.inputIcon} />
                                <TextInput style={s.input} placeholder="Min. 8 characters" placeholderTextColor={Colors.textMuted}
                                    value={password} onChangeText={(v) => { setPassword(v); setErrors((p: any) => ({ ...p, password: undefined })); }}
                                    secureTextEntry />
                            </View>
                            {errors.password && <Text style={s.fieldError}>{errors.password}</Text>}

                            {/* Submit */}
                            <TouchableOpacity onPress={handleFormSubmit} activeOpacity={0.85} style={{ marginTop: 24 }}>
                                <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={s.primaryBtn}>
                                    <Text style={s.primaryBtnText}>Next: Choose Plan</Text>
                                    <Ionicons name="arrow-forward" size={16} color="#fff" />
                                </LinearGradient>
                            </TouchableOpacity>

                            <TouchableOpacity onPress={() => navigation.navigate('Login')} style={{ marginTop: 16 }}>
                                <Text style={{ textAlign: 'center', fontSize: 14, color: Colors.textSecondary }}>
                                    Already have an account? <Text style={{ color: Colors.primary, fontWeight: '600' }}>Log In</Text>
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </Animated.View>
    );
}

// ═══════════════════════════════════════════════════════════════
// STYLES
// ═══════════════════════════════════════════════════════════════
const s = StyleSheet.create({
    // ── Splash ──
    splashContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    splashRings: { alignItems: 'center', justifyContent: 'center', width: 160, height: 160, marginBottom: 32 },
    splashLogo: {
        width: 96, height: 96, borderRadius: 48,
        backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center',
        borderWidth: 2, borderColor: 'rgba(255,255,255,0.3)',
    },
    splashBrand: { fontSize: 48, fontWeight: '700', color: '#fff', letterSpacing: -1 },
    splashTagline: { color: 'rgba(255,255,255,0.8)', fontSize: 14, letterSpacing: 4, marginTop: 8, textTransform: 'uppercase' },
    loadingDots: { flexDirection: 'row', gap: 8, marginTop: 48 },
    dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: 'rgba(255,255,255,0.7)' },

    // ── Success ──
    successContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#fff', padding: 24 },
    successCircle: { width: 96, height: 96, borderRadius: 48, backgroundColor: '#f0fdf4', justifyContent: 'center', alignItems: 'center', marginBottom: 24 },
    successTitle: { fontSize: 26, fontWeight: '700', color: Colors.foreground, marginBottom: 8 },
    successSubtitle: { fontSize: 16, color: Colors.textSecondary, textAlign: 'center', lineHeight: 24 },
    successPlanBadge: { marginTop: 24, fontSize: 14, color: Colors.primary, fontWeight: '600', backgroundColor: Colors.primaryBg, paddingHorizontal: 16, paddingVertical: 8, borderRadius: Radius.xl, overflow: 'hidden' },

    // ── Header ──
    smallHeader: { height: 140, justifyContent: 'center', alignItems: 'center' },
    smallBrand: { fontSize: 28, fontWeight: '700', color: '#fff', marginTop: 4 },

    // ── Card ──
    card: { backgroundColor: '#fff', borderRadius: Radius['3xl'], padding: 24, ...Shadows.premiumLg },

    // ── Progress ──
    progressRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginBottom: 24 },
    progressDot: { width: 32, height: 32, borderRadius: 16, backgroundColor: Colors.border, justifyContent: 'center', alignItems: 'center' },
    progressDotText: { color: '#fff', fontSize: 12, fontWeight: '700' },
    progressLine: { flex: 1, height: 2, backgroundColor: Colors.border, marginHorizontal: 6, marginBottom: 16 },
    progressLabel: { fontSize: 10, color: Colors.textMuted, marginTop: 4 },

    // ── Form ──
    cardTitle: { fontSize: 22, fontWeight: '700', color: Colors.foreground, marginBottom: 8 },
    cardSubtitle: { fontSize: 14, color: Colors.textSecondary, marginBottom: 4 },
    errorBanner: { backgroundColor: Colors.dangerBg, borderWidth: 1, borderColor: '#fecaca', borderRadius: Radius['2xl'], padding: 16, marginBottom: 16 },
    errorText: { color: '#b91c1c', fontSize: 14 },
    fieldLabel: { fontSize: 14, fontWeight: '600', color: Colors.foreground, marginBottom: 6 },
    inputWrapper: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl, height: 44, paddingHorizontal: 12 },
    inputError: { borderColor: '#f87171' },
    inputIcon: { marginRight: 10 },
    input: { flex: 1, fontSize: 14, color: Colors.foreground },
    fieldError: { color: Colors.danger, fontSize: 12, marginTop: 4 },
    primaryBtn: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', height: 48, borderRadius: Radius.xl, gap: 8 },
    primaryBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },

    // ── Plan Cards ──
    planCard: {
        padding: 16, borderRadius: Radius['2xl'], borderWidth: 1.5, borderColor: Colors.border,
        backgroundColor: '#fff', position: 'relative', ...Shadows.sm,
    },
    planIcon: { width: 44, height: 44, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
    planName: { fontSize: 17, fontWeight: '700' },
    planMembers: { fontSize: 12, color: Colors.textSecondary, marginTop: 1 },
    planPrice: { fontSize: 22, fontWeight: '800' },
    planPeriod: { fontSize: 11, color: Colors.textMuted },
    planBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
    planBadgeText: { color: '#fff', fontSize: 10, fontWeight: '700' },
    planFeature: { fontSize: 12, color: Colors.textSecondary, marginLeft: 6 },
    radioOuter: { position: 'absolute', right: 16, top: 16, width: 22, height: 22, borderRadius: 11, borderWidth: 2, borderColor: Colors.border, justifyContent: 'center', alignItems: 'center' },
    radioInner: { width: 12, height: 12, borderRadius: 6 },

    // ── Family Choice ──
    choiceCard: { flexDirection: 'row', alignItems: 'center', padding: 16, backgroundColor: '#fff', borderRadius: Radius['2xl'], borderWidth: 1, borderColor: Colors.border, ...Shadows.sm },
    choiceIcon: { width: 48, height: 48, borderRadius: 14, justifyContent: 'center', alignItems: 'center', marginRight: 14 },
    choiceTitle: { fontSize: 16, fontWeight: '600', color: Colors.foreground },
    choiceDesc: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
});
