import React, { useState } from 'react';
import { useLocalSearchParams } from 'expo-router';
import { StoriesViewer } from '../../src/features/stories/components/viewer/StoriesViewer';

export default function AuthorStoriesScreen() {
  const { authorId, storyId } = useLocalSearchParams<{ authorId: string; storyId?: string }>();
  const [visible, setVisible] = useState(true);

  const handleClose = () => {
    setVisible(false);
    // Navigate back or to a specific route
  };

  return (
    <StoriesViewer
      visible={visible}
      authorId={authorId}
      initialStoryId={storyId}
      onClose={handleClose}
    />
  );
}