import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Video, ResizeMode } from 'expo-av';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/contexts/AuthContext';
import { useVideoUpload } from '../../src/hooks/useVideoUpload';
import { Button } from '../../src/components/common';
import { COLORS, SPACING } from '../../src/utils/constants';

export default function CreateReel() {
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [caption, setCaption] = useState('');
  const [isPosting, setIsPosting] = useState(false);
  
  const { user } = useAuth();
  const { pickVideo, recordVideo, isLoading: videoLoading } = useVideoUpload();

  const handleSelectVideo = () => {
    Alert.alert(
      'Select Video',
      'Choose how you want to add your video',
      [
        { text: 'Record Video', onPress: handleRecordVideo },
        { text: 'Choose from Gallery', onPress: handlePickVideo },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const handlePickVideo = async () => {
    const video = await pickVideo();
    if (video) {
      setVideoUri(video);
    }
  };

  const handleRecordVideo = async () => {
    const video = await recordVideo();
    if (video) {
      setVideoUri(video);
    }
  };

  const handleRemoveVideo = () => {
    setVideoUri(null);
  };

  const extractHashtags = (text: string): string[] => {
    const hashtags = text.match(/#\w+/g);
    return hashtags ? hashtags.map(tag => tag.substring(1).toLowerCase()) : [];
  };

  const handlePost = async () => {
    if (!videoUri) {
      Alert.alert('No Video', 'Please select or record a video first');
      return;
    }

    // For now, just show success message
    // TODO: Implement actual video upload to backend
    Alert.alert(
      'Reel Created!',
      'Your reel has been posted successfully',
      [{ text: 'OK', onPress: () => router.back() }]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoid}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Ionicons name="arrow-back" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Create Reel</Text>
          <TouchableOpacity
            style={styles.postButton}
            onPress={handlePost}
            disabled={isPosting || !videoUri}
          >
            <Text style={[
              styles.postButtonText,
              (isPosting || !videoUri) && styles.postButtonDisabled
            ]}>
              {isPosting ? 'Posting...' : 'Share'}
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} keyboardShouldPersistTaps="handled">
          {/* Video Section */}
          <View style={styles.videoSection}>
            {!videoUri ? (
              <TouchableOpacity
                style={styles.selectVideoButton}
                onPress={handleSelectVideo}
                disabled={videoLoading}
              >
                <Ionicons 
                  name={videoLoading ? 'sync' : 'videocam'} 
                  size={48} 
                  color={COLORS.primary} 
                />
                <Text style={styles.selectVideoText}>
                  {videoLoading ? 'Loading...' : 'Select or Record Video'}
                </Text>
                <Text style={styles.selectVideoSubtext}>
                  Maximum 60 seconds
                </Text>
              </TouchableOpacity>
            ) : (
              <View style={styles.videoContainer}>
                <Video
                  source={{ uri: videoUri }}
                  style={styles.videoPreview}
                  resizeMode={ResizeMode.COVER}
                  shouldPlay={false}
                  useNativeControls
                />
                <TouchableOpacity
                  style={styles.removeVideoButton}
                  onPress={handleRemoveVideo}
                >
                  <Ionicons name="close-circle" size={32} color={COLORS.error} />
                </TouchableOpacity>
              </View>
            )}
          </View>

          {/* Caption Section */}
          <View style={styles.captionSection}>
            <Text style={styles.sectionTitle}>Caption</Text>
            <TextInput
              style={styles.captionInput}
              placeholder="Write a caption... Use #hashtags to reach more people"
              placeholderTextColor={COLORS.textSecondary}
              value={caption}
              onChangeText={setCaption}
              multiline
              numberOfLines={4}
              maxLength={2200}
            />
            <Text style={styles.characterCount}>{caption.length}/2200</Text>
          </View>

          {/* Options Section */}
          <View style={styles.optionsSection}>
            <Text style={styles.sectionTitle}>Reel Settings</Text>
            
            <TouchableOpacity style={styles.optionItem}>
              <View style={styles.optionLeft}>
                <Ionicons name="musical-notes" size={20} color={COLORS.text} />
                <Text style={styles.optionText}>Add Music</Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color={COLORS.textSecondary} />
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.optionItem}>
              <View style={styles.optionLeft}>
                <Ionicons name="people" size={20} color={COLORS.text} />
                <Text style={styles.optionText}>Tag People</Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color={COLORS.textSecondary} />
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.optionItem}>
              <View style={styles.optionLeft}>
                <Ionicons name="location" size={20} color={COLORS.text} />
                <Text style={styles.optionText}>Add Location</Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color={COLORS.textSecondary} />
            </TouchableOpacity>

            <View style={styles.optionItem}>
              <View style={styles.optionLeft}>
                <Ionicons name="eye" size={20} color={COLORS.text} />
                <Text style={styles.optionText}>Privacy</Text>
              </View>
              <Text style={styles.optionValue}>Public</Text>
            </View>
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
  keyboardAvoid: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: SPACING.xs,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  postButton: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs,
  },
  postButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  postButtonDisabled: {
    color: COLORS.gray400,
  },
  content: {
    flex: 1,
  },
  videoSection: {
    padding: SPACING.md,
    alignItems: 'center',
  },
  selectVideoButton: {
    width: 200,
    height: 300,
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderStyle: 'dashed',
    borderRadius: SPACING.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  selectVideoText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.sm,
    textAlign: 'center',
  },
  selectVideoSubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
    textAlign: 'center',
  },
  videoContainer: {
    position: 'relative',
  },
  videoPreview: {
    width: 200,
    height: 300,
    borderRadius: SPACING.md,
  },
  removeVideoButton: {
    position: 'absolute',
    top: -10,
    right: -10,
  },
  captionSection: {
    paddingHorizontal: SPACING.md,
    marginBottom: SPACING.lg,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: SPACING.md,
  },
  captionInput: {
    fontSize: 16,
    color: COLORS.text,
    textAlignVertical: 'top',
    minHeight: 80,
    maxHeight: 120,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    paddingVertical: SPACING.sm,
  },
  characterCount: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'right',
    marginTop: SPACING.xs,
  },
  optionsSection: {
    paddingHorizontal: SPACING.md,
  },
  optionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  optionText: {
    fontSize: 16,
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  optionValue: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
});