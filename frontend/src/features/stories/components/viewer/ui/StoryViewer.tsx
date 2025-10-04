import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  StyleSheet,
  Image,
  Dimensions,
  Alert,
} from 'react-native';
import { Video } from 'expo-av';
import { PanGestureHandler, State } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  useAnimatedGestureHandler,
  withSpring,
  runOnJS,
} from 'react-native-reanimated';
import { StoryControls } from './controls/StoryControls';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

export interface Story {
  id: string;
  authorId: string;
  author: {
    id: string;
    username: string;
    fullName: string;
    profileImage?: string;
  };
  media: string;
  mediaType: 'image' | 'video';
  text?: string;
  textPosition?: { x: number; y: number };
  textStyle?: { color: string; fontSize: number };
  duration: number;
  createdAt: string;
  expiresAt: string;
}

export interface StoryViewerProps {
  stories: Story[];
  initialIndex?: number;
  onClose: () => void;
  onStoryComplete?: (storyId: string) => void;
}

export const StoryViewer: React.FC<StoryViewerProps> = ({
  stories,
  initialIndex = 0,
  onClose,
  onStoryComplete,
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isPlaying, setIsPlaying] = useState(true);
  const videoRef = useRef<Video>(null);
  
  const translateY = useSharedValue(0);
  const opacity = useSharedValue(1);

  const currentStory = stories[currentIndex];

  const handleNext = useCallback(() => {
    if (currentIndex < stories.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      onClose();
    }
  }, [currentIndex, stories.length, onClose]);

  const handlePrevious = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  }, [currentIndex]);

  const handleStoryComplete = useCallback(() => {
    onStoryComplete?.(currentStory.id);
    handleNext();
  }, [currentStory?.id, onStoryComplete, handleNext]);

  const handleTogglePlay = useCallback(() => {
    setIsPlaying(prev => !prev);
    if (currentStory.mediaType === 'video' && videoRef.current) {
      if (isPlaying) {
        videoRef.current.pauseAsync();
      } else {
        videoRef.current.playAsync();
      }
    }
  }, [isPlaying, currentStory?.mediaType]);

  const gestureHandler = useAnimatedGestureHandler({
    onStart: () => {
      runOnJS(setIsPlaying)(false);
    },
    onActive: (event) => {
      translateY.value = event.translationY;
      opacity.value = 1 - Math.abs(event.translationY) / screenHeight;
    },
    onEnd: (event) => {
      if (Math.abs(event.translationY) > screenHeight * 0.3) {
        runOnJS(onClose)();
      } else {
        translateY.value = withSpring(0);
        opacity.value = withSpring(1);
        runOnJS(setIsPlaying)(true);
      }
    },
  });

  const animatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateY: translateY.value }],
      opacity: opacity.value,
    };
  });

  const renderMedia = () => {
    if (!currentStory) return null;

    if (currentStory.mediaType === 'video') {
      return (
        <Video
          ref={videoRef}
          source={{ uri: currentStory.media }}
          style={styles.media}
          shouldPlay={isPlaying}
          isLooping={false}
          resizeMode="cover"
          onPlaybackStatusUpdate={(status) => {
            if (status.isLoaded && status.didJustFinish) {
              handleStoryComplete();
            }
          }}
        />
      );
    } else {
      return (
        <Image
          source={{ uri: currentStory.media }}
          style={styles.media}
          resizeMode="cover"
          onError={(error) => {
            console.error('Story image load error:', error);
            Alert.alert('Error', 'Failed to load story image');
          }}
        />
      );
    }
  };

  if (!currentStory) {
    return null;
  }

  return (
    <View style={styles.container}>
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View style={[styles.storyContainer, animatedStyle]}>
          {renderMedia()}
          
          <StoryControls
            stories={stories}
            currentIndex={currentIndex}
            isPlaying={isPlaying}
            onClose={onClose}
            onNext={handleNext}
            onPrevious={handlePrevious}
            onTogglePlay={handleTogglePlay}
            onStoryComplete={handleStoryComplete}
          />
        </Animated.View>
      </PanGestureHandler>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  storyContainer: {
    flex: 1,
    width: screenWidth,
    height: screenHeight,
  },
  media: {
    width: screenWidth,
    height: screenHeight,
    position: 'absolute',
  },
});