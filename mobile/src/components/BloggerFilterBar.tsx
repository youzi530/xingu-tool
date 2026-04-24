import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Colors, FontSize, Radius, Spacing } from '../theme';
import { Blogger } from '../types';
import { BloggerAvatar } from './BloggerAvatar';

interface Props {
  bloggers: Blogger[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}

export function BloggerFilterBar({ bloggers, selectedId, onSelect }: Props) {
  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {/* 全部 */}
        <TouchableOpacity
          style={[styles.chip, selectedId === null && styles.chipActive]}
          onPress={() => onSelect(null)}
          activeOpacity={0.8}
        >
          <Text style={[styles.chipText, selectedId === null && styles.chipTextActive]}>
            全部
          </Text>
        </TouchableOpacity>

        {bloggers.map((b) => {
          const isActive = selectedId === b.id;
          return (
            <TouchableOpacity
              key={b.id}
              style={[styles.chip, isActive && styles.chipActive]}
              onPress={() => onSelect(isActive ? null : b.id)}
              activeOpacity={0.8}
            >
              <BloggerAvatar blogger={b} size={18} />
              <Text style={[styles.chipText, isActive && styles.chipTextActive]}>
                {b.name}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  scrollContent: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: Spacing.md,
    paddingVertical: 6,
    borderRadius: Radius.full,
    backgroundColor: Colors.surfaceSecondary,
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  chipActive: {
    backgroundColor: Colors.primary + '12',
    borderColor: Colors.primary,
  },
  chipText: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  chipTextActive: {
    color: Colors.primary,
    fontWeight: '700',
  },
});
