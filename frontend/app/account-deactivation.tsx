import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../src/contexts/AuthContext';
import { COLORS, SPACING } from '../src/utils/constants';

const DEACTIVATION_REASONS = [
  'Taking a break from social media',
  'Privacy concerns',
  'Too much time spent on the app',
  'Found another platform I prefer',
  'Account security issues',
  'Content not relevant to me',
  'Technical issues with the app',
  'Other',
];

export default function AccountDeactivation() {
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [selectedReason, setSelectedReason] = useState('');
  const [customReason, setCustomReason] = useState('');
  const [confirmDeactivation, setConfirmDeactivation] = useState(false);

  const handleDeactivateAccount = async () => {
    if (!selectedReason) {
      Alert.alert('Error', 'Please select a reason for deactivation');
      return;
    }

    if (selectedReason === 'Other' && !customReason.trim()) {
      Alert.alert('Error', 'Please provide a reason for deactivation');
      return;
    }

    if (!confirmDeactivation) {
      Alert.alert('Error', 'Please confirm that you want to deactivate your account');
      return;
    }

    Alert.alert(
      'Confirm Account Deactivation',
      'Are you sure you want to deactivate your account? You can reactivate it anytime by logging in again.',
      [
        { text: 'Cancel' },
        {
          text: 'Deactivate',
          style: 'destructive',
          onPress: confirmDeactivation,
        },
      ]
    );
  };

  const confirmDeactivationProcess = async () => {
    setLoading(true);
    try {
      const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';
      const reason = selectedReason === 'Other' ? customReason : selectedReason;
      
      const response = await fetch(`${API_BASE_URL}/api/auth/deactivate-account`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user?.token}`,
        },
        body: JSON.stringify({
          reason: reason,
          confirm: true,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert(
          'Account Deactivated',
          'Your account has been successfully deactivated. You can reactivate it anytime by logging in again.',
          [
            {
              text: 'OK',
              onPress: () => {
                logout();
                router.push('/');
              },
            },
          ]
        );
      } else {
        Alert.alert('Error', data.detail || 'Failed to deactivate account. Please try again.');
      }
    } catch (error) {
      console.error('Account deactivation error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView 
        style={styles.container} 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Deactivate Account</Text>
          <View style={{ width: 24 }} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.warningContainer}>
            <Ionicons name="warning" size={32} color={COLORS.warning} />
            <Text style={styles.warningTitle}>Account Deactivation</Text>
            <Text style={styles.warningText}>
              When you deactivate your account:
            </Text>
            <View style={styles.warningList}>
              <Text style={styles.warningListItem}>• Your profile will be hidden from other users</Text>
              <Text style={styles.warningListItem}>• Your posts and content will be temporarily hidden</Text>
              <Text style={styles.warningListItem}>• You can reactivate anytime by logging in</Text>
              <Text style={styles.warningListItem}>• Your data will be preserved</Text>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Reason for Deactivation</Text>
            <Text style={styles.sectionDescription}>
              Help us improve by telling us why you're leaving (optional):
            </Text>

            {DEACTIVATION_REASONS.map((reason, index) => (
              <TouchableOpacity
                key={index}
                style={[
                  styles.reasonOption,
                  selectedReason === reason && styles.reasonOptionSelected
                ]}
                onPress={() => setSelectedReason(reason)}
              >
                <View style={[
                  styles.radioButton,
                  selectedReason === reason && styles.radioButtonSelected
                ]}>
                  {selectedReason === reason && (
                    <View style={styles.radioButtonInner} />
                  )}
                </View>
                <Text style={[
                  styles.reasonText,
                  selectedReason === reason && styles.reasonTextSelected
                ]}>
                  {reason}
                </Text>
              </TouchableOpacity>
            ))}

            {selectedReason === 'Other' && (
              <TextInput
                style={styles.customReasonInput}
                value={customReason}
                onChangeText={setCustomReason}
                placeholder="Please specify your reason..."
                placeholderTextColor={COLORS.textSecondary}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />
            )}
          </View>

          <View style={styles.confirmationContainer}>
            <View style={styles.confirmationRow}>
              <Switch
                value={confirmDeactivation}
                onValueChange={setConfirmDeactivation}
                trackColor={{ false: COLORS.border, true: COLORS.primary + '40' }}
                thumbColor={confirmDeactivation ? COLORS.primary : COLORS.textSecondary}
              />
              <Text style={styles.confirmationText}>
                I understand that my account will be deactivated and I can reactivate it by logging in again
              </Text>
            </View>
          </View>

          <TouchableOpacity
            style={[
              styles.deactivateButton,
              (!selectedReason || !confirmDeactivation || loading) && styles.deactivateButtonDisabled
            ]}
            onPress={handleDeactivateAccount}
            disabled={!selectedReason || !confirmDeactivation || loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <Text style={styles.deactivateButtonText}>Deactivate Account</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.cancelButton}
            onPress={() => router.back()}
            disabled={loading}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
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
  warningContainer: {
    margin: SPACING.lg,
    padding: SPACING.lg,
    backgroundColor: COLORS.warning + '10',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.warning + '30',
    alignItems: 'center',
  },
  warningTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.sm,
    marginBottom: SPACING.xs,
  },
  warningText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: SPACING.sm,
  },
  warningList: {
    alignSelf: 'stretch',
  },
  warningListItem: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: SPACING.xs,
    lineHeight: 20,
  },
  section: {
    margin: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  sectionDescription: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: SPACING.md,
    lineHeight: 20,
  },
  reasonOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: 8,
    marginBottom: SPACING.xs,
  },
  reasonOptionSelected: {
    backgroundColor: COLORS.primary + '10',
    borderWidth: 1,
    borderColor: COLORS.primary + '30',
  },
  radioButton: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: COLORS.textSecondary,
    marginRight: SPACING.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioButtonSelected: {
    borderColor: COLORS.primary,
  },
  radioButtonInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.primary,
  },
  reasonText: {
    fontSize: 14,
    color: COLORS.text,
    flex: 1,
  },
  reasonTextSelected: {
    color: COLORS.primary,
    fontWeight: '500',
  },
  customReasonInput: {
    backgroundColor: COLORS.cardBackground,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: SPACING.md,
    fontSize: 14,
    color: COLORS.text,
    marginTop: SPACING.sm,
    minHeight: 80,
  },
  confirmationContainer: {
    margin: SPACING.lg,
    padding: SPACING.md,
    backgroundColor: COLORS.cardBackground,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  confirmationRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  confirmationText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    marginLeft: SPACING.sm,
    lineHeight: 20,
  },
  deactivateButton: {
    backgroundColor: COLORS.danger,
    borderRadius: 8,
    paddingVertical: SPACING.md,
    alignItems: 'center',
    marginHorizontal: SPACING.lg,
    marginBottom: SPACING.md,
  },
  deactivateButtonDisabled: {
    opacity: 0.5,
  },
  deactivateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  cancelButton: {
    alignItems: 'center',
    paddingVertical: SPACING.md,
    marginHorizontal: SPACING.lg,
    marginBottom: SPACING.xl,
  },
  cancelButtonText: {
    fontSize: 16,
    color: COLORS.primary,
    fontWeight: '500',
  },
});