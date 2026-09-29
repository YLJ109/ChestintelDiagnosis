<!-- // AI辅助开发：DeepSeek-Coder-V2，2026.03.28
// 人工修改：增加 AbortController 实现任务取消、细化进度状态枚举（pending/processing/completed/failed）、优化三列 Grid 布局响应式适配
/** 批量诊断页面 - 从文件名解析患者信息 */ -->
<template>
    <div class="batch-diagnose-page">
        <!-- 顶部步骤指示器 -->
        <div class="top-bar">
            <div class="steps-indicator">
                <div class="step-item" :class="{ active: currentStep >= 1, done: currentStep > 1 }">
                    <div class="step-num">1</div>
                    <div class="step-text">
                        <div class="step-title">选择影像</div>
                        <div class="step-desc">上传并关联患者</div>
                    </div>
                </div>
                <div class="step-line" :class="{ active: currentStep >= 2 }"></div>
                <div class="step-item" :class="{ active: currentStep >= 2, done: currentStep > 2 }">
                    <div class="step-num">2</div>
                    <div class="step-text">
                        <div class="step-title">AI检测</div>
                        <div class="step-desc">批量智能分析</div>
                    </div>
                </div>
                <div class="step-line" :class="{ active: currentStep >= 3 }"></div>
                <div class="step-item" :class="{ active: currentStep >= 3 }">
                    <div class="step-num">3</div>
                    <div class="step-text">
                        <div class="step-title">报告生成</div>
                        <div class="step-desc">查看结果与报告</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 主体内容 -->
        <div class="main-content">
            <!-- 阶段1：上传影像（未开始诊断） -->
            <div v-if="!diagnosing && patientResults.length === 0" class="phase-upload">
                <!-- 空状态：上传区域 -->
                <div v-if="imageItems.length === 0" class="upload-container">
                    <div class="upload-card">
                        <div class="card-header">
                            <div class="header-left">
                                <div class="upload-icon">
                                    <el-icon :size="20">
                                        <Upload />
                                    </el-icon>
                                </div>
                                <div class="header-text">
                                    <div class="header-title">选择影像</div>
                                    <div class="header-subtitle">SELECT IMAGES</div>
                                </div>
                            </div>
                            <el-tag type="info" size="small">待选择</el-tag>
                        </div>
                        <div class="card-body">
                            <el-upload ref="uploadRef" drag :auto-upload="false" :show-file-list="false" :limit="50"
                                accept=".png,.jpg,.jpeg,.bmp,.gif,.webp" :on-change="onFileChange" multiple>
                                <div class="upload-placeholder">
                                    <el-icon :size="48" color="var(--primary)">
                                        <Upload />
                                    </el-icon>
                                    <div class="upload-main-text">拖拽或点击选择X光影像文件</div>
                                    <div class="upload-sub-text">
                                        支持 <span class="highlight">PNG / JPG / JPEG / DCM</span>，可多选或选择整个文件夹
                                    </div>
                                    <div class="upload-format-hint">
                                        文件名格式：<span class="format-code">P患者ID-姓名-性别-年龄-临床发现-图片ID.扩展名</span>
                                    </div>
                                </div>
                            </el-upload>
                        </div>
                        <div class="card-footer">
                            <el-button type="primary" disabled>
                                <el-icon class="is-loading" v-if="false">
                                    <Loading />
                                </el-icon>
                                开始检测 (0张)
                            </el-button>
                        </div>
                    </div>
                </div>

                <!-- 有数据：影像列表 -->
                <div v-else class="images-container">
                    <div class="images-card">
                        <div class="card-header">
                            <div class="header-left">
                                <div class="upload-icon">
                                    <el-icon :size="20">
                                        <Upload />
                                    </el-icon>
                                </div>
                                <div class="header-text">
                                    <div class="header-title">选择影像</div>
                                    <div class="header-subtitle">SELECT IMAGES</div>
                                </div>
                            </div>
                            <el-tag type="success" size="small">已选 {{ imageItems.length }} 张</el-tag>
                        </div>

                        <div class="card-body">
                            <div class="images-grid">
                                <div v-for="(item, index) in imageItems" :key="index" class="image-item">
                                    <div class="image-thumbnail">
                                        <el-image :src="item.thumbnail" fit="cover" class="thumb-img" lazy />
                                        <div class="image-overlay">
                                            <el-button type="danger" circle size="small" @click="removeImage(index)">
                                                <el-icon>
                                                    <Delete />
                                                </el-icon>
                                            </el-button>
                                        </div>
                                    </div>
                                    <div class="image-info">
                                        <div class="image-filename">{{ item.filename }}</div>
                                        <div class="image-size">{{ item.fileSize }}</div>

                                        <div class="patient-badge" v-if="item.parsed">
                                            <el-avatar :size="20"
                                                :style="{ background: getAvatarColor(item.parsed.name) }">
                                                {{ item.parsed.name?.charAt(0) || '?' }}
                                            </el-avatar>
                                            <div class="patient-details">
                                                <div class="patient-name-row">
                                                    <span class="name">{{ item.parsed.name }}</span>
                                                    <span class="gender-age">{{ item.parsed.gender === 'male' ? '男' :
                                                        '女' }}
                                                        / {{ item.parsed.age }}岁</span>
                                                </div>
                                                <div class="patient-id">{{ item.parsed.patientId }}</div>
                                            </div>
                                        </div>

                                        <div class="clinical-info" v-if="item.parsed">
                                            <el-tag size="small" type="info" effect="plain">
                                                {{ getClinicalDisplay(item.parsed.clinical) }}
                                            </el-tag>
                                            <span class="image-index">图片#{{ item.parsed.imageId }}</span>
                                        </div>

                                        <div class="match-status" v-if="item.parsed">
                                            <el-icon color="var(--primary)">
                                                <CircleCheck />
                                            </el-icon>
                                            <span>已匹配患者</span>
                                        </div>

                                        <!-- ✅ 文件丢失提示 -->
                                        <div v-if="!item.file" class="file-missing-alert">
                                            <el-alert type="info" :closable="false" show-icon size="small">
                                                <template #title>
                                                    <span style="font-size: 11px">ℹ️ 原始文件需重新上传（诊断结果已保留）</span>
                                                </template>
                                            </el-alert>
                                        </div>

                                        <div class="symptom-input" v-if="item.parsed && item.file">
                                            <el-input v-model="item.parsed.symptom" placeholder="症状描述" size="small" />
                                        </div>

                                        <!-- ✅ 文件名不规范时，显示患者选择 -->
                                        <div v-if="!item.parsed && item.file" class="patient-select">
                                            <el-alert type="warning" :closable="false" show-icon size="small">
                                                <template #title>
                                                    <span style="font-size: 11px">文件名不规范</span>
                                                </template>
                                            </el-alert>
                                            <div class="select-actions">
                                                <el-button size="small" type="primary" plain
                                                    @click="openPatientSelectDialog(index)">
                                                    <el-icon>
                                                        <User />
                                                    </el-icon>
                                                    选择患者
                                                </el-button>
                                                <el-button size="small" type="success" plain
                                                    @click="openCreatePatientDialog(index)">
                                                    <el-icon>
                                                        <Plus />
                                                    </el-icon>
                                                    创建患者
                                                </el-button>
                                            </div>
                                            <div v-if="item.selectedPatient" class="selected-patient-info">
                                                <el-icon color="var(--primary)">
                                                    <CircleCheck />
                                                </el-icon>
                                                <span>{{ item.selectedPatient.name }} ({{
                                                    item.selectedPatient.patient_no }})</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card-footer">
                            <!-- ✅ 隐藏的 el-upload 组件，用于继续添加文件 -->
                            <el-upload ref="uploadRef" :auto-upload="false" :show-file-list="false" :limit="50"
                                accept=".png,.jpg,.jpeg,.bmp,.gif,.webp" :on-change="onFileChange" multiple
                                style="display: none;">
                            </el-upload>
                            <el-button plain @click="handleAddMore">
                                <el-icon>
                                    <Plus />
                                </el-icon> 继续添加
                            </el-button>
                            <el-button type="primary" @click="handleStartDiagnosis" :disabled="diagnosing">
                                <el-icon class="is-loading" v-if="diagnosing">
                                    <Loading />
                                </el-icon>
                                开始检测 ({{ imageItems.length }}张)
                            </el-button>
                            <el-button plain @click="handleClearAll">
                                <el-icon>
                                    <Delete />
                                </el-icon> 清空
                            </el-button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 阶段2-3：诊断中/诊断完成（三栏布局） -->
            <div v-else class="phase-diagnosis">
                <!-- 顶部进度信息 -->
                <div class="diagnosis-header" v-if="diagnosing">
                    <div class="current-file-info">
                        <span class="file-name">{{ currentFileName }}</span>
                        <span class="progress-text">检测中 {{ completedCount }}/{{ imageItems.length }}</span>
                    </div>
                </div>

                <!-- 三栏布局 -->
                <div class="three-columns">
                    <!-- 左侧：患者列表 -->
                    <div class="left-panel">
                        <div class="panel-header">
                            <span class="panel-title">患者列表</span>
                            <span class="panel-badge">{{ patientResults.length }}人</span>
                        </div>
                        <div class="panel-body">
                            <div v-for="(patient, idx) in patientResults" :key="idx" class="patient-item"
                                :class="{ active: selectedPatientIndex === idx }" @click="selectPatient(idx)">
                                <div class="patient-avatar"
                                    :style="{ background: getAvatarColor(patient.name || '?') }">
                                    {{ (patient.name || '?').charAt(0) }}
                                </div>
                                <div class="patient-info">
                                    <div class="patient-name">
                                        {{ patient.name || '未知患者' }}
                                        <span v-if="patient.patient_no" class="patient-no">({{ patient.patient_no
                                            }})</span>
                                    </div>
                                    <div class="patient-status">
                                        <el-tag v-if="patient.status === 'waiting'" size="small" type="info">
                                            <el-icon class="is-loading" :size="12">
                                                <Loading />
                                            </el-icon>
                                            等待中
                                        </el-tag>
                                        <el-tag v-else-if="patient.status === 'processing'" size="small" type="warning">
                                            <el-icon class="is-loading" :size="12">
                                                <Loading />
                                            </el-icon>
                                            诊断中
                                        </el-tag>
                                        <el-tag v-else-if="patient.status === 'completed'" size="small" type="success">
                                            已完成
                                        </el-tag>
                                        <el-tag v-else-if="patient.status === 'error'" size="small" type="danger">
                                            失败
                                        </el-tag>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="panel-footer" v-if="diagnosing || diagnosisAborted || patientResults.length > 0">
                            <el-button v-if="diagnosing" type="danger" size="small" @click="handleStopDiagnosis"
                                style="width:100%">
                                <el-icon>
                                    <Close />
                                </el-icon> 终止检测
                            </el-button>
                            <el-button v-else type="warning" size="small" @click="handleClearData" style="width:100%">
                                <el-icon>
                                    <Delete />
                                </el-icon> 清空数据
                            </el-button>
                        </div>
                    </div>

                    <!-- 中间：诊断结果 -->
                    <div class="center-panel">
                        <!-- 等待诊断 -->
                        <div v-if="currentPatientResult?.status === 'waiting'" class="waiting-state">
                            <div class="loading-spinner">
                                <div class="spinner-ring"></div>
                                <div class="spinner-ring"></div>
                                <div class="spinner-ring"></div>
                                <div class="spinner-icon">
                                    <el-icon :size="32" class="rotating-icon">
                                        <Cpu />
                                    </el-icon>
                                </div>
                            </div>
                            <p class="waiting-text">等待诊断中...</p>
                            <p class="waiting-hint">前面还有 {{ selectedPatientIndex }} 个患者</p>
                        </div>

                        <!-- 诊断中 -->
                        <div v-else-if="currentPatientResult?.status === 'processing'" class="processing-state">
                            <div class="loading-spinner">
                                <div class="spinner-ring"></div>
                                <div class="spinner-ring"></div>
                                <div class="spinner-ring"></div>
                                <div class="spinner-icon">
                                    <el-icon :size="32" class="rotating-icon">
                                        <Cpu />
                                    </el-icon>
                                </div>
                            </div>
                            <p class="processing-text">AI正在分析影像...</p>
                            <p class="processing-hint">请稍候，正在提取特征</p>
                        </div>

                        <!-- 诊断完成 -->
                        <template v-else-if="currentPatientResult?.status === 'completed'">
                            <!-- ✅ 立即显示诊断结果（不等待AI报告） -->
                            <!-- 诊断结果头部 -->
                            <div class="result-header" v-if="currentPatientResult">
                                <div class="result-badge"
                                    :class="currentPatientResult.result?.includes('正常') ? 'normal' : 'abnormal'">
                                    <el-icon :size="24">
                                        <CircleCheck v-if="currentPatientResult.result?.includes('正常')" />
                                        <Warning v-else />
                                    </el-icon>
                                    <div class="result-text">
                                        <div class="result-title">{{ currentPatientResult.result }}</div>
                                        <div class="result-conf">置信度 {{ currentPatientResult.confidence }}%</div>
                                    </div>
                                </div>
                            </div>

                            <!-- 患者信息卡片 -->
                            <div class="info-card" v-if="currentPatientResult?.patient">
                                <div class="card-title">患者信息</div>
                                <div class="info-grid">
                                    <div class="info-row">
                                        <span class="label">姓名</span>
                                        <span class="value">{{ currentPatientResult.patient.name || '-' }}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="label">性别</span>
                                        <span class="value">{{ currentPatientResult.patient.gender === 'male' ? '男' :
                                            '女'
                                        }}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="label">年龄</span>
                                        <span class="value">{{ currentPatientResult.patient.age }}岁</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="label">临床信息</span>
                                        <span class="value">{{ currentPatientResult.clinical_info || '体检' }}</span>
                                    </div>
                                </div>
                            </div>

                            <!-- 概率分布 -->
                            <div class="prob-card" v-if="currentPatientResult?.probabilities">
                                <div class="card-title">疾病概率分布</div>
                                <div class="prob-list">
                                    <div v-for="(prob, idx) in currentPatientResult.probabilities.slice(0, 5)"
                                        :key="idx" class="prob-item">
                                        <div class="prob-header">
                                            <span class="prob-dot"
                                                :style="{ background: getProbColor(prob.disease_code) }"></span>
                                            <span class="prob-label">{{ prob.disease_name_zh }}</span>
                                            <span class="prob-value">{{ (prob.probability * 100).toFixed(1) }}%</span>
                                        </div>
                                        <div class="prob-bar">
                                            <div class="prob-fill" :style="{
                                                width: (prob.probability * 100) + '%',
                                                background: getProbColor(prob.disease_code)
                                            }"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 影像展示 -->
                            <div class="image-cards" v-if="currentPatientResult?.imageUrl">
                                <div class="image-card">
                                    <div class="image-label">原始影像</div>
                                    <el-image :src="currentPatientResult.imageUrl" fit="contain" class="preview-img"
                                        lazy />
                                </div>
                                <div class="image-card" v-if="currentPatientResult.heatmapUrl">
                                    <div class="image-label">热力图</div>
                                    <el-image :src="currentPatientResult.heatmapUrl" fit="contain" class="preview-img"
                                        lazy />
                                </div>
                            </div>
                        </template>

                        <!-- 错误状态 -->
                        <div v-else-if="currentPatientResult?.status === 'error'" class="error-state">
                            <el-icon :size="48" color="var(--danger)">
                                <CircleClose />
                            </el-icon>
                            <p>诊断失败</p>
                        </div>

                        <!-- 空状态 -->
                        <div v-else class="empty-center">
                            <el-icon :size="48" color="var(--text-muted)">
                                <Document />
                            </el-icon>
                            <p>正在分析中，请稍候...</p>
                        </div>
                    </div>

                    <!-- 右侧：AI报告 -->
                    <div class="right-panel">
                        <div class="panel-header">
                            <span class="panel-title">AI诊断报告</span>
                            <el-button v-if="currentPatientResult?.diagnosis_id" type="primary" size="small"
                                @click="handlePrint(currentPatientResult)">
                                打印报告
                            </el-button>
                        </div>
                        <div class="panel-body">
                            <!-- ✅ 报告加载中（漂亮的加载动画） -->
                            <div v-if="currentPatientResult?.generatingReport" class="report-loading">
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

                            <!-- 报告内容 -->
                            <div v-else-if="currentPatientResult?.reportContent" class="report-content">
                                <div class="report-text"
                                    v-html="formatReportToHtml(currentPatientResult.reportContent)"></div>
                            </div>

                            <!-- 空状态（诊断未完成时显示） -->
                            <div v-else class="report-waiting">
                                <el-icon :size="48" color="var(--text-muted)">
                                    <Document />
                                </el-icon>
                                <p>等待诊断完成</p>
                                <span class="hint-text">AI诊断完成后将自动生成报告</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 底部导航 -->
                <div class="bottom-nav" v-if="patientResults.length > 0">
                    <el-button size="small" :disabled="selectedPatientIndex === 0" @click="prevPatient">
                        <el-icon>
                            <ArrowLeft />
                        </el-icon> 上一个
                    </el-button>
                    <div class="nav-info">
                        <span class="nav-text">第 {{ selectedPatientIndex + 1 }}/{{ patientResults.length }} 个患者</span>
                        <el-select v-model="selectedPatientIndex" size="small" style="width: 200px"
                            @change="onPatientSelect">
                            <el-option v-for="(p, idx) in patientResults" :key="idx"
                                :label="`${p.name || '未知'} (${p.patient_no || ''})`" :value="idx" />
                        </el-select>
                    </div>
                    <el-button size="small" :disabled="selectedPatientIndex === patientResults.length - 1"
                        @click="nextPatient">
                        下一个 <el-icon>
                            <ArrowRight />
                        </el-icon>
                    </el-button>


                </div>
            </div>
        </div>

        <!-- ✅ 选择患者对话框 -->
        <el-dialog v-model="patientSelectDialogVisible" title="选择患者" width="600px" :close-on-click-modal="false">
            <el-input v-model="patientSearchKeyword" placeholder="搜索患者姓名或编号" clearable style="margin-bottom: 16px">
                <template #prefix>
                    <el-icon>
                        <Search />
                    </el-icon>
                </template>
            </el-input>
            <div class="patient-list" style="max-height: 400px; overflow-y: auto">
                <div v-for="patient in filteredPatients" :key="patient.id" class="patient-option"
                    :class="{ selected: tempSelectedPatient?.id === patient.id }"
                    @click="tempSelectedPatient = patient">
                    <div class="patient-option-info">
                        <el-avatar :size="36" :style="{ background: getAvatarColor(patient.name) }">
                            {{ patient.name?.charAt(0) || '?' }}
                        </el-avatar>
                        <div class="patient-option-details">
                            <div class="patient-option-name">{{ patient.name }}</div>
                            <div class="patient-option-meta">
                                <span>{{ patient.patient_no }}</span>
                                <span>{{ patient.gender === 'male' ? '男' : '女' }} / {{ patient.age }}岁</span>
                            </div>
                        </div>
                    </div>
                    <el-icon v-if="tempSelectedPatient?.id === patient.id" color="var(--primary)" :size="20">
                        <CircleCheck />
                    </el-icon>
                </div>
                <el-empty v-if="filteredPatients.length === 0" description="暂无匹配的患者" />
            </div>
            <template #footer>
                <el-button @click="patientSelectDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="confirmSelectPatient" :disabled="!tempSelectedPatient">
                    确定选择
                </el-button>
            </template>
        </el-dialog>

        <!-- ✅ 创建患者对话框 -->
        <el-dialog v-model="patientCreateDialogVisible" title="创建新患者" width="500px" :close-on-click-modal="false">
            <el-form :model="newPatientForm" label-width="80px" label-position="left">
                <el-form-item label="患者编号" required>
                    <el-input v-model="newPatientForm.patient_no" placeholder="如：P20260101001" />
                </el-form-item>
                <el-form-item label="姓名" required>
                    <el-input v-model="newPatientForm.name" placeholder="请输入姓名" />
                </el-form-item>
                <el-form-item label="性别" required>
                    <el-radio-group v-model="newPatientForm.gender">
                        <el-radio value="male">男</el-radio>
                        <el-radio value="female">女</el-radio>
                    </el-radio-group>
                </el-form-item>
                <el-form-item label="年龄" required>
                    <el-input-number v-model="newPatientForm.age" :min="0" :max="150" style="width: 100%" />
                </el-form-item>
                <el-form-item label="电话">
                    <el-input v-model="newPatientForm.phone" placeholder="可选" />
                </el-form-item>
                <el-form-item label="地址">
                    <el-input v-model="newPatientForm.address" placeholder="可选" type="textarea" :rows="2" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="patientCreateDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="confirmCreatePatient">创建并选择</el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { diagnoseSingleApi } from '@/api/diagnose'
