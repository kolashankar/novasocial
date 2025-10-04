import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  StyleSheet,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { ChatHeader } from './ui/header/ChatHeader';
import { MessagesList } from './ui/messages/MessagesList';
import { ChatInput } from './ui/input/ChatInput';
import { useSocket } from '../../services/socketService';
import { chatApi } from '../../services/chatApi';
import { useAuthContext } from '../../../../contexts/AuthContext';

export interface Message {
  id: string;
  conversationId: string;
  text?: string;
  messageType: string;
  media?: string;
  createdAt: string;
  sender: {
    id: string;
    username: string;
    fullName: string;
    profileImage?: string;
  };
  readBy: Array<{
    userId: string;
    readAt: string;
  }>;
}

export interface Conversation {
  id: string;
  name?: string;
  isGroup: boolean;
  participants: Array<{
    id: string;
    username: string;
    fullName: string;
    profileImage?: string;
  }>;
}

export const ChatScreen: React.FC = () => {
  const { conversationId } = useLocalSearchParams<{ conversationId: string }>();
  const { user } = useAuthContext();
  const { socket, joinConversation, leaveConversation } = useSocket();
  
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);

  const loadConversation = useCallback(async () => {
    if (!conversationId || !user) return;
    
    try {
      const conversations = await chatApi.getConversations();
      const conv = conversations.find(c => c.id === conversationId);
      if (conv) {
        setConversation(conv);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
      Alert.alert('Error', 'Failed to load conversation');
    }
  }, [conversationId, user]);

  const loadMessages = useCallback(async () => {
    if (!conversationId) return;
    
    try {
      const messagesData = await chatApi.getMessages(conversationId);
      setMessages(messagesData);
    } catch (error) {
      console.error('Failed to load messages:', error);
      Alert.alert('Error', 'Failed to load messages');
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  const handleSendMessage = async (messageData: { text?: string; media?: string; messageType: string }) => {
    if (!conversationId || !user || sendingMessage) return;
    
    setSendingMessage(true);
    try {
      const newMessage = await chatApi.sendMessage(conversationId, messageData);
      setMessages(prev => [newMessage, ...prev]);
    } catch (error) {
      console.error('Failed to send message:', error);
      Alert.alert('Error', 'Failed to send message');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleNewMessage = useCallback((data: { conversationId: string; message: Message }) => {
    if (data.conversationId === conversationId) {
      setMessages(prev => {
        const existsIndex = prev.findIndex(m => m.id === data.message.id);
        if (existsIndex >= 0) {
          return prev; // Message already exists
        }
        return [data.message, ...prev];
      });
    }
  }, [conversationId]);

  useEffect(() => {
    if (conversationId && user) {
      loadConversation();
      loadMessages();
      joinConversation(conversationId);
    }
    
    return () => {
      if (conversationId) {
        leaveConversation(conversationId);
      }
    };
  }, [conversationId, user, loadConversation, loadMessages, joinConversation, leaveConversation]);

  useEffect(() => {
    if (socket) {
      socket.on('new_message', handleNewMessage);
      return () => {
        socket.off('new_message', handleNewMessage);
      };
    }
  }, [socket, handleNewMessage]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#667eea" />
      </View>
    );
  }

  if (!conversation || !user) {
    return null;
  }

  return (
    <View style={styles.container}>
      <ChatHeader
        conversation={conversation}
        currentUserId={user.id}
        onBack={() => router.back()}
        onProfile={() => {/* Navigate to profile */}}
      />
      
      <MessagesList
        messages={messages}
        currentUserId={user.id}
        onEndReached={loadMessages}
      />
      
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={sendingMessage}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#ffffff',
  },
});