/**
 * AI Assistant — DilcareGit exact: primary #3b82f6, violet #8b5cf6.
 */
import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { aiService } from '../services/api';
import { Colors, Gradients, Radius, Shadows } from '../theme/colors';

interface Message { id: string; text: string; isUser: boolean; time: string; }

export default function AIAssistantScreen() {
    const [messages, setMessages] = useState<Message[]>([
        { id: '0', text: "Hello! I'm your DilCare health assistant. Ask me anything about your health, medications, or wellness tips!", isUser: false, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const flatListRef = useRef<FlatList>(null);

    const sendMessage = async () => {
        if (!input.trim() || loading) return;
        const userMsg: Message = { id: Date.now().toString(), text: input.trim(), isUser: true, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) };
        setMessages(prev => [...prev, userMsg]); setInput(''); setLoading(true);
        try {
            const { data } = await aiService.sendMessage(userMsg.text);
            const reply = data?.response || data?.message || "I'm here to help with your health questions!";
            setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: reply, isUser: false, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
        } catch {
            setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: "Sorry, I couldn't process that. Please try again.", isUser: false, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }]);
        }
        setLoading(false);
    };

    const renderMessage = ({ item }: { item: Message }) => (
        <View style={[styles.msgRow, item.isUser && styles.msgRowUser]}>
            {!item.isUser && <View style={styles.aiAvatar}><Ionicons name="sparkles" size={14} color={Colors.primary} /></View>}
            <View style={[styles.bubble, item.isUser ? styles.bubbleUser : styles.bubbleAI]}>
                <Text style={[styles.msgText, item.isUser && { color: '#fff' }]}>{item.text}</Text>
                <Text style={[styles.msgTime, item.isUser && { color: 'rgba(255,255,255,0.6)' }]}>{item.time}</Text>
            </View>
        </View>
    );

    return (
        <KeyboardAvoidingView style={{ flex: 1, backgroundColor: Colors.background }} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={90}>
            <View style={styles.header}>
                <View style={styles.headerIcon}><Ionicons name="sparkles" size={20} color={Colors.primary} /></View>
                <View><Text style={styles.headerTitle}>AI Health Assistant</Text><Text style={styles.headerSub}>{loading ? 'Thinking...' : 'Online'}</Text></View>
            </View>
            <FlatList ref={flatListRef} data={messages} renderItem={renderMessage} keyExtractor={i => i.id}
                contentContainerStyle={{ padding: 16, paddingBottom: 8 }} onContentSizeChange={() => flatListRef.current?.scrollToEnd()} />
            <View style={styles.inputBar}>
                <TextInput style={styles.input} value={input} onChangeText={setInput} placeholder="Ask about your health..." placeholderTextColor={Colors.textMuted} multiline returnKeyType="send" onSubmitEditing={sendMessage} />
                <TouchableOpacity onPress={sendMessage} disabled={loading} activeOpacity={0.7}>
                    <LinearGradient colors={loading ? ['#94a3b8', '#94a3b8'] : Gradients.primaryButton as any} style={styles.sendBtn}>
                        <Ionicons name="send" size={18} color="#fff" />
                    </LinearGradient>
                </TouchableOpacity>
            </View>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    header: { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: Colors.borderLight },
    headerIcon: { width: 40, height: 40, borderRadius: Radius.lg, backgroundColor: Colors.primaryBg, justifyContent: 'center', alignItems: 'center' },
    headerTitle: { fontSize: 17, fontWeight: '700', color: Colors.foreground },
    headerSub: { fontSize: 12, color: Colors.textMuted },
    msgRow: { flexDirection: 'row', marginBottom: 12, alignItems: 'flex-end', gap: 8 },
    msgRowUser: { justifyContent: 'flex-end' },
    aiAvatar: { width: 28, height: 28, borderRadius: 14, backgroundColor: Colors.primaryBg, justifyContent: 'center', alignItems: 'center' },
    bubble: { maxWidth: '80%', padding: 14, borderRadius: 18 },
    bubbleUser: { backgroundColor: Colors.primary, borderBottomRightRadius: 4 },
    bubbleAI: { backgroundColor: '#fff', borderBottomLeftRadius: 4, ...Shadows.sm },
    msgText: { fontSize: 15, color: Colors.foreground, lineHeight: 22 },
    msgTime: { fontSize: 10, color: Colors.textMuted, marginTop: 6, textAlign: 'right' },
    inputBar: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingBottom: 24, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: Colors.borderLight, gap: 10 },
    input: { flex: 1, backgroundColor: '#f1f5f9', borderRadius: 20, paddingHorizontal: 16, paddingVertical: 10, fontSize: 15, maxHeight: 100, color: Colors.foreground },
    sendBtn: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
});
