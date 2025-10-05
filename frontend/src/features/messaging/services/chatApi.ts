import { api } from '../../../services/api';

export interface User {
  id: string;
  username: string;
  fullName: string;
  email: string;
  profileImage?: string;
  bio?: string;
}

export interface Message {
  id: string;
  conversationId: string;
  text?: string;
  messageType: string;
  media?: string;
  replyTo?: string;
  createdAt: string;
  updatedAt: string;
  sender: User;
  readBy: Array<{
    userId: string;
    readAt: string;
  }>;
}

export interface Conversation {
  id: string;
  participantIds: string[];
  participants: User[];
  isGroup: boolean;
  name?: string;
  description?: string;
  lastMessage?: Message;
  unreadCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateConversationData {
  participantIds: string[];
  isGroup?: boolean;
  name?: string;
  description?: string;
}

export interface SendMessageData {
  text?: string;
  messageType: string;
  media?: string;
  replyTo?: string;
}

class ChatApiService {
  async getConversations(skip = 0, limit = 50): Promise<Conversation[]> {
    const response = await api.get(`/conversations?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async createConversation(data: CreateConversationData): Promise<Conversation> {
    const response = await api.post('/conversations', data);
    return response.data;
  }

  async getMessages(conversationId: string, skip = 0, limit = 50): Promise<Message[]> {
    const response = await api.get(`/conversations/${conversationId}/messages?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async sendMessage(conversationId: string, data: SendMessageData): Promise<Message> {
    const messageData = {
      ...data,
      conversationId,
    };
    const response = await api.post(`/conversations/${conversationId}/messages`, messageData);
    return response.data;
  }

  // Helper method to find or create a direct conversation with a user
  async getOrCreateDirectConversation(otherUserId: string): Promise<Conversation> {
    // First, try to find existing conversation
    const conversations = await this.getConversations();
    const existing = conversations.find(conv => 
      !conv.isGroup && 
      conv.participants.length === 2 &&
      conv.participants.some(p => p.id === otherUserId)
    );

    if (existing) {
      return existing;
    }

    // Create new conversation
    return await this.createConversation({
      participantIds: [otherUserId],
      isGroup: false,
    });
  }

  // PHASE 14: Enhanced Messaging & Real-time Features
  async getFilteredConversations(params: {
    filterType: 'all' | 'unread' | 'groups' | 'direct';
    searchQuery?: string;
    skip?: number;
    limit?: number;
  }): Promise<Conversation[]> {
    const queryParams = new URLSearchParams({
      filter_type: params.filterType,
      skip: String(params.skip || 0),
      limit: String(params.limit || 50),
    });
    
    if (params.searchQuery) {
      queryParams.append('search_query', params.searchQuery);
    }

    const response = await api.get(`/conversations/filters?${queryParams.toString()}`);
    return response.data;
  }

  async updateConversationSettings(conversationId: string, settings: {
    isArchived?: boolean;
    isMuted?: boolean;
    muteUntil?: string;
  }): Promise<void> {
    await api.put(`/conversations/${conversationId}/settings`, settings);
  }

  async sendTypingIndicator(conversationId: string, isTyping: boolean): Promise<void> {
    await api.post(`/conversations/${conversationId}/typing`, {
      conversationId,
      userId: '', // Will be set by backend from auth
      isTyping,
    });
  }

  async markMessageRead(messageId: string): Promise<void> {
    await api.put(`/messages/${messageId}/read`);
  }

  async markAllMessagesRead(conversationId: string): Promise<void> {
    await api.put(`/conversations/${conversationId}/read-all`);
  }

  async getUserActivity(userId: string): Promise<{
    userId: string;
    status: string;
    lastSeen: string;
    isOnline: boolean;
  }> {
    const response = await api.get(`/users/${userId}/activity`);
    return response.data;
  }

  async updateUserActivity(status: 'online' | 'offline' | 'away' | 'busy'): Promise<void> {
    await api.put('/user/activity', { status });
  }

  async queueOfflineMessage(messageData: SendMessageData & { conversationId: string }): Promise<{ queueId: string }> {
    const response = await api.post('/messages/queue', messageData);
    return response.data;
  }

  async syncOfflineMessages(): Promise<{
    sentCount: number;
    failedCount: number;
    totalProcessed: number;
  }> {
    const response = await api.post('/messages/sync');
    return response.data;
  }
}

export const chatApi = new ChatApiService();