import Constants from 'expo-constants';

const API_BASE_URL = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;

export interface User {
  id: string;
  email: string;
  username: string;
  fullName: string;
  profileImage?: string;
  bio?: string;
}

export interface Notification {
  id: string;
  recipientId: string;
  senderId?: string;
  sender?: User;
  type: string;
  title: string;
  message: string;
  relatedId?: string;
  relatedType?: string;
  isRead: boolean;
  createdAt: string;
}

class NotificationsApi {
  private getHeaders(token: string) {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }

  async getNotifications(token: string, skip: number = 0, limit: number = 50): Promise<Notification[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/notifications?skip=${skip}&limit=${limit}`,
      {
        method: 'GET',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch notifications');
    }

    return response.json();
  }

  async markAsRead(notificationId: string, token: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/notifications/${notificationId}/read`,
      {
        method: 'PUT',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to mark notification as read');
    }
  }

  async markAllAsRead(token: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/notifications/read-all`,
      {
        method: 'PUT',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to mark all notifications as read');
    }
  }

  async getUnreadCount(token: string): Promise<number> {
    const notifications = await this.getNotifications(token, 0, 100);
    return notifications.filter(n => !n.isRead).length;
  }
}

export const notificationsApi = new NotificationsApi();