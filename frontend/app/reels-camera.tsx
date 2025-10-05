import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Dimensions,
  ActivityIndicator,
  Modal,
  ScrollView,
  Animated,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../src/utils/constants';
import { useAuth } from '../src/contexts/AuthContext';
import Constants from 'expo-constants';

// Conditionally import VisionCamera only for mobile platforms
let Camera: any = null;
let useCameraDevices: any = null;
let useCameraPermission: any = null;

if (Platform.OS !== 'web') {
  try {
    const VisionCamera = require('react-native-vision-camera');
    Camera = VisionCamera.Camera;
    useCameraDevices = VisionCamera.useCameraDevices;
    useCameraPermission = VisionCamera.useCameraPermission;
  } catch (error) {
    console.warn('VisionCamera not available on this platform');
  }
}

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface VideoFilter {
  id: string;
  name: string;
  type: string;
  parameters: Record<string, number>;
  presetName?: string;
  icon: string;
  displayName: string;
}

interface AREffect {
  id: string;
  name: string;
  type: string;
  assetUrl?: string;
  parameters: Record<string, any>;
  icon: string;
  displayName: string;
}

const PRESET_FILTERS: VideoFilter[] = [
  {
    id: 'vintage',
    name: 'vintage',
    type: 'effect',
    parameters: { sepia: 0.7, contrast: 1.2, vignette: 0.4, noise: 0.1 },
    presetName: 'vintage',
    icon: 'camera-outline',
    displayName: 'Vintage'
  },
  {
    id: 'dramatic',
    name: 'dramatic', 
    type: 'adjustment',
    parameters: { contrast: 1.5, brightness: 0.9, saturation: 1.3, shadows: 0.7 },
    presetName: 'dramatic',
    icon: 'contrast-outline',
    displayName: 'Dramatic'
  },
  {
    id: 'soft_glow',
    name: 'soft_glow',
    type: 'effect', 
    parameters: { blur: 0.3, brightness: 1.1, glow_intensity: 0.6 },
    presetName: 'soft_glow',
    icon: 'sunny-outline',
    displayName: 'Soft Glow'
  },
  {
    id: 'black_white',
    name: 'black_white',
    type: 'adjustment',
    parameters: { saturation: 0.0, contrast: 1.2 },
    presetName: 'black_white',
    icon: 'contrast-outline',
    displayName: 'B&W'
  }
];

const PRESET_AR_EFFECTS: AREffect[] = [
  {
    id: 'heart_eyes',
    name: 'heart_eyes',
    type: 'face_tracking',
    assetUrl: '/ar_assets/heart_eyes.png',
    parameters: { facial_landmark: 'eyes', tracking_confidence: 0.8 },
    icon: 'heart-outline',
    displayName: 'Heart Eyes'
  },
  {
    id: 'dog_ears',
    name: 'dog_ears',
    type: 'face_tracking',
    assetUrl: '/ar_assets/dog_ears.png', 
    parameters: { facial_landmark: 'head_top', tracking_confidence: 0.7 },
    icon: 'paw-outline',
    displayName: 'Dog Ears'
  },
  {
    id: 'sparkles',
    name: 'sparkles',
    type: 'animation',
    assetUrl: '/ar_assets/sparkles.json',
    parameters: { animation_duration: 2.0, particle_count: 50 },
    icon: 'sparkles-outline',
    displayName: 'Sparkles'
  }
];

