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
  messageType: 'text' | 'image' | 'video' | 'emoji';
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

export interface SocketEvents {
  connect: () => void;
  disconnect: () => void;
  new_message: (data: { conversationId: string; message: Message }) => void;
  user_typing: (data: { conversationId: string; userId: string; typing: boolean }) => void;
  messages_read: (data: { conversationId: string; userId: string; messageIds: string[] }) => void;
}

export interface SendMessageData {
  text?: string;
  messageType: Message['messageType'];
  media?: string;
  replyTo?: string;
}

export interface CreateConversationData {
  participantIds: string[];
  isGroup?: boolean;
  name?: string;
  description?: string;
}