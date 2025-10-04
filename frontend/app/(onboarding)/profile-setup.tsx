import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/contexts/AuthContext';
import { Button, Input } from '../../src/components/common';
import { useImagePicker } from '../../src/hooks/useImagePicker';
import { COLORS, SPACING } from '../../src/utils/constants';

export default function ProfileSetup() {
  const [bio, setBio] = useState('');
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const { updateProfile, user } = useAuth();
  const { pickImage, takePhoto, isLoading: imageLoading } = useImagePicker();

  const handleImageSelection = () => {
    Alert.alert(
      'Select Profile Photo',
      'Choose how you want to select your profile photo',
      [
        { text: 'Camera', onPress: handleTakePhoto },
        { text: 'Photo Library', onPress: handlePickImage },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const handlePickImage = async () => {
    const image = await pickImage();
    if (image) {
      setProfileImage(image);
    }
  };

  const handleTakePhoto = async () => {
    const image = await takePhoto();
    if (image) {
      setProfileImage(image);
    }
  };

  const handleSaveProfile = async () => {
    setIsLoading(true);
    
    try {
      const success = await updateProfile({
        profileImage: profileImage || undefined,
        bio: bio.trim() || undefined,
      });
      
      if (success) {
        router.replace('/(tabs)/home');
      } else {
        Alert.alert('Error', 'Failed to update profile. Please try again.');
      }
    } catch (error) {
      Alert.alert('Error', 'An error occurred while updating your profile.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    router.replace('/(tabs)/home');
  };

  return (
    <LinearGradient
      colors={['#1a1a2e', '#16213e', '#0f3460']}
      style={styles.container}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoid}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text style={styles.title}>Complete Your Profile</Text>
            <Text style={styles.subtitle}>
              Add a profile photo and bio to get started
            </Text>
          </View>

          <View style={styles.form}>
            {/* Profile Image Section */}
            <View style={styles.imageSection}>
              <Text style={styles.sectionTitle}>Profile Photo</Text>
              <TouchableOpacity
                style={styles.imageContainer}
                onPress={handleImageSelection}
                disabled={imageLoading}
              >
                {profileImage ? (
                  <Image source={{ uri: profileImage }} style={styles.profileImage} />
                ) : (
                  <View style={styles.placeholderImage}>
                    {imageLoading ? (
                      <Ionicons name="sync" size={40} color={COLORS.gray400} />
                    ) : (
                      <Ionicons name="camera" size={40} color={COLORS.gray400} />
                    )}
                  </View>
                )}
                <View style={styles.cameraIconContainer}>
                  <Ionicons name="camera" size={16} color={COLORS.white} />
                </View>
              </TouchableOpacity>
              <Text style={styles.imageHint}>Tap to add profile photo</Text>
            </View>

            {/* Bio Section */}
            <View style={styles.bioSection}>
              <Input
                label="Bio (Optional)"
                value={bio}
                onChangeText={setBio}
                placeholder="Tell us about yourself..."
                multiline
                numberOfLines={4}
                maxLength={150}
                style={styles.bioInput}
              />
              <Text style={styles.characterCount}>{bio.length}/150</Text>
            </View>

            {/* Buttons */}
            <View style={styles.buttonContainer}>
              <Button
                title={isLoading ? 'Saving...' : 'Complete Setup'}
                onPress={handleSaveProfile}
                disabled={isLoading}
                style={styles.completeButton}
              />
              
              <TouchableOpacity
                style={styles.skipButton}
                onPress={handleSkip}
                disabled={isLoading}
              >
                <Text style={styles.skipButtonText}>Skip for Now</Text>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  keyboardAvoid: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: SPACING.lg,
  },
  header: {
    alignItems: 'center',
    marginBottom: SPACING.xxl,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.white,
    marginBottom: SPACING.sm,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.gray400,
    textAlign: 'center',
    lineHeight: 22,
  },
  form: {
    width: '100%',
  },
  imageSection: {
    alignItems: 'center',
    marginBottom: SPACING.xl,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: SPACING.lg,
  },
  imageContainer: {
    position: 'relative',
    marginBottom: SPACING.sm,
  },
  profileImage: {
    width: 120,
    height: 120,
    borderRadius: 60,
    borderWidth: 3,
    borderColor: COLORS.primary,
  },
  placeholderImage: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: COLORS.gray700,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.gray600,
    borderStyle: 'dashed',
  },
  cameraIconContainer: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: COLORS.primary,
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  imageHint: {
    fontSize: 14,
    color: COLORS.gray400,
    textAlign: 'center',
  },
  bioSection: {
    marginBottom: SPACING.xl,
  },
  bioInput: {
    textAlignVertical: 'top',
    minHeight: 80,
  },
  characterCount: {
    fontSize: 12,
    color: COLORS.gray400,
    textAlign: 'right',
    marginTop: SPACING.xs,
  },
  buttonContainer: {
    width: '100%',
  },
  completeButton: {
    marginBottom: SPACING.lg,
  },
  skipButton: {
    alignItems: 'center',
    paddingVertical: SPACING.md,
  },
  skipButtonText: {
    color: COLORS.gray400,
    fontSize: 16,
    fontWeight: '500',
  },
});