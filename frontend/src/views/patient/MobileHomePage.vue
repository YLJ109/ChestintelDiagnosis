/**
* 移动端首页 - 统计卡片 + 功能网格
*/
<template>
    <div class="mobile-home">
        <!-- 欢迎卡片 -->
        <div class="welcome-card glass-card">
            <div class="welcome-header">
                <div class="avatar">
                    <el-icon :size="32">
                        <User />
                    </el-icon>
                </div>
                <div class="welcome-text">
                    <h2 class="greeting">您好,{{ patientName || '患者' }}</h2>
                    <p class="patient-no" v-if="patientNo">患者编号: {{ patientNo }}</p>
                </div>
            </div>
        </div>

        <!-- 统计卡片横向滚动 -->
        <div class="stats-scroll">
            <div class="stat-card" v-for="(stat, index) in stats" :key="index">
                <div class="stat-icon" :style="{ background: stat.color }">
                    <el-icon :size="24">
                        <component :is="stat.icon" />
                    </el-icon>
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                </div>
            </div>
        </div>

        <!-- 功能模块网格 -->
        <div class="function-grid">
            <div class="function-item glass-card" v-for="func in functions" :key="func.name"
                @click="handleFunctionClick(func)">
                <div class="function-icon" :style="{ background: func.gradient }">
                    <el-icon :size="28">
                        <component :is="func.icon" />
                    </el-icon>
                </div>
                <span class="function-label">{{ func.label }}</span>
            </div>
        </div>

        <!-- 快捷操作 -->
        <div class="quick-actions">
            <h3 class="section-title">快捷操作</h3>
            <div class="action-list">
                <div class="action-item" v-for="action in quickActions" :key="action.name"
                    @click="handleActionClick(action)">
                    <el-icon :size="20" :color="action.color">
                        <component :is="action.icon" />
                    </el-icon>
                    <span>{{ action.label }}</span>
                    <el-icon class="arrow">
                        <ArrowRight />
                    </el-icon>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import {
    User, Document, Clock, Aim, ChatDotRound,
    ArrowRight, FirstAidKit, Tickets, TrendCharts
} from '@element-plus/icons-vue'
import { getPatientDashboardApi } from '@/api/patient-portal'
import { ElMessage } from 'element-plus'
import { requestPermission, getPermissionStatus } from '@/utils/notification'

const router = useRouter()

// 患者信息（F-11: 移除伪造演示数据，默认空值，由真实接口填充）
const patientName = ref('')
const patientNo = ref('')

// 统计数据（F-11: 默认 0，不做假数据兜底）
const stats = ref([
    { label: '诊断次数', value: 0, icon: markRaw(FirstAidKit), color: 'linear-gradient(135deg, #0EA5E9, #06B6D4)' },
    { label: '报告数量', value: 0, icon: markRaw(Document), color: 'linear-gradient(135deg, #10B981, #059669)' },
    { label: '就诊记录', value: 0, icon: markRaw(Clock), color: 'linear-gradient(135deg, #F59E0B, #D97706)' },
])

// 功能模块
const functions = ref([
    { name: 'report', label: '诊断报告', icon: markRaw(Document), gradient: 'linear-gradient(135deg, #3B82F6, #2563EB)' },
    { name: 'history', label: '就诊历史', icon: markRaw(Clock), gradient: 'linear-gradient(135deg, #10B981, #059669)' },
    { name: 'triage', label: '智能分诊', icon: markRaw(Aim), gradient: 'linear-gradient(135deg, #F59E0B, #D97706)' },
    { name: 'chat', label: 'AI咨询', icon: markRaw(ChatDotRound), gradient: 'linear-gradient(135deg, #8B5CF6, #7C3AED)' },
])

// 快捷操作
const quickActions = ref([
    { name: 'face-login', label: '刷脸登录', icon: markRaw(Tickets), color: '#0EA5E9' },
    { name: 'view-report', label: '查看最新报告', icon: markRaw(TrendCharts), color: '#10B981' },
])

