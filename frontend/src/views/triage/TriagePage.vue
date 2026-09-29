<template>
  <div class="triage-page">
    <div class="triage-layout">
      <!-- 左侧：分诊表单 -->
      <div class="glass-card form-card">
        <div class="card-header">
          <h3 class="card-title">
            <el-icon>
              <Document />
            </el-icon> 症状信息填写
          </h3>
        </div>

        <el-form :model="form" ref="formRef" label-width="90px" size="default">
          <!-- 基本信息 -->
          <div class="form-section">
            <div class="section-title">基本信息</div>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="年龄" prop="age">
                  <el-input-number v-model="form.age" :min="0" :max="150" class="age-input" placeholder="岁" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="性别" prop="gender">
                  <el-radio-group v-model="form.gender">
                    <el-radio value="male">男</el-radio>
                    <el-radio value="female">女</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- 症状选择 -->
          <div class="form-section">
            <div class="section-title">主要症状 <span class="section-hint">（可多选）</span></div>
            <div class="symptom-grid">
              <div v-for="symptom in symptomOptions.filter(s => s.id !== 'other')" :key="symptom.id"
                class="symptom-item" :class="{ active: form.symptoms.includes(symptom.id) }"
                @click="toggleSymptom(symptom.id)">
                <div class="symptom-icon" :style="{ background: symptom.bgColor }">
                  <span>{{ symptom.icon }}</span>
                </div>
                <span class="symptom-name">{{ symptom.label }}</span>
              </div>
              <div v-for="id in otherSymptomIds" :key="id" class="symptom-item"
                :class="{ active: form.symptoms.includes(id) }" @click="toggleSymptom(id)">
                <div class="symptom-icon" style="background: rgba(34, 211, 238, 0.2);">
                  <span>{{ getSymptomDetail(id).name ? getSymptomDetail(id).name.charAt(0) : '➕' }}</span>
                </div>
                <span class="symptom-name">{{ getSymptomDetail(id).name || '其他症状' }}</span>
              </div>
              <div class="symptom-item add-other-btn" @click="addOtherSymptom">
                <div class="symptom-icon" style="background: rgba(34, 211, 238, 0.15);">
                  <span>➕</span>
                </div>
                <span class="symptom-name">其他</span>
              </div>
            </div>
          </div>

          <!-- 症状详情 -->
          <div class="form-section" v-if="form.symptoms.length > 0">
            <div class="section-title">症状详情 <span class="section-hint">（请补充症状具体表现）</span></div>
            <div class="symptom-detail-list">
              <div v-for="symptomId in form.symptoms" :key="symptomId" class="symptom-detail-card">
                <template v-if="getSymptomById(symptomId)">
                  <div class="symptom-detail-header">
                    <span class="symptom-detail-icon">{{ sById(symptomId).icon }}</span>
                    <span class="symptom-detail-title">{{ isOtherSymptom(symptomId) ? (getSymptomDetail(symptomId).name
                      || '其他症状') : sById(symptomId).label }}</span>
                    <span class="symptom-detail-desc">{{ isOtherSymptom(symptomId) ? '自定义症状' :
                      sById(symptomId).description }}</span>
                    <el-button v-if="isOtherSymptom(symptomId)" class="remove-other-btn" size="small"
                      @click="removeOtherSymptom(symptomId)">
                      <el-icon>
                        <Close />
                      </el-icon>
                    </el-button>
                  </div>

                  <div class="symptom-detail-row" v-if="isOtherSymptom(symptomId)">
                    <label class="detail-label">症状名称：</label>
                    <el-input v-model="getSymptomDetail(symptomId).name" placeholder="请输入其他症状名称" maxlength="30"
                      show-word-limit size="small" class="other-detail-input" />
                  </div>

                  <div class="symptom-detail-row">
                    <label class="detail-label">严重程度：</label>
                    <el-radio-group v-model="getSymptomDetail(symptomId).severity" size="small">
                      <el-radio-button value="mild">轻微</el-radio-button>
                      <el-radio-button value="moderate">中度</el-radio-button>
                      <el-radio-button value="severe">严重</el-radio-button>
                    </el-radio-group>
                  </div>

                  <div class="symptom-detail-row"
                    v-if="sById(symptomId).details && sById(symptomId).details.length > 0">
                    <label class="detail-label">具体表现：</label>
                    <div class="detail-checkbox-area">
                      <el-checkbox-group v-model="getSymptomDetail(symptomId).details" size="small">
                        <el-checkbox v-for="detail in sById(symptomId).details" :key="detail" :value="detail">{{ detail
                        }}</el-checkbox>
                        <el-checkbox value="__other__">其他</el-checkbox>
                      </el-checkbox-group>
                      <el-input v-if="getSymptomDetail(symptomId).details.includes('__other__')"
                        v-model="getSymptomDetail(symptomId).detailsOther" placeholder="请输入其他具体表现" size="small"
                        class="other-detail-input" />
                    </div>
                  </div>

                  <div class="symptom-detail-row" v-else>
                    <label class="detail-label">具体表现：</label>
                    <el-input v-model="getSymptomDetail(symptomId).detailsOther" placeholder="请描述该症状的具体表现" size="small"
                      class="other-detail-input" />
                  </div>

                  <div class="symptom-detail-row"
                    v-if="sById(symptomId).triggers && sById(symptomId).triggers.length > 0">
                    <label class="detail-label">触发因素：</label>
                    <div class="detail-checkbox-area">
                      <el-checkbox-group v-model="getSymptomDetail(symptomId).triggers" size="small">
                        <el-checkbox v-for="trigger in sById(symptomId).triggers" :key="trigger" :value="trigger">{{
                          trigger }}</el-checkbox>
                        <el-checkbox value="__other__">其他</el-checkbox>
                      </el-checkbox-group>
                      <el-input v-if="getSymptomDetail(symptomId).triggers.includes('__other__')"
                        v-model="getSymptomDetail(symptomId).triggersOther" placeholder="请输入其他触发因素" size="small"
                        class="other-detail-input" />
                    </div>
                  </div>

                  <div class="symptom-detail-row" v-else>
                    <label class="detail-label">触发因素：</label>
                    <el-input v-model="getSymptomDetail(symptomId).triggersOther" placeholder="请描述该症状的触发因素" size="small"
                      class="other-detail-input" />
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- 持续时间 + 病史 + 按钮 -->
          <div class="form-section-row">
            <!-- 持续时间 -->
            <div class="form-section half">
              <div class="section-title">症状持续时间</div>
              <el-form-item prop="duration">
                <el-radio-group v-model="form.duration" class="duration-group">
                  <el-radio value="数小时" class="duration-item"><span class="duration-label">数小时</span><span
                      class="duration-desc">突发急症</span></el-radio>
                  <el-radio value="1-3天" class="duration-item"><span class="duration-label">1-3天</span><span
                      class="duration-desc">急性发作</span></el-radio>
                  <el-radio value="4-7天" class="duration-item"><span class="duration-label">4-7天</span><span
                      class="duration-desc">持续一周</span></el-radio>
                  <el-radio value="1-2周" class="duration-item"><span class="duration-label">1-2周</span><span
                      class="duration-desc">超过一周</span></el-radio>
                  <el-radio value="2-4周" class="duration-item"><span class="duration-label">2-4周</span><span
                      class="duration-desc">亚急性</span></el-radio>
                  <el-radio value="1-3月" class="duration-item"><span class="duration-label">1-3月</span><span
                      class="duration-desc">慢性早期</span></el-radio>
                  <el-radio value="3月以上" class="duration-item"><span class="duration-label">3月以上</span><span
                      class="duration-desc">长期慢性</span></el-radio>
                  <el-radio value="反复发作" class="duration-item"><span class="duration-label">反复发作</span><span
                      class="duration-desc">间歇性</span></el-radio>
                </el-radio-group>
              </el-form-item>
              <el-input v-model="form.durationDetail" placeholder="补充说明：如每天发作几次、每次持续多久等"
                class="duration-detail-input" />
            </div>

            <!-- 病史 + 按钮 -->
            <div class="form-section half">
              <div class="section-title">既往病史</div>
              <el-form-item prop="medical_history">
                <el-input v-model="form.medical_history" type="textarea" :rows="3" placeholder="请描述既往病史、用药情况、过敏史等"
                  class="history-textarea" />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" size="large" class="submit-btn" @click="handleTriage" :loading="analyzing">
                  <el-icon>
                    <SetUp />
                  </el-icon> 开始智能分诊评估
                </el-button>
              </el-form-item>
            </div>
          </div>
        </el-form>
      </div>

      <!-- 右侧：分诊结果 -->
      <div class="result-area">
        <div class="glass-card empty-card" v-if="!triageResult">
          <div class="empty-state">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14h-2v-4h2v4zm0-8h-2V7h2v2z" />
              </svg>
            </div>
            <h3>等待分诊评估</h3>
            <p>请填写上方症状信息，系统将为您生成智能分诊报告</p>
            <div class="empty-tips">
              <div class="tip-item"><el-icon color="#22D3EE">
                  <SuccessFilled />
                </el-icon><span>AI智能分析症状匹配</span></div>
              <div class="tip-item"><el-icon color="#8B5CF6">
                  <DataAnalysis />
                </el-icon><span>多维度风险评估</span></div>
              <div class="tip-item"><el-icon color="#3B82F6">
                  <Position />
                </el-icon><span>精准就诊建议</span></div>
            </div>
          </div>
        </div>

        <template v-else>
          <div class="result-row">
            <div class="risk-card">
              <div class="risk-header">
                <div>
                  <div class="risk-label">综合风险评分</div>
                  <div class="risk-score-main">
                    <span class="risk-number" :style="{ color: triageResult.riskColor }">{{ triageResult.riskScore
                    }}</span>
                    <span class="risk-total">/ 100</span>
                  </div>
                </div>
                <div class="risk-level-badge" :style="{ background: triageResult.riskBgColor }">{{
                  triageResult.riskLevel }}</div>
              </div>
              <div class="risk-bar">
                <div class="risk-bar-fill"
                  :style="{ width: triageResult.riskScore + '%', background: triageResult.riskColor }"></div>
              </div>
              <div class="risk-desc" :style="{ color: triageResult.riskColor }">{{ triageResult.riskDescription }}</div>
            </div>

            <div class="glass-card result-detail-card disease-card">
              <div class="card-header">
                <h3 class="card-title"><el-icon>
                    <Warning />
                  </el-icon> 可能相关疾病</h3>
              </div>
              <div class="disease-list">
                <div v-for="(disease, index) in triageResult.diseases" :key="index" class="disease-item">
                  <div class="disease-rank" :style="{ background: disease.rankColor }">{{ Number(index) + 1 }}</div>
                  <div class="disease-info">
                    <div class="disease-name">{{ disease.name }}</div>
                    <div class="disease-prob">
                      <div class="prob-bar-mini">
                        <div class="prob-fill-mini"
                          :style="{ width: disease.probability + '%', background: disease.rankColor }"></div>
                      </div>
                      <span class="prob-text" :style="{ color: disease.rankColor }">{{ disease.probability }}%</span>
                    </div>
                    <div class="disease-reason">{{ disease.reason }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="result-row">
            <div class="glass-card result-detail-card advice-card">
              <div class="card-header">
                <h3 class="card-title"><el-icon>
                    <Position />
                  </el-icon> 就诊建议</h3>
              </div>
              <div class="advice-list">
                <div v-for="(advice, index) in triageResult.advice" :key="index" class="advice-item">
                  <div class="advice-icon" :style="{ background: advice.bgColor }"><span>{{ advice.icon }}</span></div>
                  <div class="advice-content">
                    <div class="advice-title" :style="{ color: advice.color }">{{ advice.title }}</div>
                    <div class="advice-desc">{{ advice.desc }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="glass-card result-detail-card notice-card">
              <div class="card-header">
                <h3 class="card-title"><el-icon>
                    <InfoFilled />
                  </el-icon> 注意事项</h3>
              </div>
              <div class="notice-list">
                <div v-for="(notice, index) in triageResult.notices" :key="index" class="notice-item">
                  <span class="notice-icon">{{ Number(index) + 1 }}</span>
                  <span class="notice-text">{{ notice }}</span>
                </div>
              </div>
              <div class="disclaimer-bar">
                <el-icon>
                  <WarningFilled />
                </el-icon>
                <span>本分诊结果仅供参考，不能替代医生的专业诊断。如有紧急情况请立即拨打120急救电话。</span>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue'
import { llmApi } from '@/api/llm'
import { ElMessage } from 'element-plus'
import { Close } from '@element-plus/icons-vue'

const formRef = ref(null)
const analyzing = ref(false)
const triageResult = ref<any>(null)

const form = reactive({
  age: 35,
  gender: 'male',
  symptoms: [] as string[],
  symptomDetails: {} as Record<string, any>,
  duration: '',
  durationDetail: '',
  medical_history: ''
})

const otherSymptomIds = computed(() => form.symptoms.filter(id => id.startsWith('other_')))

const symptomOptions = [
  { id: 'cough', label: '咳嗽', icon: '🤧', bgColor: 'rgba(239, 68, 68, 0.15)', description: '呼吸道受到刺激时的保护性反射动作', details: ['干咳无痰', '咳嗽有痰', '阵发性咳嗽', '持续性咳嗽', '夜间加重'], triggers: ['冷空气刺激', '运动后', '进食后', '说话过多', '无明显诱因'] },
  { id: 'fever', label: '发热', icon: '🌡', bgColor: 'rgba(245, 158, 11, 0.15)', description: '体温升高，可能伴随寒战、出汗', details: ['低热37.3-38°C', '中热38.1-39°C', '高热39.1-41°C', '超高热>41°C', '反复发热'], triggers: ['感染性疾病', '免疫系统反应', '药物反应', '不明原因'] },
  { id: 'chest_pain', label: '胸痛', icon: '💔', bgColor: 'rgba(239, 68, 68, 0.2)', description: '胸部区域疼痛或不适感', details: ['刺痛感', '钝痛/闷痛', '压迫感', '撕裂样痛', '隐痛'], triggers: ['深呼吸时加重', '咳嗽时加重', '体位改变时', '活动后加重', '情绪激动时'] },
  { id: 'dyspnea', label: '呼吸困难', icon: '😮‍💨', bgColor: 'rgba(139, 92, 246, 0.15)', description: '感觉呼吸费力或气不够用', details: ['轻度活动后气促', '静息时呼吸困难', '夜间阵发性呼吸困难', '端坐呼吸', '呼吸急促'], triggers: ['体力活动', '平躺时', '接触过敏原', '情绪紧张', '无明显诱因'] },
  { id: 'sputum', label: '咳痰', icon: '🤮', bgColor: 'rgba(245, 158, 11, 0.2)', description: '咳嗽时咳出痰液', details: ['白色泡沫痰', '黄脓痰', '铁锈色痰', '血丝痰', '大量痰液'], triggers: ['晨起明显', '全天持续', '进食后', '体位改变时'] },
  { id: 'hemoptysis', label: '咯血', icon: '🩸', bgColor: 'rgba(239, 68, 68, 0.25)', description: '咳嗽时咳出血液（需紧急关注）', details: ['痰中带血丝', '少量咯血', '大量咯血', '鲜红色血液', '暗红色血块'], triggers: ['剧烈咳嗽后', '无明显诱因', '外伤后', '服用抗凝药物'] },
  { id: 'night_sweat', label: '夜间盗汗', icon: '💧', bgColor: 'rgba(59, 130, 246, 0.15)', description: '睡眠时出汗，醒来后汗止', details: ['轻微出汗', '明显出汗', '大汗淋漓', '需更换衣物', '伴有发热'], triggers: ['结核感染', '内分泌疾病', '肿瘤性疾病', '药物影响'] },
  { id: 'fatigue', label: '乏力', icon: '😴', bgColor: 'rgba(156, 163, 175, 0.15)', description: '全身无力、精力不足', details: ['轻度疲乏', '中度疲乏', '严重乏力', '持续乏力', '活动后加重'], triggers: ['睡眠不足', '营养缺乏', '慢性疾病', '精神压力大'] },
  { id: 'weight_loss', label: '体重下降', icon: '📉', bgColor: 'rgba(139, 92, 246, 0.2)', description: '非主动减重情况下体重减轻', details: ['轻微下降(<5%)', '明显下降(5-10%)', '严重下降(>10%)', '短期内快速下降', '渐进性下降'], triggers: ['食欲减退', '消化吸收障碍', '代谢异常', '恶性肿瘤消耗'] },
  { id: 'headache', label: '头痛', icon: '🤕', bgColor: 'rgba(245, 158, 11, 0.15)', description: '头部疼痛不适', details: ['胀痛', '跳痛', '针刺样痛', '紧箍感', '偏头痛'], triggers: ['发热伴随', '血压波动', '睡眠不足', '精神紧张', '用眼过度'] },
  { id: 'sore_throat', label: '咽痛', icon: '😷', bgColor: 'rgba(239, 68, 68, 0.15)', description: '咽喉部疼痛或不适', details: ['吞咽疼痛', '持续疼痛', '灼烧感', '干燥感', '声音嘶哑'], triggers: ['上呼吸道感染', '用嗓过度', '空气干燥', '烟酒刺激'] },
  { id: 'muscle_pain', label: '肌肉酸痛', icon: '🦵', bgColor: 'rgba(59, 130, 246, 0.2)', description: '全身或局部肌肉疼痛', details: ['全身酸痛', '四肢酸痛', '背部酸痛', '胸部肌肉痛', '运动后加重'], triggers: ['病毒感染', '剧烈运动', '肌肉劳损', '发热伴随'] },
  { id: 'loss_appetite', label: '食欲不振', icon: '🤢', bgColor: 'rgba(245, 158, 11, 0.2)', description: '不想进食或进食量减少', details: ['轻度减退', '明显减退', '厌食', '恶心感', '早饱感'], triggers: ['消化系统疾病', '全身感染', '精神因素', '药物影响'] },
  { id: 'nausea', label: '恶心', icon: '😵', bgColor: 'rgba(156, 163, 175, 0.2)', description: '胃部不适、想吐的感觉', details: ['轻微恶心', '明显恶心', '频繁恶心', '伴呕吐', '晨起明显'], triggers: ['进食后', '闻到异味', '乘车时', '服药后', '妊娠反应'] },
  { id: 'chills', label: '畏寒', icon: '🥶', bgColor: 'rgba(59, 130, 246, 0.15)', description: '感觉寒冷、怕冷', details: ['轻微怕冷', '明显畏寒', '寒战', '四肢冰凉', '发热前兆'], triggers: ['感染发热', '贫血', '甲状腺功能减退', '循环不良'] },
  { id: 'wheeze', label: '喘息', icon: '🫁', bgColor: 'rgba(139, 92, 246, 0.15)', description: '呼吸时伴有哮鸣音', details: ['轻度喘息', '明显喘息', '呼气困难', '伴有咳嗽', '夜间发作'], triggers: ['过敏原接触', '冷空气刺激', '运动诱发', '情绪激动', '感染后'] },
  { id: 'dizziness', label: '头晕', icon: '🌀', bgColor: 'rgba(59, 130, 246, 0.15)', description: '头部昏沉、眩晕感', details: ['轻度头晕', '眩晕感', '站立不稳', '眼前发黑', '伴恶心'], triggers: ['血压异常', '贫血', '颈椎问题', '低血糖', '体位改变'] },
  { id: 'palpitations', label: '心悸', icon: '💓', bgColor: 'rgba(239, 68, 68, 0.2)', description: '心跳加快、心慌的感觉', details: ['轻微心慌', '心跳加速', '心律不齐感', '胸闷心悸', '夜间明显'], triggers: ['剧烈运动', '情绪激动', '发热时', '贫血', '甲状腺疾病'] },
  { id: 'other', label: '其他', icon: '➕', bgColor: 'rgba(156, 163, 175, 0.15)', description: '其他未列出的症状', details: [] as string[], triggers: [] as string[] }
]

const TRIAGE_SYSTEM_PROMPT = `你是一位专业的医疗智能分诊AI助手。根据用户提供的症状信息，进行智能分诊评估。

你必须严格按照以下JSON格式返回结果（不要包含任何其他文字说明）：
{
  "riskScore": 0到100的整数,
  "riskLevel": "低风险" 或 "中风险" 或 "高风险",
  "riskDescription": "简短的风险描述（一句话）",
  "diseases": [
    {"name": "疾病名称", "probability": 0到100的整数, "reason": "判断依据"}
  ],
  "advice": [
    {"title": "建议标题", "desc": "具体建议内容"}
  ],
  "notices": ["注意事项1", "注意事项2", "注意事项3"]
}

评估原则：
- 咯血、呼吸困难、高热组合 → 高风险
- 慢性咳嗽+盗汗+体重下降 → 重点排查肺结核
- 急性发热+咳嗽+咳痰 → 肺炎可能性大
- 症状较轻、单一 → 低风险
- riskScore范围：20-100
- diseases列表按probability从高到低排列，最多5个
- advice至少包含：推荐就诊科室、建议检查项目、建议就诊时间
- notices至少3条`

function toggleSymptom(id: string) {
  const idx = form.symptoms.indexOf(id)
  if (idx > -1) {
    form.symptoms.splice(idx, 1)
    if (!isOtherSymptom(id)) delete form.symptomDetails[id]
  } else {
    form.symptoms.push(id)
    if (!form.symptomDetails[id]) {
      form.symptomDetails[id] = { severity: 'moderate', details: [], detailsOther: '', triggers: [], triggersOther: '', ...(isOtherSymptom(id) ? { name: '' } : {}) }
    }
  }
}

function isOtherSymptom(id: string) { return id.startsWith('other_') }

let otherCounter = 0
function addOtherSymptom() {
  otherCounter++
  const id = `other_${otherCounter}`
  form.symptoms.push(id)
  form.symptomDetails[id] = { severity: 'moderate', name: '', details: [] as string[], detailsOther: '', triggers: [] as string[], triggersOther: '' }
}

function removeOtherSymptom(id: string) {
  const idx = form.symptoms.indexOf(id)
  if (idx > -1) { form.symptoms.splice(idx, 1); delete form.symptomDetails[id] }
}

function getSymptomById(id: string) {
  const opt = symptomOptions.find(s => s.id === id)
  if (opt) return opt
  if (isOtherSymptom(id)) return { id, label: form.symptomDetails[id]?.name || '其他症状', icon: '➕', bgColor: 'rgba(156, 163, 175, 0.15)', description: '自定义症状', details: [] as string[], triggers: [] as string[] }
  return null
}

// Non-null version for template use inside v-if guard
function sById(id: string) { return getSymptomById(id)! }

function getSymptomDetail(id: string) {
  if (!form.symptomDetails[id]) form.symptomDetails[id] = { severity: 'moderate', details: [] as string[], detailsOther: '', triggers: [] as string[], triggersOther: '' }
  if (form.symptomDetails[id].detailsOther === undefined) form.symptomDetails[id].detailsOther = ''
  if (form.symptomDetails[id].triggersOther === undefined) form.symptomDetails[id].triggersOther = ''
  return form.symptomDetails[id]
}

async function handleTriage() {
  if (form.symptoms.length === 0) { ElMessage.warning('请至少选择一个症状'); return }
  for (const id of form.symptoms) {
    if (isOtherSymptom(id) && !getSymptomDetail(id).name?.trim()) { ElMessage.warning('请填写其他症状的名称'); return }
  }
  analyzing.value = true

  // F-09: 取消上一次未完成的分诊请求，避免竞态
  analyzeAbort?.abort()
  analyzeAbort = new AbortController()

  const symptomDescriptions = form.symptoms.map(id => {
    const opt = getSymptomById(id)
    const detail = form.symptomDetails[id] || {}
    const severityMap: Record<string, string> = { mild: '轻微', moderate: '中度', severe: '严重' }
    let desc = ''
    if (isOtherSymptom(id)) { desc = detail.name || '其他症状' } else { desc = opt ? opt.label : id }
    if (detail.severity) desc += `（${severityMap[detail.severity] || '中度'}）`
    if (detail.details && detail.details.length > 0) {
      const filteredDetails = detail.details.filter((d: string) => d !== '__other__')
      const otherDetail = detail.details.includes('__other__') && detail.detailsOther ? detail.detailsOther : ''
      const allDetails = [...filteredDetails, otherDetail].filter(Boolean)
      if (allDetails.length > 0) desc += `，具体表现：${allDetails.join('、')}`
    } else if (detail.detailsOther) { desc += `，具体表现：${detail.detailsOther}` }
    if (detail.triggers && detail.triggers.length > 0) {
      const filteredTriggers = detail.triggers.filter((t: string) => t !== '__other__')
      const otherTrigger = detail.triggers.includes('__other__') && detail.triggersOther ? detail.triggersOther : ''
      const allTriggers = [...filteredTriggers, otherTrigger].filter(Boolean)
      if (allTriggers.length > 0) desc += `，触发因素：${allTriggers.join('、')}`
    } else if (detail.triggersOther) { desc += `，触发因素：${detail.triggersOther}` }
    return desc
  })

  const userPrompt = `请根据以下患者信息进行智能分诊评估：

【基本信息】
年龄：${form.age}岁
性别：${form.gender === 'male' ? '男' : '女'}

【主要症状详情】
${symptomDescriptions.join('\n')}

【症状持续时间】
${form.duration || '未填写'}${form.durationDetail ? `，${form.durationDetail}` : ''}

【既往病史】
${form.medical_history || '无'}

请按照指定JSON格式返回分诊结果。`

  try {
    const res: any = await llmApi.patientChat({
      messages: [
        { role: 'system', content: TRIAGE_SYSTEM_PROMPT },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.3,
      max_tokens: 2000
    }, { signal: analyzeAbort.signal })

    // 检查API是否成功
    if (!res.success && res.error) {
      ElMessage.error(res.error || 'AI服务暂不可用')
      return
    }

    let aiContent = res.content || ''

    // 去除markdown代码块标记
    aiContent = aiContent.replace(/```json\s*/g, '').replace(/```\s*/g, '').trim()

    const jsonMatch = aiContent.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      try {
        const parsed = JSON.parse(jsonMatch[0])
        const riskColorMap: Record<string, { color: string; bg: string }> = {
          '低风险': { color: '#22D3EE', bg: 'rgba(34, 211, 238, 0.2)' },
          '中风险': { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.2)' },
          '高风险': { color: '#EF4444', bg: 'rgba(239, 68, 68, 0.2)' }
        }
        const diseaseColors = ['#EF4444', '#F59E0B', '#3B82F6', '#8B5CF6', '#22D3EE']
        triageResult.value = {
          // F-09: riskScore 钳制到 0-100，防止 AI 越界值打爆进度条
          riskScore: Math.min(100, Math.max(0, Number(parsed.riskScore) || 0)),
          riskLevel: parsed.riskLevel,
          riskColor: riskColorMap[parsed.riskLevel]?.color || '#F59E0B',
          riskBgColor: riskColorMap[parsed.riskLevel]?.bg || 'rgba(245, 158, 11, 0.2)',
          riskDescription: parsed.riskDescription,
          diseases: (parsed.diseases || []).map((d: any, i: number) => ({ name: d.name, probability: d.probability, rankColor: diseaseColors[i % diseaseColors.length], reason: d.reason })),
          advice: (parsed.advice || []).map((a: any) => ({ icon: getAdviceIcon(a.title), title: a.title, desc: a.desc, color: '#3B82F6', bgColor: 'rgba(59, 130, 246, 0.15)' })),
          notices: parsed.notices || ['分诊结果仅供参考，不构成医疗诊断，请以医生面诊意见为准', '如出现持续高热、严重呼吸困难、咯血等紧急症状，请立即拨打120', '就诊时请携带既往检查报告和用药记录']
        }
      } catch (parseErr) {
        console.error('分诊JSON解析失败:', parseErr)
        ElMessage.error('AI返回结果格式异常，请重试')
      }
    } else {
      console.warn('分诊原始内容(无JSON):', aiContent.substring(0, 200))
      ElMessage.error('AI未返回有效数据，请重试')
    }
  } catch (err: any) {
    // F-09: 用户取消/新请求替换旧请求时静默处理
    if (err?.name === 'CanceledError' || err?.name === 'AbortError' || err?.code === 'ERR_CANCELED') return
    ElMessage.error('智能分诊调用失败，请重试')
  } finally { analyzing.value = false }
}

// F-09: 离开页面时取消进行中的请求
let analyzeAbort: AbortController | null = null
onUnmounted(() => { analyzeAbort?.abort() })

function getAdviceIcon(title: string) {
  if (title.includes('科室')) return '🏥'
  if (title.includes('检查')) return '🔬'
  if (title.includes('时间')) return '⏰'
  if (title.includes('AI') || title.includes('诊断')) return '🤖'
  if (title.includes('药物') || title.includes('用药')) return '💊'
  if (title.includes('生活') || title.includes('护理')) return '🛏'
  return '📋'
}
</script>

<style scoped lang="scss">
// 全局统一表单元素圆角
:deep(.el-input__wrapper) {
  border-radius: var(--radius-md) !important;
}

:deep(.el-textarea__inner) {
  border-radius: var(--radius-md) !important;
}

:deep(.el-input-number__wrapper) {
  border-radius: var(--radius-md) !important;
}

// 年龄输入框样式
.age-input {
  width: 100%;

  :deep(.el-input-number__wrapper) {
    border-radius: var(--radius-md) !important;
    background-color: var(--card-bg) !important;
    border-color: var(--glass-border) !important;
    box-shadow: none !important;
    transition: all 0.3s ease !important;
    padding: 4px 12px !important;

    &:hover {
      border-color: var(--primary) !important;
    }

    &.is-focus {
      border-color: var(--primary) !important;
      box-shadow: 0 0 0 1px var(--primary) inset !important;
    }
  }

  :deep(.el-input__inner) {
    color: var(--text-primary) !important;
    font-size: 14px;

    &::placeholder {
      color: var(--text-muted);
    }
  }

  :deep(.el-input-number__decrease),
  :deep(.el-input-number__increase) {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border-color: var(--glass-border) !important;

    &:hover {
      color: var(--primary) !important;
      border-color: var(--primary) !important;
    }
  }
}

.triage-page {
  .triage-layout {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
}

.form-section {
  margin-bottom: 28px;
  margin-top: 28px;

  .section-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 16px;
    padding-left: 14px;
    border-left: 3px solid var(--primary);
    display: flex;
    align-items: center;

    .section-hint {
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 400;
      margin-left: 8px;
    }
  }
}

// 左右布局容器
.form-section-row {
  display: flex;
  gap: 20px;

  .form-section.half {
    flex: 1;
    min-width: 0; // 允许flex收缩

    &:first-child {
      margin-top: 28px;
      margin-bottom: 28px;
    }

    &:last-child {
      margin-top: 28px;
      margin-bottom: 28px;
    }
  }
}

.symptom-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 14px;
}

.symptom-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 16px 10px;
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-bg-hover), transparent);
  }

  &:hover {
    transform: translateY(-3px);
    border-color: var(--glass-border-hover);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
  }

  &.active {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(34, 211, 238, 0.1));
    border-color: var(--primary);
    box-shadow: 0 0 0 1px var(--primary), 0 8px 24px rgba(34, 211, 238, 0.25);

    .symptom-name {
      color: var(--primary);
      font-weight: 600;
    }
  }

  .symptom-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    transition: all 0.3s ease;
  }

  .symptom-name {
    font-size: 13px;
    color: var(--text-secondary);
    text-align: center;
    transition: all 0.3s ease;
    font-weight: 500;
  }

  &.add-other-btn {
    border-style: dashed;

    .symptom-name {
      color: var(--primary);
      font-weight: 600;
    }

    &:hover {
      border-color: var(--primary);
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.1), rgba(34, 211, 238, 0.05));

      .symptom-icon {
        background: rgba(34, 211, 238, 0.3);
      }
    }

    &:active {
      background: linear-gradient(135deg, rgba(34, 211, 238, 0.25), rgba(34, 211, 238, 0.12));
      border-color: var(--primary);
      box-shadow: 0 0 0 1px var(--primary), 0 4px 12px rgba(34, 211, 238, 0.3);
      transform: scale(0.95);
    }
  }
}

