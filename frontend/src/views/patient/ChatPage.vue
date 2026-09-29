/** 患者端AI咨询页面 - 临时对话（不存储到数据库） */
<template>
    <div class="patient-chat-wrapper">
        <!-- 返回主页按钮 -->
        <div class="back-home-bar">
            <el-button text @click="router.push('/patient/home')">
                <el-icon>
                    <ArrowLeft />
                </el-icon>
                返回主页
            </el-button>
        </div>

        <!-- 聊天区域 -->
        <div class="chat-container">
            <!-- 消息列表 -->
            <div class="chat-messages" ref="messagesContainer">
                <!-- 欢迎消息 -->
                <div class="message welcome-message" v-if="messages.length === 0">
                    <div class="message-avatar bot">
                        <el-icon :size="24">
                            <ChatDotRound />
                        </el-icon>
                    </div>
                    <div class="message-content">
                        <div class="message-bubble bot">
                            <p>您好！我是<strong>AI健康助手</strong>，可以为您解答健康问题。</p>
                            <p>您可以向我咨询以下内容：</p>
                            <div class="quick-questions">
                                <div v-for="q in quickQuestions" :key="q" class="quick-q" @click="sendQuickQ(q)">{{ q }}
                                </div>
                            </div>
                            <p class="disclaimer">⚠️ AI回复仅供参考，不能替代专业医生诊断。</p>
                        </div>
                    </div>
                </div>

                <!-- 消息列表 -->
                <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
                    <template v-if="msg.role === 'assistant'">
                        <div class="message-avatar bot">
                            <el-icon :size="20">
                                <ChatDotRound />
                            </el-icon>
                        </div>
                        <div class="message-content">
                            <div class="message-bubble bot" v-html="formatMessage(msg.content)"></div>
                            <div class="message-time">{{ msg.time }}</div>
                        </div>
                    </template>
                    <template v-else>
                        <div class="message-content user-content">
                            <div class="message-bubble user">{{ msg.content }}</div>
                            <div class="message-time">{{ msg.time }}</div>
                        </div>
                        <div class="message-avatar user">{{ userName.charAt(0) }}</div>
                    </template>
                </div>

                <!-- AI正在输入 -->
                <div class="message assistant" v-if="isTyping">
                    <div class="message-avatar bot">
                        <el-icon :size="20">
                            <ChatDotRound />
                        </el-icon>
                    </div>
                    <div class="message-content">
                        <div class="message-bubble bot typing-bubble">
                            <div class="typing-indicator">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 输入区域 -->
            <div class="chat-input-area">
                <el-input v-model="inputText" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }"
                    placeholder="输入您的健康问题..." @keydown.enter.exact="handleSend as any" :disabled="isTyping"
                    class="chat-input" />
                <el-button type="primary" class="send-btn" @click="handleSend as any"
                    :disabled="!inputText.trim() || isTyping" :loading="isTyping">
                    <el-icon v-if="!isTyping">
                        <Promotion />
                    </el-icon>
                </el-button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ChatDotRound, Promotion } from '@element-plus/icons-vue'
import { llmApi } from '@/api/llm'
import { useAuthStore } from '@/stores/auth'
import { escapeHtml } from '@/utils/xss'

const router = useRouter()
const authStore = useAuthStore()
const userName = computed(() => authStore.user?.name || '患者')

// 临时对话状态（不存储到数据库）
const messages = ref<Array<{ role: string; content: string; time: string }>>([])
const inputText = ref('')
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
let abortController: AbortController | null = null
let requestGeneration = 0

// 快捷问题
const quickQuestions = [
    '最近总是咳嗽怎么办？',
    '如何预防感冒？',
    '胸痛可能是什么原因？',
    '体检报告异常怎么看？'
]

