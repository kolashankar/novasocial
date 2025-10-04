import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, RefreshControl, Dimensions, FlatList } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/contexts/AuthContext';
import { COLORS, SPACING } from '../../src/utils/constants';
import { Button } from '../../src/components/common';
import { router } from 'expo-router';

const { width } = Dimensions.get('window');
const itemSize = (width - SPACING.lg * 3) / 3; // 3 columns with spacing

export default function Profile() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('posts');
  const [refreshing, setRefreshing] = useState(false);
  const [userStats, setUserStats] = useState({
    postsCount: 0,
    followersCount: 0,
    followingCount: 0,
  });
  const [userPosts, setUserPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchUserStats = async () => {
    try {
      if (!user?.id) return;
      
      const response = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/users/${user.id}/stats`);
      if (response.ok) {
        const stats = await response.json();
        setUserStats(stats);
      }
    } catch (error) {
      console.error('Error fetching user stats:', error);
    }
  };

  const fetchUserPosts = async () => {
    try {
      if (!user?.id) return;
      
      const response = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/users/${user.id}/posts`);
      if (response.ok) {
        const posts = await response.json();
        setUserPosts(posts);
      }
    } catch (error) {
      console.error('Error fetching user posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchUserStats(), fetchUserPosts()]);
    setRefreshing(false);
  };

  const handleLogout = async () => {
    await logout();
  };

  const navigateToSettings = () => {
    router.push('/settings');
  };

  const navigateToEditProfile = () => {
    router.push('/edit-profile');
  };

  useEffect(() => {
    if (user?.id) {
      fetchUserStats();
      fetchUserPosts();
    }
  }, [user?.id]);

  const renderPostGrid = () => {
    if (loading) {
      return (
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading posts...</Text>
        </View>
      );
    }

    if (userPosts.length === 0) {
      return (
        <View style={styles.emptyPosts}>
          <Ionicons name="camera-outline" size={60} color={COLORS.gray400} />
          <Text style={styles.emptyPostsText}>No posts yet</Text>
          <Text style={styles.emptyPostsSubtext}>Share your first post to get started</Text>
        </View>
      );
    }

    return (
      <FlatList
        data={userPosts}
        numColumns={3}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity 
            style={styles.postGridItem}
            onPress={() => router.push(`/post/${item.id}`)}
          >
            <Image 
              source={{ uri: item.media[0] }} 
              style={styles.postGridImage}
              resizeMode="cover"
            />
            {item.media.length > 1 && (
              <View style={styles.multipleMediaIndicator}>
                <Ionicons name="copy-outline" size={16} color="white" />
              </View>
            )}
          </TouchableOpacity>
        )}
        contentContainerStyle={styles.postsGrid}
        scrollEnabled={false}
      />
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'posts':
        return renderPostGrid();
      case 'reels':
        return (
          <View style={styles.emptyPosts}>
            <Ionicons name="videocam-outline" size={60} color={COLORS.gray400} />
            <Text style={styles.emptyPostsText}>No reels yet</Text>
            <Text style={styles.emptyPostsSubtext}>Create your first reel</Text>
          </View>
        );
      case 'tagged':
        return (
          <View style={styles.emptyPosts}>
            <Ionicons name="bookmark-outline" size={60} color={COLORS.gray400} />
            <Text style={styles.emptyPostsText}>No tagged posts</Text>
            <Text style={styles.emptyPostsSubtext}>Posts you're tagged in will appear here</Text>
          </View>
        );
      default:
        return null;
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{user?.username || 'Profile'}</Text>
          <TouchableOpacity style={styles.settingsButton} onPress={navigateToSettings}>
            <Ionicons name="settings-outline" size={24} color={COLORS.text} />
          </TouchableOpacity>
        </View>

        {/* Profile Info Section */}
        <View style={styles.profileSection}>
          <View style={styles.profileImageContainer}>
            {user?.profileImage ? (
              <Image source={{ uri: user.profileImage }} style={styles.profileImage} />
            ) : (
              <View style={styles.defaultProfileImage}>
                <Ionicons name="person" size={50} color={COLORS.gray400} />
              </View>
            )}
          </View>
          
          <Text style={styles.fullName}>{user?.fullName || 'User Name'}</Text>
          
          {user?.bio && (
            <Text style={styles.bio}>{user.bio}</Text>
          )}

          {/* Stats */}
          <View style={styles.statsContainer}>
            <TouchableOpacity style={styles.statItem}>
              <Text style={styles.statNumber}>{userStats.postsCount}</Text>
              <Text style={styles.statLabel}>Posts</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.statItem}>
              <Text style={styles.statNumber}>{userStats.followersCount}</Text>
              <Text style={styles.statLabel}>Followers</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.statItem}>
              <Text style={styles.statNumber}>{userStats.followingCount}</Text>
              <Text style={styles.statLabel}>Following</Text>
            </TouchableOpacity>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionsContainer}>
            <TouchableOpacity style={styles.editProfileButton} onPress={navigateToEditProfile}>
              <Text style={styles.editProfileButtonText}>Edit Profile</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.shareProfileButton}>
              <Ionicons name="share-outline" size={20} color={COLORS.text} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Tabs */}
        <View style={styles.tabsContainer}>
          <TouchableOpacity 
            style={[styles.tab, activeTab === 'posts' && styles.activeTab]}
            onPress={() => setActiveTab('posts')}
          >
            <Ionicons 
              name={activeTab === 'posts' ? 'grid' : 'grid-outline'} 
              size={24} 
              color={activeTab === 'posts' ? COLORS.primary : COLORS.gray400} 
            />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.tab, activeTab === 'reels' && styles.activeTab]}
            onPress={() => setActiveTab('reels')}
          >
            <Ionicons 
              name={activeTab === 'reels' ? 'videocam' : 'videocam-outline'} 
              size={24} 
              color={activeTab === 'reels' ? COLORS.primary : COLORS.gray400} 
            />
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.tab, activeTab === 'tagged' && styles.activeTab]}
            onPress={() => setActiveTab('tagged')}
          >
            <Ionicons 
              name={activeTab === 'tagged' ? 'bookmark' : 'bookmark-outline'} 
              size={24} 
              color={activeTab === 'tagged' ? COLORS.primary : COLORS.gray400} 
            />
          </TouchableOpacity>
        </View>

        {/* Tab Content */}
        <View style={styles.tabContent}>
          {renderTabContent()}
        </View>
      </ScrollView>
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
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  settingsButton: {
    padding: SPACING.sm,
  },
  profileSection: {
    alignItems: 'center',
    padding: SPACING.lg,
  },
  profileImageContainer: {
    marginBottom: SPACING.md,
  },
  profileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  defaultProfileImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: COLORS.cardBackground,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  fullName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: SPACING.xs,
    textAlign: 'center',
  },
  bio: {
    fontSize: 14,
    color: COLORS.text,
    textAlign: 'center',
    marginBottom: SPACING.lg,
    lineHeight: 20,
    paddingHorizontal: SPACING.md,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    paddingVertical: SPACING.lg,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: COLORS.border,
    marginBottom: SPACING.lg,
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  statLabel: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
  },
  actionsContainer: {
    flexDirection: 'row',
    paddingHorizontal: SPACING.lg,
    gap: SPACING.sm,
    marginBottom: SPACING.lg,
  },
  editProfileButton: {
    flex: 1,
    backgroundColor: COLORS.cardBackground,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingVertical: SPACING.sm,
    alignItems: 'center',
  },
  editProfileButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  shareProfileButton: {
    backgroundColor: COLORS.cardBackground,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabsContainer: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: SPACING.md,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: COLORS.primary,
  },
  tabContent: {
    flex: 1,
    minHeight: 300,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: SPACING.xl,
  },
  loadingText: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  emptyPosts: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: SPACING.xl * 2,
  },
  emptyPostsText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginTop: SPACING.md,
  },
  emptyPostsSubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: SPACING.xs,
    textAlign: 'center',
  },
  postsGrid: {
    padding: SPACING.xs,
  },
  postGridItem: {
    width: itemSize,
    height: itemSize,
    margin: SPACING.xs,
    borderRadius: 4,
    overflow: 'hidden',
    position: 'relative',
  },
  postGridImage: {
    width: '100%',
    height: '100%',
  },
  multipleMediaIndicator: {
    position: 'absolute',
    top: SPACING.xs,
    right: SPACING.xs,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderRadius: 12,
    padding: 2,
  },
});