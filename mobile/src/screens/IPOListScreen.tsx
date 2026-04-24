import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, RefreshControl,
  TouchableOpacity, ActivityIndicator, StatusBar, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Colors, FontSize, Radius, Spacing } from '../theme';
import { IPO, IPOStatus, RootStackParamList } from '../types';
import { api, MOCK_IPOS } from '../services/api';
import { IPOCard } from '../components/IPOCard';

type NavProp = NativeStackNavigationProp<RootStackParamList, 'MainTabs'>;

const STATUS_TABS: { key: IPOStatus | 'all'; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'subscribing', label: '认购中' },
  { key: 'upcoming', label: '即将认购' },
  { key: 'listing', label: '即将上市' },
  { key: 'listed', label: '已上市' },
];

interface Props {
  navigation: NavProp;
}

export function IPOListScreen({ navigation }: Props) {
  const [ipos, setIpos] = useState<IPO[]>([]);
  const [activeTab, setActiveTab] = useState<IPOStatus | 'all'>('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadIpos = useCallback(async (tab: IPOStatus | 'all') => {
    try {
      const data = await api.getIPOs(tab === 'all' ? undefined : tab);
      setIpos(data);
    } catch {
      // 后端未启动时回退到 Mock 数据
      const filtered = tab === 'all' ? MOCK_IPOS : MOCK_IPOS.filter(i => i.status === tab);
      setIpos(filtered);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadIpos(activeTab);
  }, [activeTab, loadIpos]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadIpos(activeTab);
  };

  const handleTabChange = (tab: IPOStatus | 'all') => {
    setActiveTab(tab);
    setLoading(true);
    setIpos([]);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={Colors.primary} />

      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>新股通</Text>
          <Text style={styles.headerSub}>港股打新分析聚合</Text>
        </View>
        <View style={styles.headerBadge}>
          <Text style={styles.headerBadgeText}>HKEX</Text>
        </View>
      </View>

      {/* Tab 栏 */}
      <View style={styles.tabBar}>
        {STATUS_TABS.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => handleTabChange(tab.key)}
            activeOpacity={0.8}
          >
            <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* 内容区 */}
      {loading ? (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>加载中...</Text>
        </View>
      ) : (
        <FlatList
          data={ipos}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => (
            <IPOCard
              ipo={item}
              onPress={() =>
                navigation.navigate('IPODetail', {
                  ipoId: item.id,
                  stockName: item.stock_name,
                })
              }
            />
          )}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              colors={[Colors.primary]}
              tintColor={Colors.primary}
            />
          }
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>📋</Text>
              <Text style={styles.emptyText}>暂无新股数据</Text>
              <Text style={styles.emptySubText}>下拉刷新重试</Text>
            </View>
          }
          showsVerticalScrollIndicator={false}
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  headerBadge: {
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: Radius.sm,
  },
  headerBadgeText: {
    fontSize: FontSize.sm,
    fontWeight: '900',
    color: '#fff',
    letterSpacing: 1.5,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: Spacing.xs,
  },
  tab: {
    flex: 1,
    paddingVertical: 6,
    alignItems: 'center',
    borderRadius: Radius.md,
  },
  tabActive: {
    backgroundColor: Colors.primary,
  },
  tabText: {
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  tabTextActive: {
    color: '#fff',
    fontWeight: '700',
  },
  list: {
    paddingTop: Spacing.lg,
    paddingBottom: Spacing.xxxl,
  },
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
  },
  loadingText: {
    fontSize: FontSize.md,
    color: Colors.textSecondary,
  },
  empty: {
    alignItems: 'center',
    paddingTop: 80,
    gap: Spacing.sm,
  },
  emptyIcon: {
    fontSize: 48,
  },
  emptyText: {
    fontSize: FontSize.lg,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  emptySubText: {
    fontSize: FontSize.sm,
    color: Colors.textTertiary,
  },
});
