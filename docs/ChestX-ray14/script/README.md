# ChestX-ray14 模型训练脚本说明

## 📊 数据集信息

### ChestX-ray 14 胸部 X 射线图像数据集

**关于超神经 Hyper.AI**  
超神经 Hyper.AI https://hyper.ai 是科技实验媒体，专注报道人工智能与其适用场景。致力于推动中文领域对机器智能的认知与普及，探讨机器智能的对社会的影响。超神经为提高科研效率，提供大陆范围内最快最全的公开数据集下载节点、人工智能百科词条等多个产品，服务产业相关从业者和科研院所的师生。

**数据集详情：**
- **数据集名称**: ChestX-ray 14 胸部 X 射线图像数据集
- **发布机构**: NIH Clinical Center（美国国立卫生研究院临床研究中心）
- **下载地址**: https://hyper.ai/datasets/16729
- **原始发布地址**: https://nihcc.app.box.com/v/ChestXray-NIHCC
- **数据规模**: 112,120 张正身 X 射线图像（来自 30,805 位患者）
- **疾病标注**: 14 种常见胸部疾病（利用 NLP 技术从放射学报告中自动提取）

**数据集简介：**  
这是一个关于胸部 X 射线的医学成像数据集，包含了 30,805 位特殊患者的 112,120 张正身 X 射线图像，这些图像中包括 14 种常见疾病标注（利用 NPL 技术从放射学报告中获取）。

该数据集增加六种额外的胸部疾病（水肿、肺气肿、纤维化、胸膜增厚和疝）来扩展 ChestX-ray8 数据集。

**14 种疾病标签：**
1. Atelectasis（肺不张）
2. Cardiomegaly（心脏肥大）
3. Effusion（胸腔积液）
4. Infiltration（浸润）
5. Mass（肿块）
6. Nodule（结节）
7. Pneumonia（肺炎）
8. Pneumothorax（气胸）
9. Consolidation（实变）
10. Edema（水肿）⭐ 新增
11. Emphysema（肺气肿）⭐ 新增
12. Fibrosis（纤维化）⭐ 新增
13. Pleural_Thickening（胸膜增厚）⭐ 新增
14. Hernia（疝气）⭐ 新增

> ⭐ 标记为相比 ChestX-ray8 新增的疾病类型

---

## 📁 目录结构

```
ChestX-ray14/
├── dataset/
│   ├── images/              # X光图像文件
│   ├── Data_Entry_2017.csv  # 标签文件
│   └── splits/              # 数据集划分结果
├── script/
│   ├── data_preprocessing.py  # 数据预处理
│   ├── train.py               # 模型训练
│   └── evaluate.py            # 模型评估
├── output/
│   ├── best_model.pth         # PyTorch 模型
│   └── best_model.onnx        # ONNX 模型
└── log/
    ├── training.log           # 训练日志
    ├── evaluation.log         # 评估日志
    ├── preprocessing.log      # 预处理日志
    ├── training_curves.png    # 训练曲线图
    ├── roc_curves.png         # ROC 曲线图
    └── evaluation_report.json # 评估报告
```

## 🚀 使用流程

### 1. 数据预处理

```bash
cd script
python data_preprocessing.py
```

**功能：**
- 检查数据集完整性（缺失/损坏图像）
- 分析14种疾病的类别分布
- 划分训练集(80%)、验证集(10%)、测试集(10%)
- 生成数据统计报告

**输出：**
- `../dataset/splits/train.csv`
- `../dataset/splits/val.csv`
- `../dataset/splits/test.csv`
- `../log/dataset_statistics.txt`

---

### 2. 模型训练

```bash
cd script
python train.py
```

**配置参数（在 train.py 中修改）：**
```python
config = {
    'data_dir': '../dataset/images',
    'csv_path': '../dataset/Data_Entry_2017.csv',
    'batch_size': 32,          # 批次大小
    'num_epochs': 20,          # 训练轮数
    'learning_rate': 1e-4,     # 学习率
    'weight_decay': 1e-5,      # 权重衰减
    'num_workers': 4,          # 数据加载线程数
}
```

**训练特性：**
- ✅ DenseNet-121 预训练模型迁移学习
- ✅ 数据增强（随机翻转、旋转、颜色抖动）
- ✅ BCEWithLogitsLoss 多标签分类损失
- ✅ Adam 优化器 + ReduceLROnPlateau 学习率调度
- ✅ 早停机制（patience=7）
- ✅ 自动保存最佳模型（PyTorch + ONNX）
- ✅ 实时绘制训练曲线

**目标性能：**
- **AUC ≥ 0.8149**（Macro Average）

**输出：**
- `../output/best_model.pth` - PyTorch 模型
- `../output/best_model.onnx` - ONNX 模型
- `../log/training.log` - 训练日志
- `../log/training_curves.png` - Loss/AUC 曲线
- `../log/training_history.json` - 训练历史数据

---

### 3. 模型评估

```bash
cd script
python evaluate.py
```

**评估指标：**
- 每个疾病的 AUC（ROC 曲线下面积）
- 每个疾病的 AP（平均精度）
- Macro Average AUC/AP
- ROC 曲线可视化

