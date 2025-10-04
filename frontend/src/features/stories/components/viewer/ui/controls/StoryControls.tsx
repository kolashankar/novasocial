import React from 'react';
import {
  View,
  TouchableOpacity,
  StyleSheet,
  Text,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { ProgressBar } from './progress/bar/ProgressBar';

export interface StoryControlsProps {
  stories: Array<{
    id: string;
    author: {
      id: string;
      username: string;
      fullName: string;
      profileImage?: string;
    };
    media: string;
    text?: string;
    createdAt: string;
  }>;
  currentIndex: number;
  isPlaying: boolean;
  onClose: () => void;
  onNext: () => void;
  onPrevious: () => void;
  onTogglePlay: () => void;
  onStoryComplete: () => void;
}

export const StoryControls: React.FC<StoryControlsProps> = ({
  stories,
  currentIndex,
  isPlaying,
  onClose,
  onNext,
  onPrevious,
  onTogglePlay,
  onStoryComplete,
}) => {
  const currentStory = stories[currentIndex];
  
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return `${Math.floor(diffInHours * 60)}m`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h`;
    } else {
      return `${Math.floor(diffInHours / 24)}d`;
    }
  };

  return (
    <View style={styles.container}>
      {/* Progress Bars */}
      <View style={styles.progressContainer}>
        {stories.map((_, index) => (
          <ProgressBar
            key={index}
            duration={5000} // 5 seconds per story
            isActive={index === currentIndex}
            isPaused={!isPlaying}
            onComplete={onStoryComplete}
          />
        ))}
      </View>

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.userInfo}>
          <Image
            source={{ 
              uri: currentStory?.author.profileImage || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==' 
            }}
            style={styles.avatar}
          />
          <View style={styles.userText}>
            <Text style={styles.username}>
              {currentStory?.author.username}
            </Text>
            <Text style={styles.timeAgo}>
              {currentStory ? formatTimeAgo(currentStory.createdAt) : ''}
            </Text>
          </View>
        </View>
        
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.actionButton} onPress={onTogglePlay}>
            <Ionicons 
              name={isPlaying ? 'pause' : 'play'} 
              size={20} 
              color="#ffffff" 
            />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={onClose}>
            <Ionicons name="close" size={24} color="#ffffff" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Navigation Areas */}
      <TouchableOpacity 
        style={styles.leftTouchArea} 
        onPress={onPrevious}
        activeOpacity={1}
      />
      
      <TouchableOpacity 
        style={styles.rightTouchArea} 
        onPress={onNext}
        activeOpacity={1}
      />

      {/* Story Text Overlay */}
      {currentStory?.text && (
        <View style={styles.textOverlay}>
          <Text style={styles.storyText}>
            {currentStory.text}
          </Text>
        </View>
      )}

      {/* Bottom Actions */}
      <View style={styles.bottomActions}>
        <TouchableOpacity style={styles.replyButton}>
          <Ionicons name="chatbubble-outline" size={24} color="#ffffff" />
          <Text style={styles.replyText}>Send message</Text>
        </TouchableOpacity>
        
        <View style={styles.rightActions}>
          <TouchableOpacity style={styles.bottomActionButton}>
            <Ionicons name="heart-outline" size={28} color="#ffffff" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.bottomActionButton}>
            <Ionicons name="share-outline" size={24} color="#ffffff" />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 10,
  },
  progressContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingTop: 60,
    paddingBottom: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    marginRight: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  userText: {
    flex: 1,
  },
  username: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  timeAgo: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 12,
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionButton: {
    padding: 8,
    marginLeft: 8,
  },
  leftTouchArea: {
    position: 'absolute',
    left: 0,
    top: 120,
    bottom: 120,
    width: '30%',
  },
  rightTouchArea: {
    position: 'absolute',
    right: 0,
    top: 120,
    bottom: 120,
    width: '30%',
  },
  textOverlay: {
    position: 'absolute',
    bottom: 200,
    left: 20,
    right: 20,
    alignItems: 'center',
  },
  storyText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 4,
    padding: 12,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: 12,
  },
  bottomActions: {
    position: 'absolute',
    bottom: 50,
    left: 16,
    right: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  replyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 25,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginRight: 12,
  },
  replyText: {
    color: '#ffffff',
    fontSize: 16,
    marginLeft: 8,
  },
  rightActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  bottomActionButton: {
    padding: 8,
    marginLeft: 8,
  },
});