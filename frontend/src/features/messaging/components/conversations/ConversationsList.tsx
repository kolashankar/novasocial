import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Image,
  Alert,
  RefreshControl,
  TextInput,
  ScrollView,
} from 'react-native';
import { router } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { chatApi, Conversation } from '../../services/chatApi';
import { useSocket } from '../../services/socketService';
import { useAuthContext } from '../../../../contexts/AuthContext';

export const ConversationsList: React.FC = () => {
  const { user } = useAuthContext();
  const { socket } = useSocket();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Phase 14 - Enhanced Messaging Features
  const [activeFilter, setActiveFilter] = useState<'all' | 'unread' | 'groups' | 'direct'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [userStatuses, setUserStatuses] = useState<Record<string, { isOnline: boolean; lastSeen: string }>>({});

  const filters = [
    { key: 'all', label: 'All', icon: 'chatbubbles-outline' },
    { key: 'unread', label: 'Unread', icon: 'radio-button-on-outline' },
    { key: 'groups', label: 'Groups', icon: 'people-outline' },
    { key: 'direct', label: 'Direct', icon: 'person-outline' },
  ];

  const loadConversations = useCallback(async () => {
    try {
      // Phase 14: Use enhanced API with filters
      const data = await chatApi.getFilteredConversations({
        filterType: activeFilter,
        searchQuery: searchQuery || undefined,
      });
      setConversations(data);
      
      // Load user activity statuses for participants
      if (data.length > 0) {
        const allUserIds = new Set<string>();
        data.forEach(conv => {
          conv.participants.forEach(p => {
            if (p.id !== user?.id) {
              allUserIds.add(p.id);
            }
          });
        });
        
        // Fetch activity statuses for all users
        const statusPromises = Array.from(allUserIds).map(async (userId) => {
          try {
            const status = await chatApi.getUserActivity(userId);
            return { userId, status };
          } catch {
            return { userId, status: { isOnline: false, lastSeen: new Date().toISOString() } };
          }
        });
        
        const statuses = await Promise.all(statusPromises);
        const statusMap: Record<string, { isOnline: boolean; lastSeen: string }> = {};
        statuses.forEach(({ userId, status }) => {
          statusMap[userId] = status;
        });
        setUserStatuses(statusMap);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
      Alert.alert('Error', 'Failed to load conversations');
    } finally {
      setLoading(false);
    }
  }, [activeFilter, searchQuery, user]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadConversations();
    setRefreshing(false);
  }, [loadConversations]);

  useEffect(() => {
    if (user) {
      loadConversations();
    }
  }, [user, loadConversations]);

  useEffect(() => {
    if (socket) {
      const handleNewMessage = (data: { conversationId: string; message: any }) => {
        setConversations(prev => 
          prev.map(conv => {
            if (conv.id === data.conversationId) {
              return {
                ...conv,
                lastMessage: data.message,
                unreadCount: data.message.sender.id !== user?.id ? conv.unreadCount + 1 : conv.unreadCount,
                updatedAt: data.message.createdAt,
              };
            }
            return conv;
          })
        );
      };

      socket.on('new_message', handleNewMessage);
      return () => {
        socket.off('new_message', handleNewMessage);
      };
    }
  }, [socket, user]);

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  const getDisplayInfo = (conversation: Conversation) => {
    if (conversation.isGroup) {
      return {
        name: conversation.name || 'Group Chat',
        image: null,
      };
    } else {
      const otherUser = conversation.participants.find(p => p.id !== user?.id);
      return {
        name: otherUser?.fullName || otherUser?.username || 'Unknown',
        image: otherUser?.profileImage,
      };
    }
  };

  // Phase 14: Enhanced conversation rendering with status indicators
  const renderConversation = ({ item }: { item: Conversation }) => {
    const displayInfo = getDisplayInfo(item);
    const lastMessageText = item.lastMessage?.text || 
      (item.lastMessage?.messageType === 'image' ? '📷 Photo' : 'No messages yet');

    // Get online status for direct conversations
    const otherUser = !item.isGroup ? item.participants.find(p => p.id !== user?.id) : null;
    const userStatus = otherUser ? userStatuses[otherUser.id] : null;

    return (
      <TouchableOpacity
        style={styles.conversationItem}
        onPress={() => router.push(`/(tabs)/chat/conversation/${item.id}`)}
      >
        <View style={styles.avatarContainer}>
          <Image
            source={{ 
              uri: displayInfo.image || 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==' 
            }}
            style={styles.avatar}
          />
          {/* Phase 14: Online status indicator */}
          {!item.isGroup && userStatus?.isOnline && (
            <View style={styles.onlineIndicator} />
          )}
        </View>
        
        <View style={styles.conversationContent}>
          <View style={styles.conversationHeader}>
            <Text style={styles.conversationName} numberOfLines={1}>
              {displayInfo.name}
            </Text>
            <View style={styles.headerRight}>
              {item.lastMessage && (
                <Text style={styles.time}>
                  {formatTime(item.lastMessage.createdAt)}
                </Text>
              )}
              {/* Phase 14: Read receipts indicators */}
              {item.lastMessage && item.lastMessage.sender.id === user?.id && (
                <View style={styles.readReceiptContainer}>
                  <Ionicons 
                    name="checkmark-done" 
                    size={16} 
                    color={item.lastMessage.readBy?.length > 1 ? "#4f46e5" : "#94a3b8"} 
                  />
                </View>
              )}
            </View>
          </View>
          
          <View style={styles.messageRow}>
            <Text style={styles.lastMessage} numberOfLines={1}>
              {lastMessageText}
            </Text>
            {item.unreadCount > 0 && (
              <View style={styles.unreadBadge}>
                <Text style={styles.unreadText}>
                  {item.unreadCount > 99 ? '99+' : item.unreadCount}
                </Text>
              </View>
            )}
          </View>
          
          {/* Phase 14: Show last seen for offline users */}
          {!item.isGroup && userStatus && !userStatus.isOnline && (
            <Text style={styles.lastSeenText}>
              Last seen {formatTime(userStatus.lastSeen)}
            </Text>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  // Phase 14: Render filter tabs
  const renderFilterTabs = () => (
    <View style={styles.filterContainer}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
        {filters.map((filter) => (
          <TouchableOpacity
            key={filter.key}
            style={[
              styles.filterTab,
              activeFilter === filter.key && styles.activeFilterTab
            ]}
            onPress={() => setActiveFilter(filter.key as any)}
          >
            <Ionicons 
              name={filter.icon as any} 
              size={20} 
              color={activeFilter === filter.key ? '#ffffff' : '#64748b'} 
            />
            <Text style={[
              styles.filterText,
              activeFilter === filter.key && styles.activeFilterText
            ]}>
              {filter.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      
      {/* Search toggle */}
      <TouchableOpacity
        style={styles.searchToggle}
        onPress={() => setShowSearch(!showSearch)}
      >
        <Ionicons 
          name={showSearch ? "close" : "search"} 
          size={20} 
          color="#64748b" 
        />
      </TouchableOpacity>
    </View>
  );

  // Phase 14: Render search bar
  const renderSearchBar = () => {
    if (!showSearch) return null;
    
    return (
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#94a3b8" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search conversations..."
          placeholderTextColor="#94a3b8"
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoFocus
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color="#94a3b8" />
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const handleNewChat = () => {
    // Navigate to user selection screen
    router.push('/(tabs)/chat/new-chat');
  };

  if (loading) {
    return (
      <View style={styles.emptyContainer}>
        <Text>Loading conversations...</Text>
      </View>
    );
  }

  if (conversations.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="chatbubbles-outline" size={64} color="#94a3b8" />
        <Text style={styles.emptyTitle}>No conversations yet</Text>
        <Text style={styles.emptySubtitle}>Start a new chat to get started</Text>
        
        <TouchableOpacity style={styles.newChatButton} onPress={handleNewChat}>
          <LinearGradient
            colors={['#667eea', '#764ba2']}
            style={styles.newChatGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Ionicons name="add" size={24} color="#ffffff" />
            <Text style={styles.newChatText}>Start New Chat</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Phase 14: Filter tabs */}
      {renderFilterTabs()}
      
      {/* Phase 14: Search bar */}
      {renderSearchBar()}
      
      <FlatList
        data={conversations}
        keyExtractor={(item) => item.id}
        renderItem={renderConversation}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
      />
      
      <TouchableOpacity style={styles.fab} onPress={handleNewChat}>
        <LinearGradient
          colors={['#667eea', '#764ba2']}
          style={styles.fabGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Ionicons name="add" size={24} color="#ffffff" />
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  listContent: {
    paddingBottom: 80,
  },
  conversationItem: {
    flexDirection: 'row',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
    alignItems: 'center',
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginRight: 12,
    backgroundColor: '#f1f5f9',
  },
  conversationContent: {
    flex: 1,
  },
  conversationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  conversationName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e293b',
    flex: 1,
  },
  time: {
    fontSize: 12,
    color: '#64748b',
  },
  messageRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lastMessage: {
    fontSize: 14,
    color: '#64748b',
    flex: 1,
  },
  unreadBadge: {
    backgroundColor: '#667eea',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
  },
  unreadText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1e293b',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 24,
  },
  newChatButton: {
    marginTop: 16,
  },
  newChatGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 25,
  },
  newChatText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  fab: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    width: 56,
    height: 56,
    borderRadius: 28,
    elevation: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
  },
  fabGradient: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Phase 14: New styles for enhanced messaging UI
  filterContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
    backgroundColor: '#ffffff',
  },
  filterScroll: {
    flex: 1,
  },
  filterTab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: '#f8fafc',
  },
  activeFilterTab: {
    backgroundColor: '#667eea',
  },
  filterText: {
    marginLeft: 6,
    fontSize: 14,
    fontWeight: '500',
    color: '#64748b',
  },
  activeFilterText: {
    color: '#ffffff',
  },
  searchToggle: {
    padding: 8,
    marginLeft: 8,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#f8fafc',
    borderRadius: 25,
  },
  searchInput: {
    flex: 1,
    marginLeft: 8,
    fontSize: 16,
    color: '#1e293b',
  },
  avatarContainer: {
    position: 'relative',
    marginRight: 12,
  },
  onlineIndicator: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#10b981',
    borderWidth: 2,
    borderColor: '#ffffff',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  readReceiptContainer: {
    marginLeft: 4,
  },
  lastSeenText: {
    fontSize: 12,
    color: '#94a3b8',
    marginTop: 2,
  },
});