.symptom-detail-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.other-detail-input {
  max-width: 320px;

  :deep(.el-input__wrapper) {
    background-color: var(--card-bg) !important;
    border-color: var(--glass-border) !important;
    box-shadow: none !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.3s ease !important;

    &:hover {
      border-color: var(--primary) !important;
    }

    &.is-focus {
      border-color: var(--primary) !important;
      box-shadow: 0 0 0 1px var(--primary) inset !important;
    }
  }

  :deep(.el-input__inner) {
    color: var(--text-primary) !important;
    font-size: 13px;

    &::placeholder {
      color: var(--text-muted);
    }
  }

  :deep(.el-input__count-inner) {
    background: transparent !important;
    color: var(--text-muted) !important;
  }
}

.detail-checkbox-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.symptom-detail-card {
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-bg-hover), transparent);
  }

  &:hover {
    transform: translateY(-2px);
    border-color: var(--primary);
    box-shadow: 0 8px 24px rgba(34, 211, 238, 0.15);
  }

  // 统一卡片内输入框圆角
  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner) {
    border-radius: var(--radius-md) !important;
  }
}

.symptom-detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--glass-border);

  .symptom-detail-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    background: rgba(34, 211, 238, 0.15);
    flex-shrink: 0;
  }

  .symptom-detail-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .symptom-detail-desc {
    font-size: 12px;
    color: var(--text-muted);
    margin-left: auto;
    max-width: 200px;
    text-align: right;
  }

  .remove-other-btn {
    margin-left: 4px;
    flex-shrink: 0;
    width: 28px;
    height: 28px;
    min-width: 28px;
    padding: 0 !important;
    border-radius: 50% !important;
    background: rgba(239, 68, 68, 0.12) !important;
    border: 1px solid rgba(239, 68, 68, 0.25) !important;
    color: #EF4444 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;

    .el-icon {
      font-size: 14px;
      margin: 0 !important;
    }

    &:hover {
      background: rgba(239, 68, 68, 0.25) !important;
      border-color: rgba(239, 68, 68, 0.5) !important;
    }
  }
}

