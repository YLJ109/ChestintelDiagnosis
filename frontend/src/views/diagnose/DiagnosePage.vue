<template>
  <div class="diagnosis-page">
    <!-- 流程步骤指示器 -->
    <div class="flow-steps">
      <div class="step" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
        <div class="step-dot"><span>1</span></div>
        <div class="step-info">
          <span class="step-title">患者挂号</span>
          <span class="step-desc">选择患者并登记信息</span>
        </div>
      </div>
      <div class="step-line" :class="{ active: currentStep >= 2 }"></div>
      <div class="step" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
        <div class="step-dot"><span>2</span></div>
        <div class="step-info">
          <span class="step-title">影像检查</span>
          <span class="step-desc">上传X光影像</span>
        </div>
      </div>
      <div class="step-line" :class="{ active: currentStep >= 3 }"></div>
      <div class="step" :class="{ active: currentStep >= 3, done: currentStep > 3 }">
        <div class="step-dot"><span>3</span></div>
        <div class="step-info">
          <span class="step-title">AI诊断</span>
          <span class="step-desc">智能分析与结果</span>
        </div>
      </div>
      <div class="step-line" :class="{ active: currentStep >= 4 }"></div>
      <div class="step" :class="{ active: currentStep >= 4 }">
        <div class="step-dot"><span>4</span></div>
        <div class="step-info">
          <span class="step-title">报告输出</span>
          <span class="step-desc">审核确认与取报告</span>
        </div>
      </div>
    </div>

    <!-- ===== 第一区：患者挂号 + 影像检查（有结果后隐藏）===== -->
    <div class="zone-grid" v-if="!result">
      <!-- 左区：患者挂号 -->
      <div class="zone-card registration-zone" :class="{ active: currentStep === 1 }">
        <div class="zone-header">
          <div class="zone-badge">
            <el-icon>
              <User />
            </el-icon>
          </div>
          <div class="zone-title-group">
            <h3 class="zone-title">患者挂号</h3>
            <span class="zone-subtitle">Registration</span>
          </div>
          <div class="zone-status">
            <el-tag :type="selectedPatientId ? 'success' : 'info'" size="small" effect="dark">
              {{ selectedPatientId ? '已登记' : '待登记' }}
            </el-tag>
          </div>
        </div>
        <div class="zone-body">
          <!-- 患者信息摘要卡（选中后显示） -->
          <div class="patient-brief" v-if="currentPatient">
            <div class="brief-avatar">{{ currentPatient.name?.charAt(0) }}</div>
            <div class="brief-info">
              <div class="brief-name">{{ currentPatient.name }}
                <span class="brief-gender" :class="currentPatient.gender">
                  {{ currentPatient.gender === 'male' ? '男' : '女' }}
                </span>
                <span class="brief-age">{{ currentPatient.age }}岁</span>
              </div>
              <div class="brief-no">{{ currentPatient.patient_no }}</div>
              <div class="brief-history" v-if="currentPatient.medical_history">
                既往史: {{ currentPatient.medical_history }}
              </div>
            </div>
          </div>

          <el-form :model="form" :rules="rules" ref="formRef" label-width="80px" size="default">
            <el-form-item label="选择患者" prop="patient_id">
              <el-select v-model="selectedPatientId" placeholder="请选择患者" filterable style="width:100%"
                @change="onPatientChange">
                <el-option v-for="p in patientList" :key="p.id" :label="`${p.patient_no} - ${p.name}`" :value="p.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="症状描述">
              <el-input v-model="form.symptoms" type="textarea" :rows="2" placeholder="请输入患者症状" />
            </el-form-item>
            <el-form-item label="临床信息">
              <el-input v-model="form.clinical_info" type="textarea" :rows="2" placeholder="补充临床信息" />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <!-- 右区：影像检查 -->
      <div class="zone-card examination-zone" :class="{ active: currentStep === 2 }">
        <div class="zone-header">
          <div class="zone-badge">
            <el-icon>
              <Picture />
            </el-icon>
          </div>
          <div class="zone-title-group">
            <h3 class="zone-title">影像检查</h3>
            <span class="zone-subtitle">Examination</span>
          </div>
          <div class="zone-status">
            <el-tag :type="selectedFile ? 'success' : 'info'" size="small" effect="dark">
              {{ selectedFile ? '已上传' : '待上传' }}
            </el-tag>
          </div>
        </div>
        <div class="zone-body">
          <div class="upload-area">
            <div class="glass-upload-area" :class="{ 'has-file': selectedFile }">
              <el-upload ref="uploadRef" drag :auto-upload="false" :show-file-list="false" :limit="1"
                accept=".png,.jpg,.jpeg,.bmp,.gif,.webp" :on-change="onFileChange" class="upload-inner">
                <div class="upload-placeholder" v-if="!selectedFile">
                  <div class="upload-icon">
                    <el-icon :size="36">
                      <Upload />
                    </el-icon>
                  </div>
                  <div class="upload-text">拖拽胸部X光影像到此处</div>
                  <div class="upload-hint">或 <em>点击上传</em></div>
                  <div class="upload-formats">PNG / JPG / JPEG / BMP / WEBP，最大50MB</div>
                </div>
              </el-upload>
              <div class="upload-preview" v-if="selectedFile">
                <img :src="imagePreviewUrl" alt="preview" />
                <div class="preview-overlay" @click="onFileRemove">
                  <el-icon :size="20">
                    <Delete />
                  </el-icon>
                  <span>移除影像</span>
                </div>
              </div>
            </div>
          </div>
          <el-button type="primary" size="large" class="diagnose-btn" :loading="diagnosing" @click="handleDiagnose"
            :disabled="!selectedFile || !selectedPatientId" style="width:100%; margin-top:16px;">
            <el-icon>
              <SetUp />
            </el-icon> 开始AI诊断
          </el-button>
        </div>
      </div>
    </div>

    <!-- ===== 第二区：AI诊断结果 + 诊断报告 ===== -->
    <div class="zone-card result-zone" v-if="result" :class="{ active: currentStep >= 3 }">
      <div class="zone-header">
        <div class="zone-badge result-badge">
          <el-icon>
            <Cpu />
          </el-icon>
        </div>
        <div class="zone-title-group">
          <h3 class="zone-title">AI诊断结果</h3>
          <span class="zone-subtitle">Diagnosis Result</span>
        </div>
        <div class="zone-status">
          <el-tag :type="resultTagType" size="small" effect="dark">{{ resultTagLabel }}</el-tag>
          <el-button type="danger" plain size="small" @click="handleClearResult" style="margin-left: 8px;">
            <el-icon>
              <Delete />
            </el-icon> 清空
          </el-button>
        </div>
      </div>
      <div class="zone-body">
        <div class="result-layout">
          <!-- 左：AI诊断结果（影像+热力图+医生审核） -->
          <div class="result-left-panel">
            <!-- 影像分析 -->
            <div class="result-images">
              <div class="image-box">
                <div class="image-label">原始影像</div>
                <div class="preview-img-wrapper" :class="{ 'has-image': imagePreviewUrl || result?.image_url }">
                  <el-image v-if="imagePreviewUrl || result?.image_url" :src="imagePreviewUrl || result.image_url" lazy
                    fit="contain" class="preview-img" :preview-src-list="[imagePreviewUrl || result.image_url]">
                    <template #error>
                      <div class="image-error"><el-icon :size="28">
                          <Picture></Picture>
                        </el-icon><span>影像加载失败</span></div>
                    </template>
                  </el-image>
                  <div v-else class="image-placeholder"><el-icon :size="28">
                      <Picture></Picture>
                    </el-icon><span>暂无影像</span></div>
                </div>
              </div>
              <div class="image-box" v-if="result?.heatmap_url">
                <div class="image-label">Grad-CAM 热力图</div>
                <div class="preview-img-wrapper has-image">
                  <el-image :src="result.heatmap_url" fit="contain" class="preview-img" lazy
                    :preview-src-list="[result.heatmap_url]">
                    <template #error>
                      <div class="image-error"><el-icon :size="28">
                          <Picture />
                        </el-icon><span>热力图加载失败</span></div>
                    </template>
                  </el-image>
                </div>
              </div>
            </div>

            <!-- 报告操作面板 -->
            <div class="result-actions-panel">
              <div class="action-title">报告操作</div>
              <div class="action-buttons">
                <el-button size="large" @click="handleGenerateReport" :loading="generatingReport"
                  class="action-btn report" :type="!reportContent ? 'primary' : 'default'"
                  :class="{ 'report-pending': !reportContent }">
                  <el-icon>
                    <Document />
                  </el-icon> {{ reportContent ? '重新生成' : '生成报告' }}
                </el-button>
              </div>
              <div class="action-note">{{ reportContent ? '如需修改报告内容，可点击重新生成' : '检测完成！诊断已自动保存至历史记录并提交审批' }}</div>
            </div>
          </div>

          <!-- 右：诊断详情 + 诊断报告（横向排列） -->
          <div class="result-right-panel">
            <!-- 诊断详情 -->
            <div class="result-detail">
              <!-- 主结果 -->
              <div class="result-hero" :class="topResult === 'normal' ? 'normal' : 'abnormal'">
                <div class="result-hero-icon">
                  <el-icon v-if="topResult === 'normal'">
                    <CircleCheck />
                  </el-icon>
                  <el-icon v-else>
                    <Warning />
                  </el-icon>
                </div>
                <div class="result-hero-text">
                  <div class="result-hero-label">{{ resultLabel }}</div>
                  <div class="result-hero-conf">置信度 {{ topConfidence }}%</div>
                </div>
              </div>

              <!-- 患者信息 -->
              <div class="patient-info-section" v-if="currentPatient">
                <div class="section-title">患者信息</div>
                <div class="patient-info-grid">
                  <div class="info-row">
                    <span class="info-label">姓名</span>
                    <span class="info-value">{{ currentPatient.name }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">性别</span>
                    <span class="info-value">{{ currentPatient.gender === 'male' ? '男' : '女' }}</span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">年龄</span>
                    <span class="info-value">{{ currentPatient.age }}岁</span>
                  </div>
                  <div class="info-row">
                    <span class="info-label">患者编号</span>
                    <span class="info-value mono">{{ currentPatient.patient_no }}</span>
                  </div>
                  <div class="info-row" v-if="currentPatient.phone">
                    <span class="info-label">联系电话</span>
                    <span class="info-value">{{ currentPatient.phone }}</span>
                  </div>
                  <div class="info-row" v-if="currentPatient.id_card">
                    <span class="info-label">身份证号</span>
                    <span class="info-value mono">{{ currentPatient.id_card }}</span>
                  </div>
                  <div class="info-row full-width" v-if="currentPatient.medical_history">
                    <span class="info-label">既往病史</span>
                    <span class="info-value">{{ currentPatient.medical_history }}</span>
                  </div>
                  <div class="info-row full-width" v-if="currentPatient.allergy_history">
                    <span class="info-label">过敏史</span>
                    <span class="info-value">{{ currentPatient.allergy_history }}</span>
                  </div>
                </div>
              </div>

              <!-- 概率分布 -->
              <div class="prob-section">
                <div class="prob-item" v-for="p in top5Probs" :key="p.disease_code">
                  <div class="prob-header">
                    <span class="prob-dot" :style="{ background: probColor(p.disease_code) }"></span>
                    <span class="prob-label">{{ p.disease_name_zh }}</span>
                    <span class="prob-value">{{ (p.probability * 100).toFixed(1) }}%</span>
                  </div>
                  <div class="prob-bar">
                    <div class="prob-fill"
                      :style="{ width: p.probability * 100 + '%', background: probColor(p.disease_code) }">
                    </div>
                  </div>
                </div>
              </div>

              <!-- 附加信息 -->
              <div class="result-meta">
                <div class="meta-item">
                  <span class="meta-label">记录编号</span>
                  <span class="meta-value mono">{{ result.diagnosis_no }}</span>
                </div>
                <div class="meta-item" v-if="result.ai_report?.ai_model_used">
                  <span class="meta-label">AI模型</span>
                  <span class="meta-value">{{ result.ai_report.ai_model_used }}</span>
                </div>
              </div>
            </div>

            <!-- 诊断报告区域 -->
            <div class="report-section">
              <!-- 报告生成中 -->
              <div v-if="generatingReport" class="report-loading">
                <div class="loading-spinner">
                  <div class="spinner-ring"></div>
                  <div class="spinner-ring"></div>
                  <div class="spinner-ring"></div>
                  <div class="spinner-icon">
                    <el-icon :size="32" class="rotating-icon">
                      <Document />
                    </el-icon>
                  </div>
                </div>
                <h4 class="loading-title">AI正在生成诊断报告</h4>
                <p class="loading-desc">正在分析影像学表现，生成标准化医学报告...</p>
                <div class="loading-progress">
                  <div class="progress-bar">
                    <div class="progress-fill"></div>
                  </div>
                  <span class="progress-text">预计需要10-20秒</span>
                </div>
              </div>

              <!-- 报告未生成时的占位提示 -->
              <div v-else-if="!reportContent" class="report-placeholder">
                <div class="placeholder-icon">
                  <el-icon :size="48">
                    <Document />
                  </el-icon>
                </div>
                <h4 class="placeholder-title">诊断报告待生成</h4>
                <p class="placeholder-desc">请完成医生审核后，点击左侧「生成报告」按钮</p>
                <div class="placeholder-tips">
                  <div class="tip-item">
                    <el-icon>
                      <InfoFilled />
                    </el-icon>
                    <span>AI将根据诊断结果自动生成标准化医学报告</span>
                  </div>
                  <div class="tip-item">
                    <el-icon>
                      <InfoFilled />
                    </el-icon>
                    <span>报告包含影像学表现、诊断结论及治疗建议</span>
                  </div>
                  <div class="tip-item">
                    <el-icon>
                      <InfoFilled />
                    </el-icon>
                    <span>生成后可打印或导出为PDF格式</span>
                  </div>
                </div>
              </div>

              <!-- 报告已生成时的内容 -->
              <template v-else>
                <div class="report-header-inline">
                  <h4 class="report-title-inline">诊断报告</h4>
                  <div class="report-actions-inline">
                    <el-button size="small" @click="handlePrintReport">
                      <el-icon>
                        <Printer />
                      </el-icon> 打印
                    </el-button>

                  </div>
                </div>
                <div class="report-content-inline">
                  <pre class="report-pre">{{ reportContent }}</pre>
                </div>
                <div class="report-footer-inline">
                  <div class="footer-item">本报告由AI辅助诊断系统生成，仅供临床医生参考，最终诊断以临床医生意见为准</div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { diagnoseSingleApi } from '@/api/diagnose'
import { getPatientsApi } from '@/api/patients'
import { regenerateReportApi } from '@/api/reports'
import { ElMessage } from 'element-plus'

const router = useRouter()
import { User, Upload, Delete, Picture, Refresh, Printer, Cpu, CircleCheck, Warning, Document, InfoFilled, SetUp } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'

const formRef = ref()
const uploadRef = ref()
const patientList = ref<any[]>([])
const selectedPatientId = ref<number | undefined>()
const diagnosing = ref(false)
const generatingReport = ref(false)
const selectedFile = ref<File | null>(null)
const imagePreviewUrl = ref('')
const result = ref<any>(null)
const reportContent = ref('')

const form = ref({ patient_id: undefined as number | undefined, symptoms: '', clinical_info: '' })

const currentPatient = computed(() => {
  if (!selectedPatientId.value || !patientList.value.length) return null
  return patientList.value.find((p: any) => p.id === selectedPatientId.value)
})

// 流程步骤
const currentStep = computed(() => {
  if (result.value && reportContent.value) return 4
  if (result.value) return 3
  if (selectedFile.value) return 2
  if (selectedPatientId.value) return 1
  return 0
})

const rules = { patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }] }

