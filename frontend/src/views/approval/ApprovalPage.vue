/** 诊断审批页面 - 审批诊断报告流程 */
<template>
  <div class="approval-page">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in statCards" :key="s.key" :class="{ active: filters.status === s.key }"
        @click="filterByStatus(s.key)">
        <div class="stat-value" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <div class="glass-card">
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <div class="filter-item">
          <el-input v-model="filters.keyword" placeholder="患者姓名/编号" clearable @keyup.enter="search"
            class="filter-input">
            <template #prefix><el-icon>
                <Search />
              </el-icon></template>
          </el-input>
        </div>
        <div class="filter-item">
          <span class="filter-label">优先级</span>
          <el-select v-model="filters.priority" placeholder="全部" clearable>
            <el-option label="普通" value="normal" />
            <el-option label="紧急" value="urgent" />
            <el-option label="危急" value="critical" />
          </el-select>
        </div>
        <div class="filter-actions">
          <el-button type="primary" @click="search">
            <el-icon>
              <Search />
            </el-icon> 搜索
          </el-button>
          <el-button @click="resetFilters">
            <el-icon>
              <Refresh />
            </el-icon> 重置
          </el-button>
        </div>
        <div class="filter-actions" style="margin-left: auto;">
          <el-button type="warning" @click="handleSyncMissing" :loading="syncing" v-if="stats.unsubmitted > 0">
            <el-icon>
              <Refresh />
            </el-icon> 同步未提交审批 ({{ stats.unsubmitted }})
          </el-button>
        </div>
      </div>

      <!-- 批量操作栏 -->
      <div class="batch-actions" v-if="selectedRows.length > 0">
        <el-alert type="info" :closable="false" show-icon>
          <span>已选择 <strong>{{ selectedRows.length }}</strong> 条记录</span>
          <el-button type="success" size="small" :loading="batchProcessing" @click="handleBatchApprove"
            style="margin-left: 16px;">
            批量通过
          </el-button>
          <el-button size="small" @click="selectedRows = []">
            取消选择
          </el-button>
        </el-alert>
      </div>

      <!-- 数据表格 -->
      <el-table :data="tableData" v-loading="loading" empty-text="暂无审批记录" class="glass-table" @row-click="openDetail"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column label="患者" width="80">
          <template #default="{ row }">
            <span class="patient-name">{{ row.patient_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="主要发现" min-width="120">
          <template #default="{ row }">
            <span v-if="row.top_disease" class="top-disease" :class="{ exceeded: row.top_threshold_exceeded }">
              {{ row.top_disease }} {{ (row.top_probability * 100).toFixed(1) }}%
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="诊断编号" width="130">
          <template #default="{ row }">{{ row.diagnosis_no || `DX-${row.diagnosis_id}` }}</template>
        </el-table-column>
        <el-table-column label="类型" width="70">
          <template #default="{ row }">
            <span class="type-badge" :class="row.diagnosis_type">{{ row.diagnosis_type === 'batch' ? '批量' : '单次'
            }}</span>
          </template>
        </el-table-column>
        <el-table-column label="提交人" width="120">
          <template #default="{ row }">{{ row.submitter_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="优先级" width="80">
          <template #default="{ row }">
            <span class="priority-badge" :class="row.priority">{{ priorityMap[row.priority] || row.priority }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span class="status-badge" :class="row.status">
              <span class="status-dot-inline" :class="row.status"></span>
              {{ statusMap[row.status] || row.status }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="submitted_at" label="提交时间" min-width="140" />
        <el-table-column label="审批时间" min-width="140">
          <template #default="{ row }">{{ row.reviewed_at || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right" @click.stop>
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="primary" link size="small" class="action-link"
                @click.stop="openReviewDialog(row, 'approve')">通过</el-button>
              <el-button type="warning" link size="small" class="action-link"
                @click.stop="openReviewDialog(row, 'reject')">驳回</el-button>
              <el-button type="info" link size="small" class="action-link"
                @click.stop="openReviewDialog(row, 'revise')">退修</el-button>
            </template>
            <el-button type="primary" link size="small" class="action-link" @click.stop="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.per_page"
          :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData" @current-change="fetchData" />
      </div>
    </div>

    <!-- 审批详情对话框 -->
    <el-dialog v-model="detailVisible" title="审批详情" width="700px" top="5vh">
      <div v-if="currentDetail" class="detail-content">
        <!-- 影像区域 -->
        <div class="detail-images" v-if="currentDetail.image_url || currentDetail.heatmap_url">
          <div class="detail-img-box" v-if="currentDetail.image_url">
            <div class="detail-img-label">原始影像</div>
            <el-image :src="currentDetail.image_url" fit="contain" class="detail-img" lazy
              :preview-src-list="[currentDetail.image_url]" />
          </div>
          <div class="detail-img-box" v-if="currentDetail.heatmap_url">
            <div class="detail-img-label">Grad-CAM 热力图</div>
            <el-image :src="currentDetail.heatmap_url" fit="contain" class="detail-img" lazy
              :preview-src-list="[currentDetail.heatmap_url]" />
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="detail-title">患者信息</div>
          <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">姓名</span><span class="detail-value">{{
              currentDetail.patient?.name || '-' }}</span></div>
            <div class="detail-item"><span class="detail-label">编号</span><span class="detail-value">{{
              currentDetail.patient?.patient_no || '-' }}</span></div>
            <div class="detail-item"><span class="detail-label">性别</span><span class="detail-value">{{
              currentDetail.patient?.gender === 'male' ? '男' : currentDetail.patient?.gender === 'female' ? '女' : '-'
            }}</span></div>
            <div class="detail-item"><span class="detail-label">年龄</span><span class="detail-value">{{
              currentDetail.patient?.age != null ? currentDetail.patient.age + '岁' : '-' }}</span></div>
          </div>
        </div>

        <!-- 诊断信息 -->
        <div class="detail-section">
          <div class="detail-title">诊断结果</div>
          <div class="prob-list" v-if="currentDetail.probabilities?.length">
            <div class="prob-item" v-for="p in currentDetail.probabilities.slice(0, 5)" :key="p.disease_code">
              <span class="prob-name">{{ p.disease_name_zh }}</span>
              <div class="prob-bar-wrap">
                <div class="prob-bar" :class="{ exceeded: p.threshold_exceeded }"
                  :style="{ width: (p.probability * 100) + '%' }"></div>
              </div>
              <span class="prob-value" :class="{ exceeded: p.threshold_exceeded }">{{ (p.probability * 100).toFixed(1)
              }}%</span>
            </div>
          </div>
          <div v-else class="text-muted">暂无概率数据</div>
        </div>

        <!-- 报告内容 -->
        <div class="detail-section" v-if="detailReport">
          <div class="detail-title">AI诊断报告</div>
          <template v-if="hasReportContent">
            <div class="report-preview" v-html="formatReport(detailReport)"
              style="font-size:13px;color:var(--text-secondary);line-height:1.8;max-height:200px;overflow-y:auto;padding:12px;background:var(--glass-bg);border-radius:var(--radius-md);border:1px solid var(--glass-border);">
            </div>
          </template>
          <div v-else class="report-empty"
            style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:28px 16px;color:var(--text-muted);font-size:13px;background:var(--glass-bg);border-radius:var(--radius-md);border:1px dashed var(--glass-border);">
            <el-icon :size="32">
              <Document />
            </el-icon>
            <span>报告尚未生成</span>
            <span style="font-size:12px;color:var(--text-placeholder)">请在诊断中心点击"生成报告"</span>
          </div>
        </div>

        <!-- 审批信息 -->
        <div class="detail-section">
          <div class="detail-title">审批信息</div>
          <div class="detail-grid">
            <div class="detail-item"><span class="detail-label">状态</span>
              <span class="status-badge" :class="currentDetail.status">
                <span class="status-dot-inline" :class="currentDetail.status"></span>
                {{ statusMap[currentDetail.status] }}
              </span>
            </div>
            <div class="detail-item"><span class="detail-label">优先级</span>
              <span class="priority-badge" :class="currentDetail.priority">{{ priorityMap[currentDetail.priority]
              }}</span>
            </div>
            <div class="detail-item"><span class="detail-label">提交人</span><span class="detail-value">{{
              currentDetail.submitter?.real_name || '-' }}</span></div>
            <div class="detail-item"><span class="detail-label">审批人</span><span class="detail-value">{{
              currentDetail.reviewer?.real_name || '-' }}</span></div>
          </div>
          <div v-if="currentDetail.reject_reason" class="reject-reason">
            <span class="detail-label">驳回原因：</span>{{ currentDetail.reject_reason }}
          </div>
          <div v-if="currentDetail.review_notes" class="review-notes">
            <span class="detail-label">审批意见：</span>{{ currentDetail.review_notes }}
          </div>
        </div>
      </div>

      <!-- 审批操作（仅pending状态） -->
      <template #footer v-if="currentDetail?.status === 'pending'">
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="info" @click="detailVisible = false; openReviewDialog(currentDetail, 'revise')">退修</el-button>
        <el-button type="warning"
          @click="detailVisible = false; openReviewDialog(currentDetail, 'reject')">驳回</el-button>
        <el-button type="primary"
          @click="detailVisible = false; openReviewDialog(currentDetail, 'approve')">审批通过</el-button>
      </template>
      <template #footer v-else>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 审批操作对话框 -->
    <el-dialog v-model="reviewVisible" :title="reviewTitle" width="500px">
      <el-form :model="reviewForm" label-width="90px" size="default">
        <el-form-item label="审批操作">
          <el-tag :type="reviewType === 'approve' ? 'success' : reviewType === 'reject' ? 'danger' : 'warning'">
            {{ reviewType === 'approve' ? '通过' : reviewType === 'reject' ? '驳回' : '退回修改' }}
          </el-tag>
        </el-form-item>
        <el-form-item :label="reviewType === 'reject' ? '驳回原因' : '审批意见'" :required="reviewType !== 'approve'">
          <el-input v-model="reviewForm.reason" type="textarea" :rows="3"
            :placeholder="reviewType === 'reject' ? '请输入驳回原因' : reviewType === 'revise' ? '请输入修改意见' : '审批意见（可选）'" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button :type="reviewType === 'approve' ? 'primary' : reviewType === 'reject' ? 'danger' : 'warning'"
          :loading="submitting" @click="handleReview">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Document } from '@element-plus/icons-vue'
import {
  getApprovalsApi, getApprovalApi, approveApprovalApi,
  rejectApprovalApi, requestRevisionApi, getApprovalStatsApi,
  syncMissingApprovalsApi,
} from '@/api/approvals'
import { getReportApi } from '@/api/reports'
import { getDiagnosisApi } from '@/api/diagnose'
import { sanitizeHtml } from '@/utils/xss'

const loading = ref(false)
const submitting = ref(false)
const syncing = ref(false)
const tableData = ref<any[]>([])
const selectedRows = ref<any[]>([])
const batchProcessing = ref(false)
const detailVisible = ref(false)
const reviewVisible = ref(false)
const currentDetail = ref<any>(null)
const currentRow = ref<any>(null)
const fetchedReport = ref<any>(null)
const reviewType = ref<'approve' | 'reject' | 'revise'>('approve')

const stats = reactive({ total: 0, pending: 0, approved: 0, rejected: 0, revision_needed: 0, unsubmitted: 0 })
const filters = reactive({ keyword: '', status: '', priority: '' })
const pagination = reactive({ page: 1, per_page: 20, total: 0 })
const reviewForm = reactive({ reason: '' })

const statusMap: Record<string, string> = {
  pending: '待审批', approved: '已通过', rejected: '已驳回', revision_needed: '待修改',
}
const priorityMap: Record<string, string> = {
  normal: '普通', urgent: '紧急', critical: '危急',
}

const statCards = computed(() => [
  { key: '', label: '全部', value: stats.total, color: 'var(--text-primary)' },
  { key: 'pending', label: '待审批', value: stats.pending, color: '#F59E0B' },
  { key: 'approved', label: '已通过', value: stats.approved, color: 'var(--primary)' },
  { key: 'rejected', label: '已驳回', value: stats.rejected, color: '#EF4444' },
  { key: 'revision_needed', label: '待修改', value: stats.revision_needed, color: '#8B5CF6' },
  { key: 'unsubmitted', label: '未提交', value: stats.unsubmitted, color: '#6B7280' },
])

/** 详情中的报告数据（兼容多种后端返回格式 + 远程获取） */
const detailReport = computed(() => {
  const d = currentDetail.value
  if (!d) return null
  // 1. 内嵌报告（批量诊断）— 必须有实际内容才使用，空壳不放行
  const inline = d.report || d.diagnosis_report || d.ai_report || d.diagnosis?.report
  if (inline && typeof inline === 'object') {
    const inlineContent = inline.final_content || inline.doctor_edited_content ||
      inline.ai_generated_content || inline.findings ||
      inline.impression || inline.recommendations
    if (inlineContent && String(inlineContent).trim()) {
      return inline
    }
    // 内嵌报告是空壳，继续往下走 → 取 fetchedReport
  }
  // 2. 通过 diagnosis_id 远程获取的报告（诊断中心单次诊断）
  if (fetchedReport.value) {
    return fetchedReport.value
  }
  return null
})

/** 报告是否有实际内容（非空对象且至少有一个内容字段有值） */
const hasReportContent = computed(() => {
  const r = detailReport.value
  if (!r || typeof r !== 'object') return false
  const content = r.final_content || r.doctor_edited_content ||
    r.ai_generated_content || r.content || r.report_content ||
    r.findings || r.impression || r.recommendations || r.text || r.body
  return Boolean(content && content.toString().trim())
})

const reviewTitle = computed(() => {
  if (reviewType.value === 'approve') return '审批通过'
  if (reviewType.value === 'reject') return '驳回审批'
  return '退回修改'
})

function filterByStatus(key: string) {
  if (key === 'unsubmitted') {
    // 未提交的审批不在approvals表中，提示用户同步
    if (stats.unsubmitted > 0) {
      handleSyncMissing()
    }
    return
  }
  filters.status = filters.status === key ? '' : key
  search()
}

function formatReport(report: any) {
  if (!report) return ''
  // 方式1：结构化字段（HistoryPage 同款：findings/impression/recommendations）
  const parts: string[] = []
  if (report.findings) parts.push('【检查所见】\n' + report.findings)
  if (report.impression) parts.push('【诊断意见】\n' + report.impression)
  if (report.recommendations) parts.push('【建议】\n' + report.recommendations)
  if (parts.length) return parts.join('<br><br>')

  // 方式2：长文本字段
  const content = report.final_content || report.doctor_edited_content ||
    report.ai_generated_content || report.content || report.report_content ||
    report.text || report.body || (typeof report === 'string' ? report : '') || ''
  return sanitizeHtml(content.replace(/\n/g, '<br>'))
}

async function loadStats() {
  try {
    const res: any = await getApprovalStatsApi()
    Object.assign(stats, res.data)
  } catch { /* handled */ }
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, per_page: pagination.per_page }
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.keyword) params.keyword = filters.keyword
    const res: any = await getApprovalsApi(params)
    tableData.value = res.data.items
    pagination.total = res.data.total
  } catch { /* handled */ } finally { loading.value = false }
}

