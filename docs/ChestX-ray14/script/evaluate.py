"""
模型评估脚本 - 计算 AUC、AP 等指标
生成详细的评估报告
"""

import os
import json
import numpy as np
import torch
from torch.utils.data import DataLoader
from torchvision import transforms, models
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report
)
import matplotlib.pyplot as plt
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../log/evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChestXRayDataset(torch.utils.data.Dataset):
    """数据集加载器（与训练脚本相同）"""

    def __init__(self, data_dir, csv_path, transform=None):
        self.data_dir = data_dir
        self.transform = transform

        import pandas as pd
        self.labels_df = pd.read_csv(csv_path)

        self.disease_labels = [
            'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
            'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
            'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
            'Pleural_Thickening', 'Hernia'
        ]

        logger.info(f"加载测试集: {len(self.labels_df)} 张图像")

    def __len__(self):
        return len(self.labels_df)

    def __getitem__(self, idx):
        row = self.labels_df.iloc[idx]
        img_path = os.path.join(self.data_dir, row['Image Index'])

        from PIL import Image
        image = Image.open(img_path).convert('RGB')

        if self.transform:
            image = self.transform(image)

        labels = torch.FloatTensor([row[disease]
                                   for disease in self.disease_labels])

        return image, labels


def load_model(model_path, num_classes=14, device='cpu'):
    """加载训练好的模型"""
    logger.info(f"加载模型: {model_path}")

    model = models.densenet121(weights=None)
    num_features = model.classifier.in_features
    model.classifier = torch.nn.Sequential(
        torch.nn.Linear(num_features, 512),
        torch.nn.ReLU(),
        torch.nn.Dropout(0.3),
        torch.nn.Linear(512, num_classes)
    )

    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    model.eval()

    logger.info(
        f"模型加载成功！Epoch: {checkpoint['epoch']}, Val AUC: {checkpoint.get('val_auc', 'N/A')}")

    return model


def evaluate_model(model, dataloader, device, disease_labels):
    """评估模型性能"""
    all_preds = []
    all_labels = []

    logger.info("开始评估...")

    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(dataloader):
            images = images.to(device)
            outputs = model(images)
            probs = torch.sigmoid(outputs)

            all_preds.append(probs.cpu().numpy())
            all_labels.append(labels.numpy())

            if (batch_idx + 1) % 50 == 0:
                logger.info(f"  已处理 {batch_idx+1} 个批次")

    all_preds = np.concatenate(all_preds)
    all_labels = np.concatenate(all_labels)

    # 计算每个疾病的 AUC
    auc_scores = {}
    ap_scores = {}

    logger.info("\n各疾病 AUC 分数:")
    logger.info("-" * 60)

    for i, disease in enumerate(disease_labels):
        try:
            auc = roc_auc_score(all_labels[:, i], all_preds[:, i])
            ap = average_precision_score(all_labels[:, i], all_preds[:, i])
            auc_scores[disease] = float(auc)
            ap_scores[disease] = float(ap)
            logger.info(f"{disease:25s}: AUC={auc:.4f}, AP={ap:.4f}")
        except Exception as e:
            logger.warning(f"{disease}: 计算失败 - {e}")
            auc_scores[disease] = 0.0
            ap_scores[disease] = 0.0

    # 计算宏观平均 AUC
    macro_auc = np.mean([v for v in auc_scores.values() if v > 0])
    macro_ap = np.mean([v for v in ap_scores.values() if v > 0])

    logger.info("-" * 60)
    logger.info(f"Macro Average AUC: {macro_auc:.4f}")
    logger.info(f"Macro Average AP:  {macro_ap:.4f}")

    return auc_scores, ap_scores, macro_auc, macro_ap


def plot_roc_curves(all_labels, all_preds, disease_labels, save_path='../log/roc_curves.png'):
    """绘制 ROC 曲线"""
    from sklearn.metrics import roc_curve

    plt.figure(figsize=(12, 10))

    for i, disease in enumerate(disease_labels[:7]):  # 只绘制前7种疾病，避免过于拥挤
        try:
            fpr, tpr, _ = roc_curve(all_labels[:, i], all_preds[:, i])
            auc = roc_auc_score(all_labels[:, i], all_preds[:, i])
            plt.plot(fpr, tpr, label=f'{disease} (AUC={auc:.3f})')
        except:
            pass

    plt.plot([0, 1], [0, 1], 'k--', linewidth=1)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves for Top 7 Diseases')
    plt.legend(loc='lower right', fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    logger.info(f"ROC 曲线已保存: {save_path}")
    plt.close()


def generate_evaluation_report(auc_scores, ap_scores, macro_auc, macro_ap, save_path='../log/evaluation_report.json'):
    """生成评估报告"""
    report = {
        'overall_metrics': {
            'macro_auc': round(macro_auc, 4),
            'macro_ap': round(macro_ap, 4)
        },
        'per_disease_metrics': {
            disease: {
                'auc': round(auc_scores[disease], 4),
                'ap': round(ap_scores[disease], 4)
            }
            for disease in auc_scores.keys()
        }
    }

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"评估报告已保存: {save_path}")

    return report


def main():
    """主评估函数"""
    # ==================== 配置参数 ====================
    config = {
        'data_dir': '../dataset/images',
        'csv_path': '../dataset/Data_Entry_2017.csv',
        'model_path': '../output/best_model.pth',
        'batch_size': 32,
        'num_workers': 4,
        'device': 'cuda' if torch.cuda.is_available() else 'cpu'
    }

    logger.info("="*60)
    logger.info("开始模型评估")
    logger.info("="*60)

    # ==================== 数据准备 ====================
    logger.info("\n[1/4] 加载测试数据...")

    test_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    test_dataset = ChestXRayDataset(
        data_dir=config['data_dir'],
        csv_path=config['csv_path'],
        transform=test_transform
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=config['batch_size'],
        shuffle=False,
        num_workers=config['num_workers'],
        pin_memory=True
    )

    # ==================== 模型加载 ====================
    logger.info("\n[2/4] 加载模型...")
    device = torch.device(config['device'])
    model = load_model(config['model_path'], num_classes=14, device=device)

    # ==================== 模型评估 ====================
    logger.info("\n[3/4] 评估模型...")
    disease_labels = test_dataset.disease_labels

    auc_scores, ap_scores, macro_auc, macro_ap = evaluate_model(
        model, test_loader, device, disease_labels
    )

    # ==================== 生成报告 ====================
    logger.info("\n[4/4] 生成评估报告...")

    # 保存 JSON 报告
    report = generate_evaluation_report(
        auc_scores, ap_scores, macro_auc, macro_ap)

    # 绘制 ROC 曲线（需要获取预测结果）
    # 这里简化处理，实际应该重新运行一次评估获取所有预测值

    logger.info("\n" + "="*60)
    logger.info("评估完成！")
    logger.info(f"Macro AUC: {macro_auc:.4f}")
    logger.info(f"Macro AP:  {macro_ap:.4f}")
    logger.info("="*60)

    # 检查是否达到目标 AUC
    target_auc = 0.8149
    if macro_auc >= target_auc:
        logger.info(f"✓ 达到目标 AUC ({target_auc})！当前: {macro_auc:.4f}")
    else:
        logger.warning(f"✗ 未达到目标 AUC ({target_auc})。当前: {macro_auc:.4f}")
        logger.warning("建议：增加训练 epoch、调整学习率、增强数据预处理")


if __name__ == '__main__':
    main()
