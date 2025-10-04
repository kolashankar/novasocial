import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
  Image,
  Animated,
} from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import { COLORS, SPACING } from '../../utils/constants';
import { apiService } from '../../services/api';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

interface Reel {
  id: string;
  author: {
    id: string;
    username: string;
    fullName: string;
    profileImage?: string;
  };
  caption: string;
  videoUrl: string;
  likes: string[];
  likesCount: number;
  commentsCount: number;
  createdAt: string;
}

interface ReelVideoProps {
  reel: Reel;
  isActive: boolean;
  onLike?: (reelId: string, liked: boolean) => void;
  onComment?: (reelId: string) => void;
  onShare?: (reelId: string) => void;
  onFollow?: (userId: string) => void;
}

export const ReelVideo: React.FC<ReelVideoProps> = ({
  reel,
  isActive,
  onLike,
  onComment,
  onShare,
  onFollow,
}) => {
  const videoRef = useRef<Video>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [likesCount, setLikesCount] = useState(reel.likesCount);
  const [isLiking, setIsLiking] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const heartAnimation = useRef(new Animated.Value(0)).current;
  
  const { user, token } = useAuth();

  useEffect(() => {
    setIsLiked(reel.likes.includes(user?.id || ''));
    setLikesCount(reel.likesCount);
  }, [reel, user]);

  useEffect(() => {
    if (isActive && videoRef.current) {
      videoRef.current.playAsync();
      setIsPlaying(true);
    } else if (!isActive && videoRef.current) {
      videoRef.current.pauseAsync();
      setIsPlaying(false);
    }
  }, [isActive]);

  const handleVideoPress = async () => {
    if (!videoRef.current) return;

    if (isPlaying) {
      await videoRef.current.pauseAsync();
      setIsPlaying(false);
    } else {
      await videoRef.current.playAsync();
      setIsPlaying(true);
    }
    
    setShowControls(true);
    setTimeout(() => setShowControls(false), 2000);
  };

  const handleLike = async () => {
    if (isLiking || !token) return;

    setIsLiking(true);
    const newLiked = !isLiked;
    const newCount = newLiked ? likesCount + 1 : likesCount - 1;

    // Optimistic update
    setIsLiked(newLiked);
    setLikesCount(newCount);

    // Animate heart
    if (newLiked) {
      Animated.sequence([
        Animated.timing(heartAnimation, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(heartAnimation, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }

    try {
      const response = await apiService.post(`/posts/${reel.id}/like`, {}, token);
      setLikesCount(response.likesCount);
      onLike?.(reel.id, response.liked);
    } catch (error) {
      // Revert on error
      setIsLiked(!newLiked);
      setLikesCount(likesCount);
    } finally {
      setIsLiking(false);
    }
  };

  const handleDoubleTap = () => {
    if (!isLiked) {
      handleLike();
    }
  };

  const formatCount = (count: number): string => {
    if (count < 1000) return count.toString();
    if (count < 1000000) return `${(count / 1000).toFixed(1)}K`;
    return `${(count / 1000000).toFixed(1)}M`;
  };

  return (
    <View style={styles.container}>
      {/* Video */}
      <TouchableOpacity
        activeOpacity={1}
        onPress={handleVideoPress}
        onLongPress={() => {}} // Prevent context menu
        delayLongPress={500}
        style={styles.videoContainer}
      >
        <Video
          ref={videoRef}
          source={{ uri: reel.videoUrl }}
          style={styles.video}
          resizeMode={ResizeMode.COVER}
          shouldPlay={isActive}
          isLooping
          isMuted={false}
        />
        
        {/* Play/Pause Overlay */}
        {showControls && (
          <View style={styles.playOverlay}>
            <Ionicons
              name={isPlaying ? 'pause' : 'play'}
              size={60}
              color={COLORS.white}
            />
          </View>
        )}
        
        {/* Double Tap Heart Animation */}
        <Animated.View
          style={[
            styles.heartAnimation,
            {
              transform: [
                {
                  scale: heartAnimation.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0, 1.2],
                  }),
                },
              ],
              opacity: heartAnimation.interpolate({
                inputRange: [0, 0.5, 1],
                outputRange: [0, 1, 0],
              }),
            },
          ]}
          pointerEvents="none"
        >
          <Ionicons name="heart" size={80} color={COLORS.error} />
        </Animated.View>
      </TouchableOpacity>

      {/* Right Side Actions */}
      <View style={styles.rightActions}>
        {/* Author Profile */}
        <View style={styles.authorContainer}>
          {reel.author.profileImage ? (
            <Image
              source={{ uri: reel.author.profileImage }}
              style={styles.authorAvatar}
            />
          ) : (
            <View style={styles.defaultAvatar}>
              <Ionicons name="person" size={20} color={COLORS.gray400} />
            </View>
          )}
          {user?.id !== reel.author.id && (
            <TouchableOpacity
              style={styles.followButton}
              onPress={() => onFollow?.(reel.author.id)}
            >
              <Ionicons name="add" size={16} color={COLORS.white} />
            </TouchableOpacity>
          )}
        </View>

        {/* Like Button */}
        <TouchableOpacity style={styles.actionButton} onPress={handleLike}>
          <Ionicons
            name={isLiked ? 'heart' : 'heart-outline'}
            size={28}
            color={isLiked ? COLORS.error : COLORS.white}
          />
          <Text style={styles.actionCount}>{formatCount(likesCount)}</Text>
        </TouchableOpacity>

        {/* Comment Button */}
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => onComment?.(reel.id)}
        >
          <Ionicons name="chatbubble-outline" size={26} color={COLORS.white} />
          <Text style={styles.actionCount}>{formatCount(reel.commentsCount)}</Text>
        </TouchableOpacity>

        {/* Share Button */}
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => onShare?.(reel.id)}
        >
          <Ionicons name="paper-plane-outline" size={26} color={COLORS.white} />
        </TouchableOpacity>

        {/* More Options */}
        <TouchableOpacity style={styles.actionButton}>
          <Ionicons name="ellipsis-horizontal" size={26} color={COLORS.white} />
        </TouchableOpacity>
      </View>

      {/* Bottom Info */}
      <View style={styles.bottomInfo}>
        <Text style={styles.username}>@{reel.author.username}</Text>
        {reel.caption && (
          <Text style={styles.caption} numberOfLines={2}>
            {reel.caption}
          </Text>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: screenWidth,
    height: screenHeight,
    backgroundColor: COLORS.background,
  },
  videoContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  video: {
    width: screenWidth,
    height: screenHeight,
  },
  playOverlay: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    borderRadius: 40,
    width: 80,
    height: 80,
  },
  heartAnimation: {
    position: 'absolute',
    justifyContent: 'center',
    alignItems: 'center',
  },
  rightActions: {
    position: 'absolute',
    right: SPACING.md,
    bottom: 100,
    alignItems: 'center',
  },
  authorContainer: {
    alignItems: 'center',
    marginBottom: SPACING.lg,
    position: 'relative',
  },
  authorAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  defaultAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.cardBackground,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  followButton: {
    position: 'absolute',
    bottom: -8,
    backgroundColor: COLORS.error,
    borderRadius: 12,
    width: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  actionButton: {
    alignItems: 'center',
    marginBottom: SPACING.lg,
  },
  actionCount: {
    color: COLORS.white,
    fontSize: 12,
    marginTop: SPACING.xs,
    fontWeight: '600',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  bottomInfo: {
    position: 'absolute',
    bottom: 100,
    left: SPACING.md,
    right: 80,
  },
  username: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
    marginBottom: SPACING.xs,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  caption: {
    color: COLORS.white,
    fontSize: 14,
    lineHeight: 18,
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
});