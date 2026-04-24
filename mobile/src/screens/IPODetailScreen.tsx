import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { Colors, FontSize, Radius, Shadow, Spacing } from '../theme';
import { Blogger, IPOWithAnalyses, RootStackParamList } from '../types';
import { api, MOCK_BLOGGERS } from '../services/api';
import { IPOStatusBadge } from '../components/IPOStatusBadge';
import { AnalysisCard } from '../components/AnalysisCard';
import { BloggerFilterBar } from '../components/BloggerFilterBar';

type NavProp = NativeStackNavigationProp<RootStackParamList, 'IPODetail'>;
type RoutePropType = RouteProp<RootStackParamList, 'IPODetail'>;

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <View style={infoStyles.item}>
      <Text style={infoStyles.label}>{label}</Text>
      <Text style={infoStyles.value}>{value}</Text>
    </View>
  );
}

const infoStyles = StyleSheet.create({
  item: { alignItems: 'center', flex: 1 },
  label: { fontSize: FontSize.xs, color: Colors.textTertiary, marginBottom: 2 },
  value: { fontSize: FontSize.sm, fontWeight: '700', color: Colors.textPrimary },
});

interface Props {
  navigation: NavProp;
  route: RoutePropType;
}

export function IPODetailScreen({ navigation, route }: Props) {
  const { ipoId, stockName } = route.params;

  const [detail, setDetail] = useState<IPOWithAnalyses | null>(null);
  const [bloggers, setBloggers] = useState<Blogger[]>([]);
  const [selectedBloggerId, setSelectedBloggerId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async (bloggerId: number | null) => {
    try {
      const [detailData, bloggerData] = await Promise.all([
        api.getIPODetail(ipoId, bloggerId ?? undefined),
        api.getBloggers(),
      ]);
      setDetail(detailData);
      setBloggers(bloggerData);
    } catch {
      setBloggers(MOCK_BLOGGERS);
      // Mock detail fallback
    } finally {
      setLoading(false);
    }
  }, [ipoId]);

  useEffect(() => {
    loadData(selectedBloggerId);
  }, [selectedBloggerId, loadData]);

  const handleBloggerSelect = (id: number | null) => {
    setSelectedBloggerId(id);
    setLoading(true);
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.navBar}>
          <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
            <Text style={styles.backIcon}>←</Text>
          </TouchableOpacity>
          <Text style={styles.navTitle}>{stockName}</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  const analyses = detail?.analyses ?? [];
  const activeBloggers = bloggers.filter(b =>
    analyses.some(a => a.blogger_id === b.id)
  );
  // show all bloggers in filter, not just ones with articles for this ipo
  const filterBloggers = bloggers.length > 0 ? bloggers : MOCK_BLOGGERS;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* 导航栏 */}
      <View style={styles.navBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
        <Text style={styles.navTitle}>{stockName}</Text>
        <View style={{ width: 40 }} />
      </View>

      <FlatList
        data={analyses}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <AnalysisCard
            analysis={item}
            onPress={() => {
              if (item.content_url) {
                navigation.navigate('ArticleDetail', {
                  url: item.content_url,
                  title: item.title,
                });
              }
            }}
          />
        )}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <>
            {/* 新股信息卡 */}
            {detail && (
              <View style={styles.ipoCard}>
                <View style={styles.ipoCardTop}>
                  <View>
                    <View style={styles.codeRow}>
                      <Text style={styles.stockCode}>{detail.stock_code}</Text>
                      <Text style={styles.exchange}>{detail.exchange}</Text>
                    </View>
                    <Text style={styles.stockName}>{detail.stock_name}</Text>
                    {detail.industry && (
                      <Text style={styles.industry}>{detail.industry}</Text>
                    )}
                  </View>
                  <IPOStatusBadge status={detail.status} />
                </View>

                {/* 核心指标第一行 */}
                <View style={styles.metaRow}>
                  <InfoItem
                    label="发行价"
                    value={
                      detail.ipo_price_min === detail.ipo_price_max
                        ? `HK$${detail.ipo_price_min ?? '—'}`
                        : `HK$${detail.ipo_price_min}–${detail.ipo_price_max}`
                    }
                  />
                  <View style={styles.metaDivider} />
                  <InfoItem label="每手股数" value={detail.lot_size ? `${detail.lot_size}股` : '—'} />
                  <View style={styles.metaDivider} />
                  <InfoItem
                    label="认购截止"
                    value={detail.subscribe_end
                      ? new Date(detail.subscribe_end).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) + ''
                      : '—'}
                  />
                  <View style={styles.metaDivider} />
                  <InfoItem
                    label="上市日期"
                    value={detail.listing_date
                      ? new Date(detail.listing_date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) + ''
                      : '—'}
                  />
                </View>

                {/* 核心指标第二行：中签日 + 市值 */}
                {(detail.allotment_date || detail.market_cap) && (
                  <View style={[styles.metaRow, { marginTop: -8 }]}>
                    {detail.allotment_date && (
                      <>
                        <InfoItem
                          label="中签公布"
                          value={new Date(detail.allotment_date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) + ''}
                        />
                        {detail.market_cap && <View style={styles.metaDivider} />}
                      </>
                    )}
                    {detail.market_cap && (
                      <InfoItem label="市值" value={detail.market_cap} />
                    )}
                    {/* 数据来源角标 */}
                    <View style={{ flex: 1, alignItems: 'flex-end' }}>
                      <Text style={styles.dataSourceTag}>
                        {detail.data_source === 'itick' ? '📡 iTick' : '✏️ 手动'}
                      </Text>
                    </View>
                  </View>
                )}

                {/* 公司简介 */}
                {detail.description && (
                  <Text style={styles.description} numberOfLines={3}>
                    {detail.description}
                  </Text>
                )}
              </View>
            )}

            {/* 博主筛选 */}
            <BloggerFilterBar
              bloggers={filterBloggers}
              selectedId={selectedBloggerId}
              onSelect={handleBloggerSelect}
            />

            {/* 分析列表 Header */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                📊 分析文章 {analyses.length > 0 ? `(${analyses.length})` : ''}
              </Text>
            </View>
          </>
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyIcon}>🔍</Text>
            <Text style={styles.emptyText}>暂无分析文章</Text>
            <Text style={styles.emptySubText}>
              {selectedBloggerId ? '该博主暂未发布分析，切换其他博主试试' : '敬请期待，我们持续更新中'}
            </Text>
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  navBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backIcon: {
    fontSize: 22,
    color: Colors.primary,
    fontWeight: '600',
  },
  navTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: FontSize.lg,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ipoCard: {
    backgroundColor: Colors.surface,
    margin: Spacing.lg,
    borderRadius: Radius.lg,
    padding: Spacing.xl,
    ...Shadow.card,
    borderTopWidth: 3,
    borderTopColor: Colors.primary,
  },
  ipoCardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: Spacing.lg,
  },
  codeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    marginBottom: 4,
  },
  stockCode: {
    fontSize: FontSize.sm,
    fontWeight: '700',
    color: Colors.primary,
  },
  exchange: {
    fontSize: FontSize.xs,
    color: Colors.textTertiary,
    backgroundColor: Colors.surfaceSecondary,
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: Radius.sm,
  },
  stockName: {
    fontSize: FontSize.xxl,
    fontWeight: '900',
    color: Colors.textPrimary,
    marginBottom: 2,
  },
  industry: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.background,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  metaDivider: {
    width: 1,
    height: 32,
    backgroundColor: Colors.border,
  },
  description: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  dataSourceTag: {
    fontSize: FontSize.xs,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  sectionHeader: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
  },
  sectionTitle: {
    fontSize: FontSize.md,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  list: {
    paddingBottom: Spacing.xxxl,
  },
  empty: {
    alignItems: 'center',
    paddingTop: 60,
    paddingHorizontal: Spacing.xxxl,
    gap: Spacing.sm,
  },
  emptyIcon: {
    fontSize: 40,
  },
  emptyText: {
    fontSize: FontSize.lg,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  emptySubText: {
    fontSize: FontSize.sm,
    color: Colors.textTertiary,
    textAlign: 'center',
    lineHeight: 20,
  },
});
