import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  StatusBar,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../src/contexts/AuthContext';
import { ReelVideo } from '../../src/components/reels/ReelVideo';
import { COLORS } from '../../src/utils/constants';
import { apiService } from '../../src/services/api';

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

export default function Reels() {
  const [reels, setReels] = useState<Reel[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  
  const { token, user } = useAuth();
  const flashListRef = useRef<FlashList<Reel>>(null);

  // Mock reels data for now (since we don't have video upload yet)
  const mockReels: Reel[] = [
    {
      id: '1',
      author: {
        id: 'user1',
        username: 'traveler_jane',
        fullName: 'Jane Doe',
        profileImage: undefined,
      },
      caption: 'Beautiful sunset at the beach! 🌅 #sunset #beach #travel',
      videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
      likes: [],
      likesCount: 1250,
      commentsCount: 87,
      createdAt: new Date().toISOString(),
    },
    {
      id: '2', 
      author: {
        id: 'user2',
        username: 'chef_mike',
        fullName: 'Mike Chen',
        profileImage: undefined,
      },
      caption: 'Making the perfect pasta! 🍝 Recipe in bio #cooking #pasta #food',
      videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
      likes: [],
      likesCount: 3420,
      commentsCount: 156,
      createdAt: new Date().toISOString(),
    },
    {
      id: '3',
      author: {
        id: 'user3',
        username: 'fitness_guru',
        fullName: 'Alex Johnson',
        profileImage: undefined,
      },
      caption: 'Morning workout routine 💪 Let\'s get stronger together! #fitness #workout #motivation',
      videoUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
      likes: [],
      likesCount: 892,
      commentsCount: 45,
      createdAt: new Date().toISOString(),
    },
  ];

  useEffect(() => {
    // Load mock reels for now
    setReels(mockReels);
  }, []);

  const handleLike = (reelId: string, liked: boolean) => {
    setReels(prev => prev.map(reel => {
      if (reel.id === reelId) {
        const newLikes = liked 
          ? [...reel.likes, user?.id || ''].filter((id, index, arr) => arr.indexOf(id) === index)
          : reel.likes.filter(id => id !== user?.id);
        return {
          ...reel,
          likes: newLikes,
          likesCount: newLikes.length,
        };
      }
      return reel;
    }));
  };

  const handleComment = (reelId: string) => {
    // Navigate to comments screen
    Alert.alert('Comments', 'Comments feature coming soon!');
  };

  const handleShare = (reelId: string) => {
    Alert.alert('Share', 'Share functionality coming soon!');
  };

  const handleFollow = (userId: string) => {
    Alert.alert('Follow', 'Follow functionality coming soon!');
  };

  const onViewableItemsChanged = ({ viewableItems }: any) => {
    if (viewableItems.length > 0) {
      setCurrentIndex(viewableItems[0].index || 0);
    }
  };

  const viewabilityConfig = {
    itemVisiblePercentThreshold: 80,
  };

  const renderReel = ({ item, index }: { item: Reel; index: number }) => (
    <ReelVideo
      reel={item}
      isActive={index === currentIndex}
      onLike={handleLike}
      onComment={handleComment}
      onShare={handleShare}
      onFollow={handleFollow}
    />
  );

  const getItemLayout = (data: any, index: number) => ({
    length: 800, // Approximate reel height
    offset: 800 * index,
    index,
  });

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      
      {reels.length > 0 ? (
        <FlashList
          ref={flashListRef}
          data={reels}
          renderItem={renderReel}
          estimatedItemSize={800}
          pagingEnabled
          showsVerticalScrollIndicator={false}
          onViewableItemsChanged={onViewableItemsChanged}
          viewabilityConfig={viewabilityConfig}
          getItemLayout={getItemLayout}
          decelerationRate="fast"
          snapToInterval={800}
          snapToAlignment="start"
        />
      ) : (
        <View style={styles.emptyContainer}>
          {/* Will show loading or empty state */}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});