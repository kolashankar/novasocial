import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { storiesApi, Story } from '../../services/storiesApi';
import { useAuthContext } from '../../../../contexts/AuthContext';

export const StoriesList: React.FC = () => {
  const { user } = useAuthContext();
  const [stories, setStories] = useState<Story[]>([]);
  const [groupedStories, setGroupedStories] = useState<Array<{
    author: Story['author'];
    stories: Story[];
    hasUnviewed: boolean;
  }>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStories();
  }, []);

  const loadStories = async () => {
    try {
      const storiesData = await storiesApi.getStoriesFeed();
      setStories(storiesData);
      
      const grouped = storiesApi.groupStoriesByAuthor(storiesData);
      setGroupedStories(grouped);
    } catch (error) {
      console.error('Failed to load stories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStoryPress = (authorId: string, storyId?: string) => {
    router.push(`/stories/${authorId}${storyId ? `?storyId=${storyId}` : ''}`);
  };

  const handleAddStory = () => {
    router.push('/story-upload');
  };

  const renderStoryItem = (item: typeof groupedStories[0], index: number) => (
    <TouchableOpacity
      key={item.author.id}
      style={[styles.storyItem, index === 0 && styles.firstStoryItem]}
      onPress={() => handleStoryPress(item.author.id)}
    >
      <View style={[
        styles.storyRing,
        item.hasUnviewed && styles.unviewedRing
      ]}>
        <Image
          source={{ 
            uri: item.author.profileImage || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==' 
          }}
          style={styles.storyImage}
        />
      </View>
      <Text style={styles.storyUsername} numberOfLines={1}>
        {item.author.username}
      </Text>
    </TouchableOpacity>
  );

  const renderAddStoryButton = () => (
    <TouchableOpacity
      style={[styles.storyItem, styles.firstStoryItem]}
      onPress={handleAddStory}
    >
      <LinearGradient
        colors={['#667eea', '#764ba2']}
        style={styles.addStoryButton}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <Ionicons name="add" size={24} color="#ffffff" />
      </LinearGradient>
      <Text style={styles.storyUsername} numberOfLines={1}>
        Your Story
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return null; // Could show skeleton loader
  }

  return (
    <View style={styles.container}>
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {renderAddStoryButton()}
        {groupedStories.map((item, index) => renderStoryItem(item, index + 1))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#ffffff',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  scrollContent: {
    paddingHorizontal: 12,
  },
  storyItem: {
    alignItems: 'center',
    marginHorizontal: 6,
    width: 70,
  },
  firstStoryItem: {
    marginLeft: 16,
  },
  storyRing: {
    width: 64,
    height: 64,
    borderRadius: 32,
    padding: 2,
    backgroundColor: '#e2e8f0',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
  },
  unviewedRing: {
    background: 'linear-gradient(45deg, #667eea, #764ba2)',
    // For React Native, we'll use a different approach for gradient borders
    borderWidth: 2,
    borderColor: '#667eea',
  },
  storyImage: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: '#f8fafc',
  },
  addStoryButton: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 6,
  },
  storyUsername: {
    fontSize: 12,
    color: '#1e293b',
    textAlign: 'center',
    fontWeight: '500',
  },
});