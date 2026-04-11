/**
 * FamilyMembersScreen — Family member list, detail cards, and create/join family flow.
 * Adapted from DilcareGit's AddFamilyMembers.tsx for the invite_code/join flow.
 */
import React, { useState, useCallback, useRef } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity,
    TextInput, Alert, ActivityIndicator, Animated, Platform, Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { familyService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

// ─── Types ───────────────────────────────────────────────────────────────────
interface FamilyMember {
    user_id: number;
    name: string;
    email?: string;
    role: string;
    nickname?: string;
    is_admin?: boolean;
}

interface MemberHealth {
    overall_status?: string;
    latest_bp?: string;
    latest_sugar?: string;
    latest_heart_rate?: string;
    medicines_today_taken?: number;
    medicines_today_total?: number;
    water_glasses_today?: number;
    water_goal_today?: number;
}

// ─── Relationship helpers ─────────────────────────────────────────────────────
const RELATIONSHIP_META: Record<string, { emoji: string; color: string; bg: string }> = {
    mother: { emoji: '👩', color: '#ec4899', bg: '#fce7f3' },
    father: { emoji: '👨', color: '#3b82f6', bg: '#eff6ff' },
    guardian: { emoji: '🧑', color: '#8b5cf6', bg: '#f5f3ff' },
    brother: { emoji: '👦', color: '#f97316', bg: '#fff7ed' },
    sister: { emoji: '👧', color: '#14b8a6', bg: '#f0fdfa' },
    grandpa: { emoji: '👴', color: '#84cc16', bg: '#f7fee7' },
    grandma: { emoji: '👵', color: '#a855f7', bg: '#faf5ff' },
    child: { emoji: '🧒', color: '#f59e0b', bg: '#fffbeb' },
    admin: { emoji: '👑', color: '#f59e0b', bg: '#fffbeb' },
    member: { emoji: '👤', color: Colors.primary, bg: Colors.primaryBg },
};

function getMeta(role?: string, nickname?: string) {
    const search = (nickname || role || '').toLowerCase();
    const key = Object.keys(RELATIONSHIP_META).find(k => search.includes(k));
    return key ? RELATIONSHIP_META[key] : RELATIONSHIP_META.member;
}

const STATUS_COLORS: Record<string, string> = { good: '#16a34a', warning: '#f59e0b', danger: '#ef4444' };

// ─── Mini health stat chip ────────────────────────────────────────────────────
function HealthChip({ icon, label, value, iconColor }: any) {
    return (
        <View style={cs.chip}>
            <Ionicons name={icon} size={13} color={iconColor} />
            <Text style={cs.chipLabel}>{label}</Text>
            <Text style={cs.chipValue}>{value}</Text>
        </View>
    );
}

// ─── Member detail view ───────────────────────────────────────────────────────
function MemberDetail({
    member, health, isAdmin, onBack, onRemove,
}: {
    member: FamilyMember; health?: MemberHealth; isAdmin: boolean;
    onBack: () => void; onRemove: () => void;
}) {
    const meta = getMeta(member.role, member.nickname);
    const gradient: [string, string] = member.role === 'admin' || member.is_admin
        ? ['#f59e0b', '#ea580c']
        : [meta.color, meta.color + 'bb'];
    const status = health?.overall_status || 'good';
    const medPct = (health?.medicines_today_total || 0) > 0
        ? Math.round(((health?.medicines_today_taken || 0) / (health?.medicines_today_total || 1)) * 100)
        : 0;

    return (
        <ScrollView
            style={{ flex: 1, backgroundColor: Colors.background }}
            contentContainerStyle={{ paddingBottom: 40 }}
            showsVerticalScrollIndicator={false}
        >
            {/* Back button */}
            <TouchableOpacity style={cs.backBtn} onPress={onBack} activeOpacity={0.7}>
                <View style={cs.backBtnInner}>
                    <Ionicons name="chevron-back" size={16} color={Colors.textSecondary} />
                </View>
                <Text style={cs.backBtnText}>Family</Text>
            </TouchableOpacity>

            {/* Profile hero */}
            <View style={cs.heroWrap}>
                <LinearGradient colors={gradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={cs.hero}>
                    <View style={cs.heroBubble1} />
                    <View style={cs.heroBubble2} />
                    <View style={cs.heroRow}>
                        <View style={cs.heroAvatarWrap}>
                            <Text style={cs.heroEmoji}>{meta.emoji}</Text>
                        </View>
                        <View style={{ flex: 1, marginLeft: 16 }}>
                            <Text style={cs.heroName}>{member.name || member.email}</Text>
                            <Text style={cs.heroRole} numberOfLines={1}>
                                {member.role}{member.nickname ? ` · ${member.nickname}` : ''}
                            </Text>
                            <View style={cs.livePill}>
                                <View style={cs.liveDot} />
                                <Text style={cs.liveText}>Live monitoring</Text>
                            </View>
                        </View>
                        {/* Admin actions */}
                        {isAdmin && (
                            <TouchableOpacity
                                style={cs.removeBtn}
                                onPress={onRemove}
                                activeOpacity={0.8}
                            >
                                <Ionicons name="trash" size={16} color="#fff" />
                            </TouchableOpacity>
                        )}
                    </View>
                </LinearGradient>
            </View>

            <View style={{ paddingHorizontal: 16 }}>
                {/* Overall status */}
                <View style={[cs.statusBanner, { backgroundColor: STATUS_COLORS[status] + '18' }]}>
                    <View style={[cs.statusDot, { backgroundColor: STATUS_COLORS[status] }]} />
                    <Text style={[cs.statusText, { color: STATUS_COLORS[status] }]}>
                        {status === 'good' ? 'All vitals look good' : status === 'warning' ? 'Some readings need attention' : 'Health alert — check vitals'}
                    </Text>
                </View>

                {/* Health grid */}
                <Text style={cs.sectionTitle}>Health Stats</Text>
                <View style={cs.healthGrid}>
                    {[
                        health?.latest_bp && { icon: 'heart', color: '#ef4444', label: 'Blood Pressure', value: health.latest_bp, bg: '#fef2f2' },
                        health?.latest_sugar && { icon: 'water', color: '#f97316', label: 'Blood Sugar', value: `${health.latest_sugar} mg/dL`, bg: '#fff7ed' },
                        health?.latest_heart_rate && { icon: 'pulse', color: '#8b5cf6', label: 'Heart Rate', value: `${health.latest_heart_rate} bpm`, bg: '#f5f3ff' },
                        { icon: 'water-outline', color: '#0ea5e9', label: 'Water Intake', value: `${health?.water_glasses_today || 0}/${health?.water_goal_today || 8} glasses`, bg: '#f0f9ff' },
                    ].filter(Boolean).map((item: any) => (
                        <View key={item.label} style={[cs.statCard, { backgroundColor: item.bg }]}>
                            <View style={cs.statIconWrap}>
                                <Ionicons name={item.icon} size={16} color={item.color} />
                            </View>
                            <Text style={cs.statLabel}>{item.label}</Text>
                            <Text style={cs.statValue}>{item.value}</Text>
                        </View>
                    ))}
                </View>

                {/* Medicine adherence */}
                <Text style={cs.sectionTitle}>Medicine Adherence</Text>
                <View style={cs.medCard}>
                    <View style={cs.medHeader}>
                        <View style={cs.medIconWrap}>
                            <Ionicons name="medical" size={18} color={Colors.primary} />
                        </View>
                        <View style={{ flex: 1 }}>
                            <Text style={cs.medTitle}>Today's Medicines</Text>
                            <Text style={cs.medSub}>Daily adherence</Text>
                        </View>
                        <Text style={[cs.medCount, { color: medPct === 100 ? '#22c55e' : Colors.primary }]}>
                            {health?.medicines_today_taken || 0}
                            <Text style={cs.medTotal}>/{health?.medicines_today_total || 0}</Text>
                        </Text>
                    </View>
                    {/* Progress bar */}
                    <View style={cs.medBarBg}>
                        <View style={[cs.medBarFill, {
                            width: `${medPct}%` as any,
                            backgroundColor: medPct === 100 ? '#22c55e' : Colors.primary,
                        }]} />
                    </View>
                    <Text style={cs.medPct}>{medPct}% completed today</Text>
                </View>
            </View>
        </ScrollView>
    );
}

// ─── Member row card ──────────────────────────────────────────────────────────
function MemberRow({ member, health, onPress }: { member: FamilyMember; health?: MemberHealth; onPress: () => void }) {
    const scaleAnim = useRef(new Animated.Value(1)).current;
    const meta = getMeta(member.role, member.nickname);
    const status = health?.overall_status || 'good';
    const medTaken = health?.medicines_today_taken || 0;
    const medTotal = health?.medicines_today_total || 0;

    const handlePress = () => {
        Animated.sequence([
            Animated.timing(scaleAnim, { toValue: 0.97, duration: 70, useNativeDriver: true }),
            Animated.timing(scaleAnim, { toValue: 1, duration: 80, useNativeDriver: true }),
        ]).start();
        onPress();
    };

    return (
        <Animated.View style={[cs.memberRow, { transform: [{ scale: scaleAnim }] }]}>
            <TouchableOpacity onPress={handlePress} activeOpacity={1} style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                {/* Color accent bar */}
                <View style={[cs.accentBar, { backgroundColor: meta.color }]} />

                {/* Avatar */}
                <View style={[cs.rowAvatar, { backgroundColor: meta.bg }]}>
                    <Text style={{ fontSize: 22 }}>{meta.emoji}</Text>
                    <View style={[cs.statusDotSmall, { backgroundColor: STATUS_COLORS[status], borderColor: meta.bg }]} />
                </View>

                {/* Info */}
                <View style={{ flex: 1 }}>
                    <Text style={cs.rowName} numberOfLines={1}>{member.name || member.email}</Text>
                    <Text style={cs.rowRole} numberOfLines={1}>
                        {member.role}{member.nickname ? ` · ${member.nickname}` : ''}
                    </Text>
                </View>

                {/* Med count */}
                {medTotal > 0 && (
                    <View style={cs.medBadge}>
                        <Ionicons name="medical" size={11} color={Colors.primary} />
                        <Text style={cs.medBadgeText}>{medTaken}/{medTotal}</Text>
                    </View>
                )}
                <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
            </TouchableOpacity>
        </Animated.View>
    );
}

// ─── Join / Create modal ──────────────────────────────────────────────────────
function JoinCreateModal({ visible, onDismiss, onCreated, onJoined }: {
    visible: boolean; onDismiss: () => void;
    onCreated: (f: any) => void; onJoined: (f: any) => void;
}) {
    const [mode, setMode] = useState<'menu' | 'create' | 'join'>('menu');
    const [familyName, setFamilyName] = useState('');
    const [inviteCode, setInviteCode] = useState('');
    const [nickname, setNickname] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const reset = () => { setMode('menu'); setFamilyName(''); setInviteCode(''); setNickname(''); setError(''); };

    const handleCreate = async () => {
        if (!familyName.trim()) { setError('Please enter a family name.'); return; }
        setLoading(true); setError('');
        try {
            const { data } = await familyService.createFamily(familyName.trim());
            reset(); onCreated(data);
        } catch (e: any) {
            setError(e?.response?.data?.detail || 'Could not create family. Please try again.');
        } finally { setLoading(false); }
    };

    const handleJoin = async () => {
        if (inviteCode.trim().length < 4) { setError('Enter a valid invite code.'); return; }
        setLoading(true); setError('');
        try {
            const { data } = await familyService.joinFamily(inviteCode.trim().toUpperCase(), nickname.trim() || undefined);
            reset(); onJoined(data);
        } catch (e: any) {
            setError(e?.response?.data?.detail || 'Invalid code or already in a family.');
        } finally { setLoading(false); }
    };

    return (
        <Modal visible={visible} animationType="slide" transparent presentationStyle="overFullScreen">
            <TouchableOpacity style={cs.modalBackdrop} activeOpacity={1} onPress={() => { reset(); onDismiss(); }} />
            <View style={cs.modalSheet}>
                <View style={cs.modalHandle} />

                {mode === 'menu' && (
                    <>
                        <Text style={cs.modalTitle}>Get Started</Text>
                        <Text style={cs.modalSub}>Create your family group or join an existing one.</Text>
                        <TouchableOpacity style={cs.menuBtn} onPress={() => setMode('create')} activeOpacity={0.8}>
                            <LinearGradient colors={Gradients.primaryButton} style={cs.menuBtnGrad}>
                                <Ionicons name="add-circle" size={20} color="#fff" />
                                <Text style={cs.menuBtnText}>Create a Family Group</Text>
                            </LinearGradient>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={cs.menuBtnOutline}
                            onPress={() => setMode('join')}
                            activeOpacity={0.8}
                        >
                            <Ionicons name="link" size={20} color={Colors.primary} />
                            <Text style={cs.menuBtnOutlineText}>Join with Invite Code</Text>
                        </TouchableOpacity>
                    </>
                )}

                {mode === 'create' && (
                    <>
                        <TouchableOpacity onPress={() => { setMode('menu'); setError(''); }} style={cs.modalBack}>
                            <Ionicons name="chevron-back" size={16} color={Colors.textSecondary} />
                            <Text style={cs.modalBackText}>Back</Text>
                        </TouchableOpacity>
                        <Text style={cs.modalTitle}>Create Family</Text>
                        <Text style={cs.modalSub}>Give your family a name to get started.</Text>
                        <Text style={cs.inputLabel}>Family Name</Text>
                        <TextInput
                            style={cs.input}
                            placeholder="e.g. The Sharma Family"
                            placeholderTextColor={Colors.textMuted}
                            value={familyName}
                            onChangeText={t => { setFamilyName(t); setError(''); }}
                        />
                        {error ? <Text style={cs.errorText}>{error}</Text> : null}
                        <TouchableOpacity style={cs.submitBtn} onPress={handleCreate} disabled={loading} activeOpacity={0.85}>
                            <LinearGradient colors={Gradients.primaryButton} style={cs.submitBtnGrad}>
                                {loading
                                    ? <ActivityIndicator color="#fff" />
                                    : <><Ionicons name="people" size={18} color="#fff" /><Text style={cs.submitBtnText}>Create Group</Text></>
                                }
                            </LinearGradient>
                        </TouchableOpacity>
                    </>
                )}

                {mode === 'join' && (
                    <>
                        <TouchableOpacity onPress={() => { setMode('menu'); setError(''); }} style={cs.modalBack}>
                            <Ionicons name="chevron-back" size={16} color={Colors.textSecondary} />
                            <Text style={cs.modalBackText}>Back</Text>
                        </TouchableOpacity>
                        <Text style={cs.modalTitle}>Join Family</Text>
                        <Text style={cs.modalSub}>Ask the family admin to share their invite code.</Text>
                        <Text style={cs.inputLabel}>Invite Code</Text>
                        <TextInput
                            style={[cs.input, cs.codeInput]}
                            placeholder="XXXXXX"
                            placeholderTextColor={Colors.textMuted}
                            value={inviteCode}
                            onChangeText={t => { setInviteCode(t.toUpperCase()); setError(''); }}
                            autoCapitalize="characters"
                            maxLength={10}
                        />
                        <Text style={cs.inputLabel}>Nickname (optional)</Text>
                        <TextInput
                            style={cs.input}
                            placeholder="e.g. Son, Daughter…"
                            placeholderTextColor={Colors.textMuted}
                            value={nickname}
                            onChangeText={t => { setNickname(t); setError(''); }}
                        />
                        {error ? <Text style={cs.errorText}>{error}</Text> : null}
                        <TouchableOpacity style={cs.submitBtn} onPress={handleJoin} disabled={loading} activeOpacity={0.85}>
                            <LinearGradient colors={Gradients.primaryButton} style={cs.submitBtnGrad}>
                                {loading
                                    ? <ActivityIndicator color="#fff" />
                                    : <><Ionicons name="link" size={18} color="#fff" /><Text style={cs.submitBtnText}>Join Family</Text></>
                                }
                            </LinearGradient>
                        </TouchableOpacity>
                    </>
                )}
            </View>
        </Modal>
    );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────
export default function FamilyMembersScreen({ navigation, route }: any) {
    const [family, setFamily] = useState<any>(null);
    const [memberHealth, setMemberHealth] = useState<Record<number, MemberHealth>>({});
    const [loading, setLoading] = useState(true);
    const [selectedMemberId, setSelectedMemberId] = useState<number | null>(route?.params?.memberId || null);
    const [showModal, setShowModal] = useState(false);

    const fetchFamily = useCallback(async () => {
        try {
            const { data } = await familyService.getMyFamily();
            setFamily(data);
            if (data?.members) {
                const hm: Record<number, MemberHealth> = {};
                await Promise.allSettled(
                    data.members.map(async (m: FamilyMember) => {
                        try {
                            const res = await familyService.getMemberHealth(m.user_id);
                            hm[m.user_id] = res.data;
                        } catch { }
                    })
                );
                setMemberHealth(hm);
            }
        } catch {
            setFamily(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useFocusEffect(useCallback(() => { fetchFamily(); }, [fetchFamily]));

    const handleRemove = (member: FamilyMember) => {
        Alert.alert(
            'Remove Member',
            `Remove ${member.name || member.email} from the family?`,
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Remove', style: 'destructive',
                    onPress: async () => {
                        try {
                            await familyService.removeMember(member.user_id);
                            setSelectedMemberId(null);
                            fetchFamily();
                        } catch {
                            Alert.alert('Error', 'Could not remove member. Try again.');
                        }
                    },
                },
            ]
        );
    };

    // ── Detail view ───────────────────────────────────────────────
    const selectedMember = family?.members?.find((m: FamilyMember) => m.user_id === selectedMemberId);
    if (selectedMember) {
        return (
            <View style={{ flex: 1, backgroundColor: Colors.background, paddingTop: Platform.OS === 'ios' ? 48 : 20 }}>
                <MemberDetail
                    member={selectedMember}
                    health={memberHealth[selectedMember.user_id]}
                    isAdmin={family?.my_role === 'admin' || family?.my_role === 'parent'}
                    onBack={() => setSelectedMemberId(null)}
                    onRemove={() => handleRemove(selectedMember)}
                />
            </View>
        );
    }

    // ── Loading ───────────────────────────────────────────────────
    if (loading) {
        return (
            <View style={{ flex: 1, backgroundColor: Colors.background, justifyContent: 'center', alignItems: 'center' }}>
                <ActivityIndicator size="large" color={Colors.primary} />
            </View>
        );
    }

    const members: FamilyMember[] = family?.members || [];
    const hasFamily = family?.has_family;
    const isAdmin = family?.my_role === 'admin' || family?.my_role === 'parent';

    // ── No family state ───────────────────────────────────────────
    if (!hasFamily) {
        return (
            <View style={{ flex: 1, backgroundColor: Colors.background }}>
                <View style={cs.screenHeader}>
                    <TouchableOpacity onPress={() => navigation.goBack()} style={cs.headerBack}>
                        <Ionicons name="chevron-back" size={20} color={Colors.foreground} />
                    </TouchableOpacity>
                    <Text style={cs.screenTitle}>Family Members</Text>
                    <View style={{ width: 40 }} />
                </View>
                <View style={cs.emptyCenter}>
                    <LinearGradient colors={['#f3e8ff', '#eff6ff']} style={cs.emptyIcon}>
                        <Ionicons name="people-outline" size={40} color={Colors.primary} />
                    </LinearGradient>
                    <Text style={cs.emptyTitle}>No Family Group</Text>
                    <Text style={cs.emptySub}>Create a new family group or join one using an invite code.</Text>
                    <TouchableOpacity
                        style={cs.emptyBtn}
                        onPress={() => setShowModal(true)}
                        activeOpacity={0.85}
                    >
                        <LinearGradient colors={Gradients.primaryButton} style={cs.emptyBtnGrad}>
                            <Ionicons name="people" size={18} color="#fff" />
                            <Text style={cs.emptyBtnText}>Get Started</Text>
                        </LinearGradient>
                    </TouchableOpacity>
                </View>
                <JoinCreateModal
                    visible={showModal}
                    onDismiss={() => setShowModal(false)}
                    onCreated={() => { setShowModal(false); fetchFamily(); }}
                    onJoined={() => { setShowModal(false); fetchFamily(); }}
                />
            </View>
        );
    }

    // ── Member list ───────────────────────────────────────────────
    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <View style={cs.screenHeader}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={cs.headerBack}>
                    <Ionicons name="chevron-back" size={20} color={Colors.foreground} />
                </TouchableOpacity>
                <View style={{ flex: 1 }}>
                    <Text style={cs.screenTitle}>Family Members</Text>
                    <Text style={cs.screenSub}>{members.length} members in {family?.name}</Text>
                </View>
            </View>

            <ScrollView
                contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 100 }}
                showsVerticalScrollIndicator={false}
            >
                {/* Members */}
                <Text style={cs.sectionTitle2}>All Members</Text>
                {members.map(m => (
                    <MemberRow
                        key={m.user_id}
                        member={m}
                        health={memberHealth[m.user_id]}
                        onPress={() => setSelectedMemberId(m.user_id)}
                    />
                ))}

                {/* Admin leave/manage */}
                {isAdmin && (
                    <TouchableOpacity
                        style={cs.leaveBtn}
                        onPress={() => Alert.alert(
                            'Leave Family',
                            'Are you sure you want to leave this family group?',
                            [
                                { text: 'Cancel', style: 'cancel' },
                                {
                                    text: 'Leave', style: 'destructive',
                                    onPress: async () => {
                                        try { await familyService.leaveFamily(); fetchFamily(); } catch {
                                            Alert.alert('Error', 'Could not leave. Try again.');
                                        }
                                    },
                                },
                            ]
                        )}
                        activeOpacity={0.8}
                    >
                        <Ionicons name="exit-outline" size={18} color="#ef4444" />
                        <Text style={cs.leaveBtnText}>Leave Family Group</Text>
                    </TouchableOpacity>
                )}
            </ScrollView>
        </View>
    );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const cs = StyleSheet.create({
    // Screen
    screenHeader: {
        flexDirection: 'row', alignItems: 'center', gap: 10,
        paddingHorizontal: 16,
        paddingTop: Platform.OS === 'ios' ? 56 : 28,
        paddingBottom: 12,
    },
    screenTitle: { fontSize: 22, fontWeight: '800', color: Colors.foreground, letterSpacing: -0.3 },
    screenSub: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
    headerBack: {
        width: 38, height: 38, borderRadius: 19,
        backgroundColor: Colors.surface, justifyContent: 'center', alignItems: 'center',
        ...Shadows.sm,
    },

    // Member row
    memberRow: {
        backgroundColor: Colors.surface, borderRadius: Radius['2xl'],
        padding: 14, marginBottom: 10, overflow: 'hidden', ...Shadows.sm,
    },
    accentBar: { width: 4, height: '100%', position: 'absolute', left: 0, top: 0, borderTopLeftRadius: Radius['2xl'], borderBottomLeftRadius: Radius['2xl'] },
    rowAvatar: { width: 46, height: 46, borderRadius: 14, justifyContent: 'center', alignItems: 'center', position: 'relative', marginLeft: 6 },
    statusDotSmall: {
        position: 'absolute', bottom: -2, right: -2,
        width: 12, height: 12, borderRadius: 6, borderWidth: 2,
    },
    rowName: { fontSize: 15, fontWeight: '700', color: Colors.foreground },
    rowRole: { fontSize: 12, color: Colors.textSecondary, textTransform: 'capitalize', marginTop: 2 },
    medBadge: {
        flexDirection: 'row', alignItems: 'center', gap: 3,
        backgroundColor: Colors.primaryBg, paddingHorizontal: 8, paddingVertical: 4, borderRadius: Radius.full,
    },
    medBadgeText: { fontSize: 11, fontWeight: '700', color: Colors.primary },

    // Section title
    sectionTitle: { fontSize: 15, fontWeight: '700', color: Colors.foreground, marginBottom: 12, marginTop: 4 },
    sectionTitle2: { fontSize: 15, fontWeight: '700', color: Colors.foreground, marginBottom: 12, marginTop: 8 },

    // Health chips
    chip: {
        flexDirection: 'row', alignItems: 'center', gap: 4,
        backgroundColor: '#f8fafc', borderRadius: 10,
        paddingHorizontal: 10, paddingVertical: 5,
    },
    chipLabel: { fontSize: 11, color: Colors.textMuted, fontWeight: '500' },
    chipValue: { fontSize: 12, fontWeight: '700', color: Colors.foreground },

    // Back button
    backBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 16, paddingVertical: 12 },
    backBtnInner: {
        width: 30, height: 30, borderRadius: 10,
        backgroundColor: Colors.surface, borderWidth: 1, borderColor: Colors.border,
        justifyContent: 'center', alignItems: 'center',
    },
    backBtnText: { fontSize: 14, fontWeight: '600', color: Colors.textSecondary },

    // Detail hero
    heroWrap: { marginHorizontal: 16, marginBottom: 16, borderRadius: Radius['3xl'], overflow: 'hidden', ...Shadows.premium },
    hero: { padding: 20, overflow: 'hidden', position: 'relative' },
    heroBubble1: { position: 'absolute', top: -30, right: -20, width: 120, height: 120, borderRadius: 60, backgroundColor: 'rgba(255,255,255,0.12)' },
    heroBubble2: { position: 'absolute', bottom: -40, left: -20, width: 90, height: 90, borderRadius: 45, backgroundColor: 'rgba(255,255,255,0.10)' },
    heroRow: { flexDirection: 'row', alignItems: 'center', zIndex: 1 },
    heroAvatarWrap: {
        width: 60, height: 60, borderRadius: 20,
        backgroundColor: 'rgba(255,255,255,0.25)', justifyContent: 'center', alignItems: 'center',
    },
    heroEmoji: { fontSize: 30 },
    heroName: { fontSize: 20, fontWeight: '800', color: '#fff', marginBottom: 2 },
    heroRole: { fontSize: 12, color: 'rgba(255,255,255,0.7)', textTransform: 'capitalize', marginBottom: 6 },
    livePill: { flexDirection: 'row', alignItems: 'center', gap: 5 },
    liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#4ade80' },
    liveText: { fontSize: 11, fontWeight: '600', color: 'rgba(255,255,255,0.75)' },
    removeBtn: {
        width: 38, height: 38, borderRadius: 12,
        backgroundColor: 'rgba(239,68,68,0.35)', justifyContent: 'center', alignItems: 'center',
    },

    // Overall status
    statusBanner: {
        flexDirection: 'row', alignItems: 'center', gap: 8,
        borderRadius: Radius.xl, paddingHorizontal: 14, paddingVertical: 10, marginBottom: 16,
    },
    statusDot: { width: 8, height: 8, borderRadius: 4 },
    statusText: { fontSize: 13, fontWeight: '600' },

    // Health grid
    healthGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 20 },
    statCard: { width: '47%', borderRadius: Radius['2xl'], padding: 14, gap: 6 },
    statIconWrap: {
        width: 32, height: 32, borderRadius: 10,
        backgroundColor: 'rgba(255,255,255,0.7)', justifyContent: 'center', alignItems: 'center',
    },
    statLabel: { fontSize: 11, fontWeight: '600', color: Colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.3 },
    statValue: { fontSize: 18, fontWeight: '800', color: Colors.foreground },

    // Medicine card
    medCard: {
        backgroundColor: Colors.surface, borderRadius: Radius['2xl'],
        padding: 16, ...Shadows.sm, gap: 10,
    },
    medHeader: { flexDirection: 'row', alignItems: 'center', gap: 12 },
    medIconWrap: {
        width: 38, height: 38, borderRadius: 12,
        backgroundColor: Colors.primaryBg, justifyContent: 'center', alignItems: 'center',
    },
    medTitle: { fontSize: 14, fontWeight: '700', color: Colors.foreground },
    medSub: { fontSize: 11, color: Colors.textMuted, marginTop: 1 },
    medCount: { fontSize: 22, fontWeight: '800' },
    medTotal: { fontSize: 16, fontWeight: '400', color: '#cbd5e1' },
    medBarBg: { height: 8, backgroundColor: '#f1f5f9', borderRadius: 4, overflow: 'hidden' },
    medBarFill: { height: '100%', borderRadius: 4 },
    medPct: { fontSize: 11, fontWeight: '600', color: Colors.textMuted },

    // Empty state
    emptyCenter: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 32 },
    emptyIcon: { width: 80, height: 80, borderRadius: 28, justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
    emptyTitle: { fontSize: 22, fontWeight: '800', color: Colors.foreground, textAlign: 'center' },
    emptySub: { fontSize: 14, color: Colors.textSecondary, textAlign: 'center', marginTop: 8, lineHeight: 20 },
    emptyBtn: { marginTop: 24, borderRadius: Radius['2xl'], overflow: 'hidden', ...Shadows.md },
    emptyBtnGrad: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 28, paddingVertical: 14 },
    emptyBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },

    // Leave button
    leaveBtn: {
        flexDirection: 'row', alignItems: 'center', gap: 8,
        justifyContent: 'center', borderRadius: Radius.xl,
        borderWidth: 1.5, borderColor: '#fecaca',
        paddingVertical: 12, marginTop: 16,
    },
    leaveBtnText: { fontSize: 14, fontWeight: '700', color: '#ef4444' },

    // Modal
    modalBackdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.4)' },
    modalSheet: {
        position: 'absolute', bottom: 0, left: 0, right: 0,
        backgroundColor: '#fff',
        borderTopLeftRadius: 28, borderTopRightRadius: 28,
        paddingHorizontal: 20, paddingBottom: Platform.OS === 'ios' ? 44 : 28,
        ...Shadows.premiumLg,
    },
    modalHandle: { width: 40, height: 4, borderRadius: 2, backgroundColor: '#e2e8f0', alignSelf: 'center', marginTop: 12, marginBottom: 20 },
    modalTitle: { fontSize: 22, fontWeight: '800', color: Colors.foreground, marginBottom: 4 },
    modalSub: { fontSize: 14, color: Colors.textSecondary, marginBottom: 20, lineHeight: 20 },
    modalBack: { flexDirection: 'row', alignItems: 'center', gap: 4, marginBottom: 16 },
    modalBackText: { fontSize: 14, fontWeight: '600', color: Colors.textSecondary },
    menuBtn: { borderRadius: Radius['2xl'], overflow: 'hidden', marginBottom: 10 },
    menuBtnGrad: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14 },
    menuBtnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
    menuBtnOutline: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
        borderRadius: Radius['2xl'], borderWidth: 1.5, borderColor: Colors.primaryLight,
        paddingVertical: 14, backgroundColor: Colors.primaryBg,
    },
    menuBtnOutlineText: { color: Colors.primary, fontSize: 15, fontWeight: '700' },
    inputLabel: { fontSize: 13, fontWeight: '700', color: Colors.foreground, marginBottom: 6 },
    input: {
        borderWidth: 1.5, borderColor: Colors.border, borderRadius: Radius.xl,
        paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: Colors.foreground,
        backgroundColor: '#f8fafc', marginBottom: 14,
    },
    codeInput: { textAlign: 'center', fontSize: 22, fontWeight: '800', letterSpacing: 6 },
    errorText: { fontSize: 13, color: '#ef4444', fontWeight: '500', marginBottom: 10, marginTop: -6 },
    submitBtn: { borderRadius: Radius['2xl'], overflow: 'hidden', marginTop: 4 },
    submitBtnGrad: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14 },
    submitBtnText: { color: '#fff', fontSize: 15, fontWeight: '700' },
});
