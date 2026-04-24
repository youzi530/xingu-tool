import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { Colors, FontSize } from '../theme';
import { Blogger } from '../types';

const BLOGGER_COLORS = [
  '#C8102E', '#D4A017', '#059669', '#3B82F6',
  '#8B5CF6', '#EC4899', '#14B8A6', '#F97316',
];

function getColor(name: string) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return BLOGGER_COLORS[Math.abs(hash) % BLOGGER_COLORS.length];
}

interface Props {
  blogger: Blogger;
  size?: number;
}

export function BloggerAvatar({ blogger, size = 36 }: Props) {
  const color = getColor(blogger.name);
  const initial = blogger.name.charAt(0);

  if (blogger.avatar_url) {
    return (
      <Image
        source={{ uri: blogger.avatar_url }}
        style={[styles.image, { width: size, height: size, borderRadius: size / 2 }]}
      />
    );
  }

  return (
    <View style={[styles.fallback, { width: size, height: size, borderRadius: size / 2, backgroundColor: color }]}>
      <Text style={[styles.initial, { fontSize: size * 0.4 }]}>{initial}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  image: {
    backgroundColor: Colors.border,
  },
  fallback: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  initial: {
    color: '#fff',
    fontWeight: '700',
  },
});
