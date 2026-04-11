/**
 * Doctor — DilcareGit exact: blue-500 #3b82f6, blue-50 #eff6ff.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Modal, Alert, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { doctorService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

export default function DoctorScreen() {
    const [doctors, setDoctors] = useState<any[]>([]);
    const [modalVisible, setModalVisible] = useState(false);
    const [newDoc, setNewDoc] = useState({ name: '', specialization: '', phone: '', hospital: '' });
    const [refreshing, setRefreshing] = useState(false);

    const fetchDoctors = async () => { try { const { data } = await doctorService.getDoctors(); setDoctors(data?.results || data || []); } catch { } };
    useFocusEffect(useCallback(() => { fetchDoctors(); }, []));

    const addDoctor = async () => {
        if (!newDoc.name.trim()) { Alert.alert('Error', 'Doctor name is required'); return; }
        try { await doctorService.addDoctor(newDoc); setNewDoc({ name: '', specialization: '', phone: '', hospital: '' }); setModalVisible(false); fetchDoctors(); }
        catch (err: any) { Alert.alert('Error', err?.response?.data?.error || 'Failed'); }
    };

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await fetchDoctors(); setRefreshing(false); }} />}>

                {/* Hero */}
                <View style={styles.heroWrapper}>
                    <LinearGradient colors={['#3b82f6', '#2563eb']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
                        <View style={[styles.heroCircle, { top: -24, right: -24, width: 128, height: 128 }]} />
                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}><Ionicons name="medical-outline" size={16} color="rgba(255,255,255,0.7)" /><Text style={styles.heroLabel}>DILCARE</Text></View>
                                <Text style={styles.heroTitle}>My Doctors</Text>
                                <Text style={styles.heroSubtitle}>Manage your healthcare providers</Text>
                            </View>
                            <View style={styles.heroIconBox}><Ionicons name="medical" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                {doctors.length === 0 && <Text style={styles.emptyText}>No doctors added yet. Tap + to add.</Text>}
                {doctors.map((d: any, i: number) => (
                    <View key={d.id || i} style={styles.docCard}>
                        <View style={styles.docBar} />
                        <View style={styles.docBody}>
                            <View style={styles.docAvatar}><Ionicons name="medical" size={22} color="#3b82f6" /></View>
                            <View style={{ flex: 1 }}><Text style={styles.docName}>Dr. {d.name}</Text><Text style={styles.docSpec}>{d.specialization || 'General'} {d.hospital ? `• ${d.hospital}` : ''}</Text>{d.phone && <Text style={styles.docPhone}>{d.phone}</Text>}</View>
                            <TouchableOpacity onPress={() => Alert.alert('Delete', `Remove Dr. ${d.name}?`, [{ text: 'Cancel' }, { text: 'Delete', style: 'destructive', onPress: async () => { try { await doctorService.deleteDoctor(d.id); fetchDoctors(); } catch { } } }])}><Ionicons name="trash-outline" size={20} color={Colors.textMuted} /></TouchableOpacity>
                        </View>
                    </View>
                ))}

                {/* Add button */}
                <TouchableOpacity onPress={() => setModalVisible(true)} activeOpacity={0.85} style={{ marginTop: 16 }}>
                    <LinearGradient colors={Gradients.primaryButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.addBtn}>
                        <Ionicons name="add" size={16} color="#fff" /><Text style={styles.addBtnText}>Add Doctor</Text>
                    </LinearGradient>
                </TouchableOpacity>
            </ScrollView>

            <Modal visible={modalVisible} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}><Text style={styles.modalTitle}>Add Doctor</Text><TouchableOpacity onPress={() => setModalVisible(false)}><Ionicons name="close" size={24} color={Colors.textMuted} /></TouchableOpacity></View>
                        {[{ key: 'name', label: 'Name *', ph: 'Dr. Name' }, { key: 'specialization', label: 'Specialization', ph: 'Cardiology' }, { key: 'hospital', label: 'Hospital', ph: 'Hospital name' }, { key: 'phone', label: 'Phone', ph: 'Phone number' }].map(f => (
                            <View key={f.key}><Text style={styles.fieldLabel}>{f.label}</Text><TextInput style={styles.modalInput} placeholder={f.ph} placeholderTextColor={Colors.textMuted} value={(newDoc as any)[f.key]} onChangeText={(v) => setNewDoc(p => ({ ...p, [f.key]: v }))} /></View>
                        ))}
                        <TouchableOpacity onPress={addDoctor} activeOpacity={0.85}><LinearGradient colors={Gradients.primaryButton} style={styles.modalBtn}><Text style={styles.modalBtnText}>Add Doctor</Text></LinearGradient></TouchableOpacity>
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
    heroLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 12, fontWeight: '600', letterSpacing: 3 },
    heroTitle: { fontSize: 24, fontWeight: '700', color: '#fff', marginTop: 2 },
    heroSubtitle: { color: 'rgba(255,255,255,0.6)', fontSize: 14, marginTop: 4 },
    heroIconBox: { width: 56, height: 56, borderRadius: Radius['2xl'], backgroundColor: 'rgba(255,255,255,0.20)', justifyContent: 'center', alignItems: 'center' },
    emptyText: { fontSize: 14, color: Colors.textMuted, textAlign: 'center', paddingVertical: 32 },
    docCard: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', marginBottom: 10, ...Shadows.sm },
    docBar: { width: 4, backgroundColor: '#3b82f6', borderTopLeftRadius: 12, borderBottomLeftRadius: 12 },
    docBody: { flex: 1, flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
    docAvatar: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#eff6ff', justifyContent: 'center', alignItems: 'center' },
    docName: { fontSize: 16, fontWeight: '600', color: Colors.foreground },
    docSpec: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
    docPhone: { fontSize: 12, color: Colors.primary, marginTop: 2 },
    addBtn: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', height: 44, borderRadius: Radius['2xl'], gap: 8 },
    addBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
    modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
    modalContent: { backgroundColor: '#fff', borderTopLeftRadius: Radius['3xl'], borderTopRightRadius: Radius['3xl'], padding: 24, paddingBottom: 40 },
    modalTitle: { fontSize: 18, fontWeight: '700', color: Colors.foreground },
    fieldLabel: { fontSize: 14, fontWeight: '600', color: Colors.foreground, marginBottom: 6 },
    modalInput: { borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl, height: 44, paddingHorizontal: 14, fontSize: 14, color: Colors.foreground, marginBottom: 14 },
    modalBtn: { height: 44, borderRadius: Radius.xl, justifyContent: 'center', alignItems: 'center' },
    modalBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
});
