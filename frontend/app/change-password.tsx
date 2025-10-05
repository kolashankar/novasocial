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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuth } from '../src/contexts/AuthContext';
import { COLORS, SPACING } from '../src/utils/constants';

export default function ChangePassword() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const validatePassword = (password) => {
    return password.length >= 8;
  };

  const handleChangePassword = async () => {
    // Validation
    if (!formData.currentPassword || !formData.newPassword || !formData.confirmPassword) {
      Alert.alert('Error', 'All fields are required');
      return;
    }

    if (!validatePassword(formData.newPassword)) {
      Alert.alert('Error', 'New password must be at least 8 characters long');
      return;
    }

    if (formData.newPassword !== formData.confirmPassword) {
      Alert.alert('Error', 'New passwords do not match');
      return;
    }

    if (formData.currentPassword === formData.newPassword) {
      Alert.alert('Error', 'New password must be different from current password');
      return;
    }

    setLoading(true);
    try {
      const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user?.token}`,
        },
        body: JSON.stringify({
          current_password: formData.currentPassword,
          new_password: formData.newPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert(
          'Password Changed',
          'Your password has been successfully changed. You will receive a confirmation email shortly.',
          [{ text: 'OK', onPress: () => router.back() }]
        );
        
        // Reset form
        setFormData({
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        });
      } else {
        Alert.alert('Error', data.detail || 'Failed to change password. Please try again.');
      }
    } catch (error) {
      console.error('Change password error:', error);
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
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
          <Text style={styles.headerTitle}>Change Password</Text>
          <View style={{ width: 24 }} />
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.formContainer}>
            <Text style={styles.description}>
              For your security, please enter your current password and choose a new one.
            </Text>

            {/* Current Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Current Password</Text>
              <View style={styles.passwordInputContainer}>
                <TextInput
                  style={[styles.input, styles.passwordInput]}
                  value={formData.currentPassword}
                  onChangeText={(text) => setFormData(prev => ({ ...prev, currentPassword: text }))}
                  placeholder="Enter your current password"
                  placeholderTextColor={COLORS.textSecondary}
                  secureTextEntry={!showPasswords.current}
                  autoCapitalize="none"
                />
                <TouchableOpacity
                  onPress={() => togglePasswordVisibility('current')}
                  style={styles.eyeIcon}
                >
                  <Ionicons
                    name={showPasswords.current ? 'eye-outline' : 'eye-off-outline'}
                    size={20}
                    color={COLORS.textSecondary}
                  />
                </TouchableOpacity>
              </View>
            </View>

            {/* New Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>New Password</Text>
              <View style={styles.passwordInputContainer}>
                <TextInput
                  style={[styles.input, styles.passwordInput]}
                  value={formData.newPassword}
                  onChangeText={(text) => setFormData(prev => ({ ...prev, newPassword: text }))}
                  placeholder="Enter your new password"
                  placeholderTextColor={COLORS.textSecondary}
                  secureTextEntry={!showPasswords.new}
                  autoCapitalize="none"
                />
                <TouchableOpacity
                  onPress={() => togglePasswordVisibility('new')}
                  style={styles.eyeIcon}
                >
                  <Ionicons
                    name={showPasswords.new ? 'eye-outline' : 'eye-off-outline'}
                    size={20}
                    color={COLORS.textSecondary}
                  />
                </TouchableOpacity>
              </View>
              <Text style={styles.inputHint}>Password must be at least 8 characters long</Text>
            </View>

            {/* Confirm New Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Confirm New Password</Text>
              <View style={styles.passwordInputContainer}>
                <TextInput
                  style={[styles.input, styles.passwordInput]}
                  value={formData.confirmPassword}
                  onChangeText={(text) => setFormData(prev => ({ ...prev, confirmPassword: text }))}
                  placeholder="Confirm your new password"
                  placeholderTextColor={COLORS.textSecondary}
                  secureTextEntry={!showPasswords.confirm}
                  autoCapitalize="none"
                />
                <TouchableOpacity
                  onPress={() => togglePasswordVisibility('confirm')}
                  style={styles.eyeIcon}
                >
                  <Ionicons
                    name={showPasswords.confirm ? 'eye-outline' : 'eye-off-outline'}
                    size={20}
                    color={COLORS.textSecondary}
                  />
                </TouchableOpacity>
              </View>
            </View>

            {/* Password Requirements */}
            <View style={styles.requirementsContainer}>
              <Text style={styles.requirementsTitle}>Password Requirements:</Text>
              <View style={styles.requirement}>
                <Ionicons
                  name={formData.newPassword.length >= 8 ? 'checkmark-circle' : 'ellipse-outline'}
                  size={16}
                  color={formData.newPassword.length >= 8 ? COLORS.success : COLORS.textSecondary}
                />
                <Text style={[
                  styles.requirementText,
                  formData.newPassword.length >= 8 && { color: COLORS.success }
                ]}>
                  At least 8 characters
                </Text>
              </View>
              <View style={styles.requirement}>
                <Ionicons
                  name={formData.newPassword !== formData.currentPassword && formData.newPassword.length > 0 ? 'checkmark-circle' : 'ellipse-outline'}
                  size={16}
                  color={formData.newPassword !== formData.currentPassword && formData.newPassword.length > 0 ? COLORS.success : COLORS.textSecondary}
                />
                <Text style={[
                  styles.requirementText,
                  formData.newPassword !== formData.currentPassword && formData.newPassword.length > 0 && { color: COLORS.success }
                ]}>
                  Different from current password
                </Text>
              </View>
              <View style={styles.requirement}>
                <Ionicons
                  name={formData.newPassword === formData.confirmPassword && formData.confirmPassword.length > 0 ? 'checkmark-circle' : 'ellipse-outline'}
                  size={16}
                  color={formData.newPassword === formData.confirmPassword && formData.confirmPassword.length > 0 ? COLORS.success : COLORS.textSecondary}
                />
                <Text style={[
                  styles.requirementText,
                  formData.newPassword === formData.confirmPassword && formData.confirmPassword.length > 0 && { color: COLORS.success }
                ]}>
                  Passwords match
                </Text>
              </View>
            </View>

            {/* Change Password Button */}
            <TouchableOpacity
              style={[
                styles.changePasswordButton,
                loading && styles.changePasswordButtonDisabled
              ]}
              onPress={handleChangePassword}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.changePasswordButtonText}>Change Password</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.forgotPasswordButton}
              onPress={() => {
                Alert.alert(
                  'Forgot Password?',
                  'You can reset your password from the login screen.',
                  [
                    { text: 'Cancel' },
                    { text: 'Go to Login', onPress: () => router.push('/(auth)/login') }
                  ]
                );
              }}
            >
              <Text style={styles.forgotPasswordText}>Forgot your current password?</Text>
            </TouchableOpacity>
          </View>
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
  formContainer: {
    padding: SPACING.lg,
  },
  description: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 20,
    marginBottom: SPACING.xl,
    textAlign: 'center',
  },
  inputGroup: {
    marginBottom: SPACING.lg,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  passwordInputContainer: {
    position: 'relative',
  },
  input: {
    backgroundColor: COLORS.cardBackground,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: 16,
    color: COLORS.text,
  },
  passwordInput: {
    paddingRight: 50,
  },
  eyeIcon: {
    position: 'absolute',
    right: SPACING.md,
    top: '50%',
    transform: [{ translateY: -10 }],
  },
  inputHint: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  requirementsContainer: {
    backgroundColor: COLORS.cardBackground,
    borderRadius: 8,
    padding: SPACING.md,
    marginBottom: SPACING.xl,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  requirementsTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.text,
    marginBottom: SPACING.sm,
  },
  requirement: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.xs,
  },
  requirementText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginLeft: SPACING.xs,
  },
  changePasswordButton: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: SPACING.md,
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  changePasswordButtonDisabled: {
    opacity: 0.5,
  },
  changePasswordButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  forgotPasswordButton: {
    alignItems: 'center',
    paddingVertical: SPACING.sm,
  },
  forgotPasswordText: {
    fontSize: 14,
    color: COLORS.primary,
    textDecorationLine: 'underline',
  },
});