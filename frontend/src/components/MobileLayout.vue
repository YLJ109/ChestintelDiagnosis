/**
* 移动端布局组件 - 底部Tab导航
* 类似微信/支付宝的Tab切换体验
*/
<template>
    <div class="mobile-layout">
        <!-- 顶部标题栏 -->
        <header class="mobile-header" :style="{ paddingTop: safeAreaTop }">
            <div class="header-content">
                <h1 class="header-title">{{ currentTitle }}</h1>
            </div>
        </header>

        <!-- 可滑动内容区 -->
        <main class="mobile-content" ref="contentRef" @touchstart="onTouchStart" @touchmove="onTouchMove"
            @touchend="onTouchEnd">
            <div class="swipe-container" :style="{ transform: `translateX(-${currentTab * 100}%)` }">
                <!-- 首页 -->
                <div class="tab-page" data-tab="home">
                    <slot name="home" />
                </div>

                <!-- 报告 -->
                <div class="tab-page" data-tab="reports">
                    <slot name="reports" />
                </div>

                <!-- 分诊 -->
                <div class="tab-page" data-tab="triage">
                    <slot name="triage" />
                </div>

                <!-- AI咨询 -->
                <div class="tab-page" data-tab="chat">
                    <slot name="chat" />
                </div>

                <!-- 我的 -->
                <div class="tab-page" data-tab="profile">
                    <slot name="profile" />
                </div>
            </div>
        </main>

        <!-- 底部Tab导航 -->
        <nav class="mobile-tabbar" :style="{ paddingBottom: safeAreaBottom }">
            <div v-for="tab in tabs" :key="tab.name" class="tab-item" :class="{ active: currentTab === tab.index }"
                @click="switchTab(tab.index)">
                <div class="tab-icon">
                    <component :is="tab.icon" :size="24" />
                </div>
                <span class="tab-label">{{ tab.label }}</span>
                <div v-if="tab.badge" class="tab-badge">{{ tab.badge }}</div>
            </div>
        </nav>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { HomeFilled, Document, Tickets, ChatDotRound, User } from '@element-plus/icons-vue'

interface TabItem {
    name: string
    label: string
    icon: any
    index: number
    badge?: number | string
}

const props = defineProps<{
    defaultTab?: number
}>()

const emit = defineEmits(['tab-change'])

// Tab配置
const tabs: TabItem[] = [
    { name: 'home', label: '首页', icon: HomeFilled, index: 0 },
    { name: 'reports', label: '报告', icon: Document, index: 1 },
    { name: 'triage', label: '分诊', icon: Tickets, index: 2 },
    { name: 'chat', label: 'AI咨询', icon: ChatDotRound, index: 3 },
    { name: 'profile', label: '我的', icon: User, index: 4 },
]

// 当前Tab索引
const currentTab = ref(props.defaultTab || 0)

// 安全区域(iPhone刘海屏)
const safeAreaTop = computed(() => {
    const top = getComputedStyle(document.documentElement).getPropertyValue('--safe-area-top')
    return top || '0px'
})

const safeAreaBottom = computed(() => {
    const bottom = getComputedStyle(document.documentElement).getPropertyValue('--safe-area-bottom')
    return bottom || '0px'
})

// 当前页面标题
const currentTitle = computed(() => {
    const titles = ['首页', '报告', '分诊', 'AI咨询', '我的']
    return titles[currentTab.value]
})

// 触摸滑动相关
const contentRef = ref<HTMLElement>()
let startX = 0
let startY = 0
let isSwiping = false

function onTouchStart(e: TouchEvent) {
    startX = e.touches[0].clientX
    startY = e.touches[0].clientY
    isSwiping = true
}

function onTouchMove(e: TouchEvent) {
    if (!isSwiping) return

    const deltaX = e.touches[0].clientX - startX
    const deltaY = e.touches[0].clientY - startY

    // 如果垂直滑动距离大于水平,不处理(避免干扰页面滚动)
    if (Math.abs(deltaY) > Math.abs(deltaX)) {
        isSwiping = false
        return
    }

    // 阻止默认行为(防止页面滚动)
    e.preventDefault()
}

function onTouchEnd(e: TouchEvent) {
    if (!isSwiping) return

    const endX = e.changedTouches[0].clientX
    const deltaX = endX - startX

    // 滑动阈值
    const threshold = 50

    if (Math.abs(deltaX) > threshold) {
        if (deltaX > 0 && currentTab.value > 0) {
            // 右滑 - 上一个Tab
            switchTab(currentTab.value - 1)
        } else if (deltaX < 0 && currentTab.value < tabs.length - 1) {
            // 左滑 - 下一个Tab
            switchTab(currentTab.value + 1)
        }
    }

    isSwiping = false
}

// 切换Tab
function switchTab(index: number) {
    if (index === currentTab.value) return

    currentTab.value = index
    emit('tab-change', index)

    // Haptic Feedback (震动反馈)
    if ('vibrate' in navigator) {
        navigator.vibrate(10)
    }
}

// 暴露方法给父组件
defineExpose({
    switchTab,
    currentTab,
})
</script>

<style scoped lang="scss">
.mobile-layout {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary, #f5f7fa); // U-27: 暗黑态跟随主题变量
    overflow: hidden;
}

/* ===== 顶部标题栏 ===== */
.mobile-header {
    height: 56px;
    background: linear-gradient(135deg, #0EA5E9, #06B6D4);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);
    z-index: 100;
    flex-shrink: 0;
}

.header-content {
    width: 100%;
    padding: 0 16px;
    text-align: center;
}

.header-title {
    font-size: 18px;
    font-weight: 600;
    margin: 0;
}

/* ===== 内容区 ===== */
.mobile-content {
    flex: 1;
    overflow: hidden;
    position: relative;
}

.swipe-container {
    display: flex;
    width: 500%; // 5个Tab
    height: 100%;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-page {
    width: 100vw; // 每个Tab占满整个视口宽度
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    -webkit-overflow-scrolling: touch; // iOS平滑滚动
}

/* ===== 底部Tab导航 ===== */
.mobile-tabbar {
    height: 60px;
    background: white;
    border-top: 1px solid #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-around;
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
    z-index: 100;
    flex-shrink: 0;
}

.tab-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px 0;
    cursor: pointer;
    position: relative;
    transition: all 0.2s ease;
    min-height: var(--touch-target-min, 44px);

    &:active {
        transform: scale(0.95);
    }

    &.active {
        .tab-icon {
            color: #0EA5E9;
            transform: scale(1.1);
        }

        .tab-label {
            color: #0EA5E9;
            font-weight: 600;
        }
    }
}

.tab-icon {
    color: #9CA3AF;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.tab-label {
    font-size: 12px;
    color: #9CA3AF;
    transition: all 0.2s ease;
}

.tab-badge {
    position: absolute;
    top: 4px;
    right: calc(50% - 20px);
    min-width: 18px;
    height: 18px;
    padding: 0 4px;
    background: #EF4444;
    color: white;
    font-size: 11px;
    font-weight: 600;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid white;
}

/* ===== 响应式优化 ===== */
@media (max-width: 375px) {
    .header-title {
        font-size: 16px;
    }

    .tab-label {
        font-size: 11px;
    }
}

/* 横屏优化 */
@media (orientation: landscape) and (max-height: 500px) {
    .mobile-header {
        height: 44px;
    }

    .mobile-tabbar {
        height: 50px;
    }

    .tab-label {
        display: none; // 横屏时隐藏文字,只显示图标
    }
}
</style>
