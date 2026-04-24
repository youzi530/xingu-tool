import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, FontSize, Radius, Spacing } from '../theme';

const REC_CONFIG: Record<string, { color: string; bg: string; icon: string }> = {
  '积极': { color: Colors.recPositive, bg: '#D1FAE5', icon: '▲' },
  '中性': { color: Colors.recNeutral, bg: '#FEF3C7', icon: '◆' },
  '谨慎': { color: Colors.recCautious, bg: '#FEE2E2', icon: '▼' },
};

interface Props {
  recommendation: string;
}

export function RecommendationTag({ recommendation }: Props) {
  const cfg = REC_CONFIG[recommendation] ?? { color: Colors.textSecondary, bg: Colors.surfaceSecondary, icon: '—' };

  return (
    <View style={[styles.tag, { backgroundColor: cfg.bg }]}>
      <Text style={[styles.icon, { color: cfg.color }]}>{cfg.icon}</Text>
      <Text style={[styles.label, { color: cfg.color }]}>{recommendation}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: Radius.full,
    gap: 3,
  },
  icon: {
    fontSize: 8,
    fontWeight: '900',
  },
  label: {
    fontSize: FontSize.xs,
    fontWeight: '700',
  },
});
