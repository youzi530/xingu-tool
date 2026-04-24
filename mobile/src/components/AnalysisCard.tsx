import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Colors, FontSize, Radius, Shadow, Spacing } from '../theme';
import { Analysis } from '../types';
import { BloggerAvatar } from './BloggerAvatar';
import { RecommendationTag } from './RecommendationTag';

function formatDate(dateStr?: string) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return '今天';
  if (diffDays === 1) return '昨天';
  if (diffDays < 7) return `${diffDays}天前`;
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

function formatCount(n: number) {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

interface Props {
  analysis: Analysis;
  onPress: () => void;
}

export function AnalysisCard({ analysis, onPress }: Props) {
  const blogger = analysis.blogger;

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.92}>
      {/* Header：博主信息 */}
      <View style={styles.header}>
        {blogger && <BloggerAvatar blogger={blogger} size={32} />}
        <View style={styles.headerText}>
          <Text style={styles.bloggerName}>{blogger?.name ?? '未知博主'}</Text>
          <Text style={styles.date}>{formatDate(analysis.published_at)}</Text>
        </View>
        {analysis.recommendation && (
          <RecommendationTag recommendation={analysis.recommendation} />
        )}
      </View>

      {/* 标题 */}
      <Text style={styles.title} numberOfLines={2}>{analysis.title}</Text>

      {/* 摘要 */}
      {analysis.summary && (
        <Text style={styles.summary} numberOfLines={3}>{analysis.summary}</Text>
      )}

      {/* Footer：阅读量 / 点赞 / 来源 */}
      <View style={styles.footer}>
        <View style={styles.footerLeft}>
          <Text style={styles.stat}>👁 {formatCount(analysis.view_count)}</Text>
          <Text style={styles.stat}>👍 {formatCount(analysis.like_count)}</Text>
        </View>
        <View style={styles.channelBadge}>
          <Text style={styles.channelText}>
            {analysis.source_channel === 'wechat' ? '公众号' : analysis.source_channel}
          </Text>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.lg,
    marginHorizontal: Spacing.lg,
    marginBottom: Spacing.md,
    ...Shadow.card,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  headerText: {
    flex: 1,
  },
  bloggerName: {
    fontSize: FontSize.sm,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  date: {
    fontSize: FontSize.xs,
    color: Colors.textTertiary,
    marginTop: 1,
  },
  title: {
    fontSize: FontSize.md,
    fontWeight: '700',
    color: Colors.textPrimary,
    lineHeight: 22,
    marginBottom: Spacing.sm,
  },
  summary: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
    marginBottom: Spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: Spacing.xs,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
  },
  footerLeft: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  stat: {
    fontSize: FontSize.xs,
    color: Colors.textTertiary,
  },
  channelBadge: {
    backgroundColor: Colors.channelWechat + '20',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: Radius.full,
  },
  channelText: {
    fontSize: FontSize.xs,
    color: Colors.channelWechat,
    fontWeight: '600',
  },
});
