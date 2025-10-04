import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../src/contexts/AuthContext';
import { COLORS, SPACING } from '../src/utils/constants';

export default function Settings() {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState({
    likes: true,
    comments: true,
    follows: true,
    messages: true,
    posts: true,
  });
  const [privacy, setPrivacy] = useState({
    privateAccount: false,
    showActivity: true,
    readReceipts: true,
  });
  const [darkMode, setDarkMode] = useState(false);

  const handleLogout = async () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Sign Out', 
          style: 'destructive',
          onPress: async () => {
            await logout();
          }
        }
      ]
    );
  };

  const handleDeactivateAccount = () => {
    Alert.alert(
      'Deactivate Account',
      'This will temporarily deactivate your account. You can reactivate it by logging in again.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Deactivate', 
          style: 'destructive',
          onPress: () => {
            // Handle account deactivation
            Alert.alert('Feature Coming Soon', 'Account deactivation will be available soon.');
          }
        }
      ]
    );
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This will permanently delete your account and all your data. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: () => {
            Alert.alert('Feature Coming Soon', 'Account deletion will be available soon.');
          }
        }
      ]
    );
  };

  const SettingsSection = ({ title, children }) => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionContent}>
        {children}
      </View>
    </View>
  );

  const SettingsRow = ({ 
    icon, 
    title, 
    subtitle, 
    onPress, 
    rightComponent, 
    showArrow = true,
    destructive = false 
  }) => (
    <TouchableOpacity 
      style={styles.settingsRow} 
      onPress={onPress}
      disabled={!onPress}
    >
      <View style={styles.settingsRowLeft}>
        {icon && (
          <Ionicons 
            name={icon} 
            size={20} 
            color={destructive ? COLORS.error : COLORS.textSecondary} 
            style={styles.settingsIcon} 
          />
        )}
        <View style={styles.settingsTextContainer}>
          <Text style={[styles.settingsTitle, destructive && { color: COLORS.error }]}>
            {title}
          </Text>
          {subtitle && (
            <Text style={styles.settingsSubtitle}>{subtitle}</Text>
          )}
        </View>
      </View>
      <View style={styles.settingsRowRight}>
        {rightComponent}
        {showArrow && onPress && (
          <Ionicons 
            name="chevron-forward" 
            size={20} 
            color={COLORS.textSecondary} 
          />
        )}
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Settings</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Account Settings */}
        <SettingsSection title="Account">
          <SettingsRow
            icon="person-outline"
            title="Edit Profile"
            subtitle="Change your profile information"
            onPress={() => router.push('/edit-profile')}
          />
          <SettingsRow
            icon="key-outline"
            title="Change Password"
            subtitle="Update your account password"
            onPress={() => router.push('/change-password')}
          />
          <SettingsRow
            icon="shield-outline"
            title="Privacy and Security"
            subtitle="Control who can see your content"
            onPress={() => {/* Navigate to privacy settings */}}
          />
        </SettingsSection>

        {/* Notifications */}
        <SettingsSection title="Notifications">
          <SettingsRow
            icon="heart-outline"
            title="Likes"
            subtitle="Get notified when someone likes your posts"
            rightComponent={
              <Switch
                value={notifications.likes}
                onValueChange={(value) => 
                  setNotifications(prev => ({ ...prev, likes: value }))
                }
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
          <SettingsRow
            icon="chatbubble-outline"
            title="Comments"
            subtitle="Get notified when someone comments on your posts"
            rightComponent={
              <Switch
                value={notifications.comments}
                onValueChange={(value) => 
                  setNotifications(prev => ({ ...prev, comments: value }))
                }
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
          <SettingsRow
            icon="person-add-outline"
            title="Follows"
            subtitle="Get notified when someone follows you"
            rightComponent={
              <Switch
                value={notifications.follows}
                onValueChange={(value) => 
                  setNotifications(prev => ({ ...prev, follows: value }))
                }
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
          <SettingsRow
            icon="mail-outline"
            title="Messages"
            subtitle="Get notified for new messages"
            rightComponent={
              <Switch
                value={notifications.messages}
                onValueChange={(value) => 
                  setNotifications(prev => ({ ...prev, messages: value }))
                }
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
        </SettingsSection>

        {/* Privacy */}
        <SettingsSection title="Privacy">
          <SettingsRow
            icon="lock-closed-outline"
            title="Private Account"
            subtitle="Only approved followers can see your posts"
            rightComponent={
              <Switch
                value={privacy.privateAccount}
                onValueChange={(value) => 
                  setPrivacy(prev => ({ ...prev, privateAccount: value }))
                }
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
          <SettingsRow
            icon="eye-outline"
            title="Activity Status"
            subtitle="Show when you were last active"
            rightComponent={
              <Switch
                value={privacy.showActivity}
                onValueChange={(value) => 
                  setPrivacy(prev => ({ ...prev, showActivity: value }))
                }
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
          <SettingsRow
            icon="checkmark-done-outline"
            title="Read Receipts"
            subtitle="Let people know when you've read their messages"
            rightComponent={
              <Switch
                value={privacy.readReceipts}
                onValueChange={(value) => 
                  setPrivacy(prev => ({ ...prev, readReceipts: value }))
                }
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
        </SettingsSection>

        {/* Appearance */}
        <SettingsSection title="Appearance">
          <SettingsRow
            icon="moon-outline"
            title="Dark Mode"
            subtitle="Switch to dark theme"
            rightComponent={
              <Switch
                value={darkMode}
                onValueChange={setDarkMode}
                trackColor={{ false: COLORS.gray300, true: COLORS.primary }}
                thumbColor={COLORS.background}
              />
            }
            showArrow={false}
          />
        </SettingsSection>

        {/* Support */}
        <SettingsSection title="Support">
          <SettingsRow
            icon="help-circle-outline"
            title="Help Center"
            subtitle="Get help with using NovaSocial"
            onPress={() => Alert.alert('Coming Soon', 'Help center will be available soon.')}
          />
          <SettingsRow
            icon="bug-outline"
            title="Report a Problem"
            subtitle="Let us know if something isn't working"
            onPress={() => Alert.alert('Coming Soon', 'Problem reporting will be available soon.')}
          />
          <SettingsRow
            icon="information-circle-outline"
            title="About"
            subtitle="App version and information"
            onPress={() => Alert.alert('NovaSocial', 'Version 1.0.0\nBuilt with React Native')}
          />
        </SettingsSection>

        {/* Account Actions */}
        <SettingsSection title="Account Actions">
          <SettingsRow
            icon="log-out-outline"
            title="Sign Out"
            onPress={handleLogout}
            destructive={true}
          />
          <SettingsRow
            icon="pause-circle-outline"
            title="Deactivate Account"
            subtitle="Temporarily disable your account"
            onPress={handleDeactivateAccount}
            destructive={true}
          />
          <SettingsRow
            icon="trash-outline"
            title="Delete Account"
            subtitle="Permanently delete your account and data"
            onPress={handleDeleteAccount}
            destructive={true}
          />
        </SettingsSection>

        <View style={{ height: SPACING.xl }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  content: {
    flex: 1,
  },
  section: {
    marginTop: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
    paddingHorizontal: SPACING.lg,
    paddingBottom: SPACING.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionContent: {
    backgroundColor: COLORS.cardBackground,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: COLORS.border,
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  settingsRowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingsIcon: {
    marginRight: SPACING.md,
  },
  settingsTextContainer: {
    flex: 1,
  },
  settingsTitle: {
    fontSize: 16,
    color: COLORS.text,
    marginBottom: 2,
  },
  settingsSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  settingsRowRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});