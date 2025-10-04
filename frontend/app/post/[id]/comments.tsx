import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../../src/contexts/AuthContext';
import { COLORS, SPACING } from '../../../src/utils/constants';
import { apiService } from '../../../src/services/api';

interface Comment {
  id: string;
  postId: string;
  author: {
    id: string;
    username: string;
    fullName: string;
    profileImage?: string;
  };
  text: string;
  likes: string[];
  likesCount: number;
  createdAt: string;
}

export default function CommentsScreen() {
  const { id: postId } = useLocalSearchParams<{ id: string }>();
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPosting, setIsPosting] = useState(false);
  
  const { user, token } = useAuth();

  useEffect(() => {
    if (postId) {
      fetchComments();
    }
  }, [postId]);

  const fetchComments = async () => {
    if (!token || !postId) return;

    setIsLoading(true);
    try {
      const commentsData = await apiService.get(`/posts/${postId}/comments`, token);
      setComments(commentsData);
    } catch (error) {
      console.error('Fetch comments error:', error);
      Alert.alert('Error', 'Failed to load comments');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePostComment = async () => {
    if (!newComment.trim() || !token || !postId) return;

    setIsPosting(true);
    try {
      const comment = await apiService.post(
        `/posts/${postId}/comments`,
        { text: newComment.trim(), postId },
        token
      );
      
      setComments(prev => [comment, ...prev]);
      setNewComment('');
    } catch (error) {
      console.error('Post comment error:', error);
      Alert.alert('Error', 'Failed to post comment');
    } finally {
      setIsPosting(false);
    }
  };

  const formatTime = (dateString: string) => {
    const now = new Date();
    const commentDate = new Date(dateString);
    const diffInHours = Math.floor((now.getTime() - commentDate.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'now';
    if (diffInHours < 24) return `${diffInHours}h`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d`;
    return `${Math.floor(diffInHours / 168)}w`;
  };

  const renderComment = ({ item }: { item: Comment }) => (
    <View style={styles.commentContainer}>
      <View style={styles.commentHeader}>
        {item.author.profileImage ? (
          <Image
            source={{ uri: item.author.profileImage }}
            style={styles.commentAvatar}
          />
        ) : (
          <View style={styles.defaultAvatar}>
            <Ionicons name="person" size={16} color={COLORS.gray400} />
          </View>
        )}
        <View style={styles.commentContent}>
          <View style={styles.commentBubble}>
            <Text style={styles.commentUsername}>{item.author.username}</Text>
            <Text style={styles.commentText}>{item.text}</Text>
          </View>
          <View style={styles.commentActions}>
            <Text style={styles.commentTime}>{formatTime(item.createdAt)}</Text>
            <TouchableOpacity style={styles.replyButton}>
              <Text style={styles.replyText}>Reply</Text>
            </TouchableOpacity>
            {item.likesCount > 0 && (
              <Text style={styles.likesText}>{item.likesCount} likes</Text>
            )}
          </View>
        </View>
        <TouchableOpacity style={styles.likeButton}>
          <Ionicons 
            name={item.likes.includes(user?.id || '') ? 'heart' : 'heart-outline'} 
            size={16} 
            color={item.likes.includes(user?.id || '') ? COLORS.error : COLORS.textSecondary} 
          />
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="chatbubble-outline" size={48} color={COLORS.gray400} />
      <Text style={styles.emptyText}>No comments yet</Text>
      <Text style={styles.emptySubtext}>Be the first to comment!</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Comments</Text>
        <View style={styles.headerRight} />
      </View>

      {/* Comments List */}
      <FlatList
        data={comments}
        renderItem={renderComment}
        keyExtractor={(item) => item.id}
        style={styles.commentsList}
        contentContainerStyle={comments.length === 0 ? styles.emptyList : undefined}
        ListEmptyComponent={!isLoading ? renderEmpty : null}
        showsVerticalScrollIndicator={false}
      />

      {/* Comment Input */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.inputContainer}
      >
        <View style={styles.inputRow}>
          {user?.profileImage ? (
            <Image
              source={{ uri: user.profileImage }}
              style={styles.inputAvatar}
            />
          ) : (
            <View style={styles.defaultInputAvatar}>
              <Ionicons name="person" size={16} color={COLORS.gray400} />
            </View>
          )}
          <TextInput
            style={styles.textInput}
            placeholder="Add a comment..."
            placeholderTextColor={COLORS.textSecondary}
            value={newComment}
            onChangeText={setNewComment}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            style={[
              styles.postButton,
              (!newComment.trim() || isPosting) && styles.postButtonDisabled
            ]}
            onPress={handlePostComment}
            disabled={!newComment.trim() || isPosting}
          >
            <Text style={[
              styles.postButtonText,
              (!newComment.trim() || isPosting) && styles.postButtonTextDisabled
            ]}>
              {isPosting ? 'Posting...' : 'Post'}
            </Text>
          </TouchableOpacity>
        </View>
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
  headerRight: {
    width: 40,
  },
  commentsList: {
    flex: 1,
  },
  emptyList: {
    flexGrow: 1,
  },
  commentContainer: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  commentHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  commentAvatar: {
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
  commentContent: {
    flex: 1,
    marginLeft: SPACING.sm,
  },
  commentBubble: {
    backgroundColor: COLORS.cardBackground,
    borderRadius: 16,
    paddingHorizontal: SPACING.sm,
    paddingVertical: SPACING.xs,
  },
  commentUsername: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 2,
  },
  commentText: {
    fontSize: 14,
    color: COLORS.text,
    lineHeight: 18,
  },
  commentActions: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: SPACING.xs,
    marginLeft: SPACING.sm,
  },
  commentTime: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginRight: SPACING.md,
  },
  replyButton: {
    marginRight: SPACING.md,
  },
  replyText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  likesText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  likeButton: {
    padding: SPACING.xs,
    marginLeft: SPACING.sm,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginTop: SPACING.md,
  },
  emptySubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  inputContainer: {
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.background,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
  },
  inputAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
  },
  defaultInputAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.cardBackground,
    justifyContent: 'center',
    alignItems: 'center',
  },
  textInput: {
    flex: 1,
    backgroundColor: COLORS.cardBackground,
    borderRadius: 20,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    marginHorizontal: SPACING.sm,
    fontSize: 14,
    color: COLORS.text,
    maxHeight: 100,
  },
  postButton: {
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.xs,
  },
  postButtonDisabled: {
    opacity: 0.5,
  },
  postButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
  },
  postButtonTextDisabled: {
    color: COLORS.textSecondary,
  },
});