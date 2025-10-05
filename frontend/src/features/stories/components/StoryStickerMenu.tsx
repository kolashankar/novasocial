import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  SafeAreaView,
  FlatList,
  TextInput,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

interface StickerOption {
  id: string;
  name: string;
  icon: string;
  category: string;
  color: string;
}

interface MusicItem {
  id: string;
  title: string;
  artist: string;
  duration: number;
  genre?: string;
  category: string;
}

interface GifItem {
  id: string;
  title: string;
  url: string;
  thumbnailUrl: string;
  category: string;
}

interface ColorPalette {
  id: string;
  name: string;
  colors: string[];
  category: string;
}

interface StoryStickerMenuProps {
  visible: boolean;
  onClose: () => void;
  onStickerAdd: (stickerData: any) => void;
  storyId: string;
}

export const StoryStickerMenu: React.FC<StoryStickerMenuProps> = ({
  visible,
  onClose,
  onStickerAdd,
  storyId
}) => {
  const [activeCategory, setActiveCategory] = useState<string>('main');
  const [searchQuery, setSearchQuery] = useState('');
  const [musicLibrary, setMusicLibrary] = useState<MusicItem[]>([]);
  const [gifLibrary, setGifLibrary] = useState<GifItem[]>([]);
  const [colorPalettes, setColorPalettes] = useState<ColorPalette[]>([]);
  const [loading, setLoading] = useState(false);

  const stickerCategories: StickerOption[] = [
    // Basic Stickers
    { id: 'location', name: 'Location', icon: 'location', category: 'main', color: '#ef4444' },
    { id: 'mention', name: 'Mention', icon: 'at', category: 'main', color: '#3b82f6' },
    { id: 'music', name: 'Music', icon: 'musical-notes', category: 'main', color: '#8b5cf6' },
    { id: 'photo', name: 'Photo', icon: 'image', category: 'main', color: '#06b6d4' },
    { id: 'whatsapp', name: 'WhatsApp', icon: 'logo-whatsapp', category: 'main', color: '#10b981' },
    { id: 'gif', name: 'GIF', icon: 'happy', category: 'main', color: '#f59e0b' },
    
    // Creative Tools
    { id: 'frame', name: 'Frame', icon: 'crop', category: 'creative', color: '#84cc16' },
    { id: 'question', name: 'Question', icon: 'help-circle', category: 'creative', color: '#ec4899' },
    { id: 'poll', name: 'Poll', icon: 'bar-chart', category: 'creative', color: '#6366f1' },
    { id: 'quiz', name: 'Quiz', icon: 'school', category: 'creative', color: '#f97316' },
    { id: 'countdown', name: 'Countdown', icon: 'timer', category: 'creative', color: '#dc2626' },
    { id: 'hashtag', name: 'Hashtag', icon: 'pricetag', category: 'creative', color: '#059669' },
    
    // Interactive Elements
    { id: 'add_yours', name: 'Add Yours', icon: 'add-circle', category: 'interactive', color: '#7c3aed' },
    { id: 'like_percentage', name: 'Like %', icon: 'heart', category: 'interactive', color: '#e11d48' },
    { id: 'slider', name: 'Slider', icon: 'options', category: 'interactive', color: '#0891b2' },
    { id: 'notify', name: 'Notify', icon: 'notifications', category: 'interactive', color: '#ea580c' },
    
    // E-commerce & Links
    { id: 'link', name: 'Link', icon: 'link', category: 'commerce', color: '#4338ca' },
    { id: 'shop', name: 'Shop', icon: 'storefront', category: 'commerce', color: '#16a34a' },
    { id: 'order', name: 'Get Order', icon: 'bag', category: 'commerce', color: '#be185d' },
  ];

  const categories = [
    { id: 'main', name: 'Popular', icon: 'star' },
    { id: 'creative', name: 'Creative', icon: 'color-palette' },
    { id: 'interactive', name: 'Interactive', icon: 'chatbubbles' },
    { id: 'commerce', name: 'Commerce', icon: 'storefront' },
    { id: 'text', name: 'Text', icon: 'text' },
    { id: 'colors', name: 'Colors', icon: 'color-fill' },
  ];

  useEffect(() => {
    if (visible) {
      loadCreativeResources();
    }
  }, [visible]);

  const loadCreativeResources = async () => {
    setLoading(true);
    try {
      // Load music library
      const musicResponse = await fetch('/api/creative/music');
      const musicData = await musicResponse.json();
      setMusicLibrary(musicData);

      // Load GIF library
      const gifResponse = await fetch('/api/creative/gifs');
      const gifData = await gifResponse.json();
      setGifLibrary(gifData);

      // Load color palettes
      const colorResponse = await fetch('/api/creative/colors');
      const colorData = await colorResponse.json();
      setColorPalettes(colorData);
    } catch (error) {
      console.error('Error loading creative resources:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStickerSelect = (sticker: StickerOption) => {
    const position = {
      x: 0.5,
      y: 0.5,
      rotation: 0,
      scale: 1
    };

    switch (sticker.id) {
      case 'location':
        handleLocationSticker(position);
        break;
      case 'mention':
        handleMentionSticker(position);
        break;
      case 'music':
        setActiveCategory('music');
        break;
      case 'gif':
        setActiveCategory('gif');
        break;
      case 'question':
        handleQuestionSticker(position);
        break;
      case 'poll':
        handlePollSticker(position);
        break;
      case 'countdown':
        handleCountdownSticker(position);
        break;
      case 'add_yours':
        handleAddYoursSticker(position);
        break;
      default:
        handleGenericSticker(sticker, position);
    }
  };

  const handleLocationSticker = (position: any) => {
    // This would typically open a location picker
    Alert.prompt(
      'Add Location',
      'Enter location name:',
      (locationName) => {
        if (locationName) {
          const stickerData = {
            type: 'location',
            data: {
              locationName,
              displayName: locationName,
              coordinates: { lat: 40.7128, lng: -74.0060 } // Mock NYC coordinates
            },
            position
          };
          onStickerAdd(stickerData);
          onClose();
        }
      }
    );
  };

  const handleMentionSticker = (position: any) => {
    Alert.prompt(
      'Mention Someone',
      'Enter username:',
      (username) => {
        if (username) {
          const stickerData = {
            type: 'mention',
            data: {
              username: username.startsWith('@') ? username : `@${username}`,
              userId: 'mock_user_id' // In real app, would search for actual user
            },
            position
          };
          onStickerAdd(stickerData);
          onClose();
        }
      }
    );
  };

  const handleQuestionSticker = (position: any) => {
    Alert.prompt(
      'Ask a Question',
      'What do you want to ask?',
      (question) => {
        if (question) {
          const stickerData = {
            type: 'question',
            data: {
              question,
              responses: []
            },
            position,
            isInteractive: true
          };
          onStickerAdd(stickerData);
          onClose();
        }
      }
    );
  };

  const handlePollSticker = (position: any) => {
    const stickerData = {
      type: 'poll',
      data: {
        question: 'Which do you prefer?',
        options: ['Option A', 'Option B'],
        responses: []
      },
      position,
      isInteractive: true
    };
    onStickerAdd(stickerData);
    onClose();
  };

  const handleCountdownSticker = (position: any) => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const stickerData = {
      type: 'countdown',
      data: {
        title: 'Countdown',
        targetDate: tomorrow.toISOString(),
        isActive: true
      },
      position,
      expiresAt: tomorrow.toISOString()
    };
    onStickerAdd(stickerData);
    onClose();
  };

  const handleAddYoursSticker = (position: any) => {
    Alert.prompt(
      'Add Yours Template',
      'Create a prompt for others to follow:',
      (promptText) => {
        if (promptText) {
          const stickerData = {
            type: 'add_yours',
            data: {
              promptText,
              template: { textStyle: 'bold', backgroundColor: '#667eea' },
              participants: []
            },
            position,
            isInteractive: true
          };
          onStickerAdd(stickerData);
          onClose();
        }
      }
    );
  };

  const handleGenericSticker = (sticker: StickerOption, position: any) => {
    const stickerData = {
      type: sticker.id,
      data: {
        name: sticker.name,
        color: sticker.color,
        icon: sticker.icon
      },
      position
    };
    onStickerAdd(stickerData);
    onClose();
  };

  const handleMusicSelect = (music: MusicItem) => {
    const position = {
      x: 0.5,
      y: 0.8, // Bottom of screen
      rotation: 0,
      scale: 1
    };

    const stickerData = {
      type: 'music',
      data: {
        title: music.title,
        artist: music.artist,
        duration: music.duration,
        musicId: music.id
      },
      position
    };
    onStickerAdd(stickerData);
    onClose();
  };

  const handleGifSelect = (gif: GifItem) => {
    const position = {
      x: 0.5,
      y: 0.5,
      rotation: 0,
      scale: 1
    };

    const stickerData = {
      type: 'gif',
      data: {
        title: gif.title,
        url: gif.url,
        thumbnailUrl: gif.thumbnailUrl,
        gifId: gif.id
      },
      position
    };
    onStickerAdd(stickerData);
    onClose();
  };

  const handleColorSelect = (color: string) => {
    // This would be used for text styling
    // For now, just close the menu
    Alert.alert('Color Selected', `Selected color: ${color}`);
  };

  const renderStickerGrid = () => {
    const filteredStickers = stickerCategories.filter(sticker => 
      activeCategory === 'main' || sticker.category === activeCategory
    );

    return (
      <ScrollView style={styles.stickerGrid} showsVerticalScrollIndicator={false}>
        <View style={styles.gridContainer}>
          {filteredStickers.map((sticker) => (
            <TouchableOpacity
              key={sticker.id}
              style={styles.stickerItem}
              onPress={() => handleStickerSelect(sticker)}
            >
              <LinearGradient
                colors={[sticker.color, `${sticker.color}CC`]}
                style={styles.stickerIconContainer}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name={sticker.icon as any} size={28} color="#ffffff" />
              </LinearGradient>
              <Text style={styles.stickerName}>{sticker.name}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    );
  };

  const renderMusicLibrary = () => (
    <View style={styles.libraryContainer}>
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#94a3b8" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search music..."
          placeholderTextColor="#94a3b8"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>
      <FlatList
        data={musicLibrary.filter(music => 
          music.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          music.artist.toLowerCase().includes(searchQuery.toLowerCase())
        )}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.musicItem}
            onPress={() => handleMusicSelect(item)}
          >
            <View style={styles.musicIcon}>
              <Ionicons name="musical-note" size={24} color="#8b5cf6" />
            </View>
            <View style={styles.musicInfo}>
              <Text style={styles.musicTitle}>{item.title}</Text>
              <Text style={styles.musicArtist}>{item.artist}</Text>
            </View>
            <Text style={styles.musicDuration}>{item.duration}s</Text>
          </TouchableOpacity>
        )}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );

  const renderGifLibrary = () => (
    <View style={styles.libraryContainer}>
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#94a3b8" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search GIFs..."
          placeholderTextColor="#94a3b8"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>
      <FlatList
        data={gifLibrary.filter(gif => 
          gif.title.toLowerCase().includes(searchQuery.toLowerCase())
        )}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.gifItem}
            onPress={() => handleGifSelect(item)}
          >
            <Image source={{ uri: item.thumbnailUrl }} style={styles.gifThumbnail} />
            <Text style={styles.gifTitle}>{item.title}</Text>
          </TouchableOpacity>
        )}
        numColumns={2}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );

  const renderColorPalettes = () => (
    <ScrollView style={styles.libraryContainer} showsVerticalScrollIndicator={false}>
      {colorPalettes.map((palette) => (
        <View key={palette.id} style={styles.paletteContainer}>
          <Text style={styles.paletteName}>{palette.name}</Text>
          <View style={styles.colorRow}>
            {palette.colors.map((color, index) => (
              <TouchableOpacity
                key={index}
                style={[styles.colorSwatch, { backgroundColor: color }]}
                onPress={() => handleColorSelect(color)}
              />
            ))}
          </View>
        </View>
      ))}
    </ScrollView>
  );

  const renderContent = () => {
    if (loading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>Loading creative tools...</Text>
        </View>
      );
    }

    switch (activeCategory) {
      case 'music':
        return renderMusicLibrary();
      case 'gif':
        return renderGifLibrary();
      case 'colors':
        return renderColorPalettes();
      default:
        return renderStickerGrid();
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => setActiveCategory('main')}>
            <Ionicons name="chevron-back" size={24} color="#1e293b" />
          </TouchableOpacity>
          <Text style={styles.title}>
            {activeCategory === 'music' ? 'Music Library' :
             activeCategory === 'gif' ? 'GIF Library' :
             activeCategory === 'colors' ? 'Color Palettes' :
             'Story Stickers'}
          </Text>
          <TouchableOpacity onPress={onClose}>
            <Ionicons name="close" size={24} color="#1e293b" />
          </TouchableOpacity>
        </View>

        {/* Category Tabs */}
        {activeCategory !== 'music' && activeCategory !== 'gif' && activeCategory !== 'colors' && (
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            style={styles.categoryTabs}
            contentContainerStyle={styles.categoryTabsContent}
          >
            {categories.map((category) => (
              <TouchableOpacity
                key={category.id}
                style={[
                  styles.categoryTab,
                  activeCategory === category.id && styles.activeCategoryTab
                ]}
                onPress={() => setActiveCategory(category.id)}
              >
                <Ionicons 
                  name={category.icon as any} 
                  size={20} 
                  color={activeCategory === category.id ? '#ffffff' : '#64748b'} 
                />
                <Text style={[
                  styles.categoryTabText,
                  activeCategory === category.id && styles.activeCategoryTabText
                ]}>
                  {category.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}

        {/* Content */}
        <View style={styles.content}>
          {renderContent()}
        </View>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1e293b',
  },
  categoryTabs: {
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  categoryTabsContent: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  categoryTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: '#f8fafc',
  },
  activeCategoryTab: {
    backgroundColor: '#667eea',
  },
  categoryTabText: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '500',
    color: '#64748b',
  },
  activeCategoryTabText: {
    color: '#ffffff',
  },
  content: {
    flex: 1,
  },
  stickerGrid: {
    flex: 1,
    padding: 16,
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  stickerItem: {
    width: '30%',
    alignItems: 'center',
    marginBottom: 24,
  },
  stickerIconContainer: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  stickerName: {
    fontSize: 12,
    fontWeight: '500',
    color: '#64748b',
    textAlign: 'center',
  },
  libraryContainer: {
    flex: 1,
    padding: 16,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#f8fafc',
    borderRadius: 25,
    marginBottom: 16,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#1e293b',
  },
  musicItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  musicIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  musicInfo: {
    flex: 1,
  },
  musicTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 2,
  },
  musicArtist: {
    fontSize: 14,
    color: '#64748b',
  },
  musicDuration: {
    fontSize: 12,
    color: '#94a3b8',
  },
  gifItem: {
    width: '48%',
    marginBottom: 16,
    marginRight: '2%',
  },
  gifThumbnail: {
    width: '100%',
    height: 120,
    borderRadius: 8,
    marginBottom: 8,
  },
  gifTitle: {
    fontSize: 12,
    fontWeight: '500',
    color: '#64748b',
    textAlign: 'center',
  },
  paletteContainer: {
    marginBottom: 24,
  },
  paletteName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: 12,
  },
  colorRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  colorSwatch: {
    width: 50,
    height: 50,
    borderRadius: 25,
    borderWidth: 2,
    borderColor: '#ffffff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 12,
  },
});