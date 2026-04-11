/**
 * FamilyLocationScreen — Live family location tracking
 * Native port of DilcareGit's FamilyLocation.tsx using react-native-maps + expo-location
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
    View, Text, StyleSheet, TouchableOpacity, ScrollView,
    Animated, Platform, Linking, Alert, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { locationService } from '../services/api';
import { useFocusEffect } from '@react-navigation/native';

// ─── Try to import optional native deps gracefully ───────────────────────────
let MapView: any = null;
let Marker: any = null;
let PROVIDER_GOOGLE: any = null;
try {
    const maps = require('react-native-maps');
    MapView = maps.default;
    Marker = maps.Marker;
    PROVIDER_GOOGLE = maps.PROVIDER_GOOGLE;
} catch { }

// ─── Types ───────────────────────────────────────────────────────────────────
type Relationship = 'mother' | 'father' | 'guardian' | 'brother' | 'sister' | 'grandpa' | 'grandma' | 'child';

interface MemberLocation {
    id: string;
    name: string;
    relationship: Relationship;
    lat: number;
    lng: number;
    lastSeen: string;
    isLive: boolean;
    batteryLevel?: number;
    speed?: number;
    address?: string;
}

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

function getMeta(rel: string) {
    const key = Object.keys(RELATIONSHIP_META).find(k => rel?.toLowerCase().includes(k));
    return key ? RELATIONSHIP_META[key] : { emoji: '👤', color: Colors.primary, bg: Colors.primaryBg };
}

function normalizeRel(value: string): Relationship {
    const r = value?.toLowerCase() || '';
    if (r.includes('mother')) return 'mother';
    if (r.includes('father')) return 'father';
    if (r.includes('brother')) return 'brother';
    if (r.includes('sister')) return 'sister';
    if (r.includes('grand')) return r.includes('ma') || r.includes('mother') ? 'grandma' : 'grandpa';
    if (r.includes('child') || r.includes('kid')) return 'child';
    return 'guardian';
}

function relativeTime(iso: string) {
    const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (diff < 10) return 'Just now';
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
}

function mapApiItem(item: any): MemberLocation {
    return {
        id: String(item.parent_id || item.user_id || item.id),
        name: item.parent_name || item.name || 'Member',
        relationship: normalizeRel(item.relationship || ''),
        lat: Number(item.latitude || item.lat || 0),
        lng: Number(item.longitude || item.lng || 0),
        lastSeen: item.recorded_at || item.last_seen || new Date().toISOString(),
        isLive: item.is_live ?? false,
        batteryLevel: item.battery_level ?? null,
        speed: Math.max(0, Math.round(item.speed_kmh ?? 0)),
        address: item.address || 'Shared location',
    };
}

// ─── Battery indicator ────────────────────────────────────────────────────────
function BatteryBar({ level }: { level: number | null }) {
    if (level === null || level === undefined) return null;
    const color = level > 30 ? '#22c55e' : '#ef4444';
    return (
        <View style={bs.batteryWrap}>
            <View style={bs.batteryShell}>
                <View style={[bs.batteryFill, { width: `${level}%` as any, backgroundColor: color }]} />
            </View>
            <Text style={[bs.batteryText, { color }]}>{level}%</Text>
        </View>
    );
}

// ─── Member Bottom Sheet ──────────────────────────────────────────────────────
function MemberSheet({ member, onClose }: { member: MemberLocation; onClose: () => void }) {
    const slideAnim = useRef(new Animated.Value(300)).current;
    const meta = getMeta(member.relationship);

    useEffect(() => {
        Animated.spring(slideAnim, {
            toValue: 0, damping: 20, stiffness: 200, useNativeDriver: true,
        }).start();
    }, []);

    const handleClose = () => {
        Animated.timing(slideAnim, {
            toValue: 300, duration: 220, useNativeDriver: true,
        }).start(onClose);
    };

    return (
        <Animated.View style={[bs.sheet, { transform: [{ translateY: slideAnim }] }]}>
            {/* Drag handle */}
            <View style={bs.dragHandle} />

            {/* Header */}
            <View style={bs.sheetHeader}>
                <View style={[bs.sheetAvatar, { backgroundColor: meta.bg }]}>
                    <Text style={bs.sheetAvatarEmoji}>{meta.emoji}</Text>
                </View>
                <View style={{ flex: 1 }}>
                    <Text style={bs.sheetName}>{member.name}</Text>
                    <View style={bs.sheetMeta}>
                        <Text style={bs.sheetRel}>{member.relationship}</Text>
                        <Text style={bs.sheetDot}>·</Text>
                        {member.isLive ? (
                            <View style={bs.livePill}>
                                <View style={bs.liveDot} />
                                <Text style={bs.liveText}>Live</Text>
                            </View>
                        ) : (
                            <Text style={bs.lastSeenText}>{relativeTime(member.lastSeen)}</Text>
                        )}
                    </View>
                </View>
                <TouchableOpacity style={bs.closeBtn} onPress={handleClose}>
                    <Ionicons name="chevron-down" size={20} color={Colors.textMuted} />
                </TouchableOpacity>
            </View>

            {/* Address */}
            <View style={bs.addressRow}>
                <Ionicons name="location" size={16} color="#ef4444" />
                <Text style={bs.addressText} numberOfLines={1}>{member.address}</Text>
                <Ionicons name="time-outline" size={14} color={Colors.textMuted} />
                <Text style={bs.addressTime}>{relativeTime(member.lastSeen)}</Text>
            </View>

            {/* Stats */}
            <View style={bs.statsRow}>
                <View style={[bs.statCard, { backgroundColor: '#fff7ed' }]}>
                    <Ionicons name="navigate" size={16} color="#f97316" />
                    <Text style={bs.statValue}>{member.speed ?? 0} km/h</Text>
                    <Text style={bs.statLabel}>Speed</Text>
                </View>
                <View style={[bs.statCard, { backgroundColor: '#eff6ff' }]}>
                    <Ionicons name="wifi" size={16} color={Colors.primary} />
                    <Text style={bs.statValue}>{member.isLive ? 'Live' : 'Offline'}</Text>
                    <Text style={bs.statLabel}>Status</Text>
                </View>
                <View style={[bs.statCard, { backgroundColor: '#f0fdf4' }]}>
                    <Ionicons name="battery-half" size={16} color="#16a34a" />
                    <Text style={bs.statValue}>{member.batteryLevel != null ? `${member.batteryLevel}%` : 'N/A'}</Text>
                    <Text style={bs.statLabel}>Battery</Text>
                </View>
            </View>

            {/* Actions */}
            <View style={bs.actionsRow}>
                <BatteryBar level={member.batteryLevel ?? null} />
                <TouchableOpacity
                    style={[bs.callBtn, { backgroundColor: meta.color }]}
                    activeOpacity={0.8}
                    onPress={() => Alert.alert('Call', `Call ${member.name}?`, [
                        { text: 'Cancel', style: 'cancel' },
                        { text: 'Call', onPress: () => Linking.openURL(`tel:`) },
                    ])}
                >
                    <Ionicons name="call" size={16} color="#fff" />
                    <Text style={bs.callBtnText}>Call {member.name.split(' ')[0]}</Text>
                </TouchableOpacity>
            </View>
        </Animated.View>
    );
}

