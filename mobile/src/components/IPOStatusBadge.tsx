import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, FontSize, Radius, Spacing } from '../theme';
import { IPOStatus } from '../types';

const STATUS_CONFIG: Record<IPOStatus, { label: string; color: string; bg: string }> = {
  upcoming: { label: '即将认购', color: Colors.statusUpcoming, bg: '#F3EFFE' },
  subscribing: { label: '认购中', color: Colors.statusSubscribing, bg: '#D1FAE5' },
  listing: { label: '即将上市', color: Colors.statusListing, bg: '#FEF3C7' },
  listed: { label: '已上市', color: Colors.statusListed, bg: '#F3F4F6' },
};

interface Props {
  status: IPOStatus;
  size?: 'sm' | 'md';
}

export function IPOStatusBadge({ status, size = 'md' }: Props) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.upcoming;
  const isSmall = size === 'sm';

  return (
    <View style={[styles.badge, { backgroundColor: cfg.bg }, isSmall && styles.badgeSm]}>
      <View style={[styles.dot, { backgroundColor: cfg.color }]} />
      <Text style={[styles.label, { color: cfg.color }, isSmall && styles.labelSm]}>
        {cfg.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: Radius.full,
    gap: 4,
  },
  badgeSm: {
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  label: {
    fontSize: FontSize.sm,
    fontWeight: '600',
  },
  labelSm: {
    fontSize: FontSize.xs,
  },
});
