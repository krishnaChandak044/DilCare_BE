/**
 * Water Tracker — DilcareGit exact colors: sky-500 #0ea5e9, sky-50 #f0f9ff.
 * Hero: sky gradient. Glass grid. Progress circle.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { waterService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

const DAILY_GOAL = 8;

export default function WaterTrackerScreen() {
    const [glasses, setGlasses] = useState(0);
    const [goal, setGoal] = useState(DAILY_GOAL);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        try { const { data } = await waterService.getToday(); setGlasses(data?.glasses || data?.count || 0); setGoal(data?.goal || DAILY_GOAL); } catch { }
    };
    useFocusEffect(useCallback(() => { fetchData(); }, []));

    const addGlass = async () => { try { await waterService.addGlass(); fetchData(); } catch { } };
    const removeGlass = async () => { if (glasses <= 0) return; try { await waterService.removeGlass(); fetchData(); } catch { } };

    const progress = Math.min((glasses / goal) * 100, 100);
    const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.water} />}>

                {/* Hero */}
                <View style={styles.heroWrapper}>
                    <LinearGradient colors={['#0ea5e9', '#0284c7']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
                        <View style={[styles.heroCircle, { top: -24, right: -24, width: 128, height: 128 }]} />
                        <View style={[styles.heroCircle, { bottom: 0, left: 40, width: 80, height: 80, opacity: 0.08 }]} />
                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                    <Ionicons name="water-outline" size={16} color="rgba(255,255,255,0.7)" />
                                    <Text style={styles.heroLabel}>DILCARE</Text>
                                </View>
                                <Text style={styles.heroTitle}>Water Tracker</Text>
                                <Text style={styles.heroSubtitle}>Stay hydrated, stay healthy</Text>
                            </View>
                            <View style={styles.heroIconBox}><Ionicons name="water" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                {/* Progress card */}
                <View style={styles.mainCard}>
                    <View style={styles.circle}>
                        <Text style={styles.circleCount}>{glasses}</Text>
                        <Text style={styles.circleGoal}>/ {goal} glasses</Text>
                    </View>
                    <View style={styles.progBar}>
                        <LinearGradient colors={Gradients.water} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[styles.progFill, { width: `${progress}%` }]} />
                    </View>
                    <Text style={styles.progText}>{Math.round(progress)}% of daily goal</Text>

                    {/* + / - controls */}
                    <View style={styles.controlsRow}>
                        <TouchableOpacity onPress={removeGlass} style={styles.controlBtn} activeOpacity={0.7}>
                            <Ionicons name="remove" size={24} color={Colors.danger} />
                        </TouchableOpacity>
                        <TouchableOpacity onPress={addGlass} activeOpacity={0.85}>
                            <LinearGradient colors={Gradients.water} style={styles.addGlassBtn}>
                                <Ionicons name="add" size={20} color="#fff" />
                                <Text style={{ color: '#fff', fontWeight: '600', fontSize: 14 }}>Add Glass</Text>
                            </LinearGradient>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={removeGlass} style={styles.controlBtn} activeOpacity={0.7}>
                            <Ionicons name="refresh-outline" size={20} color={Colors.textMuted} />
                        </TouchableOpacity>
                    </View>
                </View>

                {/* Glass grid */}
                <View style={styles.gridCard}>
                    <Text style={styles.sectionTitle}>Today's Intake</Text>
                    <View style={styles.glassGrid}>
                        {Array.from({ length: goal }).map((_, i) => (
                            <View key={i} style={[styles.glassItem, i < glasses && styles.glassItemFilled]}>
                                <Ionicons name="water" size={24} color={i < glasses ? '#0ea5e9' : '#cbd5e1'} />
                                <Text style={[styles.glassNum, i < glasses && { color: '#0284c7' }]}>{i + 1}</Text>
                            </View>
                        ))}
                    </View>
                </View>

                {/* Hydration tips — AI insight style card */}
                <View style={styles.tipCard}>
                    <View style={styles.tipBar}><LinearGradient colors={Gradients.water} style={{ width: 4, height: '100%', borderRadius: 4 }} /></View>
                    <View style={{ flex: 1, padding: 20 }}>
                        <View style={{ flexDirection: 'row', alignItems: 'flex-start', gap: 12 }}>
                            <View style={{ backgroundColor: '#f0f9ff', width: 40, height: 40, borderRadius: Radius['2xl'], justifyContent: 'center', alignItems: 'center' }}>
                                <Ionicons name="sparkles" size={20} color="#0ea5e9" />
                            </View>
                            <View style={{ flex: 1 }}>
                                <Text style={{ fontSize: 12, fontWeight: '700', color: '#0369a1', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>Hydration Tip</Text>
                                <Text style={{ fontSize: 14, color: '#374151', lineHeight: 22 }}>
                                    Drinking water first thing in the morning helps kickstart your metabolism and flush out toxins. 💧
                                </Text>
                            </View>
                        </View>
                    </View>
                </View>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    heroWrapper: { marginBottom: 20, borderRadius: Radius['3xl'], overflow: 'hidden', ...Shadows.md },
    hero: { paddingHorizontal: 24, paddingTop: 28, paddingBottom: 24, overflow: 'hidden', position: 'relative' },
    heroCircle: { position: 'absolute', borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.10)' },
    heroContent: { flexDirection: 'row', alignItems: 'flex-start', zIndex: 1 },
    heroLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 12, fontWeight: '600', letterSpacing: 3, textTransform: 'uppercase' },
    heroTitle: { fontSize: 24, fontWeight: '700', color: '#fff', marginTop: 2 },
    heroSubtitle: { color: 'rgba(255,255,255,0.6)', fontSize: 14, marginTop: 4 },
    heroIconBox: { width: 56, height: 56, borderRadius: Radius['2xl'], backgroundColor: 'rgba(255,255,255,0.20)', justifyContent: 'center', alignItems: 'center' },

    mainCard: { backgroundColor: '#fff', borderRadius: Radius['2xl'], padding: 24, alignItems: 'center', marginBottom: 20, ...Shadows.sm },
    circle: { width: 140, height: 140, borderRadius: 70, borderWidth: 4, borderColor: '#bae6fd', justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
    circleCount: { fontSize: 40, fontWeight: '900', color: '#0284c7' },
    circleGoal: { fontSize: 12, color: Colors.textMuted },
    progBar: { width: '100%', height: 8, backgroundColor: '#e2e8f0', borderRadius: 4, overflow: 'hidden', marginBottom: 8 },
    progFill: { height: '100%', borderRadius: 4 },
    progText: { fontSize: 12, color: Colors.textMuted, marginBottom: 20 },
    controlsRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
    controlBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#f1f5f9', justifyContent: 'center', alignItems: 'center' },
    addGlassBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 20, height: 44, borderRadius: Radius['2xl'] },

    gridCard: { backgroundColor: '#fff', borderRadius: Radius.lg, padding: 16, marginBottom: 20, ...Shadows.sm },
    sectionTitle: { fontSize: 14, fontWeight: '700', color: Colors.foreground, marginBottom: 12 },
    glassGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
    glassItem: { width: 48, height: 56, borderRadius: Radius.lg, backgroundColor: '#f8fafc', justifyContent: 'center', alignItems: 'center', borderWidth: 1.5, borderColor: '#e2e8f0' },
    glassItemFilled: { backgroundColor: '#f0f9ff', borderColor: '#7dd3fc' },
    glassNum: { fontSize: 10, color: Colors.textMuted, marginTop: 2 },

    tipCard: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', ...Shadows.md },
    tipBar: {},
});
