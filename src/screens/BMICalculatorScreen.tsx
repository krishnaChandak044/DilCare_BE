/**
 * BMI Calculator — DilcareGit exact: purple-600 #9333ea, purple-50 #faf5ff.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { bmiService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

const getCategory = (bmi: number) => {
    if (bmi < 18.5) return { label: 'Underweight', color: '#f59e0b', bg: '#fffbeb', icon: 'trending-down-outline' };
    if (bmi < 25) return { label: 'Normal', color: '#16a34a', bg: '#f0fdf4', icon: 'checkmark-circle-outline' };
    if (bmi < 30) return { label: 'Overweight', color: '#f97316', bg: '#fff7ed', icon: 'trending-up-outline' };
    return { label: 'Obese', color: '#ef4444', bg: '#fef2f2', icon: 'alert-circle-outline' };
};

export default function BMICalculatorScreen() {
    const [weight, setWeight] = useState('');
    const [height, setHeight] = useState('');
    const [records, setRecords] = useState<any[]>([]);
    const [latestBMI, setLatestBMI] = useState<number | null>(null);
    const [refreshing, setRefreshing] = useState(false);

    const fetchRecords = async () => {
        try { const { data } = await bmiService.getRecords(); const list = data?.results || data || []; const arr = Array.isArray(list) ? list : []; setRecords(arr); if (arr.length > 0) setLatestBMI(arr[0].bmi); } catch { }
    };
    useFocusEffect(useCallback(() => { fetchRecords(); }, []));

    const calculate = async () => {
        const w = parseFloat(weight), h = parseFloat(height);
        if (isNaN(w) || isNaN(h) || w <= 0 || h <= 0) { Alert.alert('Error', 'Enter valid weight and height'); return; }
        try { await bmiService.addRecord({ weight_kg: w, height_cm: h }); setWeight(''); setHeight(''); fetchRecords(); }
        catch (err: any) { Alert.alert('Error', err?.response?.data?.error || 'Failed'); }
    };

    const cat = latestBMI ? getCategory(latestBMI) : null;
    const onRefresh = async () => { setRefreshing(true); await fetchRecords(); setRefreshing(false); };

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#9333ea" />}>

                {/* Hero */}
                <View style={styles.heroWrapper}>
                    <LinearGradient colors={['#8b5cf6', '#6d28d9']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
                        <View style={[styles.heroCircle, { top: -24, right: -24, width: 128, height: 128 }]} />
                        <View style={[styles.heroCircle, { bottom: 0, left: 40, width: 80, height: 80, opacity: 0.08 }]} />
                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                    <Ionicons name="scale-outline" size={16} color="rgba(255,255,255,0.7)" />
                                    <Text style={styles.heroLabel}>DILCARE</Text>
                                </View>
                                <Text style={styles.heroTitle}>BMI Calculator</Text>
                                <Text style={styles.heroSubtitle}>Know your Body Mass Index</Text>
                            </View>
                            <View style={styles.heroIconBox}><Ionicons name="scale" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                {/* Latest BMI result */}
                {latestBMI && cat && (
                    <View style={[styles.resultCard, { borderLeftColor: cat.color }]}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <View>
                                <Text style={styles.resultLabel}>Your BMI</Text>
                                <Text style={[styles.resultValue, { color: cat.color }]}>{latestBMI.toFixed(1)}</Text>
                            </View>
                            <View style={[styles.statusBadge, { backgroundColor: cat.bg }]}>
                                <Ionicons name={cat.icon as any} size={14} color={cat.color} />
                                <Text style={[styles.statusText, { color: cat.color }]}>{cat.label}</Text>
                            </View>
                        </View>
                    </View>
                )}

                {/* Calculator */}
                <View style={styles.calcCard}>
                    <Text style={styles.sectionTitle}>Calculate BMI</Text>
                    <Text style={styles.fieldLabel}>Weight (kg)</Text>
                    <View style={styles.inputWrapper}><Ionicons name="fitness-outline" size={18} color="#8b5cf6" style={{ marginRight: 10 }} />
                        <TextInput style={styles.input} placeholder="e.g. 70" placeholderTextColor={Colors.textMuted} value={weight} onChangeText={setWeight} keyboardType="numeric" /></View>
                    <Text style={[styles.fieldLabel, { marginTop: 14 }]}>Height (cm)</Text>
                    <View style={styles.inputWrapper}><Ionicons name="resize-outline" size={18} color="#8b5cf6" style={{ marginRight: 10 }} />
                        <TextInput style={styles.input} placeholder="e.g. 170" placeholderTextColor={Colors.textMuted} value={height} onChangeText={setHeight} keyboardType="numeric" /></View>
                    <TouchableOpacity onPress={calculate} activeOpacity={0.85} style={{ marginTop: 20 }}>
                        <LinearGradient colors={Gradients.bmi} style={styles.calcBtn}><Ionicons name="calculator-outline" size={18} color="#fff" /><Text style={styles.calcBtnText}>Calculate</Text></LinearGradient>
                    </TouchableOpacity>
                </View>

                {/* History */}
                {records.length > 0 && (
                    <View style={{ marginTop: 8 }}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, paddingHorizontal: 4 }}>
                            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}><Ionicons name="time-outline" size={16} color="#8b5cf6" /><Text style={styles.sectionTitle}>History</Text></View>
                            <View style={styles.countPill}><Text style={styles.countPillText}>{records.length} entries</Text></View>
                        </View>
                        {records.slice(0, 8).map((r: any, i: number) => {
                            const c = getCategory(r.bmi);
                            return (
                                <View key={r.id || i} style={styles.historyCard}>
                                    <View style={[styles.historyBar, { backgroundColor: c.color }]} />
                                    <View style={styles.historyBody}>
                                        <View style={[styles.historyDot, { backgroundColor: c.bg }]}><Text style={[styles.historyBMI, { color: c.color }]}>{r.bmi.toFixed(1)}</Text></View>
                                        <View style={{ flex: 1 }}><Text style={styles.historyLabel}>{c.label}</Text><Text style={styles.historyMeta}>{r.weight_kg}kg • {r.height_cm}cm</Text></View>
                                        <Text style={styles.historyDate}>{r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</Text>
                                    </View>
                                </View>
                            );
                        })}
                    </View>
                )}
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

    resultCard: { backgroundColor: '#fff', borderRadius: Radius.lg, padding: 20, borderLeftWidth: 4, marginBottom: 16, ...Shadows.sm },
    resultLabel: { fontSize: 13, color: Colors.textMuted },
    resultValue: { fontSize: 40, fontWeight: '900' },
    statusBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999 },
    statusText: { fontSize: 13, fontWeight: '600' },

    calcCard: { backgroundColor: '#fff', borderRadius: Radius.lg, padding: 20, ...Shadows.sm, marginBottom: 16 },
    sectionTitle: { fontSize: 14, fontWeight: '700', color: Colors.foreground, marginBottom: 16 },
    fieldLabel: { fontSize: 14, fontWeight: '600', color: Colors.foreground, marginBottom: 6 },
    inputWrapper: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl, height: 44, paddingHorizontal: 12 },
    input: { flex: 1, fontSize: 14, color: Colors.foreground },
    calcBtn: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', height: 44, borderRadius: Radius.xl, gap: 8 },
    calcBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },

    countPill: { backgroundColor: '#f3f4f6', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999 },
    countPillText: { fontSize: 12, color: Colors.textMuted },
    historyCard: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', marginBottom: 10, ...Shadows.sm },
    historyBar: { width: 4, borderTopLeftRadius: 12, borderBottomLeftRadius: 12 },
    historyBody: { flex: 1, flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
    historyDot: { width: 48, height: 48, borderRadius: Radius.lg, justifyContent: 'center', alignItems: 'center' },
    historyBMI: { fontSize: 16, fontWeight: '700' },
    historyLabel: { fontSize: 14, fontWeight: '600', color: Colors.foreground },
    historyMeta: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
    historyDate: { fontSize: 12, color: Colors.textMuted },
});