import { createPatientApi, getPatientsApi } from '@/api/patients'
import { ElMessage, ElMessageBox } from 'element-plus'
import { escapeHtml } from '@/utils/xss'
import {
    Upload, Delete, Plus, Loading, CircleCheck, Document, InfoFilled, Warning, Close, User, Search,
    ArrowLeft, ArrowRight
} from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'

const router = useRouter()
const uploadRef = ref()
const diagnosing = ref(false)
const diagnosisAborted = ref(false) // 诊断是否被终止
let diagnosisTask: any = null // 保存诊断任务引用
let abortController: AbortController | null = null // ✅ 用于中断API请求

// ✅ 患者选择对话框相关
const patientSelectDialogVisible = ref(false)
const patientCreateDialogVisible = ref(false)
const patientSearchKeyword = ref('')
const tempSelectedPatient = ref<any>(null)
const currentEditImageIndex = ref(-1)  // 当前编辑的影像索引
const availablePatients = ref<any[]>([])  // 可用患者列表

// ✅ 新患者表单
const newPatientForm = ref({
    patient_no: '',
    name: '',
    gender: 'male',
    age: 30,
    phone: '',
    address: ''
})

// 过滤后的患者列表
const filteredPatients = computed(() => {
    if (!patientSearchKeyword.value) return availablePatients.value
    const keyword = patientSearchKeyword.value.toLowerCase()
    return availablePatients.value.filter(p =>
        p.name?.toLowerCase().includes(keyword) ||
        p.patient_no?.toLowerCase().includes(keyword)
    )
})

