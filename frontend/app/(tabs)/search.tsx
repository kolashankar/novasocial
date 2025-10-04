import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  ScrollView,
  TouchableOpacity,
  Image,
  RefreshControl,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useAuthContext } from '../../src/contexts/AuthContext';
import { searchApi, SearchResult } from '../../src/services/searchApi';
import { PostCard } from '../../src/components/feed/PostCard';

export default function SearchScreen() {
  const { token } = useAuthContext();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [trendingHashtags, setTrendingHashtags] = useState<Array<{hashtag: string; count: number}>>([]);
  const [userSuggestions, setUserSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [searchType, setSearchType] = useState<'all' | 'users' | 'posts' | 'hashtags'>('all');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      if (token) {
        const [hashtags, suggestions] = await Promise.all([
          searchApi.getTrendingHashtags(token),
          searchApi.getUserSuggestions(token),
        ]);
        setTrendingHashtags(hashtags);
        setUserSuggestions(suggestions);
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      if (token) {
        const results = await searchApi.search(searchQuery, searchType, token);
        setSearchResults(results);
      }
    } catch (error) {
      console.error('Search failed:', error);
      Alert.alert('Error', 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadInitialData().finally(() => setRefreshing(false));
  };

  const handleUserPress = (userId: string) => {
    router.push(`/profile/${userId}`);
  };

  const handleHashtagPress = (hashtag: string) => {
    setSearchQuery(hashtag);
    setSearchType('posts');
    handleSearch();
  };

  const renderSearchTypeButtons = () => (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      style={styles.searchTypeContainer}
      contentContainerStyle={styles.searchTypeContent}
    >
      {(['all', 'users', 'posts', 'hashtags'] as const).map((type) => (
        <TouchableOpacity
          key={type}
          style={[
            styles.searchTypeButton,
            searchType === type && styles.activeSearchTypeButton,
          ]}
          onPress={() => setSearchType(type)}
        >
          <Text
            style={[
              styles.searchTypeText,
              searchType === type && styles.activeSearchTypeText,
            ]}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );

  const renderUserItem = (user: any) => (
    <TouchableOpacity
      key={user.id}
      style={styles.userItem}
      onPress={() => handleUserPress(user.id)}
    >
      <Image
        source={{
          uri: user.profileImage || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
        }}
        style={styles.userAvatar}
      />
      <View style={styles.userInfo}>
        <Text style={styles.username}>{user.username}</Text>
        <Text style={styles.fullName}>{user.fullName}</Text>
        {user.bio && <Text style={styles.userBio} numberOfLines={1}>{user.bio}</Text>}
      </View>
      <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
    </TouchableOpacity>
  );

  const renderHashtagItem = (hashtag: string | {hashtag: string; count: number}) => {
    const hashtagText = typeof hashtag === 'string' ? hashtag : hashtag.hashtag;
    const count = typeof hashtag === 'object' ? hashtag.count : undefined;
    
    return (
      <TouchableOpacity
        key={hashtagText}
        style={styles.hashtagItem}
        onPress={() => handleHashtagPress(hashtagText)}
      >
        <View style={styles.hashtagIcon}>
          <Ionicons name="pricetag" size={20} color="#3b82f6" />
        </View>
        <View style={styles.hashtagInfo}>
          <Text style={styles.hashtagText}>#{hashtagText}</Text>
          {count && <Text style={styles.hashtagCount}>{count} posts</Text>}
        </View>
      </TouchableOpacity>
    );
  };

  const renderSearchResults = () => {
    if (!searchResults) return null;

    return (
      <View style={styles.searchResults}>
        {searchResults.users.length > 0 && (
          <View style={styles.resultSection}>
            <Text style={styles.sectionTitle}>Users</Text>
            {searchResults.users.map(renderUserItem)}
          </View>
        )}

        {searchResults.hashtags.length > 0 && (
          <View style={styles.resultSection}>
            <Text style={styles.sectionTitle}>Hashtags</Text>
            {searchResults.hashtags.map(renderHashtagItem)}
          </View>
        )}

        {searchResults.posts.length > 0 && (
          <View style={styles.resultSection}>
            <Text style={styles.sectionTitle}>Posts</Text>
            {searchResults.posts.map((post, index) => (
              <PostCard key={post.id} post={post} />
            ))}
          </View>
        )}

        {searchResults.users.length === 0 && searchResults.posts.length === 0 && searchResults.hashtags.length === 0 && (
          <View style={styles.noResultsContainer}>
            <Ionicons name="search-outline" size={48} color="#9ca3af" />
            <Text style={styles.noResultsTitle}>No results found</Text>
            <Text style={styles.noResultsText}>Try searching for something else</Text>
          </View>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.searchContainer}>
          <View style={styles.searchInputContainer}>
            <Ionicons name="search" size={20} color="#9ca3af" style={styles.searchIcon} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search users, posts, hashtags..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              onSubmitEditing={handleSearch}
              returnKeyType="search"
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity
                style={styles.clearButton}
                onPress={() => {
                  setSearchQuery('');
                  setSearchResults(null);
                }}
              >
                <Ionicons name="close-circle" size={20} color="#9ca3af" />
              </TouchableOpacity>
            )}
          </View>
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
            <Text style={styles.searchButtonText}>Search</Text>
          </TouchableOpacity>
        </View>
        {renderSearchTypeButtons()}
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
      >
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#3b82f6" />
            <Text style={styles.loadingText}>Searching...</Text>
          </View>
        ) : searchResults ? (
          renderSearchResults()
        ) : (
          <>
            {trendingHashtags.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Trending Hashtags</Text>
                {trendingHashtags.map(renderHashtagItem)}
              </View>
            )}

            {userSuggestions.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Suggested Users</Text>
                {userSuggestions.map(renderUserItem)}
              </View>
            )}
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    borderRadius: 24,
    paddingHorizontal: 16,
    height: 44,
    marginRight: 12,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#1e293b',
  },
  clearButton: {
    marginLeft: 8,
  },
  searchButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
  },
  searchButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  searchTypeContainer: {
    marginBottom: 16,
  },
  searchTypeContent: {
    paddingHorizontal: 4,
  },
  searchTypeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: '#f1f5f9',
    marginRight: 8,
  },
  activeSearchTypeButton: {
    backgroundColor: '#3b82f6',
  },
  searchTypeText: {
    fontSize: 14,
    color: '#64748b',
    fontWeight: '500',
  },
  activeSearchTypeText: {
    color: '#ffffff',
  },
  content: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 80,
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 16,
  },
  section: {
    paddingVertical: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 12,
    paddingHorizontal: 16,
  },
  userItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  userAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    marginRight: 12,
  },
  userInfo: {
    flex: 1,
  },
  username: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  fullName: {
    fontSize: 14,
    color: '#64748b',
    marginTop: 2,
  },
  userBio: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 4,
  },
  hashtagItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  hashtagIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#eff6ff',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  hashtagInfo: {
    flex: 1,
  },
  hashtagText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
  },
  hashtagCount: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
  searchResults: {
    flex: 1,
  },
  resultSection: {
    marginBottom: 24,
  },
  noResultsContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 80,
    paddingHorizontal: 40,
  },
  noResultsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
  },
  noResultsText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
});