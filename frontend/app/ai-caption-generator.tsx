import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Image,
  TextInput,
  Alert,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../src/contexts/AuthContext';
import { COLORS } from '../src/utils/constants';
import Constants from 'expo-constants';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface CaptionSuggestion {
  id: string;
  caption: string;
  hashtags: string[];
  confidence: number;
  category: string;
}

interface CaptionGenerationResponse {
  suggestions: CaptionSuggestion[];
  mediaUrl: string;
  generatedAt: string;
}

export default function AICaptionGenerator() {
  const router = useRouter();
  const { mediaUrl, mediaType } = useLocalSearchParams<{ 
    mediaUrl: string; 
    mediaType: string 
  }>();
  const { user, token } = useAuth();

  const [suggestions, setSuggestions] = useState<CaptionSuggestion[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<CaptionSuggestion | null>(null);
  const [customCaption, setCustomCaption] = useState('');
  const [context, setContext] = useState('');
  const [editingCaption, setEditingCaption] = useState(false);

  const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || 'https://socialcrypt-app.preview.emergentagent.com';

  const generateCaptions = async () => {
    if (!mediaUrl) {
      Alert.alert('Error', 'No media URL provided');
      return;
    }

    setIsGenerating(true);
    setSuggestions([]);

    try {
      const response = await fetch(`${backendUrl}/api/ai/caption`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          mediaUrl: mediaUrl,
          mediaType: mediaType || 'image',
          context: context || undefined,
        }),
      });

      const data: CaptionGenerationResponse = await response.json();

      if (response.ok) {
        setSuggestions(data.suggestions);
        
        if (data.suggestions.length > 0) {
          // Auto-select the first (highest confidence) suggestion
          setSelectedSuggestion(data.suggestions[0]);
          setCustomCaption(data.suggestions[0].caption);
        }
      } else {
        throw new Error(data.message || 'Failed to generate captions');
      }
    } catch (error) {
      console.error('Caption generation error:', error);
      Alert.alert('Error', 'Failed to generate captions. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const selectSuggestion = (suggestion: CaptionSuggestion) => {
    setSelectedSuggestion(suggestion);
    setCustomCaption(suggestion.caption);
    setEditingCaption(false);
  };

  const getCategoryIcon = (category: string): keyof typeof Ionicons.glyphMap => {
    const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
      lifestyle: 'heart',
      travel: 'airplane',
      food: 'restaurant',
      fashion: 'shirt',
      fitness: 'fitness',
      nature: 'leaf',
      general: 'image',
      business: 'briefcase',
      art: 'color-palette',
      music: 'musical-notes',
    };
    return icons[category] || 'image';
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      lifestyle: '#FF6B9D',
      travel: '#4ECDC4',
      food: '#FFE66D',
      fashion: '#A8E6CF',
      fitness: '#FF8B94',
      nature: '#95E1D3',
      general: '#B19CD9',
      business: '#FFA07A',
      art: '#FFB3BA',
      music: '#BAFFC9',
    };
    return colors[category] || '#B19CD9';
  };

  const renderHashtags = (hashtags: string[]) => (
    <View style={styles.hashtagContainer}>
      {hashtags.map((tag, index) => (
        <View key={index} style={styles.hashtag}>
          <Text style={styles.hashtagText}>#{tag}</Text>
        </View>
      ))}
    </View>
  );

  const renderSuggestion = (suggestion: CaptionSuggestion, index: number) => (
    <TouchableOpacity
      key={suggestion.id}
      style={[
        styles.suggestionCard,
        selectedSuggestion?.id === suggestion.id && styles.selectedSuggestionCard
      ]}
      onPress={() => selectSuggestion(suggestion)}
    >
      <View style={styles.suggestionHeader}>
        <View style={styles.categoryBadge}>
          <Ionicons 
            name={getCategoryIcon(suggestion.category)} 
            size={16} 
            color="white" 
            style={[styles.categoryIcon, { backgroundColor: getCategoryColor(suggestion.category) }]}
          />
          <Text style={styles.categoryText}>{suggestion.category}</Text>
        </View>
        <View style={styles.confidenceContainer}>
          <Text style={styles.confidenceText}>
            {Math.round(suggestion.confidence * 100)}%
          </Text>
          <View style={[styles.confidenceBar, { width: suggestion.confidence * 50 }]} />
        </View>
      </View>
      
      <Text style={styles.suggestionCaption}>{suggestion.caption}</Text>
      
      {renderHashtags(suggestion.hashtags)}
      
      {selectedSuggestion?.id === suggestion.id && (
        <View style={styles.selectedIndicator}>
          <Ionicons name="checkmark-circle" size={20} color={COLORS.primary} />
        </View>
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.headerButton}>
          <Ionicons name="arrow-back" size={24} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>AI Caption Generator</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="sparkles" size={24} color={COLORS.primary} />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Media Preview */}
        {mediaUrl && (
          <View style={styles.mediaPreviewContainer}>
            <Image source={{ uri: mediaUrl }} style={styles.mediaPreview} />
            <LinearGradient
              colors={['transparent', 'rgba(0,0,0,0.6)']}
              style={styles.mediaOverlay}
            />
            <Text style={styles.mediaType}>{mediaType?.toUpperCase() || 'IMAGE'}</Text>
          </View>
        )}

        {/* Context Input */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Add Context (Optional)</Text>
          <TextInput
            style={styles.contextInput}
            placeholder="Describe your photo to get better captions..."
            placeholderTextColor={COLORS.textSecondary}
            value={context}
            onChangeText={setContext}
            multiline
            maxLength={200}
          />
          <Text style={styles.contextHint}>
            e.g., "Beach vacation with friends", "Homemade pasta dinner", etc.
          </Text>
        </View>

        {/* Generate Button */}
        <TouchableOpacity
          style={[styles.generateButton, isGenerating && styles.generateButtonDisabled]}
          onPress={generateCaptions}
          disabled={isGenerating}
        >
          <LinearGradient
            colors={[COLORS.primary, '#A855F7']}
            style={styles.generateButtonGradient}
          >
            {isGenerating ? (
              <>
                <ActivityIndicator size="small" color="white" />
                <Text style={styles.generateButtonText}>Generating...</Text>
              </>
            ) : (
              <>
                <Ionicons name="sparkles" size={20} color="white" />
                <Text style={styles.generateButtonText}>Generate Captions</Text>
              </>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* AI Suggestions */}
        {suggestions.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>AI Generated Suggestions</Text>
            {suggestions.map((suggestion, index) => renderSuggestion(suggestion, index))}
          </View>
        )}

        {/* Caption Editor */}
        {selectedSuggestion && (
          <View style={styles.section}>
            <View style={styles.editorHeader}>
              <Text style={styles.sectionTitle}>Your Caption</Text>
              <TouchableOpacity
                onPress={() => setEditingCaption(!editingCaption)}
                style={styles.editButton}
              >
                <Ionicons 
                  name={editingCaption ? "checkmark" : "create"} 
                  size={20} 
                  color={COLORS.primary} 
                />
              </TouchableOpacity>
            </View>
            
            <View style={styles.captionEditor}>
              <TextInput
                style={[styles.captionInput, !editingCaption && styles.captionInputDisabled]}
                value={customCaption}
                onChangeText={setCustomCaption}
                multiline
                editable={editingCaption}
                placeholder="Your caption will appear here..."
                placeholderTextColor={COLORS.textSecondary}
              />
              
              {selectedSuggestion.hashtags.length > 0 && (
                <View style={styles.selectedHashtags}>
                  {renderHashtags(selectedSuggestion.hashtags)}
                </View>
              )}
            </View>
          </View>
        )}

        {/* Action Buttons */}
        {selectedSuggestion && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.copyButton}
              onPress={() => {
                // Copy to clipboard functionality would go here
                Alert.alert('Copied!', 'Caption copied to clipboard');
              }}
            >
              <Ionicons name="copy" size={20} color={COLORS.primary} />
              <Text style={styles.copyButtonText}>Copy Caption</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.useButton}
              onPress={() => {
                // Navigate back to post creation with caption
                router.back();
                // You would pass the caption back to the previous screen
              }}
            >
              <LinearGradient
                colors={[COLORS.primary, '#A855F7']}
                style={styles.useButtonGradient}
              >
                <Ionicons name="checkmark" size={20} color="white" />
                <Text style={styles.useButtonText}>Use Caption</Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  headerButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
  },
  content: {
    flex: 1,
  },
  mediaPreviewContainer: {
    position: 'relative',
    margin: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  mediaPreview: {
    width: '100%',
    height: 200,
    resizeMode: 'cover',
  },
  mediaOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 60,
  },
  mediaType: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  section: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  contextInput: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    padding: 16,
    color: COLORS.text,
    fontSize: 16,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  contextHint: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 8,
    fontStyle: 'italic',
  },
  generateButton: {
    marginHorizontal: 16,
    marginBottom: 24,
    borderRadius: 12,
    overflow: 'hidden',
  },
  generateButtonDisabled: {
    opacity: 0.7,
  },
  generateButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  generateButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  suggestionCard: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
    position: 'relative',
  },
  selectedSuggestionCard: {
    borderColor: COLORS.primary,
  },
  suggestionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryIcon: {
    padding: 4,
    borderRadius: 6,
    marginRight: 6,
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
    textTransform: 'capitalize',
  },
  confidenceContainer: {
    alignItems: 'flex-end',
  },
  confidenceText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 2,
  },
  confidenceBar: {
    height: 3,
    backgroundColor: COLORS.primary,
    borderRadius: 1.5,
  },
  suggestionCaption: {
    fontSize: 16,
    color: COLORS.text,
    lineHeight: 22,
    marginBottom: 12,
  },
  hashtagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  hashtag: {
    backgroundColor: COLORS.primary + '20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  hashtagText: {
    fontSize: 12,
    color: COLORS.primary,
    fontWeight: '500',
  },
  selectedIndicator: {
    position: 'absolute',
    top: 12,
    right: 12,
  },
  editorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  editButton: {
    padding: 4,
  },
  captionEditor: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 16,
  },
  captionInput: {
    color: COLORS.text,
    fontSize: 16,
    lineHeight: 22,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  captionInputDisabled: {
    backgroundColor: 'transparent',
  },
  selectedHashtags: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginHorizontal: 16,
    marginBottom: 32,
  },
  copyButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderWidth: 2,
    borderColor: COLORS.primary,
    borderRadius: 12,
  },
  copyButtonText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  useButton: {
    flex: 1,
    borderRadius: 12,
    overflow: 'hidden',
  },
  useButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  useButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});