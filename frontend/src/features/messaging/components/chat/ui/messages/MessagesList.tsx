import React from 'react';
import { FlatList, View, StyleSheet } from 'react-native';
import { MessageBubble, MessageBubbleProps } from './bubble/MessageBubble';

export interface MessagesListProps {
  messages: MessageBubbleProps['message'][];
  currentUserId: string;
  onMediaPress?: (media: string) => void;
  onEndReached?: () => void;
  refreshing?: boolean;
  onRefresh?: () => void;
}

export const MessagesList: React.FC<MessagesListProps> = ({
  messages,
  currentUserId,
  onMediaPress,
  onEndReached,
  refreshing,
  onRefresh,
}) => {
  const renderMessage = ({ item }: { item: MessageBubbleProps['message'] }) => (
    <MessageBubble
      message={item}
      isOwn={item.sender.id === currentUserId}
      currentUserId={currentUserId}
      onMediaPress={onMediaPress}
    />
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        inverted
        showsVerticalScrollIndicator={false}
        onEndReached={onEndReached}
        onEndReachedThreshold={0.1}
        refreshing={refreshing}
        onRefresh={onRefresh}
        contentContainerStyle={styles.listContent}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  listContent: {
    paddingVertical: 8,
  },
});