// ─── MapView not available fallback ──────────────────────────────────────────
function NoMapFallback({ members, onMemberPress }: { members: MemberLocation[]; onMemberPress: (m: MemberLocation) => void }) {
    return (
        <View style={styles.noMapWrap}>
            <Ionicons name="map-outline" size={56} color={Colors.textMuted} />
            <Text style={styles.noMapTitle}>Map Unavailable</Text>
            <Text style={styles.noMapSub}>Install react-native-maps to see the live map</Text>
            {members.length > 0 && (
                <View style={{ width: '100%', marginTop: 24 }}>
                    {members.map(m => {
                        const meta = getMeta(m.relationship);
                        return (
                            <TouchableOpacity
                                key={m.id}
                                style={styles.listCard}
                                onPress={() => onMemberPress(m)}
                                activeOpacity={0.75}
                            >
                                <View style={[styles.listAvatar, { backgroundColor: meta.bg }]}>
                                    <Text style={{ fontSize: 22 }}>{meta.emoji}</Text>
                                </View>
                                <View style={{ flex: 1 }}>
                                    <Text style={styles.listName}>{m.name}</Text>
                                    <Text style={styles.listMeta}>{m.relationship} · {relativeTime(m.lastSeen)}</Text>
                                </View>
                                {m.isLive && <View style={[styles.liveDotSmall, { backgroundColor: meta.color }]} />}
                            </TouchableOpacity>
                        );
                    })}
                </View>
            )}
        </View>
    );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────
export default function FamilyLocationScreen({ navigation }: any) {
    const [members, setMembers] = useState<MemberLocation[]>([]);
    const [selected, setSelected] = useState<MemberLocation | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [lastRefresh, setLastRefresh] = useState(new Date());
    const mapRef = useRef<any>(null);
    const pulseAnim = useRef(new Animated.Value(1)).current;

    // Pulse animation for live markers
    useEffect(() => {
        Animated.loop(
            Animated.sequence([
                Animated.timing(pulseAnim, { toValue: 1.3, duration: 900, useNativeDriver: true }),
                Animated.timing(pulseAnim, { toValue: 1, duration: 900, useNativeDriver: true }),
            ])
        ).start();
    }, []);

    const fetchLocations = useCallback(async () => {
        try {
            const res = await locationService.getFamilyLiveLocations();
            const payload = Array.isArray(res.data) ? res.data : [];
            setMembers(payload.map(mapApiItem));
            setLastRefresh(new Date());
        } catch {
            // silently keep last known locations
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    useFocusEffect(useCallback(() => {
        fetchLocations();
        const interval = setInterval(fetchLocations, 15000);
        return () => clearInterval(interval);
    }, [fetchLocations]));

    const flyTo = (m: MemberLocation) => {
        setSelected(m);
        mapRef.current?.animateToRegion({
            latitude: m.lat, longitude: m.lng,
            latitudeDelta: 0.01, longitudeDelta: 0.01,
        }, 700);
    };

    const liveCount = members.filter(m => m.isLive).length;
    const hasMap = MapView !== null;

    return (
        <View style={styles.container}>
            {/* ── Header ── */}
            <View style={styles.header}>
                <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
                    <Ionicons name="chevron-back" size={20} color={Colors.foreground} />
                </TouchableOpacity>
                <View style={{ flex: 1 }}>
                    <Text style={styles.headerTitle}>Live Location</Text>
                    <View style={styles.headerMeta}>
                        <Ionicons
                            name={liveCount > 0 ? 'wifi' : 'wifi-outline'}
                            size={12}
                            color={liveCount > 0 ? '#16a34a' : Colors.textMuted}
                        />
                        <Text style={[styles.headerMetaText, { color: liveCount > 0 ? '#16a34a' : Colors.textMuted }]}>
                            {liveCount}/{members.length} live
                        </Text>
                        <Text style={styles.headerDot}>·</Text>
                        <Text style={styles.headerMetaText}>Updated {relativeTime(lastRefresh.toISOString())}</Text>
                    </View>
                </View>
                <TouchableOpacity
                    style={styles.refreshBtn}
                    onPress={async () => { setRefreshing(true); await fetchLocations(); }}
                    disabled={refreshing}
                >
                    {refreshing
                        ? <ActivityIndicator size="small" color={Colors.primary} />
                        : <Ionicons name="refresh" size={19} color={Colors.primary} />
                    }
                </TouchableOpacity>
            </View>

            {/* ── Map or fallback ── */}
            {loading ? (
                <View style={styles.loadingWrap}>
                    <ActivityIndicator size="large" color={Colors.primary} />
                    <Text style={styles.loadingText}>Loading locations…</Text>
                </View>
            ) : hasMap ? (
                <MapView
                    ref={mapRef}
                    style={StyleSheet.absoluteFillObject}
                    provider={PROVIDER_GOOGLE}
                    initialRegion={{
                        latitude: members[0]?.lat || 19.076,
                        longitude: members[0]?.lng || 72.877,
                        latitudeDelta: 0.05,
                        longitudeDelta: 0.05,
                    }}
                    showsUserLocation
                    showsMyLocationButton={false}
                >
                    {members.map(m => {
                        const meta = getMeta(m.relationship);
                        return (
                            <Marker
                                key={m.id}
                                coordinate={{ latitude: m.lat, longitude: m.lng }}
                                onPress={() => flyTo(m)}
                            >
                                <View style={styles.markerWrap}>
                                    {m.isLive && (
                                        <Animated.View style={[
                                            styles.markerPulse,
                                            { borderColor: meta.color, transform: [{ scale: pulseAnim }] },
                                        ]} />
                                    )}
                                    <View style={[styles.markerPin, {
                                        backgroundColor: meta.bg,
                                        borderColor: meta.color,
                                        shadowColor: meta.color,
                                    }]}>
                                        <Text style={styles.markerEmoji}>{meta.emoji}</Text>
                                    </View>
                                    <View style={[styles.markerTip, { backgroundColor: meta.color }]} />
                                </View>
                            </Marker>
                        );
                    })}
                </MapView>
            ) : (
                <NoMapFallback members={members} onMemberPress={flyTo} />
            )}

            {/* ── Empty state overlay ── */}
            {!loading && members.length === 0 && (
                <View style={styles.emptyOverlay}>
                    <View style={styles.emptyCard}>
                        <Ionicons name="location-outline" size={44} color={Colors.textMuted} />
                        <Text style={styles.emptyTitle}>No Live Locations</Text>
                        <Text style={styles.emptySubtitle}>
                            Family members need to enable location sharing from their device settings.
                        </Text>
                    </View>
                </View>
            )}

            {/* ── Avatar strip at bottom ── */}
            {!selected && members.length > 0 && (
                <View style={styles.avatarStrip}>
                    <View style={styles.avatarStripHeader}>
                        <Text style={styles.avatarStripTitle}>{members.length} Family Members</Text>
                        <View style={styles.securedBadge}>
                            <Ionicons name="shield-checkmark" size={12} color="#16a34a" />
                            <Text style={styles.securedText}>Secured</Text>
                        </View>
                    </View>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 14 }}>
                        {members.map(m => {
                            const meta = getMeta(m.relationship);
                            return (
                                <TouchableOpacity
                                    key={m.id}
                                    style={styles.avatarItem}
                                    onPress={() => flyTo(m)}
                                    activeOpacity={0.7}
                                >
                                    <View style={styles.avatarRelWrap}>
                                        <View style={[styles.avatarCircle, {
                                            backgroundColor: meta.bg,
                                            borderColor: meta.color,
                                        }]}>
                                            <Text style={styles.avatarEmoji}>{meta.emoji}</Text>
                                        </View>
                                        {m.isLive && (
                                            <View style={[styles.avatarLiveDot, { backgroundColor: meta.color }]} />
                                        )}
                                    </View>
                                    <Text style={styles.avatarName} numberOfLines={1}>
                                        {m.name.split(' ')[0]}
                                    </Text>
                                </TouchableOpacity>
                            );
                        })}
                    </ScrollView>
                </View>
            )}

            {/* ── Member bottom sheet ── */}
            {selected && (
                <MemberSheet
                    member={selected}
                    onClose={() => setSelected(null)}
                />
            )}
        </View>
    );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f0f4f8' },

    // Header
    header: {
        position: 'absolute', top: 0, left: 0, right: 0, zIndex: 30,
        flexDirection: 'row', alignItems: 'center', gap: 10,
        paddingHorizontal: 16,
        paddingTop: Platform.OS === 'ios' ? 56 : 28,
        paddingBottom: 12,
        backgroundColor: 'rgba(255,255,255,0.92)',
        borderBottomWidth: 0.5,
        borderBottomColor: 'rgba(0,0,0,0.07)',
    },
    backBtn: {
        width: 38, height: 38, borderRadius: 19,
        backgroundColor: Colors.surface, justifyContent: 'center', alignItems: 'center',
        ...Shadows.sm,
    },
    headerTitle: { fontSize: 17, fontWeight: '800', color: Colors.foreground },
    headerMeta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
    headerMetaText: { fontSize: 11, fontWeight: '500', color: Colors.textMuted },
    headerDot: { color: Colors.textMuted, fontSize: 11 },
    refreshBtn: {
        width: 38, height: 38, borderRadius: 19,
        backgroundColor: Colors.primaryBg, justifyContent: 'center', alignItems: 'center',
        ...Shadows.sm,
    },

    // Loading
    loadingWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12 },
    loadingText: { fontSize: 14, color: Colors.textSecondary },

    // Markers
    markerWrap: { alignItems: 'center' },
    markerPulse: {
        position: 'absolute', width: 52, height: 52, borderRadius: 26,
        borderWidth: 2, backgroundColor: 'transparent', top: -6, left: -6,
    },
    markerPin: {
        width: 40, height: 40, borderRadius: 14, borderWidth: 2,
        justifyContent: 'center', alignItems: 'center',
        shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 5,
    },
    markerEmoji: { fontSize: 20 },
    markerTip: { width: 8, height: 8, borderRadius: 2, marginTop: -2, transform: [{ rotate: '45deg' }] },

    // No map fallback
    noMapWrap: {
        flex: 1, alignItems: 'center', paddingHorizontal: 24,
        paddingTop: Platform.OS === 'ios' ? 130 : 100,
    },
    noMapTitle: { fontSize: 20, fontWeight: '800', color: Colors.foreground, marginTop: 16 },
    noMapSub: { fontSize: 13, color: Colors.textSecondary, textAlign: 'center', marginTop: 6 },
    listCard: {
        flexDirection: 'row', alignItems: 'center', gap: 12,
        backgroundColor: Colors.surface, borderRadius: Radius['2xl'],
        padding: 14, marginBottom: 10, ...Shadows.sm,
    },
    listAvatar: { width: 44, height: 44, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },
    listName: { fontSize: 15, fontWeight: '700', color: Colors.foreground },
    listMeta: { fontSize: 12, color: Colors.textSecondary, marginTop: 2, textTransform: 'capitalize' },
    liveDotSmall: { width: 10, height: 10, borderRadius: 5 },

    // Empty overlay
    emptyOverlay: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'center', alignItems: 'center',
        paddingHorizontal: 32, paddingTop: 100,
    },
    emptyCard: {
        backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: Radius['3xl'],
        padding: 28, alignItems: 'center', ...Shadows.premium,
    },
    emptyTitle: { fontSize: 18, fontWeight: '800', color: Colors.foreground, marginTop: 14 },
    emptySubtitle: { fontSize: 13, color: Colors.textSecondary, textAlign: 'center', marginTop: 6, lineHeight: 18 },

    // Avatar strip
    avatarStrip: {
        position: 'absolute', bottom: 0, left: 0, right: 0,
        backgroundColor: 'rgba(255,255,255,0.97)',
        paddingHorizontal: 16, paddingTop: 14,
        paddingBottom: Platform.OS === 'ios' ? 34 : 18,
        borderTopLeftRadius: 24, borderTopRightRadius: 24,
        ...Shadows.premiumLg,
    },
    avatarStripHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
    avatarStripTitle: { fontSize: 12, fontWeight: '700', color: Colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.5 },
    securedBadge: { flexDirection: 'row', alignItems: 'center', gap: 3 },
    securedText: { fontSize: 11, fontWeight: '600', color: '#16a34a' },
    avatarItem: { alignItems: 'center', gap: 6 },
    avatarRelWrap: { position: 'relative' },
    avatarCircle: {
        width: 54, height: 54, borderRadius: 18, borderWidth: 2,
        justifyContent: 'center', alignItems: 'center',
    },
    avatarEmoji: { fontSize: 24 },
    avatarLiveDot: {
        position: 'absolute', top: -3, right: -3,
        width: 14, height: 14, borderRadius: 7, borderWidth: 2, borderColor: '#fff',
    },
    avatarName: { fontSize: 11, fontWeight: '600', color: Colors.foreground, maxWidth: 54 },
});

