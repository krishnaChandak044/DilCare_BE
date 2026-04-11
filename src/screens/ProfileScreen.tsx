/**
 * Profile Screen — DilcareGit exact colors & patterns.
 * Avatar with primary gradient, link code in primaryBg, menu cards with icon pills.
 */
import React, { useState, useCallback } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput,
    Alert, RefreshControl, Clipboard,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../context/AuthContext';
import { userService, familyService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

export default function ProfileScreen({ navigation }: any) {
    const { user, logout, refreshUser } = useAuth();
    const [editing, setEditing] = useState(false);
    const [form, setForm] = useState({ name: '', phone: '', address: '', emergency_contact: '' });
    const [linkCode, setLinkCode] = useState('');
    const [family, setFamily] = useState<any>(null);
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        try { const { data } = await userService.getProfile(); setForm({ name: data?.name || `${data?.first_name || ''} ${data?.last_name || ''}`.trim(), phone: data?.phone || '', address: data?.address || '', emergency_contact: data?.emergency_contact || '' }); } catch { }
        try { const { data } = await userService.getLinkCode(); setLinkCode(data?.parent_link_code || data?.link_code || ''); } catch { }
        try { const { data } = await familyService.getMyFamily(); setFamily(data); } catch { setFamily(null); }
    };
    useFocusEffect(useCallback(() => { fetchData(); }, []));

    const saveProfile = async () => { try { await userService.updateProfile(form); setEditing(false); await refreshUser(); Alert.alert('Success', 'Profile updated'); } catch { Alert.alert('Error', 'Failed to update'); } };
    const handleLogout = () => { Alert.alert('Logout', 'Are you sure?', [{ text: 'Cancel' }, { text: 'Logout', style: 'destructive', onPress: logout }]); };
    const copyCode = () => { if (linkCode) { try { Clipboard.setString(linkCode); } catch { } Alert.alert('Copied', `Link code: ${linkCode}`); } };

    const initial = (user?.name || user?.first_name || 'U')[0].toUpperCase();
    const onRefresh = async () => { setRefreshing(true); await fetchData(); setRefreshing(false); };

    const menuItems = [
        { icon: 'people-outline', label: 'Family', desc: family?.has_family ? `${family.name} (${family.member_count} members)` : 'Not in a family', screen: 'FamilyDashboard', color: Colors.primary, bg: Colors.primaryBg },
        { icon: 'water-outline', label: 'Water Tracker', screen: 'Water', color: '#0ea5e9', bg: '#f0f9ff' },
        { icon: 'notifications-outline', label: 'Notifications', screen: 'Notifications', color: '#f97316', bg: '#fff7ed' },
        { icon: 'settings-outline', label: 'Settings', color: Colors.textMuted, bg: '#f8fafc' },
        { icon: 'help-circle-outline', label: 'Help & Support', color: Colors.textMuted, bg: '#f8fafc' },
    ];

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primary} />}>

                {/* Avatar */}
                <View style={styles.avatarSection}>
                    <LinearGradient colors={Gradients.primaryButton} style={styles.avatar}>
                        <Text style={styles.avatarText}>{initial}</Text>
                    </LinearGradient>
                    <Text style={styles.userName}>{user?.name || form.name || 'User'}</Text>
                    <Text style={styles.userEmail}>{user?.email || ''}</Text>
                    {!!linkCode && (
                        <TouchableOpacity style={styles.linkCodeBox} onPress={copyCode} activeOpacity={0.7}>
                            <Ionicons name="link-outline" size={16} color={Colors.primary} />
                            <Text style={styles.linkCodeText}>{linkCode}</Text>
                            <Ionicons name="copy-outline" size={16} color={Colors.textMuted} />
                        </TouchableOpacity>
                    )}
                </View>

                {/* Profile Details */}
                <View style={styles.section}>
                    <View style={styles.sectionHeader}>
                        <Text style={styles.sectionTitle}>Profile Details</Text>
                        <TouchableOpacity onPress={() => editing ? saveProfile() : setEditing(true)}>
                            <Text style={{ color: Colors.primary, fontWeight: '600', fontSize: 14 }}>{editing ? 'Save' : 'Edit'}</Text>
                        </TouchableOpacity>
                    </View>
                    {[{ label: 'Name', key: 'name', icon: 'person-outline' }, { label: 'Phone', key: 'phone', icon: 'call-outline' }, { label: 'Address', key: 'address', icon: 'location-outline' }, { label: 'Emergency Contact', key: 'emergency_contact', icon: 'alert-circle-outline' }].map(f => (
                        <View key={f.key} style={styles.fieldRow}>
                            <View style={styles.fieldIcon}><Ionicons name={f.icon as any} size={18} color={Colors.primary} /></View>
                            <View style={{ flex: 1 }}>
                                <Text style={styles.fieldLabel}>{f.label}</Text>
                                {editing ? (
                                    <TextInput style={styles.fieldInput} value={(form as any)[f.key]} onChangeText={(v) => setForm(p => ({ ...p, [f.key]: v }))} placeholder={`Enter ${f.label.toLowerCase()}`} placeholderTextColor={Colors.textMuted} />
                                ) : (
                                    <Text style={styles.fieldValue}>{(form as any)[f.key] || 'Not set'}</Text>
                                )}
                            </View>
                        </View>
                    ))}
                </View>

                {/* Menu */}
                <View style={styles.section}>
                    {menuItems.map((item, i) => (
                        <TouchableOpacity key={i} style={styles.menuRow} onPress={() => item.screen && navigation.navigate(item.screen)} activeOpacity={0.7}>
                            <View style={[styles.menuIcon, { backgroundColor: item.bg }]}><Ionicons name={item.icon as any} size={20} color={item.color} /></View>
                            <View style={{ flex: 1 }}><Text style={styles.menuLabel}>{item.label}</Text>{item.desc && <Text style={styles.menuDesc}>{item.desc}</Text>}</View>
                            <Ionicons name="chevron-forward" size={18} color={Colors.textMuted} />
                        </TouchableOpacity>
                    ))}
                </View>

                {/* Logout */}
                <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.7}>
                    <Ionicons name="log-out-outline" size={20} color={Colors.danger} />
                    <Text style={styles.logoutText}>Log Out</Text>
                </TouchableOpacity>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    avatarSection: { alignItems: 'center', paddingVertical: 24, paddingTop: 16 },
    avatar: { width: 80, height: 80, borderRadius: 40, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
    avatarText: { fontSize: 32, fontWeight: '700', color: '#fff' },
    userName: { fontSize: 22, fontWeight: '700', color: Colors.foreground },
    userEmail: { fontSize: 14, color: Colors.textSecondary, marginTop: 2 },
    linkCodeBox: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.primaryBg, paddingHorizontal: 14, paddingVertical: 8, borderRadius: Radius.lg, marginTop: 12, gap: 8 },
    linkCodeText: { fontSize: 15, fontWeight: '800', color: Colors.primary, letterSpacing: 2 },

    section: { marginHorizontal: 16, backgroundColor: '#fff', borderRadius: Radius.lg, padding: 16, marginBottom: 16, ...Shadows.sm },
    sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
    sectionTitle: { fontSize: 14, fontWeight: '700', color: Colors.foreground },

    fieldRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: Colors.borderLight, gap: 12 },
    fieldIcon: { width: 36, height: 36, borderRadius: 10, backgroundColor: Colors.primaryBg, justifyContent: 'center', alignItems: 'center' },
    fieldLabel: { fontSize: 12, color: Colors.textMuted },
    fieldValue: { fontSize: 15, fontWeight: '500', color: Colors.foreground, marginTop: 2 },
    fieldInput: { fontSize: 15, color: Colors.foreground, borderBottomWidth: 1, borderBottomColor: Colors.primary, marginTop: 2, paddingVertical: 2 },

    menuRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12, gap: 12 },
    menuIcon: { width: 40, height: 40, borderRadius: Radius.lg, justifyContent: 'center', alignItems: 'center' },
    menuLabel: { fontSize: 15, fontWeight: '500', color: Colors.foreground },
    menuDesc: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },

    logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginHorizontal: 16, marginBottom: 40, padding: 14, borderRadius: Radius.lg, backgroundColor: Colors.dangerBg, gap: 8 },
    logoutText: { fontSize: 16, fontWeight: '600', color: Colors.danger },
});
