import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  TextInput,
  Alert,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { Video } from 'expo-av';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  useAnimatedGestureHandler,
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';
import { storiesApi } from '../../services/storiesApi';
import { useAuthContext } from '../../../../contexts/AuthContext';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export const StoryUpload: React.FC = () => {
  const { user } = useAuthContext();
  const [media, setMedia] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<'image' | 'video'>('image');
  const [text, setText] = useState('');
  const [textPosition, setTextPosition] = useState({ x: 0.5, y: 0.3 });
  const [textStyle, setTextStyle] = useState({ color: '#ffffff', fontSize: 24 });
  const [uploading, setUploading] = useState(false);
  const [showTextInput, setShowTextInput] = useState(false);

  // Animated values for text positioning
  const translateX = useSharedValue(screenWidth * textPosition.x);
  const translateY = useSharedValue(screenHeight * textPosition.y);

  const pickMedia = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'We need permission to access your photos and videos');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.All,
      allowsEditing: true,
      aspect: [9, 16],
      quality: 0.8,
      base64: true,
      videoMaxDuration: 30, // 30 seconds max for stories
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      if (asset.base64) {
        const base64Media = `data:${asset.type === 'video' ? 'video/mp4' : 'image/jpeg'};base64,${asset.base64}`;
        setMedia(base64Media);
        setMediaType(asset.type === 'video' ? 'video' : 'image');
      }
    }
  };

  const takePicture = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'We need camera permission to take pictures');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.All,
      allowsEditing: true,
      aspect: [9, 16],
      quality: 0.8,
      base64: true,
      videoMaxDuration: 30,
    });

    if (!result.canceled && result.assets[0]) {
      const asset = result.assets[0];
      if (asset.base64) {
        const base64Media = `data:${asset.type === 'video' ? 'video/mp4' : 'image/jpeg'};base64,${asset.base64}`;
        setMedia(base64Media);
        setMediaType(asset.type === 'video' ? 'video' : 'image');
      }
    }
  };

  const handleTextGesture = useAnimatedGestureHandler({
    onActive: (event) => {
      translateX.value = event.absoluteX;
      translateY.value = event.absoluteY;
    },
    onEnd: () => {
      // Update text position state
      const newPosition = {
        x: translateX.value / screenWidth,
        y: translateY.value / screenHeight,
      };
      setTextPosition(newPosition);
    },
  });

  const animatedTextStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { translateX: translateX.value - 100 },
        { translateY: translateY.value - 50 },
      ],
    };
  });

  const handleUpload = async () => {
    if (!media || !user) {
      Alert.alert('Error', 'Please select media first');
      return;
    }

    setUploading(true);
    try {
      await storiesApi.createStory({
        media,
        mediaType,
        text: text.trim() || undefined,
        textPosition: text.trim() ? textPosition : undefined,
        textStyle: text.trim() ? textStyle : undefined,
        duration: 24, // 24 hours
      });

      Alert.alert('Success', 'Story uploaded successfully!', [
        { text: 'OK', onPress: () => router.back() }
      ]);
    } catch (error) {
      console.error('Failed to upload story:', error);
      Alert.alert('Error', 'Failed to upload story. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const renderMedia = () => {
    if (!media) return null;

    if (mediaType === 'video') {
      return (
        <Video
          source={{ uri: media }}
          style={styles.media}
          shouldPlay
          isLooping
          resizeMode="cover"
        />
      );
    } else {
      return (
        <Image
          source={{ uri: media }}
          style={styles.media}
          resizeMode="cover"
        />
      );
    }
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {media ? (
        <View style={styles.previewContainer}>
          {renderMedia()}
          
          {/* Text Overlay */}
          {text.trim() && (
            <PanGestureHandler onGestureEvent={handleTextGesture}>
              <Animated.View style={[styles.textOverlay, animatedTextStyle]}>
                <Text style={[styles.overlayText, textStyle]}>
                  {text}
                </Text>
              </Animated.View>
            </PanGestureHandler>
          )}

          {/* Controls */}
          <View style={styles.previewControls}>
            <TouchableOpacity style={styles.backButton} onPress={() => setMedia(null)}>
              <Ionicons name="chevron-back" size={24} color="#ffffff" />
            </TouchableOpacity>
            
            <View style={styles.rightControls}>
              <TouchableOpacity 
                style={styles.controlButton} 
                onPress={() => setShowTextInput(true)}
              >
                <Ionicons name="text" size={24} color="#ffffff" />
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={styles.controlButton} 
                onPress={handleUpload}
                disabled={uploading}
              >
                <Ionicons 
                  name={uploading ? 'hourglass' : 'checkmark'} 
                  size={24} 
                  color="#ffffff" 
                />
              </TouchableOpacity>
            </View>
          </View>

          {/* Text Input Modal */}
          {showTextInput && (
            <View style={styles.textInputModal}>
              <TextInput
                style={styles.textInput}
                value={text}
                onChangeText={setText}
                placeholder="Add text to your story..."
                placeholderTextColor="#94a3b8"
                multiline
                maxLength={200}
                autoFocus
              />
              <View style={styles.textInputActions}>
                <TouchableOpacity 
                  style={styles.textActionButton}
                  onPress={() => setShowTextInput(false)}
                >
                  <Text style={styles.textActionText}>Done</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      ) : (
        <View style={styles.uploadContainer}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => router.back()}>
              <Ionicons name="close" size={28} color="#1e293b" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Create Story</Text>
            <View style={styles.headerSpacer} />
          </View>

          <View style={styles.uploadOptions}>
            <TouchableOpacity style={styles.uploadButton} onPress={takePicture}>
              <LinearGradient
                colors={['#667eea', '#764ba2']}
                style={styles.uploadButtonGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="camera" size={32} color="#ffffff" />
              </LinearGradient>
              <Text style={styles.uploadButtonText}>Take Photo/Video</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.uploadButton} onPress={pickMedia}>
              <LinearGradient
                colors={['#667eea', '#764ba2']}
                style={styles.uploadButtonGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name="images" size={32} color="#ffffff" />
              </LinearGradient>
              <Text style={styles.uploadButtonText}>Choose from Library</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  uploadContainer: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingTop: 60,
    backgroundColor: '#ffffff',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
  },
  headerSpacer: {
    width: 28,
  },
  uploadOptions: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  uploadButton: {
    alignItems: 'center',
    marginVertical: 20,
  },
  uploadButtonGradient: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  uploadButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1e293b',
    textAlign: 'center',
  },
  previewContainer: {
    flex: 1,
    backgroundColor: '#000000',
  },
  media: {
    width: screenWidth,
    height: screenHeight,
    position: 'absolute',
  },
  textOverlay: {
    position: 'absolute',
    width: 200,
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  overlayText: {
    textAlign: 'center',
    fontWeight: '600',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
  },
  previewControls: {
    position: 'absolute',
    top: 60,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  backButton: {
    padding: 8,
  },
  rightControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  controlButton: {
    padding: 8,
    marginLeft: 12,
  },
  textInputModal: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    padding: 20,
    paddingBottom: 40,
  },
  textInput: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#1e293b',
    minHeight: 100,
    textAlignVertical: 'top',
  },
  textInputActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 12,
  },
  textActionButton: {
    backgroundColor: '#667eea',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 20,
  },
  textActionText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});