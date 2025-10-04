import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuthContext } from '../../contexts/AuthContext';
import { COLORS, SPACING } from '../../utils/constants';
import { apiService } from '../../services/api';

const { width: screenWidth } = Dimensions.get('window');

interface Post {
  id: string;
  author: {
    id: string;
    username: string;
    fullName: string;
    profileImage?: string;
  };
  caption: string;
  media: string[];
  mediaTypes: string[];
  hashtags: string[];
  taggedUsers: string[];
  likes: string[];
  likesCount: number;
  commentsCount: number;
  createdAt: string;
}

interface PostCardProps {
  post: Post;
  onLike?: (postId: string, liked: boolean) => void;
  onComment?: (postId: string) => void;
  onShare?: (postId: string) => void;
}

export const PostCard: React.FC<PostCardProps> = ({
  post,
  onLike,
  onComment,
  onShare,
}) => {
  const { user, token } = useAuthContext();
  const [isLiked, setIsLiked] = useState(post.likes.includes(user?.id || ''));
  const [likesCount, setLikesCount] = useState(post.likesCount);
  const [isLiking, setIsLiking] = useState(false);

  const handleLike = async () => {
    if (isLiking || !token) return;

    setIsLiking(true);
    const newLiked = !isLiked;
    const newCount = newLiked ? likesCount + 1 : likesCount - 1;

    // Optimistic update
    setIsLiked(newLiked);
    setLikesCount(newCount);

    try {
      const response = await apiService.post(`/posts/${post.id}/like`, {}, token);
      setLikesCount(response.likesCount);
      onLike?.(post.id, response.liked);
    } catch (error) {
      // Revert on error
      setIsLiked(!newLiked);
      setLikesCount(likesCount);
      Alert.alert('Error', 'Failed to update like status');
    } finally {
      setIsLiking(false);
    }
  };

  const handleComment = () => {
    onComment?.(post.id);
  };

  const handleShare = () => {
    onShare?.(post.id);
  };

  const formatTime = (dateString: string) => {
    const now = new Date();
    const postDate = new Date(dateString);
    const diffInHours = Math.floor((now.getTime() - postDate.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'now';
    if (diffInHours < 24) return `${diffInHours}h`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d`;
    return `${Math.floor(diffInHours / 168)}w`;
  };

  const renderHashtags = (text: string) => {
    const words = text.split(' ');
    return (
      <Text style={styles.caption}>
        {words.map((word, index) => {
          if (word.startsWith('#')) {
            return (
              <Text key={index} style={styles.hashtag}>
                {word}{index < words.length - 1 ? ' ' : ''}
              </Text>
            );
          }
          return `${word}${index < words.length - 1 ? ' ' : ''}`;
        })}
      </Text>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.authorInfo}>
          {post.author.profileImage ? (
            <Image
              source={{ uri: post.author.profileImage }}
              style={styles.authorAvatar}
            />
          ) : (
            <View style={styles.defaultAvatar}>
              <Ionicons name="person" size={20} color={COLORS.gray400} />
            </View>
          )}
          <View style={styles.authorText}>
            <Text style={styles.authorName}>{post.author.username}</Text>
            <Text style={styles.timeText}>{formatTime(post.createdAt)}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.moreButton}>
          <Ionicons name="ellipsis-horizontal" size={20} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      {/* Media */}
      {post.media.length > 0 && (
        <View style={styles.mediaContainer}>
          <Image
            source={{ uri: post.media[0] }}
            style={styles.media}
            resizeMode="cover"
          />
          {post.media.length > 1 && (
            <View style={styles.mediaIndicator}>
              <Ionicons name="copy" size={16} color={COLORS.white} />
              <Text style={styles.mediaCount}>{post.media.length}</Text>
            </View>
          )}
        </View>
      )}

      {/* Actions */}
      <View style={styles.actions}>
        <View style={styles.leftActions}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={handleLike}
            disabled={isLiking}
          >
            <Ionicons
              name={isLiked ? 'heart' : 'heart-outline'}
              size={24}
              color={isLiked ? COLORS.error : COLORS.text}
            />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={handleComment}>
            <Ionicons name="chatbubble-outline" size={24} color={COLORS.text} />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
            <Ionicons name="paper-plane-outline" size={24} color={COLORS.text} />
          </TouchableOpacity>
        </View>
        <TouchableOpacity style={styles.bookmarkButton}>
          <Ionicons name="bookmark-outline" size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>

      {/* Likes and Comments Count */}
      <View style={styles.stats}>
        {likesCount > 0 && (
          <Text style={styles.likesText}>
            {likesCount} {likesCount === 1 ? 'like' : 'likes'}
          </Text>
        )}
      </View>

      {/* Caption */}
      {post.caption && (
        <View style={styles.captionContainer}>
          <Text style={styles.authorUsername}>{post.author.username} </Text>
          {renderHashtags(post.caption)}
        </View>
      )}

      {/* Comments */}
      {post.commentsCount > 0 && (
        <TouchableOpacity onPress={handleComment}>
          <Text style={styles.viewComments}>
            View all {post.commentsCount} comments
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.background,
    marginBottom: SPACING.sm,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  authorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  authorAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
  },
  defaultAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.cardBackground,
    justifyContent: 'center',
    alignItems: 'center',
  },
  authorText: {
    marginLeft: SPACING.sm,
  },
  authorName: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  timeText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  moreButton: {
    padding: SPACING.xs,
  },
  mediaContainer: {
    position: 'relative',
  },
  media: {
    width: screenWidth,
    height: screenWidth,
  },
  mediaIndicator: {
    position: 'absolute',
    top: SPACING.sm,
    right: SPACING.sm,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    paddingHorizontal: SPACING.xs,
    paddingVertical: 2,
    borderRadius: 12,
  },
  mediaCount: {
    color: COLORS.white,
    fontSize: 12,
    marginLeft: 2,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.sm,
  },
  leftActions: {
    flexDirection: 'row',
  },
  actionButton: {
    paddingRight: SPACING.md,
  },
  bookmarkButton: {
    padding: SPACING.xs,
  },
  stats: {
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.xs,
  },
  likesText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  captionContainer: {
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.xs,
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  authorUsername: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  caption: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 18,
  },
  hashtag: {
    color: COLORS.primary,
  },
  viewComments: {
    fontSize: 14,
    color: COLORS.textSecondary,
    paddingHorizontal: SPACING.md,
    paddingTop: SPACING.xs,
    paddingBottom: SPACING.sm,
  },
});