// 加载数据
onMounted(async () => {
    // 注意: 登录检查已在 MobileMainPage 统一处理,这里不再重复检查

    try {
        const res: any = await getPatientDashboardApi()
        if (res.data) {
            // F-11: 按后端 /patient/dashboard 真实返回结构取值
            const patient = res.data.patient || {}
            const statData = res.data.stats || {}
            patientName.value = patient.name || ''
            patientNo.value = patient.patient_no || ''
            stats.value[0].value = statData.total_diagnoses ?? 0
            stats.value[1].value = statData.reviewed_reports ?? 0
            stats.value[2].value = statData.triage_count ?? 0
        }

        // 请求通知权限
        const permission = getPermissionStatus()
        if (permission === 'default') {
            setTimeout(() => {
                requestPermission().then((result) => {
                    if (result === 'granted') {
                        console.log('[首页] 通知权限已授予')
                    }
                })
            }, 2000) // 延迟2秒后请求,避免打扰用户
        }
    } catch (error: any) {
        console.error('加载首页数据失败:', error)

        // 如果是401错误,跳转到移动端访客页
        if (error.response?.status === 401) {
            ElMessage.error('登录已过期,请重新登录')
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            router.push('/patient-login')
        }
    }
})

// 功能点击
function handleFunctionClick(func: any) {
    const routes: Record<string, string> = {
        report: '/patient/report',
        history: '/patient/history',
        triage: '/patient/triage',
        chat: '/patient/chat',
    }

    router.push(routes[func.name] || '/')
}

// 快捷操作点击
function handleActionClick(action: any) {
    switch (action.name) {
        case 'face-login':
            router.push('/patient-login/face')
            break
        case 'view-report':
            router.push('/patient/report')
            break
    }
}
</script>

<style scoped lang="scss">
.mobile-home {
    padding: 16px;
    min-height: 100%;
    height: 100%; // 确保填满父容器
    background: #f5f7fa;
}

/* ===== 欢迎卡片 ===== */
.welcome-card {
    background: linear-gradient(135deg, #0EA5E9, #06B6D4);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}

.welcome-header {
    display: flex;
    align-items: center;
    gap: 16px;
}

.avatar {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
}

.welcome-text {
    flex: 1;
}

.greeting {
    font-size: 20px;
    font-weight: 600;
    color: white;
    margin: 0 0 4px 0;
}

.patient-no {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
    margin: 0;
}

/* ===== 统计卡片横向滚动 ===== */
.stats-scroll {
    display: flex;
    gap: 12px;
    overflow-x: auto;
    padding: 4px 0 16px 0;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none; // Firefox

    &::-webkit-scrollbar {
        display: none; // Chrome/Safari
    }
}

.stat-card {
    flex: 0 0 calc(33.333% - 8px);
    min-width: 100px;
    background: white;
    border-radius: 12px;
    padding: 16px 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
}

.stat-info {
    text-align: center;
}

.stat-value {
    font-size: 24px;
    font-weight: 700;
    color: #1F2937;
    line-height: 1;
}

.stat-label {
    font-size: 12px;
    color: #6B7280;
    margin-top: 4px;
}

/* ===== 功能模块网格 ===== */
.function-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 24px;
}

.function-item {
    background: white;
    border-radius: 16px;
    padding: 20px 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: all 0.2s ease;
    cursor: pointer;

    &:active {
        transform: scale(0.95);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
}

.function-icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
}

.function-label {
    font-size: 14px;
    font-weight: 600;
    color: #1F2937;
}

/* ===== 快捷操作 ===== */
.quick-actions {
    background: white;
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-title {
    font-size: 16px;
    font-weight: 600;
    color: #1F2937;
    margin: 0 0 12px 0;
}

.action-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.action-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 12px;
    border-radius: 12px;
    background: #F9FAFB;
    cursor: pointer;
    transition: all 0.2s ease;

    &:active {
        background: #F3F4F6;
        transform: scale(0.98);
    }

    span {
        flex: 1;
        font-size: 15px;
        color: #1F2937;
        font-weight: 500;
    }

    .arrow {
        color: #9CA3AF;
        font-size: 16px;
    }
}

/* ===== 玻璃态效果 ===== */
.glass-card {
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}
</style>