.symptom-detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;

  &:last-child {
    margin-bottom: 0;
  }

  .detail-label {
    font-size: 13px;
    color: var(--text-secondary);
    min-width: 75px;
    line-height: 32px;
    flex-shrink: 0;
    font-weight: 500;
  }

  // 统一输入框圆角与按钮一致
  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner) {
    border-radius: var(--radius-md) !important;
  }

  :deep(.el-radio-group) {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  :deep(.el-radio-button__inner) {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    color: var(--text-secondary);
    font-weight: 500;
    padding: 8px 16px;
    border-radius: var(--radius-md) !important;
    transition: all 0.3s ease;

    &:hover {
      background: var(--glass-bg-hover);
      border-color: var(--glass-border-hover);
      color: var(--text-primary);
    }
  }

  :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.2), rgba(34, 211, 238, 0.1));
    border-color: var(--primary);
    color: var(--primary);
    box-shadow: 0 0 0 1px var(--primary), 0 4px 12px rgba(34, 211, 238, 0.2);
  }

  :deep(.el-checkbox-group) {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  :deep(.el-checkbox) {
    margin-right: 0;
    height: auto;

    .el-checkbox__input .el-checkbox__inner {
      background: var(--glass-bg);
      border-color: var(--glass-border);
      border-radius: 4px;
      width: 18px;
      height: 18px;
      transition: all 0.3s ease;

      &:hover {
        border-color: var(--primary);
      }

      &.is-checked .el-checkbox__inner {
        background: var(--primary);
        border-color: var(--primary);
      }
    }

    .el-checkbox__label {
      font-size: 13px;
      color: var(--text-secondary);
      font-weight: 500;
      padding-left: 10px;
    }

    &.is-checked .el-checkbox__label {
      color: var(--text-primary);
    }
  }

  // 统一输入框与其他控件的圆角
  :deep(.el-input__wrapper) {
    border-radius: var(--radius-md) !important;
  }

  :deep(.el-textarea__inner) {
    border-radius: var(--radius-md) !important;
  }
}

