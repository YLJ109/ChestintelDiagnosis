<template>
  <div class="consultation-page">
    <div class="chat-layout">
      <!-- 左侧会话列表 -->
      <div class="glass-card session-panel">
        <div class="session-header">
          <h3 class="card-title">会话列表</h3>
          <el-button type="primary" size="small" @click="showExpertPicker = true">
            <el-icon>
              <Plus />
            </el-icon> 新建
          </el-button>
        </div>
        <div class="session-list">
          <div v-if="sessions.length === 0" class="session-empty">
            <p>暂无会话</p>
            <p class="hint">点击「新建」开始咨询</p>
          </div>
          <div v-for="session in sessions" :key="session.id" class="session-item"
            :class="{ active: session.id === activeSessionId }" @click="switchSession(session.id)">
            <div class="session-icon" :style="{ background: getExpert(session.expertId)?.avatarBg }"
              v-html="expertIconSvg(getExpert(session.expertId)?.icon, 18)"></div>
            <div class="session-info">
              <div class="session-title">{{ session.title }}</div>
              <div class="session-meta">
                <span class="session-expert">{{ getExpert(session.expertId)?.shortName }}</span>
                <span class="session-time">{{ formatTime(session.time) }}</span>
              </div>
            </div>
            <div class="session-delete" @click.stop="consultationStore.deleteSession(session.id)">
              <el-icon size="14">
                <Close />
              </el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧聊天区域 -->
      <div class="glass-card chat-panel">
        <!-- 无会话时的空状态 -->
        <template v-if="!activeSessionId">
          <div class="chat-empty-state">
            <div class="empty-icon-big" v-html="expertIconSvg('robot', 64)"></div>
            <h3>选择一位AI专家开始咨询</h3>
            <p>每位专家拥有不同的专业领域，为您解答对应的医疗问题</p>
            <div class="expert-quick-grid">
              <div v-for="expert in experts" :key="expert.id" class="expert-quick-card"
                @click="startWithExpert(expert.id)">
                <div class="eqc-avatar" :style="{ background: expert.avatarBg }"
                  v-html="expertIconSvg(expert.icon, 28)"></div>
                <div class="eqc-name">{{ expert.shortName }}</div>
                <div class="eqc-title">{{ expert.title }}</div>
              </div>
            </div>
          </div>
        </template>

        <!-- 有会话时 -->
        <template v-else>
          <!-- 聊天头部 -->
          <div class="chat-header">
            <div class="chat-bot-info">
              <div class="bot-avatar" :style="{ background: currentExpert?.avatarBg }"
                v-html="expertIconSvg(currentExpert?.icon, 22)">
              </div>
              <div>
                <div class="bot-name">{{ currentExpert?.name }}</div>
                <div class="bot-status">
                  <span class="status-dot online"></span> 在线 · {{ currentExpert?.title }}
                </div>
              </div>
            </div>
            <div class="chat-actions">
              <el-tooltip content="清空会话" placement="bottom">
                <el-button circle size="small" @click="clearMessages">
                  <el-icon>
                    <Delete />
                  </el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </div>

          <!-- 消息区域 -->
          <div class="chat-messages" ref="messagesContainer">
            <!-- 欢迎消息 -->
            <div class="message welcome-message" v-if="messages.length === 0">
              <div class="message-avatar bot" :style="{ background: currentExpert?.avatarBg }"
                v-html="expertIconSvg(currentExpert?.icon, 20)"></div>
              <div class="message-content">
                <div class="message-bubble bot">
                  <p>您好，我是<strong>{{ currentExpert?.name }}</strong>，{{ currentExpert?.welcome }}</p>
                  <p>您可以向我咨询以下内容：</p>
                  <div class="quick-questions">
                    <div v-for="q in currentExpert?.quickQuestions" :key="q.text" class="quick-q"
                      @click="sendQuickQ(q.text)">{{ q.label }}</div>
                  </div>
                  <p class="disclaimer">[!] AI回复仅供参考，不能替代专业医生诊断。</p>
                </div>
              </div>
            </div>

            <!-- 消息列表 -->
            <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role">
              <template v-if="msg.role === 'assistant'">
                <div class="message-avatar bot" :style="{ background: currentExpert?.avatarBg }"
                  v-html="expertIconSvg(currentExpert?.icon, 20)">
                </div>
                <div class="message-content">
                  <div class="message-bubble bot" v-html="formatMessage(msg.content)"></div>
                  <div class="message-time">{{ formatMessageTime(msg.time) }}</div>
                </div>
              </template>
              <template v-else>
                <div class="message-content user-content">
                  <div class="message-bubble user">{{ msg.content }}</div>
                  <div class="message-time">{{ formatMessageTime(msg.time) }}</div>
                </div>
                <div class="message-avatar user">{{ userName.charAt(0) }}</div>
              </template>
            </div>

            <!-- AI正在输入 -->
            <div class="message assistant" v-if="isTyping">
              <div class="message-avatar bot" :style="{ background: currentExpert?.avatarBg }"
                v-html="expertIconSvg(currentExpert?.icon, 20)">
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
              placeholder="输入您的医疗咨询问题..." @keydown.enter.exact="handleSend as any" :disabled="isTyping"
              class="chat-input" />
            <el-button type="primary" class="send-btn" @click="handleSend as any"
              :disabled="!inputText.trim() || isTyping" :loading="isTyping">
              <el-icon v-if="!isTyping">
                <Promotion />
              </el-icon>
            </el-button>
          </div>
        </template>
      </div>
    </div>

    <!-- 新建会话 - 选择专家弹窗 -->
    <el-dialog v-model="showExpertPicker" title="选择AI医疗专家" width="680px" class="expert-dialog">
      <div class="expert-grid">
        <div v-for="expert in experts" :key="expert.id" class="expert-card" @click="startWithExpert(expert.id)">
          <div class="ec-avatar" :style="{ background: expert.avatarBg }" v-html="expertIconSvg(expert.icon, 28)"></div>
          <div class="ec-info">
            <div class="ec-name">{{ expert.name }}</div>
            <div class="ec-title">{{ expert.title }}</div>
            <div class="ec-desc">{{ expert.description }}</div>
            <div class="ec-tags">
              <span v-for="tag in expert.tags" :key="tag" class="ec-tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onBeforeUnmount, watch, onMounted } from 'vue'
