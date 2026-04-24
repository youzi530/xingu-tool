import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors, FontSize, Radius, Shadow, Spacing } from '../theme';
import { Blogger } from '../types';
import { api, MOCK_BLOGGERS } from '../services/api';
import { BloggerAvatar } from '../components/BloggerAvatar';

const CHANNEL_LABEL: Record<string, string> = {
  wechat: '微信公众号',
  xhs: '小红书',
  broker: '券商App',
  other: '其他',
};

export function BloggersScreen() {
  const [bloggers, setBloggers] = useState<Blogger[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getBloggers()
      .then(setBloggers)
      .catch(() => setBloggers(MOCK_BLOGGERS))
      .finally(() => setLoading(false));
  }, []);

  const renderBlogger = ({ item }: { item: Blogger }) => (
    <View style={styles.card}>
      <BloggerAvatar blogger={item} size={52} />
      <View style={styles.cardContent}>
        <View style={styles.cardTop}>
          <Text style={styles.name}>{item.name}</Text>
          <View style={styles.channelBadge}>
            <Text style={styles.channelText}>{CHANNEL_LABEL[item.channel] ?? item.channel}</Text>
          </View>
        </View>
        {item.follower_count && (
          <Text style={styles.followers}>👥 {item.follower_count} 关注者</Text>
        )}
        {item.description && (
          <Text style={styles.desc} numberOfLines={2}>{item.description}</Text>
        )}
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>分析博主</Text>
        <Text style={styles.headerSub}>精选港股打新内容创作者</Text>
      </View>

      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      ) : (
        <FlatList
          data={bloggers}
          keyExtractor={(item) => String(item.id)}
          renderItem={renderBlogger}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          ListHeaderComponent={
            <Text style={styles.listHeader}>共 {bloggers.length} 位博主</Text>
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.xl,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.xl,
  },
  headerTitle: {
    fontSize: FontSize.xxl,
    fontWeight: '900',
    color: '#fff',
    letterSpacing: 1,
  },
  headerSub: {
    fontSize: FontSize.sm,
    color: 'rgba(255,255,255,0.75)',
    marginTop: 2,
  },
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  listHeader: {
    fontSize: FontSize.sm,
    color: Colors.textTertiary,
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.sm,
  },
  list: {
    paddingTop: Spacing.lg,
    paddingBottom: Spacing.xxxl,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    marginHorizontal: Spacing.lg,
    marginBottom: Spacing.md,
    padding: Spacing.lg,
    flexDirection: 'row',
    gap: Spacing.md,
    ...Shadow.card,
  },
  cardContent: {
    flex: 1,
    gap: 4,
  },
  cardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  name: {
    fontSize: FontSize.lg,
    fontWeight: '800',
    color: Colors.textPrimary,
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
  followers: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
  desc: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
});
