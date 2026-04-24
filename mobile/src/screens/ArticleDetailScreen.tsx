import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ActivityIndicator,
  Alert, Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { WebView } from 'react-native-webview';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { Colors, FontSize, Radius, Spacing } from '../theme';
import { RootStackParamList } from '../types';

type NavProp = NativeStackNavigationProp<RootStackParamList, 'ArticleDetail'>;
type RoutePropType = RouteProp<RootStackParamList, 'ArticleDetail'>;

interface Props {
  navigation: NavProp;
  route: RoutePropType;
}

export function ArticleDetailScreen({ navigation, route }: Props) {
  const { url, title } = route.params;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const openInBrowser = async () => {
    try {
      await Linking.openURL(url);
    } catch {
      Alert.alert('无法打开链接', url);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* 导航栏 */}
      <View style={styles.navBar}>
        <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={styles.backIcon}>←</Text>
        </TouchableOpacity>
        <Text style={styles.navTitle} numberOfLines={1}>{title}</Text>
        <TouchableOpacity style={styles.browserBtn} onPress={openInBrowser}>
          <Text style={styles.browserIcon}>🔗</Text>
        </TouchableOpacity>
      </View>

      {/* WebView */}
      {error ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>😓</Text>
          <Text style={styles.errorTitle}>页面加载失败</Text>
          <Text style={styles.errorSub}>公众号文章可能需要在微信内打开</Text>
          <TouchableOpacity style={styles.openBtn} onPress={openInBrowser}>
            <Text style={styles.openBtnText}>在浏览器中打开</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <WebView
          source={{ uri: url }}
          style={styles.webview}
          onLoadStart={() => setLoading(true)}
          onLoadEnd={() => setLoading(false)}
          onError={() => {
            setLoading(false);
            setError(true);
          }}
          userAgent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
          javaScriptEnabled
          domStorageEnabled
          renderLoading={() => (
            <View style={styles.webviewLoading}>
              <ActivityIndicator size="large" color={Colors.primary} />
            </View>
          )}
          startInLoadingState
        />
      )}

      {loading && !error && (
        <View style={[styles.loadingOverlay, { pointerEvents: 'none' }]}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.surface,
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
    fontSize: FontSize.md,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginHorizontal: Spacing.sm,
  },
  browserBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  browserIcon: {
    fontSize: 20,
  },
  webview: {
    flex: 1,
  },
  webviewLoading: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.surface,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 100, left: 0, right: 0, bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.6)',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
    paddingHorizontal: Spacing.xxxl,
  },
  errorIcon: { fontSize: 48 },
  errorTitle: {
    fontSize: FontSize.lg,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  errorSub: {
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  openBtn: {
    marginTop: Spacing.md,
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.xxl,
    paddingVertical: Spacing.md,
    borderRadius: Radius.full,
  },
  openBtnText: {
    color: '#fff',
    fontSize: FontSize.md,
    fontWeight: '700',
  },
});
