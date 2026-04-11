/**
 * Gyaan / Wellness — DilcareGit exact: violet-500 #8b5cf6, violet-50 #f5f3ff.
 */
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { gyaanService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';
import { useFocusEffect } from '@react-navigation/native';

const LOCAL_TIPS = [
    { id: 'l1', title: 'Heart-Healthy Diet', content: 'Eat more fruits, vegetables, whole grains, and lean proteins. Limit sodium intake to maintain healthy blood pressure.', category: 'Nutrition', icon: 'nutrition-outline', color: '#16a34a', bg: '#f0fdf4' },
    { id: 'l2', title: 'Stay Active', content: 'Aim for at least 150 minutes of moderate exercise per week to strengthen your heart.', category: 'Exercise', icon: 'bicycle-outline', color: '#f97316', bg: '#fff7ed' },
    { id: 'l3', title: 'Manage Stress', content: 'Practice deep breathing, meditation, or yoga to reduce stress hormones.', category: 'Mental Health', icon: 'leaf-outline', color: '#8b5cf6', bg: '#f5f3ff' },
    { id: 'l4', title: 'Quality Sleep', content: 'Get 7-9 hours of sleep each night. Poor sleep is linked to high blood pressure.', category: 'Sleep', icon: 'moon-outline', color: '#3b82f6', bg: '#eff6ff' },
    { id: 'l5', title: 'Monitor Your Numbers', content: 'Regular checkups for blood pressure, cholesterol, and blood sugar help catch issues early.', category: 'Prevention', icon: 'pulse-outline', color: '#ef4444', bg: '#fef2f2' },
    { id: 'l6', title: 'Hydration Matters', content: 'Drink at least 8 glasses of water daily to keep blood flowing smoothly.', category: 'Hydration', icon: 'water-outline', color: '#0ea5e9', bg: '#f0f9ff' },
];

export default function GyaanScreen() {
    const [tips, setTips] = useState(LOCAL_TIPS);
    const [expanded, setExpanded] = useState<string | null>(null);
    const [activeCategory, setActiveCategory] = useState('All');
    const [refreshing, setRefreshing] = useState(false);

    const fetchTips = async () => {
        try { const { data } = await gyaanService.getTips(); const list = data?.results || data || []; if (Array.isArray(list) && list.length > 0) setTips(list.map((t: any, i: number) => ({ ...t, icon: LOCAL_TIPS[i % LOCAL_TIPS.length].icon, color: LOCAL_TIPS[i % LOCAL_TIPS.length].color, bg: LOCAL_TIPS[i % LOCAL_TIPS.length].bg }))); } catch { }
    };
    useFocusEffect(useCallback(() => { fetchTips(); }, []));

    const categories = ['All', ...new Set(tips.map(t => t.category))];
    const filtered = activeCategory === 'All' ? tips : tips.filter(t => t.category === activeCategory);

    return (
        <View style={{ flex: 1, backgroundColor: Colors.background }}>
            <LinearGradient colors={Gradients.dashboardBg} locations={[0, 0.5, 1]} style={StyleSheet.absoluteFillObject} />
            <ScrollView contentContainerStyle={{ paddingBottom: 100 }}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={async () => { setRefreshing(true); await fetchTips(); setRefreshing(false); }} />}>

                {/* Hero */}
                <View style={{ marginHorizontal: 16, marginTop: 24, marginBottom: 16, borderRadius: Radius['3xl'], overflow: 'hidden', ...Shadows.md }}>
                    <LinearGradient colors={['#8b5cf6', '#6d28d9']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ paddingHorizontal: 24, paddingTop: 28, paddingBottom: 24, overflow: 'hidden', position: 'relative' }}>
                        <View style={{ position: 'absolute', top: -24, right: -24, width: 128, height: 128, borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.10)' }} />
                        <View style={{ flexDirection: 'row', alignItems: 'flex-start', zIndex: 1 }}>
                            <View style={{ flex: 1 }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}><Ionicons name="book-outline" size={16} color="rgba(255,255,255,0.7)" /><Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 12, fontWeight: '600', letterSpacing: 3 }}>DILCARE</Text></View>
                                <Text style={{ fontSize: 24, fontWeight: '700', color: '#fff', marginTop: 2 }}>Wellness Corner</Text>
                                <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 14, marginTop: 4 }}>Expert health tips & insights</Text>
                            </View>
                            <View style={{ width: 56, height: 56, borderRadius: Radius['2xl'], backgroundColor: 'rgba(255,255,255,0.20)', justifyContent: 'center', alignItems: 'center' }}><Ionicons name="book" size={28} color="#fff" /></View>
                        </View>
                    </LinearGradient>
                </View>

                {/* Categories */}
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }} contentContainerStyle={{ paddingHorizontal: 16, gap: 8 }}>
                    {categories.map(c => (
                        <TouchableOpacity key={c} style={[styles.catTab, activeCategory === c && styles.catTabActive]} onPress={() => setActiveCategory(c)}>
                            <Text style={[styles.catTabText, activeCategory === c && styles.catTabTextActive]}>{c}</Text>
                        </TouchableOpacity>
                    ))}
                </ScrollView>

                {/* Tips */}
                {filtered.map(tip => (
                    <TouchableOpacity key={tip.id} style={styles.tipCard} onPress={() => setExpanded(expanded === tip.id ? null : tip.id)} activeOpacity={0.7}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                            <View style={[styles.tipIcon, { backgroundColor: tip.bg }]}><Ionicons name={tip.icon as any} size={22} color={tip.color} /></View>
                            <View style={{ flex: 1 }}>
                                <Text style={styles.tipCategory}>{tip.category}</Text>
                                <Text style={styles.tipTitle}>{tip.title}</Text>
                            </View>
                            <Ionicons name={expanded === tip.id ? 'chevron-up' : 'chevron-down'} size={18} color={Colors.textMuted} />
                        </View>
                        {expanded === tip.id && <Text style={styles.tipContent}>{tip.content}</Text>}
                    </TouchableOpacity>
                ))}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    catTab: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 999, backgroundColor: '#fff', borderWidth: 1, borderColor: Colors.border },
    catTabActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
    catTabText: { fontSize: 13, fontWeight: '600', color: Colors.foreground },
    catTabTextActive: { color: '#fff' },
    tipCard: { marginHorizontal: 16, marginBottom: 12, backgroundColor: '#fff', borderRadius: Radius.lg, padding: 16, ...Shadows.sm },
    tipIcon: { width: 44, height: 44, borderRadius: Radius.lg, justifyContent: 'center', alignItems: 'center' },
    tipCategory: { fontSize: 11, fontWeight: '700', color: Colors.primary, textTransform: 'uppercase', letterSpacing: 1 },
    tipTitle: { fontSize: 15, fontWeight: '600', color: Colors.foreground, marginTop: 2 },
    tipContent: { fontSize: 14, color: Colors.textSecondary, lineHeight: 22, marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: Colors.borderLight },
});
