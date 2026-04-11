/**
 * Health Tracker — EXACT match of DilcareGit/pages/HealthTracker.tsx
 *
 * - Hero: rounded-3xl gradient #16a34a→#059669, decorative circles
 * - Metric cards: 2×2 grid, border-0 shadow-sm, colored top stripe (h-0.5)
 * - Add reading button: w-full h-11 rounded-2xl
 * - Reading cards: flex with left colored bar (w-1), rounded-2xl icon bg
 * - AI Insight card at bottom
 */
import React, { useState, useCallback } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
    Modal, Alert, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { healthService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

const METRIC_META = {
    bp: { title: 'Blood Pressure', icon: 'heart-outline', color: '#ef4444', bg: '#fef2f2', accent: '#ef4444', unit: 'mmHg' },
    sugar: { title: 'Blood Sugar', icon: 'water-outline', color: '#3b82f6', bg: '#eff6ff', accent: '#3b82f6', unit: 'mg/dL' },
    weight: { title: 'Weight', icon: 'fitness-outline', color: '#16a34a', bg: '#f0fdf4', accent: '#16a34a', unit: 'kg' },
    heartRate: { title: 'Heart Rate', icon: 'pulse-outline', color: '#f97316', bg: '#fff7ed', accent: '#f97316', unit: 'bpm' },
} as const;

const STATUS_META = {
    normal: { label: 'Normal', badgeBg: '#dcfce7', badgeColor: '#15803d' },
    warning: { label: 'Warning', badgeBg: '#fef3c7', badgeColor: '#92400e' },
    danger: { label: 'High', badgeBg: '#fee2e2', badgeColor: '#991b1b' },
};

type MetricKey = keyof typeof METRIC_META;

export default function HealthTrackerScreen() {
    const [readings, setReadings] = useState<any[]>([]);
    const [selectedType, setSelectedType] = useState<MetricKey>('bp');
    const [modalVisible, setModalVisible] = useState(false);
    const [newValue, setNewValue] = useState('');
    const [addType, setAddType] = useState<MetricKey>('bp');
    const [refreshing, setRefreshing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const fetchReadings = async () => {
        try {
            const { data } = await healthService.getReadings({ type: selectedType, limit: 50 });
            const list = data?.results || data || [];
            setReadings(Array.isArray(list) ? list : []);
        } catch { }
    };

    useFocusEffect(useCallback(() => { fetchReadings(); }, [selectedType]));

    const latest = (type: MetricKey) => readings.find((r: any) => (r.reading_type || r.type) === type);

    const addReading = async () => {
        if (!newValue.trim()) return;
        setIsSaving(true);
        try {
            await healthService.addReading({ reading_type: addType, value: newValue.trim() });
            setNewValue('');
            setModalVisible(false);
            fetchReadings();
        } catch (err: any) {
            Alert.alert('Error', err?.response?.data?.error || 'Failed to add reading');
        } finally { setIsSaving(false); }
    };

    const onRefresh = async () => { setRefreshing(true); await fetchReadings(); setRefreshing(false); };
    const typeMeta = METRIC_META[selectedType];

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />

            <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>

                {/* ── Hero header — gradient #16a34a→#059669, rounded-3xl ─── */}
                <View style={styles.heroWrapper}>
                    <LinearGradient colors={Gradients.healthHero} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
                        {/* Decorative circles */}
                        <View style={[styles.heroCircle, { top: -24, right: -24, width: 128, height: 128 }]} />
                        <View style={[styles.heroCircle, { bottom: 0, left: 40, width: 80, height: 80, opacity: 0.08 }]} />

                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                    <Ionicons name="pulse-outline" size={16} color="rgba(255,255,255,0.7)" />
                                    <Text style={styles.heroLabel}>DILCARE</Text>
                                </View>
                                <Text style={styles.heroTitle}>Health Tracker</Text>
                                <Text style={styles.heroSubtitle}>Monitor your vital signs</Text>
                            </View>
                            <View style={styles.heroIcon}>
                                <Ionicons name="pulse" size={28} color="#fff" />
                            </View>
                        </View>
                    </LinearGradient>
                </View>

                {/* ── Metric cards 2×2 — border-0 shadow-sm with colored top stripe ─ */}
                <View style={styles.metricGrid}>
                    {(Object.keys(METRIC_META) as MetricKey[]).map(type => {
                        const m = METRIC_META[type];
                        const r = latest(type);
                        const status = (r?.status || 'normal') as keyof typeof STATUS_META;
                        const sm = STATUS_META[status];
                        return (
                            <TouchableOpacity
                                key={type}
                                style={styles.metricCard}
                                onPress={() => setSelectedType(type)}
                                activeOpacity={0.7}
                            >
                                <View style={[styles.metricStripe, { backgroundColor: m.accent }]} />
                                <View style={styles.metricBody}>
                                    <View style={styles.metricTopRow}>
                                        <View style={[styles.metricIcon, { backgroundColor: m.bg }]}>
                                            <Ionicons name={m.icon as any} size={20} color={m.color} />
                                        </View>
                                        {r && (
                                            <View style={[styles.statusBadge, { backgroundColor: sm.badgeBg }]}>
                                                <Text style={[styles.statusBadgeText, { color: sm.badgeColor }]}>{sm.label}</Text>
                                            </View>
                                        )}
                                    </View>
                                    <Text style={styles.metricLabel}>{m.title}</Text>
                                    <Text style={styles.metricValue}>{r?.value ?? '—'}</Text>
                                    <Text style={styles.metricUnit}>{m.unit}</Text>
                                </View>
                            </TouchableOpacity>
                        );
                    })}
                </View>

                {/* ── Add New Reading button — w-full h-11 rounded-2xl ─── */}
                <TouchableOpacity onPress={() => { setAddType(selectedType); setModalVisible(true); }} activeOpacity={0.85}>
                    <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.addButton}>
                        <Ionicons name="add" size={16} color="#fff" />
                        <Text style={styles.addButtonText}>Add New Reading</Text>
                    </LinearGradient>
                </TouchableOpacity>

                {/* ── Recent Readings — with left color bar ────────────── */}
                <View style={styles.readingsHeader}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                        <Ionicons name="time-outline" size={16} color="#16a34a" />
                        <Text style={styles.readingsTitle}>Recent Readings</Text>
                    </View>
                    <View style={styles.countPill}>
                        <Text style={styles.countPillText}>{readings.length} entries</Text>
                    </View>
                </View>

                {readings.length === 0 && (
                    <Text style={styles.emptyText}>No readings yet. Add your first reading above.</Text>
                )}

                {readings.slice(0, 5).map((reading: any, i: number) => {
                    const type = (reading.reading_type || reading.type || selectedType) as MetricKey;
                    const m = METRIC_META[type] || METRIC_META.bp;
                    const status = (reading.status || 'normal') as keyof typeof STATUS_META;
                    const sm = STATUS_META[status];
                    return (
                        <View key={reading.id || i} style={styles.readingCard}>
                            <View style={[styles.readingBar, { backgroundColor: m.accent }]} />
                            <View style={styles.readingBody}>
                                <View style={[styles.readingIcon, { backgroundColor: m.bg }]}>
                                    <Ionicons name={m.icon as any} size={20} color={m.color} />
                                </View>
                                <View style={{ flex: 1 }}>
                                    <Text style={styles.readingTitle}>{m.title}</Text>
                                    <Text style={styles.readingDate}>
                                        {reading.recorded_at ? new Date(reading.recorded_at).toLocaleDateString() : ''} · {reading.recorded_at ? new Date(reading.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                                    </Text>
                                </View>
                                <View style={{ alignItems: 'flex-end' }}>
                                    <Text style={styles.readingValue}>{reading.value}</Text>
                                    <Text style={styles.readingUnit}>{m.unit}</Text>
                                    <View style={[styles.statusBadge, { backgroundColor: sm.badgeBg, marginTop: 4 }]}>
                                        <Text style={[styles.statusBadgeText, { color: sm.badgeColor }]}>{sm.label}</Text>
                                    </View>
                                </View>
                            </View>
                        </View>
                    );
                })}

                {/* ── AI Health Insight ─────────────────────────────────── */}
                <View style={styles.insightCard}>
                    <View style={[styles.readingBar, { borderTopLeftRadius: 12, borderBottomLeftRadius: 12 }]}>
                        <LinearGradient colors={Gradients.success} style={{ width: 4, height: '100%', borderRadius: 4 }} />
                    </View>
                    <View style={{ flex: 1, padding: 20 }}>
                        <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 12 }}>
                            <View style={{ backgroundColor: '#f0fdf4', width: 40, height: 40, borderRadius: Radius['2xl'], justifyContent: 'center', alignItems: 'center' }}>
                                <Ionicons name="sparkles" size={20} color="#16a34a" />
                            </View>
                            <View style={{ flex: 1 }}>
                                <Text style={{ fontSize: 12, fontWeight: '700', color: '#15803d', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>AI Health Insight</Text>
                                <Text style={{ fontSize: 14, color: '#374151', lineHeight: 22 }}>
                                    Your blood pressure has been stable this week! Keep up the good work with your morning walks. 🚶‍♂️
                                </Text>
                            </View>
                        </View>
                    </View>
                </View>

            </ScrollView>

            {/* ── Add Modal ──────────────────────────────────────────── */}
            <Modal visible={modalVisible} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                                <Ionicons name="pulse-outline" size={20} color="#16a34a" />
                                <Text style={styles.modalTitle}>Add Health Reading</Text>
                            </View>
                            <TouchableOpacity onPress={() => setModalVisible(false)}>
                                <Ionicons name="close" size={24} color={Colors.textMuted} />
                            </TouchableOpacity>
                        </View>

                        <Text style={styles.fieldLabel}>Metric Type</Text>
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }} contentContainerStyle={{ gap: 8 }}>
                            {(Object.keys(METRIC_META) as MetricKey[]).map(t => {
                                const m = METRIC_META[t];
                                return (
                                    <TouchableOpacity key={t} onPress={() => setAddType(t)}
                                        style={[styles.chipBtn, addType === t && { backgroundColor: m.accent, borderColor: m.accent }]}>
                                        <Text style={[styles.chipText, addType === t && { color: '#fff' }]}>{m.title}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>

                        <Text style={styles.fieldLabel}>Value</Text>
                        <TextInput style={styles.modalInput} placeholder="e.g., 120/80, 95, 72.5" placeholderTextColor={Colors.textMuted}
                            value={newValue} onChangeText={setNewValue}
                            keyboardType={addType === 'bp' ? 'default' : 'numeric'} />

                        <TouchableOpacity onPress={addReading} disabled={isSaving} activeOpacity={0.85}>
                            <LinearGradient colors={Gradients.primaryButton} style={styles.modalBtn}>
                                <Text style={styles.modalBtnText}>{isSaving ? 'Saving...' : 'Save Reading'}</Text>
                            </LinearGradient>
                        </TouchableOpacity>
                    </View>
                </View>
            </Modal>
        </View>
    );
}

const styles = StyleSheet.create({
    // Hero
    heroWrapper: { marginBottom: 20, borderRadius: Radius['3xl'], overflow: 'hidden', ...Shadows.md },
    hero: { paddingHorizontal: 24, paddingTop: 28, paddingBottom: 24, overflow: 'hidden', position: 'relative' },
    heroCircle: { position: 'absolute', borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.10)' },
    heroContent: { flexDirection: 'row', alignItems: 'flex-start', zIndex: 1 },
    heroLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 12, fontWeight: '600', letterSpacing: 3, textTransform: 'uppercase' },
    heroTitle: { fontSize: 24, fontWeight: '700', color: '#fff', marginTop: 2 },
    heroSubtitle: { color: 'rgba(255,255,255,0.6)', fontSize: 14, marginTop: 4 },
    heroIcon: { width: 56, height: 56, borderRadius: Radius['2xl'], backgroundColor: 'rgba(255,255,255,0.20)', justifyContent: 'center', alignItems: 'center' },

    // Metrics
    metricGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 20 },
    metricCard: { width: '48%', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', ...Shadows.sm },
    metricStripe: { height: 2, width: '100%' },
    metricBody: { padding: 16 },
    metricTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 },
    metricIcon: { width: 40, height: 40, borderRadius: Radius.xl, justifyContent: 'center', alignItems: 'center' },
    metricLabel: { fontSize: 12, color: Colors.textMuted, fontWeight: '500', marginBottom: 2 },
    metricValue: { fontSize: 24, fontWeight: '900', color: Colors.foreground, lineHeight: 28 },
    metricUnit: { fontSize: 11, color: Colors.textMuted, marginTop: 4 },

    statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 },
    statusBadgeText: { fontSize: 10, fontWeight: '700' },

    // Add button
    addButton: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', height: 44, borderRadius: Radius['2xl'], gap: 8, marginBottom: 24 },
    addButtonText: { color: '#fff', fontSize: 14, fontWeight: '600' },

    // Readings
    readingsHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, paddingHorizontal: 4 },
    readingsTitle: { fontSize: 14, fontWeight: '700', color: Colors.foreground },
    countPill: { backgroundColor: '#f3f4f6', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999 },
    countPillText: { fontSize: 12, color: Colors.textMuted },
    emptyText: { fontSize: 14, color: Colors.textMuted, textAlign: 'center', paddingVertical: 32 },

    readingCard: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', marginBottom: 12, ...Shadows.sm },
    readingBar: { width: 4, borderTopLeftRadius: 12, borderBottomLeftRadius: 12 },
    readingBody: { flex: 1, flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
    readingIcon: { width: 40, height: 40, borderRadius: Radius['2xl'], justifyContent: 'center', alignItems: 'center' },
    readingTitle: { fontSize: 15, fontWeight: '700', color: Colors.foreground },
    readingDate: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
    readingValue: { fontSize: 20, fontWeight: '900', color: Colors.foreground },
    readingUnit: { fontSize: 11, color: Colors.textMuted },

    // Insight card
    insightCard: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', marginTop: 8, ...Shadows.md },

    // Modal
    modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
    modalContent: { backgroundColor: '#fff', borderTopLeftRadius: Radius['3xl'], borderTopRightRadius: Radius['3xl'], padding: 24, paddingBottom: 40 },
    modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
    modalTitle: { fontSize: 18, fontWeight: '700', color: Colors.foreground },
    fieldLabel: { fontSize: 14, fontWeight: '600', color: Colors.foreground, marginBottom: 6 },
    chipBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: Radius.xl, borderWidth: 1, borderColor: Colors.border, backgroundColor: '#fff' },
    chipText: { fontSize: 13, fontWeight: '600', color: Colors.foreground },
    modalInput: { borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl, height: 44, paddingHorizontal: 14, fontSize: 14, color: Colors.foreground, marginBottom: 20 },
    modalBtn: { height: 44, borderRadius: Radius.xl, justifyContent: 'center', alignItems: 'center' },
    modalBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
});