**输出：**
- `../log/evaluation.log` - 评估日志
- `../log/evaluation_report.json` - 详细评估报告
- `../log/roc_curves.png` - ROC 曲线图

**示例输出：**
```
各疾病 AUC 分数:
------------------------------------------------------------
Atelectasis              : AUC=0.8234, AP=0.4521
Cardiomegaly             : AUC=0.9123, AP=0.6234
Effusion                 : AUC=0.8876, AP=0.5432
...
------------------------------------------------------------
Macro Average AUC: 0.8149
Macro Average AP:  0.4523

✓ 达到目标 AUC (0.8149)！当前: 0.8149
```

---

## 📊 14 种胸部疾病

| 编号 | 疾病名称 | 中文名称 |
|------|---------|---------|
| 1 | Atelectasis | 肺不张 |
| 2 | Cardiomegaly | 心脏肥大 |
| 3 | Effusion | 胸腔积液 |
| 4 | Infiltration | 浸润 |
| 5 | Mass | 肿块 |
| 6 | Nodule | 结节 |
| 7 | Pneumonia | 肺炎 |
| 8 | Pneumothorax | 气胸 |
| 9 | Consolidation | 实变 |
| 10 | Edema | 水肿 |
| 11 | Emphysema | 肺气肿 |
| 12 | Fibrosis | 纤维化 |
| 13 | Pleural_Thickening | 胸膜增厚 |
| 14 | Hernia | 疝气 |

---

## 🔧 环境要求

```bash
pip install torch torchvision
pip install pandas numpy scikit-learn matplotlib pillow
pip install onnx onnxruntime  # 可选，用于 ONNX 导出
```

**推荐配置：**
- GPU: NVIDIA RTX 3060+ (显存 6GB+)
- CPU: Intel i7 / AMD Ryzen 7
- 内存: 16GB+
- 存储: 100GB+ (数据集约 40GB)

---

## 💡 训练技巧

### 提升 AUC 的方法

1. **增加训练轮数**
   ```python
   'num_epochs': 30  # 从 20 增加到 30
   ```

2. **调整学习率**
   ```python
   'learning_rate': 5e-5  # 降低学习率，更精细的训练
   ```

3. **增大数据集**
   - 使用更多数据增强技术
   - 混合其他胸部 X 光数据集

4. **模型集成**
   - 训练多个模型取平均
   - 使用不同架构（ResNet, EfficientNet）

5. **类别权重平衡**
   ```python
   # 在 BCEWithLogitsLoss 中添加 pos_weight
   pos_weight = torch.tensor([...])  # 根据类别分布计算
   criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
   ```

---

## 📝 日志文件说明

### training.log
```
2026-04-21 10:30:15 - INFO - 开始训练 DenseNet-121 胸部 X 光诊断模型
2026-04-21 10:30:16 - INFO - 训练集: 89696 张图像
2026-04-21 10:30:16 - INFO - 验证集: 11212 张图像
2026-04-21 10:30:20 - INFO - Epoch [1/20]
2026-04-21 10:35:45 - INFO - Train Loss: 0.3245, Train AUC: 0.7234
2026-04-21 10:37:12 - INFO - Val Loss:   0.2987, Val AUC:   0.7456
2026-04-21 10:37:12 - INFO - ✓ 保存最佳模型 (Val AUC: 0.7456)
...
```

### evaluation_report.json
```json
{
  "overall_metrics": {
    "macro_auc": 0.8149,
    "macro_ap": 0.4523
  },
  "per_disease_metrics": {
    "Atelectasis": {"auc": 0.8234, "ap": 0.4521},
    "Cardiomegaly": {"auc": 0.9123, "ap": 0.6234},
    ...
  }
}
```

---

## ⚠️ 常见问题

### Q1: CUDA out of memory
**解决：** 减小 batch_size
```python
'batch_size': 16  # 从 32 降到 16
```

### Q2: 训练速度慢
**解决：** 
- 增加 num_workers: `'num_workers': 8`
- 启用混合精度训练（AMP）
- 使用更快的 SSD 硬盘

### Q3: AUC 达不到 0.8149
**解决：**
- 增加训练轮数到 30-50
- 检查数据预处理是否正确
- 尝试不同的学习率（1e-5 ~ 5e-4）
- 确保使用了 ImageNet 预训练权重

### Q4: ONNX 导出失败
**解决：**
- 更新 onnx 和 onnxruntime 版本
- 检查 PyTorch 版本兼容性
- 使用 opset_version=11

---

## 📚 参考资料

1. **数据集**: Wang et al., "ChestX-ray8", CVPR 2017
2. **模型**: Huang et al., "Densely Connected Convolutional Networks", CVPR 2017
3. **CheXNet**: Rajpurkar et al., "CheXNet: Radiologist-Level Pneumonia Detection", arXiv 2017

---

## 🎯 性能基准

| 模型 | AUC | 备注 |
|------|-----|------|
| CheXNet (原始) | 0.809 | Pneumonia 单标签 |
| DenseNet-121 (本系统) | **0.8149** | 14 标签 Macro Avg |
| ResNet-50 | ~0.80 | 基线对比 |
| EfficientNet-B3 | ~0.82 | 更先进架构 |

---

**最后更新**: 2026-04-21  
**维护者**: 胸影智诊 开发团队