import { useConsultationStore } from '@/stores/consultation'
import { useAuthStore } from '@/stores/auth'
import { llmApi } from '@/api/llm'
import { ElMessage } from 'element-plus'
import { Close, Delete, Plus, Promotion } from '@element-plus/icons-vue'
import { escapeHtml } from '@/utils/xss'

const authStore = useAuthStore()
const consultationStore = useConsultationStore()
const userName = computed(() => authStore.user?.real_name || '用户')

const sessions = computed(() => consultationStore.sessions)
const activeSessionId = computed(() => consultationStore.activeSessionId)
const messages = computed(() => consultationStore.currentMessages)

const inputText = ref('')
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const showExpertPicker = ref(false)
let abortController: AbortController | null = null

// ==================== AI专家配置 ====================
const experts = [
  {
    id: 'respiratory',
    name: '李明远 · 呼吸内科专家',
    shortName: '呼吸内科',
    title: '主任医师 · 呼吸与危重症医学科',
    icon: 'lungs',
    avatarBg: 'linear-gradient(135deg, #22D3EE, #06B6D4)',
    description: '擅长呼吸系统疾病诊断与治疗，对肺炎、慢阻肺、哮喘、间质性肺病等有丰富临床经验。',
    tags: ['肺炎', '慢阻肺', '哮喘', '呼吸衰竭'],
    welcome: '专注于呼吸系统疾病的诊疗。无论是肺部感染、慢性气道疾病还是呼吸功能评估，我都可以为您提供专业建议。',
    quickQuestions: [
      { label: '肺炎治疗方案', text: '社区获得性肺炎的经验性抗感染治疗方案有哪些？' },
      { label: '慢阻肺管理', text: '慢阻肺稳定期如何规范用药和管理？' },
      { label: '哮喘控制', text: '支气管哮喘的阶梯治疗方案是怎样的？' },
      { label: '呼吸困难鉴别', text: '呼吸困难的常见病因和鉴别诊断思路？' }
    ],
    systemPrompt: `你是一位资深呼吸内科专家"李明远"，拥有30年临床经验，主任医师职称，专长于呼吸与危重症医学。
专业领域：肺部感染性疾病、慢性阻塞性肺疾病、支气管哮喘、间质性肺病、呼吸衰竭、肺部肿瘤的内科治疗。
回答风格：
- 结合最新临床指南（如GOLD指南、GINA指南等）给出循证建议
- 注重鉴别诊断思维，给出系统性的分析思路
- 适当引用研究数据支撑观点
- 使用 **粗体** 强调关键药物和检查
- 每次回答末尾提醒：以上建议仅供参考，请以临床医生面诊意见为准`
  },
  {
    id: 'radiology',
    name: '张慧敏 · 影像科专家',
    shortName: '影像科',
    title: '主任医师 · 医学影像中心',
    icon: 'microscope',
    avatarBg: 'linear-gradient(135deg, #3B82F6, #1D4ED8)',
    description: '擅长胸部影像诊断，对X光、CT、MRI的肺部病变解读具有深厚造诣，尤其擅长早期肺癌筛查。',
    tags: ['X光解读', 'CT诊断', '肺结节', '肺癌筛查'],
    welcome: '专注于医学影像诊断，尤其是胸部X光和CT的解读。我可以帮助您理解影像报告、分析影像特征、评估肺结节风险。',
    quickQuestions: [
      { label: '肺结节评估', text: '肺部磨玻璃结节的随访策略和手术指征是什么？' },
      { label: 'X光读片要点', text: '胸部X光片的基本读片步骤和常见漏诊原因？' },
      { label: '肺炎影像分型', text: '大叶性肺炎、支气管肺炎和间质性肺炎的影像学鉴别要点？' },
      { label: 'CT报告解读', text: '胸部CT报告中常见术语的含义和临床意义？' }
    ],
    systemPrompt: `你是一位资深影像科专家"张慧敏"，拥有25年影像诊断经验，主任医师职称，专长于胸部影像诊断和早期肺癌筛查。
专业领域：胸部X光诊断、胸部CT解读、肺结节良恶性评估、肺癌筛查（LDCT）、感染性病变影像分型。
回答风格：
- 注重影像特征的精确描述（密度、形态、边缘、分布等）
- 结合Fleischner学会指南评估肺结节
- 给出具体的影像-病理对照分析
- 使用 **粗体** 标注关键影像征象
- 每次回答末尾提醒：以上建议仅供参考，请以临床医生面诊意见为准`
  },
  {
    id: 'infectious',
    name: '王建国 · 感染科专家',
    shortName: '感染科',
    title: '主任医师 · 感染性疾病科',
    icon: 'virus',
    avatarBg: 'linear-gradient(135deg, #F59E0B, #D97706)',
    description: '擅长各类感染性疾病的诊治，对细菌、病毒、真菌感染的抗生素使用和耐药问题有深入研究。',
    tags: ['抗感染', '抗生素', '败血症', '不明原因发热'],
    welcome: '专注于感染性疾病的诊疗和抗生素合理使用。无论是社区感染、院内感染还是不明原因发热，我都可以帮助分析。',
    quickQuestions: [
      { label: '抗生素选择', text: '社区获得性肺炎的初始抗感染方案如何选择？' },
      { label: '不明原因发热', text: '不明原因发热的诊断思路和检查策略？' },
      { label: '耐药菌处理', text: '多重耐药菌感染的治疗策略和抗生素选择？' },
      { label: '真菌感染', text: '侵袭性肺真菌病的高危因素和早期诊断方法？' }
    ],
    systemPrompt: `你是一位资深感染科专家"王建国"，拥有28年感染病诊疗经验，主任医师职称，专长于抗感染治疗和临床微生物学。
专业领域：细菌感染与抗生素治疗、病毒性感染、真菌感染、不明原因发热、院内感染控制、抗菌药物合理使用。
回答风格：
- 依据药敏和PK/PD原则指导抗生素选择
- 重视病原学诊断，强调精准抗感染
- 引用相关指南（IDSA、中华医学会指南等）
- 使用 **粗体** 标注关键抗生素和病原体
- 每次回答末尾提醒：以上建议仅供参考，请以临床医生面诊意见为准`
  },
  {
    id: 'tuberculosis',
    name: '陈思远 · 结核病专家',
    shortName: '结核病',
    title: '主任医师 · 结核病防治中心',
    icon: 'shield',
    avatarBg: 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
    description: '专注结核病诊疗30年，对肺结核、耐药结核、结核性胸膜炎的诊治及预防有深厚造诣。',
    tags: ['肺结核', '耐药结核', '结核预防', '潜伏感染'],
    welcome: '专注于结核病的诊断、治疗和预防。我可以帮助您了解结核病的筛查策略、抗结核方案、耐药处理和预防措施。',
    quickQuestions: [
      { label: '肺结核诊断', text: '肺结核的诊断标准需要哪些检查来确认？' },
      { label: '耐药结核治疗', text: '耐多药结核病的治疗方案和疗程是怎样的？' },
      { label: '潜伏感染处理', text: '结核潜伏感染是否需要预防性治疗？方案有哪些？' },
      { label: '结核与肺癌鉴别', text: '肺结核和肺癌在影像学上如何鉴别？' }
    ],
    systemPrompt: `你是一位资深结核病专家"陈思远"，拥有30年结核病诊疗经验，主任医师职称，专长于结核病的诊断和治疗。
专业领域：肺结核诊断与治疗、耐药结核病管理、结核性胸膜炎、潜伏结核感染管理、结核病预防与控制。
回答风格：
- 熟悉WHO结核病指南和中国结核病防治指南
- 注重菌阴肺结核的诊断思路
- 关注耐药结核的个体化治疗方案
- 使用 **粗体** 强调关键检查和治疗药物
- 每次回答末尾提醒：以上建议仅供参考，请以临床医生面诊意见为准`
  },
  {
    id: 'emergency',
    name: '刘志强 · 急诊医学专家',
    shortName: '急诊科',
    title: '主任医师 · 急诊医学科',
    icon: 'ambulance',
    avatarBg: 'linear-gradient(135deg, #EF4444, #B91C1C)',
    description: '擅长急危重症救治，对呼吸衰竭、大咯血、张力性气胸等胸部急症有丰富抢救经验。',
    tags: ['呼吸衰竭', '大咯血', '气胸', '危重症'],
    welcome: '专注于急危重症的识别和救治。当您遇到紧急症状时，我可以帮助判断严重程度和紧急处理措施。',
    quickQuestions: [
      { label: '呼吸衰竭处理', text: '急性呼吸衰竭的紧急评估和处理步骤是什么？' },
      { label: '大咯血急救', text: '大咯血的紧急处理措施和注意事项？' },
      { label: '气胸识别', text: '自发性气胸的临床表现和紧急处理？' },
      { label: '胸痛鉴别', text: '急性胸痛的快速鉴别诊断和处理流程？' }
    ],
    systemPrompt: `你是一位资深急诊医学专家"刘志强"，拥有20年急危重症救治经验，主任医师职称，专长于胸部急症和呼吸危重症。
专业领域：急性呼吸衰竭、大咯血、张力性气胸、肺栓塞、重症肺炎、急性胸痛的鉴别与处理。
回答风格：
- 优先判断病情危重程度，给出ABC评估思路
- 强调时间就是生命，给出明确的优先级
- 给出具体的急救措施和药物剂量
- 使用 **粗体** 标注关键急救药物和时间节点
- 每次回答末尾提醒：如遇紧急情况请立即拨打120急救电话！以上建议仅供参考。`
  },
  {
    id: 'general',
    name: '赵文博 · 全科医学专家',
    shortName: '全科',
    title: '主任医师 · 全科医学科',
    icon: 'doctor',
    avatarBg: 'linear-gradient(135deg, #06B6D4, #0891B2)',
    description: '全科医学视野宽广，擅长常见病多发病的诊疗，健康管理和疾病预防，提供综合性医疗建议。',
    tags: ['健康管理', '常见病', '预防保健', '慢病管理'],
    welcome: '作为全科医学专家，我可以为您提供全面的健康咨询，涵盖常见疾病诊疗、健康管理、疾病预防和慢病管理等方面。',
    quickQuestions: [
      { label: '年度体检', text: '成年人年度健康体检应该做哪些项目？' },
      { label: '肺部健康', text: '日常生活中如何保护肺部健康？' },
      { label: '反复感冒', text: '反复感冒应该做哪些检查？如何提高免疫力？' },
      { label: '咳嗽不止', text: '持续咳嗽超过两周应该怎么办？需要做哪些检查？' }
    ],
    systemPrompt: `你是一位资深全科医学专家"赵文博"，拥有25年全科医疗经验，主任医师职称，专长于常见病诊疗和健康管理。
专业领域：常见呼吸系统疾病、慢性病管理、健康体检咨询、疾病预防、生活方式医学、多病共存管理。
回答风格：
- 以患者为中心，综合考虑身心社会因素
- 注重预防和早期发现
- 给出实用可行的生活方式建议
- 使用 **粗体** 标注关键建议和预警信号
- 每次回答末尾提醒：以上建议仅供参考，如有不适请及时就医。`
  }
]