async function openDetail(row: any) {
  try {
    fetchedReport.value = null // 重置
    const res: any = await getApprovalApi(row.id)
    const data = res.data

    currentDetail.value = data

    // ====== 报告获取策略（参考 HistoryPage 的做法）======
    //
    // 批量诊断：report 内容内嵌在审批记录中，直接使用
    // 单次诊断：需要通过 diagnosis_id 获取完整诊断记录，
    //           从 diagnosis.reports[0] 中提取最新报告内容
    //

    const inlineReport = data.report || data.diagnosis_report || data.ai_report || data.diagnosis?.report

    // 检查内嵌报告是否有实际内容
    if (inlineReport) {
      const inlineContent = inlineReport.final_content || inlineReport.doctor_edited_content ||
        inlineReport.ai_generated_content || inlineReport.findings ||
        inlineReport.impression || inlineReport.recommendations
      if (inlineContent && String(inlineContent).trim()) {
        // 有内容的内嵌报告（批量诊断），直接使用
        fetchedReport.value = inlineReport
        return detailVisible.value = true
      }
    }

    // 内嵌报告为空 → 通过 diagnosis_id 获取诊断记录（和 HistoryPage 相同的方式）
    const diagId = data.diagnosis_id || data.diagnosis?.id
    if (diagId) {
      try {
        const diagRes: any = await getDiagnosisApi(diagId)
        const diagnosis = diagRes.data

        // 和 HistoryPage 一样，从 reports 数组中取
        const reports = diagnosis.reports || []
        if (reports.length > 0) {
          fetchedReport.value = reports[0]
        } else {
          // 没有 reports 数组，尝试 ai_report 字段
          if (diagnosis.ai_report) {
            console.log('[审批详情] 从诊断记录 ai_report 获取到报告')
            fetchedReport.value = diagnosis.ai_report
          }
        }
      } catch (e) {
        console.warn('[审批详情] 获取诊断记录失败:', e)
      }
    }

    // 最终兜底：尝试用 report_id 直接取
    if (!fetchedReport.value) {
      const reportId = data.report_id || data.diagnosis?.report_id
      if (reportId) {
        try {
          const reportRes: any = await getReportApi(reportId)
          fetchedReport.value = reportRes.data
        } catch { /* ignore */ }
      }
    }

    detailVisible.value = true
  } catch { /* handled */ }
}

