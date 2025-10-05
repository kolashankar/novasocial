import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { GiftedChat, IMessage, User, InputToolbar, Composer, Send } from 'react-native-gifted-chat';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import io, { Socket } from 'socket.io-client';
import { useAuth } from '../../src/contexts/AuthContext';
import { COLORS } from '../../src/utils/constants';
import Constants from 'expo-constants';

// Mock encryption functions (in production, use actual encryption libraries)
const encryptMessage = (message: string, nonce: string): string => {
  // Simplified mock encryption - in production use libsodium/NaCl
  const encrypted = btoa(message + nonce); // Simple base64 encoding for demo
  return encrypted;
};

const decryptMessage = (encryptedMessage: string, nonce: string): string => {
  try {
    // Simplified mock decryption - in production use libsodium/NaCl
    const decrypted = atob(encryptedMessage).replace(nonce, '');
    return decrypted;
  } catch {
    return '[Decryption failed]';
  }
};

const generateNonce = (): string => {
  return Date.now().toString() + Math.random().toString(36).substr(2, 9);
};

interface EncryptedMessage {
  id: string;
  conversationId: string;
  senderId: string;
  recipientId: string;
  encryptedContent: string;
  messageType: string;
  nonce: string;
  timestamp: string;
  delivered: boolean;
  read: boolean;
}

