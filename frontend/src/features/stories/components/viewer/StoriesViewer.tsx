import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Modal,
  StatusBar,
} from 'react-native';
import { StoryViewer, Story } from './ui/StoryViewer';
import { storiesApi } from '../../services/storiesApi';

export interface StoriesViewerProps {
  visible: boolean;
  authorId?: string;
  initialStoryId?: string;
  onClose: () => void;
}

export const StoriesViewer: React.FC<StoriesViewerProps> = ({
  visible,
  authorId,
  initialStoryId,
  onClose,
}) => {
  const [stories, setStories] = useState<Story[]>([]);
  const [initialIndex, setInitialIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (visible) {
      loadStories();
    }
  }, [visible, authorId]);

  const loadStories = async () => {
    try {
      setLoading(true);
      const storiesData = await storiesApi.getStoriesFeed();
      
      let filteredStories = storiesData;
      if (authorId) {
        filteredStories = storiesData.filter(story => story.authorId === authorId);
      }
      
      setStories(filteredStories);
      
      // Find initial index if initialStoryId is provided
      if (initialStoryId) {
        const index = filteredStories.findIndex(story => story.id === initialStoryId);
        if (index >= 0) {
          setInitialIndex(index);
        }
      }
    } catch (error) {
      console.error('Failed to load stories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStoryComplete = async (storyId: string) => {
    try {
      await storiesApi.viewStory(storyId);
    } catch (error) {
      console.error('Failed to mark story as viewed:', error);
    }
  };

  const handleClose = () => {
    setStories([]);
    setInitialIndex(0);
    onClose();
  };

  if (!visible || loading || stories.length === 0) {
    return null;
  }

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="fullScreen"
      statusBarTranslucent
    >
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      <View style={styles.container}>
        <StoryViewer
          stories={stories}
          initialIndex={initialIndex}
          onClose={handleClose}
          onStoryComplete={handleStoryComplete}
        />
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
});