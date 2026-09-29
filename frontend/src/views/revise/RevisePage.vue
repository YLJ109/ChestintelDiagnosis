<template>
    <div class="revise-page">
        <!-- 统计卡片 -->
        <div class="stats-row">
            <div class="stat-card rejected" @click="filterByStatus('rejected')">
                <div class="stat-value">{{ stats.rejected }}</div>
                <div class="stat-label">已退回</div>
            </div>
            <div class="stat-card revision" @click="filterByStatus('revision_needed')">
                <div class="stat-value">{{ stats.revision }}</div>
                <div class="stat-label">需修正</div>
            </div>
            <div class="stat-card total">
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">总计</div>
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
                    <span class="filter-label">状态</span>
                    <el-select v-model="filters.status" placeholder="全部" clearable>
                        <el-option label="已退回" value="rejected" />
                        <el-option label="需修正" value="revision_needed" />
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
            </div>

            <!-- 批量操作栏 -->
            <div class="batch-actions" v-if="selectedRows.length > 0">
                <el-alert type="info" :closable="false" show-icon>
                    <span>已选择 <strong>{{ selectedRows.length }}</strong> 条记录</span>
                    <el-button type="primary" size="small" :loading="batchProcessing" @click="handleBatchRevise"
                        style="margin-left: 16px;">
                        批量修正
                    </el-button>
                    <el-button size="small" @click="selectedRows = []">
                        取消选择
                    </el-button>
                </el-alert>
            </div>

            <!-- 数据表格 -->
            <el-table :data="tableData" v-loading="loading" empty-text="暂无待修改记录" class="glass-table"
                @row-click="openDetail" @selection-change="handleSelectionChange">
                <el-table-column type="selection" width="55" />
                <el-table-column label="患者" width="110">
                    <template #default="{ row }">
                        <div class="patient-info">
                            <div class="patient-name">{{ row.patient_name || '-' }}</div>
                            <div class="patient-no">{{ row.patient_no || '-' }}</div>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="主要发现" width="160">
                    <template #default="{ row }">
                        <span v-if="row.top_disease" class="top-disease"
                            :class="{ exceeded: row.top_threshold_exceeded }">
                            {{ row.top_disease }} {{ (row.top_probability * 100).toFixed(1) }}%
                        </span>
                        <span v-else class="text-muted">-</span>
                    </template>
                </el-table-column>
                <el-table-column label="诊断编号" width="180">
                    <template #default="{ row }">
                        <span class="diagnosis-no">{{ row.diagnosis_no || `DX-${row.diagnosis_id}` }}</span>
                    </template>
                </el-table-column>
                <el-table-column label="状态" width="120">
                    <template #default="{ row }">
                        <span class="status-badge" :class="row.status">
                            <span class="status-dot-inline" :class="row.status"></span>
                            {{ statusMap[row.status] || row.status }}
                        </span>
                    </template>
                </el-table-column>
                <el-table-column label="原因/意见" min-width="200">
                    <template #default="{ row }">
                        <div class="reason-text" :title="row.reject_reason || row.review_notes">
                            {{ row.reject_reason || row.review_notes || '-' }}
                        </div>
                    </template>
                </el-table-column>
                <el-table-column label="审批人" width="120">
                    <template #default="{ row }">{{ row.reviewer_name || '-' }}</template>
                </el-table-column>
                <el-table-column prop="reviewed_at" label="退回时间" width="155" />
                <el-table-column label="操作" width="120" fixed="right" @click.stop>
                    <template #default="{ row }">
                        <el-button link size="small" class="action-link" @click.stop="openReviseDialog(row)">
                            <el-icon>
                                <Edit />
                            </el-icon> 修改报告
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination-bar">
                <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.per_page"
                    :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
                    @size-change="fetchList" @current-change="fetchList" />
            </div>
        </div>

        <!-- 修改报告对话框 -->
        <el-dialog v-model="showReviseDialog" title="诊断修正" width="900px" class="revise-dialog">
            <div v-if="currentApproval" class="revise-content">
                <!-- 患者信息 -->
                <div class="patient-detail-card">
                    <h4>患者信息</h4>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="label">姓名：</span>
                            <span class="value">{{ currentApproval.patient_name }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">编号：</span>
                            <span class="value">{{ currentApproval.patient_no }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">性别：</span>
                            <span class="value">{{ currentApproval.patient_gender === 'male' ? '男' : '女' }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="label">年龄：</span>
                            <span class="value">{{ currentApproval.patient_age }}岁</span>
                        </div>
                    </div>
                </div>

                <!-- 退回/修正原因 -->
                <div class="reason-card" :class="currentApproval.status">
                    <h4>
                        <el-icon>
                            <WarningFilled />
                        </el-icon>
                        {{ currentApproval.status === 'rejected' ? '退回原因' : '修正意见' }}
                    </h4>
                    <p>{{ currentApproval.reject_reason || currentApproval.review_notes }}</p>
                </div>

                <!-- AI原始报告 -->
                <div class="report-section">
                    <h4>AI原始报告</h4>
                    <pre class="ai-report-text">{{ aiReportContent }}</pre>
                </div>

                <!-- 修改后的报告 -->
                <div class="report-section">
                    <h4>修改后报告 <span class="required">*</span></h4>
                    <el-input v-model="revisedReport" type="textarea" :rows="12" placeholder="请根据审批意见修改报告内容..."
                        class="report-textarea" />
                </div>

                <!-- 修改说明 -->
                <div class="report-section">
                    <h4>修改说明</h4>
                    <el-input v-model="reviseNotes" type="textarea" :rows="3" placeholder="请说明修改了哪些内容..." />
                </div>

                <!-- 操作按钮 -->
                <div class="dialog-actions">
                    <el-button @click="showReviseDialog = false">取消</el-button>
                    <el-button type="warning" @click="regenerateReport" :loading="regenerating">
                        <el-icon>
                            <Refresh />
                        </el-icon> 重新生成报告
                    </el-button>
                    <el-button type="primary" @click="submitRevision" :loading="submitting">
                        <el-icon>
                            <Check />
                        </el-icon> 提交修改
                    </el-button>
                </div>
            </div>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Edit, Check, WarningFilled } from '@element-plus/icons-vue'
import http from '@/api/index'

interface ApprovalItem {
    id: number
    diagnosis_id: number
    patient_id: number
    patient_name: string
    patient_no: string
    patient_gender: string
    patient_age: number
    diagnosis_no: string
    top_disease?: string
    top_probability?: number
    top_threshold_exceeded?: boolean
    status: 'rejected' | 'revision_needed'
    reject_reason?: string
    review_notes?: string
    reviewer_name?: string
    reviewed_at?: string
    report_id?: number
}

const loading = ref(false)
const submitting = ref(false)
const regenerating = ref(false)
const tableData = ref<ApprovalItem[]>([])
const selectedRows = ref<ApprovalItem[]>([])
const batchProcessing = ref(false)
const showReviseDialog = ref(false)
const currentApproval = ref<ApprovalItem | null>(null)
const aiReportContent = ref('')
const revisedReport = ref('')
const reviseNotes = ref('')

const filters = reactive({
    keyword: '',
    status: '',
})

const pagination = reactive({
    page: 1,
    per_page: 20,
    total: 0,
})

const stats = reactive({
    rejected: 0,
    revision: 0,
    total: 0,
})

const statusMap: Record<string, string> = {
    rejected: '已退回',
    revision_needed: '需修正',
}

// 获取列表
async function fetchList() {
    loading.value = true
    try {
        const params: any = {
            page: pagination.page,
            per_page: pagination.per_page,
        }
        if (filters.keyword) params.keyword = filters.keyword

        // F-10: "全部" = 已退回 + 需修正，走后端多状态查询，保持标准分页
        params.status = filters.status || 'rejected,revision_needed'

        const res: any = await http.get('/approvals/', { params })
        if (res.code === 200) {
            tableData.value = res.data.items || []
            pagination.total = res.data.total
        }
    } catch (e: any) {
        console.error('获取列表失败', e)
        tableData.value = []
        pagination.total = 0
    } finally {
        loading.value = false
    }
}

// 获取统计
async function fetchStats() {
    try {
        const res: any = await http.get('/approvals/stats')
        if (res.code === 200) {
            stats.rejected = res.data.rejected || 0
            stats.revision = res.data.revision_needed || 0  // 修正字段名
            stats.total = stats.rejected + stats.revision
        }
    } catch (e: any) {
        console.error('获取统计失败', e)
        // 静默失败，不显示错误消息
    }
}

// 搜索
function search() {
    pagination.page = 1
    fetchList()
}

// 重置筛选
function resetFilters() {
    filters.keyword = ''
    filters.status = ''
    pagination.page = 1
    fetchList()
}

// 批量选择
function handleSelectionChange(selection: ApprovalItem[]) {
    selectedRows.value = selection
}

// 批量修正（占位）
async function handleBatchRevise() {
    ElMessage.info('批量修正功能开发中...')
}

// 按状态筛选
function filterByStatus(status: string) {
    filters.status = status
    pagination.page = 1
    fetchList()
}

// 打开详情
async function openDetail(row: ApprovalItem) {
    try {
        const res: any = await http.get(`/approvals/${row.id}`)
        if (res.code === 200 && res.data.report) {
            aiReportContent.value = res.data.report.ai_generated_content ||
                res.data.report.findings || ''
        }
    } catch (e) {
        console.error('获取详情失败', e)
    }
}

// 打开修改对话框
async function openReviseDialog(row: ApprovalItem) {
    currentApproval.value = row
    revisedReport.value = ''
    reviseNotes.value = ''
    aiReportContent.value = ''

    // 获取审批详情（包含报告和患者信息）
    try {
        const res: any = await http.get(`/approvals/${row.id}`)
        console.log('[诊断修正] API返回数据:', res)

        if (res.code === 200) {
            const data = res.data
            console.log('[诊断修正] 审批详情data:', data)
            console.log('[诊断修正] data.report:', data.report)
            console.log('[诊断修正] data.report_id:', data.report_id)
            console.log('[诊断修正] data.diagnosis:', data.diagnosis)
            console.log('[诊断修正] data.probabilities:', data.probabilities)
            console.log('[诊断修正] data.diagnosis?.disease_probabilities:', data.diagnosis?.disease_probabilities)

            // ✅ 提取患者信息
            if (data.patient) {
                currentApproval.value.patient_name = data.patient.name
                currentApproval.value.patient_no = data.patient.patient_no
                currentApproval.value.patient_gender = data.patient.gender
                currentApproval.value.patient_age = data.patient.age
                console.log('[诊断修正] 患者信息:', data.patient)
            }

            // ✅ 提取AI报告内容
            if (data.report) {
                // 优先使用报告数据
                aiReportContent.value = data.report.ai_generated_content ||
                    data.report.findings ||
                    data.report.content || ''
                console.log('[诊断修正] 使用报告数据')
            } else if (data.diagnosis && data.probabilities && data.probabilities.length > 0) {
                // ✅ 降级方案：该诊断尚未生成完整报告，显示疾病概率作为参考
                // 提供报告模板，让医生可以手动填写完整报告
                const topDiseases = data.probabilities
                    .sort((a: any, b: any) => b.probability - a.probability)
                    .slice(0, 5)

                if (topDiseases.length > 0) {
                    // 生成报告模板，包含疾病概率作为参考
                    aiReportContent.value = `【影像学表现】
（请根据影像资料和AI诊断结果，描述影像学表现）

AI辅助诊断参考：
${topDiseases.map((d: any, i: number) =>
                        `  ${i + 1}. ${d.disease_name_zh} (${(d.probability * 100).toFixed(1)}%)`
                    ).join('\n')}

【诊断结论】
（请根据影像学表现和AI参考结果，给出诊断结论）

【建议】
（请给出临床建议）`
                    console.log('[诊断修正] 生成报告模板（含疾病概率参考）', topDiseases)
                } else {
                    // 如果连疾病概率都没有，提供空白模板
                    aiReportContent.value = `【影像学表现】
（请描述影像学表现）

【诊断结论】
（请给出诊断结论）

【建议】
（请给出临床建议）`
                    console.warn('[诊断修正] 无疾病概率数据，生成空白模板')
                }
            } else {
                console.warn('[诊断修正] 未找到报告或诊断数据')
            }

            // 预填充为当前内容
            if (aiReportContent.value) {
                revisedReport.value = aiReportContent.value
            }
        }
    } catch (e) {
        console.error('获取审批详情失败', e)
        ElMessage.error('获取审批详情失败')
    }

    showReviseDialog.value = true
}

// 重新生成报告
async function regenerateReport() {
    if (!currentApproval.value?.report_id) {
        ElMessage.warning('该记录没有关联的报告')
        return
    }

    regenerating.value = true
    try {
        const res: any = await http.post(`/reports/${currentApproval.value.report_id}/regenerate`)
        if (res.code === 200) {
            ElMessage.success('报告重新生成成功')
            // 刷新对话框内容
            const detailRes: any = await http.get(`/approvals/${currentApproval.value.id}`)
            if (detailRes.code === 200 && detailRes.data.report) {
                aiReportContent.value = detailRes.data.report.ai_generated_content ||
                    detailRes.data.report.findings || ''
                revisedReport.value = aiReportContent.value
            }
            fetchList()
        }
    } catch (e: any) {
        ElMessage.error(e.message || '重新生成失败')
    } finally {
        regenerating.value = false
    }
}

// 提交修改
async function submitRevision() {
    if (!revisedReport.value.trim()) {
        ElMessage.warning('请填写修改后的报告内容')
        return
    }

    if (!currentApproval.value?.report_id) {
        ElMessage.error('无法找到关联的报告')
        return
    }

    submitting.value = true
    try {
        // 更新报告内容
        const updateData: any = {
            doctor_edited_content: revisedReport.value,
        }
        if (reviseNotes.value) {
            updateData.editor_notes = reviseNotes.value
        }

        await http.put(`/reports/${currentApproval.value.report_id}`, updateData)

        // 更新审批状态为已通过
        await http.post(`/approvals/${currentApproval.value.id}/approve`)

        ElMessage.success('修改提交成功')
        showReviseDialog.value = false
        fetchList()
        fetchStats()
    } catch (e: any) {
        ElMessage.error(e.message || '提交失败')
    } finally {
        submitting.value = false
    }
}

onMounted(() => {
    fetchList()
    fetchStats()
})
</script>

<style scoped lang="scss">
.revise-page {
    padding: 0px;
}

.stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 20px;
}

.stat-card {
    background: var(--card-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
        transform: translateY(-2px);
        box-shadow: var(--card-shadow-hover);
    }

    &.rejected {
        border-left: 4px solid #EF4444;
    }

    &.revision {
        border-left: 4px solid #F59E0B;
    }

    &.total {
        border-left: 4px solid var(--primary);
    }

    .stat-value {
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 8px;
    }

    .stat-label {
        font-size: 14px;
        color: var(--text-secondary);
    }
}

.glass-card {
    background: var(--card-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    padding: 24px;
}

.filter-bar {
    display: flex;
    gap: 16px;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;

    .filter-item {
        display: flex;
        align-items: center;
        gap: 8px;

        .filter-label {
            font-size: 14px;
            color: var(--text-secondary);
            white-space: nowrap;
        }

        .filter-input {
            width: 240px;
        }
    }
}

.glass-table {
    :deep(.el-table) {
        background: transparent;
    }

    :deep(.el-table__row) {
        cursor: pointer;
        transition: background 0.2s ease;

        &:hover {
            background: var(--glass-bg-hover);
        }
    }
}

.patient-info {
    .patient-name {
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.3;
    }

    .patient-no {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 2px;
        line-height: 1.3;
    }
}

.diagnosis-no {
    font-size: 13px;
    color: var(--text-secondary);
    word-break: break-all;
    line-height: 1.4;
    display: inline-block;
    width: 100%;
}

.top-disease {
    font-size: 13px;
    color: var(--text-secondary);

    &.exceeded {
        color: #EF4444;
        font-weight: 600;
    }
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;

    &.rejected {
        background: rgba(239, 68, 68, 0.1);
        color: #EF4444;
    }

    &.revision_needed {
        background: rgba(245, 158, 11, 0.1);
        color: #F59E0B;
    }
}

.status-dot-inline {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;

    &.rejected {
        background: #EF4444;
    }

    &.revision_needed {
        background: #F59E0B;
    }
}

.reason-text {
    font-size: 13px;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
    line-height: 1.4;
}

.action-buttons {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.action-link {
    font-size: 13px;
    padding: 0;
    white-space: nowrap;
    color: var(--text-secondary);
    transition: all 0.2s;

    &:hover {
        color: var(--primary-color);
        background: rgba(59, 130, 246, 0.1);
    }
}

.dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid var(--glass-border);
    margin-top: 20px;
}

.pagination-bar {
    display: flex;
    justify-content: flex-end;
    margin-top: 20px;
}

.revise-dialog {
    :deep(.el-dialog) {
        background: var(--card-bg);
        border: 1px solid var(--glass-border);
    }
}

.revise-content {
    max-height: 70vh;
    overflow-y: auto;
    padding-right: 8px;
}

.patient-detail-card,
.reason-card,
.report-section {
    margin-bottom: 20px;
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);

    h4 {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 12px 0;
        display: flex;
        align-items: center;
        gap: 6px;

        .required {
            color: #EF4444;
            margin-left: 4px;
        }
    }
}

.detail-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;

    .detail-item {
        .label {
            font-size: 13px;
            color: var(--text-muted);
        }

        .value {
            font-size: 14px;
            color: var(--text-primary);
            font-weight: 500;
        }
    }
}

.reason-card {
    &.rejected {
        border-left: 4px solid #EF4444;
    }

    &.revision_needed {
        border-left: 4px solid #F59E0B;
    }

    p {
        font-size: 14px;
        color: var(--text-primary);
        line-height: 1.6;
        margin: 0;
    }
}

.ai-report-text,
.report-textarea {
    font-size: 13px;
    line-height: 1.8;
    color: var(--text-primary);
    background: var(--card-bg);
    padding: 12px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--glass-border);
    white-space: pre-wrap;
    word-break: break-word;
}

.report-textarea {
    :deep(textarea) {
        font-size: 13px;
        line-height: 1.8;
        font-family: inherit;
    }
}
</style>