// 从概率数组推导主结果（最高概率 < 0.3 视为正常）
const sortedProbs = computed(() => {
  const probs = result.value?.probabilities || result.value?.disease_probabilities || []
  if (!probs.length) return []
  return [...probs].sort((a: any, b: any) => b.probability - a.probability)
})

const topResult = computed(() => {
  if (!sortedProbs.value.length) return 'normal'
  if (sortedProbs.value[0].probability < 0.3) return 'normal'
  return sortedProbs.value[0].disease_code
})

const topResultName = computed(() => {
  if (topResult.value === 'normal') return '正常'
  return sortedProbs.value[0]?.disease_name_zh || topResult.value
})

const topConfidence = computed(() => {
  if (!sortedProbs.value.length) return '0.0'
  return (sortedProbs.value[0].probability * 100).toFixed(1)
})

// 前5种概率
const top5Probs = computed(() => sortedProbs.value.slice(0, 5))

const resultTypeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = { normal: 'success' }

const resultLabel = computed(() => topResultName.value)
const resultTagType = computed(() => resultTypeMap[topResult.value] || 'warning')
const resultTagLabel = computed(() => resultLabel.value)

function probColor(code: string): string {
  const map: Record<string, string> = {
    Atelectasis: '#F59E0B',
    Cardiomegaly: '#EF4444',
    Effusion: '#3B82F6',
    Infiltration: '#8B5CF6',
    Mass: '#EC4899',
    Nodule: '#6366F1',
    Pneumonia: '#F97316',
    Pneumothorax: '#EF4444',
    Consolidation: '#F59E0B',
    Edema: '#06B6D4',
    Emphysema: '#14B8A6',
    Fibrosis: '#8B5CF6',
    Pleural_Thickening: '#64748B',
    Hernia: '#A855F7',
  }
  return map[code] || '#60A5FA'
}

