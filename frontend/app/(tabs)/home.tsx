import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { FlashList } from '@shopify/flash-list';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthContext } from '../../src/contexts/AuthContext';
import { PostCard } from '../../src/components/feed/PostCard';
import { StoriesList } from '../../src/features/stories/components/list/StoriesList';
import { COLORS, SPACING } from '../../src/utils/constants';
import { apiService } from '../../src/services/api';

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

export default function Home() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  
  const { token, user } = useAuthContext();

  const fetchPosts = useCallback(async (refresh = false) => {
    if (!token || (isLoading && !refresh)) return;

    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const skip = refresh ? 0 : posts.length;
      const newPosts = await apiService.get(`/posts/feed?skip=${skip}&limit=20`, token);
      
      if (refresh) {
        setPosts(newPosts);
      } else {
        setPosts(prev => [...prev, ...newPosts]);
      }
      
      setHasMore(newPosts.length === 20);
    } catch (error) {
      console.error('Fetch posts error:', error);
      Alert.alert('Error', 'Failed to load posts');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [token, posts.length, isLoading]);

  useEffect(() => {
    fetchPosts(true);
  }, [token]);

  const handleRefresh = () => {
    fetchPosts(true);
  };

  const handleLoadMore = () => {
    if (hasMore && !isLoading) {
      fetchPosts();
    }
  };

  const handleLike = (postId: string, liked: boolean) => {
    setPosts(prev => prev.map(post => {
      if (post.id === postId) {
        const newLikes = liked 
          ? [...post.likes, user?.id || ''].filter((id, index, arr) => arr.indexOf(id) === index)
          : post.likes.filter(id => id !== user?.id);
        return {
          ...post,
          likes: newLikes,
          likesCount: newLikes.length,
        };
      }
      return post;
    }));
  };

  const handleComment = (postId: string) => {
    // Navigate to comments screen
    router.push(`/post/${postId}/comments`);
  };

  const handleShare = (postId: string) => {
    // Implement share functionality
    Alert.alert('Share', 'Share functionality coming soon!');
  };

  const renderPost = ({ item }: { item: Post }) => (
    <PostCard
      post={item}
      onLike={handleLike}
      onComment={handleComment}
      onShare={handleShare}
    />
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <Text style={styles.title}>NovaSocial</Text>
      <View style={styles.headerActions}>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => router.push('/create-post')}
        >
          <Ionicons name="add" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="paper-plane-outline" size={24} color={COLORS.text} />
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="images-outline" size={64} color={COLORS.gray400} />
      <Text style={styles.emptyTitle}>No Posts Yet</Text>
      <Text style={styles.emptySubtitle}>
        Follow some users or create your first post to get started!
      </Text>
      <TouchableOpacity 
        style={styles.createPostButton}
        onPress={() => router.push('/create-post')}
      >
        <Text style={styles.createPostButtonText}>Create Your First Post</Text>
      </TouchableOpacity>
    </View>
  );

  const renderFooter = () => {
    if (!isLoading || isRefreshing) return null;
    return (
      <View style={styles.loadingFooter}>
        <Text style={styles.loadingText}>Loading more posts...</Text>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {renderHeader()}
      <StoriesList />
      
      <FlashList
        data={posts}
        renderItem={renderPost}
        estimatedItemSize={400}
        onEndReached={handleLoadMore}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            colors={[COLORS.primary]}
            tintColor={COLORS.primary}
          />
        }
        ListEmptyComponent={!isLoading ? renderEmpty : null}
        ListFooterComponent={renderFooter}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={posts.length === 0 ? styles.emptyList : undefined}
      />
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
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  headerActions: {
    flexDirection: 'row',
  },
  headerButton: {
    padding: SPACING.xs,
    marginLeft: SPACING.sm,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.text,
    marginTop: SPACING.lg,
    marginBottom: SPACING.sm,
  },
  emptySubtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: SPACING.lg,
  },
  createPostButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderRadius: 25,
  },
  createPostButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  emptyList: {
    flexGrow: 1,
  },
  loadingFooter: {
    padding: SPACING.lg,
    alignItems: 'center',
  },
  loadingText: {
    color: COLORS.textSecondary,
    fontSize: 14,
  },
});