/**
 * Medicine Reminder — DilcareGit exact colors & patterns.
 * Hero: deep blue-indigo gradient. Cards: border-0 shadow-sm with pill avatar.
 * Progress: colored bar with taken/total count.
 */
import React, { useState, useCallback } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
    Modal, Alert, RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { medicineService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

const PILL_COLORS = ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#06b6d4', '#0ea5e9'];

export default function MedicineReminderScreen() {
    const [medicines, setMedicines] = useState<any[]>([]);
    const [modalVisible, setModalVisible] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [newMed, setNewMed] = useState({ medicine_name: '', dosage: '', schedule_time: '08:00' });

    const fetchMedicines = async () => {
        try { const { data } = await medicineService.getTodaySchedule(); setMedicines(data?.results || data || []); } catch { }
    };

    useFocusEffect(useCallback(() => { fetchMedicines(); }, []));

    const toggleTaken = async (id: number, taken: boolean) => {
        try {
            if (taken) {
                await medicineService.toggleIntake(String(id), 'skipped');
            } else {
                await medicineService.toggleIntake(String(id), 'taken');
            }
            fetchMedicines();
        } catch { }
    };

    const addMedicine = async () => {
        if (!newMed.medicine_name.trim()) { Alert.alert('Error', 'Medicine name is required'); return; }
        try { await medicineService.addMedicine(newMed); setNewMed({ medicine_name: '', dosage: '', schedule_time: '08:00' }); setModalVisible(false); fetchMedicines(); }
        catch (err: any) { Alert.alert('Error', err?.response?.data?.error || 'Failed'); }
    };

    const taken = medicines.filter((m: any) => m.is_taken).length;
    const total = medicines.length;
    const progress = total > 0 ? (taken / total) * 100 : 0;
    const onRefresh = async () => { setRefreshing(true); await fetchMedicines(); setRefreshing(false); };

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primary} />}>

                {/* Hero — medicine blue-indigo gradient */}
                <View style={styles.heroWrapper}>
                    <LinearGradient colors={['#3b82f6', '#4f46e5']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
                        <View style={[styles.heroCircle, { top: -24, right: -24, width: 128, height: 128 }]} />
                        <View style={[styles.heroCircle, { bottom: 0, left: 40, width: 80, height: 80, opacity: 0.08 }]} />
                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                    <Ionicons name="medkit-outline" size={16} color="rgba(255,255,255,0.7)" />
                                    <Text style={styles.heroLabel}>DILCARE</Text>
                                </View>
                                <Text style={styles.heroTitle}>Medicine Reminder</Text>
                                <Text style={styles.heroSubtitle}>Stay on track with your medications</Text>
                            </View>
                            <View style={styles.heroIconBox}><Ionicons name="medkit" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                {/* Progress card */}
                <View style={styles.progressCard}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 }}>
                        <Text style={styles.progressLabel}>Today's Progress</Text>
                        <Text style={styles.progressCount}>{taken}/{total}</Text>
                    </View>
                    <View style={styles.progressBar}>
                        <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                            style={[styles.progressFill, { width: `${progress}%` }]} />
                    </View>
                    {total > 0 && <Text style={styles.progressPercent}>{Math.round(progress)}% completed</Text>}
                </View>

                {/* Medicine list */}
                {medicines.length === 0 && <Text style={styles.emptyText}>No medicines scheduled today</Text>}
                {medicines.map((med: any, i: number) => {
                    const color = PILL_COLORS[i % PILL_COLORS.length];
                    return (
                        <TouchableOpacity key={med.id || i} style={styles.medCard} onPress={() => toggleTaken(med.id, med.is_taken)} activeOpacity={0.7}>
                            <View style={[styles.medBar, { backgroundColor: color }]} />
                            <View style={styles.medBody}>
                                <View style={[styles.medAvatar, { backgroundColor: color + '15' }]}>
                                    <Ionicons name="medical" size={20} color={color} />
                                </View>
                                <View style={{ flex: 1 }}>
                                    <Text style={[styles.medName, med.is_taken && styles.medNameDone]}>{med.medicine_name}</Text>
                                    <Text style={styles.medDosage}>{med.dosage} · {med.schedule_time}</Text>
                                </View>
                                <View style={[styles.statusChip, { backgroundColor: med.is_taken ? Colors.successBg : Colors.warningBg }]}>
                                    <Text style={[styles.statusChipText, { color: med.is_taken ? Colors.success : Colors.warning }]}>
                                        {med.is_taken ? 'Taken' : 'Pending'}
                                    </Text>
                                </View>
                            </View>
                        </TouchableOpacity>
                    );
                })}

                {/* Add button */}
                <TouchableOpacity onPress={() => setModalVisible(true)} activeOpacity={0.85} style={{ marginTop: 16 }}>
                    <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.addBtn}>
                        <Ionicons name="add" size={16} color="#fff" />
                        <Text style={styles.addBtnText}>Add Medicine</Text>
                    </LinearGradient>
                </TouchableOpacity>
            </ScrollView>

            {/* Add Modal */}
            <Modal visible={modalVisible} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                            <Text style={styles.modalTitle}>Add Medicine</Text>
                            <TouchableOpacity onPress={() => setModalVisible(false)}><Ionicons name="close" size={24} color={Colors.textMuted} /></TouchableOpacity>
                        </View>
                        <Text style={styles.fieldLabel}>Medicine Name *</Text>
                        <TextInput style={styles.modalInput} placeholder="e.g. Aspirin" placeholderTextColor={Colors.textMuted} value={newMed.medicine_name} onChangeText={(v) => setNewMed(p => ({ ...p, medicine_name: v }))} />
                        <Text style={styles.fieldLabel}>Dosage</Text>
                        <TextInput style={styles.modalInput} placeholder="e.g. 100mg" placeholderTextColor={Colors.textMuted} value={newMed.dosage} onChangeText={(v) => setNewMed(p => ({ ...p, dosage: v }))} />
                        <Text style={styles.fieldLabel}>Schedule Time</Text>
                        <TextInput style={styles.modalInput} placeholder="HH:MM" placeholderTextColor={Colors.textMuted} value={newMed.schedule_time} onChangeText={(v) => setNewMed(p => ({ ...p, schedule_time: v }))} />
                        <TouchableOpacity onPress={addMedicine} activeOpacity={0.85}>
                            <LinearGradient colors={Gradients.primaryButton} style={styles.modalBtn}><Text style={styles.modalBtnText}>Save Medicine</Text></LinearGradient>
                        </TouchableOpacity>
                    </View>
                </View>
            </Modal>
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

    progressCard: { backgroundColor: '#fff', borderRadius: Radius.lg, padding: 16, marginBottom: 20, ...Shadows.sm },
    progressLabel: { fontSize: 14, fontWeight: '700', color: Colors.foreground },
    progressCount: { fontSize: 14, fontWeight: '700', color: Colors.primary },
    progressBar: { height: 8, backgroundColor: '#e2e8f0', borderRadius: 4, overflow: 'hidden' },
    progressFill: { height: '100%', borderRadius: 4 },
    progressPercent: { fontSize: 12, color: Colors.textMuted, marginTop: 8, textAlign: 'right' },

    emptyText: { fontSize: 14, color: Colors.textMuted, textAlign: 'center', paddingVertical: 32 },

    medCard: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', marginBottom: 12, ...Shadows.sm },
    medBar: { width: 4, borderTopLeftRadius: 12, borderBottomLeftRadius: 12 },
    medBody: { flex: 1, flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
    medAvatar: { width: 40, height: 40, borderRadius: Radius['2xl'], justifyContent: 'center', alignItems: 'center' },
    medName: { fontSize: 15, fontWeight: '700', color: Colors.foreground },
    medNameDone: { textDecorationLine: 'line-through', opacity: 0.5 },
    medDosage: { fontSize: 12, color: Colors.textMuted, marginTop: 2 },
    statusChip: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999 },
    statusChipText: { fontSize: 11, fontWeight: '700' },

    addBtn: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', height: 44, borderRadius: Radius['2xl'], gap: 8 },
    addBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },

    modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
    modalContent: { backgroundColor: '#fff', borderTopLeftRadius: Radius['3xl'], borderTopRightRadius: Radius['3xl'], padding: 24, paddingBottom: 40 },
    modalTitle: { fontSize: 18, fontWeight: '700', color: Colors.foreground },
    fieldLabel: { fontSize: 14, fontWeight: '600', color: Colors.foreground, marginBottom: 6 },
    modalInput: { borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl, height: 44, paddingHorizontal: 14, fontSize: 14, color: Colors.foreground, marginBottom: 16 },
    modalBtn: { height: 44, borderRadius: Radius.xl, justifyContent: 'center', alignItems: 'center' },
    modalBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
});
