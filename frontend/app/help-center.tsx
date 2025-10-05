import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useTheme } from '../src/contexts/ThemeContext';

interface FAQ {
  id: string;
  category: string;
  question: string;
  answer: string;
  keywords: string[];
  helpful: number;
  notHelpful: number;
}

interface SupportTicket {
  category: string;
  subject: string;
  description: string;
  attachments?: string[];
}

export default function HelpCenterScreen() {
  const { theme } = useTheme();
  const styles = getStyles(theme);

  const [activeTab, setActiveTab] = useState<'faq' | 'contact'>('faq');
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [filteredFaqs, setFilteredFaqs] = useState<FAQ[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedFaq, setExpandedFaq] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Contact form state
  const [contactForm, setContactForm] = useState<SupportTicket>({
    category: 'technical',
    subject: '',
    description: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const categories = [
    { id: 'all', label: 'All', icon: 'apps-outline' },
    { id: 'account', label: 'Account', icon: 'person-outline' },
    { id: 'privacy', label: 'Privacy', icon: 'shield-outline' },
    { id: 'posting', label: 'Posting', icon: 'camera-outline' },
    { id: 'messaging', label: 'Messaging', icon: 'chatbubble-outline' },
    { id: 'technical', label: 'Technical', icon: 'cog-outline' },
    { id: 'safety', label: 'Safety', icon: 'shield-checkmark-outline' }
  ];

  const supportCategories = [
    { id: 'bug', label: 'Bug Report', icon: 'bug-outline' },
    { id: 'feature_request', label: 'Feature Request', icon: 'bulb-outline' },
    { id: 'account_issue', label: 'Account Issue', icon: 'person-circle-outline' },
    { id: 'harassment', label: 'Harassment', icon: 'warning-outline' },
    { id: 'technical', label: 'Technical Issue', icon: 'construct-outline' },
    { id: 'other', label: 'Other', icon: 'help-outline' }
  ];

  useEffect(() => {
    loadFAQs();
  }, []);

  useEffect(() => {
    filterFAQs();
  }, [faqs, searchQuery, selectedCategory]);

  const loadFAQs = async () => {
    try {
      const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/support/faq`);
      
      if (response.ok) {
        const data = await response.json();
        setFaqs(data);
      } else {
        console.error('Failed to load FAQs');
      }
    } catch (error) {
      console.error('Error loading FAQs:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchFAQs = async (query: string) => {
    if (!query.trim()) {
      setFilteredFaqs(faqs);
      return;
    }

    try {
      const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
      const response = await fetch(`${backendUrl}/api/support/faq/search?q=${encodeURIComponent(query)}`);
      
      if (response.ok) {
        const data = await response.json();
        setFilteredFaqs(data.results);
      }
    } catch (error) {
      console.error('Error searching FAQs:', error);
    }
  };

  const filterFAQs = () => {
    let filtered = faqs;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(faq => faq.category === selectedCategory);
    }

    // Search if query exists
    if (searchQuery.trim()) {
      searchFAQs(searchQuery);
      return;
    }

    setFilteredFaqs(filtered);
  };

  const handleSearch = (text: string) => {
    setSearchQuery(text);
  };

  const toggleFAQ = (id: string) => {
    setExpandedFaq(expandedFaq === id ? null : id);
  };

  const submitSupportTicket = async () => {
    if (!contactForm.subject.trim() || !contactForm.description.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSubmitting(true);

    try {
      const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
      // Note: You'll need to get the auth token from your auth context
      // const token = await getAuthToken();
      
      const response = await fetch(`${backendUrl}/api/support/tickets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(contactForm)
      });

      if (response.ok) {
        Alert.alert(
          'Success',
          'Your support ticket has been submitted. We\'ll get back to you soon!',
          [{ text: 'OK', onPress: () => router.back() }]
        );
      } else {
        Alert.alert('Error', 'Failed to submit support ticket. Please try again.');
      }
    } catch (error) {
      console.error('Error submitting support ticket:', error);
      Alert.alert('Error', 'Failed to submit support ticket. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderFAQ = (faq: FAQ) => (
    <View key={faq.id} style={styles.faqItem}>
      <TouchableOpacity
        style={styles.faqQuestion}
        onPress={() => toggleFAQ(faq.id)}
      >
        <Text style={styles.questionText}>{faq.question}</Text>
        <Ionicons
          name={expandedFaq === faq.id ? 'chevron-up' : 'chevron-down'}
          size={20}
          color={theme.colors.textSecondary}
        />
      </TouchableOpacity>
      
      {expandedFaq === faq.id && (
        <View style={styles.faqAnswer}>
          <Text style={styles.answerText}>{faq.answer}</Text>
          <View style={styles.faqActions}>
            <TouchableOpacity style={styles.helpfulButton}>
              <Ionicons name="thumbs-up-outline" size={16} color={theme.colors.primary} />
              <Text style={styles.helpfulText}>Helpful ({faq.helpful})</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.helpfulButton}>
              <Ionicons name="thumbs-down-outline" size={16} color={theme.colors.textSecondary} />
              <Text style={styles.helpfulText}>Not helpful ({faq.notHelpful})</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );

  const renderFAQTab = () => (
    <View style={styles.tabContent}>
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={theme.colors.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search FAQs..."
          placeholderTextColor={theme.colors.textSecondary}
          value={searchQuery}
          onChangeText={handleSearch}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color={theme.colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {/* Category Filter */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
        {categories.map((category) => (
          <TouchableOpacity
            key={category.id}
            style={[
              styles.categoryChip,
              selectedCategory === category.id && styles.categoryChipActive
            ]}
            onPress={() => setSelectedCategory(category.id)}
          >
            <Ionicons
              name={category.icon as any}
              size={16}
              color={selectedCategory === category.id ? theme.colors.background : theme.colors.primary}
            />
            <Text
              style={[
                styles.categoryChipText,
                selectedCategory === category.id && styles.categoryChipTextActive
              ]}
            >
              {category.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* FAQs List */}
      <ScrollView style={styles.faqList}>
        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.primary} style={styles.loader} />
        ) : filteredFaqs.length > 0 ? (
          filteredFaqs.map(renderFAQ)
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="help-circle-outline" size={48} color={theme.colors.textSecondary} />
            <Text style={styles.emptyText}>
              {searchQuery ? 'No FAQs found for your search' : 'No FAQs available'}
            </Text>
          </View>
        )}
      </ScrollView>
    </View>
  );

  const renderContactTab = () => (
    <KeyboardAvoidingView
      style={styles.tabContent}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView style={styles.contactForm}>
        <Text style={styles.formLabel}>Category *</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
          {supportCategories.map((category) => (
            <TouchableOpacity
              key={category.id}
              style={[
                styles.categoryChip,
                contactForm.category === category.id && styles.categoryChipActive
              ]}
              onPress={() => setContactForm(prev => ({ ...prev, category: category.id }))}
            >
              <Ionicons
                name={category.icon as any}
                size={16}
                color={contactForm.category === category.id ? theme.colors.background : theme.colors.primary}
              />
              <Text
                style={[
                  styles.categoryChipText,
                  contactForm.category === category.id && styles.categoryChipTextActive
                ]}
              >
                {category.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        <Text style={styles.formLabel}>Subject *</Text>
        <TextInput
          style={styles.textInput}
          placeholder="Brief description of your issue"
          placeholderTextColor={theme.colors.textSecondary}
          value={contactForm.subject}
          onChangeText={(text) => setContactForm(prev => ({ ...prev, subject: text }))}
        />

        <Text style={styles.formLabel}>Description *</Text>
        <TextInput
          style={[styles.textInput, styles.textArea]}
          placeholder="Please provide detailed information about your issue"
          placeholderTextColor={theme.colors.textSecondary}
          value={contactForm.description}
          onChangeText={(text) => setContactForm(prev => ({ ...prev, description: text }))}
          multiline
          numberOfLines={6}
          textAlignVertical="top"
        />

        <TouchableOpacity
          style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
          onPress={submitSupportTicket}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator size="small" color={theme.colors.background} />
          ) : (
            <>
              <Ionicons name="send" size={18} color={theme.colors.background} />
              <Text style={styles.submitButtonText}>Submit Ticket</Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Help Center</Text>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'faq' && styles.tabActive]}
          onPress={() => setActiveTab('faq')}
        >
          <Ionicons
            name="help-circle-outline"
            size={20}
            color={activeTab === 'faq' ? theme.colors.primary : theme.colors.textSecondary}
          />
          <Text
            style={[
              styles.tabText,
              activeTab === 'faq' && styles.tabTextActive
            ]}
          >
            FAQ
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, activeTab === 'contact' && styles.tabActive]}
          onPress={() => setActiveTab('contact')}
        >
          <Ionicons
            name="mail-outline"
            size={20}
            color={activeTab === 'contact' ? theme.colors.primary : theme.colors.textSecondary}
          />
          <Text
            style={[
              styles.tabText,
              activeTab === 'contact' && styles.tabTextActive
            ]}
          >
            Contact Us
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      {activeTab === 'faq' ? renderFAQTab() : renderContactTab()}
    </SafeAreaView>
  );
}

const getStyles = (theme: any) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  backButton: {
    marginRight: theme.spacing.md,
  },
  headerTitle: {
    fontSize: theme.typography.large,
    fontWeight: '600',
    color: theme.colors.text,
  },
  tabNavigation: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.md,
    gap: theme.spacing.xs,
  },
  tabActive: {
    borderBottomWidth: 2,
    borderBottomColor: theme.colors.primary,
  },
  tabText: {
    fontSize: theme.typography.medium,
    color: theme.colors.textSecondary,
  },
  tabTextActive: {
    color: theme.colors.primary,
    fontWeight: '600',
  },
  tabContent: {
    flex: 1,
    padding: theme.spacing.md,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    marginBottom: theme.spacing.md,
    gap: theme.spacing.sm,
  },
  searchInput: {
    flex: 1,
    fontSize: theme.typography.medium,
    color: theme.colors.text,
  },
  categoryScroll: {
    marginBottom: theme.spacing.md,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.colors.surface,
    borderWidth: 1,
    borderColor: theme.colors.primary,
    borderRadius: theme.borderRadius.full,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    marginRight: theme.spacing.sm,
    gap: theme.spacing.xs,
  },
  categoryChipActive: {
    backgroundColor: theme.colors.primary,
  },
  categoryChipText: {
    fontSize: theme.typography.small,
    color: theme.colors.primary,
    fontWeight: '500',
  },
  categoryChipTextActive: {
    color: theme.colors.background,
  },
  faqList: {
    flex: 1,
  },
  faqItem: {
    backgroundColor: theme.colors.card,
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing.sm,
    overflow: 'hidden',
    ...theme.shadows.small,
  },
  faqQuestion: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: theme.spacing.md,
  },
  questionText: {
    flex: 1,
    fontSize: theme.typography.medium,
    fontWeight: '500',
    color: theme.colors.text,
    marginRight: theme.spacing.sm,
  },
  faqAnswer: {
    paddingHorizontal: theme.spacing.md,
    paddingBottom: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: theme.colors.border,
  },
  answerText: {
    fontSize: theme.typography.medium,
    color: theme.colors.textSecondary,
    lineHeight: 22,
    marginBottom: theme.spacing.md,
  },
  faqActions: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  helpfulButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  helpfulText: {
    fontSize: theme.typography.small,
    color: theme.colors.textSecondary,
  },
  loader: {
    marginTop: theme.spacing.xl,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.xl,
    gap: theme.spacing.md,
  },
  emptyText: {
    fontSize: theme.typography.medium,
    color: theme.colors.textSecondary,
    textAlign: 'center',
  },
  contactForm: {
    flex: 1,
  },
  formLabel: {
    fontSize: theme.typography.medium,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: theme.spacing.sm,
    marginTop: theme.spacing.md,
  },
  textInput: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius.md,
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    fontSize: theme.typography.medium,
    color: theme.colors.text,
    borderWidth: 1,
    borderColor: theme.colors.border,
    marginBottom: theme.spacing.md,
  },
  textArea: {
    height: 120,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: theme.colors.primary,
    borderRadius: theme.borderRadius.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.md,
    marginTop: theme.spacing.lg,
    gap: theme.spacing.sm,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    fontSize: theme.typography.medium,
    fontWeight: '600',
    color: theme.colors.background,
  },
});