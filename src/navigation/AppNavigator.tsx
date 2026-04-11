/**
 * Navigation — Auth stack + Main tab navigator.
 * Mirrors DilcareGit's routing structure.
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { View, StyleSheet, Platform } from 'react-native';
import { Colors } from '../theme/colors';

// Auth screens
import LoginScreen from '../screens/LoginScreen';
import SignupScreen from '../screens/SignupScreen';

// Main screens
import HomeScreen from '../screens/HomeScreen';
import MedicineReminderScreen from '../screens/MedicineReminderScreen';
import StepTrackerScreen from '../screens/StepTrackerScreen';
import BMICalculatorScreen from '../screens/BMICalculatorScreen';
import HealthTrackerScreen from '../screens/HealthTrackerScreen';
import GyaanScreen from '../screens/GyaanScreen';
import SOSEmergencyScreen from '../screens/SOSEmergencyScreen';
import WaterTrackerScreen from '../screens/WaterTrackerScreen';

// Stack-only screens
import ProfileScreen from '../screens/ProfileScreen';
import DoctorScreen from '../screens/DoctorScreen';
import AIAssistantScreen from '../screens/AIAssistantScreen';
import FamilyDashboardScreen from '../screens/FamilyDashboardScreen';
import FamilyLocationScreen from '../screens/FamilyLocationScreen';
import FamilyMembersScreen from '../screens/FamilyMembersScreen';
import NotificationsScreen from '../screens/NotificationsScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// ─── Bottom Tab Navigator ──────────────────────────────────────────
const TAB_ITEMS = [
    { name: 'Home', icon: 'home', component: HomeScreen, color: '#ef4444' },
    { name: 'Medicine', icon: 'medical', component: MedicineReminderScreen, color: '#6366f1' },
    { name: 'Steps', icon: 'footsteps', component: StepTrackerScreen, color: '#f97316' },
    { name: 'Health', icon: 'pulse', component: HealthTrackerScreen, color: '#16a34a' },
    { name: 'Family', icon: 'people', component: FamilyDashboardScreen, color: '#ec4899' },
    { name: 'SOS', icon: 'shield', component: SOSEmergencyScreen, color: '#ef4444' },
];

function MainTabs() {
    return (
        <Tab.Navigator
            screenOptions={({ route }) => {
                const item = TAB_ITEMS.find(t => t.name === route.name);
                return {
                    headerShown: false,
                    tabBarIcon: ({ focused, size }) => {
                        const iconName = (item?.icon || 'home') + (focused ? '' : '-outline');
                        return (
                            <View style={[
                                styles.tabIconWrapper,
                                focused && { backgroundColor: item?.color || Colors.primary, shadowColor: item?.color || Colors.primary },
                            ]}>
                                <Ionicons
                                    name={iconName as any}
                                    size={18}
                                    color={focused ? '#fff' : '#b0b7c3'}
                                />
                            </View>
                        );
                    },
                    tabBarLabel: route.name,
                    tabBarActiveTintColor: item?.color || Colors.primary,
                    tabBarInactiveTintColor: '#b0b7c3',
                    tabBarLabelStyle: { fontSize: 10, fontWeight: '600' as any, marginTop: -2 },
                    tabBarStyle: {
                        height: Platform.OS === 'ios' ? 88 : 70,
                        paddingTop: 8,
                        paddingBottom: Platform.OS === 'ios' ? 28 : 10,
                        backgroundColor: 'rgba(255,255,255,0.95)',
                        borderTopWidth: 0.5,
                        borderTopColor: 'rgba(0,0,0,0.07)',
                        elevation: 20,
                        shadowColor: '#000',
                        shadowOffset: { width: 0, height: -4 },
                        shadowOpacity: 0.08,
                        shadowRadius: 12,
                    },
                };
            }}
        >
            {TAB_ITEMS.map(item => (
                <Tab.Screen key={item.name} name={item.name} component={item.component} />
            ))}
        </Tab.Navigator>
    );
}

// ─── Auth Stack ────────────────────────────────────────────────────
export function AuthStack() {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="Signup" component={SignupScreen} />
        </Stack.Navigator>
    );
}

// ─── Main Stack (Tabs + detail screens) ────────────────────────────
export function MainStack() {
    return (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
            <Stack.Screen name="MainTabs" component={MainTabs} />
            <Stack.Screen name="Profile" component={ProfileScreen} />
            <Stack.Screen name="Water" component={WaterTrackerScreen} />
            <Stack.Screen name="Doctor" component={DoctorScreen} />
            <Stack.Screen name="AI" component={AIAssistantScreen} />
            <Stack.Screen name="BMI" component={BMICalculatorScreen} />
            <Stack.Screen name="Wellness" component={GyaanScreen} />
            <Stack.Screen name="Gyaan" component={GyaanScreen} />
            <Stack.Screen name="FamilyDashboard" component={FamilyDashboardScreen} />
            <Stack.Screen name="FamilyLocation" component={FamilyLocationScreen} />
            <Stack.Screen name="FamilyMembers" component={FamilyMembersScreen} />
            <Stack.Screen name="Notifications" component={NotificationsScreen} />
        </Stack.Navigator>
    );
}

const styles = StyleSheet.create({
    tabIconWrapper: {
        width: 36, height: 36, borderRadius: 12, justifyContent: 'center', alignItems: 'center',
        shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0, shadowRadius: 8,
    },
});
