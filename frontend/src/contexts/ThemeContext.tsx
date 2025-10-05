import React, { createContext, useContext, useEffect, useState } from 'react';
import { Appearance, ColorSchemeName } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Constants from 'expo-constants';

// Theme colors and styles
const lightTheme = {
  colors: {
    primary: '#007AFF',
    accent: '#FF3B30',
    background: '#FFFFFF',
    surface: '#F8F9FA',
    card: '#FFFFFF',
    text: '#000000',
    textSecondary: '#666666',
    border: '#E1E4E8',
    notification: '#FF3B30',
    success: '#34C759',
    warning: '#FF9500',
    error: '#FF3B30',
    // Social media specific colors
    heart: '#FF3B30',
    comment: '#8E8E93',
    share: '#8E8E93',
    message: '#007AFF',
    // Status colors
    online: '#34C759',
    offline: '#8E8E93',
    away: '#FF9500',
    busy: '#FF3B30'
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48
  },
  typography: {
    small: 12,
    medium: 16,
    large: 20,
    extraLarge: 24,
    title: 28,
    display: 34
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999
  },
  shadows: {
    small: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.08,
      shadowRadius: 2,
      elevation: 1
    },
    medium: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.12,
      shadowRadius: 4,
      elevation: 2
    },
    large: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.16,
      shadowRadius: 8,
      elevation: 4
    }
  }
};

const darkTheme = {
  ...lightTheme,
  colors: {
    primary: '#0A84FF',
    accent: '#FF453A',
    background: '#000000',
    surface: '#1C1C1E',
    card: '#2C2C2E',
    text: '#FFFFFF',
    textSecondary: '#8E8E93',
    border: '#38383A',
    notification: '#FF453A',
    success: '#32D74B',
    warning: '#FF9F0A',
    error: '#FF453A',
    // Social media specific colors
    heart: '#FF453A',
    comment: '#8E8E93',
    share: '#8E8E93',
    message: '#0A84FF',
    // Status colors
    online: '#32D74B',
    offline: '#8E8E93',
    away: '#FF9F0A',
    busy: '#FF453A'
  }
};

// High contrast themes for accessibility
const lightHighContrastTheme = {
  ...lightTheme,
  colors: {
    ...lightTheme.colors,
    primary: '#0051D5',
    background: '#FFFFFF',
    surface: '#FFFFFF',
    card: '#FFFFFF',
    text: '#000000',
    textSecondary: '#000000',
    border: '#000000'
  }
};

const darkHighContrastTheme = {
  ...darkTheme,
  colors: {
    ...darkTheme.colors,
    primary: '#409CFF',
    background: '#000000',
    surface: '#000000',
    card: '#1C1C1C',
    text: '#FFFFFF',
    textSecondary: '#FFFFFF',
    border: '#FFFFFF'
  }
};

interface ThemeSettings {
  themeMode: 'light' | 'dark' | 'system';
  primaryColor: string;
  accentColor: string;
  fontSize: 'small' | 'medium' | 'large' | 'extraLarge';
  fontFamily: string;
  highContrast: boolean;
  reduceMotion: boolean;
  colorBlindMode: 'protanopia' | 'deuteranopia' | 'tritanopia' | null;
}

