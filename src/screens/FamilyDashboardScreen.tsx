/**
 * FamilyDashboardScreen — Premium family hub
 * Adapted from DilcareGit with native UX enhancements.
 */
import React, { useState, useCallback, useRef } from 'react';
import {
    View, Text, StyleSheet, ScrollView, TouchableOpacity,
    Alert, RefreshControl, Clipboard, Animated, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { familyService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

// ─── Status helpers ──────────────────────────────────────────────────────────
const STATUS_COLORS: Record<string, string> = {
    good: '#16a34a',
    warning: '#f59e0b',
    danger: '#ef4444',
};

const RELATIONSHIP_META: Record<string, { emoji: string; color: string; bg: string }> = {
    mother: { emoji: '👩', color: '#ec4899', bg: '#fce7f3' },
    father: { emoji: '👨', color: '#3b82f6', bg: '#eff6ff' },
    guardian: { emoji: '🧑', color: '#8b5cf6', bg: '#f5f3ff' },
    brother: { emoji: '👦', color: '#f97316', bg: '#fff7ed' },
    sister: { emoji: '👧', color: '#14b8a6', bg: '#f0fdfa' },
    grandpa: { emoji: '👴', color: '#84cc16', bg: '#f7fee7' },
    grandma: { emoji: '👵', color: '#a855f7', bg: '#faf5ff' },
    child: { emoji: '🧒', color: '#f59e0b', bg: '#fffbeb' },
};

function getRelMeta(role?: string) {
    if (!role) return { emoji: '👤', color: Colors.primary, bg: Colors.primaryBg };
    const key = Object.keys(RELATIONSHIP_META).find(k => role.toLowerCase().includes(k));
    return key ? RELATIONSHIP_META[key] : { emoji: '👤', color: Colors.primary, bg: Colors.primaryBg };
}

// ─── MemberCard ───────────────────────────────────────────────────────────────
function MemberCard({ member, health, onPress }: { member: any; health: any; onPress: () => void }) {
    const scaleAnim = useRef(new Animated.Value(1)).current;
    const meta = getRelMeta(member.role || member.nickname);
    const overall = health?.overall_status || 'good';

    const handlePress = () => {
        Animated.sequence([
            Animated.timing(scaleAnim, { toValue: 0.97, duration: 80, useNativeDriver: true }),
            Animated.timing(scaleAnim, { toValue: 1, duration: 80, useNativeDriver: true }),
        ]).start();
        onPress();
    };

    return (
        <Animated.View style={[styles.memberCard, { transform: [{ scale: scaleAnim }] }]}>
            <TouchableOpacity onPress={handlePress} activeOpacity={1}>
                {/* Member header */}
                <View style={styles.memberHeader}>
                    <View style={[styles.memberAvatarWrap, { backgroundColor: meta.bg }]}>
                        <Text style={styles.memberAvatarEmoji}>{meta.emoji}</Text>
                        {/* Live dot */}
                        <View style={[styles.statusDotBorder, { borderColor: meta.bg }]}>
                            <View style={[styles.statusDot, { backgroundColor: STATUS_COLORS[overall] || '#16a34a' }]} />
                        </View>
                    </View>
                    <View style={{ flex: 1 }}>
                        <Text style={styles.memberName} numberOfLines={1}>{member.name || member.email}</Text>
                        <Text style={styles.memberRole}>
                            {member.role}
                            {member.nickname ? ` · ${member.nickname}` : ''}
                        </Text>
                    </View>
                    <View style={[styles.overallBadge, { backgroundColor: STATUS_COLORS[overall] + '22' }]}>
                        <Text style={[styles.overallBadgeText, { color: STATUS_COLORS[overall] || '#16a34a' }]}>
                            {overall === 'good' ? '✓ Good' : overall === 'warning' ? '⚠ Watch' : '⚡ Alert'}
                        </Text>
                    </View>
                </View>

                {/* Health chips */}
                {health ? (
                    <View style={styles.healthGrid}>
                        {health.latest_bp && (
                            <View style={styles.healthChip}>
                                <Ionicons name="heart" size={13} color="#ef4444" />
                                <Text style={styles.chipLabel}>BP</Text>
                                <Text style={styles.chipValue}>{health.latest_bp}</Text>
                            </View>
                        )}
                        {health.latest_sugar && (
                            <View style={styles.healthChip}>
                                <Ionicons name="water" size={13} color="#f97316" />
                                <Text style={styles.chipLabel}>Sugar</Text>
                                <Text style={styles.chipValue}>{health.latest_sugar}</Text>
                            </View>
                        )}
                        {health.latest_heart_rate && (
                            <View style={styles.healthChip}>
                                <Ionicons name="pulse" size={13} color="#8b5cf6" />
                                <Text style={styles.chipLabel}>HR</Text>
                                <Text style={styles.chipValue}>{health.latest_heart_rate} bpm</Text>
                            </View>
                        )}
                        <View style={styles.healthChip}>
                            <Ionicons name="medical" size={13} color="#16a34a" />
                            <Text style={styles.chipLabel}>Meds</Text>
                            <Text style={styles.chipValue}>
                                {health.medicines_today_taken || 0}/{health.medicines_today_total || 0}
                            </Text>
                        </View>
                        <View style={styles.healthChip}>
                            <Ionicons name="water-outline" size={13} color="#0ea5e9" />
                            <Text style={styles.chipLabel}>Water</Text>
                            <Text style={styles.chipValue}>
                                {health.water_glasses_today || 0}/{health.water_goal_today || 8}
                            </Text>
                        </View>
                        {/* Medicine progress bar */}
                        {(health.medicines_today_total || 0) > 0 && (
                            <View style={styles.medBarWrap}>
                                <View style={[styles.medBar, {
                                    width: `${Math.round(((health.medicines_today_taken || 0) / (health.medicines_today_total || 1)) * 100)}%` as any,
                                    backgroundColor: (health.medicines_today_taken || 0) === (health.medicines_today_total || 0) ? '#16a34a' : Colors.primary,
                                }]} />
                            </View>
                        )}
                    </View>
                ) : (
                    <View style={styles.noHealthWrap}>
                        <Text style={styles.noHealthText}>No health data yet</Text>
                    </View>
                )}
            </TouchableOpacity>
        </Animated.View>
    );
}

// ─── Loading skeleton ─────────────────────────────────────────────────────────
function Skeleton() {
    const anim = useRef(new Animated.Value(0.4)).current;
    React.useEffect(() => {
        Animated.loop(
            Animated.sequence([
                Animated.timing(anim, { toValue: 1, duration: 700, useNativeDriver: true }),
                Animated.timing(anim, { toValue: 0.4, duration: 700, useNativeDriver: true }),
            ])
        ).start();
    }, []);
    return (
        <View style={{ paddingHorizontal: 16, paddingTop: 24 }}>
            {[0, 1, 2].map(i => (
                <Animated.View
                    key={i}
                    style={[styles.skeletonCard, { opacity: anim, marginBottom: 12 + i * 4 }]}
                />
            ))}
        </View>
    );
}

// ─── Quick Action Button ──────────────────────────────────────────────────────
function QuickAction({ icon, label, color, onPress }: any) {
    return (
        <TouchableOpacity style={[styles.quickAction, { borderColor: color + '33' }]} onPress={onPress} activeOpacity={0.75}>
            <View style={[styles.quickActionIcon, { backgroundColor: color + '18' }]}>
                <Ionicons name={icon} size={22} color={color} />
            </View>
            <Text style={[styles.quickActionLabel, { color }]}>{label}</Text>
        </TouchableOpacity>
    );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────
export default function FamilyDashboardScreen({ navigation }: any) {
    const [family, setFamily] = useState<any>(null);
    const [memberHealth, setMemberHealth] = useState<Record<number, any>>({});
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const fetchFamily = async () => {
        try {
            const { data } = await familyService.getMyFamily();
            setFamily(data);
            if (data?.members) {
                const healthMap: Record<number, any> = {};
                await Promise.allSettled(
                    data.members.map(async (m: any) => {
                        try {
                            const res = await familyService.getMemberHealth(m.user_id);
                            healthMap[m.user_id] = res.data;
                        } catch { }
                    })
                );
                setMemberHealth(healthMap);
            }
        } catch {
            setFamily(null);
        } finally {
            setLoading(false);
        }
    };

    useFocusEffect(useCallback(() => { fetchFamily(); }, []));

    const onRefresh = async () => {
        setRefreshing(true);
        await fetchFamily();
        setRefreshing(false);
    };

    const copyInviteCode = () => {
        if (family?.invite_code) {
            try { Clipboard.setString(family.invite_code); } catch { }
            Alert.alert('📋 Copied!', `Invite code: ${family.invite_code}\n\nShare this with your family members.`);
        }
    };

    // ── Loading state ──────────────────────────────────────────────
    if (loading) {
        return (
            <View style={{ flex: 1, backgroundColor: Colors.background }}>
                <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
                <View style={styles.screenHeader}>
                    <Text style={styles.screenTitle}>Family</Text>
                </View>
                <Skeleton />
            </View>
        );
    }

    // ── No family state ────────────────────────────────────────────
    if (!family || !family.has_family) {
        return (
            <View style={{ flex: 1, backgroundColor: Colors.background }}>
                <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
                <View style={styles.screenHeader}>
                    <Text style={styles.screenTitle}>Family</Text>
                </View>
                <View style={styles.emptyCenter}>
                    <LinearGradient colors={['#f3e8ff', '#eff6ff']} style={styles.emptyIconWrap}>
                        <Ionicons name="people-outline" size={40} color={Colors.primary} />
                    </LinearGradient>
                    <Text style={styles.emptyTitle}>No Family Group Yet</Text>
                    <Text style={styles.emptySubtitle}>
                        Create a family group or join an existing one to monitor everyone's health together.
                    </Text>
                    <TouchableOpacity
                        style={styles.emptyBtn}
                        onPress={() => navigation.navigate('FamilyMembers')}
                        activeOpacity={0.8}
                    >
                        <LinearGradient colors={Gradients.primaryButton} style={styles.emptyBtnGrad}>
                            <Ionicons name="people" size={18} color="#fff" />
                            <Text style={styles.emptyBtnText}>Get Started</Text>
                        </LinearGradient>
                    </TouchableOpacity>
                </View>
            </View>
        );
    }

    const members = family.members || [];

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />

            {/* Screen Header */}
            <View style={styles.screenHeader}>
                <View>
                    <Text style={styles.screenTitle}>Family</Text>
                    <Text style={styles.screenSubtitle}>{members.length} members · {family.my_role}</Text>
                </View>
                <TouchableOpacity
                    style={styles.headerBtn}
                    onPress={() => navigation.navigate('Notifications')}
                    activeOpacity={0.7}
                >
                    <Ionicons name="notifications-outline" size={22} color={Colors.foreground} />
                </TouchableOpacity>
            </View>

            <ScrollView
                contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 110 }}
                showsVerticalScrollIndicator={false}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.primary} />}
            >
                {/* ── Hero card ── */}
                <View style={styles.heroWrap}>
                    <LinearGradient
                        colors={Gradients.primaryButton}
                        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                        style={styles.hero}
                    >
                        {/* Decorative circles */}
                        <View style={[styles.heroBubble, { top: -30, right: -20, width: 130, height: 130 }]} />
                        <View style={[styles.heroBubble, { bottom: -40, left: -20, width: 100, height: 100 }]} />

                        <View style={styles.heroContent}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                                    <Ionicons name="people-outline" size={12} color="rgba(255,255,255,0.65)" />
                                    <Text style={styles.heroEyebrow}>DILCARE FAMILY</Text>
                                </View>
                                <Text style={styles.heroName}>{family.name}</Text>
                                <Text style={styles.heroMeta}>
                                    {family.member_count} members · You are {family.my_role}
                                </Text>
                            </View>
                            <View style={styles.heroIcon}>
                                <Ionicons name="people" size={28} color="#fff" />
                            </View>
                        </View>

                        {/* Stats row */}
                        <View style={styles.heroStats}>
                            {[
                                { icon: 'people', value: String(family.member_count || 0), label: 'Members' },
                                { icon: 'heart', value: `${members.filter((_: any, i: number) => memberHealth[members[i]?.user_id]?.overall_status === 'good').length}/${members.length}`, label: 'Healthy' },
                                { icon: 'shield-checkmark', value: family.plan || 'Free', label: 'Plan' },
                            ].map((s) => (
                                <View key={s.label} style={styles.heroStatItem}>
                                    <Text style={styles.heroStatValue}>{s.value}</Text>
                                    <Text style={styles.heroStatLabel}>{s.label}</Text>
                                </View>
                            ))}
                        </View>
                    </LinearGradient>
                </View>

                {/* ── Invite code ── */}
                <TouchableOpacity style={styles.inviteCard} onPress={copyInviteCode} activeOpacity={0.75}>
                    <View style={[styles.inviteIconWrap]}>
                        <Ionicons name="key" size={18} color={Colors.primary} />
                    </View>
                    <View style={{ flex: 1 }}>
                        <Text style={styles.inviteHint}>Family Invite Code</Text>
                        <Text style={styles.inviteCode}>{family.invite_code}</Text>
                    </View>
                    <View style={styles.copyBtn}>
                        <Ionicons name="copy-outline" size={16} color={Colors.primary} />
                        <Text style={styles.copyBtnText}>Copy</Text>
                    </View>
                </TouchableOpacity>

                {/* ── Quick actions ── */}
                <View style={styles.quickRow}>
                    <QuickAction
                        icon="location"
                        label="Live Location"
                        color="#ef4444"
                        onPress={() => navigation.navigate('FamilyLocation')}
                    />
                    <QuickAction
                        icon="people"
                        label="Manage Members"
                        color={Colors.primary}
                        onPress={() => navigation.navigate('FamilyMembers')}
                    />
                </View>

                {/* ── Section title ── */}
                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Health Overview</Text>
                    <Text style={styles.sectionMeta}>{members.length} members</Text>
                </View>

                {/* ── Member cards ── */}
                {members.map((member: any) => (
                    <MemberCard
                        key={member.user_id}
                        member={member}
                        health={memberHealth[member.user_id]}
                        onPress={() => navigation.navigate('FamilyMembers', { memberId: member.user_id })}
                    />
                ))}
            </ScrollView>
        </View>
    );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
    // Header
    screenHeader: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
        paddingHorizontal: 20, paddingTop: Platform.OS === 'ios' ? 56 : 28, paddingBottom: 12,
    },
    screenTitle: { fontSize: 28, fontWeight: '800', color: Colors.foreground, letterSpacing: -0.5 },
    screenSubtitle: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
    headerBtn: {
        width: 40, height: 40, borderRadius: 20,
        backgroundColor: Colors.surface, justifyContent: 'center', alignItems: 'center',
        ...Shadows.sm,
    },

    // Hero
    heroWrap: { marginBottom: 14, borderRadius: Radius['3xl'], overflow: 'hidden', ...Shadows.premium },
    hero: { paddingHorizontal: 22, paddingTop: 26, paddingBottom: 20, overflow: 'hidden', position: 'relative' },
    heroBubble: { position: 'absolute', borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.12)' },
    heroContent: { flexDirection: 'row', alignItems: 'flex-start', zIndex: 1, marginBottom: 20 },
    heroEyebrow: { fontSize: 10, fontWeight: '700', color: 'rgba(255,255,255,0.6)', letterSpacing: 2 },
    heroName: { fontSize: 24, fontWeight: '800', color: '#fff', marginTop: 4, letterSpacing: -0.3 },
    heroMeta: { fontSize: 13, color: 'rgba(255,255,255,0.65)', marginTop: 4, textTransform: 'capitalize' },
    heroIcon: {
        width: 56, height: 56, borderRadius: Radius['2xl'],
        backgroundColor: 'rgba(255,255,255,0.22)', justifyContent: 'center', alignItems: 'center',
    },
    heroStats: { flexDirection: 'row', borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.15)', paddingTop: 14 },
    heroStatItem: { flex: 1, alignItems: 'center' },
    heroStatValue: { fontSize: 18, fontWeight: '800', color: '#fff' },
    heroStatLabel: { fontSize: 11, color: 'rgba(255,255,255,0.6)', marginTop: 2, fontWeight: '600' },

    // Invite code
    inviteCard: {
        flexDirection: 'row', alignItems: 'center', gap: 12,
        backgroundColor: Colors.primaryBg, borderRadius: Radius['2xl'],
        padding: 14, marginBottom: 14, borderWidth: 1, borderColor: Colors.primaryLight,
    },
    inviteIconWrap: {
        width: 36, height: 36, borderRadius: 12,
        backgroundColor: Colors.primary + '1A', justifyContent: 'center', alignItems: 'center',
    },
    inviteHint: { fontSize: 11, color: Colors.textMuted, fontWeight: '600', marginBottom: 2 },
    inviteCode: { fontSize: 20, fontWeight: '800', color: Colors.primary, letterSpacing: 4 },
    copyBtn: {
        flexDirection: 'row', alignItems: 'center', gap: 4,
        backgroundColor: Colors.primary + '15', paddingHorizontal: 12, paddingVertical: 6,
        borderRadius: Radius.xl,
    },
    copyBtnText: { fontSize: 12, fontWeight: '700', color: Colors.primary },

    // Quick actions
    quickRow: { flexDirection: 'row', gap: 12, marginBottom: 20 },
    quickAction: {
        flex: 1, borderRadius: Radius['2xl'], borderWidth: 1.5,
        backgroundColor: Colors.surface, padding: 14, alignItems: 'center', gap: 8,
        ...Shadows.sm,
    },
    quickActionIcon: { width: 44, height: 44, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
    quickActionLabel: { fontSize: 13, fontWeight: '700' },

    // Section
    sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
    sectionTitle: { fontSize: 17, fontWeight: '700', color: Colors.foreground },
    sectionMeta: { fontSize: 12, color: Colors.textMuted, fontWeight: '500' },

    // Member card
    memberCard: {
        backgroundColor: Colors.surface, borderRadius: Radius['2xl'],
        padding: 16, marginBottom: 12, ...Shadows.md,
    },
    memberHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 12 },
    memberAvatarWrap: {
        width: 48, height: 48, borderRadius: 16,
        justifyContent: 'center', alignItems: 'center',
        position: 'relative',
    },
    memberAvatarEmoji: { fontSize: 24 },
    statusDotBorder: {
        position: 'absolute', bottom: -2, right: -2,
        width: 14, height: 14, borderRadius: 7, borderWidth: 2, justifyContent: 'center', alignItems: 'center',
    },
    statusDot: { width: 8, height: 8, borderRadius: 4 },
    memberName: { fontSize: 15, fontWeight: '700', color: Colors.foreground, marginBottom: 2 },
    memberRole: { fontSize: 12, color: Colors.textSecondary, textTransform: 'capitalize' },
    overallBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: Radius.full },
    overallBadgeText: { fontSize: 11, fontWeight: '700' },

    // Health chips
    healthGrid: { gap: 6 },
    healthChip: {
        flexDirection: 'row', alignItems: 'center', gap: 4,
        backgroundColor: '#f8fafc', borderRadius: 10,
        paddingHorizontal: 10, paddingVertical: 5,
        alignSelf: 'flex-start',
        marginRight: 6, marginBottom: 2,
        // wrapping is done by flexWrap on parent
        flexWrap: 'wrap',
    },
    chipLabel: { fontSize: 11, color: Colors.textMuted, fontWeight: '500' },
    chipValue: { fontSize: 12, fontWeight: '700', color: Colors.foreground },
    medBarWrap: {
        height: 4, backgroundColor: '#f1f5f9',
        borderRadius: 2, overflow: 'hidden', marginTop: 8,
        width: '100%',
    },
    medBar: { height: '100%', borderRadius: 2 },
    noHealthWrap: { backgroundColor: '#f8fafc', borderRadius: 12, padding: 12, alignItems: 'center' },
    noHealthText: { fontSize: 12, color: Colors.textMuted, fontWeight: '500' },

    // Skeleton
    skeletonCard: {
        height: 120, backgroundColor: '#e2e8f0',
        borderRadius: Radius['2xl'],
    },

    // Empty state
    emptyCenter: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 32 },
    emptyIconWrap: { width: 84, height: 84, borderRadius: 28, justifyContent: 'center', alignItems: 'center', marginBottom: 20 },
    emptyTitle: { fontSize: 22, fontWeight: '800', color: Colors.foreground, textAlign: 'center', letterSpacing: -0.3 },
    emptySubtitle: { fontSize: 14, color: Colors.textSecondary, textAlign: 'center', marginTop: 8, lineHeight: 20 },
    emptyBtn: { marginTop: 24, borderRadius: Radius['2xl'], overflow: 'hidden', ...Shadows.md },
    emptyBtnGrad: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 28, paddingVertical: 14 },
    emptyBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