// ==================== 工具函数 ====================
function formatMessage(text: string) {
    const escaped = escapeHtml(text || '')
    return escaped
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/^(#{1,3})\s(.+)$/gm, (_m: string, _h: string, t: string) => `<strong>${t}</strong>`)
}

function getCurrentTime() {
    const now = new Date()
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
}

function scrollToBottom() {
    nextTick(() => {
        if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
    })
}

function sendQuickQ(text: string) {
    inputText.value = text
    handleSend()
}

function cancelCurrentRequest() {
    if (abortController) {
        abortController.abort()
        abortController = null
    }
    requestGeneration++
    isTyping.value = false
}

// ==================== 发送消息 ====================
async function handleSend(e?: KeyboardEvent) {
    if (e && e.type === 'keydown' && e.shiftKey) return
    const text = inputText.value.trim()
    if (!text || isTyping.value) return

    cancelCurrentRequest()
    const currentGen = ++requestGeneration

    // 添加用户消息
    messages.value.push({
        role: 'user',
        content: text,
        time: getCurrentTime()
    })
    inputText.value = ''
    scrollToBottom()

    abortController = new AbortController()
    isTyping.value = true

    try {
        // 构建对话历史
        const chatMessages = [
            {
                role: 'system',
                content: `你是一位专业的AI健康助手，专门为患者提供健康咨询服务。
回答风格：
- 使用通俗易懂的语言，避免过多医学术语
- 给出实用建议，但强调需要就医确认
- 适当使用 **粗体** 强调关键点
- 每次回答末尾提醒：以上建议仅供参考，如有不适请及时就医`
            },
            ...messages.value.map(m => ({ role: m.role, content: m.content }))
        ]

        const res: any = await llmApi.patientChat({
            messages: chatMessages,
            temperature: 0.7,
            max_tokens: 2000
        }, { signal: abortController.signal })

        if (currentGen !== requestGeneration) return

        if (res.success === false) {
            const errMsg = res.error || '服务暂时不可用'
            messages.value.push({
                role: 'assistant',
                content: `抱歉，AI服务暂时不可用：${errMsg}，请稍后重试。`,
                time: getCurrentTime()
            })
        } else {
            const aiContent = res.content || '抱歉，服务暂时不可用，请稍后重试。'
            messages.value.push({
                role: 'assistant',
                content: aiContent,
                time: getCurrentTime()
            })
        }
    } catch (err: any) {
        if (currentGen !== requestGeneration) return

        if (err.name !== 'AbortError' && err.code !== 'ERR_CANCELED') {
            const status = err?.response?.status
            let errMsg = 'AI服务调用失败，请检查网络或稍后重试。'
            if (status === 503) {
                errMsg = 'AI服务暂不可用，请稍后重试。'
            }
            messages.value.push({
                role: 'assistant',
                content: `抱歉，${errMsg}`,
                time: getCurrentTime()
            })
            ElMessage.error('AI回复失败，请重试')
        }
    } finally {
        if (currentGen === requestGeneration) {
            isTyping.value = false
            abortController = null
            scrollToBottom()
        }
    }
}

// ==================== 生命周期 ====================
onMounted(() => {
    scrollToBottom()
})
</script>

<style scoped>
/* ===== AI咨询页面 - 自然布局，允许滚动 ===== */
.patient-chat-wrapper {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 24px 40px;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}

/* 返回主页按钮栏 */
.back-home-bar {
    margin-bottom: 24px;
    flex-shrink: 0;
}

.back-home-bar .el-button {
    font-size: 14px;
    color: var(--patient-text-secondary);
    padding: 10px 20px;
    border-radius: var(--patient-radius-md);
    transition: all 0.3s ease;
    background: var(--patient-card-bg);
    border: 1px solid var(--patient-card-border);
    box-shadow: var(--patient-card-shadow);
    letter-spacing: 0.3px;
}

.back-home-bar .el-button:hover {
    color: var(--patient-primary);
    background: var(--patient-primary-light);
    border-color: var(--patient-primary);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

/* ===== 聊天容器 ===== */
.chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    min-height: 0;
}

/* ===== 消息区域 ===== */
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* ===== 消息项 ===== */
.message {
    display: flex;
    gap: 12px;
    max-width: 85%;
}

.message.user {
    align-self: flex-end;
    flex-direction: row-reverse;
}

.message.welcome-message {
    max-width: 100%;
}

/* 头像 */
.message-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-weight: 700;
    color: #fff;
}

.message-avatar.bot {
    background: linear-gradient(135deg, #3B82F6, #2563EB);
}

.message-avatar.user {
    background: linear-gradient(135deg, #10B981, #059669);
}

/* 消息内容 */
.message-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.message.user .message-content {
    align-items: flex-end;
}

/* 消息气泡 */
.message-bubble {
    padding: 12px 16px;
    border-radius: 12px;
    line-height: 1.6;
    word-wrap: break-word;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message-bubble.bot {
    background: #F3F4F6;
    color: #1F2937;
    border-top-left-radius: 4px;
}

.message-bubble.user {
    background: linear-gradient(135deg, #3B82F6, #2563EB);
    color: #fff;
    border-top-right-radius: 4px;
}

.message-bubble p {
    margin: 0 0 8px 0;
}

.message-bubble p:last-child {
    margin-bottom: 0;
}

.message-bubble strong {
    font-weight: 600;
}

/* 欢迎消息特殊样式 */
.welcome-message .message-bubble.bot {
    background: linear-gradient(135deg, #EFF6FF, #DBEAFE);
    border: 1px solid #BFDBFE;
}

.disclaimer {
    font-size: 12px;
    color: #EF4444;
    margin-top: 12px !important;
    padding-top: 12px;
    border-top: 1px dashed #FCA5A5;
}

/* 快捷问题 */
.quick-questions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0;
}

.quick-q {
    padding: 8px 14px;
    background: #fff;
    border: 1px solid #3B82F6;
    border-radius: 20px;
    font-size: 13px;
    color: #3B82F6;
    cursor: pointer;
    transition: all 0.2s ease;
}

.quick-q:hover {
    background: #3B82F6;
    color: #fff;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* 时间戳 */
.message-time {
    font-size: 11px;
    color: #9CA3AF;
    padding: 0 4px;
}

/* 输入指示器 */
.typing-bubble {
    padding: 16px 20px;
}

.typing-indicator {
    display: flex;
    gap: 4px;
    align-items: center;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #9CA3AF;
    animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {

    0%,
    60%,
    100% {
        transform: translateY(0);
        opacity: 0.4;
    }

    30% {
        transform: translateY(-8px);
        opacity: 1;
    }
}

/* ===== 输入区域 ===== */
.chat-input-area {
    padding: 16px 20px;
    border-top: 1px solid #E5E7EB;
    display: flex;
    gap: 12px;
    align-items: flex-end;
    background: #FAFAFA;
}

.chat-input {
    flex: 1;
}

.chat-input :deep(.el-textarea__inner) {
    border-radius: 12px;
    border: 1px solid #D1D5DB;
    resize: none;
    font-size: 14px;
    line-height: 1.6;
    transition: all 0.2s ease;
}

.chat-input :deep(.el-textarea__inner):focus {
    border-color: #3B82F6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.send-btn {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
</style>
