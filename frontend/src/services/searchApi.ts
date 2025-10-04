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

export interface Post {
  id: string;
  authorId: string;
  author: User;
  caption: string;
  media: string[];
  mediaTypes: string[];
  hashtags: string[];
  taggedUsers: string[];
  likes: string[];
  likesCount: number;
  commentsCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface SearchResult {
  users: User[];
  posts: Post[];
  hashtags: string[];
}

class SearchApi {
  private getHeaders(token: string) {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }

  async search(
    query: string,
    type: 'all' | 'users' | 'posts' | 'hashtags' = 'all',
    token: string,
    limit: number = 20
  ): Promise<SearchResult> {
    const response = await fetch(
      `${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}&type=${type}&limit=${limit}`,
      {
        method: 'GET',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to perform search');
    }

    return response.json();
  }

  async getTrendingHashtags(
    token: string,
    limit: number = 20
  ): Promise<Array<{ hashtag: string; count: number }>> {
    const response = await fetch(
      `${API_BASE_URL}/api/trending/hashtags?limit=${limit}`,
      {
        method: 'GET',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch trending hashtags');
    }

    return response.json();
  }

  async getUserSuggestions(
    token: string,
    limit: number = 20
  ): Promise<User[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/users/suggestions?limit=${limit}`,
      {
        method: 'GET',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch user suggestions');
    }

    return response.json();
  }

  async getRecommendedFeed(
    token: string,
    skip: number = 0,
    limit: number = 20
  ): Promise<Post[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/feed/recommendations?skip=${skip}&limit=${limit}`,
      {
        method: 'GET',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch recommended feed');
    }

    return response.json();
  }

  async followUser(userId: string, token: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/users/${userId}/follow`,
      {
        method: 'POST',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to follow user');
    }
  }

  async unfollowUser(userId: string, token: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/users/${userId}/follow`,
      {
        method: 'DELETE',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to unfollow user');
    }
  }

  async getUserFollowers(
    userId: string,
    token: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<User[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/users/${userId}/followers?skip=${skip}&limit=${limit}`,
      {
        method: 'GET',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch user followers');
    }

    return response.json();
  }

  async getUserFollowing(
    userId: string,
    token: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<User[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/users/${userId}/following?skip=${skip}&limit=${limit}`,
      {
        method: 'GET',
        headers: this.getHeaders(token),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch user following');
    }

    return response.json();
  }
}

export const searchApi = new SearchApi();