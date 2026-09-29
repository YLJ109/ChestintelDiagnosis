<div align="center">

# ChestintelDiagnosis

**胸影智诊 · 胸部 X 光 AI 智能辅助诊断系统**

[![Vue 3](https://img.shields.io/badge/Vue-3.5-42b883?logo=vue.js)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178c6?logo=typescript)](https://typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/YLJ109/ChestintelDiagnosis?style=social)](https://github.com/YLJ109/ChestintelDiagnosis)

**胸部 X 光 AI 智能辅助诊断系统** — 基于 DenseNet-121 + ONNX 加速推理 + 大语言模型的全栈医学影像 AI 平台

[功能特性](#功能特性) · [系统截图](#系统截图) · [快速开始](#快速开始) · [部署指南](#部署指南) · [API 文档](#api-接口文档)

<img src="docs/screenshots/医护人员-批量诊断-检测完成.png" alt="批量诊断" width="900"/>

</div>

---

## 目录

- [项目简介](#项目简介)
- [功能演进](#功能演进)
- [功能特性](#功能特性)
- [系统截图](#系统截图)
- [技术架构](#技术架构)
- [性能指标](#性能指标)
- [模块说明](#模块说明)
- [数据库设计](#数据库设计)
- [API 接口文档](#api-接口文档)
- [快速开始](#快速开始)
- [部署指南](#部署指南)
- [配置说明](#配置说明)
- [默认账号](#默认账号)
- [常见问题](#常见问题-faq)
- [安全说明](#安全说明)
- [已知限制](#已知限制)
- [开发路线图](#开发路线图)
- [项目结构](#项目结构)

---

## About

**ChestintelDiagnosis（胸影智诊）** 是一套面向医疗机构与基层卫生院的全栈 **AI 辅助胸部 X 光影像诊断平台**。基于 **DenseNet-121 (CheXNet)** 深度学习模型，对 **14 种胸部疾病** 进行多标签概率预测，叠加 Grad-CAM 热力图可视化，并结合大语言模型（LLM）一键生成专业放射学诊断报告。

- **架构**：Vue 3 + TypeScript 前端 / Flask 后端 / SQLite 存储，支持纯 CPU 推理部署
- **多端**：业务端（医护）、患者门户、管理端（权重 / LLM / 审计 / 系统）
- **开箱即用**：内置模型权重与示例数据，三步启动

> 中文名"胸影智诊"，英文项目名 **ChestintelDiagnosis**。

## 项目简介

胸影智诊 是一套面向医疗机构的全栈 **AI 辅助胸部 X 光影像诊断平台**。系统基于 **DenseNet-121 (CheXNet)** 深度学习模型，支持对 **14 种胸部疾病** 进行多标签概率预测，并结合大语言模型（LLM）自动生成专业放射学诊断报告。

### 训练数据集

**ChestX-ray 14 胸部 X 射线图像数据集**

> **关于超神经 Hyper.AI**  
> 超神经 Hyper.AI https://hyper.ai 是科技实验媒体，专注报道人工智能与其适用场景。致力于推动中文领域对机器智能的认知与普及，探讨机器智能的对社会的影响。超神经为提高科研效率，提供大陆范围内最快最全的公开数据集下载节点、人工智能百科词条等多个产品，服务产业相关从业者和科研院所的师生。

- **数据集名称**: ChestX-ray 14 胸部 X 射线图像数据集
- **发布机构**: NIH Clinical Center（美国国立卫生研究院临床研究中心）
- **下载地址**: https://hyper.ai/datasets/16729（国内镜像，推荐）
- **原始发布地址**: https://nihcc.app.box.com/v/ChestXray-NIHCC
- **数据规模**: 112,120 张正身 X 射线图像（来自 30,805 位患者）
- **疾病标注**: 14 种常见胸部疾病（利用 NLP 技术从放射学报告中自动提取）

**数据集简介：**  
这是一个关于胸部 X 射线的医学成像数据集，包含了 30,805 位特殊患者的 112,120 张正身 X 射线图像，这些图像中包括 14 种常见疾病标注（利用 NPL 技术从放射学报告中获取）。

该数据集增加六种额外的胸部疾病（水肿、肺气肿、纤维化、胸膜增厚和疝）来扩展 ChestX-ray8 数据集。

### 核心优势

| 维度 | 能力 |
|:-----|:-----|
| **AI 精度** | 基于 ChestX-ray14 数据集训练的 DenseNet-121，AUC 达到 0.8149 |
| **推理速度** | ONNX Runtime 加速，比原生 PyTorch 快 2~5 倍 |
| **可解释性** | Grad-CAM 热力图可视化，直观展示 AI 关注区域 |
| **报告质量** | LLM (通义千问/DeepSeek) 生成专业放射学报告 (CRISPE 提示框架) |
| **批量处理** | 多线程并行预处理 + 批量推理，数十张影像一键处理 |
| **临床辅助** | 智能分诊 + AI 医学咨询 + 诊断审批工作流 |
| **易部署** | SQLite 零配置数据库，Docker 一键启动，无需额外基础设施 |
| **安全性** | JWT 认证 + RBAC 权限 + AES 加密存储 API Key + 审计日志 |
| **患者门户** | 完整患者终端系统，PC+移动端自适应，人脸识别/二维码登录 |
| **用户体验** | 影像分析立即显示，AI报告异步生成，无需等待 |

### 支持检测的 14 种胸部疾病

| 肺部疾病 | 心血管 | 胸膜/其他 |
|:---------|:-------|:----------|
| `Pneumonia` 肺炎 | `Cardiomegaly` 心脏肥大 | `Pneumothorax` 气胸 |
| `Atelectasis` 肺不张 | `Edema` 水肿 | `Hernia` 疝 |
| `Consolidation` 实变 | — | `Pleural_Thickening` 胸膜增厚 |
| `Infiltration` 浸润 | — | — |
| `Mass` 肿块 | — | — |
| `Nodule` 结节 | — | — |
| `Effusion` 胸腔积液 | — | — |
| `Emphysema` 肺气肿 | — | — |
| `Fibrosis` 纤维化 | — | — |

---

## 功能演进

### 功能演进总览

> 从传统单体应用到现代化全栈平台的全面重构

| 升级项 | 早期版本 | 当前版本 |
|:-------|:-----|:-----|
| **前端框架** | Vue 2 + Options API | Vue 3 + Composition API + `<script setup>` |
| **开发语言** | JavaScript | TypeScript (严格类型) |
| **构建工具** | Webpack | Vite (HMR 极速热更新) |
| **UI 组件库** | Element UI | Element Plus (全新设计语言) |
| **状态管理** | Vuex | Pinia (更轻量, 更好的 TS 支持) |
| **AI 推理引擎** | PyTorch 单引擎 | ONNX 优先 + PyTorch 回退 (双引擎) |
| **推理加速** | 无 | ONNX Runtime (2-5x 加速) + GPU/DirectML 支持 |
| **GPU 方案** | 仅 CUDA | CUDA / DirectML / CPU 自动检测 |
| **批量诊断** | 同步串行处理 | 异步多线程 + 实时进度轮询 + 可取消 |
| **热力图生成** | 随推理同步生成 | 懒加载 (按需加载 PyTorch, 节省显存) |
| **大模型集成** | 固定单一模型 | 多 LLM 配置管理 + AES 加密存储 + 优先级切换 |
| **AI 咨询** | 无 | SSE 流式对话 + 5 种医生角色切换 |
| **智能分诊** | 无 | 症状分析 + 生命体征 + 分诊评估 |
| **诊断审批** | 无 | 完整审批工作流 (待审/通过/驳回) |
| **审计日志** | 基础记录 | 29+ 操作类型中文标签 + 自动清理 |
| **主题系统** | 单一主题 | 深色/浅色双主题 + CSS 变量动态切换 |
| **布局** | 单一布局 | 业务端 + 管理端双布局分离 |
| **文件命名** | 手动录入 | 智能解析 (`P编号-姓名-性别-年龄-症状-序号.png`) |
| **数据库锁** | 频繁死锁 | 自动重试机制 + WAL 模式优化 |
| **患者门户** | 无 | 完整患者终端系统（PC端） |
| **人脸识别** | 无 | 高清摄像头自动识别登录（1280x720 HD） |
| **二维码登录** | 无 | 手机扫码快速登录 |
| **诊断修正** | 无 | 已审批诊断二次修正 + 重新生成报告 |
| **统一打印** | 分散在各模块 | 跨模块统一打印入口 + 患者照片/二维码集成 |
| **移动端适配** | 无 | 响应式设计（规划中） |
| **渲染优化** | 等待全部完成 | 影像分析立即显示，AI报告异步生成 |

---

## 功能特性

### 业务端 (10 大功能模块)

#### 1. 数据看板

<p align="center">
  <img src="docs/screenshots/医护人员-数据看板.png" alt="数据看板" width="800"/>
</p>

- 诊断统计概览：今日 / 本周 / 本月 / 总计 诊断量趋势
- 疾病分布图表：ECharts 饼图（占比）+ 柱状图（频次）
- 用户活跃度统计：各角色活跃人数分布
- 待审批数量实时提醒（顶部导航 Badge）
- 系统 AI 模型运行状态监控

#### 2. 诊断中心

<p align="center">
  <img src="docs/screenshots/医护人员-诊断中心.png" alt="诊断中心" width="280"/>
  <img src="docs/screenshots/医护人员-历史诊断.png" alt="检测结果" width="280"/>
</p>

- 拖拽或点击上传胸部 X 光影像（PNG / JPG / JPEG）
- **智能文件名解析** — 自动提取患者信息：
  ```
  P20260315001-张伟-male-45-Cough-001.png
   │    │     │   │   │       │
   │    │     │   │   │       └── 序号
   │    │     │   │   └────────── 症状代码
   │    │     │   └────────────── 年龄
   │    │     └───────────────── 性别
   │    └─────────────────────── 姓名
   └──────────────────────────── 患者编号
  ```
- AI 实时推理：14 种疾病概率排序展示（进度动画）
- Grad-CAM 热力图叠加显示（青→红渐变，透明度可调）
- **LLM 一键生成报告** — CRISPE 提示词框架，输出检查所见 / 诊断意见 / 建议
- PDF 报告导出下载

#### 3. 批量诊断

<p align="center">
  <img src="docs/screenshots/医护人员-批量诊断.png" alt="批量诊断" width="800"/>
</p>

- 一次选择多张影像，每张独立患者卡片展示
- **继续添加图片** — 诊断中途仍可追加影像
- **关闭按钮** — hover 显示，逐张移除不需要的图片
- 并行批量推理：ThreadPoolExecutor 4 线程预处理 + ONNX 批量推理
- 实时进度条反馈（已处理 / 总数 + 各项状态）
- **停止检测按钮** — 中途取消任务
- 结果区统一查看所有检测概率 + 逐张生成报告

#### 4. 智能分诊

<p align="center">
  <img src="docs/screenshots/医护人员-智能分诊.png" alt="智能分诊" width="800"/>
</p>

- **15+ 种常见症状**多选：咳嗽 / 胸痛 / 呼吸困难 / 咯血 / 发热 / 咳痰等
- **4 级严重程度**分级：轻微 / 中度 / 严重 / 危急
- **5 项生命体征**录入：体温 / 心率 / 收缩压 / 舒张压 / 血氧饱和度 / 呼吸频率
- AI 分诊评估结果：
  - 推荐科室（呼吸科 / 心内科 / 胸外科 / 急诊科）
  - 紧急程度判定（普通 / 严重 / 危急）
  - 分诊依据说明
- 分诊记录历史查询

#### 5. AI 医学咨询

<p align="center">
  <img src="docs/screenshots/医护人员-AI咨询.png" alt="AI咨询" width="800"/>
</p>

- **SSE 流式对话** — 实时打字效果，用户体验流畅
- **5 种医生角色**切换：

  | 角色 | 专业领域 |
  |:-----|:---------|
  | 放射科专家 | 影像解读、疾病鉴别诊断 |
  | 呼吸科专家 | 疾病诊疗方案、用药指导 |
  | 胸外科专家 | 手术指征评估、术后管理 |
  | 急诊科专家 | 急危重症识别和处理 |
  | 全科顾问 | 综合性医学咨询 |

- 会话管理：新建 / 切换 / 删除会话
- Markdown 格式渲染回复内容
- 保留最近 10 轮对话上下文

#### 6. 诊断历史 & 7. 诊断审批 & 8. 诊断修正

**诊断历史：**
- 所有诊断记录列表（支持分页）
- 按时间范围 / 患者 / 状态筛选
- 详情查看：检测结果 + 热力图 + 报告全文
- PDF 在线预览 / 下载

**诊断审批：**
- 三态列表：待审批 / 已审批 / 已驳回
- 审核操作：通过 / 驳回（含备注）
- 审批状态流转追踪

**诊断修正（新增）：**
- 对已审批的诊断进行二次修正
- 支持重新生成 AI 报告
- 完整的修改记录追溯
- 标准医疗报告格式模板（影像学表现/诊断结论/建议）

#### 9. 个人信息管理 & 10. 打印报告

**个人信息：**
- 医护人员个人资料查看与编辑
- 密码修改
- 执业信息维护

**统一打印报告：**
- 跨模块统一打印入口
- 患者照片 + 二维码自动集成
- Base64 图片编码确保打印窗口正常显示
- 医护端模板完整保留主题设置
- 支持从诊断中心、批量诊断、历史诊断等多处调用

---

### 患者门户 (8 大功能模块)

> **全新患者终端系统** — 提供完整的自助医疗服务（PC端）

#### 1. 患者登录与注册

**多种登录方式：**
- **人脸识别登录**（新增）：高清摄像头自动识别，无需手动操作
  - 1280x720 HD 高清分辨率
  - 每 300ms 自动检测人脸
  - 智能频率切换（检测到人脸加速，未检测减速）
  - 相似度阈值 0.5，确保准确性
- **二维码扫码登录**（新增）：手机扫描二维码快速登录
- **传统账号密码登录**：手机号/身份证号 + 密码

**患者注册：**
- 支持 PC 端和移动端注册页面
- 完整的个人信息录入
- 既往病史、过敏史记录
- 紧急联系人信息
- 支持 PC 端和移动端注册页面

#### 2. 患者主页

- 个性化欢迎界面
- 快速访问入口：智能分诊、AI咨询、报告查询
- 最近就诊记录展示
- 健康小贴士推荐

#### 3. 智能分诊

- **15+ 种常见症状**多选：咳嗽 / 胸痛 / 呼吸困难 / 咯血 / 发热等
- **4 级严重程度**分级：轻微 / 中度 / 严重 / 危急
- **5 项生命体征**录入：体温 / 心率 / 血压 / 血氧 / 呼吸频率
- AI 分诊评估结果：
  - 推荐科室（呼吸科 / 心内科 / 胸外科 / 急诊科）
  - 紧急程度判定（普通 / 严重 / 危急）
  - 分诊依据说明
- 分诊记录历史查询

#### 4. AI 医学咨询

- **SSE 流式对话** — 实时打字效果，用户体验流畅
- **5 种医生角色**切换：放射科专家 / 呼吸科专家 / 胸外科专家 / 急诊科专家 / 全科顾问
- 会话管理：新建 / 切换 / 删除会话
- 支持 PC 端和移动端专属界面
- Markdown 格式渲染回复内容
- 保留最近 10 轮对话上下文
- 支持 PC 端和移动端专属界面

#### 5. 诊断报告查询

- 个人所有诊断报告列表（分页显示）
- 按时间范围筛选
- 报告详情查看：检测结果 + 热力图 + AI 生成报告
- PDF 在线预览 / 下载
- **权限控制**：患者只能查看自己的报告，无法查看他人数据

#### 6. 就诊历史

- 完整就诊记录时间线
- 历次诊断结果对比
- 疾病发展趋势分析
- 检查影像资料归档

#### 7. 统一打印报告

- 患者照片 + 二维码自动集成
#### 8. 移动端专属优化

- **响应式设计**：自动检测设备类型，跳转至移动端页面
- **移动端首页**：简化布局，触控友好
- **移动端登录/注册**：专为小屏优化的表单
- **移动端报告列表**：卡片式布局，滑动浏览
- **移动端 AI 咨询**：聊天界面优化，输入便捷
- **移动端智能分诊**：步骤引导，清晰直观
- **移动端个人信息**：资料编辑优化
- **移动端二维码**：扫码登录快捷入口
- **访客模式**：未登录用户可浏览部分公开内容

---
- Base64 图片编码确保打印窗口正常显示
- 支持从报告列表、历史记录多处调用
- 打印模板适配 A4 纸张
#### 8. 移动端专属优化

- **响应式设计**：自动检测设备类型，跳转至移动端页面
- **移动端首页**：简化布局，触控友好
- **移动端登录/注册**：专为小屏优化的表单
- **移动端报告列表**：卡片式布局，滑动浏览
- **移动端 AI 咨询**：聊天界面优化，输入便捷
- **移动端智能分诊**：步骤引导，清晰直观
- **移动端个人信息**：资料编辑优化
- **移动端二维码**：扫码登录快捷入口
- **访客模式**：未登录用户可浏览部分公开内容

---

### 管理端 (7 大功能模块)

<p align="center">
  <img src="docs/screenshots/后台管理-系统概览.png" alt="系统概览" width="280"/>
  <img src="docs/screenshots/后台管理-用户管理.png" alt="用户管理" width="280"/>
  <img src="docs/screenshots/后台管理-患者管理.png" alt="患者管理" width="280"/>
</p>
<p align="center">
  <img src="docs/screenshots/后台管理-权重管理.png" alt="权重管理" width="280"/>
  <img src="docs/screenshots/后台管理-API管理.png" alt="LLM管理" width="280"/>
  <img src="docs/screenshots/后台管理-系统日志.png" alt="审计日志" width="280"/>
</p>
<p align="center">
  <img src="docs/screenshots/后台管理-系统设置.png" alt="系统设置" width="500"/>
</p>

| 模块 | 核心功能 |
|:-----|:---------|
| **系统概览** | 运行数据大盘、用户/患者/诊断统计、模型状态监控 |
| **用户管理** | CRUD、角色分配(admin/doctor/nurse)、启用禁用、密码重置 |
| **患者管理** | CRUD、既往史/过敏史、关联诊断记录查看 |
| **权重文件管理** | 上传(.pth/.pt/.onnx)、列表管理、**在线切换激活权重** |
| **大模型 API 管理** | 多 LLM 配置、**AES 加密存储** API Key、OpenAI 兼容接口、测试连接、优先级 |
| **审计日志** | 29+ 操作类型中文标签、筛选(类型/时间/IP)、操作人/详情完整记录、自动清理 |
| **系统设置** | 系统名称、检测阈值、上传大小限制、会话超时、日志保留天数、并发数 |

---

### 通用特性

- **深色 / 浅色主题** — 全局 CSS 变量主题系统，偏好持久化到数据库
- **响应式侧边栏** — 可折叠导航栏，图标模式节省空间
- **JWT 身份认证** — Bearer Token，30 天有效期
- **RBAC 权限控制** — 基于角色的页面级访问控制（管理员专属页面）
- **路由守卫** — 未登录跳转登录页，无权限拦截回业务端
- **全局错误处理** — 统一 Toast 提示 + 网络异常友好提示
- **玻璃拟态风格** — 登录页毛玻璃效果，科技感视觉设计

---

## 系统截图

### 医护人员端截图

#### 登录与认证

| 页面 | 截图 |
|:-----|:-----|
| 登录界面 | ![登录](docs/screenshots/医护人员-登录界面.png) |
| 人脸识别登录 | ![人脸识别](docs/screenshots/医护人员-登录界面-人脸识别.png) |
| 识别中 | ![识别中](docs/screenshots/医护人员-登录界面-人脸识别中.png) |

#### 核心功能

| 页面 | 截图 |
|:-----|:-----|
| 数据看板 | ![数据看板](docs/screenshots/医护人员-数据看板.png) |
| 诊断中心 | ![诊断中心](docs/screenshots/医护人员-诊断中心.png) |
| 选择患者 | ![选择患者](docs/screenshots/医护人员-诊断中心-选择患者.png) |
| 检测完成 | ![检测完成](docs/screenshots/医护人员-诊断中心-检测完成.png) |
| 批量诊断 | ![批量诊断](docs/screenshots/医护人员-批量诊断.png) |
| 选择患者 (批量) | ![选择患者](docs/screenshots/医护人员-批量诊断-选择患者.png) |
| 检测完成 (批量) | ![检测完成](docs/screenshots/医护人员-批量诊断-检测完成.png) |
| 智能分诊 | ![智能分诊](docs/screenshots/医护人员-智能分诊.png) |
| 选择症状 | ![选择症状](docs/screenshots/医护人员-智能分诊-选择症状.png) |
| 诊断结果 | ![诊断结果](docs/screenshots/医护人员-智能分诊-诊断结果.png) |
| AI 咨询 | ![AI咨询](docs/screenshots/医护人员-AI咨询.png) |
| 历史诊断 | ![历史诊断](docs/screenshots/医护人员-历史诊断.png) |
| 诊断审批 | ![诊断审批](docs/screenshots/医护人员-诊断审批.png) |
| 诊断修正 | ![诊断修正](docs/screenshots/医护人员-诊断修正.png) |

### 患者终端截图

| 页面 | 截图 |
|:-----|:-----|
| 登录界面 | ![登录](docs/screenshots/患者终端-登陆界面.png) |
| 主页 | ![主页](docs/screenshots/患者终端-主页.png) |
| 智能分诊 | ![智能分诊](docs/screenshots/患者终端-智能分诊.png) |
| AI 咨询 | ![AI咨询](docs/screenshots/患者终端-AI咨询.png) |
| 打印报告 | ![打印报告](docs/screenshots/患者终端-打印报告.png) |
| 打印界面 | ![打印界面](docs/screenshots/患者终端-打印报告界面.png) |

### 管理端截图

| 页面 | 截图 |
|:-----|:-----|
| 系统概览 | ![系统概览](docs/screenshots/后台管理-系统概览.png) |
| 用户管理 | ![用户管理](docs/screenshots/后台管理-用户管理.png) |
| 患者管理 | ![患者管理](docs/screenshots/后台管理-患者管理.png) |
| 权重管理 | ![权重管理](docs/screenshots/后台管理-权重管理.png) |
| API 管理 | ![API管理](docs/screenshots/后台管理-API管理.png) |
| 系统日志 | ![审计日志](docs/screenshots/后台管理-系统日志.png) |
| 系统设置 | ![系统设置](docs/screenshots/后台管理-系统设置.png) |

---

## 技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端浏览器                              │
│                                                                 │
│   Vue 3 + TypeScript + Element Plus + ECharts + Pinia           │
│   ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌────────────┐  │
│   │  业务端布局  │ │  管理端布局  │ │  登录页面  │ │  API 服务层 │  │
│   │ MainLayout  │ │AdminLayout │ │ LoginPage │ │   Axios    │  │
│   └──────┬─────┘ └──────┬─────┘ └────┬─────┘ └──────┬─────┘  │
└──────────┼──────────────┼────────────┼──────────────┼───────────┘
           │              │            │              │
           ▼              ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask 后端 :5000                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    API 层 (15 个 Blueprint)                │  │
│  │                                                           │  │
│  │  auth │ users │ patients │ diagnose │ reports             │  │
│  │  batch │ triage │ chat │ model_weights │ llm               │  │
│  │  llm_configs │ audit │ settings │ dashboard │ approvals    │  │
│  └──────────────────────────────┬────────────────────────────┘  │
│                                 │                               │
│  ┌─────────────────────────────▼────────────────────────────┐  │
│  │                      服务层 (Services)                     │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │  ai_service  │  │ llm_service  │  │ report_service│   │  │
│  │  │ ─────────── │  │ ─────────── │  │ ─────────── │   │  │
│  │  │ ONNX 推理引擎 │  │ LLM 报告生成  │  │ PDF 报告导出  │   │  │
│  │  │ Grad-CAM 热力│  │ SSE 流式对话  │  │ 报告组装      │   │  │
│  │  │ 批量并行处理  │  │ 智能分诊分析  │  │              │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────┬───────────────────────────┘  │
│                                 │                               │
│  ┌─────────────────────────────▼───────────────────────────┐  │
│  │                       数据层 (ORM Models)                  │  │
│  │                                                           │  │
│  │  User │ Patient │ Diagnosis │ DiseaseProbability         │  │
│  │  Report │ BatchRecord │ ModelWeight │ LlmConfig          │  │
│  │  TriageRecord │ AiChatSession │ AiChatMessage            │  │
│  │  AuditLog │ SystemSetting │ UserPreference               │  │
│  └──────────────────────────────┬──────────────────────────┘  │
│                                 │                               │
│  ┌─────────────────────────────▼───────────────────────────┐  │
│  │                    SQLite (aixray.db)                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     工具层 (Utils)                         │  │
│  │  auth (JWT Token) │ encryption (AES-256) │ validators     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
   │  ONNX 模型    │   │  PyTorch 权重 │   │  外部 LLM API    │
   │ model_chestX- │   │ model_*.pth  │   │  通义千问/DeepSeek│
   │ ray14_*.onnx  │   │  (GradCAM用) │   │  OpenAI 兼容接口  │
   └──────────────┘   └──────────────┘   └──────────────────┘
```

### 技术栈全景

| 层级 | 技术 | 说明 |
|:-----|:-----|:-----|
| **前端框架** | Vue 3.5 | Composition API + `<script setup lang="ts">` |
| **开发语言** | TypeScript 6.0 | 严格模式，全量类型定义 |
| **构建工具** | Vite 8.0 | ESM 原生、极速 HMR、基于 esbuild |
| **UI 组件库** | Element Plus 2.13 | 企业级 Vue 3 组件库，暗色模式内置 |
| **图表可视化** | ECharts 6.0 + vue-echarts 8.0 | 饼图、柱状图、折线图 |
| **状态管理** | Pinia 3.0 | Vue 官方推荐，TypeScript 友好 |
| **HTTP 客户端** | Axios 1.15 | 请求/响应拦截器、Token 注入 |
| **CSS 预处理** | Sass 1.99 | CSS Variables 主题系统 |
| **后端框架** | Flask 3.0 | 应用工厂模式、Blueprint 模块化 |
| **ORM** | SQLAlchemy 2.0 | SQLite 数据库，关系映射 |
| **AI 推理引擎** | PyTorch 2.0 | DenseNet-121 (CheXNet) 多标签分类 |
| **加速推理** | ONNX Runtime 1.18 | 跨平台优化推理，2-5x 加速 |
| **GPU 加速** | CUDA / DirectML | NVIDIA GPU 或 Windows DirectX GPU |
| **图像处理** | OpenCV 4.9 + Pillow 10.0 | 图像预处理、热力图合成 |
| **大模型 SDK** | OpenAI Python 1.0 | 兼容 OpenAI API 协议的所有 LLM |
| **PDF 生成** | ReportLab 4.0 | 服务端 PDF 报告导出 |
| **实时通信** | Flask-SocketIO 5.3 | WebSocket 支持（预留） |
| **API 限流** | Flask-Limiter 3.5 | 200 次/分钟 默认限制 |
| **加密库** | Cryptography 42.0 | AES-256 对称加密（API Key 存储） |
| **生产 WSGI** | Gunicorn 21 + Gevent 24 | 异步高并发 Worker |

---

## 性能指标

### AI 推理性能

| 场景 | 配置 | 耗时 | 吞吐量 |
|:-----|:-----|:-----|:-------|
| **单张推理 (ONNX + CPU)** | Intel i7 / 16GB RAM | ~80-120ms | ~10 张/秒 |
| **单张推理 (ONNX + GPU)** | NVIDIA RTX 4090 | ~15-30ms | ~40-60 张/秒 |
| **批量 10 张 (ONNX + CPU)** | 同上，含并行预处理 | ~300-500ms | ~25 张/秒 |
| **批量 50 张 (ONNX + CPU)** | 同上 | ~1.5-2.5s | ~25 张/秒 |
| **Grad-CAM 热力图** | PyTorch (懒加载) | ~200-500ms/张 | 按需生成 |

> 注：以上为参考值，实际性能取决于硬件配置和模型复杂度。首次推理包含模型预热开销。

### 系统资源占用

| 组件 | 空闲内存 | 工作时内存 | 说明 |
|:-----|:--------|:----------|:-----|
| Flask 后端 | ~150MB | ~500MB-2GB | 取决于是否加载 AI 模型 |
| ONNX 模型 | — | ~200MB | DenseNet-121 ONNX 格式 |
| PyTorch 模型 (Grad-CAM) | — | ~800MB-1.5GB | 按需懒加载 |
| 前端 Dev Server | ~200MB | ~300MB | Vite HMR 开发模式 |
| 前端 Production Build | — | ~5MB (gzip ~1.5MB) | 静态资源 |

---

## 模块说明

### 后端目录 (`backend/`)

```
backend/
├── app.py                      # 应用工厂: 蓝图注册、静态文件路由、全局异常处理
├── config.py                   # 配置类: 开发/生产环境、JWT、DB、LLM、阈值
├── extensions.py               # Flask 扩展: SQLAlchemy / CORS / SocketIO / Limiter
├── init_db.py                  # 数据库初始化: 建表 + 种子数据 (8用户+10患者+设置)
├── requirements.txt            # Python 依赖清单
│
├── api/                        # ★ API 路由层 (17 个 Blueprint)
│   ├── auth.py                 #   认证: 登录/登出/修改密码/当前用户
│   ├── users.py                #   用户: 列表/创建/编辑/删除/重置密码/偏好
│   ├── patients.py             #   患者: 列表/创建/编辑/删除/关联诊断
│   ├── diagnose.py             #   诊断: 上传影像→AI推理→返回结果
│   ├── reports.py              #   报告: 列表/详情/PDF下载
│   ├── batch.py                #   批量: 上传/异步诊断/进度查询/取消
│   ├── triage.py               #   分诊: 分析/保存记录/列表/详情
│   ├── chat.py                 #   咨询: 会话CRUD/SSE流式对话
│   ├── model_weights.py        #   权重: 上传/列表/激活切换/删除
│   ├── llm_configs.py          #   LLM: CRUD/测试连接/设为默认
│   ├── llm.py                  #   LLM调用: 直接调用接口
│   ├── audit.py                #   审计: 日志查询/操作类型/清理
│   ├── settings.py             #   设置: 读取/修改系统参数
│   ├── dashboard.py            #   看板: 统计聚合/图表数据
│   ├── approvals.py            #   审批: 待审列表/通过/驳回/历史
│   ├── face_auth.py            #   人脸识别: 注册/登录/特征提取/匹配
│   └── patient_portal.py       #   患者门户: 报告查询/历史记录/二维码生成
│
├── models/                     # ★ ORM 数据模型 (14 张表)
│   ├── user.py                 #   users — 用户账号
│   ├── patient.py              #   patients — 患者信息
│   ├── diagnosis.py            #   diagnoses + disease_probabilities — 诊断&概率
│   ├── report.py               #   reports — AI 生成的诊断报告
│   ├── batch.py                #   batch_records — 批量诊断任务
│   ├── model_weight.py         #   model_weights — 模型权重文件元数据
│   ├── llm_config.py           #   llm_configs — 大模型 API 配置
│   ├── triage.py               #   triage_records — 分诊评估记录
│   ├── chat.py                 #   ai_chat_sessions + messages — AI 对话
│   ├── audit.py                #   audit_logs — 操作审计日志
│   └── settings.py             #   system_settings + user_preferences + login_sessions
│
├── services/                   # ★ 核心业务服务
│   ├── ai_service.py           #   AI 推理引擎: ONNX/PyTorch/Grad-CAM/批量
│   ├── llm_service.py          #   LLM 服务: 报告生成/流式对话/分诊分析
│   ├── report_service.py       #   报告组装服务
│   └── pdf_service.py          #   PDF 生成服务
│
├── utils/                      # 工具函数
│   ├── auth.py                 #   JWT Token 生成 / 校验 / 解码
│   ├── encryption.py           #   AES-256 加密 / 解密 (用于 API Key 安全存储)
│   └── validators.py           #   数据校验器
│
├── data/aixray.db              # SQLite 数据库文件 (自动创建)
├── uploads/                    # 用户上传文件存储
│   ├── images/                 #   原始 X 光影像
│   ├── heatmaps/               #   Grad-CAM 热力图
│   └── reports/                #   生成的 PDF 报告
├── weights/                    # AI 模型权重
│   ├── model_chestX-ray14_epochs5_81.49_v1.0.onnx  # ONNX 格式 (★ 推荐, 自动优先加载)
│   └── model_*.pth             #   PyTorch 格式 (Grad-CAM 热力图必需)
└── scripts/
    └── convert_to_onnx.py      # PyTorch → ONNX 模型格式转换工具
```

### 前端目录 (`frontend/`)

```
frontend/
├── index.html                  # HTML 入口
├── package.json                # NPM 依赖与脚本
├── vite.config.ts              # Vite 配置: 代理(@/别名/API代理/插件)
├── tsconfig.json               # TypeScript 编译选项
│
├── public/favicon.svg          # 网站图标 (医疗/X光主题 SVG, #22d3ee)
│
├── src/
│   ├── main.ts                 # 应用入口: 注册 Vue/Pinia/Router/ElementPlus/图标
│   ├── App.vue                 # 根组件: <router-view />
│   │
│   ├── router/index.ts         # 路由: 10业务页 + 7管理页 + 8患者门户 + 登录/注册 + 守卫逻辑
│   ├── router/index.ts         # 路由: 10业务页 + 7管理页 + 9患者门户 + 登录/注册 + 守卫逻辑
│   ├── router/index.ts         # 路由: 10业务页 + 7管理页 + 8患者门户 + 登录/注册 + 守卫逻辑
│   │
│   ├── stores/                 # Pinia 状态管理
│   │   ├── auth.ts             #     认证: user/token/role/login/logout
│   │   ├── app.ts              #     应用: sidebarCollapsed/theme/toggleSidebar
│   │   └── consultation.ts     #     咨询: sessions/currentSessionId
│   │
│   ├── api/                    # API 服务层 (Axios 封装, 18 个模块)
│   │   ├── index.ts            #     Axios 实例 + 请求/响应拦截器
│   │   ├── auth.ts             #     认证 API
│   │   ├── users.ts            #     用户管理 API
│   │   ├── patients.ts         #     患者管理 API
│   │   ├── diagnose.ts         #     诊断 API
│   │   ├── reports.ts          #     报告 API
│   │   ├── batch.ts            #     批量诊断 API
│   │   ├── triage.ts           #     智能分诊 API
│   │   ├── chat.ts             #     AI 咨询 API
│   │   ├── approvals.ts        #     审批 API
│   │   ├── revise.ts           #     诊断修正 API
│   │   ├── model-weights.ts    #     权重管理 API
│   │   ├── llm-configs.ts      #     LLM 配置 API
│   │   ├── llm.ts              #     LLM 调用 API
│   │   ├── audit.ts            #     审计日志 API
│   │   ├── settings.ts         #     系统设置 API
│   │   ├── dashboard.ts        #     数据看板 API
│   │   ├── face.ts             #     人脸识别 API
│   │   └── patient-portal.ts   #     患者门户 API
│   │
│   ├── layouts/                # 布局组件
│   │   ├── MainLayout.vue      #     业务端: 侧边栏 + 顶栏 + 内容 + 密码弹窗
│   │   └── AdminLayout.vue     #     管理端: 侧边栏 + 顶栏 + 内容
│   │
│   ├── views/                  # 页面组件 (35+ 个)
│   │   ├── login/                      # 登录注册模块
│   │   │   ├── LoginPage.vue           #   医护登录（玻璃拟态深色）
│   │   │   ├── MobileLoginPage.vue     #   移动端医护登录
│   │   │   ├── PatientLoginPage.vue    #   患者登录（支持人脸识别/二维码）
│   │   │   ├── MobileRegisterPage.vue  #   移动端患者注册
│   │   │   └── PatientRegisterPage.vue #   PC端患者注册
│   │   │
│   │   ├── patient/                    # 患者门户模块（18 个页面）
│   │   │   ├── MainPage.vue            #   患者门户主布局
│   │   │   ├── HomePage.vue            #   患者主页
│   │   │   ├── MobileMainPage.vue      #   移动端主页
│   │   │   ├── MobileGuestPage.vue     #   移动端访客页
│   │   │   ├── ReportListPage.vue      #   报告列表
│   │   │   ├── MobileReportListPage.vue#   移动端报告列表
│   │   │   ├── HistoryPage.vue         #   就诊历史
│   │   │   ├── TriagePage.vue          #   智能分诊
│   │   │   ├── MobileTriagePage.vue    #   移动端分诊
│   │   │   ├── ChatPage.vue            #   AI咨询
│   │   │   ├── MobileChatPage.vue      #   移动端AI咨询
│   │   │   ├── ReportPrintPage.vue     #   统一打印报告
│   │   │   ├── FaceLoginPage.vue       #   人脸识别登录
│   │   │   ├── QrCodeLogin.vue         #   二维码扫码登录
│   │   │   ├── MobileProfilePage.vue   #   移动端个人信息
│   │   │   ├── MobileQRCodePage.vue    #   移动端二维码
│   │   │   └── README.md               #   患者门户说明文档
│   ├── views/                  # 页面组件 (26+ 个)
│   │   ├── login/                      # 登录注册模块
│   │   │   ├── LoginPage.vue           #   医护登录（玻璃拟态深色）
│   │   │   ├── PatientLoginPage.vue    #   患者登录（支持人脸识别/二维码）
│   │   │   └── PatientRegisterPage.vue #   PC端患者注册
│   │   │
│   │   ├── patient/                    # 患者门户模块（9 个页面）
│   │   │   ├── MainPage.vue            #   患者门户主布局
│   │   │   ├── HomePage.vue            #   患者主页
│   │   │   ├── ReportListPage.vue      #   报告列表
│   │   │   ├── HistoryPage.vue         #   就诊历史
│   │   │   ├── TriagePage.vue          #   智能分诊
│   │   │   ├── ChatPage.vue            #   AI咨询
│   │   │   ├── ReportPrintPage.vue     #   统一打印报告
│   │   │   ├── FaceLoginPage.vue       #   人脸识别登录
│   │   │   └── QrCodeLogin.vue         #   二维码扫码登录
│   ├── views/                  # 页面组件 (35+ 个)
│   │   ├── login/                      # 登录注册模块
│   │   │   ├── LoginPage.vue           #   医护登录（玻璃拟态深色）
│   │   │   ├── MobileLoginPage.vue     #   移动端医护登录
│   │   │   ├── PatientLoginPage.vue    #   患者登录（支持人脸识别/二维码）
│   │   │   ├── MobileRegisterPage.vue  #   移动端患者注册
│   │   │   └── PatientRegisterPage.vue #   PC端患者注册
│   │   │
│   │   ├── patient/                    # 患者门户模块（18 个页面）
│   │   │   ├── MainPage.vue            #   患者门户主布局
│   │   │   ├── HomePage.vue            #   患者主页
│   │   │   ├── MobileMainPage.vue      #   移动端主页
│   │   │   ├── MobileGuestPage.vue     #   移动端访客页
│   │   │   ├── ReportListPage.vue      #   报告列表
│   │   │   ├── MobileReportListPage.vue#   移动端报告列表
│   │   │   ├── HistoryPage.vue         #   就诊历史
│   │   │   ├── TriagePage.vue          #   智能分诊
│   │   │   ├── MobileTriagePage.vue    #   移动端分诊
│   │   │   ├── ChatPage.vue            #   AI咨询
│   │   │   ├── MobileChatPage.vue      #   移动端AI咨询
│   │   │   ├── ReportPrintPage.vue     #   统一打印报告
│   │   │   ├── FaceLoginPage.vue       #   人脸识别登录
│   │   │   ├── QrCodeLogin.vue         #   二维码扫码登录
│   │   │   ├── MobileProfilePage.vue   #   移动端个人信息
│   │   │   ├── MobileQRCodePage.vue    #   移动端二维码
│   │   │   └── README.md               #   患者门户说明文档
│   │   │
│   │   ├── dashboard/DashboardPage.vue # 数据看板（ECharts）
│   │   ├── diagnose/DiagnosePage.vue   # 诊断中心（单张上传+检测+报告）
│   │   ├── batch/BatchDiagnosePage.vue # 批量诊断（多选+进度+三列Grid布局）
│   │   ├── triage/TriagePage.vue       # 智能分诊（症状+体征+评估）
│   │   ├── chat/ChatPage.vue           # AI咨询（SSE流式对话）
│   │   ├── history/HistoryPage.vue     # 诊断历史（记录列表+详情）
│   │   ├── approval/ApprovalPage.vue   # 诊断审批（工作流管理）
│   │   ├── revise/RevisePage.vue       # 诊断修正（二次修正+重新生成报告）
│   │   ├── profile/ProfilePage.vue     # 个人信息（资料编辑+密码修改）
│   │   │
│   │   └── admin/                      # 管理端模块（7 个页面）
│   │       ├── OverviewPage.vue        #   系统概览
│   │       ├── UsersPage.vue           #   用户管理
│   │       ├── PatientsPage.vue        #   患者管理
│   │       ├── ModelsPage.vue          #   权重文件管理
│   │       ├── LlmPage.vue             #   大模型 API 管理
│   │       ├── AuditPage.vue           #   审计日志
│   │       └── SettingsPage.vue        #   系统设置
│   │
│   ├── styles/variables.css    # 全局 CSS 变量 (主题色/间距/圆角/阴影/字体)
│   ├── components/             # 公共组件
│   └── utils/                  # 工具函数
│
└── README.md                   # Vite 默认模板 (可忽略)
```

---

## 数据库设计

### ER 关系图

```
┌─────────────┐       ┌─────────────┐       ┌──────────────────┐
│    users    │ 1   N │  diagnoses  │ N   1 │    patients      │
│─────────────│───────│─────────────│───────│──────────────────│
│ id (PK)     │       │ id (PK)     │       │ id (PK)          │
│ username    │       │ diagnosis_no│       │ patient_no (UQ)  │
│ password_hash│       │ patient_id──┼───────│ name             │
│ role        │◄──────│ doctor_id   │       │ gender / age     │
│ department  │ 1   N │ technician  │       │ medical_history  │
│ ...         │       │ image_path  │       │ ...              │
└──────┬──────┘       │ report_status│       └────────┬─────────┘
       │              │ batch_id────┼───┐              │
       │ 1          N │ created_at  │   │ 1          N │
       ├──────────────┤             │   ├──────────────┤
       │              │ 1         N │   │ triage_records│
       │ N            ├──────────────┤   │──────────────│
       │              │disease_probs│   │ symptoms      │
       │ 1            │reports      │   │ severity      │
       ├──────────────┤             │   │ category      │
       │chat_sessions │             │   └──────────────┘
       │ 1         N │             │
       │ai_messages  │             │
       │              │             │
       │ N            │ N     1     │batch_records
       │audit_logs   │─────────────│total/processed
       │              │             │status/progress
└──────────────┘       └─────────────┘ └──────────────────┘
```

### 核心表结构详解

#### `users` — 用户表

| 字段 | 类型 | 约束 | 说明 |
|:-----|:-----|:-----|:-----|
| id | Integer | PK, AutoInc | 主键 |
| username | String(50) | UNIQUE, NOT NULL | 登录用户名 |
| password_hash | String(255) | NOT NULL | werkzeug SHA256 哈希 |
| real_name | String(50) | NOT NULL | 真实姓名 |
| role | String(20) | NOT NULL | admin / doctor / nurse |
| department | String(50) | — | 所属科室 |
| license_number | String(50) | — | 执业证书编号 |
| email | String(100) | — | 电子邮箱 |
| phone | String(20) | — | 手机号 |
| status | String(20) | DEFAULT 'active' | active / disabled |
| last_login_at | DateTime | — | 最后登录时间 |
| created_at | DateTime | AUTO | 创建时间 |
| updated_at | DateTime | AUTO UPDATE | 更新时间 |

#### `patients` — 患者表

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| id | Integer PK | 主键 |
| patient_no | String(50) UNIQUE | 患者编号 (如 P20260315001) |
| name | String(50) | 姓名 |
| gender | String(10) | male / female |
| birth_date / age | Date / Integer | 出生日期 / 年龄 |
| id_card | String(18) | 身份证号 |
| phone / address | String | 联系方式 / 住址 |
| emergency_contact / phone | String | 紧急联系人 |
| blood_type | String(5) | 血型 (A/B/AB/O +/-) |
| height / weight | Float | 身高(cm) / 体重(kg) |
| medical_history | Text JSON | 既往病史 (数组/对象) |
| allergy_history | Text | 过敏史 |
| created_by | FK(users.id) | 创建人 ID |

#### `diagnoses` — 诊断记录表

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| id | Integer PK | 主键 |
| diagnosis_no | String(50) UNIQUE | 诊断编号 |
| patient_id | FK(patients) | 患者 |
| doctor_id | FK(users) | 诊断医生 |
| technician_id | FK(users) | 上传技师 |
| image_path | String(500) | 影像文件路径 |
| heatmap_path | String(500) | 热力图文件路径 |
| image_metadata | Text JSON | 影像元数据 |
| model_version | String(50) | AI 模型版本标识 |
| report_status | String(30) | pending_review / approved / rejected |
| diagnosis_type | String(20) | single / batch |
| batch_id | FK(batch_records) | 所属批次 (批量时) |
| created_at / reviewed_at | DateTime | 创建/审核时间 |
| reviewed_by | FK(users) | 审核人 |

#### `disease_probabilities` — 疾病概率表

| 字段 | 类型 | 约束 | 说明 |
|:-----|:-----|:-----|:-----|
| id | Integer PK | — | 主键 |
| diagnosis_id | FK(diagnoses) | CASCADE | 所属诊断 |
| disease_code | String(30) | — | 如 Pneumonia, Cardiomegaly... |
| disease_name_zh | String(50) | — | 中文名称: 肺炎, 心脏肥大... |
| probability | Float | — | 0.0 ~ 1.0 检测概率 |
| threshold_exceeded | Boolean | DEFAULT False | 是否超过告警阈值 |
| **UNIQUE** | (diagnosis_id, disease_code) | — | 每种疾病每条诊断唯一 |

#### 其余 10 张表一览

| 表名 | 用途 | 核心字段 |
|:-----|:-----|:---------|
| `reports` | 诊断报告 | findings / impression / recommendations / ai_model_used / pdf_path |
| `batch_records` | 批量任务 | total_count / processed_count / status / progress_json |
| `model_weights` | 权重文件 | filename / file_path / format (.onnx/.pth) / size / is_active |
| `llm_configs` | LLM 配置 | provider / model_name / api_endpoint / api_key_encrypted(**AES**) / default_params / priority |
| `triage_records` | 分诊记录 | symptoms(JSON) / severity / vital_signs(JSON) / category / urgency / reasoning |
| `ai_chat_sessions` | AI 会话 | title / persona / message_count / user_id |
| `ai_chat_messages` | AI 消息 | session_id(FK) / role(user/assistant) / content / created_at |
| `audit_logs` | 审计日志 | action(29种) / resource_type / detail(JSON) / ip_address / user_id |
| `system_settings` | 系统设置 | setting_key(UQ) / setting_value / value_type(string/float/int) / description |
| `user_preferences` | 用户偏好 | user_id(FK, UQ) / theme(dark/light) / language |

---

## API 接口文档

### 规范约定

| 项目 | 说明 |
|:-----|:-----|
| Base URL | `http://localhost:5000/api/v1` |
| 认证方式 | `Authorization: Bearer <jwt_token>` |
| Content-Type | `application/json` |
| 统一响应格式 | `{ code: 200, message: "ok", data: {...} }` |
| 错误响应格式 | `{ code: 4xx/5xx, message: "错误描述" }` |
| 分页参数 | `?page=1&size=20` → `{ total, page, size, items: [] }` |

### 接口总览 (17 个模块, 80+ 接口)

#### 认证 `/auth`

| 方法 | 路径 | 说明 | 认证 |
|:-----|:-----|:-----|:-----|
| POST | `/auth/login` | 用户登录, 返回 JWT | 否 |
| POST | `/auth/logout` | 用户登出 | 是 |
| POST | `/auth/password` | 修改密码 | 是 |
| GET | `/auth/me` | 获取当前用户信息 | 是 |

#### 用户 `/users`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/users` | 用户列表 (分页+搜索) |
| POST | `/users` | 创建用户 |
| PUT | `/users/:id` | 更新用户 |
| DELETE | `/users/:id` | 删除用户 |
| POST | `/users/:id/reset-password` | 重置密码 |
| PUT | `/users/preferences` | 更新个人偏好 (主题等) |

#### 患者 `/patients`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/patients` | 患者列表 (分页+搜索) |
| POST | `/patients` | 创建患者 |
| PUT | `/patients/:id` | 更新患者 |
| DELETE | `/patients/:id` | 删除患者 |
| GET | `/patients/:id/diagnoses` | 患者的诊断记录 |

#### 诊断 `/diagnose`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| POST | `/diagnose/upload` | 上传影像 → AI 推理 → 返回结果 |
| POST | `/diagnose/:id/report` | 为诊断记录生成 LLM 报告 |
| GET | `/diagnose/:id` | 诊断详情 (含概率+报告) |
| GET | `/diagnose` | 诊断记录列表 |

#### 批量诊断 `/batch`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| POST | `/batch/upload` | 批量上传影像 (multipart) |
| POST | `/batch/diagnose` | 开始异步批量诊断 |
| GET | `/batch/progress/:batch_id` | 查询批量进度 (轮询) |
| POST | `/batch/cancel/:batch_id` | 取消批量任务 |
| GET | `/batch/history` | 批量历史记录 |

#### 智能分诊 `/triage`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| POST | `/triage/analyze` | 执行分诊分析 |
| POST | `/triage/records` | 保存分诊记录 |
| GET | `/triage/records` | 分诊记录列表 |
| GET | `/triage/records/:id` | 分诊详情 |

#### AI 咨询 `/chat`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/chat/sessions` | 会话列表 |
| POST | `/chat/sessions` | 新建会话 |
| DELETE | `/chat/sessions/:id` | 删除会话 |
| GET | `/chat/sessions/:id/messages` | 消息历史 |
| POST | `/chat/send` | 发送消息 (**SSE 流式返回**) |

#### 报告 `/reports`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/reports` | 报告列表 |
| GET | `/reports/:id` | 报告详情 |
| GET | `/reports/:id/pdf` | 下载 PDF 报告 |

#### 审批 `/approvals`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/approvals` | 待审批列表 |
| POST | `/approvals/:id/approve` | 通过审批 |
| POST | `/approvals/:id/reject` | 驳回审批 |
| GET | `/approvals/history` | 审批历史 |

#### 诊断修正 `/revise`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/revise/list` | 待修正诊断列表 |
| GET | `/revise/:id/detail` | 诊断详情（含报告） |
| POST | `/revise/:id/submit` | 提交修正结果 |
| POST | `/revise/:id/regenerate-report` | 重新生成 AI 报告 |

#### 人脸识别 `/face-auth`

| 方法 | 路径 | 说明 | 认证 |
|:-----|:-----|:-----|:-----|
| POST | `/face-auth/register` | 注册人脸特征 | 是 |
| POST | `/face-auth/login` | 人脸识别登录 | 否 |
| GET | `/face-auth/check-status` | 检查患者是否已注册人脸 | 否 |
| POST | `/face-auth/extract-features` | 提取人脸特征 | 是 |
| POST | `/face-auth/match` | 人脸特征匹配 | 否 |
| DELETE | `/face-auth/delete` | 删除人脸数据 | 是 |

#### 患者门户 `/patient-portal`

| 方法 | 路径 | 说明 | 认证 |
|:-----|:-----|:-----|:-----|
| GET | `/patient-portal/reports` | 患者报告列表 | 是 |
| GET | `/patient-portal/reports/:id` | 报告详情 | 是 |
| GET | `/patient-portal/history` | 就诊历史 | 是 |
| GET | `/patient-portal/qrcode` | 生成患者二维码 | 是 |
| GET | `/patient-portal/profile` | 个人信息 | 是 |

#### 权重管理 `/model-weights`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/model-weights` | 权重文件列表 |
| POST | `/model-weights/upload` | 上传权重文件 |
| POST | `/model-weights/:id/activate` | 切换激活权重 (热加载) |
| DELETE | `/model-weights/:id` | 删除权重文件 |

#### LLM 配置 `/llm-configs`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/llm-configs` | 配置列表 |
| POST | `/llm-configs` | 新建配置 |
| PUT | `/llm-configs/:id` | 更新配置 |
| DELETE | `/llm-configs/:id` | 删除配置 |
| POST | `/llm-configs/:id/test` | 测试连接 (验证可用性) |
| POST | `/llm-configs/:id/set-default` | 设为默认 |

#### 审计日志 `/audit`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/audit/logs` | 日志列表 (分页+筛选) |
| GET | `/audit/actions` | 操作类型枚举 |
| POST | `/audit/cleanup` | 清理过期日志 |

#### 系统设置 `/settings`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/settings` | 所有设置 |
| PUT | `/settings/:key` | 更新单个设置 |

#### 数据看板 `/dashboard`

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/dashboard/stats` | 统计概览 |
| GET | `/dashboard/chart-data` | 图表数据 |

#### 健康检查

| 方法 | 路径 | 说明 |
|:-----|:-----|:-----|
| GET | `/api/v1/health` | 健康检查 `{ status: "healthy" }` |

---

## 快速开始

### 环境要求

| 环境 | 最低要求 | 推荐配置 |
|:-----|:---------|:---------|
| 操作系统 | Windows 10+ / Ubuntu 20.04+ | Windows 11 / Ubuntu 22.04 |
| Python | 3.9+ | 3.10 / 3.11 |
| Node.js | 18+ | 20 LTS |
| npm | 9+ | 10+ |
| 内存 | 8 GB | 16 GB+ |
| 磁盘 | 5 GB 可用 | 10 GB+ (含模型权重) |
| GPU (可选) | — | NVIDIA RTX 3060+ / AMD RX 6000+ |

### 三步启动

```bash
# ===== 第 1 步: 克隆项目 =====
git clone https://github.com/YLJ109/ChestintelDiagnosis.git
cd ChestintelDiagnosis

# ===== 第 2 步: 启动后端 =====
cd backend
python -m venv venv                          # 创建虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt               # 安装依赖
python init_db.py                             # 初始化数据库 (种子数据)
python app.py                                 # 启动后端 → http://localhost:5000

# ===== 第 3 步: 启动前端 (新终端) =====
cd frontend
npm install                                   # 安装依赖
npm run dev                                   # 启动前端 → http://localhost:5173
```

打开浏览器访问 **http://localhost:5173**，使用默认账号登录即可。

### GPU 加速 (可选)

```bash
# NVIDIA GPU:
pip install onnxruntime-gpu
set AI_DEVICE=cuda          # Windows
# export AI_DEVICE=cuda     # Linux/macOS

# AMD GPU / Windows DirectX:
pip install onnxruntime-directml
# AI_DEVICE=auto 会自动检测 DirectML
```

### 配置环境变量 (可选)

在项目根目录创建 `.env` 文件：

```env
# ===== 必须修改 (生产环境) =====
SECRET_KEY=your-random-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars

# ===== AI 推理 =====
AI_DEVICE=auto                    # auto / cuda / cpu

# ===== 大模型 (报告生成 + AI 咨询需要) =====
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# ===== 加密 =====
LLM_ENCRYPTION_KEY=your-aes-key-exactly-32-bytes-long!!

# ===== 运行环境 =====
FLASK_ENV=development            # development / production
```

---

## 部署指南

### 方案 A: 传统部署 (Nginx + Gunicorn)

适合传统服务器 / VPS 部署场景。

**1. 构建前端**

```bash
cd frontend
npm run build
# 产物在 dist/ 目录
```

**2. Nginx 配置**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件 + SPA history 模式
    location / {
        root /opt/aixray/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到后端
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    # 静态资源 (影像/热力图/PDF)
    location /static {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

**3. Gunicorn 启动后端**

```bash
cd /opt/ChestintelDiagnosis/backend
source venv/bin/activate
export FLASK_ENV=production

gunicorn \
    --bind 127.0.0.1:5000 \
    --worker-class gevent \
    --workers 4 \
    --worker-connections 1000 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    'app:create_app()'
```

**4. Systemd 守护进程 (推荐)**

```ini
# /etc/systemd/system/aixray.service
[Unit]
Description=ChestintelDiagnosis 胸部 X 光 AI 诊断系统 After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/ChestintelDiagnosis/backend
Environment=FLASK_ENV=production
Environment=PATH=/opt/ChestintelDiagnosis/backend/venv/bin
ExecStart=/opt/ChestintelDiagnosis/backend/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --worker-class gevent \
    --workers 4 \
    --timeout 120 \
    'app:create_app()'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable aixray    # 开机自启
sudo systemctl start aixray     # 启动服务
sudo systemctl status aixray    # 查看状态
journalctl -u aixray -f         # 查看日志
```

### 方案 B: Docker 部署

适合容器化 / 云服务器 / Kubernetes 场景。

**docker-compose.yml**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: aixray-backend
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - AI_DEVICE=auto
    volumes:
      - ./data:/app/data           # 数据库持久化
      - ./uploads:/app/uploads     # 上传文件持久化
      - ./weights:/app/weights     # 模型权重持久化
    ports:
      - "5000:5000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./frontend
    container_name: aixray-frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

**后端 Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir onnxruntime

COPY . .
RUN mkdir -p data uploads/images uploads/heatmaps uploads/reports weights
RUN python init_db.py

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", \
     "--worker-class", "gevent", "--workers", "4", \
     "--timeout", "120", "'app:create_app()'"]
```

**前端 Dockerfile**

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**一键启动:**

```bash
docker-compose up -d --build
# 访问: http://your-server-ip
```

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 必须 | 说明 |
|:-------|:-------|:-----|:-----|
| `FLASK_ENV` | development | 否 | development / production |
| `SECRET_KEY` | aixray-default-* | **生产必须改** | Flask Session 密钥 |
| `JWT_SECRET_KEY` | aixray-default-* | **生产必须改** | JWT 签名密钥 |
| `JWT_ACCESS_TOKEN_EXPIRES` | 2592000 | 否 | Token 有效期 (秒), 默认 30 天 |
| `AI_DEVICE` | auto | 否 | 推理设备: auto / cuda / cpu |
| `OPENAI_API_KEY` | (空) | LLM 功能需要 | 大模型 API Key |
| `OPENAI_API_BASE` | 阿里云 DashScope | 否 | LLM API 地址 |
| `LLM_ENCRYPTION_KEY` | aixray-llm-* | 否 | AES 加密密钥 (32 字节) |
| `DISEASE_THRESHOLD` | 0.7 | 否 | 疾病概率告警阈值 (0~1) |
| `AUDIT_RETENTION_DAYS` | 180 | 否 | 审计日志保留天数 |

### 动态系统设置 (管理后台可修改)

| 设置键 | 默认值 | 说明 |
|:-------|:-------|:-----|
| `system_name` | 胸影智诊 | 系统显示名称 |
| `disease_threshold` | 0.7 | 疾病检测告警阈值 |
| `max_upload_size` | 20 | 最大上传大小 (MB) |
| `session_timeout` | 12 | 会话超时 (小时) |
| `audit_retention_days` | 180 | 日志保留天数 |
| `batch_concurrency` | 2 | 批量处理并发线程数 |

---

## 默认账号

> **生产环境请立即修改所有默认密码！**

| 角色 | 用户名 | 密码 | 姓名 | 科室 |
|:-----|:-------|:-----|:-----|:-----|
| 管理员 | `admin` | `admin123` | 系统管理员 | 信息科 |
| 医生 | `doctor_wang` | `doctor123` | 王建国 | 放射科 |
| 医生 | `doctor_li` | `doctor123` | 李秀芳 | 放射科 |
| 医生 | `doctor_zhang` | `doctor123` | 张明远 | 呼吸内科 |
| 医生 | `doctor_chen` | `doctor123` | 陈思远 | 影像科 |
| 医生 | `doctor_liu` | `doctor123` | 刘婉清 | 胸外科 |
| 护士 | `nurse_sun` | `nurse123` | 孙小美 | 放射科 |
| 护士 | `nurse_zhao` | `nurse123` | 赵雅婷 | 呼吸内科 |

> 同时预置了 **10 名示例患者** (P20260315001 ~ P20260315010)，附带完整的个人信息、既往史和过敏史。

---

## 常见问题 FAQ

### Q1: 后端启动报错 `[AI服务] AI模型加载失败`?

**原因**: `weights/` 目录下没有模型权重文件。

**解决**:
1. 将训练好的 `.onnx` 或 `.pth` 文件放入 `backend/weights/` 目录
2. 优先使用 `.onnx` 格式（会被自动优先加载）
3. 如果同时需要热力图功能，还需放置对应的 `.pth` 文件
4. 系统将以「无模型模式」启动，诊断功能不可用但其他功能正常

### Q2: 前端请求后端报 CORS 错误或 404?

**原因**: 开发环境下 Vite 代理未生效，或后端未启动。

**解决**:
1. 确认后端已在 `http://localhost:5000` 运行
2. 确认前端在 `npm run dev` 模式运行（不是直接打开 HTML）
3. 检查 `vite.config.ts` 的 proxy 配置指向正确端口

### Q3: 批量诊断一直显示"检测中"?

**可能原因及排查**:
1. 查看 **后端控制台日志** — 是否有 Python 异常输出
2. 确认模型已成功加载（启动日志应显示 `[AI服务] ✅ ONNX 模型加载成功`）
3. 检查浏览器 F12 Network 面板 — `/batch/progress/:id` 是否有返回数据
4. 如果是最后一项卡住 — 这是已知竞态条件，当前版本已修复

### Q4: 报告生成失败或返回 fallback 报告?

**原因**: LLM API 未配置或连接失败。

**解决**:
1. 在 `.env` 中配置 `OPENAI_API_KEY`
2. 或在管理后台 → 大模型API管理 中添加有效配置
3. 系统会在 LLM 不可用时自动降级为规则模板报告

### Q5: `database is locked` 错误?

**原因**: SQLite 并发写入冲突（多个请求同时写数据库）。

**解决**: 当前版本已内置自动重试机制，短暂等待后会自动恢复。如频繁出现：
1. 减少并发请求数
2. 在 `config.py` 中开启 SQLite WAL 模式
3. 生产环境建议迁移至 PostgreSQL / MySQL

### Q6: 如何切换 AI 模型权重?

1. 上传新的 `.onnx` 或 `.pth` 文件到 **管理后台 → 权重文件管理**
2. 点击「激活」按钮
3. 系统会自动热加载新权重（无需重启）

### Q7: GPU 显存不足?

**优化建议**:
1. 使用 ONNX 模式推理（比 PyTorch 占用更少显存）
2. Grad-CAM 采用懒加载策略，不生成热力图时不占额外显存
3. 设置环境变量 `AI_DEVICE=cpu` 强制使用 CPU 推理
4. 批量诊断时减小 `batch_concurrency` 设置

### Q8: 如何更换 LLM 提供商?

系统支持所有 **OpenAI API 兼容** 的 LLM 服务商：

| 提供商 | API Base 地址 | 推荐模型 |
|:-------|:-------------|:---------|
| 阿里通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-plus / qwen-max |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| OpenAI | `https://api.openai.com/v1` | gpt-4o / gpt-4o-mini |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | glm-4-flash |
| 百川 | `https://api.baichuan-ai.com/v1` | Baichuan3 |

只需在 **管理后台 → 大模型API管理** 中修改 `API Endpoint` 和 `Model Name` 即可。

### Q9: 人脸识别登录如何使用？

**前置条件：**
1. 患者需要在系统中注册人脸数据
2. 摄像头权限已授权

**使用步骤：**
1. 访问 `/patient-login` 页面
2. 点击「人脸识别登录」按钮
3. 允许浏览器访问摄像头
4. 将面部对准扫描框，保持静止
5. 系统自动识别（每 300ms 检测一次）
6. 识别成功后自动登录

**注意事项：**
- 确保光线充足，避免逆光
- 面部无遮挡（口罩、墨镜等）
- 摄像头分辨率至少 1280x720
- 相似度阈值 0.5，低于此值会拒绝登录

### Q10: 患者门户有哪些功能？

**完整患者自助服务系统：**
- **多种登录方式**：人脸识别 / 二维码扫码 / 账号密码
- **智能分诊**：症状分析 + 生命体征录入 + AI 评估
- **AI 医学咨询**：SSE 流式对话，5 种医生角色切换
- **报告查询**：查看个人所有诊断报告（含热力图）
- **就诊历史**：完整就诊记录时间线
- **打印报告**：统一打印入口，患者照片+二维码集成
- **访客模式**：未登录用户可浏览部分公开内容

**权限控制：**
- 患者只能查看自己的报告和历史记录
- 无法查看他人数据，确保隐私安全

---

## 安全说明

### 认证与授权

- **JWT Token**: 使用 HS256 签名，有效期 30 天（可配置）
- **密码存储**: werkzeug PBKDF2-SHA256 哈希，非明文
- **RBAC**: 页面级权限控制，管理员页面仅 admin 角色可访问
- **路由守卫**: 前后端双重校验，未登录自动重定向

### 数据安全

- **API Key 加密**: LLM API Key 使用 AES-256 对称加密后存入数据库
- **SQL 注入防护**: 全量使用 SQLAlchemy ORM 参数化查询
- **XSS 防护**: Vue 3 默认转义渲染内容
- **CSRF 防护**: API 使用 Bearer Token 认证（无 Cookie 依赖）
- **文件上传限制**: 白名单扩展名 (png/jpg/jpeg/dcm/dicom) + 50MB 大小上限
- **API 限流**: Flask-Limiter 默认 200 次/分钟/IP

### 生产环境安全检查清单

- [ ] 修改 `SECRET_KEY` 和 `JWT_SECRET_KEY` 为强随机字符串
- [ ] 修改所有默认用户密码
- [ ] 配置 `FLASK_ENV=production`（关闭 Debug 模式）
- [ ] 使用 HTTPS（Nginx SSL 终结或负载均衡）
- [ ] 配置防火墙，仅开放 80/443 端口
- [ ] 定期备份数据库文件 `data/aixray.db`
- [ ] 审计日志保留策略根据合规要求调整

---

## 已知限制

| **限制** | 说明 | 计划 |
|:-----|:-----|:-----|
| **SQLite 并发** | SQLite 不支持高并发写入 | 未来可选 PostgreSQL |
| **单节点部署** | 当前不支持分布式/集群 | 可通过负载均衡扩展只读 |
| **DICOM 支持** | 声明了支持但尚未完整实现 | 计划  完善 |
| **多租户** | 无医院/机构隔离 | 可通过数据标记实现 |
| **国际化** | 目前仅中文界面 | 可扩展 i18n |
| **模型更新** | 不支持在线训练/微调 | 需离线训练后替换权重 |

---

## 开发路线图

- [x] 患者门户系统（PC+移动端自适应）
- [x] 人脸识别登录（1280x720 HD 高清自动识别）
- [x] 二维码扫码登录
- [x] 诊断修正功能（二次修正+重新生成报告）
- [x] 统一打印报告（跨模块入口+患者照片/二维码集成）
- [x] 移动端专属优化（18个页面，响应式设计）
- [x] 渲染优化（影像分析立即显示，AI报告异步生成）
- [x] 批量诊断优化（三列Grid布局+实时进度）
- [x] 权限控制增强（患者只能查看自己的数据）
### 已实现功能 (已完成)

- [x] 患者门户系统（PC端）
- [x] 人脸识别登录（1280x720 HD 高清自动识别）
- [x] 二维码扫码登录
- [x] 诊断修正功能（二次修正+重新生成报告）
- [x] 统一打印报告（跨模块入口+患者照片/二维码集成）
- [x] 渲染优化（影像分析立即显示，AI报告异步生成）
- [x] 批量诊断优化（三列Grid布局+实时进度）
- [x] 权限控制增强（患者只能查看自己的数据）
- [x] 人脸识别登录（1280x720 HD 高清自动识别）
- [x] 二维码扫码登录
- [x] 诊断修正功能（二次修正+重新生成报告）
- [x] 统一打印报告（跨模块入口+患者照片/二维码集成）
- [x] 移动端专属优化（18个页面，响应式设计）
- [x] 渲染优化（影像分析立即显示，AI报告异步生成）
- [x] 批量诊断优化（三列Grid布局+实时进度）
- [x] 权限控制增强（患者只能查看自己的数据）

### 近期规划 (规划中)

- [ ] DICOM (.dcm) 文件完整支持
- [ ] PostgreSQL / MySQL 数据库可选
- [ ] 诊断报告模板自定义
- [ ] 数据导出 (Excel/CSV)
- [ ] WebSocket 实时通知 (审批/诊断完成)

### 远期规划 (远期)

- [ ] 多机构/多租户隔离
- [ ] 移动端响应式适配
- [ ] 国际化 (i18n) 英文界面

### 产品愿景 (愿景)

- [ ] 微服务架构拆分
- [ ] Kubernetes 部署方案
- [ ] 在线模型微调 (Fine-tuning)
- [ ] 多模态支持 (CT / MRI)
- [ ] HL7 FHIR 医疗互操作性标准对接

---

## 项目结构

```
ChestintelDiagnosis/
│
├── backend/                     # Python Flask 后端
│   ├── api/                     # 17 个 API 蓝图模块（含人脸识别、患者门户）
│   ├── models/                  # 14 个 ORM 数据模型
│   ├── services/                # 核心业务服务 (AI/LLM/报告)
│   ├── utils/                   # 工具函数 (认证/加密/校验)
│   ├── data/                    # SQLite 数据库
│   ├── uploads/                 # 上传文件 (影像/热力图/PDF)
│   ├── weights/                 # AI 模型权重 (.onnx/.pth)
│   ├── scripts/                 # 辅助脚本 (模型转换)
│   ├── app.py                   # 应用入口
│   ├── config.py                # 配置管理
│   ├── extensions.py            # Flask 扩展
│   ├── init_db.py               # 数据库初始化
│   └── requirements.txt         # Python 依赖
│
│   │   ├── views/               # 35+ 个页面组件（含患者门户18页、移动端适配）
├── frontend/                    # Vue 3 前端
│   ├── public/favicon.svg       # 网站图标
│   ├── src/
│   │   ├── api/                 # 18 个 API 服务模块（含人脸识别、患者门户）
│   │   ├── views/               # 26+ 个页面组件（含患者门户9页）
│   │   ├── layouts/             # 2 个布局组件
│   │   ├── stores/              # 3 个 Pinia Store
│   │   ├── router/              # 路由 + 守卫
│   │   ├── styles/              # 全局样式变量
│   │   ├── App.vue              # 根组件
│   │   └── main.ts              # 入口文件
│   │   ├── layouts/             # 2 个布局组件
│   │   ├── stores/              # 3 个 Pinia Store
│   │   ├── router/              # 路由 + 守卫
│   │   ├── styles/              # 全局样式变量
│   │   ├── App.vue              # 根组件
│   │   └── main.ts              # 入口文件
│   ├── index.html               # HTML 入口
│   ├── package.json             # NPM 依赖
│   ├── vite.config.ts           # Vite 配置
│   └── tsconfig.json            # TS 配置
│
│   ├── docs/screenshots/                # 项目截图 (30 张)
│   │   ├── 医护人员-*.png           # (16 张) 登录/诊断/分诊/审批等
│   │   ├── 患者终端-*.png           # (6 张)  患者门户各功能
│   │   └── 后台管理-*.png           # (7 张)  管理端各模块
│   └── docs/samples/                    # 批量诊断示例胸片 (12 张)
│
├── .gitignore                   # Git 忽略规则
├── .env                         # 环境变量 (需自行创建)
└── README.md                    # 本文档
```

---

<div align="center">

**胸影智诊** — 让 AI 赋能医学影像诊断

🌐 [GitHub](https://github.com/YLJ109/ChestintelDiagnosis) | 📖 [文档](#目录) | 🚀 [快速开始](#快速开始)

如有问题或建议，欢迎提 [Issue](https://github.com/YLJ109/ChestintelDiagnosis/issues) 或 [Pull Request](https://github.com/YLJ109/ChestintelDiagnosis/pulls)。

⭐ 如果这个项目对您有帮助，请给个 Star 支持一下！

</div>