interface ParsedInfo {
    patientId: string
    name: string
    gender: string
    age: number
    clinical: string
    imageId: string
    symptom: string
}

interface ImageItem {
    file: File
    filename: string
    fileSize: string
    thumbnail: string
    parsed: ParsedInfo | null
    selectedPatient: any | null  // ✅ 用户手动选择的患者
}

const imageItems = ref<ImageItem[]>([])
const patientResults = ref<any[]>([])
const selectedPatientIndex = ref(0)
const completedCount = ref(0)

// 计算属性
const currentStep = computed(() => {
    if (patientResults.value.length > 0 && completedCount.value === imageItems.value.length) return 3
    if (patientResults.value.length > 0) return 2
    return 1
})

const currentFileName = computed(() => {
    if (imageItems.value.length === 0) return '-'
    const idx = Math.min(completedCount.value, imageItems.value.length - 1)
    return imageItems.value[idx]?.filename || '-'
})

const currentPatientResult = computed(() => {
    return patientResults.value[selectedPatientIndex.value] || null
})

// 解析文件名
function parseFilename(filename: string): ParsedInfo | null {
    // 格式：P患者ID-姓名-性别-年龄-临床发现-图片ID.扩展名
    // 示例：P20260315001-张伟-male-45-Cough-001.png
    const nameWithoutExt = filename.replace(/\.[^/.]+$/, '')
    const parts = nameWithoutExt.split('-')

    if (parts.length >= 6 && parts[0].startsWith('P')) {
        return {
            patientId: parts[0], // P20260315001
            name: parts[1], // 张伟
            gender: parts[2], // male/female
            age: parseInt(parts[3]) || 0, // 45
            clinical: parts[4], // Cough
            imageId: parts[5], // 001
            symptom: getClinicalDisplay(parts[4])
        }
    }
    return null
}

// 获取临床信息显示
function getClinicalDisplay(clinical: string): string {
    const map: Record<string, string> = {
        'Cough': '咳嗽',
        'ChestPain': '胸痛',
        'Dyspnea': '呼吸困难',
        'Fever': '发热',
        'Wheeze': '喘息',
        'Fatigue': '乏力',
        'Routine': '体检',
        'FollowUp': '复查'
    }
    return map[clinical] || clinical
}

// 获取头像颜色
function getAvatarColor(name: string): string {
    const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#8B5CF6', '#EC4899']
    let hash = 0
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash)
    }
    return colors[Math.abs(hash) % colors.length]
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 文件上传处理
async function onFileChange(file: UploadFile, files: UploadFile[]) {
    const newFile = file.raw
    if (!newFile) return

    // 生成缩略图
    const thumbnail = await createThumbnail(newFile)

    // 解析文件名
    const parsed = parseFilename(file.name)

    const item: ImageItem = {
        file: newFile,
        filename: file.name,
        fileSize: formatFileSize(newFile.size),
        thumbnail,
        parsed,
        selectedPatient: null  // ✅ 初始化为 null
    }

    imageItems.value.push(item)
}

// 创建缩略图
function createThumbnail(file: File): Promise<string> {
    return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => {
            resolve(e.target?.result as string)
        }
        reader.readAsDataURL(file)
    })
}

// 删除图片
function removeImage(index: number) {
    imageItems.value.splice(index, 1)
}

// 清空所有
function handleClearAll() {
    ElMessageBox.confirm('确定要清空所有影像吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        imageItems.value = []
        patientResults.value = []
        ElMessage.success('已清空')
    }).catch(() => { })
}

// 继续添加
function handleAddMore() {
    // 通过 DOM 操作触发文件选择
    const input = uploadRef.value?.$el?.querySelector('input[type="file"]')
    if (input) {
        input.click()
    } else {
        console.error('[继续添加] 无法找到文件输入框')
    }
}

// 选择患者
function selectPatient(index: number) {
    selectedPatientIndex.value = index
}

// 上一个患者
function prevPatient() {
    if (selectedPatientIndex.value > 0) {
        selectedPatientIndex.value--
    }
}

// 下一个患者
function nextPatient() {
    if (selectedPatientIndex.value < patientResults.value.length - 1) {
        selectedPatientIndex.value++
    }
}

// 患者选择变更
function onPatientSelect(index: number) {
    selectedPatientIndex.value = index
}

// 停止诊断
async function handleStopDiagnosis() {
    try {
        await ElMessageBox.confirm(
            '确定要终止当前诊断任务吗？已完成的诊断结果将保留。',
            '终止确认',
            { type: 'warning' }
        )

        diagnosisAborted.value = true
        diagnosing.value = false

        // 保存当前状态到 localStorage
        saveDiagnosisState()

        ElMessage.warning('已终止检测')
    } catch {
        // 用户取消
    }
}

// 清空数据
function handleClearData() {
    // 清空所有状态
    imageItems.value = []
    patientResults.value = []
    selectedPatientIndex.value = 0
    completedCount.value = 0
    diagnosing.value = false
    diagnosisAborted.value = false
    diagnosisTask = null

    // 清除 localStorage
    localStorage.removeItem('batchDiagnosisState')

    ElMessage.success('已清空数据')
}

