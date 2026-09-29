"""
数据预处理脚本
- 检查数据集完整性
- 生成训练/验证/测试集划分
- 统计类别分布
"""

import os
import pandas as pd
import numpy as np
from PIL import Image
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../log/preprocessing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def check_dataset_integrity(data_dir, csv_path):
    """检查数据集完整性"""
    logger.info("="*60)
    logger.info("检查数据集完整性")
    logger.info("="*60)

    # 读取标签文件
    df = pd.read_csv(csv_path)
    logger.info(f"标签文件包含 {len(df)} 条记录")

    # 检查图像文件是否存在
    missing_images = []
    invalid_images = []

    for idx, row in df.iterrows():
        img_path = os.path.join(data_dir, row['Image Index'])

        if not os.path.exists(img_path):
            missing_images.append(row['Image Index'])
        else:
            try:
                with Image.open(img_path) as img:
                    img.verify()
            except Exception as e:
                invalid_images.append((row['Image Index'], str(e)))

        if (idx + 1) % 10000 == 0:
            logger.info(f"  已检查 {idx+1}/{len(df)} 张图像...")

    logger.info(f"\n检查结果:")
    logger.info(f"  缺失图像: {len(missing_images)} 张")
    logger.info(f"  损坏图像: {len(invalid_images)} 张")

    if missing_images:
        logger.warning(f"前10个缺失图像: {missing_images[:10]}")

    if invalid_images:
        logger.warning(f"前10个损坏图像: {invalid_images[:10]}")

    return len(missing_images), len(invalid_images)


def analyze_class_distribution(csv_path):
    """分析类别分布"""
    logger.info("\n" + "="*60)
    logger.info("分析类别分布")
    logger.info("="*60)

    df = pd.read_csv(csv_path)

    disease_labels = [
        'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
        'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
        'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
        'Pleural_Thickening', 'Hernia'
    ]

    logger.info(f"\n{'疾病名称':25s} {'阳性样本数':>10s} {'占比':>8s}")
    logger.info("-" * 50)

    total_samples = len(df)

    for disease in disease_labels:
        positive_count = df[disease].sum()
        percentage = (positive_count / total_samples) * 100
        logger.info(f"{disease:25s} {positive_count:10d} {percentage:7.2f}%")

    # 统计无疾病样本
    no_finding_count = len(df[df[disease_labels].sum(axis=1) == 0])
    logger.info("-" * 50)
    logger.info(
        f"{'No Finding':25s} {no_finding_count:10d} {(no_finding_count/total_samples)*100:7.2f}%")

    return df


def split_dataset(csv_path, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """划分训练集、验证集、测试集"""
    logger.info("\n" + "="*60)
    logger.info("划分数据集")
    logger.info("="*60)

    df = pd.read_csv(csv_path)

    # 随机打乱
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)

    total = len(df_shuffled)
    train_end = int(total * train_ratio)
    val_end = int(total * (train_ratio + val_ratio))

    train_df = df_shuffled[:train_end]
    val_df = df_shuffled[train_end:val_end]
    test_df = df_shuffled[val_end:]

    logger.info(f"训练集: {len(train_df)} 张 ({train_ratio*100:.0f}%)")
    logger.info(f"验证集: {len(val_df)} 张 ({val_ratio*100:.0f}%)")
    logger.info(f"测试集: {len(test_df)} 张 ({test_ratio*100:.0f}%)")

    # 保存划分结果
    output_dir = '../dataset/splits'
    os.makedirs(output_dir, exist_ok=True)

    train_df.to_csv(os.path.join(output_dir, 'train.csv'), index=False)
    val_df.to_csv(os.path.join(output_dir, 'val.csv'), index=False)
    test_df.to_csv(os.path.join(output_dir, 'test.csv'), index=False)

    logger.info(f"划分文件已保存到: {output_dir}")

    return train_df, val_df, test_df


def generate_statistics_report(df, save_path='../log/dataset_statistics.txt'):
    """生成数据统计报告"""
    logger.info("\n生成数据统计报告...")

    disease_labels = [
        'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
        'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
        'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
        'Pleural_Thickening', 'Hernia'
    ]

    report_lines = []
    report_lines.append("="*60)
    report_lines.append("ChestX-ray14 数据集统计报告")
    report_lines.append("="*60)
    report_lines.append("")
    report_lines.append(f"总样本数: {len(df)}")
    report_lines.append("")
    report_lines.append("类别分布:")
    report_lines.append("-"*60)

    total_samples = len(df)

    for disease in disease_labels:
        positive_count = df[disease].sum()
        percentage = (positive_count / total_samples) * 100
        report_lines.append(
            f"{disease:25s}: {positive_count:6d} ({percentage:5.2f}%)")

    no_finding_count = len(df[df[disease_labels].sum(axis=1) == 0])
    report_lines.append("-"*60)
    report_lines.append(
        f"{'No Finding':25s}: {no_finding_count:6d} ({(no_finding_count/total_samples)*100:5.2f}%)")
    report_lines.append("")
    report_lines.append(
        f"平均每张图像的标签数: {df[disease_labels].sum(axis=1).mean():.2f}")
    report_lines.append(
        f"多标签样本比例: {(df[disease_labels].sum(axis=1) > 1).sum() / total_samples * 100:.2f}%")

    report_text = "\n".join(report_lines)

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    logger.info(f"统计报告已保存: {save_path}")
    logger.info("\n" + report_text)


def main():
    """主函数"""
    data_dir = '../dataset/images'
    csv_path = '../dataset/Data_Entry_2017.csv'

    # 1. 检查数据集完整性
    missing, invalid = check_dataset_integrity(data_dir, csv_path)

    # 2. 分析类别分布
    df = analyze_class_distribution(csv_path)

    # 3. 划分数据集
    train_df, val_df, test_df = split_dataset(csv_path)

    # 4. 生成统计报告
    generate_statistics_report(df)

    logger.info("\n" + "="*60)
    logger.info("数据预处理完成！")
    logger.info("="*60)


if __name__ == '__main__':
    main()