.duration-group {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.duration-item {
  :deep(.el-radio__input) {
    display: none;
  }

  :deep(.el-radio__label) {
    padding: 0;
    width: 100%;
  }

  width: 100%;
  padding: 16px !important;
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  margin-bottom: 0;
  transition: all 0.3s ease;
  display: flex !important;
  align-items: center;
  position: relative;
  overflow: hidden;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-bg-hover), transparent);
  }

  &:hover {
    transform: translateY(-2px);
    border-color: var(--glass-border-hover);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  &.is-checked {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.15), rgba(34, 211, 238, 0.08));
    border-color: var(--primary);
    box-shadow: 0 0 0 1px var(--primary), 0 4px 16px rgba(34, 211, 238, 0.2);

    .duration-label {
      color: var(--primary);
      font-weight: 600;
    }

    .duration-desc {
      color: var(--primary);
      opacity: 0.8;
    }
  }

  .duration-label {
    font-size: 17px;
    font-weight: 500;
    color: var(--text-primary);
    margin-right: 16px;
    transition: all 0.3s ease;
  }

  .duration-desc {
    font-size: 12px;
    color: var(--text-muted);
    transition: all 0.3s ease;
  }
}

// 病史 textarea 统一圆角
.history-textarea {
  :deep(.el-textarea__inner) {
    border-radius: var(--radius-md) !important;
    background-color: var(--card-bg) !important;
    border-color: var(--glass-border) !important;
    transition: all 0.3s ease !important;

    &:hover {
      border-color: var(--primary) !important;
    }

    &:focus {
      border-color: var(--primary) !important;
      box-shadow: 0 0 0 1px var(--primary) inset !important;
    }
  }
}

