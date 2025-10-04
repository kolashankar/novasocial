import React from 'react';
import { View, Text, StyleSheet, Image, Pressable } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

export interface MessageBubbleProps {
  message: {
    id: string;
    text?: string;
    messageType: string;
    media?: string;
    createdAt: string;
    sender: {
      id: string;
      username: string;
      profileImage?: string;
    };
    readBy: Array<{
      userId: string;
      readAt: string;
    }>;
  };
  isOwn: boolean;
  currentUserId: string;
  onMediaPress?: (media: string) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isOwn,
  currentUserId,
  onMediaPress,
}) => {
  const isRead = message.readBy.some(r => r.userId !== currentUserId);
  
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMedia = () => {
    if (!message.media) return null;
    
    return (
      <Pressable onPress={() => onMediaPress?.(message.media!)}>
        <Image 
          source={{ uri: message.media }}
          style={styles.media}
          resizeMode="cover"
        />
      </Pressable>
    );
  };

  return (
    <View style={[styles.container, isOwn ? styles.ownMessage : styles.otherMessage]}>
      {!isOwn && (
        <Image
          source={{ 
            uri: message.sender.profileImage || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==' 
          }}
          style={styles.avatar}
        />
      )}
      
      {isOwn ? (
        <LinearGradient
          colors={['#667eea', '#764ba2']}
          style={styles.bubble}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          {renderMedia()}
          {message.text && <Text style={styles.ownText}>{message.text}</Text>}
          <View style={styles.messageFooter}>
            <Text style={styles.timeOwn}>{formatTime(message.createdAt)}</Text>
            <Text style={[styles.readStatus, { color: isRead ? '#4ade80' : '#94a3b8' }]}>✓</Text>
          </View>
        </LinearGradient>
      ) : (
        <View style={[styles.bubble, styles.otherBubble]}>
          {renderMedia()}
          {message.text && <Text style={styles.otherText}>{message.text}</Text>}
          <Text style={styles.timeOther}>{formatTime(message.createdAt)}</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    marginVertical: 4,
    paddingHorizontal: 16,
    alignItems: 'flex-end',
  },
  ownMessage: {
    justifyContent: 'flex-end',
  },
  otherMessage: {
    justifyContent: 'flex-start',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    marginRight: 8,
  },
  bubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 16,
    minWidth: 60,
  },
  otherBubble: {
    backgroundColor: '#f1f5f9',
    borderBottomLeftRadius: 4,
  },
  ownText: {
    color: '#ffffff',
    fontSize: 16,
    lineHeight: 20,
  },
  otherText: {
    color: '#1e293b',
    fontSize: 16,
    lineHeight: 20,
  },
  media: {
    width: 200,
    height: 200,
    borderRadius: 12,
    marginBottom: 8,
  },
  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 4,
  },
  timeOwn: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 12,
    marginRight: 4,
  },
  timeOther: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  readStatus: {
    fontSize: 12,
    fontWeight: 'bold',
  },
});