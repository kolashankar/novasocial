import { api } from '../../../services/api';

export interface User {
  id: string;
  username: string;
  fullName: string;
  email: string;
  profileImage?: string;
  bio?: string;
}

export interface Story {
  id: string;
  authorId: string;
  author: User;
  media: string;
  mediaType: 'image' | 'video';
  text?: string;
  textPosition?: { x: number; y: number };
  textStyle?: { color: string; fontSize: number };
  duration: number;
  viewers: string[];
  viewersCount: number;
  createdAt: string;
  expiresAt: string;
}

export interface CreateStoryData {
  media: string;
  mediaType: 'image' | 'video';
  text?: string;
  textPosition?: { x: number; y: number };
  textStyle?: { color: string; fontSize: number };
  duration?: number;
}

class StoriesApiService {
  async createStory(data: CreateStoryData): Promise<Story> {
    const response = await api.post('/stories', data);
    return response.data;
  }

  async getStoriesFeed(skip = 0, limit = 50): Promise<Story[]> {
    const response = await api.get(`/stories/feed?skip=${skip}&limit=${limit}`);
    return response.data;
  }

  async viewStory(storyId: string): Promise<{ viewed: boolean }> {
    const response = await api.post(`/stories/${storyId}/view`);
    return response.data;
  }

  async deleteStory(storyId: string): Promise<{ deleted: boolean }> {
    const response = await api.delete(`/stories/${storyId}`);
    return response.data;
  }

  // Helper method to group stories by author
  groupStoriesByAuthor(stories: Story[]): Array<{
    author: User;
    stories: Story[];
    hasUnviewed: boolean;
  }> {
    const grouped = stories.reduce((acc, story) => {
      const authorId = story.authorId;
      if (!acc[authorId]) {
        acc[authorId] = {
          author: story.author,
          stories: [],
          hasUnviewed: false,
        };
      }
      acc[authorId].stories.push(story);
      
      // Check if story is unviewed (simplified - you might want to track this properly)
      if (!story.viewers.length) {
        acc[authorId].hasUnviewed = true;
      }
      
      return acc;
    }, {} as Record<string, { author: User; stories: Story[]; hasUnviewed: boolean }>);

    return Object.values(grouped);
  }
}

export const storiesApi = new StoriesApiService();