function onPatientChange(id: number) {
  form.value.patient_id = id
  const p = patientList.value.find((i: any) => i.id === id)
  if (p) {
    form.value.symptoms = p.medical_history || ''
  }
}

function onFileChange(file: UploadFile) {
  if (file.raw) {
    selectedFile.value = file.raw
    imagePreviewUrl.value = URL.createObjectURL(file.raw)
  }
}

function onFileRemove() {
  if (imagePreviewUrl.value && imagePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(imagePreviewUrl.value)
  }
  selectedFile.value = null
  imagePreviewUrl.value = ''
  result.value = null
  reportContent.value = ''
  if (uploadRef.value) { uploadRef.value.clearFiles() }
}

async function handleDiagnose() {
  if (!selectedFile.value || !selectedPatientId.value) return
  diagnosing.value = true
  result.value = null
  reportContent.value = ''
  try {
    const formData = new FormData()
    formData.append('image', selectedFile.value)
    formData.append('patient_id', String(selectedPatientId.value))
    if (form.value.symptoms) formData.append('symptoms', form.value.symptoms)
    if (form.value.clinical_info) formData.append('clinical_info', form.value.clinical_info)
    // 先跳过报告生成，快速显示检测结果
    formData.append('skip_report', 'true')
    const res: any = await diagnoseSingleApi(formData)
    result.value = res.data
    ElMessage.success('检测完成，正在生成AI报告...')
    // 后台异步生成报告
    generateReportAsync()
  } catch {
    // error handled by interceptor
  } finally {
    diagnosing.value = false
  }
}

