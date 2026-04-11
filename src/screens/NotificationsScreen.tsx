/**
 * Notifications — DilcareGit exact colors.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { communityService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

export default function NotificationsScreen() {
    const [refreshing, setRefreshing] = useState(false);
    const fetch = async () => { try { await communityService.getLeaderboard(); } catch { } };
    useFocusEffect(useCallback(() => { fetch(); }, []));

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingBottom: 100, flexGrow: 1 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await fetch(); setRefreshing(false); }} />}>

                {/* Hero */}
                <View style={{ marginHorizontal: 16, marginTop: 24, marginBottom: 16, borderRadius: Radius['3xl'], overflow: 'hidden', ...Shadows.md }}>
                    <LinearGradient colors={['#f97316', '#ea580c']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ paddingHorizontal: 24, paddingTop: 28, paddingBottom: 24, overflow: 'hidden', position: 'relative' }}>
                        <View style={{ position: 'absolute', top: -24, right: -24, width: 128, height: 128, borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.10)' }} />
                        <View style={{ flexDirection: 'row', alignItems: 'flex-start', zIndex: 1 }}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}><Ionicons name="notifications-outline" size={16} color="rgba(255,255,255,0.7)" /><Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 12, fontWeight: '600', letterSpacing: 3 }}>DILCARE</Text></View>
                                <Text style={{ fontSize: 24, fontWeight: '700', color: '#fff', marginTop: 2 }}>Notifications</Text>
                                <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 14, marginTop: 4 }}>Stay updated</Text>
                            </View>
                            <View style={{ width: 56, height: 56, borderRadius: Radius['2xl'], backgroundColor: 'rgba(255,255,255,0.20)', justifyContent: 'center', alignItems: 'center' }}><Ionicons name="notifications" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                <View style={styles.emptyState}>
                    <Ionicons name="notifications-outline" size={56} color={Colors.textMuted} />
                    <Text style={styles.emptyTitle}>All caught up!</Text>
                    <Text style={styles.emptyDesc}>No new notifications right now</Text>
                </View>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 60 },
    emptyTitle: { fontSize: 18, fontWeight: '600', color: Colors.foreground, marginTop: 16 },
    emptyDesc: { fontSize: 14, color: Colors.textMuted, marginTop: 4 },
});