// 保存诊断状态到 localStorage
function saveDiagnosisState() {
    // 构建可序列化的影像列表（排除 File 对象）
    const serializableImageItems = imageItems.value.map(item => ({
        filename: item.filename,
        fileSize: item.fileSize,
        thumbnail: item.thumbnail,
        parsed: item.parsed,
        selectedPatient: item.selectedPatient ? {
            id: item.selectedPatient.id,
            patient_no: item.selectedPatient.patient_no,
            name: item.selectedPatient.name,
            gender: item.selectedPatient.gender,
            age: item.selectedPatient.age,
            phone: item.selectedPatient.phone,
            address: item.selectedPatient.address
        } : null
    }))

    // 只保存必要的字段，避免序列化问题
    const state = {
        diagnosing: diagnosing.value,
        diagnosisAborted: diagnosisAborted.value,
        completedCount: completedCount.value,
        selectedPatientIndex: selectedPatientIndex.value,
        imageItems: serializableImageItems, // ✅ 保存影像元数据
        patientResults: patientResults.value.map(p => ({
            name: p.name,
            patient_no: p.patient_no,
            status: p.status,
            result: p.result,
            confidence: p.confidence,
            probabilities: p.probabilities,
            imageUrl: p.imageUrl,
            heatmapUrl: p.heatmapUrl,
            reportContent: p.reportContent,
            diagnosis_id: p.diagnosis_id,
            reportId: p.reportId,
            clinical_info: p.clinical_info,
            patient: p.patient ? {
                id: p.patient.id,
                patient_no: p.patient.patient_no,
                name: p.patient.name,
                gender: p.patient.gender,
                age: p.patient.age,
                phone: p.patient.phone,
                address: p.patient.address
            } : null
        })),
        timestamp: Date.now()
    }

    try {
        localStorage.setItem('batchDiagnosisState', JSON.stringify(state))
    } catch (err) {
        console.error('保存诊断状态失败:', err)
    }
}

// 从 localStorage 恢复诊断状态
function restoreDiagnosisState() {
    try {
        const savedState = localStorage.getItem('batchDiagnosisState')
        if (!savedState) {
            return false
        }

        const state = JSON.parse(savedState)

        // 检查状态是否过期（超过24小时）
        if (Date.now() - state.timestamp > 24 * 60 * 60 * 1000) {
            localStorage.removeItem('batchDiagnosisState')
            return false
        }

        // ✅ 恢复影像列表（不包含 File 对象）
        if (state.imageItems && state.imageItems.length > 0) {
            // 恢复影像元数据，但标记为需要重新上传文件
            imageItems.value = state.imageItems.map((item: any) => ({
                file: null as any, // ⚠️ File 对象无法恢复，设为 null
                filename: item.filename,
                fileSize: item.fileSize,
                thumbnail: item.thumbnail,
                parsed: item.parsed,
                selectedPatient: item.selectedPatient
            }))

            // 如果有未关联文件的影像，提示用户
            const missingFiles = imageItems.value.filter(item => !item.file).length
            if (missingFiles > 0) {
                console.warn(`[批量诊断] ${missingFiles} 个影像文件丢失（File对象无法持久化），但诊断结果已保留`)
            }
        }

        // ✅ 恢复状态逻辑
        // 如果保存时诊断正在进行中，恢复后也标记为诊断中（显示进度条）
        if (state.diagnosing) {
            diagnosing.value = true
            diagnosisAborted.value = false
        } else {
            // 诊断已完成或已终止
            diagnosing.value = false
            diagnosisAborted.value = state.diagnosisAborted || true
        }

        completedCount.value = state.completedCount || 0
        selectedPatientIndex.value = state.selectedPatientIndex || 0

        // 恢复患者结果
        if (state.patientResults && state.patientResults.length > 0) {
            patientResults.value = state.patientResults.map((p: any) => {
                let restoredStatus = p.status

                // ✅ 关键修复：根据是否有诊断结果和原状态来恢复
                if (p.result && p.result !== '-' && p.result.length > 0) {
                    // 有诊断结果，标记为 completed
                    restoredStatus = 'completed'
                } else if (p.status === 'processing') {
                    // 正在诊断中被中断，标记为 error
                    restoredStatus = 'error'
                } else if (p.status === 'waiting') {
                    // 还未开始诊断，保持 waiting 状态，等待用户重新点击开始
                    restoredStatus = 'waiting'
                }
                // 其他状态（completed/error）保持原样

                return {
                    ...p,
                    status: restoredStatus,
                    imageItems: [], // 重新初始化
                    patient: p.patient,
                    generatingReport: false // 默认值
                }
            })

            // ✅ 关键修复：刷新页面后，诊断任务已停止，必须设置 diagnosing=false
            // 无论之前是否是 diagnosing 状态，因为页面刷新后 JS 执行环境已重置
            diagnosing.value = false
            diagnosisAborted.value = true

            return true
        }

        // 如果只有影像列表但没有诊断结果，也返回 true 以保留影像列表
        if (imageItems.value.length > 0 && (!state.patientResults || state.patientResults.length === 0)) {
            return true
        }

        return false
    } catch (err) {
        console.error('恢复诊断状态失败:', err)
        return false
    }
}

// 打印报告
function handlePrint(result: any) {
    if (result.diagnosis_id) {
        router.push({ name: 'ReportPrint', params: { id: result.diagnosis_id } })
    }
}

// 获取概率颜色
function getProbColor(code: string): string {
    const colors: Record<string, string> = {
        'Atelectasis': '#F59E0B',
        'Cardiomegaly': '#EF4444',
        'Effusion': '#3B82F6',
        'Infiltration': '#8B5CF6',
        'Mass': '#EC4899',
        'Nodule': '#6366F1',
        'Pneumonia': '#F97316',
        'Pneumothorax': '#EF4444',
        'Consolidation': '#F59E0B',
        'Edema': '#06B6D4',
        'Emphysema': '#14B8A6',
        'Fibrosis': '#8B5CF6',
        'Pleural_Thickening': '#64748B',
        'Hernia': '#A855F7',
        'No Finding': '#22C55E'
    }
    return colors[code] || '#60A5FA'
}

