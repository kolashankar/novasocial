import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  FlatList,
  Image,
  Modal,
  SafeAreaView,
  Alert,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

const { width, height } = Dimensions.get('window');

interface User {
  id: string;
  username: string;
  fullName: string;
  profileImage?: string;
}

interface TagPosition {
  x: number;
  y: number;
}

interface UserTag {
  userId: string;
  user: User;
  position: TagPosition;
}

interface TagPeopleOverlayProps {
  visible: boolean;
  onClose: () => void;
  mediaUri: string;
  mediaType: 'image' | 'video';
  onTagsConfirmed: (tags: UserTag[]) => void;
  existingTags?: UserTag[];
}

export const TagPeopleOverlay: React.FC<TagPeopleOverlayProps> = ({
  visible,
  onClose,
  mediaUri,
  mediaType,
  onTagsConfirmed,
  existingTags = []
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [tags, setTags] = useState<UserTag[]>(existingTags);
  const [showSearch, setShowSearch] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isPlacing, setIsPlacing] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (searchQuery.length >= 2) {
      searchUsers(searchQuery);
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const searchUsers = async (query: string) => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/search/tags?q=${encodeURIComponent(query)}&type=users&limit=10`);
      const data = await response.json();
      setSearchResults(data.users || []);
    } catch (error) {
      console.error('Error searching users:', error);
      Alert.alert('Error', 'Failed to search users');
    } finally {
      setLoading(false);
    }
  };

  const handleUserSelect = (user: User) => {
    if (tags.find(tag => tag.userId === user.id)) {
      Alert.alert('Already Tagged', `${user.username} is already tagged in this post`);
      return;
    }

    if (tags.length >= 10) {
      Alert.alert('Tag Limit', 'You can only tag up to 10 people in a post');
      return;
    }

    setSelectedUser(user);
    setIsPlacing(true);
    setShowSearch(false);
  };

  const handleMediaPress = (event: any) => {
    if (!isPlacing || !selectedUser) return;

    const { locationX, locationY } = event.nativeEvent;
    
    // Convert to relative coordinates (0-1)
    const relativeX = locationX / width;
    const relativeY = locationY / (height * 0.7); // Approximate media container height

    const newTag: UserTag = {
      userId: selectedUser.id,
      user: selectedUser,
      position: { x: relativeX, y: relativeY }
    };

    setTags(prev => [...prev, newTag]);
    setSelectedUser(null);
    setIsPlacing(false);
  };

  const removeTag = (tagId: string) => {
    setTags(prev => prev.filter(tag => tag.userId !== tagId));
  };

  const handleConfirm = () => {
    onTagsConfirmed(tags);
    onClose();
  };

  const renderSearchResult = ({ item }: { item: User }) => (
    <TouchableOpacity
      style={styles.searchResultItem}
      onPress={() => handleUserSelect(item)}
    >
      <Image
        source={{
          uri: item.profileImage || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        }}
        style={styles.searchResultAvatar}
      />
      <View style={styles.searchResultInfo}>
        <Text style={styles.searchResultUsername}>{item.username}</Text>
        <Text style={styles.searchResultFullName}>{item.fullName}</Text>
      </View>
    </TouchableOpacity>
  );

  const renderTag = (tag: UserTag, index: number) => {
    const left = tag.position.x * width;
    const top = tag.position.y * height * 0.7;

    return (
      <View
        key={tag.userId}
        style={[
          styles.tagIndicator,
          { left: left - 12, top: top - 12 }
        ]}
      >
        <TouchableOpacity
          style={styles.tagButton}
          onPress={() => removeTag(tag.userId)}
        >
          <View style={styles.tagDot} />
        </TouchableOpacity>
        <View style={styles.tagLabel}>
          <Text style={styles.tagText}>@{tag.user.username}</Text>
          <TouchableOpacity
            style={styles.removeTagButton}
            onPress={() => removeTag(tag.userId)}
          >
            <Ionicons name="close" size={16} color="#ffffff" />
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="overFullScreen"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose}>
            <Ionicons name="close" size={24} color="#ffffff" />
          </TouchableOpacity>
          <Text style={styles.title}>Tag People</Text>
          <TouchableOpacity onPress={handleConfirm}>
            <Text style={styles.doneButton}>Done</Text>
          </TouchableOpacity>
        </View>

        {/* Instructions */}
        <View style={styles.instructions}>
          <Text style={styles.instructionText}>
            {isPlacing 
              ? `Tap on the ${mediaType} to tag @${selectedUser?.username}`
              : `${tags.length}/10 people tagged. Tap + to add more.`
            }
          </Text>
        </View>

        {/* Media Container */}
        <View style={styles.mediaContainer}>
          <TouchableOpacity
            activeOpacity={1}
            onPress={handleMediaPress}
            disabled={!isPlacing}
          >
            <Image
              source={{ uri: mediaUri }}
              style={styles.media}
              resizeMode="contain"
            />
            {/* Render existing tags */}
            {tags.map((tag, index) => renderTag(tag, index))}
            
            {/* Placement cursor */}
            {isPlacing && (
              <View style={styles.placementCursor}>
                <View style={styles.cursorDot} />
                <Text style={styles.cursorText}>Tap to place tag</Text>
              </View>
            )}
          </TouchableOpacity>
        </View>

        {/* Search Toggle Button */}
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => setShowSearch(!showSearch)}
        >
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.addButtonGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Ionicons name="add" size={24} color="#ffffff" />
            <Text style={styles.addButtonText}>Add Person</Text>
          </LinearGradient>
        </TouchableOpacity>

        {/* Search Overlay */}
        {showSearch && (
          <View style={styles.searchOverlay}>
            <View style={styles.searchContainer}>
              <View style={styles.searchHeader}>
                <Text style={styles.searchTitle}>Search People</Text>
                <TouchableOpacity onPress={() => setShowSearch(false)}>
                  <Ionicons name="close" size={24} color="#1e293b" />
                </TouchableOpacity>
              </View>
              
              <View style={styles.searchInputContainer}>
                <Ionicons name="search" size={20} color="#94a3b8" />
                <TextInput
                  style={styles.searchInput}
                  placeholder="Search by username or name..."
                  placeholderTextColor="#94a3b8"
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                  autoFocus
                />
              </View>

              <FlatList
                data={searchResults}
                keyExtractor={(item) => item.id}
                renderItem={renderSearchResult}
                showsVerticalScrollIndicator={false}
                style={styles.searchResults}
                ListEmptyComponent={() => (
                  <View style={styles.emptyState}>
                    <Ionicons name="search" size={48} color="#94a3b8" />
                    <Text style={styles.emptyText}>
                      {searchQuery.length < 2 
                        ? 'Type at least 2 characters to search'
                        : loading
                          ? 'Searching...'
                          : 'No users found'
                      }
                    </Text>
                  </View>
                )}
              />
            </View>
          </View>
        )}
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  doneButton: {
    fontSize: 16,
    fontWeight: '600',
    color: '#667eea',
  },
  instructions: {
    padding: 16,
    backgroundColor: '#1f2937',
  },
  instructionText: {
    fontSize: 14,
    color: '#d1d5db',
    textAlign: 'center',
  },
  mediaContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  media: {
    width: width,
    height: height * 0.7,
  },
  tagIndicator: {
    position: 'absolute',
    alignItems: 'center',
  },
  tagButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#667eea',
    borderWidth: 2,
    borderColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  tagDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#ffffff',
  },
  tagLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 4,
  },
  tagText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
    marginRight: 4,
  },
  removeTagButton: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: '#ef4444',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placementCursor: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -12 }, { translateY: -12 }],
    alignItems: 'center',
  },
  cursorDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#fbbf24',
    borderWidth: 2,
    borderColor: '#ffffff',
  },
  cursorText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fbbf24',
    marginTop: 4,
    textAlign: 'center',
  },
  addButton: {
    margin: 16,
  },
  addButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 25,
  },
  addButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginLeft: 8,
  },
  searchOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  searchContainer: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: height * 0.8,
  },
  searchHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  searchTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#f8fafc',
    borderRadius: 25,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#1e293b',
  },
  searchResults: {
    maxHeight: height * 0.5,
  },
  searchResultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  searchResultAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
    backgroundColor: '#f1f5f9',
  },
  searchResultInfo: {
    flex: 1,
  },
  searchResultUsername: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 2,
  },
  searchResultFullName: {
    fontSize: 14,
    color: '#64748b',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 14,
    color: '#94a3b8',
    textAlign: 'center',
    marginTop: 8,
  },
});