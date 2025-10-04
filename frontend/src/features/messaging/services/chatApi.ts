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
}

export const chatApi = new ChatApiService();