function openReviewDialog(row: any, type: 'approve' | 'reject' | 'revise') {
  currentRow.value = row
  reviewType.value = type
  reviewForm.reason = ''
  reviewVisible.value = true
}

async function handleReview() {
  if (reviewType.value !== 'approve' && !reviewForm.reason.trim()) {
    ElMessage.warning(reviewType.value === 'reject' ? '请输入驳回原因' : '请输入修改意见')
    return
  }
  submitting.value = true
  try {
    if (reviewType.value === 'approve') {
      await approveApprovalApi(currentRow.value.id, { review_notes: reviewForm.reason })
      ElMessage.success('审批通过')
    } else if (reviewType.value === 'reject') {
      await rejectApprovalApi(currentRow.value.id, { reject_reason: reviewForm.reason, review_notes: reviewForm.reason })
      ElMessage.success('已驳回')
    } else {
      await requestRevisionApi(currentRow.value.id, { review_notes: reviewForm.reason })
      ElMessage.success('已退回修改')
    }
    reviewVisible.value = false
    fetchData()
    loadStats()
  } catch { /* handled */ } finally { submitting.value = false }
}

function search() { pagination.page = 1; fetchData() }
function resetFilters() { filters.keyword = ''; filters.status = ''; filters.priority = ''; search() }