// 持续时间补充输入框统一圆角
.duration-detail-input {
  width: 100%;
  margin-top: 8px;

  :deep(.el-input__wrapper) {
    border-radius: var(--radius-md) !important;
    background-color: var(--card-bg) !important;
    border-color: var(--glass-border) !important;
    transition: all 0.3s ease !important;

    &:hover {
      border-color: var(--primary) !important;
    }

    &.is-focus {
      border-color: var(--primary) !important;
      box-shadow: 0 0 0 1px var(--primary) inset !important;
    }
  }
}

.submit-btn {
  width: 100%;
  height: 52px;
  font-size: 17px;
  font-weight: 600;
  margin-top: 12px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary), rgba(34, 211, 238, 0.8));
  border: none;
  box-shadow: 0 4px 16px rgba(34, 211, 238, 0.3);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
    transition: left 0.5s ease;
  }

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(34, 211, 238, 0.4);

    &::before {
      left: 100%;
    }
  }

  &:active {
    transform: translateY(0);
  }
}

.empty-card {
  height: 100%;
  display: none; // 隐藏等待分诊评估盒子
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.result-row {
  display: flex;
  flex-direction: column;
  gap: 20px;

  &:not(:last-child) {
    margin-bottom: 20px;
  }
}

.risk-card {
  margin-bottom: 0;
}

.empty-state {
  text-align: center;

  .empty-icon {
    width: 90px;
    height: 90px;
    margin: 0 auto 24px;
    background: var(--card-bg);
    backdrop-filter: blur(10px);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    border: 1px solid var(--glass-border);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);

    svg {
      width: 44px;
      height: 44px;
    }
  }

  h3 {
    font-size: 20px;
    color: var(--text-secondary);
    font-weight: 600;
    margin-bottom: 10px;
  }

  p {
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 28px;
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }

  .empty-tips {
    display: flex;
    gap: 28px;
    justify-content: center;
  }

  .tip-item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: var(--text-secondary);
    font-weight: 500;
    padding: 12px 20px;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    transition: all 0.3s ease;

    &:hover {
      border-color: var(--glass-border-hover);
      transform: translateY(-2px);
    }
  }
}