export default function ReelsCamera() {
  const router = useRouter();
  const { user } = useAuth();
  
  // Handle web platform gracefully
  const [hasPermission, setHasPermission] = useState(Platform.OS === 'web' ? false : false);
  const [devices, setDevices] = useState<any>(Platform.OS === 'web' ? null : null);
  const camera = useRef<any>(null);

  // Initialize camera hooks only on mobile platforms
  let cameraHooks: any = { hasPermission: false, requestPermission: () => {} };
  let cameraDevices: any = null;

  if (Platform.OS !== 'web' && useCameraPermission && useCameraDevices) {
    cameraHooks = useCameraPermission();
    cameraDevices = useCameraDevices();
  }
  
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [selectedFilters, setSelectedFilters] = useState<VideoFilter[]>([]);
  const [selectedAREffects, setSelectedAREffects] = useState<AREffect[]>([]);
  const [showFiltersModal, setShowFiltersModal] = useState(false);
  const [showARModal, setShowARModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cameraType, setCameraType] = useState<'back' | 'front'>('back');
  
  const recordingTimer = useRef<NodeJS.Timeout>();
  const animatedValue = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (Platform.OS !== 'web') {
      if (!cameraHooks.hasPermission) {
        cameraHooks.requestPermission();
      }
      setHasPermission(cameraHooks.hasPermission);
      setDevices(cameraDevices);
    }
  }, [Platform.OS]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
      
      // Animate recording button
      Animated.loop(
        Animated.sequence([
          Animated.timing(animatedValue, {
            toValue: 1.2,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(animatedValue, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording, animatedValue]);

  const device = Platform.OS === 'web' ? null : (devices && (cameraType === 'back' ? devices.back : devices.front));

  // Handle web platform - show message instead of camera
  if (Platform.OS === 'web') {
    return (
      <View style={styles.container}>
        <View style={styles.webMessage}>
          <Ionicons name="camera-outline" size={64} color={COLORS.primary} />
          <Text style={styles.webMessageTitle}>Camera Not Available</Text>
          <Text style={styles.webMessageText}>
            Camera functionality is only available on mobile devices. 
            Please use the Expo Go app on your phone to test this feature.
          </Text>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Text style={styles.backButtonText}>Go Back</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  if (!hasPermission) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>Camera permission required</Text>
        <TouchableOpacity style={styles.permissionButton} onPress={() => cameraHooks.requestPermission()}>
          <Text style={styles.permissionButtonText}>Grant Permission</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!device) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading Camera...</Text>
      </View>
    );
  }

  const startRecording = async () => {
    if (!camera.current) return;
    
    try {
      setIsRecording(true);
      setRecordingDuration(0);
      
      await camera.current.startRecording({
        flash: 'off',
        onRecordingFinished: (video) => {
          console.log('Recording finished:', video.path);
          setIsRecording(false);
          handleVideoRecorded(video.path);
        },
        onRecordingError: (error) => {
          console.error('Recording error:', error);
          setIsRecording(false);
          Alert.alert('Recording Error', 'Failed to record video');
        },
      });
      
      // Auto-stop after 60 seconds
      recordingTimer.current = setTimeout(() => {
        stopRecording();
      }, 60000);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      setIsRecording(false);
      Alert.alert('Error', 'Failed to start recording');
    }
  };

  const stopRecording = async () => {
    if (!camera.current || !isRecording) return;
    
    try {
      await camera.current.stopRecording();
      if (recordingTimer.current) {
        clearTimeout(recordingTimer.current);
      }
    } catch (error) {
      console.error('Error stopping recording:', error);
    }
  };

  const handleVideoRecorded = async (videoPath: string) => {
    setIsProcessing(true);
    
    try {
      // Convert video to base64 (simplified for demo)
      // In production, use proper video processing library
      const videoData = `data:video/mp4;base64,${videoPath}`;
      
      // Upload to backend with filters and AR effects
      const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || 'https://socialcrypt-app.preview.emergentagent.com';
      
      const response = await fetch(`${backendUrl}/api/reels/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user?.token}`,
        },
        body: JSON.stringify({
          videoData,
          caption: '',
          hashtags: [],
          tags: [],
          filters: selectedFilters,
          arEffects: selectedAREffects,
          privacy: 'public'
        }),
      });
      
      const result = await response.json();
      
      if (result.success) {
        Alert.alert(
          'Success',
          'Your reel is being processed! You can check the progress in your profile.',
          [
            { text: 'OK', onPress: () => router.back() }
          ]
        );
      } else {
        throw new Error(result.message || 'Upload failed');
      }
      
    } catch (error) {
      console.error('Upload error:', error);
      Alert.alert('Upload Failed', 'Failed to upload video. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleFilter = (filter: VideoFilter) => {
    setSelectedFilters(prev => {
      const exists = prev.find(f => f.id === filter.id);
      if (exists) {
        return prev.filter(f => f.id !== filter.id);
      } else {
        return [...prev, filter];
      }
    });
  };

  const toggleAREffect = (effect: AREffect) => {
    setSelectedAREffects(prev => {
      const exists = prev.find(e => e.id === effect.id);
      if (exists) {
        return prev.filter(e => e.id !== effect.id);
      } else {
        return [...prev, effect];
      }
    });
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <View style={styles.container}>
      {Camera && (
        <Camera
          ref={camera}
          style={styles.camera}
          device={device}
          isActive={true}
          video={true}
          audio={true}
        />
      )}
      
      {/* Header Controls */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerButton} onPress={() => router.back()}>
          <Ionicons name="close" size={24} color="white" />
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.headerButton} 
          onPress={() => setCameraType(prev => prev === 'back' ? 'front' : 'back')}
        >
          <Ionicons name="camera-reverse" size={24} color="white" />
        </TouchableOpacity>
      </View>

      {/* Recording Duration */}
      {isRecording && (
        <View style={styles.recordingInfo}>
          <View style={styles.recordingDot} />
          <Text style={styles.recordingTime}>{formatDuration(recordingDuration)}</Text>
        </View>
      )}

      {/* Side Controls */}
      <View style={styles.sideControls}>
        <TouchableOpacity 
          style={[styles.sideButton, selectedFilters.length > 0 && styles.activeButton]}
          onPress={() => setShowFiltersModal(true)}
        >
          <Ionicons name="color-filter" size={24} color="white" />
          <Text style={styles.sideButtonText}>Filters</Text>
          {selectedFilters.length > 0 && (
            <View style={styles.badgeContainer}>
              <Text style={styles.badgeText}>{selectedFilters.length}</Text>
            </View>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.sideButton, selectedAREffects.length > 0 && styles.activeButton]}
          onPress={() => setShowARModal(true)}
        >
          <Ionicons name="happy" size={24} color="white" />
          <Text style={styles.sideButtonText}>AR</Text>
          {selectedAREffects.length > 0 && (
            <View style={styles.badgeContainer}>
              <Text style={styles.badgeText}>{selectedAREffects.length}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* Bottom Controls */}
      <View style={styles.bottomControls}>
        <Animated.View style={[styles.recordButtonContainer, { transform: [{ scale: animatedValue }] }]}>
          <TouchableOpacity
            style={[styles.recordButton, isRecording && styles.recordingButton]}
            onPress={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <ActivityIndicator size="large" color="white" />
            ) : (
              <View style={[styles.recordButtonInner, isRecording && styles.recordingInner]} />
            )}
          </TouchableOpacity>
        </Animated.View>
      </View>

      {/* Filters Modal */}
      <Modal visible={showFiltersModal} animationType="slide" transparent>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Video Filters</Text>
              <TouchableOpacity onPress={() => setShowFiltersModal(false)}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.modalScroll}>
              {PRESET_FILTERS.map((filter) => (
                <TouchableOpacity
                  key={filter.id}
                  style={[
                    styles.filterItem,
                    selectedFilters.find(f => f.id === filter.id) && styles.selectedFilterItem
                  ]}
                  onPress={() => toggleFilter(filter)}
                >
                  <Ionicons name={filter.icon as any} size={24} color={COLORS.primary} />
                  <Text style={styles.filterName}>{filter.displayName}</Text>
                  {selectedFilters.find(f => f.id === filter.id) && (
                    <Ionicons name="checkmark" size={20} color={COLORS.primary} />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* AR Effects Modal */}
      <Modal visible={showARModal} animationType="slide" transparent>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>AR Effects</Text>
              <TouchableOpacity onPress={() => setShowARModal(false)}>
                <Ionicons name="close" size={24} color={COLORS.text} />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.modalScroll}>
              {PRESET_AR_EFFECTS.map((effect) => (
                <TouchableOpacity
                  key={effect.id}
                  style={[
                    styles.filterItem,
                    selectedAREffects.find(e => e.id === effect.id) && styles.selectedFilterItem
                  ]}
                  onPress={() => toggleAREffect(effect)}
                >
                  <Ionicons name={effect.icon as any} size={24} color={COLORS.primary} />
                  <Text style={styles.filterName}>{effect.displayName}</Text>
                  {selectedAREffects.find(e => e.id === effect.id) && (
                    <Ionicons name="checkmark" size={20} color={COLORS.primary} />
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'black',
  },
  camera: {
    flex: 1,
  },
  header: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    zIndex: 1,
  },
  headerButton: {
    padding: 10,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 20,
  },
  recordingInfo: {
    position: 'absolute',
    top: 100,
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,0,0,0.8)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    zIndex: 1,
  },
  recordingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'white',
    marginRight: 8,
  },
  recordingTime: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  sideControls: {
    position: 'absolute',
    right: 20,
    top: '50%',
    transform: [{ translateY: -100 }],
    zIndex: 1,
  },
  sideButton: {
    alignItems: 'center',
    padding: 10,
    marginVertical: 15,
    backgroundColor: 'rgba(0,0,0,0.5)',
    borderRadius: 20,
    minWidth: 60,
  },
  activeButton: {
    backgroundColor: 'rgba(139, 69, 255, 0.8)',
  },
  sideButtonText: {
    color: 'white',
    fontSize: 10,
    marginTop: 4,
  },
  badgeContainer: {
    position: 'absolute',
    top: -5,
    right: -5,
    backgroundColor: COLORS.primary,
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  badgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  bottomControls: {
    position: 'absolute',
    bottom: 50,
    left: 0,
    right: 0,
    alignItems: 'center',
    zIndex: 1,
  },
  recordButtonContainer: {
    padding: 5,
  },
  recordButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'white',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 4,
    borderColor: 'rgba(255,255,255,0.5)',
  },
  recordingButton: {
    borderColor: '#ff4757',
  },
  recordButtonInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#ff4757',
  },
  recordingInner: {
    width: 30,
    height: 30,
    borderRadius: 4,
    backgroundColor: '#ff4757',
  },
  permissionText: {
    color: 'white',
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 20,
  },
  permissionButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  permissionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loadingText: {
    color: 'white',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 20,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingTop: 20,
    maxHeight: SCREEN_HEIGHT * 0.6,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  modalScroll: {
    maxHeight: SCREEN_HEIGHT * 0.4,
  },
  filterItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  selectedFilterItem: {
    backgroundColor: '#f8f9fa',
  },
  filterName: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
    marginLeft: 15,
  },
});