async function generateReportAsync() {
  const reportId = result.value?.report_id
  if (!reportId) return
  generatingReport.value = true
  try {
    const res: any = await regenerateReportApi(reportId)
    if (res.data?.ai_generated_content) {
      reportContent.value = res.data.ai_generated_content
    } else if (res.data?.findings || res.data?.impression) {
      const parts: string[] = []
      if (res.data.findings) parts.push('【检查所见】\n' + res.data.findings)
      if (res.data.impression) parts.push('【诊断意见】\n' + res.data.impression)
      if (res.data.recommendations) parts.push('【建议】\n' + res.data.recommendations)
      reportContent.value = parts.join('\n\n')
    }
    ElMessage.success('AI报告生成完成')
  } catch {
    // error handled by interceptor
  } finally {
    generatingReport.value = false
  }
}

async function handleGenerateReport() {
  const reportId = result.value?.report_id
  if (!reportId) {
    ElMessage.error('未找到报告记录')
    return
  }
  generatingReport.value = true
  try {
    const res: any = await regenerateReportApi(reportId)
    if (res.data?.ai_generated_content) {
      reportContent.value = res.data.ai_generated_content
    } else if (res.data?.findings || res.data?.impression) {
      const parts: string[] = []
      if (res.data.findings) parts.push('【检查所见】\n' + res.data.findings)
      if (res.data.impression) parts.push('【诊断意见】\n' + res.data.impression)
      if (res.data.recommendations) parts.push('【建议】\n' + res.data.recommendations)
      reportContent.value = parts.join('\n\n')
    }
    ElMessage.success('报告生成成功')
  } catch {
    // error handled by interceptor
  } finally {
    generatingReport.value = false
  }
}

