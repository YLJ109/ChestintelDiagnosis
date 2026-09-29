<template>
  <div class="qrcode-login">
    <div class="login-method-toggle">
      <el-button
        :type="loginMode === 'manual' ? 'primary' : 'default'"
        @click="loginMode = 'manual'"
        size="large"
      >
        <el-icon><Edit /></el-icon>
        手动输入
      </el-button>
      <el-button
        :type="loginMode === 'qrcode' ? 'primary' : 'default'"
        @click="loginMode = 'qrcode'"
        size="large"
      >
        <el-icon><FullScreen /></el-icon>
        扫码登录
      </el-button>
    </div>

    <!-- 手动输入模式 -->
    <div v-show="loginMode === 'manual'" class="manual-login">
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item prop="patient_no">
          <el-input
            v-model="form.patient_no"
            placeholder="请输入患者编号"
            size="large"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleLogin"
            :loading="loading"
            class="login-btn"
            size="large"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 扫码登录模式 -->
    <div v-show="loginMode === 'qrcode'" class="qrcode-login-mode">
      <div class="scanner-container">
        <div v-if="!scannerActive" class="scanner-placeholder">
          <el-icon :size="80" class="placeholder-icon">
            <Camera />
          </el-icon>
          <p class="placeholder-text">点击下方按钮开启摄像头</p>
          <el-button
            type="primary"
            @click="startScanner"
            :loading="startingScanner"
            size="large"
            class="start-btn"
          >
            <el-icon><VideoCamera /></el-icon>
            开启摄像头
          </el-button>
        </div>

        <div v-else id="qr-reader" class="qr-reader"></div>

        <div class="scanner-tips">
          <el-icon class="tip-icon"><InfoFilled /></el-icon>
          <span>请将患者二维码对准摄像头</span>
        </div>

        <el-button
          v-if="scannerActive"
          @click="stopScanner"
          type="danger"
          text
          class="stop-btn"
        >
          关闭摄像头
        </el-button>
      </div>
    </div>

    <!-- 登录结果提示 -->
    <el-dialog
      v-model="resultDialogVisible"
      :title="loginSuccess ? '登录成功' : '登录失败'"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="result-content">
        <el-icon :size="60" :color="loginSuccess ? '#67C23A' : '#F56C6C'">
          <SuccessFilled v-if="loginSuccess" />
          <CircleCloseFilled v-else />
        </el-icon>
        <p class="result-message">{{ resultMessage }}</p>
      </div>
      <template #footer>
        <el-button @click="resultDialogVisible = false" type="primary">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Edit, FullScreen, Camera, VideoCamera, InfoFilled, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { patientQrcodeLoginApi } from '@/api/auth'
import { Html5Qrcode } from 'html5-qrcode'

const authStore = useAuthStore()
const router = useRouter()

const loginMode = ref<'manual' | 'qrcode'>('manual')
const loading = ref(false)
const formRef = ref()

const form = reactive({
  patient_no: '',
})

const rules = {
  patient_no: [
    { required: true, message: '请输入患者编号', trigger: 'blur' },
  ],
}

// 扫码相关
const scannerActive = ref(false)
const startingScanner = ref(false)
let html5QrCode: Html5Qrcode | null = null

// 登录结果弹窗
const resultDialogVisible = ref(false)
const loginSuccess = ref(false)
const resultMessage = ref('')

// 手动登录
async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.patientLogin(form.patient_no, 'patient_no')
    ElMessage.success('登录成功')
    router.push({ name: 'PatientHome' })
  } catch (error: any) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}

// 开启摄像头扫码
async function startScanner() {
  startingScanner.value = true
  try {
    html5QrCode = new Html5Qrcode('qr-reader')
    
    await html5QrCode.start(
      { facingMode: 'environment' },
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
      },
      onScanSuccess,
      onScanFailure
    )
    
    scannerActive.value = true
    ElMessage.success('摄像头已开启，请对准二维码')
  } catch (error: any) {
    ElMessage.error('无法访问摄像头：' + (error.message || '请检查权限设置'))
    console.error('Scanner error:', error)
  } finally {
    startingScanner.value = false
  }
}

// 扫码成功回调
async function onScanSuccess(decodedText: string) {
  // 验证二维码格式
  if (!decodedText.startsWith('PATIENT_QRCODE:')) {
    ElMessage.warning('无效的二维码，请扫描患者专属二维码')
    return
  }

  // 提取患者编号
  const patientNo = decodedText.replace('PATIENT_QRCODE:', '')
  
  // 停止扫描
  await stopScanner()
  
  // 执行登录
  loading.value = true
  try {
    await authStore.patientLogin(patientNo, 'qrcode')
    
    loginSuccess.value = true
    resultMessage.value = '登录成功！正在跳转...'
    resultDialogVisible.value = true
    
    setTimeout(() => {
      router.push({ name: 'PatientHome' })
    }, 1500)
  } catch (error: any) {
    loginSuccess.value = false
    resultMessage.value = error.message || '登录失败，请重试'
    resultDialogVisible.value = true
  } finally {
    loading.value = false
  }
}

// 扫码失败回调（持续扫描中的失败不需要提示）
function onScanFailure(error: any) {
  // 静默处理，不需要提示
}

// 停止扫码
async function stopScanner() {
  if (html5QrCode && scannerActive.value) {
    try {
      await html5QrCode.stop()
      html5QrCode.clear()
    } catch (error) {
      console.error('Stop scanner error:', error)
    }
    scannerActive.value = false
  }
}

// 组件卸载时清理
onUnmounted(() => {
  stopScanner()
})
</script>

<style scoped lang="scss">
.qrcode-login {
  width: 100%;
}

.login-method-toggle {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  justify-content: center;

  .el-button {
    flex: 1;
    max-width: 200px;
  }
}

.manual-login {
  .login-btn {
    width: 100%;
    margin-top: 8px;
  }
}

.qrcode-login-mode {
  .scanner-container {
    text-align: center;
  }

  .scanner-placeholder {
    padding: 40px 20px;
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    border: 2px dashed var(--glass-border);

    .placeholder-icon {
      color: var(--text-muted);
      margin-bottom: 16px;
    }

    .placeholder-text {
      color: var(--text-secondary);
      font-size: 14px;
      margin-bottom: 24px;
    }

    .start-btn {
      min-width: 180px;
    }
  }

  .qr-reader {
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .scanner-tips {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 16px;
    padding: 12px;
    background: rgba(var(--primary-rgb), 0.1);
    border-radius: var(--radius-md);
    color: var(--primary);
    font-size: 14px;

    .tip-icon {
      font-size: 18px;
    }
  }

  .stop-btn {
    margin-top: 16px;
  }
}

.result-content {
  text-align: center;
  padding: 20px 0;

  .result-message {
    margin-top: 16px;
    font-size: 16px;
    color: var(--text-primary);
  }
}
</style>