// ✅ 格式化报告内容，移除 Markdown 符号
function formatReportContent(content: string): string {
    if (!content) return ''

    return content
        // 移除 ## 标题符号
        .replace(/^##\s+/gm, '')
        // 移除 # 标题符号
        .replace(/^#\s+/gm, '')
        // 移除 ** 粗体符号
        .replace(/\*\*/g, '')
        // 移除 * 斜体符号
        .replace(/\*/g, '')
        // 移除 - 列表符号（保留换行）
        .replace(/^-\s+/gm, '')
        // 移除数字列表符号（如 1. 2. 3.）
        .replace(/^\d+\.\s+/gm, '')
        // 清理多余空行
        .replace(/\n{3,}/g, '\n\n')
        .trim()
}

// ✅ 将报告内容转换为 HTML 格式（带样式）
function formatReportToHtml(content: string): string {
    if (!content) return ''

    // 按 ## 标题分割
    const sections = content.split(/##\s*/)

    return sections
        .filter(section => section.trim())
        .map(section => {
            section = section.trim()
            if (!section) return ''

            // 提取标题（第一行）
            const lines = section.split('\n')
            const title = lines[0].trim()
            const body = lines.slice(1).join('\n').trim()

            // 判断标题类型
            let titleClass = 'report-section-title'
            let icon = ''

            if (title.includes('检查发现') || title.includes('影像学表现')) {
                icon = '🔍'
            } else if (title.includes('诊断印象') || title.includes('诊断结论')) {
                icon = '📋'
                titleClass = 'report-section-title diagnosis'
            } else if (title.includes('建议')) {
                icon = '💡'
                titleClass = 'report-section-title suggestion'
            }

            // 处理正文内容，高亮重要关键词
            let highlightedBody = escapeHtml(body)
                // 高亮疾病名称（如：肺不张、心脏肥大等）
                .replace(/(肺不张|心脏肥大|胸腔积液|肺浸润|实变|水肿|结节|肿块|气胸|肺炎|肺气肿|纤维化)/g, '<strong class="highlight-disease">$1</strong>')
                // 高亮CT建议
                .replace(/(CT|高分辨率CT|HRCT)/g, '<strong class="highlight-ct">$1</strong>')
                // 高亮重要医学术语
                .replace(/(支气管|纵隔|胸膜|肺门|膈肌)/g, '<strong class="highlight-term">$1</strong>')
                // 保留换行
                .replace(/\n/g, '<br>')

            return `
                <div class="report-section">
                    <div class="${titleClass}">
                        <span class="title-icon">${icon}</span>
                        <span class="title-text">${escapeHtml(title.replace(/[:：]$/, ''))}</span>
                    </div>
                    <div class="report-section-body">${highlightedBody}</div>
                </div>
            `
        })
        .join('')
}

// 开始诊断
// ✅ 打开患者选择对话框
async function openPatientSelectDialog(imageIndex: number) {
    currentEditImageIndex.value = imageIndex
    patientSearchKeyword.value = ''
    tempSelectedPatient.value = null

    try {
        // 获取所有患者
        const res: any = await getPatientsApi({ page: 1, per_page: 100 })
        availablePatients.value = res.data?.items || []
        patientSelectDialogVisible.value = true
    } catch (err) {
        console.error('获取患者列表失败:', err)
        ElMessage.error('获取患者列表失败')
    }
}

// ✅ 确认选择患者
function confirmSelectPatient() {
    if (!tempSelectedPatient.value || currentEditImageIndex.value < 0) return

    imageItems.value[currentEditImageIndex.value].selectedPatient = tempSelectedPatient.value
    patientSelectDialogVisible.value = false
    ElMessage.success(`已选择患者：${tempSelectedPatient.value.name}`)
}

// ✅ 打开创建患者对话框
function openCreatePatientDialog(imageIndex: number) {
    currentEditImageIndex.value = imageIndex
    newPatientForm.value = {
        patient_no: '',
        name: '',
        gender: 'male',
        age: 30,
        phone: '',
        address: ''
    }
    patientCreateDialogVisible.value = true
}

// ✅ 确认创建患者
async function confirmCreatePatient() {
    const form = newPatientForm.value

    // 验证必填字段
    if (!form.patient_no || !form.name) {
        ElMessage.error('请填写患者编号和姓名')
        return
    }

    try {
        const res: any = await createPatientApi(form)
        const newPatient = res.data

        // 关联到当前影像
        if (currentEditImageIndex.value >= 0) {
            imageItems.value[currentEditImageIndex.value].selectedPatient = newPatient
        }

        patientCreateDialogVisible.value = false
        ElMessage.success(`患者创建成功：${newPatient.name}`)
    } catch (err: any) {
        console.error('创建患者失败:', err)
        ElMessage.error(err.response?.data?.message || '创建患者失败')
    }
}

async function handleStartDiagnosis() {
    if (imageItems.value.length === 0) return

    // ✅ 检查是否有丢失的文件
    const missingFiles = imageItems.value.filter(item => !item.file)
    if (missingFiles.length > 0) {
        ElMessage.error(`有 ${missingFiles.length} 个影像文件已丢失，请重新上传`)
        return
    }

    // ✅ 检查是否有未关联患者的影像（仅检查有文件的影像）
    const unassignedImages = imageItems.value.filter(item => item.file && !item.parsed && !item.selectedPatient)
    if (unassignedImages.length > 0) {
        ElMessage.error(`有 ${unassignedImages.length} 个影像未关联患者，无法开始检测！请先选择或创建患者`)
        return
    }

    diagnosing.value = true
    diagnosisAborted.value = false
    completedCount.value = 0
    patientResults.value = []

    // ✅ 创建 AbortController 用于中断请求
    abortController = new AbortController()

    try {
        // 按患者分组（支持解析的和手动选择的）
        const patientMap = new Map<string | number, {
            info: ParsedInfo | null,
            patient: any | null,
            files: ImageItem[]
        }>()

        for (const item of imageItems.value) {
            // ✅ 优先使用手动选择的患者
            if (item.selectedPatient) {
                const key = item.selectedPatient.id
                if (!patientMap.has(key)) {
                    patientMap.set(key, {
                        info: null,
                        patient: item.selectedPatient,
                        files: []
                    })
                }
                patientMap.get(key)!.files.push(item)
            }
            // ✅ 其次使用解析的患者信息
            else if (item.parsed) {
                const key = item.parsed.patientId
                if (!patientMap.has(key)) {
                    patientMap.set(key, {
                        info: item.parsed,
                        patient: null,
                        files: []
                    })
                }
                patientMap.get(key)!.files.push(item)
            }
        }

        // 先为所有患者创建占位记录（显示在列表中）
        for (const [patientId, group] of patientMap) {
            patientResults.value.push({
                name: group.patient?.name || group.info?.name || '未知',
                patient_no: group.patient?.patient_no || patientId,
                patient: group.patient, // ✅ 如果有手动选择的患者，直接使用
                status: 'waiting', // waiting -> processing -> completed
                result: '-',
                confidence: '-',
                probabilities: [],
                imageUrl: '',
                heatmapUrl: '',
                reportContent: '',
                generatingReport: false,
                diagnosis_id: null,
                clinical_info: group.info ? getClinicalDisplay(group.info.clinical) : '',
                imageItems: group.files // 保存该患者的所有影像
            })
        }

        // 保存初始状态
        saveDiagnosisState()

        // 然后逐个诊断
        for (let i = 0; i < patientMap.size; i++) {
            // 检查是否被终止
            if (diagnosisAborted.value) {
                ElMessage.warning('诊断已被终止')
                break
            }

            const [patientId, group] = Array.from(patientMap.entries())[i]
            const resultIndex = i

            try {
                // ✅ 如果已经有手动选择的患者，直接使用
                let patient = group.patient

                if (!patient) {
                    // 尝试查找已有患者
                    const patientsRes: any = await getPatientsApi({ patient_no: patientId })
                    patient = patientsRes.data?.items?.[0]

                    // 如果没有，创建新患者
                    if (!patient && group.info) {

                        const createRes: any = await createPatientApi({
                            patient_no: patientId,
                            name: group.info.name,
                            gender: group.info.gender,
                            age: group.info.age,
                            phone: '',
                            address: ''
                        })
                        patient = createRes.data
                    }
                }

                // 更新患者信息
                patientResults.value[resultIndex].patient = patient
                patientResults.value[resultIndex].status = 'processing'

                // ✅ 同时启动两个加载动画：影像分析 + AI报告
                patientResults.value[resultIndex].generatingReport = true
                patientResults.value[resultIndex].reportContent = ''

                // 保存状态
                saveDiagnosisState()

                // 确保UI立即更新
                await nextTick()

                // 对每个影像进行诊断
                let lastAiReport = null // ✅ 保存最后一个影像的AI报告数据
                for (const imgItem of group.files) {
                    // 检查是否被终止
                    if (diagnosisAborted.value) {
                        break
                    }

                    try {
                        const formData = new FormData()
                        formData.append('image', imgItem.file)
                        formData.append('patient_id', String(patient.id))
                        if (group.info?.symptom) {
                            formData.append('symptoms', group.info.symptom)
                        }
                        formData.append('skip_report', 'false')

                        // ✅ 传递 abortController.signal 以支持中断
                        const res: any = await diagnoseSingleApi(
                            formData,
                            abortController?.signal
                        )
                        const data = res.data

                        // ✅ 保存最后一个影像的AI报告数据
                        if (data.ai_report) {
                            lastAiReport = data.ai_report
                        }

                        const topProb = data.probabilities?.[0]
                        const resultText = topProb?.probability < 0.3 ? '正常' : (topProb?.disease_name_zh || '异常')
                        const confidence = topProb ? (topProb.probability * 100).toFixed(1) : '0'

                        // 更新当前患者的结果（不改变status，保持processing）
                        const currentResult = patientResults.value[resultIndex].result

                        // ✅ 先显示影像分析结果
                        patientResults.value[resultIndex] = {
                            ...patientResults.value[resultIndex],
                            // 累积多个影像的结果
                            result: currentResult ? `${currentResult} | ${resultText}` : resultText,
                            confidence: confidence,
                            probabilities: data.probabilities || [],
                            imageUrl: data.image_url || '',
                            heatmapUrl: data.heatmap_url || '',
                            diagnosis_id: data.diagnosis_id,
                            reportId: data.report_id
                        }

                        completedCount.value++

                        // 每完成一个影像，保存状态
                        saveDiagnosisState()

                        // 确保UI立即更新
                        await nextTick()
                    } catch (err: any) {
                        // ✅ 检查是否是中断错误
                        if (err.name === 'AbortError' || err.message?.includes('abort')) {
                            console.log('[批量诊断] 请求被中断')
                            patientResults.value[resultIndex].status = 'error'
                            completedCount.value++
                            saveDiagnosisState()
                            await nextTick()
                            break // 跳出影像循环
                        }

                        console.error('诊断失败:', err)
                        patientResults.value[resultIndex].status = 'error'
                        completedCount.value++
                        saveDiagnosisState()
                        await nextTick() // 确保UI立即更新
                    }

                    await new Promise(resolve => setTimeout(resolve, 100))
                }

                // 检查是否被终止
                if (diagnosisAborted.value) {
                    break
                }

                // 一个患者的所有影像诊断完成，标记为 completed
                patientResults.value[resultIndex].status = 'completed'
                saveDiagnosisState()
                await nextTick()

                // ✅ 模拟AI报告异步生成（2-3秒延迟）
                setTimeout(async () => {
                    let reportContent = ''
                    if (lastAiReport) {
                        reportContent = `## 检查发现\n${lastAiReport.findings || '无异常发现'}\n\n## 诊断印象\n${lastAiReport.impression || '未见明显异常'}\n\n## 建议\n${lastAiReport.recommendations || '建议定期复查'}`
                    }

                    patientResults.value[resultIndex] = {
                        ...patientResults.value[resultIndex],
                        reportContent: reportContent,
                        generatingReport: false // ✅ 报告生成完成
                    }

                    saveDiagnosisState()
                    await nextTick()
                }, 2000 + Math.random() * 1000) // 2-3秒随机延迟
            } catch (err) {
                console.error('患者处理失败:', err)
            }
        }

        if (!diagnosisAborted.value) {
            ElMessage.success(`批量诊断完成！`)

            // 诊断完成后，更新状态但不刷新页面
            diagnosing.value = false
            diagnosisAborted.value = true
            saveDiagnosisState()
            await nextTick() // 确保UI更新
        }
    } catch (err) {
        ElMessage.error('批量诊断失败')
    } finally {
        diagnosing.value = false
        diagnosisAborted.value = true

        // ✅ 清理 AbortController
        if (abortController) {
            abortController = null
        }

        // 最终保存状态（保持患者的原始状态，不要强制改为completed）
        saveDiagnosisState()
    }
}

// 页面加载时恢复状态
onMounted(async () => {
    const hasRestored = restoreDiagnosisState()

    if (hasRestored) {
        // 成功恢复状态，强制刷新UI
        await nextTick()

        if (diagnosing.value) {
            // 诊断进行中被中断，提示用户重新点击开始
            ElMessage.warning({
                message: `⚠️ 诊断任务被中断，已恢复 ${completedCount.value}/${imageItems.value.length} 进度，请重新点击“开始检测”继续`,
                duration: 6000,
                showClose: true
            })
        } else if (patientResults.value.length > 0) {
            // 有诊断结果
            ElMessage.success(`✅ 已恢复 ${completedCount.value} 个患者的诊断结果`)

            // 检查是否有缺失的文件
            const missingFiles = imageItems.value.filter(item => !item.file).length
            if (missingFiles > 0) {
                ElMessage.info({
                    message: `ℹ️ 原始影像文件需要重新上传（浏览器安全限制），但诊断结果已保留`,
                    duration: 5000,
                    showClose: true
                })
            }
        } else if (imageItems.value.length > 0) {
            // 只有影像列表，未开始诊断
            ElMessage.info(`已恢复 ${imageItems.value.length} 个影像，请重新上传文件后开始诊断`)
        }
    } else {
        // 无状态可恢复
    }
})

// ✅ 路由守卫 - 防止诊断中切换页面导致数据丢失
import { onBeforeRouteLeave } from 'vue-router'

onBeforeRouteLeave((to, from, next) => {
    if (diagnosing.value && !diagnosisAborted.value) {
        ElMessageBox.confirm(
            '诊断任务正在进行中，离开页面将中断诊断。是否继续？',
            '警告',
            {
                confirmButtonText: '继续离开',
                cancelButtonText: '取消',
                type: 'warning'
            }
        ).then(() => {
            // 用户确认离开，中断诊断
            diagnosisAborted.value = true
            if (abortController) {
                (abortController as AbortController).abort()
            }
            saveDiagnosisState()
            next()
        }).catch(() => {
            // 用户取消离开
            next(false)
        })
    } else {
        next()
    }
})

// 页面卸载时保存状态
onUnmounted(() => {
    // ✅ 如果诊断正在进行，中断所有请求
    if (diagnosing.value && !diagnosisAborted.value) {
        diagnosisAborted.value = true
        if (abortController) {
            (abortController as AbortController).abort()
        }
    }

    // 保存状态
    if (diagnosing.value || patientResults.value.length > 0) {
        saveDiagnosisState()
    }
})
</script>

<style scoped lang="scss">
.batch-diagnose-page {
    height: calc(100vh - 120px);
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: var(--bg-primary);
    overflow: hidden;

    .top-bar {
        padding: 16px 24px;
        background: var(--card-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-xl);

        .steps-indicator {
            display: flex;
            align-items: center;
            gap: 0;

            .step-item {
                display: flex;
                align-items: center;
                gap: 12px;

                .step-num {
                    width: 32px;
                    height: 32px;
                    border-radius: 8px;
                    background: var(--bg-tertiary);
                    border: 2px solid var(--glass-border);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    font-weight: 700;
                    color: var(--text-muted);
                    transition: all 0.3s ease;
                }

                .step-text {
                    .step-title {
                        font-size: 14px;
                        font-weight: 600;
                        color: var(--text-muted);
                        transition: color 0.3s ease;
                    }

                    .step-desc {
                        font-size: 12px;
                        color: var(--text-muted);
                        opacity: 0.6;
                    }
                }

                &.active {
                    .step-num {
                        background: rgba(34, 211, 238, 0.15);
                        border-color: var(--primary);
                        color: var(--primary);
                    }

                    .step-title {
                        color: var(--text-primary);
                    }

                    .step-desc {
                        opacity: 1;
                    }
                }

                &.done {
                    .step-num {
                        background: var(--primary);
                        border-color: var(--primary);
                        color: #fff;
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
                margin: 0 12px;
                transition: background 0.3s ease;

                &.active {
                    background: var(--primary);
                }
            }
        }
    }

    .main-content {
        flex: 1;
        overflow-y: auto;
        // padding: 0 16px 16px;

        .upload-container,
        .images-container {
            // max-width: 1400px;
            margin: 0 auto;
        }


        .upload-card,
        .images-card {
            background: var(--card-bg);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-xl);
            overflow: hidden;

            .card-header {
                padding: 16px 20px;
                border-bottom: 1px solid var(--glass-border);
                display: flex;
                justify-content: space-between;
                align-items: center;

                .header-left {
                    display: flex;
                    align-items: center;
                    gap: 12px;

                    .upload-icon {
                        width: 40px;
                        height: 40px;
                        border-radius: 10px;
                        background: rgba(34, 211, 238, 0.1);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: var(--primary);
                    }

                    .header-text {
                        .header-title {
                            font-size: 16px;
                            font-weight: 600;
                            color: var(--text-primary);
                        }

                        .header-subtitle {
                            font-size: 12px;
                            color: var(--text-muted);
                            margin-top: 2px;
                        }
                    }
                }
            }

            .card-body {
                padding: 20px;

                .upload-placeholder {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 60px 40px;
                    text-align: center;

                    .upload-main-text {
                        font-size: 15px;
                        color: var(--text-secondary);
                        margin: 16px 0 8px;
                        font-weight: 500;
                    }

                    .upload-sub-text {
                        font-size: 13px;
                        color: var(--text-muted);

                        .highlight {
                            color: var(--primary);
                            font-weight: 600;
                        }
                    }

                    .upload-format-hint {
                        margin-top: 16px;
                        font-size: 12px;
                        color: var(--text-muted);

                        .format-code {
                            color: var(--primary);
                            font-family: monospace;
                            background: rgba(34, 211, 238, 0.1);
                            padding: 2px 8px;
                            border-radius: 4px;
                        }
                    }
                }

                .images-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 16px;

                    .image-item {
                        background: var(--bg-secondary);
                        border: 1px solid var(--glass-border);
                        border-radius: var(--radius-lg);
                        overflow: hidden;
                        transition: all 0.3s ease;

                        &:hover {
                            border-color: var(--primary);
                            box-shadow: 0 4px 12px rgba(34, 211, 238, 0.1);
                        }

                        .image-thumbnail {
                            position: relative;
                            height: 180px;
                            background: var(--bg-tertiary);
                            overflow: hidden;

                            .thumb-img {
                                width: 100%;
                                height: 100%;
                            }

                            .image-overlay {
                                position: absolute;
                                top: 8px;
                                right: 8px;
                                opacity: 0;
                                transition: opacity 0.3s ease;
                            }

                            &:hover .image-overlay {
                                opacity: 1;
                            }
                        }

                        .image-info {
                            padding: 12px;

                            .image-filename {
                                font-size: 13px;
                                font-weight: 600;
                                color: var(--text-primary);
                                margin-bottom: 4px;
                                overflow: hidden;
                                text-overflow: ellipsis;
                                white-space: nowrap;
                            }

                            .image-size {
                                font-size: 11px;
                                color: var(--text-muted);
                                margin-bottom: 8px;
                            }

                            .patient-badge {
                                display: flex;
                                align-items: center;
                                gap: 8px;
                                margin-bottom: 8px;

                                .patient-details {
                                    flex: 1;
                                    min-width: 0;

                                    .patient-name-row {
                                        display: flex;
                                        align-items: center;
                                        gap: 8px;

                                        .name {
                                            font-size: 13px;
                                            font-weight: 600;
                                            color: var(--text-primary);
                                        }

                                        .gender-age {
                                            font-size: 12px;
                                            color: var(--text-muted);
                                        }
                                    }

                                    .patient-id {
                                        font-size: 11px;
                                        color: var(--text-muted);
                                        margin-top: 2px;
                                    }
                                }
                            }

                            .clinical-info {
                                display: flex;
                                align-items: center;
                                gap: 8px;
                                margin-bottom: 8px;

                                .image-index {
                                    font-size: 11px;
                                    color: var(--text-muted);
                                }
                            }

                            .match-status {
                                display: flex;
                                align-items: center;
                                gap: 6px;
                                font-size: 12px;
                                color: var(--primary);
                                margin-bottom: 8px;
                            }

                            .symptom-input {
                                :deep(.el-input__wrapper) {
                                    background: var(--bg-tertiary);
                                    border-color: var(--glass-border);
                                }
                            }
                        }
                    }
                }
            }

            .card-footer {
                padding: 16px 20px;
                border-top: 1px solid var(--glass-border);
                display: flex;
                justify-content: center;
                gap: 12px;
            }
        }

        // 诊断阶段样式
        .phase-diagnosis {
            display: flex;
            flex-direction: column;
            gap: 16px;
            height: 100%;

            .diagnosis-header {
                padding: 12px 20px;
                background: var(--card-bg);
                border: 1px solid var(--glass-border);
                border-radius: var(--radius-xl);
                display: flex;
                justify-content: center;

                .current-file-info {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    padding: 8px 16px;
                    background: var(--bg-tertiary);
                    border-radius: var(--radius-md);

                    .file-name {
                        font-size: 13px;
                        color: var(--text-primary);
                        font-weight: 500;
                    }

                    .progress-text {
                        font-size: 12px;
                        color: var(--primary);
                        font-weight: 600;
                    }
                }
            }

            .three-columns {
                display: grid;
                grid-template-columns: 280px 420px 1fr;
                gap: 16px;
                flex: 1;
                overflow: hidden;

                // 左侧面板
                .left-panel {
                    background: var(--card-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-xl);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;

                    .panel-header {
                        padding: 16px;
                        border-bottom: 1px solid var(--glass-border);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;

                        .panel-title {
                            font-size: 14px;
                            font-weight: 600;
                            color: var(--text-primary);
                        }

                        .panel-badge {
                            font-size: 12px;
                            color: var(--text-muted);
                            background: var(--bg-tertiary);
                            padding: 2px 8px;
                            border-radius: 12px;
                        }
                    }

                    .panel-body {
                        flex: 1;
                        overflow-y: auto;
                        padding: 12px;

                        .patient-item {
                            display: flex;
                            align-items: center;
                            gap: 12px;
                            padding: 12px;
                            background: var(--bg-tertiary);
                            border: 1px solid var(--glass-border);
                            border-radius: var(--radius-lg);
                            cursor: pointer;
                            transition: all 0.3s ease;
                            margin-bottom: 8px;

                            &:hover {
                                border-color: var(--primary);
                                background: var(--bg-secondary);
                            }

                            &.active {
                                border-color: var(--primary);
                                background: rgba(34, 211, 238, 0.08);
                            }

                            .patient-avatar {
                                width: 40px;
                                height: 40px;
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: #fff;
                                font-weight: 700;
                                font-size: 16px;
                                flex-shrink: 0;
                            }

                            .patient-info {
                                flex: 1;
                                min-width: 0;

                                .patient-name {
                                    font-size: 14px;
                                    font-weight: 600;
                                    color: var(--text-primary);
                                    margin-bottom: 4px;

                                    .patient-no {
                                        font-size: 11px;
                                        color: var(--text-muted);
                                        font-weight: 400;
                                    }
                                }

                                .patient-status {
                                    margin-top: 4px;
                                }
                            }
                        }
                    }

                    .panel-footer {
                        padding: 12px;
                        border-top: 1px solid var(--glass-border);
                    }
                }

                // 中间面板
                .center-panel {
                    background: var(--card-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-xl);
                    display: flex;
                    flex-direction: column;
                    overflow-y: auto;
                    padding: 16px;
                    gap: 16px;

                    .result-header {
                        .result-badge {
                            display: flex;
                            align-items: center;
                            gap: 12px;
                            padding: 16px;
                            border-radius: var(--radius-lg);
                            border: 2px solid;

                            &.normal {
                                background: rgba(34, 211, 238, 0.08);
                                border-color: rgba(34, 211, 238, 0.3);

                                .el-icon {
                                    color: var(--primary);
                                }
                            }

                            &.abnormal {
                                background: rgba(245, 158, 11, 0.08);
                                border-color: rgba(245, 158, 11, 0.3);

                                .el-icon {
                                    color: var(--orange);
                                }
                            }

                            .result-text {
                                .result-title {
                                    font-size: 18px;
                                    font-weight: 700;
                                    color: var(--text-primary);
                                }

                                .result-conf {
                                    font-size: 13px;
                                    color: var(--text-secondary);
                                    margin-top: 2px;
                                }
                            }
                        }
                    }

                    .info-card,
                    .prob-card {
                        background: var(--bg-tertiary);
                        border: 1px solid var(--glass-border);
                        border-radius: var(--radius-lg);
                        padding: 16px;

                        .card-title {
                            font-size: 13px;
                            font-weight: 600;
                            color: var(--text-secondary);
                            margin-bottom: 12px;
                            padding-bottom: 8px;
                            border-bottom: 1px solid var(--glass-border);
                        }
                    }

                    .info-card {
                        .info-grid {
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 12px;

                            .info-row {
                                display: flex;
                                flex-direction: column;
                                gap: 4px;

                                .label {
                                    font-size: 12px;
                                    color: var(--text-muted);
                                }

                                .value {
                                    font-size: 14px;
                                    color: var(--text-primary);
                                    font-weight: 500;
                                }
                            }
                        }
                    }

                    // 等待诊断状态
                    .waiting-state,
                    .processing-state {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100%;
                        gap: 16px;
                        padding: 40px 20px;

                        .loading-spinner {
                            position: relative;
                            width: 80px;
                            height: 80px;

                            .spinner-ring {
                                position: absolute;
                                border-radius: 50%;
                                border: 3px solid transparent;
                                animation: spin 1.5s linear infinite;

                                &:nth-child(1) {
                                    width: 80px;
                                    height: 80px;
                                    border-top-color: var(--primary);
                                }

                                &:nth-child(2) {
                                    width: 60px;
                                    height: 60px;
                                    top: 10px;
                                    left: 10px;
                                    border-top-color: var(--success);
                                    animation-duration: 2s;
                                    animation-direction: reverse;
                                }

                                &:nth-child(3) {
                                    width: 40px;
                                    height: 40px;
                                    top: 20px;
                                    left: 20px;
                                    border-top-color: var(--warning);
                                    animation-duration: 1s;
                                }
                            }

                            .spinner-icon {
                                position: absolute;
                                top: 50%;
                                left: 50%;
                                transform: translate(-50%, -50%);
                                color: var(--primary);

                                .rotating-icon {
                                    animation: rotate-icon 2s ease-in-out infinite;
                                }
                            }
                        }

                        .waiting-text,
                        .processing-text {
                            font-size: 16px;
                            color: var(--text-primary);
                            font-weight: 600;
                            margin: 0;
                        }

                        .waiting-hint,
                        .processing-hint {
                            font-size: 13px;
                            color: var(--text-muted);
                            margin: 0;
                        }
                    }

                    // 错误状态
                    .error-state {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100%;
                        gap: 16px;
                        color: var(--text-muted);

                        p {
                            font-size: 14px;
                            margin: 0;
                        }
                    }

                    // 空状态
                    .empty-center {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100%;
                        gap: 12px;
                        color: var(--text-muted);

                        p {
                            font-size: 14px;
                            margin: 0;
                        }
                    }

                    // 加载动画关键帧
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

                    @keyframes progress-indeterminate {
                        0% {
                            width: 0%;
                            margin-left: 0%;
                        }

                        50% {
                            width: 50%;
                            margin-left: 25%;
                        }

                        100% {
                            width: 0%;
                            margin-left: 100%;
                        }
                    }

                    .prob-card {
                        .prob-list {
                            display: flex;
                            flex-direction: column;
                            gap: 12px;

                            .prob-item {
                                .prob-header {
                                    display: flex;
                                    align-items: center;
                                    gap: 8px;
                                    margin-bottom: 6px;

                                    .prob-dot {
                                        width: 8px;
                                        height: 8px;
                                        border-radius: 50%;
                                        flex-shrink: 0;
                                    }

                                    .prob-label {
                                        flex: 1;
                                        font-size: 13px;
                                        color: var(--text-secondary);
                                    }

                                    .prob-value {
                                        font-size: 13px;
                                        color: var(--text-primary);
                                        font-weight: 600;
                                    }
                                }

                                .prob-bar {
                                    height: 6px;
                                    background: var(--bg-primary);
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
                    }

                    .image-cards {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 12px;

                        .image-card {
                            background: var(--bg-tertiary);
                            border: 1px solid var(--glass-border);
                            border-radius: var(--radius-lg);
                            overflow: hidden;

                            .image-label {
                                padding: 8px 12px;
                                font-size: 12px;
                                font-weight: 600;
                                color: var(--text-secondary);
                                background: var(--bg-secondary);
                                border-bottom: 1px solid var(--glass-border);
                            }

                            .preview-img {
                                width: 100%;
                                height: 160px;
                            }
                        }
                    }

                    .empty-center {
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        gap: 12px;
                        color: var(--text-muted);

                        p {
                            font-size: 14px;
                        }
                    }
                }

                // 右侧面板
                .right-panel {
                    background: var(--card-bg);
                    border: 1px solid var(--glass-border);
                    border-radius: var(--radius-xl);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;

                    .panel-header {
                        padding: 16px;
                        border-bottom: 1px solid var(--glass-border);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;

                        .panel-title {
                            font-size: 14px;
                            font-weight: 600;
                            color: var(--text-primary);
                        }
                    }

                    .panel-body {
                        flex: 1;
                        overflow-y: auto;
                        padding: 16px;

                        .report-loading {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            height: 100%;
                            gap: 16px;
                            padding: 40px 20px;

                            .loading-spinner {
                                position: relative;
                                width: 100px;
                                height: 100px;

                                .spinner-ring {
                                    position: absolute;
                                    border-radius: 50%;
                                    border: 3px solid transparent;
                                    animation: spin 1.5s linear infinite;

                                    &:nth-child(1) {
                                        width: 100px;
                                        height: 100px;
                                        border-top-color: var(--primary);
                                        animation-duration: 1.5s;
                                    }

                                    &:nth-child(2) {
                                        width: 75px;
                                        height: 75px;
                                        top: 12.5px;
                                        left: 12.5px;
                                        border-right-color: var(--purple);
                                        animation-duration: 2s;
                                        animation-direction: reverse;
                                    }

                                    &:nth-child(3) {
                                        width: 50px;
                                        height: 50px;
                                        top: 25px;
                                        left: 25px;
                                        border-bottom-color: var(--success);
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
                                font-size: 18px;
                                font-weight: 600;
                                color: var(--text-primary);
                                margin: 0;
                            }

                            .loading-desc {
                                font-size: 13px;
                                color: var(--text-secondary);
                                margin: 0 0 24px 0;
                                text-align: center;
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

                        // ✅ 报告加载动画
                        .report-loading {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            height: 100%;
                            gap: 20px;
                            padding: 40px 20px;

                            .loading-spinner {
                                position: relative;
                                width: 100px;
                                height: 100px;

                                .spinner-ring {
                                    position: absolute;
                                    border-radius: 50%;
                                    border: 3px solid transparent;
                                    animation: spin 1.5s linear infinite;

                                    &:nth-child(1) {
                                        width: 100px;
                                        height: 100px;
                                        border-top-color: var(--primary);
                                        animation-duration: 1.5s;
                                    }

                                    &:nth-child(2) {
                                        width: 75px;
                                        height: 75px;
                                        top: 12.5px;
                                        left: 12.5px;
                                        border-right-color: var(--purple);
                                        animation-duration: 2s;
                                        animation-direction: reverse;
                                    }

                                    &:nth-child(3) {
                                        width: 50px;
                                        height: 50px;
                                        top: 25px;
                                        left: 25px;
                                        border-bottom-color: var(--success);
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
                                font-size: 18px;
                                font-weight: 600;
                                color: var(--text-primary);
                                margin: 0;
                            }

                            .loading-desc {
                                font-size: 13px;
                                color: var(--text-secondary);
                                margin: 0;
                                text-align: center;
                            }

                            .loading-progress {
                                width: 100%;
                                max-width: 300px;
                                display: flex;
                                flex-direction: column;
                                align-items: center;
                                gap: 8px;

                                .progress-bar {
                                    width: 100%;
                                    height: 4px;
                                    background: var(--bg-tertiary);
                                    border-radius: 2px;
                                    overflow: hidden;

                                    .progress-fill {
                                        height: 100%;
                                        background: linear-gradient(90deg, var(--primary), var(--purple));
                                        border-radius: 2px;
                                        animation: progress-indeterminate 2s ease-in-out infinite;
                                    }
                                }

                                .progress-text {
                                    font-size: 12px;
                                    color: var(--text-muted);
                                }
                            }
                        }

                        // ✅ 等待状态
                        .report-waiting {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            height: 100%;
                            gap: 16px;
                            padding: 40px 20px;

                            p {
                                font-size: 16px;
                                font-weight: 500;
                                color: var(--text-primary);
                                margin: 0;
                            }

                            .hint-text {
                                font-size: 13px;
                                color: var(--text-secondary);
                            }
                        }

                        .report-content {
                            .report-text {
                                font-family: 'Microsoft YaHei', sans-serif;
                                font-size: 13px;
                                line-height: 1.8;
                                color: var(--text-secondary);
                                word-break: break-all;

                                // ✅ 报告区块
                                .report-section {
                                    margin-bottom: 24px;

                                    &:last-child {
                                        margin-bottom: 0;
                                    }
                                }

                                // ✅ 标题样式
                                .report-section-title {
                                    font-size: 20px;
                                    font-weight: 800;
                                    color: var(--text-primary);
                                    margin-bottom: 16px;
                                    padding: 12px 16px;
                                    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%);
                                    border-left: 5px solid var(--primary);
                                    border-radius: 8px;
                                    display: flex;
                                    align-items: center;
                                    gap: 10px;
                                    letter-spacing: 1px;

                                    .title-icon {
                                        font-size: 22px;
                                        flex-shrink: 0;
                                    }

                                    .title-text {
                                        font-size: 20px;
                                        font-weight: 800;
                                        letter-spacing: 1.5px;
                                    }

                                    // 诊断印象标题（橙色）
                                    &.diagnosis {
                                        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
                                        border-left-color: var(--orange);
                                    }

                                    // 建议标题（绿色）
                                    &.suggestion {
                                        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(34, 197, 94, 0.05) 100%);
                                        border-left-color: var(--success);
                                    }
                                }

                                // ✅ 正文样式
                                .report-section-body {
                                    padding: 0 14px;
                                    text-align: justify;

                                    // 高亮疾病名称（红色）
                                    .highlight-disease {
                                        color: #FF4444;
                                        font-weight: 700;
                                        font-size: 14px;
                                        background: rgba(255, 68, 68, 0.15);
                                        padding: 2px 8px;
                                        border-radius: 4px;
                                        border: 1px solid rgba(255, 68, 68, 0.3);
                                    }

                                    // 高亮CT（蓝色）
                                    .highlight-ct {
                                        color: #00AAFF;
                                        font-weight: 700;
                                        font-size: 14px;
                                        background: rgba(0, 170, 255, 0.15);
                                        padding: 2px 8px;
                                        border-radius: 4px;
                                        border: 1px solid rgba(0, 170, 255, 0.3);
                                    }

                                    // 高亮医学术语（紫色）
                                    .highlight-term {
                                        color: #AA55FF;
                                        font-weight: 700;
                                        font-size: 14px;
                                        background: rgba(170, 85, 255, 0.15);
                                        padding: 2px 8px;
                                        border-radius: 4px;
                                        border: 1px solid rgba(170, 85, 255, 0.3);
                                    }
                                }
                            }
                        }

                        .report-waiting {
                            display: flex;
                            flex-direction: column;
                            align-items: center;
                            justify-content: center;
                            height: 100%;
                            gap: 16px;
                            padding: 40px 20px;

                            p {
                                font-size: 16px;
                                font-weight: 500;
                                color: var(--text-primary);
                                margin: 0;
                            }

                            .hint-text {
                                font-size: 13px;
                                color: var(--text-secondary);
                            }

                            .loading-spinner {
                                position: relative;
                                width: 100px;
                                height: 100px;

                                .spinner-ring {
                                    position: absolute;
                                    border-radius: 50%;
                                    border: 3px solid transparent;
                                    animation: spin 1.5s linear infinite;

                                    &:nth-child(1) {
                                        width: 100px;
                                        height: 100px;
                                        border-top-color: var(--primary);
                                        animation-duration: 1.5s;
                                    }

                                    &:nth-child(2) {
                                        width: 75px;
                                        height: 75px;
                                        top: 12.5px;
                                        left: 12.5px;
                                        border-right-color: var(--purple);
                                        animation-duration: 2s;
                                        animation-direction: reverse;
                                    }

                                    &:nth-child(3) {
                                        width: 50px;
                                        height: 50px;
                                        top: 25px;
                                        left: 25px;
                                        border-bottom-color: var(--success);
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

                            .waiting-title {
                                font-size: 18px;
                                font-weight: 600;
                                color: var(--text-primary);
                                margin: 0;
                            }

                            .waiting-desc {
                                font-size: 13px;
                                color: var(--text-secondary);
                                margin: 0 0 24px 0;
                                text-align: center;
                            }

                            .waiting-tips {
                                width: 100%;
                                max-width: 320px;
                                display: flex;
                                flex-direction: column;
                                gap: 12px;

                                .tip-item {
                                    display: flex;
                                    align-items: center;
                                    gap: 8px;
                                    padding: 8px 12px;
                                    background: var(--bg-tertiary);
                                    border: 1px solid var(--glass-border);
                                    border-radius: var(--radius-md);
                                    font-size: 12px;
                                    color: var(--text-secondary);

                                    .el-icon {
                                        color: var(--primary);
                                        flex-shrink: 0;
                                    }

                                    span {
                                        flex: 1;
                                    }
                                }
                            }
                        }

                        // ✅ 内联加载提示（小加载动画，不遮挡）
                        .report-loading-inline {
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            padding: 12px 16px;
                            background: var(--bg-tertiary);
                            border: 1px solid var(--glass-border);
                            border-radius: var(--radius-md);
                            margin-bottom: 16px;

                            .el-icon {
                                color: var(--primary);
                            }

                            span {
                                font-size: 13px;
                                color: var(--text-secondary);
                            }
                        }

                        .report-section {
                            height: 100%;
                            display: flex;
                            flex-direction: column;
                        }
                    }
                }
            }
        }

        // 底部导航
        .bottom-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: var(--card-bg);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-xl);

            .nav-info {
                display: flex;
                align-items: center;
                gap: 16px;

                .nav-text {
                    font-size: 13px;
                    color: var(--text-secondary);
                    font-weight: 500;
                }
            }
        }
    }
}

@media (max-width: 768px) {
    .images-grid {
        grid-template-columns: 1fr !important;
    }
}

// 进度条移动动画
@keyframes progress-move {
    0% {
        margin-left: -30%;
    }

    100% {
        margin-left: 100%;
    }
}

/* ✅ 患者选择区域样式 */
.patient-select {
    margin-top: 8px;
}

.patient-select .el-alert {
    margin-bottom: 8px;
    padding: 6px 8px;
}

/* ✅ 文件丢失提示样式 */
.file-missing-alert {
    margin-top: 8px;
}

.file-missing-alert .el-alert {
    margin-bottom: 8px;
    padding: 6px 8px;
}

.select-actions {
    display: flex;
    gap: 6px;
    margin-bottom: 8px;
}

.select-actions .el-button {
    flex: 1;
    font-size: 11px;
}

.selected-patient-info {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 8px;
    background: var(--el-color-primary-light-9);
    border-radius: 4px;
    font-size: 11px;
    color: var(--el-color-primary);
}

/* ✅ 患者选择对话框样式 */
.patient-option {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    border: 1px solid var(--el-border-color);
    border-radius: 8px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.patient-option:hover {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
}

.patient-option.selected {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
}

.patient-option-info {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
}

.patient-option-details {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.patient-option-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary);
}

.patient-option-meta {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: var(--el-text-color-secondary);
}
</style>