// 清空诊断结果
function handleClearResult() {
  ElMessage.success('正在清空诊断结果...')

  // 清除 sessionStorage 缓存
  sessionStorage.removeItem('diagnose_state')

  // 清理 blob URL
  if (imagePreviewUrl.value && imagePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(imagePreviewUrl.value)
  }

  // 延迟刷新页面，确保提示显示
  setTimeout(() => {
    location.reload()
  }, 500)
}

// 图片转Base64（确保打印时图片正常显示）
async function imageToBase64(url: string): Promise<string> {
  try {
    const response = await fetch(url)
    const blob = await response.blob()
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  } catch {
    return ''
  }
}

async function handlePrintReport() {
  const r = result.value
  if (!r) return

  // 跳转到统一打印页面（业务端路由）
  router.push({ name: 'ReportPrint', params: { id: r.diagnosis_id } })
}

onMounted(async () => {
  // 先加载患者列表（无论是否有缓存）
  try {
    const res: any = await getPatientsApi({ per_page: 200 })
    patientList.value = res.data.items
  } catch { /* handled */ }

  // 尝试从 sessionStorage 恢复诊断状态
  const savedState = sessionStorage.getItem('diagnose_state')
  if (savedState) {
    try {
      const state = JSON.parse(savedState)
      result.value = state.result || null
      reportContent.value = state.reportContent || ''
      selectedPatientId.value = state.selectedPatientId || undefined

      // 恢复患者选择（此时 patientList 已加载）
      if (selectedPatientId.value && patientList.value.length) {
        const p = patientList.value.find((item: any) => item.id === selectedPatientId.value)
        if (p) {
          form.value.patient_id = p.id
          form.value.symptoms = p.medical_history || ''
        }
      }

      if (result.value) {
        ElMessage.info('已恢复上次的诊断结果')
      }
    } catch {
      // 忽略解析错误
    }
  }

  // 如果没有保存的数据，清理状态
  if (!result.value) {
    selectedFile.value = null
    if (imagePreviewUrl.value && imagePreviewUrl.value.startsWith('blob:')) {
      URL.revokeObjectURL(imagePreviewUrl.value)
    }
    imagePreviewUrl.value = ''
    reportContent.value = ''
  }
})

// 保存诊断状态到 sessionStorage
function saveState() {
  if (result.value) {
    sessionStorage.setItem('diagnose_state', JSON.stringify({
      result: result.value,
      reportContent: reportContent.value,
      selectedPatientId: selectedPatientId.value,
    }))
  } else {
    sessionStorage.removeItem('diagnose_state')
  }
}

// 监听结果变化，自动保存
watch(result, () => {
  saveState()
}, { deep: true })

watch(reportContent, () => {
  saveState()
})

onUnmounted(() => {
  // 组件卸载时清理 blob URL
  if (imagePreviewUrl.value && imagePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(imagePreviewUrl.value)
  }
})
</script>

