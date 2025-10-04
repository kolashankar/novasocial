import { useEffect } from 'react';
import { router } from 'expo-router';

// This is a dummy tab that redirects to the actual create post screen
export default function CreatePostTab() {
  useEffect(() => {
    router.push('/create-post');
  }, []);

  return null;
}