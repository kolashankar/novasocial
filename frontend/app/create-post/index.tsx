import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/contexts/AuthContext';
import { useImagePicker } from '../../src/hooks/useImagePicker';
import { Button } from '../../src/components/common';
import { COLORS, SPACING } from '../../src/utils/constants';
import { apiService } from '../../src/services/api';

export default function CreatePost() {
  const [selectedMedia, setSelectedMedia] = useState<string[]>([]);
  const [caption, setCaption] = useState('');
  const [isPosting, setIsPosting] = useState(false);
  
  const { user, token } = useAuth();
  const { pickImage, takePhoto, isLoading: imageLoading } = useImagePicker();

  const handleAddMedia = () => {
    if (selectedMedia.length >= 10) {
      Alert.alert('Maximum Limit', 'You can only add up to 10 media items');
      return;
    }

    Alert.alert(
      'Add Media',
      'Choose how you want to add media',
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
      setSelectedMedia(prev => [...prev, image]);
    }
  };

  const handleTakePhoto = async () => {
    const image = await takePhoto();
    if (image) {
      setSelectedMedia(prev => [...prev, image]);
    }
  };

  const handleRemoveMedia = (index: number) => {
    setSelectedMedia(prev => prev.filter((_, i) => i !== index));
  };

  const extractHashtags = (text: string): string[] => {
    const hashtags = text.match(/#\w+/g);
    return hashtags ? hashtags.map(tag => tag.substring(1).toLowerCase()) : [];
  };

  const handlePost = async () => {
    if (selectedMedia.length === 0) {
      Alert.alert('No Media', 'Please add at least one photo or video');
      return;
    }

    if (!token) {
      Alert.alert('Error', 'You must be logged in to create a post');
      return;
    }

    setIsPosting(true);

    try {
      const hashtags = extractHashtags(caption);
      const mediaTypes = selectedMedia.map(() => 'image'); // For now, assume all are images

      await apiService.post('/posts', {
        caption: caption.trim(),
        media: selectedMedia,
        mediaTypes,
        hashtags,
        taggedUsers: [], // Will implement tagging later
      }, token);

      Alert.alert(
        'Success!',
        'Your post has been shared',
        [{ text: 'OK', onPress: () => router.back() }]
      );
    } catch (error) {
      console.error('Create post error:', error);
      Alert.alert('Error', 'Failed to create post. Please try again.');
    } finally {
      setIsPosting(false);
    }
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
          <Text style={styles.headerTitle}>New Post</Text>
          <TouchableOpacity
            style={styles.postButton}
            onPress={handlePost}
            disabled={isPosting || selectedMedia.length === 0}
          >
            <Text style={[
              styles.postButtonText,
              (isPosting || selectedMedia.length === 0) && styles.postButtonDisabled
            ]}>
              {isPosting ? 'Posting...' : 'Share'}
            </Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} keyboardShouldPersistTaps="handled">
          {/* User Info */}
          <View style={styles.userInfo}>
            {user?.profileImage ? (
              <Image source={{ uri: user.profileImage }} style={styles.userAvatar} />
            ) : (
              <View style={styles.defaultAvatar}>
                <Ionicons name="person" size={24} color={COLORS.gray400} />
              </View>
            )}
            <Text style={styles.username}>{user?.username}</Text>
          </View>

          {/* Caption Input */}
          <View style={styles.captionSection}>
            <TextInput
              style={styles.captionInput}
              placeholder="Write a caption..."
              placeholderTextColor={COLORS.textSecondary}
              value={caption}
              onChangeText={setCaption}
              multiline
              numberOfLines={4}
              maxLength={2200}
            />
            <Text style={styles.characterCount}>{caption.length}/2200</Text>
          </View>

          {/* Media Section */}
          <View style={styles.mediaSection}>
            <View style={styles.mediaSectionHeader}>
              <Text style={styles.sectionTitle}>Photos & Videos</Text>
              <TouchableOpacity
                style={styles.addMediaButton}
                onPress={handleAddMedia}
                disabled={imageLoading || selectedMedia.length >= 10}
              >
                <Ionicons 
                  name="add-circle" 
                  size={24} 
                  color={selectedMedia.length >= 10 ? COLORS.gray400 : COLORS.primary} 
                />
              </TouchableOpacity>
            </View>

            {selectedMedia.length === 0 ? (
              <TouchableOpacity
                style={styles.emptyMediaContainer}
                onPress={handleAddMedia}
                disabled={imageLoading}
              >
                <Ionicons 
                  name={imageLoading ? 'sync' : 'camera'} 
                  size={48} 
                  color={COLORS.gray400} 
                />
                <Text style={styles.emptyMediaText}>
                  {imageLoading ? 'Loading...' : 'Tap to add photos or videos'}
                </Text>
              </TouchableOpacity>
            ) : (
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <View style={styles.mediaList}>
                  {selectedMedia.map((media, index) => (
                    <View key={index} style={styles.mediaItem}>
                      <Image source={{ uri: media }} style={styles.mediaPreview} />
                      <TouchableOpacity
                        style={styles.removeMediaButton}
                        onPress={() => handleRemoveMedia(index)}
                      >
                        <Ionicons name="close-circle" size={24} color={COLORS.error} />
                      </TouchableOpacity>
                    </View>
                  ))}
                  {selectedMedia.length < 10 && (
                    <TouchableOpacity
                      style={styles.addMoreButton}
                      onPress={handleAddMedia}
                      disabled={imageLoading}
                    >
                      <Ionicons name="add" size={32} color={COLORS.primary} />
                    </TouchableOpacity>
                  )}
                </View>
              </ScrollView>
            )}
          </View>

          {/* Post Options */}
          <View style={styles.optionsSection}>
            <TouchableOpacity style={styles.optionItem}>
              <Ionicons name="people" size={20} color={COLORS.text} />
              <Text style={styles.optionText}>Tag People</Text>
              <Ionicons name="chevron-forward" size={16} color={COLORS.textSecondary} />
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.optionItem}>
              <Ionicons name="location" size={20} color={COLORS.text} />
              <Text style={styles.optionText}>Add Location</Text>
              <Ionicons name="chevron-forward" size={16} color={COLORS.textSecondary} />
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
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
  },
  userAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
  },
  defaultAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.cardBackground,
    justifyContent: 'center',
    alignItems: 'center',
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginLeft: SPACING.sm,
  },
  captionSection: {
    paddingHorizontal: SPACING.md,
    marginBottom: SPACING.lg,
  },
  captionInput: {
    fontSize: 16,
    color: COLORS.text,
    textAlignVertical: 'top',
    minHeight: 80,
    maxHeight: 120,
  },
  characterCount: {
    fontSize: 12,
    color: COLORS.textSecondary,
    textAlign: 'right',
    marginTop: SPACING.xs,
  },
  mediaSection: {
    paddingHorizontal: SPACING.md,
    marginBottom: SPACING.lg,
  },
  mediaSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  addMediaButton: {
    padding: SPACING.xs,
  },
  emptyMediaContainer: {
    height: 200,
    borderWidth: 2,
    borderColor: COLORS.border,
    borderStyle: 'dashed',
    borderRadius: SPACING.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyMediaText: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginTop: SPACING.sm,
    textAlign: 'center',
  },
  mediaList: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  mediaItem: {
    position: 'relative',
    marginRight: SPACING.sm,
  },
  mediaPreview: {
    width: 80,
    height: 80,
    borderRadius: SPACING.sm,
  },
  removeMediaButton: {
    position: 'absolute',
    top: -8,
    right: -8,
  },
  addMoreButton: {
    width: 80,
    height: 80,
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderStyle: 'dashed',
    borderRadius: SPACING.sm,
    justifyContent: 'center',
    alignItems: 'center',
  },
  optionsSection: {
    paddingHorizontal: SPACING.md,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  optionText: {
    fontSize: 16,
    color: COLORS.text,
    marginLeft: SPACING.sm,
    flex: 1,
  },
});