import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  Easing,
} from 'react-native-reanimated';

export interface ProgressBarProps {
  duration: number; // in milliseconds
  isActive: boolean;
  isPaused: boolean;
  onComplete: () => void;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  duration,
  isActive,
  isPaused,
  onComplete,
}) => {
  const progress = useSharedValue(0);

  const animatedStyle = useAnimatedStyle(() => {
    return {
      width: `${progress.value * 100}%`,
    };
  });

  useEffect(() => {
    if (isActive && !isPaused) {
      progress.value = withTiming(
        1,
        {
          duration: duration * (1 - progress.value),
          easing: Easing.linear,
        },
        (finished) => {
          if (finished) {
            onComplete();
          }
        }
      );
    }
  }, [isActive, isPaused, duration, onComplete]);

  useEffect(() => {
    if (!isActive) {
      progress.value = 0;
    }
  }, [isActive]);

  return (
    <View style={styles.container}>
      <View style={styles.background} />
      <Animated.View style={[styles.progress, animatedStyle]} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    height: 3,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 1.5,
    overflow: 'hidden',
    margin: 2,
  },
  background: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  progress: {
    height: '100%',
    backgroundColor: '#ffffff',
    borderRadius: 1.5,
  },
});