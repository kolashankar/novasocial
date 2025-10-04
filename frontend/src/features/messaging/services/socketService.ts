import { useEffect, useState, useCallback } from 'react';
import io, { Socket } from 'socket.io-client';
import Constants from 'expo-constants';
import { useAuthContext } from '../../../contexts/AuthContext';

class SocketService {
  private socket: Socket | null = null;
  private connected: boolean = false;

  connect(token: string) {
    const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || 'http://localhost:8001';
    
    if (!this.socket) {
      this.socket = io(backendUrl, {
        auth: {
          token,
        },
        transports: ['websocket'],
      });

      this.socket.on('connect', () => {
        console.log('Socket connected');
        this.connected = true;
      });

      this.socket.on('disconnect', () => {
        console.log('Socket disconnected');
        this.connected = false;
      });

      this.socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
        this.connected = false;
      });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  getSocket() {
    return this.socket;
  }

  isConnected() {
    return this.connected;
  }

  joinConversation(conversationId: string) {
    if (this.socket && this.connected) {
      this.socket.emit('join_conversation', { conversationId });
    }
  }

  leaveConversation(conversationId: string) {
    if (this.socket && this.connected) {
      this.socket.emit('leave_conversation', { conversationId });
    }
  }

  sendTypingStart(conversationId: string, userId: string) {
    if (this.socket && this.connected) {
      this.socket.emit('typing_start', { conversationId, userId });
    }
  }

  sendTypingStop(conversationId: string, userId: string) {
    if (this.socket && this.connected) {
      this.socket.emit('typing_stop', { conversationId, userId });
    }
  }

  markAsRead(conversationId: string, userId: string, messageIds: string[]) {
    if (this.socket && this.connected) {
      this.socket.emit('mark_read', { conversationId, userId, messageIds });
    }
  }
}

const socketService = new SocketService();

export const useSocket = () => {
  const { user, token } = useAuthContext();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (user && token) {
      socketService.connect(token);
      setSocket(socketService.getSocket());
      
      const checkConnection = setInterval(() => {
        setConnected(socketService.isConnected());
      }, 1000);

      return () => {
        clearInterval(checkConnection);
      };
    } else {
      socketService.disconnect();
      setSocket(null);
      setConnected(false);
    }
  }, [user, token]);

  const joinConversation = useCallback((conversationId: string) => {
    socketService.joinConversation(conversationId);
  }, []);

  const leaveConversation = useCallback((conversationId: string) => {
    socketService.leaveConversation(conversationId);
  }, []);

  const sendTypingStart = useCallback((conversationId: string, userId: string) => {
    socketService.sendTypingStart(conversationId, userId);
  }, []);

  const sendTypingStop = useCallback((conversationId: string, userId: string) => {
    socketService.sendTypingStop(conversationId, userId);
  }, []);

  const markAsRead = useCallback((conversationId: string, userId: string, messageIds: string[]) => {
    socketService.markAsRead(conversationId, userId, messageIds);
  }, []);

  return {
    socket,
    connected,
    joinConversation,
    leaveConversation,
    sendTypingStart,
    sendTypingStop,
    markAsRead,
  };
};

export default socketService;