function getExpert(expertId: string | undefined) {
  if (!expertId) return experts[experts.length - 1]
  return experts.find(e => e.id === expertId) || experts[experts.length - 1]
}

// SVG医生头像图标映射
function expertIconSvg(name: string | undefined, _size = 24) {
  const icons: Record<string, string> = {
    // 呼吸内科 - 男医生头像（圆角矩形）
    lungs: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="2" y="2" width="96" height="96" rx="16" fill="#22D3EE"/><circle cx="50" cy="38" r="16" fill="#fff"/><path d="M25 78c0-14 11-25 25-25s25 11 25 25v8H25v-8z" fill="#fff"/><rect x="42" y="30" width="16" height="4" rx="2" fill="#22D3EE"/></svg>',
    // 影像科 - 女医生头像（圆角矩形）
    microscope: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="2" y="2" width="96" height="96" rx="16" fill="#3B82F6"/><circle cx="50" cy="38" r="16" fill="#fff"/><path d="M25 78c0-14 11-25 25-25s25 11 25 25v8H25v-8z" fill="#fff"/><ellipse cx="50" cy="26" rx="18" ry="12" fill="#fff" opacity="0.9"/></svg>',
    // 感染科 - 男医生头像（圆角矩形）
    virus: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="2" y="2" width="96" height="96" rx="16" fill="#F59E0B"/><circle cx="50" cy="38" r="16" fill="#fff"/><path d="M25 78c0-14 11-25 25-25s25 11 25 25v8H25v-8z" fill="#fff"/><rect x="42" y="30" width="16" height="4" rx="2" fill="#F59E0B"/></svg>',
    // 结核病 - 女医生头像（圆角矩形）
    shield: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="2" y="2" width="96" height="96" rx="16" fill="#8B5CF6"/><circle cx="50" cy="38" r="16" fill="#fff"/><path d="M25 78c0-14 11-25 25-25s25 11 25 25v8H25v-8z" fill="#fff"/><ellipse cx="50" cy="26" rx="18" ry="12" fill="#fff" opacity="0.9"/></svg>',
    // 急诊科 - 男医生头像（圆角矩形）
    ambulance: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="2" y="2" width="96" height="96" rx="16" fill="#EF4444"/><circle cx="50" cy="38" r="16" fill="#fff"/><path d="M25 78c0-14 11-25 25-25s25 11 25 25v8H25v-8z" fill="#fff"/><rect x="42" y="30" width="16" height="4" rx="2" fill="#EF4444"/></svg>',
    // 全科 - 女医生头像（圆角矩形）
    doctor: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect x="2" y="2" width="96" height="96" rx="16" fill="#06B6D4"/><circle cx="50" cy="38" r="16" fill="#fff"/><path d="M25 78c0-14 11-25 25-25s25 11 25 25v8H25v-8z" fill="#fff"/><ellipse cx="50" cy="26" rx="18" ry="12" fill="#fff" opacity="0.9"/></svg>'
  }
  return icons[name || 'doctor'] || icons.doctor
}