// 批量选择
function handleSelectionChange(selection: any[]) {
  selectedRows.value = selection
}

// 批量审批（占位）
async function handleBatchApprove() {
  ElMessage.info('批量审批功能开发中...')
}

async function handleSyncMissing() {
  syncing.value = true
  try {
    const res: any = await syncMissingApprovalsApi()
    ElMessage.success(`已补建 ${res.data.created} 条审批记录`)
    loadStats()
    fetchData()
  } catch { /* handled */ } finally { syncing.value = false }
}

onMounted(() => { loadStats(); fetchData() })
</script>

<style scoped lang="scss">
.approval-page {

  // 统计卡片
  .stats-row {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 16px;
  }

  .stat-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-md);
    padding: 16px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;

    &:hover {
      border-color: var(--primary);
      transform: translateY(-1px);
    }

    &.active {
      border-color: var(--primary);
      background: rgba(34, 211, 238, 0.08);
    }

    .stat-value {
      font-size: 28px;
      font-weight: 800;
      line-height: 1.2;
    }

    .stat-label {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }
  }

  // 筛选栏
  .filter-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;

    .filter-item {
      display: flex;
      align-items: center;
      gap: 6px;

      .filter-label {
        font-size: 12px;
        color: var(--text-secondary);
        white-space: nowrap;
        flex-shrink: 0;
      }

      .filter-input {
        width: 220px;
      }

      :deep(.el-input__wrapper) {
        height: 36px !important;
        padding: 0 12px !important;
      }

      :deep(.el-select .el-select__wrapper) {
        height: 36px !important;
        min-height: 36px !important;
      }
    }

    .filter-actions {
      display: flex;
      gap: 8px;

      :deep(.el-button) {
        height: 36px !important;
        padding: 0 16px !important;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }

  // 患者姓名
  .patient-name {
    font-weight: 600;
    color: var(--text-primary);
  }

  // 主要发现
  .top-disease {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary);

    &.exceeded {
      color: #EF4444;
    }
  }

  // 类型徽标
  .type-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;

    &.single {
      background: rgba(59, 130, 246, 0.12);
      color: #60A5FA;
    }

    &.batch {
      background: rgba(245, 158, 11, 0.12);
      color: #FBBF24;
    }
  }

  // 优先级徽标
  .priority-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;

    &.normal {
      background: rgba(107, 114, 128, 0.12);
      color: #9CA3AF;
    }

    &.urgent {
      background: rgba(245, 158, 11, 0.15);
      color: #FBBF24;
    }

    &.critical {
      background: rgba(239, 68, 68, 0.15);
      color: #F87171;
    }
  }

  // 状态徽标
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--text-secondary);

    &.pending {
      color: #FBBF24;
    }

    &.approved {
      color: var(--primary);
    }

    &.rejected {
      color: #F87171;
    }

    &.revision_needed {
      color: #A78BFA;
    }
  }

  .status-dot-inline {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;

    &.pending {
      background: #FBBF24;
      box-shadow: 0 0 6px rgba(245, 158, 11, 0.5);
    }

    &.approved {
      background: var(--primary);
      box-shadow: 0 0 8px rgba(34, 211, 238, 0.6);
    }

    &.rejected {
      background: #F87171;
      box-shadow: 0 0 6px rgba(239, 68, 68, 0.5);
    }

    &.revision_needed {
      background: #A78BFA;
      box-shadow: 0 0 6px rgba(139, 92, 246, 0.5);
    }
  }

  .pagination-wrap {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
  }

  // 详情内容
  .detail-content {
    max-height: 60vh;
    overflow-y: auto;
  }

  // 影像区域
  .detail-images {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;

    .detail-img-box {
      .detail-img-label {
        font-size: 12px;
        color: var(--text-secondary);
        font-weight: 600;
        margin-bottom: 6px;
      }

      .detail-img {
        width: 100%;
        height: 180px;
        border-radius: var(--radius-md);
        background: var(--bg-tertiary);
        border: 1px solid var(--glass-border);
      }
    }
  }

  // 详情区块（:deep 穿透 el-dialog Teleport）
  :deep(.detail-section) {
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--glass-border);

    &:last-child {
      border-bottom: none;
      margin-bottom: 0;
    }
  }

  :deep(.detail-title) {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 12px;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .detail-item {
    display: flex;
    align-items: center;
    gap: 8px;

    .detail-label {
      font-size: 13px;
      color: var(--text-muted);
      white-space: nowrap;
    }

    .detail-value {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
    }
  }

  // 概率列表
  .prob-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .prob-item {
    display: flex;
    align-items: center;
    gap: 10px;

    .prob-name {
      width: 80px;
      font-size: 13px;
      color: var(--text-secondary);
      text-align: right;
      flex-shrink: 0;
    }

    .prob-bar-wrap {
      flex: 1;
      height: 8px;
      background: var(--glass-border);
      border-radius: 4px;
      overflow: hidden;
    }

    .prob-bar {
      height: 100%;
      border-radius: 4px;
      background: var(--primary);
      transition: width 0.3s;

      &.exceeded {
        background: #EF4444;
      }
    }

    .prob-value {
      width: 55px;
      font-size: 13px;
      font-weight: 600;
      text-align: right;
      color: var(--text-secondary);

      &.exceeded {
        color: #EF4444;
      }
    }
  }

  // 报告预览（:deep 穿透 el-dialog Teleport）
  :deep(.report-preview) {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.8;
    max-height: 200px;
    overflow-y: auto;
    padding: 12px;
    background: var(--glass-bg);
    border-radius: var(--radius-md);
    border: 1px solid var(--glass-border);
  }

  // 空报告提示
  :deep(.report-empty) {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 28px 16px;
    color: var(--text-muted);
    font-size: 13px;
    background: var(--glass-bg);
    border-radius: var(--radius-md);
    border: 1px dashed var(--glass-border);

    .report-empty-hint {
      font-size: 12px;
      color: var(--text-placeholder);
    }
  }

  // 驳回原因/审批意见
  .reject-reason,
  .review-notes {
    margin-top: 10px;
    padding: 10px;
    border-radius: var(--radius-sm);
    font-size: 13px;
    line-height: 1.6;
  }

  .reject-reason {
    background: rgba(239, 68, 68, 0.08);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.15);
  }

  .review-notes {
    background: rgba(59, 130, 246, 0.08);
    color: #60A5FA;
    border: 1px solid rgba(59, 130, 246, 0.15);
  }

  .text-muted {
    color: var(--text-muted);
  }

  // 表格
  :deep(.el-table__cell) {
    display: table-cell !important;
    vertical-align: middle !important;
  }

  :deep(.el-table__row) {
    cursor: pointer;

    td .cell {
      display: flex;
      align-items: center;
      justify-content: flex-start;
    }
  }

  :deep(.el-table__body tr td) {
    .cell {

      &:has(.priority-badge),
      &:has(.status-badge) {
        justify-content: center;
      }
    }
  }
}
</style>

<style lang="scss">
.action-link {
  background: transparent !important;
  padding: 2px 6px !important;

  &:hover {
    background: transparent !important;
    opacity: 0.8;
  }
}
</style>