.risk-card {
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: 28px;
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-bg), transparent);
  }

  &::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -30%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.05) 0%, transparent 70%);
    pointer-events: none;
  }

  &:hover {
    border-color: var(--glass-border-hover);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
  }

  .risk-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
    position: relative;
    z-index: 1;
  }

  .risk-label {
    font-size: 14px;
    color: var(--text-secondary);
    margin-bottom: 10px;
    font-weight: 500;
  }

  .risk-score-main {
    display: flex;
    align-items: baseline;
    gap: 4px;
  }

  .risk-number {
    font-size: 52px;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -1px;
  }

  .risk-total {
    font-size: 20px;
    color: var(--text-muted);
    font-weight: 400;
  }

  .risk-level-badge {
    padding: 8px 20px;
    border-radius: 24px;
    font-size: 17px;
    font-weight: 600;
    backdrop-filter: blur(10px);
  }

  .risk-bar {
    height: 10px;
    background: var(--glass-bg);
    border-radius: 5px;
    overflow: hidden;
    margin-bottom: 16px;
    position: relative;
    z-index: 1;
  }

  .risk-bar-fill {
    height: 100%;
    border-radius: 5px;
    transition: width 1s ease;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(90deg, transparent, var(--glass-border-hover), transparent);
      animation: shimmer 2s infinite;
    }
  }

  .risk-desc {
    font-size: 17px;
    font-weight: 500;
    position: relative;
    z-index: 1;
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }

  100% {
    transform: translateX(100%);
  }
}

