/**
 * Home / Dashboard Screen — EXACT match of DilcareGit/pages/Index.tsx
 *
 * - Page bg: bg-gradient-to-br from-primary/20 via-white to-accent/20
 * - Greeting card: glass border-0 shadow-premium, bg overlay from-blue-500/5 to-purple-500/5
 * - Health stats: 3-col grid, bg-white/50 rounded-xl
 * - Quick actions: 6 cards with bgColor + icon + badge
 * - Secondary actions: 3 cards (AI, Doctors, Profile) — glass border-0 shadow-premium
 * - Action feed: cards with border-l-4 + variant colors
 */
import React, { useState, useCallback } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { stepsService, bmiService, healthService, medicineService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

export default function HomeScreen({ navigation }: any) {
    const { user } = useAuth();
    const hour = new Date().getHours();
    const [refreshing, setRefreshing] = useState(false);

    const [stepsToday, setStepsToday] = useState(0);
    const [latestBMI, setLatestBMI] = useState('--');
    const [latestHR, setLatestHR] = useState('--');
    const [medsDue, setMedsDue] = useState(0);

    const userName = user?.name || user?.first_name || 'User';
    const greeting = hour < 12 ? `Good Morning` : hour < 17 ? `Good Afternoon` : `Good Evening`;
    const greetingIconName = hour < 12 ? 'sunny-outline' : hour < 17 ? 'sunny' : 'moon-outline';
    const greetingIconColor = hour < 12 ? '#f59e0b' : hour < 17 ? '#f97316' : '#3b82f6';

    const fetchData = async () => {
        try {
            const [stepsRes, bmiRes, hrRes, medsRes] = await Promise.allSettled([
                stepsService.getToday(),
                bmiService.getRecords(),
                healthService.getReadings({ type: 'heartRate', limit: 1 }),
                medicineService.getTodaySchedule(),
            ]);
            if (stepsRes.status === 'fulfilled') setStepsToday(stepsRes.value.data?.steps || 0);
            if (bmiRes.status === 'fulfilled') {
                const records = bmiRes.value.data?.results || bmiRes.value.data;
                if (Array.isArray(records) && records.length > 0) setLatestBMI(records[0].bmi?.toFixed(1) || '--');
            }
            if (hrRes.status === 'fulfilled') {
                const readings = hrRes.value.data?.results || hrRes.value.data;
                if (Array.isArray(readings) && readings.length > 0) setLatestHR(`${readings[0].value} BPM`);
            }
            if (medsRes.status === 'fulfilled') {
                const meds = medsRes.value.data?.results || medsRes.value.data;
                if (Array.isArray(meds)) setMedsDue(meds.filter((m: any) => !m.is_taken).length);
            }
        } catch { }
    };

    useFocusEffect(useCallback(() => { fetchData(); }, []));

    const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

    // Quick actions — exact DilcareGit paths + colors
    const quickActions = [
        { key: 'meds', icon: 'medkit-outline', label: 'Medications', desc: 'Smart Reminders', color: '#3b82f6', bg: '#eff6ff', screen: 'Medicine', badge: medsDue > 0 ? `${medsDue} due` : null },
        { key: 'steps', icon: 'footsteps-outline', label: 'Step Tracker', desc: 'Track Steps', color: '#f97316', bg: '#fff7ed', screen: 'Steps', badge: stepsToday > 0 ? stepsToday.toLocaleString() : null },
        { key: 'bmi', icon: 'scale-outline', label: 'BMI Calculator', desc: 'Check BMI', color: '#9333ea', bg: '#faf5ff', screen: 'BMI' },
        { key: 'health', icon: 'pulse-outline', label: 'Health Metrics', desc: 'Track Progress', color: '#059669', bg: '#ecfdf5', screen: 'Health' },
        { key: 'family', icon: 'people-outline', label: 'Family', desc: 'Health Hub', color: '#ec4899', bg: '#fce7f3', screen: 'FamilyDashboard' },
        { key: 'sos', icon: 'shield-outline', label: 'Emergency', desc: 'Instant Help', color: '#ef4444', bg: '#fef2f2', screen: 'SOS' },
        { key: 'wellness', icon: 'book-outline', label: 'Wellness', desc: 'Expert Tips', color: '#8b5cf6', bg: '#f5f3ff', screen: 'Gyaan' },
    ];

    const healthStats = [
        { label: 'Steps Today', value: stepsToday.toLocaleString(), trend: 'Active', icon: 'footsteps-outline', color: '#f97316' },
        { label: 'BMI', value: latestBMI, trend: 'Normal', icon: 'scale-outline', color: '#9333ea' },
        { label: 'Heart Rate', value: latestHR, trend: 'Normal', icon: 'heart-outline', color: '#3b82f6' },
    ];

    const secondaryActions = [
        { icon: 'sparkles-outline', label: 'AI Assistant', screen: 'AI', color: Colors.primary, bg: 'rgba(59,130,246,0.10)' },
        { icon: 'people-outline', label: 'Family', screen: 'FamilyDashboard', color: '#ec4899', bg: 'rgba(236,72,153,0.10)' },
        { icon: 'water-outline', label: 'Water', screen: 'Water', color: '#0ea5e9', bg: 'rgba(14,165,233,0.10)' },
        { icon: 'person-outline', label: 'Profile', screen: 'Profile', color: Colors.textMuted, bg: 'rgba(148,163,184,0.15)' },
    ];

    return (
        <LinearGradient
            colors={Gradients.dashboardBg}
            locations={[0, 0.5, 1]}
            style={{ flex: 1 }}
        >
            <ScrollView
                contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primary} />}
            >
                {/* ── Premium Greeting Card ──────────────────────────────── */}
                <View style={styles.greetingCard}>
                    {/* glass overlay from-blue-500/5 to-purple-500/5 */}
                    <LinearGradient colors={Gradients.cardOverlay} style={StyleSheet.absoluteFillObject} />
                    <View style={styles.greetingBody}>
                        <View style={styles.greetingHeader}>
                            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1, gap: 16 }}>
                                <Ionicons name={greetingIconName as any} size={24} color={greetingIconColor} />
                                <View style={{ flex: 1 }}>
                                    <Text style={styles.greetingText}>{greeting}, {userName}</Text>
                                    <Text style={styles.greetingSubtext}>Your health companion is ready</Text>
                                </View>
                            </View>
                            <Ionicons name="sparkles-outline" size={32} color={Colors.primary} style={{ opacity: 0.6 }} />
                        </View>

                        {/* Quick health overview — grid-cols-3 gap-2 */}
                        <View style={styles.statsRow}>
                            {healthStats.map(stat => (
                                <View key={stat.label} style={styles.statBox}>
                                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                        <Ionicons name={stat.icon as any} size={16} color={stat.color} />
                                        <Text style={styles.statLabel}>{stat.label}</Text>
                                    </View>
                                    <Text style={styles.statValue}>{stat.value}</Text>
                                    <Text style={[styles.statTrend, { color: stat.color }]}>{stat.trend}</Text>
                                </View>
                            ))}
                        </View>
                    </View>
                </View>

                {/* ── Quick Actions Grid ────────────────────────────────── */}
                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Quick Actions</Text>
                </View>
                <View style={styles.actionsGrid}>
                    {quickActions.map(action => (
                        <TouchableOpacity
                            key={action.key}
                            style={styles.actionCard}
                            onPress={() => navigation.navigate(action.screen)}
                            activeOpacity={0.7}
                        >
                            <View style={[styles.actionIcon, { backgroundColor: action.bg }]}>
                                <Ionicons name={action.icon as any} size={22} color={action.color} />
                            </View>
                            <Text style={styles.actionLabel}>{action.label}</Text>
                            <Text style={styles.actionDesc}>{action.desc}</Text>
                            {action.badge && (
                                <View style={[styles.badge, { backgroundColor: action.bg }]}>
                                    <Text style={[styles.badgeText, { color: action.color }]}>{action.badge}</Text>
                                </View>
                            )}
                        </TouchableOpacity>
                    ))}
                </View>

                {/* ── Important Updates (notification feed) ─────────────── */}
                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Important Updates</Text>
                </View>
                {medsDue > 0 ? (
                    <View style={[styles.feedCard, { borderLeftColor: '#3b82f6' }]}>
                        <View style={styles.feedCardHeader}>
                            <View style={{ backgroundColor: '#dbeafe', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 }}>
                                <Text style={{ fontSize: 10, fontWeight: '700', color: '#1d4ed8', textTransform: 'uppercase', letterSpacing: 1 }}>Medicine Reminder</Text>
                            </View>
                            <Text style={{ fontSize: 10, color: Colors.textMuted, fontWeight: '500' }}>Today</Text>
                        </View>
                        <View style={{ flexDirection: 'row', gap: 12 }}>
                            <View style={{ backgroundColor: '#eff6ff', padding: 8, borderRadius: 12 }}>
                                <Ionicons name="medkit-outline" size={20} color="#3b82f6" />
                            </View>
                            <View style={{ flex: 1 }}>
                                <Text style={{ fontSize: 14, fontWeight: '600', color: Colors.foreground }}>Time for your medication!</Text>
                                <Text style={{ fontSize: 12, color: Colors.textMuted, marginTop: 4 }}>You have {medsDue} pending medication{medsDue > 1 ? 's' : ''}</Text>
                            </View>
                        </View>
                    </View>
                ) : (
                    <View style={[styles.feedCard, { borderLeftColor: '#059669' }]}>
                        <View style={styles.feedCardHeader}>
                            <View style={{ backgroundColor: '#d1fae5', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 }}>
                                <Text style={{ fontSize: 10, fontWeight: '700', color: '#047857', textTransform: 'uppercase', letterSpacing: 1 }}>Welcome</Text>
                            </View>
                            <Text style={{ fontSize: 10, color: Colors.textMuted, fontWeight: '500' }}>Just Now</Text>
                        </View>
                        <View style={{ flexDirection: 'row', gap: 12 }}>
                            <View style={{ backgroundColor: '#ecfdf5', padding: 8, borderRadius: 12 }}>
                                <Ionicons name="sparkles-outline" size={20} color="#059669" />
                            </View>
                            <View style={{ flex: 1 }}>
                                <Text style={{ fontSize: 14, fontWeight: '600', color: Colors.foreground }}>Welcome to DilCare!</Text>
                                <Text style={{ fontSize: 12, color: Colors.textMuted, marginTop: 4 }}>Your health dashboard is ready.</Text>
                            </View>
                        </View>
                    </View>
                )}

                {/* ── Secondary Actions — grid-cols-3 glass cards ────────── */}
                <View style={styles.secondaryRow}>
                    {secondaryActions.map(a => (
                        <TouchableOpacity key={a.label} style={styles.secondaryCard} onPress={() => navigation.navigate(a.screen)} activeOpacity={0.7}>
                            <View style={[styles.secondaryIcon, { backgroundColor: a.bg }]}>
                                <Ionicons name={a.icon as any} size={24} color={a.color} />
                            </View>
                            <Text style={styles.secondaryLabel}>{a.label}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </ScrollView>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    // Greeting — glass border-0 shadow-premium
    greetingCard: {
        borderRadius: Radius['2xl'],
        backgroundColor: 'rgba(255,255,255,0.80)',
        overflow: 'hidden', marginBottom: 20,
        ...Shadows.premium,
    },
    greetingBody: { padding: 32 },
    greetingHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 24 },
    greetingText: { fontSize: 24, fontWeight: '700', color: Colors.foreground },
    greetingSubtext: { fontSize: 14, color: Colors.textMuted, fontWeight: '500', marginTop: 4 },
    statsRow: { flexDirection: 'row', gap: 8 },
    statBox: { flex: 1, backgroundColor: 'rgba(255,255,255,0.5)', borderRadius: Radius.xl, padding: 8 },
    statLabel: { fontSize: 12, color: Colors.textMuted, fontWeight: '500' },
    statValue: { fontSize: 18, fontWeight: '800', color: Colors.foreground },
    statTrend: { fontSize: 12, fontWeight: '500', marginTop: 2 },

    sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 4, marginTop: 4, marginBottom: 16 },
    sectionTitle: { fontSize: 18, fontWeight: '700', color: Colors.foreground },

    // Quick action cards
    actionsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 20 },
    actionCard: {
        width: '31%', backgroundColor: '#fff', borderRadius: Radius['2xl'], padding: 16,
        alignItems: 'center',
        ...Shadows.sm,
    },
    actionIcon: { width: 48, height: 48, borderRadius: Radius.xl, justifyContent: 'center', alignItems: 'center', marginBottom: 10 },
    actionLabel: { fontSize: 12, fontWeight: '600', color: Colors.foreground, textAlign: 'center' },
    actionDesc: { fontSize: 10, color: Colors.textMuted, textAlign: 'center', marginTop: 2 },
    badge: { marginTop: 8, paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 },
    badgeText: { fontSize: 10, fontWeight: '700' },

    // Notification feed — glass border-0 shadow-sm border-l-4
    feedCard: {
        backgroundColor: 'rgba(255,255,255,0.80)', borderRadius: Radius.lg, borderLeftWidth: 4,
        padding: 16, marginBottom: 20,
        ...Shadows.sm,
    },
    feedCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 },

    // Secondary — glass border-0 shadow-premium
    secondaryRow: { flexDirection: 'row', gap: 12, marginBottom: 20 },
    secondaryCard: {
        flex: 1, backgroundColor: 'rgba(255,255,255,0.80)', borderRadius: Radius['2xl'], padding: 16, alignItems: 'center',
        ...Shadows.premium,
    },
    secondaryIcon: { borderRadius: Radius.xl, padding: 12, marginBottom: 12 },
    secondaryLabel: { fontSize: 12, fontWeight: '500', color: Colors.foreground },
});
