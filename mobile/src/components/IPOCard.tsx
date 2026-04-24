import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors, FontSize, Radius, Shadow, Spacing } from '../theme';
import { IPO } from '../types';
import { IPOStatusBadge } from './IPOStatusBadge';

function formatPriceRange(min?: string, max?: string) {
  if (!min && !max) return '—';
  if (min === max || !max) return `HK$${min}`;
  return `HK$${min}–${max}`;
}

function formatDate(d?: string) {
  if (!d) return '—';
  const dt = new Date(d);
  return `${dt.getMonth() + 1}/${dt.getDate()}`;
}

interface Props {
  ipo: IPO;
  onPress: () => void;
}

export function IPOCard({ ipo, onPress }: Props) {
  const isActive = ipo.status === 'subscribing' || ipo.status === 'listing';

  return (
    <TouchableOpacity
      style={[styles.card, isActive && styles.cardActive]}
      onPress={onPress}
      activeOpacity={0.92}
    >
      {/* 左侧色条 */}
      {isActive && <View style={styles.activeBar} />}

      <View style={styles.content}>
        {/* 股票代码 + 状态 */}
        <View style={styles.topRow}>
          <View style={styles.codeContainer}>
            <Text style={styles.code}>{ipo.stock_code}</Text>
            <Text style={styles.exchange}>{ipo.exchange}</Text>
          </View>
          <IPOStatusBadge status={ipo.status} />
        </View>

        {/* 股票名称 */}
        <Text style={styles.name}>{ipo.stock_name}</Text>

        {/* 行业 */}
        {ipo.industry && (
          <Text style={styles.industry}>{ipo.industry}</Text>
        )}

        {/* 发行价 / 认购时间 */}
        <View style={styles.metaRow}>
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>发行价</Text>
            <Text style={styles.metaValue}>{formatPriceRange(ipo.ipo_price_min, ipo.ipo_price_max)}</Text>
          </View>
          <View style={styles.metaDivider} />
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>认购期</Text>
            <Text style={styles.metaValue}>
              {formatDate(ipo.subscribe_start)}–{formatDate(ipo.subscribe_end)}
            </Text>
          </View>
          <View style={styles.metaDivider} />
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>上市日</Text>
            <Text style={styles.metaValue}>{formatDate(ipo.listing_date)}</Text>
          </View>
        </View>

        {/* 分析数量 */}
        {ipo.analysis_count > 0 && (
          <View style={styles.analysisChip}>
            <Text style={styles.analysisText}>📊 {ipo.analysis_count} 篇分析</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    marginHorizontal: Spacing.lg,
    marginBottom: Spacing.md,
    flexDirection: 'row',
    overflow: 'hidden',
    ...Shadow.card,
  },
  cardActive: {
    borderWidth: 1,
    borderColor: Colors.primary + '30',
  },
  activeBar: {
    width: 4,
    backgroundColor: Colors.primary,
    borderTopLeftRadius: Radius.lg,
    borderBottomLeftRadius: Radius.lg,
  },
  content: {
    flex: 1,
    padding: Spacing.lg,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  codeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  code: {
    fontSize: FontSize.sm,
    fontWeight: '700',
    color: Colors.primary,
    letterSpacing: 0.5,
  },
  exchange: {
    fontSize: FontSize.xs,
    color: Colors.textTertiary,
    backgroundColor: Colors.surfaceSecondary,
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: Radius.sm,
  },
  name: {
    fontSize: FontSize.xl,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginBottom: 2,
  },
  industry: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  metaItem: {
    flex: 1,
    alignItems: 'center',
  },
  metaLabel: {
    fontSize: FontSize.xs,
    color: Colors.textTertiary,
    marginBottom: 2,
  },
  metaValue: {
    fontSize: FontSize.sm,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  metaDivider: {
    width: 1,
    height: 28,
    backgroundColor: Colors.border,
  },
  analysisChip: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.primary + '12',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    borderRadius: Radius.full,
    marginTop: Spacing.xs,
  },
  analysisText: {
    fontSize: FontSize.xs,
    color: Colors.primary,
    fontWeight: '600',
  },
});