const currentExpert = computed(() => {
  const session = consultationStore.currentSession
  if (!session) return null
  return getExpert((session as any).expertId)
})

// ==================== 时间格式化 ====================
function formatTime(isoStr: string) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const diff = (today.getTime() - target.getTime()) / 86400000

  const time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`

  if (diff === 0) return `今天 ${time}`
  if (diff === 1) return `昨天 ${time}`
  if (diff < 7) return `${diff}天前`
  return `${d.getMonth() + 1}-${d.getDate()} ${time}`
}

function formatMessageTime(isoStr: string) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function getCurrentTime() {
  return new Date().toISOString()
}

// ==================== 消息处理 ====================
function formatMessage(text: string) {
  const escaped = escapeHtml(text || '')
  return escaped
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
    .replace(/^(#{1,3})\s(.+)$/gm, (_m: string, _h: string, t: string) => `<strong>${t}</strong>`)
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

// ==================== 核心发送逻辑 ====================
let requestGeneration = 0

async function handleSend(e?: KeyboardEvent) {
  if (e && e.type === 'keydown' && e.shiftKey) return
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  cancelCurrentRequest()
  const currentGen = ++requestGeneration

  consultationStore.addMessage({ role: 'user', content: text, time: getCurrentTime() })
  consultationStore.updateSessionTime(activeSessionId.value!)
  inputText.value = ''
  scrollToBottom()

  abortController = new AbortController()
  isTyping.value = true

  try {
    const expert = currentExpert.value
    const chatMessages = [
      { role: 'system', content: expert?.systemPrompt || '你是一位专业的医疗AI咨询助手。' },
      ...messages.value.map((m: any) => ({ role: m.role, content: m.content }))
    ]
    const res: any = await llmApi.chat({
      messages: chatMessages,
      temperature: 0.7,
      max_tokens: 2000
    }, { signal: abortController.signal })

    if (currentGen !== requestGeneration) return

    if (res.success === false) {
      const errMsg = res.error || '服务暂时不可用'
      consultationStore.addMessage({
        role: 'assistant',
        content: `抱歉，AI服务暂时不可用：${errMsg}，请稍后重试。`,
        time: getCurrentTime()
      })
    } else {
      const aiContent = res.content || '抱歉，服务暂时不可用，请稍后重试。'
      consultationStore.addMessage({ role: 'assistant', content: aiContent, time: getCurrentTime() })
    }
  } catch (err: any) {
    if (currentGen !== requestGeneration) return

    if (err.name !== 'AbortError' && err.code !== 'ERR_CANCELED') {
      const status = err?.response?.status
      let errMsg = 'AI服务调用失败，请检查网络或稍后重试。'
      if (status === 401) {
        errMsg = '登录已过期，请重新登录后重试。'
      } else if (status === 403) {
        errMsg = '权限不足，无法使用AI咨询功能。'
      }
      consultationStore.addMessage({
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
      nextTick(() => scrollToBottom())
    }
  }
}

// ==================== 会话管理 ====================
function startWithExpert(expertId: string) {
  cancelCurrentRequest()
  const expert = getExpert(expertId)
  consultationStore.createSession({ expertId, expertName: expert.shortName })
  showExpertPicker.value = false
  scrollToBottom()
}

function switchSession(id: number) {
  cancelCurrentRequest()
  consultationStore.switchSession(id)
  nextTick(() => {
    isTyping.value = false
    scrollToBottom()
  })
}

function clearMessages() {
  cancelCurrentRequest()
  consultationStore.clearCurrentMessages()
}

watch(activeSessionId, () => {
  isTyping.value = false
  nextTick(() => scrollToBottom())
})

onMounted(() => {
  isTyping.value = false
})

onBeforeUnmount(() => {
  cancelCurrentRequest()
})
</script>

<style scoped lang="scss">
.consultation-page {
  .chat-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 20px;
    height: calc(100vh - 120px);
    min-height: 500px;
  }
}

// ==================== 会话列表面板 ====================
.session-panel {
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  overflow: hidden;

  .session-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--glass-border);
  }

  .session-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .session-empty {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
    font-size: 14px;

    .hint {
      font-size: 12px;
      margin-top: 8px;
      opacity: 0.6;
    }
  }

  .session-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.3s ease;
    margin-bottom: 4px;
    position: relative;

    &:hover {
      background: var(--glass-bg);

      .session-delete {
        opacity: 1;
      }
    }

    &.active {
      background: rgba(34, 211, 238, 0.1);
    }

    .session-icon {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      background: transparent;
      line-height: 0;

      :deep(svg) {
        color: #fff;
        display: block;
      }
    }

    .session-info {
      flex: 1;
      overflow: hidden;
    }

    .session-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .session-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 3px;
    }

    .session-expert {
      font-size: 11px;
      color: var(--primary);
      background: rgba(34, 211, 238, 0.12);
      padding: 1px 6px;
      border-radius: 4px;
    }

    .session-time {
      font-size: 11px;
      color: var(--text-muted);
    }

    .session-delete {
      position: absolute;
      right: 8px;
      top: 50%;
      transform: translateY(-50%);
      opacity: 0;
      transition: opacity 0.2s ease;
      color: var(--text-muted);
      cursor: pointer;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 6px;

      &:hover {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
      }
    }
  }
}

// ==================== 空状态 - 专家选择 ====================
.chat-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  height: 100%;
  padding: 40px 40px 20px;
  overflow-y: auto;

  .empty-icon-big {
    margin-bottom: 16px;

    :deep(svg) {
      color: var(--primary, #22D3EE);
    }
  }

  h3 {
    font-size: 20px;
    color: var(--text-primary);
    font-weight: 600;
    margin-bottom: 8px;
  }

  p {
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 24px;
  }

  .expert-quick-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
    width: 100%;
  }

  .expert-quick-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px;
    background: var(--card-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      transform: translateY(-4px);
      border-color: var(--primary);
      box-shadow: 0 8px 24px rgba(34, 211, 238, 0.15);
    }

    .eqc-avatar {
      width: 56px;
      height: 56px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 10px;
      background: transparent;
      line-height: 0;

      :deep(svg) {
        color: #fff;
        display: block;
      }
    }

    .eqc-name {
      font-size: 17px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .eqc-title {
      font-size: 12px;
      color: var(--text-muted);
      text-align: center;
    }
  }
}

// ==================== 专家选择弹窗 ====================
.expert-dialog {
  :deep(.el-dialog) {
    background: var(--card-bg);
    border: 1px solid var(--glass-border);
  }

  :deep(.el-dialog__title) {
    color: var(--text-primary);
    font-weight: 600;
  }

  :deep(.el-dialog__headerbtn .el-dialog__close) {
    color: var(--text-muted);
  }
}

.expert-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.expert-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--card-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    border-color: var(--primary);
    box-shadow: 0 8px 24px rgba(34, 211, 238, 0.2);
  }

  .ec-avatar {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    background: transparent;
    line-height: 0;

    :deep(svg) {
      color: #fff;
      display: block;
    }
  }

  .ec-info {
    flex: 1;
    min-width: 0;
  }

  .ec-name {
    font-size: 17px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 2px;
  }

  .ec-title {
    font-size: 12px;
    color: var(--primary);
    margin-bottom: 6px;
  }

  .ec-desc {
    font-size: 12px;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 8px;
  }

  .ec-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .ec-tag {
    font-size: 11px;
    color: var(--text-secondary);
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    padding: 2px 8px;
    border-radius: 4px;
  }
}

// ==================== 聊天面板 ====================
.chat-panel {
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--glass-border);
  flex-shrink: 0;

  .chat-bot-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .bot-avatar {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    background: transparent;
    line-height: 0;

    :deep(svg) {
      color: #fff;
      display: block;
    }
  }

  .bot-name {
    font-size: 17px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .bot-status {
    font-size: 12px;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 4px;
    margin-top: 2px;
  }

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;

    &.online {
      background: var(--primary);
      box-shadow: 0 0 6px rgba(34, 211, 238, 0.6);
    }
  }
}

// ==================== 消息区域 ====================
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
  animation: msgEnter 0.3s ease;

  &.user {
    align-self: flex-end;
  }

  &.assistant {
    align-self: flex-start;
  }
}

@keyframes msgEnter {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 0;

  &.bot {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);

    :deep(svg) {
      color: #fff;
      display: block;
    }
  }

  &.user {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(34, 211, 238, 0.1));
    border: 1px solid rgba(34, 211, 238, 0.3);
    color: var(--primary, #22D3EE);
    font-size: 14px;
    font-weight: 600;
  }
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;

  &.bot {
    background: var(--card-bg);
    border: 1px solid var(--glass-border);
    color: var(--text-primary);
    border-top-left-radius: 4px;
  }

  &.user {
    background: var(--primary);
    color: white;
    border-top-right-radius: 4px;
  }
}

.message-time {
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 4px;
}

// 快捷问题
.quick-questions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 12px 0;
}

.quick-q {
  padding: 10px 14px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--primary);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;

  &:hover {
    background: var(--glass-bg-hover);
    border-color: var(--glass-border-hover);
    transform: translateY(-1px);
  }
}

.disclaimer {
  font-size: 12px !important;
  color: var(--orange) !important;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--glass-border);
}

// 打字动画
.typing-bubble {
  padding: 16px 20px;
}

.typing-indicator {
  display: flex;
  gap: 5px;
  align-items: center;

  span {
    width: 8px;
    height: 8px;
    background: var(--text-secondary);
    border-radius: 50%;
    animation: typingBounce 1.4s ease-in-out infinite;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }

    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes typingBounce {

  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }

  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

// ==================== 输入区域 ====================
.chat-input-area {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--glass-border);
  flex-shrink: 0;

  .chat-input {
    flex: 1;

    :deep(.el-textarea__inner) {
      background: var(--glass-bg) !important;
      border: 1px solid var(--glass-border) !important;
      color: var(--text-primary) !important;
      border-radius: var(--radius-md) !important;
      padding: 12px 16px !important;
      resize: none;
      font-size: 14px;

      &::placeholder {
        color: var(--text-muted);
      }

      &:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.1) !important;
      }
    }
  }

  .send-btn {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md) !important;
    flex-shrink: 0;
  }
}

// 欢迎消息样式
.welcome-message .message-bubble.bot p {
  margin-bottom: 8px;

  &:last-child {
    margin-bottom: 0;
  }

  strong {
    color: var(--primary);
  }
}

// ==================== 响应式 ====================
@media (max-width: 768px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }

  .session-panel {
    display: none;
  }

  .expert-grid {
    grid-template-columns: 1fr;
  }

  .expert-quick-grid {
    grid-template-columns: 1fr;
    max-width: 400px;
  }
}
</style>
