/** 患者门户 - 主框架页面（带导航栏的布局） */
<template>
    <div class="patient-portal">
        <!-- ===== 顶部导航栏（仅首页显示）===== -->
        <header v-if="isRoute('/patient/home')" class="portal-header">
            <div class="header-content">
                <!-- Logo和标题 -->
                <div class="header-left" @click="router.push('/patient/home')">
                    <div class="logo-icon">
                        <el-icon :size="28">
                            <FirstAidKit />
                        </el-icon>
                    </div>
                    <div class="header-title">
                        <h1>胸影智诊</h1>
                        <span class="subtitle">患者自助服务终端 V3.0</span>
                    </div>
                </div>

                <!-- 右侧用户信息 -->
                <div class="header-right">
                    <!-- 返回首页按钮（仅分诊和咨询页面显示） -->
                    <el-button v-if="isRoute('/patient/triage') || isRoute('/patient/chat')" text size="small"
                        class="back-home-btn" @click="router.push('/patient/home')">
                        <el-icon>
                            <ArrowLeft />
                        </el-icon>
                        返回首页
                    </el-button>

                    <!-- 用户信息 -->
                    <div class="user-info">
                        <el-avatar :size="32" class="user-avatar">
                            {{ (userInfo.name || 'U').charAt(0).toUpperCase() }}
                        </el-avatar>
                        <div class="user-details">
                            <span class="user-name">{{ userInfo.name || '患者' }}</span>
                            <span class="user-id">{{ userInfo.patient_no ? `编号: ${userInfo.patient_no}` : 'ID: --'
                                }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </header>

        <!-- ===== 主内容区 ===== -->
        <main class="portal-main">
            <!-- 路由视图 - 显示子页面 -->
            <router-view v-slot="{ Component }">
                <transition name="fade" mode="out-in">
                    <component :is="Component" />
                </transition>
            </router-view>
        </main>

        <!-- ===== 底部状态栏（仅首页显示）===== -->
        <footer v-if="isRoute('/patient/home')" class="portal-footer">
            <span>胸影智诊 V3.0 | 患者自助服务终端 | Powered by CheXNet + LLM</span>
        </footer>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
    FirstAidKit, ArrowLeft
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 检查是否为特定路由
const isRoute = (path: string): boolean => {
    return route.path === path
}

// 用户信息
const userInfo = computed(() => authStore.user || {})

// 退出登录
const handleLogout = () => {
    authStore.logout()
    ElMessage.success('已安全退出')
    router.push('/patient-login')
}

// 初始化主题 - U-02: 跟随用户设置，不再强制浅色
onMounted(() => {
    document.documentElement.setAttribute('data-theme', authStore.theme || 'light')
    document.documentElement.classList.remove('dark', 'light')
    document.documentElement.classList.add(authStore.theme || 'light')
})
</script>

<style scoped>
/* ===== 整体布局 ===== */
.patient-portal {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #F0F7FF 0%, #E8F4FD 100%);
    color: #000;
    overflow: hidden;
}

/* ===== 顶部导航栏 - 简洁医疗终端风格 ===== */
.portal-header {
    background: #fff;
    border-bottom: 2px solid #E5E7EB;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    z-index: 100;
    flex-shrink: 0;
}

.header-content {
    max-width: 90%;
    margin: 0 auto;
    padding: 12px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* 左侧Logo */
.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    transition: opacity 0.3s ease;
}

.header-left:hover {
    opacity: 0.85;
}

.logo-icon {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    transition: all 0.3s ease;
}

.header-left:hover .logo-icon {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.header-title h1 {
    font-size: 18px;
    font-weight: 700;
    color: #1F2937;
    margin: 0;
    letter-spacing: 0.5px;
}

.subtitle {
    font-size: 11px;
    color: #6B7280;
    font-weight: 500;
    margin-top: 2px;
    display: block;
}

/* 右侧区域 */
.header-right {
    display: flex;
    align-items: center;
    gap: 16px;
}

/* 返回首页按钮 */
.back-home-btn {
    padding: 8px 16px !important;
    font-size: 13px !important;
    color: #6B7280 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
    background: #fff !important;
}

.back-home-btn:hover {
    color: #3B82F6 !important;
    border-color: #3B82F6 !important;
    background: #EFF6FF !important;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15) !important;
}

/* 用户信息 */
.user-info {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #F9FAFB;
    padding: 6px 14px 6px 6px;
    border-radius: 20px;
    border: 1px solid #E5E7EB;
    transition: all 0.3s ease;
}

.user-info:hover {
    background: #F3F4F6;
    border-color: #3B82F6;
}

.user-avatar {
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: #fff;
    font-weight: 700;
    box-shadow: 0 2px 6px rgba(59, 130, 246, 0.25);
}

.user-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.user-name {
    font-size: 13px;
    font-weight: 600;
    color: #1F2937;
}

.user-id {
    font-size: 11px;
    color: #9CA3AF;
}

/* 操作按钮 */
.header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
}

.logout-btn {
    color: #6B7280 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    background: #fff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}

.logout-btn:hover {
    color: #fff !important;
    background: #EF4444 !important;
    border-color: #EF4444 !important;
    box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25) !important;
}

/* ===== 主内容区 ===== */
.portal-main {
    flex: 1;
    position: relative;
    overflow-y: auto;
    overflow-x: hidden;
}

/* ===== 底部状态栏 ===== */
.portal-footer {
    background: #fff;
    border-top: 2px solid #E5E7EB;
    padding: 10px 0;
    text-align: center;
    font-size: 11px;
    color: #9CA3AF;
    flex-shrink: 0;
}

/* ===== 过渡动画 ===== */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
