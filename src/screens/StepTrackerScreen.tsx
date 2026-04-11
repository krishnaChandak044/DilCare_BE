/**
 * Step Tracker — DilcareGit exact colors: orange-500 #f97316, orange-50 #fff7ed.
 * Hero: orange gradient. Progress + stats matching web tokens.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { stepsService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

const DAILY_GOAL = 10000;

export default function StepTrackerScreen() {
    const [steps, setSteps] = useState(0);
    const [goal, setGoal] = useState(DAILY_GOAL);
    const [manualSteps, setManualSteps] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        try { const { data } = await stepsService.getToday(); setSteps(data?.steps || 0); setGoal(data?.goal || DAILY_GOAL); } catch { }
    };
    useFocusEffect(useCallback(() => { fetchData(); }, []));

    const addManual = async () => {
        const num = parseInt(manualSteps);
        if (isNaN(num) || num <= 0) { Alert.alert('Error', 'Enter a valid number'); return; }
        try { await stepsService.addManual(num); setManualSteps(''); fetchData(); } catch { }
    };

    const progress = Math.min((steps / goal) * 100, 100);
    const calories = Math.round(steps * 0.04);
    const distance = (steps * 0.000762).toFixed(2);
    const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#f97316" />}>

                {/* Hero — orange */}
                <View style={styles.heroWrapper}>
                    <LinearGradient colors={['#f97316', '#ea580c']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
                        <View style={[styles.heroCircle, { top: -24, right: -24, width: 128, height: 128 }]} />
                        <View style={[styles.heroCircle, { bottom: 0, left: 40, width: 80, height: 80, opacity: 0.08 }]} />
                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                    <Ionicons name="footsteps-outline" size={16} color="rgba(255,255,255,0.7)" />
                                    <Text style={styles.heroLabel}>DILCARE</Text>
                                </View>
                                <Text style={styles.heroTitle}>Step Tracker</Text>
                                <Text style={styles.heroSubtitle}>Keep moving, stay healthy</Text>
                            </View>
                            <View style={styles.heroIconBox}><Ionicons name="footsteps" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                {/* Main card */}
                <View style={styles.mainCard}>
                    <View style={styles.circle}>
                        <Ionicons name="footsteps" size={28} color="#f97316" />
                        <Text style={styles.stepCount}>{steps.toLocaleString()}</Text>
                        <Text style={styles.stepGoal}>/ {goal.toLocaleString()}</Text>
                    </View>
                    <View style={styles.progBar}>
                        <LinearGradient colors={Gradients.steps} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={[styles.progFill, { width: `${progress}%` }]} />
                    </View>
                    <Text style={styles.progText}>{Math.round(progress)}% of daily goal</Text>

                    {/* Stats — 3 chips */}
                    <View style={styles.statsRow}>
                        <View style={styles.statBox}><Ionicons name="flame-outline" size={18} color="#ef4444" /><Text style={styles.statValue}>{calories}</Text><Text style={styles.statLabel}>Calories</Text></View>
                        <View style={styles.statBox}><Ionicons name="navigate-outline" size={18} color="#3b82f6" /><Text style={styles.statValue}>{distance}</Text><Text style={styles.statLabel}>km</Text></View>
                        <View style={styles.statBox}><Ionicons name="time-outline" size={18} color="#8b5cf6" /><Text style={styles.statValue}>{Math.round(steps / 100)}</Text><Text style={styles.statLabel}>Minutes</Text></View>
                    </View>
                </View>

                {/* Manual add */}
                <View style={styles.addCard}>
                    <Text style={styles.fieldLabel}>Add Steps Manually</Text>
                    <View style={{ flexDirection: 'row', gap: 10 }}>
                        <TextInput style={styles.manualInput} placeholder="e.g. 2000" placeholderTextColor={Colors.textMuted}
                            value={manualSteps} onChangeText={setManualSteps} keyboardType="numeric" />
                        <TouchableOpacity onPress={addManual} activeOpacity={0.85}>
                            <LinearGradient colors={Gradients.steps} style={styles.manualBtn}>
                                <Ionicons name="add" size={22} color="#fff" />
                            </LinearGradient>
                        </TouchableOpacity>
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
    circle: { width: 150, height: 150, borderRadius: 75, borderWidth: 4, borderColor: '#fed7aa', justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
    stepCount: { fontSize: 32, fontWeight: '900', color: '#ea580c' },
    stepGoal: { fontSize: 12, color: Colors.textMuted },
    progBar: { width: '100%', height: 8, backgroundColor: '#e2e8f0', borderRadius: 4, overflow: 'hidden', marginBottom: 8 },
    progFill: { height: '100%', borderRadius: 4 },
    progText: { fontSize: 12, color: Colors.textMuted, marginBottom: 20 },
    statsRow: { flexDirection: 'row', gap: 12, width: '100%' },
    statBox: { flex: 1, alignItems: 'center', backgroundColor: '#f8fafc', borderRadius: Radius.lg, padding: 14, gap: 4 },
    statValue: { fontSize: 18, fontWeight: '800', color: Colors.foreground },
    statLabel: { fontSize: 11, color: Colors.textMuted },

    addCard: { backgroundColor: '#fff', borderRadius: Radius.lg, padding: 16, ...Shadows.sm },
    fieldLabel: { fontSize: 14, fontWeight: '700', color: Colors.foreground, marginBottom: 12 },
    manualInput: { flex: 1, borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl, height: 44, paddingHorizontal: 14, fontSize: 16, color: Colors.foreground },
    manualBtn: { width: 44, height: 44, borderRadius: Radius.lg, justifyContent: 'center', alignItems: 'center' },
});