// ─── Bottom sheet styles ───────────────────────────────────────────────────────
const bs = StyleSheet.create({
    sheet: {
        position: 'absolute', bottom: 0, left: 0, right: 0,
        backgroundColor: '#fff', borderTopLeftRadius: 28, borderTopRightRadius: 28,
        paddingHorizontal: 20, paddingBottom: Platform.OS === 'ios' ? 40 : 24,
        ...Shadows.premiumLg,
    },
    dragHandle: {
        width: 40, height: 4, borderRadius: 2, backgroundColor: '#e2e8f0',
        alignSelf: 'center', marginTop: 12, marginBottom: 16,
    },
    sheetHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 14 },
    sheetAvatar: { width: 52, height: 52, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
    sheetAvatarEmoji: { fontSize: 26 },
    sheetName: { fontSize: 18, fontWeight: '800', color: Colors.foreground },
    sheetMeta: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 3 },
    sheetRel: { fontSize: 13, color: Colors.textSecondary, textTransform: 'capitalize' },
    sheetDot: { color: Colors.textMuted },
    livePill: { flexDirection: 'row', alignItems: 'center', gap: 4 },
    liveDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#16a34a' },
    liveText: { fontSize: 12, fontWeight: '700', color: '#16a34a' },
    lastSeenText: { fontSize: 12, color: Colors.textMuted },
    closeBtn: {
        width: 34, height: 34, borderRadius: 17,
        backgroundColor: '#f1f5f9', justifyContent: 'center', alignItems: 'center',
    },
    addressRow: {
        flexDirection: 'row', alignItems: 'center', gap: 6,
        backgroundColor: '#f8fafc', borderRadius: Radius.xl, padding: 12, marginBottom: 14,
    },
    addressText: { flex: 1, fontSize: 13, color: Colors.foreground },
    addressTime: { fontSize: 11, color: Colors.textMuted },
    statsRow: { flexDirection: 'row', gap: 10, marginBottom: 14 },
    statCard: { flex: 1, borderRadius: Radius.xl, padding: 12, alignItems: 'center', gap: 4 },
    statValue: { fontSize: 15, fontWeight: '800', color: Colors.foreground },
    statLabel: { fontSize: 10, fontWeight: '600', color: Colors.textMuted, textTransform: 'uppercase' },
    actionsRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
    batteryWrap: { flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1 },
    batteryShell: {
        flex: 1, height: 10, borderRadius: 5, backgroundColor: '#f1f5f9',
        overflow: 'hidden', borderWidth: 1, borderColor: '#e2e8f0',
    },
    batteryFill: { height: '100%', borderRadius: 5 },
    batteryText: { fontSize: 12, fontWeight: '700', minWidth: 36 },
    callBtn: {
        flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
        gap: 6, paddingVertical: 12, borderRadius: Radius.xl,
    },
    callBtnText: { color: '#fff', fontWeight: '700', fontSize: 14 },

    // Fallback styles
    premiumLg: {},
});