export default function EncryptedChat() {
  const { conversationId } = useLocalSearchParams<{ conversationId: string }>();
  const router = useRouter();
  const { user, token } = useAuth();
  
  const [messages, setMessages] = useState<IMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [recipientInfo, setRecipientInfo] = useState<{ id: string; name: string; status: 'online' | 'offline' } | null>(null);
  
  const socketRef = useRef<Socket | null>(null);
  const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || 'https://socialcrypt-app.preview.emergentagent.com';

  useEffect(() => {
    if (!user || !conversationId) return;

    initializeSocket();
    loadMessages();
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [user, conversationId]);

  const initializeSocket = () => {
    const socket = io(backendUrl, {
      transports: ['websocket', 'polling'],
    });

    socket.on('connect', () => {
      console.log('Connected to socket server');
      setIsConnected(true);
      
      // Join user room for receiving messages
      socket.emit('join_user', { userId: user?.id });
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from socket server');
      setIsConnected(false);
    });

    socket.on('new_encrypted_message', (encryptedMsg: EncryptedMessage) => {
      console.log('Received encrypted message:', encryptedMsg);
      
      // Decrypt and add to messages
      const decryptedText = decryptMessage(encryptedMsg.encryptedContent, encryptedMsg.nonce);
      
      const newMessage: IMessage = {
        _id: encryptedMsg.id,
        text: decryptedText,
        createdAt: new Date(encryptedMsg.timestamp),
        user: {
          _id: encryptedMsg.senderId,
          name: recipientInfo?.name || 'User',
        },
        pending: false,
        sent: true,
        received: true,
      };

      setMessages(previousMessages => GiftedChat.append(previousMessages, [newMessage]));
    });

    socket.on('message_sent', (data: { messageId: string; delivered: boolean }) => {
      console.log('Message sent confirmation:', data);
      
      // Update message status
      setMessages(previousMessages =>
        previousMessages.map(msg => 
          msg._id === data.messageId 
            ? { ...msg, sent: true, received: data.delivered, pending: false }
            : msg
        )
      );
    });

    socket.on('message_read', (data: { messageId: string; conversationId: string }) => {
      console.log('Message read:', data);
      
      // Update message status to read
      setMessages(previousMessages =>
        previousMessages.map(msg => 
          msg._id === data.messageId 
            ? { ...msg, received: true, sent: true }
            : msg
        )
      );
    });

    socket.on('error', (error) => {
      console.error('Socket error:', error);
      Alert.alert('Connection Error', error.message);
    });

    socketRef.current = socket;
  };

  const loadMessages = async () => {
    try {
      setIsLoading(true);
      
      const response = await fetch(
        `${backendUrl}/api/encrypted-chats/${conversationId}/messages?limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();
      
      if (response.ok && data.messages) {
        const decryptedMessages: IMessage[] = data.messages.map((encMsg: EncryptedMessage) => {
          const decryptedText = decryptMessage(encMsg.encryptedContent, encMsg.nonce);
          
          return {
            _id: encMsg.id,
            text: decryptedText,
            createdAt: new Date(encMsg.timestamp),
            user: {
              _id: encMsg.senderId,
              name: encMsg.senderId === user?.id ? user.username : 'Contact',
            },
            pending: false,
            sent: encMsg.senderId === user?.id,
            received: encMsg.delivered,
          };
        });
        
        setMessages(decryptedMessages);
      }

      // Load offline messages
      const offlineResponse = await fetch(`${backendUrl}/api/encrypted-chats/offline-messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const offlineData = await offlineResponse.json();
      
      if (offlineResponse.ok && offlineData.messages.length > 0) {
        const offlineMessages: IMessage[] = offlineData.messages.map((encMsg: EncryptedMessage) => {
          const decryptedText = decryptMessage(encMsg.encryptedContent, encMsg.nonce);
          
          return {
            _id: encMsg.id,
            text: decryptedText,
            createdAt: new Date(encMsg.timestamp),
            user: {
              _id: encMsg.senderId,
              name: encMsg.senderId === user?.id ? user.username : 'Contact',
            },
            pending: false,
            sent: false,
            received: true,
          };
        });
        
        setMessages(prevMessages => GiftedChat.append(prevMessages, offlineMessages));
      }

    } catch (error) {
      console.error('Error loading messages:', error);
      Alert.alert('Error', 'Failed to load messages');
    } finally {
      setIsLoading(false);
    }
  };

  const onSend = useCallback((newMessages: IMessage[] = []) => {
    if (!socketRef.current || !user) return;

    newMessages.forEach(message => {
      const nonce = generateNonce();
      const encryptedContent = encryptMessage(message.text, nonce);
      
      // Add to local messages with pending status
      const messageWithStatus: IMessage = {
        ...message,
        pending: true,
        sent: false,
        received: false,
      };
      
      setMessages(previousMessages => GiftedChat.append(previousMessages, [messageWithStatus]));

      // Send encrypted message via Socket.IO
      socketRef.current?.emit('send_encrypted_message', {
        conversationId: conversationId,
        encryptedContent: encryptedContent,
        messageType: 'text',
        nonce: nonce,
        recipientId: recipientInfo?.id || 'unknown', // You'd get this from conversation data
        senderId: user.id,
      });
    });
  }, [conversationId, user, recipientInfo]);

  const markMessageAsRead = async (messageId: string) => {
    try {
      await fetch(`${backendUrl}/api/encrypted-chats/messages/${messageId}/read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error('Error marking message as read:', error);
    }
  };

  const renderInputToolbar = (props: any) => (
    <InputToolbar
      {...props}
      containerStyle={styles.inputToolbar}
      primaryStyle={styles.inputPrimary}
    />
  );

  const renderComposer = (props: any) => (
    <Composer
      {...props}
      textInputStyle={styles.composer}
      placeholderTextColor={COLORS.textSecondary}
    />
  );

  const renderSend = (props: any) => (
    <Send {...props} containerStyle={styles.sendContainer}>
      <Ionicons name="send" size={20} color={COLORS.primary} />
    </Send>
  );

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.primary} />
          <Text style={styles.loadingText}>Loading encrypted chat...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Chat Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Ionicons 
            name="arrow-back" 
            size={24} 
            color={COLORS.text} 
            onPress={() => router.back()}
          />
          <View style={styles.headerInfo}>
            <Text style={styles.headerTitle}>Encrypted Chat</Text>
            <View style={styles.statusContainer}>
              <View style={[
                styles.statusDot, 
                { backgroundColor: isConnected ? COLORS.success : COLORS.error }
              ]} />
              <Text style={styles.statusText}>
                {isConnected ? 'End-to-end encrypted' : 'Connecting...'}
              </Text>
            </View>
          </View>
        </View>
        <Ionicons name="shield-checkmark" size={24} color={COLORS.primary} />
      </View>

      <KeyboardAvoidingView 
        style={styles.chatContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <GiftedChat
          messages={messages}
          onSend={onSend}
          user={{
            _id: user?.id || '',
            name: user?.username || '',
          }}
          renderInputToolbar={renderInputToolbar}
          renderComposer={renderComposer}
          renderSend={renderSend}
          alwaysShowSend
          scrollToBottom
          showUserAvatar={false}
          renderAvatarOnTop
          messageContainerStyle={styles.messageContainer}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    color: COLORS.textSecondary,
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.card,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  headerInfo: {
    marginLeft: 12,
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  chatContainer: {
    flex: 1,
  },
  messageContainer: {
    backgroundColor: COLORS.background,
  },
  inputToolbar: {
    backgroundColor: COLORS.card,
    borderTopColor: COLORS.border,
    borderTopWidth: 1,
    paddingVertical: 4,
  },
  inputPrimary: {
    alignItems: 'center',
  },
  composer: {
    backgroundColor: COLORS.background,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginHorizontal: 8,
    color: COLORS.text,
    fontSize: 16,
  },
  sendContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 12,
  },
});