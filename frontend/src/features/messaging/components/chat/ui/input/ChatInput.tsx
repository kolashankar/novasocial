import React, { useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { LinearGradient } from 'expo-linear-gradient';

export interface ChatInputProps {
  onSendMessage: (message: { text?: string; media?: string; messageType: string }) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage({ text: message.trim(), messageType: 'text' });
      setMessage('');
    }
  };

  const pickImage = async () => {
    if (disabled) return;

    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'We need permission to access your photos');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
      base64: true,
    });

    if (!result.canceled && result.assets[0].base64) {
      const base64Image = `data:image/jpeg;base64,${result.assets[0].base64}`;
      onSendMessage({ media: base64Image, messageType: 'image' });
    }
  };

  const handleTextChange = (text: string) => {
    setMessage(text);
    if (!isTyping && text.length > 0) {
      setIsTyping(true);
    } else if (isTyping && text.length === 0) {
      setIsTyping(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={90}
    >
      <View style={styles.container}>
        <View style={styles.inputContainer}>
          <TouchableOpacity 
            style={styles.attachButton} 
            onPress={pickImage}
            disabled={disabled}
          >
            <Ionicons name="camera" size={24} color="#667eea" />
          </TouchableOpacity>
          
          <TextInput
            style={styles.textInput}
            value={message}
            onChangeText={handleTextChange}
            placeholder="Type a message..."
            placeholderTextColor="#94a3b8"
            multiline
            maxLength={1000}
            editable={!disabled}
          />
          
          <TouchableOpacity 
            style={styles.sendButton} 
            onPress={handleSend}
            disabled={disabled || !message.trim()}
          >
            <LinearGradient
              colors={['#667eea', '#764ba2']}
              style={[
                styles.sendButtonGradient,
                (!message.trim() || disabled) && styles.sendButtonDisabled
              ]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Ionicons name="send" size={20} color="#ffffff" />
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    paddingBottom: Platform.OS === 'ios' ? 34 : 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 16,
  },
  attachButton: {
    padding: 8,
    marginRight: 8,
  },
  textInput: {
    flex: 1,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#1e293b',
    backgroundColor: '#f8fafc',
  },
  sendButton: {
    marginLeft: 8,
  },
  sendButtonGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
});