.result-detail-card {
  margin-bottom: 0;
  height: fit-content;

  &.disease-card,
  &.advice-card {
    max-height: none;
    overflow-y: visible;
  }
}

.disease-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.disease-item {
  display: flex;
  gap: 16px;
  padding: 18px;
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-bg-hover), transparent);
  }

  &:hover {
    transform: translateY(-2px);
    border-color: var(--glass-border-hover);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  .disease-rank {
    width: 32px;
    height: 32px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .disease-info {
    flex: 1;
  }

  .disease-name {
    font-size: 17px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }

  .disease-prob {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }

  .prob-bar-mini {
    flex: 1;
    height: 6px;
    background: var(--glass-bg);
    border-radius: 3px;
    overflow: hidden;
  }

  .prob-fill-mini {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s ease;
    box-shadow: 0 0 8px var(--glass-border-hover);
  }

  .prob-text {
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
  }

  .disease-reason {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.6;
  }
}

.advice-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.advice-item {
  display: flex;
  gap: 16px;
  padding: 18px;
  border-radius: var(--radius-lg);
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--glass-bg-hover), transparent);
  }

  &:hover {
    transform: translateY(-2px);
    border-color: var(--glass-border-hover);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  .advice-icon {
    width: 46px;
    height: 46px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .advice-title {
    font-size: 17px;
    font-weight: 600;
    margin-bottom: 6px;
  }

  .advice-desc {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.6;
  }
}

.notice-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notice-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  padding: 12px;
  background: var(--glass-bg);
  border-radius: var(--radius-md);
  transition: all 0.3s ease;

  &:hover {
    background: var(--glass-bg-hover);
  }
}

.notice-icon {
  width: 26px;
  height: 26px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.1));
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #3B82F6;
  flex-shrink: 0;
}

.disclaimer-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(245, 158, 11, 0.08));
  border: 1px solid rgba(245, 158, 11, 0.25);
  border-radius: var(--radius-lg);
  font-size: 13px;
  color: var(--orange);
  line-height: 1.6;
  font-weight: 500;
  backdrop-filter: blur(10px);

  .el-icon {
    font-size: 18px;
    flex-shrink: 0;
  }
}

@media (max-width: 1200px) {
  .result-row {
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .symptom-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .duration-group {
    grid-template-columns: 1fr;
  }

  .empty-tips {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