<style scoped lang="scss">
.diagnosis-page {

  // ========== 流程步骤指示器 ==========
  .flow-steps {
    display: flex;
    align-items: center;
    gap: 0;
    margin-bottom: 24px;
    padding: 20px 28px;
    background: var(--card-bg);
    backdrop-filter: blur(12px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-xl);
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.3), transparent);
    }

    .step {
      display: flex;
      align-items: center;
      gap: 14px;
      flex-shrink: 0;

      .step-dot {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: var(--glass-bg);
        border: 2px solid var(--glass-border);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.4s ease;
        flex-shrink: 0;

        span {
          font-size: 17px;
          font-weight: 700;
          color: var(--text-muted);
          transition: color 0.4s ease;
        }
      }

      .step-info {
        display: flex;
        flex-direction: column;
        gap: 2px;

        .step-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-muted);
          transition: color 0.4s ease;
        }

        .step-desc {
          font-size: 12px;
          color: var(--text-muted);
          opacity: 0.6;
        }
      }

      &.active {
        .step-dot {
          background: rgba(34, 211, 238, 0.15);
          border-color: var(--primary);
          box-shadow: 0 0 20px rgba(34, 211, 238, 0.2);

          span {
            color: var(--primary);
          }
        }

        .step-title {
          color: var(--text-primary);
        }

        .step-desc {
          opacity: 1;
          color: var(--text-secondary);
        }
      }

      &.done {
        .step-dot {
          background: var(--primary);
          border-color: var(--primary);

          span {
            color: #fff;
          }
        }

        .step-title {
          color: var(--primary);
        }
      }
    }

    .step-line {
      flex: 1;
      height: 2px;
      background: var(--glass-border);
      margin: 0 8px;
      border-radius: 1px;
      transition: background 0.4s ease;

      &.active {
        background: var(--primary);
      }
    }
  }

  // ========== 分区卡片通用样式 ==========
  .zone-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }

  .zone-card {
    background: var(--card-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-xl);
    overflow: hidden;
    transition: all 0.4s ease;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--glass-bg-hover), transparent);
    }

    &.active {
      border-color: rgba(34, 211, 238, 0.3);
      box-shadow: 0 0 30px rgba(34, 211, 238, 0.08);
    }

    .zone-header {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 20px 24px 16px;
      border-bottom: 1px solid var(--glass-border);

      .zone-badge {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: rgba(34, 211, 238, 0.15);
        border: 1px solid rgba(34, 211, 238, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--primary);
        flex-shrink: 0;

        &.result-badge {
          background: rgba(59, 130, 246, 0.15);
          border-color: rgba(59, 130, 246, 0.3);
          color: var(--blue);
        }

        &.report-badge {
          background: rgba(139, 92, 246, 0.15);
          border-color: rgba(139, 92, 246, 0.3);
          color: var(--purple);
        }
      }

      .zone-title-group {
        flex: 1;

        .zone-title {
          font-size: 18px;
          font-weight: 600;
          color: var(--text-primary);
          margin: 0;
        }

        .zone-subtitle {
          font-size: 12px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
      }

      .zone-status {
        flex-shrink: 0;
      }
    }

    .zone-body {
      padding: 20px 24px 24px;
    }
  }

  .empty-zone,
  .result-zone,
  .report-zone {
    // margin-bottom: 20px;
    max-height: 760px;
    overflow-y: auto; // U-25: 内容超出时内部滚动，避免溢出不可见
  }

  // ========== 患者挂号区 ==========
  .patient-brief {
    display: flex;
    gap: 14px;
    padding: 14px 16px;
    background: rgba(34, 211, 238, 0.06);
    border: 1px solid rgba(34, 211, 238, 0.15);
    border-radius: var(--radius-lg);
    margin-bottom: 16px;

    .brief-avatar {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(34, 211, 238, 0.1));
      border: 1px solid rgba(34, 211, 238, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 18px;
      color: var(--primary);
      flex-shrink: 0;
    }

    .brief-info {
      flex: 1;
      min-width: 0;

      .brief-name {
        font-size: 17px;
        font-weight: 700;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 4px;

        .brief-gender {
          font-size: 11px;
          padding: 2px 8px;
          border-radius: 10px;
          font-weight: 600;

          &.male {
            background: rgba(59, 130, 246, 0.2);
            color: var(--blue);
          }

          &.female {
            background: rgba(236, 72, 153, 0.2);
            color: #F472B6;
          }
        }

        .brief-age {
          font-size: 13px;
          color: var(--text-secondary);
          font-weight: 400;
        }
      }

      .brief-no {
        font-size: 12px;
        color: var(--text-muted);
        font-family: 'Courier New', monospace;
      }

      .brief-history {
        font-size: 12px;
        color: var(--text-secondary);
        margin-top: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  // ========== 影像检查区 ==========
  .upload-area {
    margin-bottom: 4px;
  }

  .upload-inner {
    width: 100%;
  }

  .diagnose-btn {
    height: 44px;
    font-size: 17px;
    font-weight: 600;
    border-radius: var(--radius-md) !important;
    background: linear-gradient(135deg, var(--primary), #06B6D4) !important;
    border: none !important;
    letter-spacing: 1px;

    &:hover {
      box-shadow: 0 8px 24px rgba(34, 211, 238, 0.4) !important;
    }

    &:disabled {
      opacity: 0.5;
    }
  }

  .glass-upload-area {
    width: 100%;
    min-height: 200px;
    background: var(--bg-tertiary);
    // border: 2px dashed var(--glass-border);
    border-radius: var(--radius-lg);
    transition: all 0.3s ease;
    overflow: hidden;

    &:hover {
      border-color: var(--glass-border-hover);
      background: var(--bg-tertiary);
    }

    &.has-file {
      border-style: solid;
      border-color: var(--primary);
    }

    :deep(.el-upload) {
      width: 100%;
    }

    :deep(.el-upload-dragger) {
      background: transparent;
      border: none;
      border-radius: var(--radius-lg);
      padding: 0;
    }
  }

  .upload-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60px 20px;

    .upload-icon {
      color: var(--text-muted);
      margin-bottom: 10px;
      opacity: 0.6;
    }

    .upload-text {
      font-size: 14px;
      color: var(--text-secondary);
      margin-bottom: 4px;
    }

    .upload-hint {
      font-size: 13px;
      color: var(--text-muted);

      em {
        color: var(--primary);
        font-style: normal;
        font-weight: 500;
      }
    }

    .upload-formats {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 10px;
      opacity: 0.7;
    }
  }

  .upload-preview {
    position: relative;

    img {
      width: 100%;
      height: 200px;
      object-fit: contain;
      display: block;
    }

    .preview-overlay {
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 6px;
      opacity: 0;
      transition: opacity 0.3s ease;
      cursor: pointer;
      color: var(--text-primary);

      span {
        font-size: 12px;
      }
    }

    &:hover .preview-overlay {
      opacity: 1;
    }
  }

  // ========== 诊断结果区 ==========
  .result-layout {
    display: grid;
    grid-template-columns: 205px 1fr;
    gap: 16px;
    align-items: stretch;
    min-height: 600px;
  }

  .result-left-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .result-right-panel {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 16px;
    align-items: start;
  }

  .result-detail {
    padding: 10px;
  }

  .result-images {
    display: flex;
    flex-direction: column;
    gap: 12px;

    .image-box {
      .image-label {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 6px;
        font-weight: 600;
      }

      .preview-img-wrapper {
        width: 100%;
        height: 160px;
        border-radius: var(--radius-md);
        background: var(--bg-tertiary);
        border: 1px solid var(--glass-border);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;

        &.has-image {
          background: var(--card-bg);
        }

        .preview-img {
          width: 100%;
          height: 100%;
        }

        .image-placeholder,
        .image-error {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 4px;
          color: var(--text-muted);
          font-size: 11px;
        }

        .image-error {
          color: var(--orange);
        }
      }
    }
  }

  .result-hero {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 18px 20px;
    border-radius: var(--radius-lg);
    margin-bottom: 16px;
    text-align: center;
    border: 2px solid;

    &.normal {
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.12), rgba(34, 211, 238, 0.05));
      border-color: rgba(34, 211, 238, 0.3);
    }

    &.abnormal {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(245, 158, 11, 0.05));
      border-color: rgba(245, 158, 11, 0.3);
    }

    .result-hero-icon {
      font-size: 40px;
      flex-shrink: 0;
    }

    &.normal .result-hero-icon {
      color: var(--primary);
    }

    &.abnormal .result-hero-icon {
      color: var(--orange);
    }

    .result-hero-text {
      .result-hero-label {
        font-size: 20px;
        font-weight: 700;
      }

      .result-hero-conf {
        font-size: 13px;
        color: var(--text-secondary);
        margin-top: 3px;
      }
    }

    &.normal .result-hero-label {
      color: var(--primary);
    }

    &.abnormal .result-hero-label {
      color: var(--orange);
    }
  }

  // 患者信息区域
  .patient-info-section {
    background: rgba(34, 211, 238, 0.04);
    border: 1px solid rgba(34, 211, 238, 0.12);
    border-radius: var(--radius-md);
    padding: 14px;
    margin-bottom: 14px;

    .section-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--primary);
      margin-bottom: 10px;
      padding-bottom: 6px;
      border-bottom: 1px solid rgba(34, 211, 238, 0.15);
    }

    .patient-info-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px 16px;

      .info-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;

        &.full-width {
          grid-column: 1 / -1;
        }

        .info-label {
          color: var(--text-muted);
          flex-shrink: 0;
          min-width: 60px;
        }

        .info-value {
          color: var(--text-primary);
          font-weight: 500;

          &.mono {
            font-family: 'Courier New', monospace;
            font-size: 11px;
          }
        }
      }
    }
  }

  .prob-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 14px;

    .prob-item {
      .prob-header {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 5px;

        .prob-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .prob-label {
          font-size: 12px;
          color: var(--text-secondary);
          flex: 1;
        }

        .prob-value {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-primary);
        }
      }

      .prob-bar {
        height: 5px;
        background: var(--bg-tertiary);
        border-radius: 3px;
        overflow: hidden;

        .prob-fill {
          height: 100%;
          border-radius: 3px;
          transition: width 0.6s ease;
        }
      }
    }
  }

  .result-meta {
    display: flex;
    gap: 16px;
    padding-top: 10px;
    border-top: 1px solid var(--glass-border);

    .meta-item {
      display: flex;
      align-items: center;
      gap: 6px;

      .meta-label {
        font-size: 11px;
        color: var(--text-muted);
      }

      .meta-value {
        font-size: 12px;
        color: var(--text-secondary);
        font-weight: 500;

        &.mono {
          font-family: 'Courier New', monospace;
        }
      }
    }
  }

  // 操作面板 - 位于影像分析区域底部
  .result-actions-panel {
    background: var(--card-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 16px;
    display: flex;
    flex-direction: column;
    // margin-top: auto;

    .action-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: 12px;
    }

    .action-buttons {
      display: flex;
      flex-direction: column;
      gap: 8px;
      width: 100%;

      .action-btn {
        width: 100%;
        height: 38px;
        border-radius: var(--radius-md) !important;
        font-size: 13px;
        font-weight: 500;
        padding: 0;
        margin: 0;
        box-sizing: border-box;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;

        &.report {
          background: linear-gradient(135deg, var(--purple), #7C3AED) !important;
          border: none !important;
          color: #fff !important;

          &.report-pending {
            background: linear-gradient(135deg, var(--primary), #06B6D4) !important;
            animation: reportPulse 2s ease-in-out infinite;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.4) !important;
          }
        }
      }
    }

    .action-note {
      font-size: 10px;
      color: var(--text-muted);
      text-align: center;
      margin-top: 12px;
      line-height: 1.5;
      padding: 0 4px;
    }
  }

  // 诊断报告区域（内联）
  .report-section {
    background: var(--card-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 20px;
    margin-top: 8px;
    min-height: 100%;
    display: flex;
    flex-direction: column;

    // 报告生成中加载动画
    .report-loading {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 20px;

      .loading-spinner {
        position: relative;
        width: 120px;
        height: 120px;
        margin-bottom: 24px;

        .spinner-ring {
          position: absolute;
          border-radius: 50%;
          border: 3px solid transparent;
          animation: spin 1.5s linear infinite;

          &:nth-child(1) {
            width: 120px;
            height: 120px;
            border-top-color: var(--primary);
            animation-duration: 1.5s;
          }

          &:nth-child(2) {
            width: 90px;
            height: 90px;
            top: 15px;
            left: 15px;
            border-right-color: var(--purple);
            animation-duration: 2s;
            animation-direction: reverse;
          }

          &:nth-child(3) {
            width: 60px;
            height: 60px;
            top: 30px;
            left: 30px;
            border-bottom-color: var(--green);
            animation-duration: 2.5s;
          }
        }

        .spinner-icon {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          color: var(--primary);

          .rotating-icon {
            animation: rotate-icon 3s ease-in-out infinite;
          }
        }
      }

      .loading-title {
        font-size: 20px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 8px 0;
      }

      .loading-desc {
        font-size: 13px;
        color: var(--text-secondary);
        margin: 0 0 24px 0;
      }

      .loading-progress {
        width: 100%;
        max-width: 280px;

        .progress-bar {
          height: 4px;
          background: var(--bg-tertiary);
          border-radius: 2px;
          overflow: hidden;
          margin-bottom: 8px;

          .progress-fill {
            height: 100%;
            width: 30%;
            background: linear-gradient(90deg, var(--primary), var(--purple));
            border-radius: 2px;
            animation: progress-move 2s ease-in-out infinite;
          }
        }

        .progress-text {
          font-size: 12px;
          color: var(--text-muted);
        }
      }
    }

    // 占位提示样式
    .report-placeholder {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 20px;

      .placeholder-icon {
        color: var(--text-muted);
        opacity: 0.5;
        margin-bottom: 16px;
      }

      .placeholder-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 8px 0;
      }

      .placeholder-desc {
        font-size: 13px;
        color: var(--text-secondary);
        margin: 0 0 24px 0;
      }

      .placeholder-tips {
        width: 100%;
        max-width: 320px;
        display: flex;
        flex-direction: column;
        gap: 12px;

        .tip-item {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          padding: 10px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--glass-border);
          border-radius: var(--radius-md);
          font-size: 12px;
          color: var(--text-secondary);
          line-height: 1.5;

          .el-icon {
            color: var(--primary);
            flex-shrink: 0;
            margin-top: 1px;
          }

          span {
            text-align: left;
          }
        }
      }
    }

    .section-divider {
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
      margin-bottom: 16px;
    }

    .report-header-inline {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .report-title-inline {
        font-size: 17px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
      }

      .report-actions-inline {
        display: flex;
        gap: 8px;
      }
    }

    .report-content-inline {
      .report-pre {
        font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
        font-size: 13px;
        line-height: 2;
        color: var(--text-secondary);
        white-space: pre-wrap;
        word-break: break-all;
        margin: 0;
        padding: 16px;
        background: var(--bg-tertiary);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-md);
        max-height: 460px;
        overflow-y: auto;
      }
    }

    .report-footer-inline {
      text-align: center;
      padding-top: 12px;
      margin-top: 16px;
      border-top: 1px solid var(--glass-border);
      color: var(--text-muted);
      font-size: 11px;

      .footer-item {
        margin-bottom: 2px;
      }
    }
  }

  // ========== 空状态 ==========
  .empty-zone .empty-state {
    text-align: center;
    padding: 60px 20px;

    .empty-icon {
      width: 80px;
      height: 80px;
      margin: 0 auto 20px;
      background: var(--glass-bg);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);

      svg {
        width: 40px;
        height: 40px;
      }
    }

    h3 {
      font-size: 18px;
      color: var(--text-secondary);
      font-weight: 600;
      margin-bottom: 8px;
    }

    p {
      font-size: 14px;
      color: var(--text-muted);
    }
  }

  // ========== 诊断报告区 ==========
  .report-zone {
    margin-bottom: 20px;

    .report-toolbar {
      display: flex;
      gap: 8px;
    }
  }

  .report-content-wrapper {
    .report-header {
      text-align: center;
      padding-bottom: 16px;
      margin-bottom: 20px;
      border-bottom: 2px solid var(--glass-border);

      .report-title {
        font-size: 22px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        letter-spacing: 2px;
      }
    }

    .report-body {
      margin-bottom: 20px;

      .report-text-content {
        flex: 1;

        .report-pre {
          font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
          font-size: 13px;
          line-height: 2;
          color: var(--text-secondary);
          white-space: pre-wrap;
          word-break: break-all;
          margin: 0;
          padding: 20px;
          background: var(--bg-tertiary);
          border: 1px solid var(--glass-border);
          border-radius: var(--radius-lg);
        }
      }
    }

    .report-footer {
      text-align: center;
      padding-top: 16px;
      border-top: 1px solid var(--glass-border);
      color: var(--text-muted);
      font-size: 12px;

      .report-footer-item {
        margin-bottom: 3px;
      }
    }
  }

  // ========== 响应式 ==========
  @media (max-width: 1200px) {
    .result-layout {
      grid-template-columns: 260px 1fr;
      gap: 12px;
    }
  }

  @media (max-width: 1024px) {
    .result-layout {
      grid-template-columns: 1fr;
    }

    .result-left-panel {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .result-right-panel {
      grid-template-columns: 1fr;
    }

    .result-actions-panel {
      grid-column: 1 / -1;
    }
  }

  @media (max-width: 768px) {
    .flow-steps {
      flex-wrap: wrap;
      padding: 16px;
      gap: 8px;

      .step-line {
        display: none;
      }

      .step {
        flex: 1;
        min-width: 140px;

        .step-info .step-desc {
          display: none;
        }
      }
    }

    .zone-grid {
      grid-template-columns: 1fr;
    }

    .result-layout {
      grid-template-columns: 1fr;
    }

    .result-actions-panel .action-buttons {
      flex-direction: column;
    }
  }
}

@keyframes reportPulse {

  0%,
  100% {
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
  }

  50% {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.7);
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

@keyframes rotate-icon {

  0%,
  100% {
    transform: rotate(0deg) scale(1);
  }

  50% {
    transform: rotate(180deg) scale(1.1);
  }
}

@keyframes progress-move {
  0% {
    margin-left: -30%;
  }

  100% {
    margin-left: 100%;
  }
}
</style>
