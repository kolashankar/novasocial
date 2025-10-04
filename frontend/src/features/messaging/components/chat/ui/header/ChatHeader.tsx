import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export interface ChatHeaderProps {
  conversation: {
    id: string;
    name?: string;
    isGroup: boolean;
    participants: Array<{
      id: string;
      username: string;
      fullName: string;
      profileImage?: string;
    }>;
  };
  currentUserId: string;
  onBack: () => void;
  onProfile: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  conversation,
  currentUserId,
  onBack,
  onProfile,
}) => {
  const insets = useSafeAreaInsets();
  
  const getDisplayInfo = () => {
    if (conversation.isGroup) {
      return {
        name: conversation.name || 'Group Chat',
        subtitle: `${conversation.participants.length} members`,
        image: null,
      };
    } else {
      const otherUser = conversation.participants.find(p => p.id !== currentUserId);
      return {
        name: otherUser?.fullName || otherUser?.username || 'Unknown',
        subtitle: 'Online',
        image: otherUser?.profileImage,
      };
    }
  };

  const displayInfo = getDisplayInfo();

  return (
    <LinearGradient
      colors={['#667eea', '#764ba2']}
      style={[styles.container, { paddingTop: insets.top }]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
    >
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={onBack}>
          <Ionicons name="chevron-back" size={24} color="#ffffff" />
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.profileSection} onPress={onProfile}>
          <Image
            source={{ 
              uri: displayInfo.image || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==' 
            }}
            style={styles.avatar}
          />
          <View style={styles.textContainer}>
            <Text style={styles.name} numberOfLines={1}>
              {displayInfo.name}
            </Text>
            <Text style={styles.subtitle} numberOfLines={1}>
              {displayInfo.subtitle}
            </Text>
          </View>
        </TouchableOpacity>
        
        <View style={styles.actions}>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="videocam" size={24} color="#ffffff" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="call" size={24} color="#ffffff" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="ellipsis-vertical" size={20} color="#ffffff" />
          </TouchableOpacity>
        </View>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 4,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 4,
    marginRight: 8,
  },
  profileSection: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  textContainer: {
    flex: 1,
  },
  name: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  subtitle: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    marginTop: 2,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  actionButton: {
    padding: 8,
    marginLeft: 4,
  },
});