interface ThemeContextType {
  theme: typeof lightTheme;
  isDarkMode: boolean;
  themeSettings: ThemeSettings;
  updateTheme: (settings: Partial<ThemeSettings>) => Promise<void>;
  getScaledSize: (size: number) => number;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'theme_settings';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeSettings, setThemeSettings] = useState<ThemeSettings>({
    themeMode: 'system',
    primaryColor: '#007AFF',
    accentColor: '#FF3B30',
    fontSize: 'medium',
    fontFamily: 'system',
    highContrast: false,
    reduceMotion: false,
    colorBlindMode: null
  });

  const [systemColorScheme, setSystemColorScheme] = useState<ColorSchemeName>(
    Appearance.getColorScheme()
  );

  // Determine if dark mode should be used
  const isDarkMode = 
    themeSettings.themeMode === 'dark' ||
    (themeSettings.themeMode === 'system' && systemColorScheme === 'dark');

  // Get the current theme based on settings
  const getCurrentTheme = () => {
    let baseTheme = isDarkMode ? darkTheme : lightTheme;

    // Apply high contrast if enabled
    if (themeSettings.highContrast) {
      baseTheme = isDarkMode ? darkHighContrastTheme : lightHighContrastTheme;
    }

    // Apply custom colors
    const customTheme = {
      ...baseTheme,
      colors: {
        ...baseTheme.colors,
        primary: themeSettings.primaryColor,
        accent: themeSettings.accentColor
      }
    };

    // Apply font size scaling
    const fontSizeMultiplier = getFontSizeMultiplier(themeSettings.fontSize);
    customTheme.typography = {
      small: Math.round(12 * fontSizeMultiplier),
      medium: Math.round(16 * fontSizeMultiplier),
      large: Math.round(20 * fontSizeMultiplier),
      extraLarge: Math.round(24 * fontSizeMultiplier),
      title: Math.round(28 * fontSizeMultiplier),
      display: Math.round(34 * fontSizeMultiplier)
    };

    return customTheme;
  };

  const getFontSizeMultiplier = (fontSize: string) => {
    switch (fontSize) {
      case 'small': return 0.85;
      case 'medium': return 1.0;
      case 'large': return 1.15;
      case 'extraLarge': return 1.3;
      default: return 1.0;
    }
  };

  const getScaledSize = (size: number) => {
    const multiplier = getFontSizeMultiplier(themeSettings.fontSize);
    return Math.round(size * multiplier);
  };

  // Load theme settings from storage
  useEffect(() => {
    const loadThemeSettings = async () => {
      try {
        const stored = await AsyncStorage.getItem(THEME_STORAGE_KEY);
        if (stored) {
          const parsedSettings = JSON.parse(stored);
          setThemeSettings(prev => ({ ...prev, ...parsedSettings }));
        }
      } catch (error) {
        console.log('Error loading theme settings:', error);
      }
    };

    loadThemeSettings();
  }, []);

  // Listen for system theme changes
  useEffect(() => {
    const subscription = Appearance.addChangeListener(({ colorScheme }) => {
      setSystemColorScheme(colorScheme);
    });

    return () => subscription?.remove();
  }, []);

  // Sync with backend when settings change
  useEffect(() => {
    const syncWithBackend = async () => {
      try {
        const backendUrl = Constants.expoConfig?.extra?.backendUrl || process.env.EXPO_PUBLIC_BACKEND_URL;
        if (!backendUrl) return;

        // Get auth token (you'll need to implement this based on your auth context)
        // const token = await getAuthToken();
        
        // if (token) {
        //   await fetch(`${backendUrl}/api/settings/theme`, {
        //     method: 'PUT',
        //     headers: {
        //       'Content-Type': 'application/json',
        //       'Authorization': `Bearer ${token}`
        //     },
        //     body: JSON.stringify(themeSettings)
        //   });
        // }
      } catch (error) {
        console.log('Error syncing theme with backend:', error);
      }
    };

    syncWithBackend();
  }, [themeSettings]);

  const updateTheme = async (newSettings: Partial<ThemeSettings>) => {
    const updatedSettings = { ...themeSettings, ...newSettings };
    setThemeSettings(updatedSettings);

    try {
      await AsyncStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(updatedSettings));
    } catch (error) {
      console.log('Error saving theme settings:', error);
    }
  };

  const theme = getCurrentTheme();

  return (
    <ThemeContext.Provider
      value={{
        theme,
        isDarkMode,
        themeSettings,
        updateTheme,
        getScaledSize
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Hook for getting themed styles
export function useThemedStyles<T>(
  stylesFn: (theme: typeof lightTheme) => T
): T {
  const { theme } = useTheme();
  return stylesFn(theme);
}