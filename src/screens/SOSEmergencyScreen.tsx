/**
 * SOS Emergency — DilcareGit exact: red-500 #ef4444, red-50 #fef2f2.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Modal, Alert, Vibration, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { sosService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

export default function SOSEmergencyScreen() {
    const [contacts, setContacts] = useState<any[]>([]);
    const [modalVisible, setModalVisible] = useState(false);
    const [newContact, setNewContact] = useState({ name: '', phone: '', relationship: '' });
    const [sosActive, setSosActive] = useState(false);
    const [refreshing, setRefreshing] = useState(false);

    const fetchContacts = async () => { try { const { data } = await sosService.getContacts(); setContacts(Array.isArray(data?.results || data) ? (data?.results || data) : []); } catch { } };
    useFocusEffect(useCallback(() => { fetchContacts(); }, []));

    const addContact = async () => {
        if (!newContact.name.trim() || !newContact.phone.trim()) { Alert.alert('Error', 'Name and phone are required'); return; }
        try { await sosService.addContact(newContact); setNewContact({ name: '', phone: '', relationship: '' }); setModalVisible(false); fetchContacts(); }
        catch (err: any) { Alert.alert('Error', err?.response?.data?.error || 'Failed'); }
    };

    const triggerSOS = async () => {
        Vibration.vibrate([100, 200, 100, 200, 100]);
        setSosActive(true);
        try { await sosService.triggerSOS({ message: 'Emergency triggered from DilCare app' }); Alert.alert('SOS Sent', 'Emergency contacts have been notified'); } catch { Alert.alert('SOS', 'Emergency alert recorded'); }
        setTimeout(() => setSosActive(false), 3000);
    };

    const confirmSOS = () => { Alert.alert('🚨 Emergency SOS', 'This will alert all your emergency contacts. Are you sure?', [{ text: 'Cancel', style: 'cancel' }, { text: 'SEND SOS', style: 'destructive', onPress: triggerSOS }]); };

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingHorizontal: 16, paddingVertical: 24, paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await fetchContacts(); setRefreshing(false); }} />}>

                {/* Hero */}
                <View style={styles.heroWrapper}>
                    <LinearGradient colors={['#ef4444', '#dc2626']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.hero}>
                        <View style={[styles.heroCircle, { top: -24, right: -24, width: 128, height: 128 }]} />
                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}><Ionicons name="shield-outline" size={16} color="rgba(255,255,255,0.7)" /><Text style={styles.heroLabel}>DILCARE</Text></View>
                                <Text style={styles.heroTitle}>Emergency SOS</Text>
                                <Text style={styles.heroSubtitle}>Quick access to emergency services</Text>
                            </View>
                            <View style={styles.heroIconBox}><Ionicons name="shield" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                {/* SOS Button */}
                <View style={{ alignItems: 'center', marginBottom: 24 }}>
                    <TouchableOpacity onPress={confirmSOS} activeOpacity={0.7}>
                        <View style={[styles.sosButton, sosActive && styles.sosButtonActive]}>
                            <Ionicons name="alert-circle" size={48} color="#fff" />
                            <Text style={styles.sosText}>HOLD FOR SOS</Text>
                            <Text style={styles.sosSub}>Tap to send emergency alert</Text>
                        </View>
                    </TouchableOpacity>
                </View>

                {/* Contacts */}
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, paddingHorizontal: 4 }}>
                    <Text style={styles.sectionTitle}>Emergency Contacts</Text>
                    <TouchableOpacity onPress={() => setModalVisible(true)}>
                        <LinearGradient colors={Gradients.sos} style={styles.addChip}><Ionicons name="add" size={16} color="#fff" /><Text style={{ color: '#fff', fontWeight: '600', fontSize: 13 }}>Add</Text></LinearGradient>
                    </TouchableOpacity>
                </View>
                {contacts.length === 0 && <Text style={styles.emptyText}>No emergency contacts added yet</Text>}
                {contacts.map((c: any, i: number) => (
                    <View key={c.id || i} style={styles.contactCard}>
                        <View style={styles.contactBar} />
                        <View style={styles.contactBody}>
                            <View style={styles.contactAvatar}><Ionicons name="person" size={20} color="#ef4444" /></View>
                            <View style={{ flex: 1 }}><Text style={styles.contactName}>{c.name}</Text><Text style={styles.contactMeta}>{c.phone} {c.relationship ? `• ${c.relationship}` : ''}</Text></View>
                            <TouchableOpacity onPress={() => Alert.alert('Delete', `Remove ${c.name}?`, [{ text: 'Cancel' }, { text: 'Delete', style: 'destructive', onPress: async () => { try { await sosService.deleteContact(c.id); fetchContacts(); } catch { } } }])}>
                                <Ionicons name="trash-outline" size={20} color={Colors.textMuted} />
                            </TouchableOpacity>
                        </View>
                    </View>
                ))}

                {/* Quick actions */}
                <View style={{ flexDirection: 'row', gap: 10, marginTop: 16 }}>
                    {[{ icon: 'call-outline', label: 'Call 112', color: '#ef4444', bg: '#fef2f2' }, { icon: 'medkit-outline', label: 'Ambulance', color: '#f97316', bg: '#fff7ed' }, { icon: 'flame-outline', label: 'Fire', color: '#ef4444', bg: '#fef2f2' }].map((a, i) => (
                        <TouchableOpacity key={i} style={[styles.quickCard, { backgroundColor: a.bg }]} activeOpacity={0.7}>
                            <Ionicons name={a.icon as any} size={24} color={a.color} />
                            <Text style={[styles.quickLabel, { color: a.color }]}>{a.label}</Text>
                        </TouchableOpacity>
                    ))}
                </View>
            </ScrollView>

            {/* Add contact modal */}
            <Modal visible={modalVisible} animationType="slide" transparent>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}><Text style={styles.modalTitle}>Add Emergency Contact</Text><TouchableOpacity onPress={() => setModalVisible(false)}><Ionicons name="close" size={24} color={Colors.textMuted} /></TouchableOpacity></View>
                        <Text style={styles.fieldLabel}>Name *</Text><TextInput style={styles.modalInput} placeholder="Contact name" placeholderTextColor={Colors.textMuted} value={newContact.name} onChangeText={(v) => setNewContact(p => ({ ...p, name: v }))} />
                        <Text style={styles.fieldLabel}>Phone *</Text><TextInput style={styles.modalInput} placeholder="Phone number" placeholderTextColor={Colors.textMuted} value={newContact.phone} onChangeText={(v) => setNewContact(p => ({ ...p, phone: v }))} keyboardType="phone-pad" />
                        <Text style={styles.fieldLabel}>Relationship</Text><TextInput style={styles.modalInput} placeholder="e.g. Father, Doctor" placeholderTextColor={Colors.textMuted} value={newContact.relationship} onChangeText={(v) => setNewContact(p => ({ ...p, relationship: v }))} />
                        <TouchableOpacity onPress={addContact} activeOpacity={0.85}><LinearGradient colors={Gradients.sos} style={styles.modalBtn}><Text style={styles.modalBtnText}>Add Contact</Text></LinearGradient></TouchableOpacity>
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
    sosButton: { width: 180, height: 180, borderRadius: 90, backgroundColor: '#ef4444', justifyContent: 'center', alignItems: 'center', ...Shadows.premiumLg, shadowColor: '#ef4444' },
    sosButtonActive: { backgroundColor: '#dc2626', transform: [{ scale: 1.05 }] },
    sosText: { color: '#fff', fontSize: 16, fontWeight: '800', marginTop: 8 },
    sosSub: { color: 'rgba(255,255,255,0.7)', fontSize: 11, marginTop: 4 },
    sectionTitle: { fontSize: 14, fontWeight: '700', color: Colors.foreground },
    emptyText: { fontSize: 14, color: Colors.textMuted, textAlign: 'center', paddingVertical: 24 },
    contactCard: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: Radius.lg, overflow: 'hidden', marginBottom: 10, ...Shadows.sm },
    contactBar: { width: 4, backgroundColor: '#ef4444', borderTopLeftRadius: 12, borderBottomLeftRadius: 12 },
    contactBody: { flex: 1, flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
    contactAvatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#fef2f2', justifyContent: 'center', alignItems: 'center' },
    contactName: { fontSize: 15, fontWeight: '600', color: Colors.foreground },
    contactMeta: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
    quickCard: { flex: 1, borderRadius: Radius.lg, padding: 18, alignItems: 'center', gap: 8, ...Shadows.sm },
    quickLabel: { fontSize: 12, fontWeight: '600' },
    addChip: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10, gap: 4 },
    modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
    modalContent: { backgroundColor: '#fff', borderTopLeftRadius: Radius['3xl'], borderTopRightRadius: Radius['3xl'], padding: 24, paddingBottom: 40 },
    modalTitle: { fontSize: 18, fontWeight: '700', color: Colors.foreground },
    fieldLabel: { fontSize: 14, fontWeight: '600', color: Colors.foreground, marginBottom: 6 },
    modalInput: { borderWidth: 1, borderColor: Colors.input, borderRadius: Radius.xl, height: 44, paddingHorizontal: 14, fontSize: 14, color: Colors.foreground, marginBottom: 16 },
    modalBtn: { height: 44, borderRadius: Radius.xl, justifyContent: 'center', alignItems: 'center' },
    modalBtnText: { color: '#fff', fontSize: 14, fontWeight: '600' },
});
