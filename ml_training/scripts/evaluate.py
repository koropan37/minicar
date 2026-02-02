#!/usr/bin/env python3
"""
学習済みモデルの評価スクリプト
"""

import os
import sys
import pickle
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import (
    PROCESSED_DATA_PATH, MODEL_SAVE_PATH, MODEL_TYPE,
    STEER_THRESHOLDS, CLASS_NAMES
)


def convert_steering_to_class(y_steering):
    """ステアリング値をクラスに変換"""
    classes = []
    for value in y_steering.flatten():
        if value < STEER_THRESHOLDS["hard_left"]:
            classes.append(0)  # hard_left
        elif value < STEER_THRESHOLDS["left"]:
            classes.append(1)  # left
        elif value < STEER_THRESHOLDS["straight"]:
            classes.append(2)  # straight
        elif value < STEER_THRESHOLDS["right"]:
            classes.append(3)  # right
        else:
            classes.append(4)  # hard_right
    
    return np.array(classes)


def convert_class_to_steering(y_class):
    """クラスをステアリング値に逆変換（可視化用）"""
    # 各クラスの中央値を使用
    class_to_value = {
        0: -0.8,  # hard_left
        1: -0.4,  # left
        2: 0.0,   # straight
        3: 0.4,   # right
        4: 0.8,   # hard_right
    }
    return np.array([class_to_value[c] for c in y_class])


def evaluate_classifier(model, X, y_true_continuous):
    """分類器の評価"""
    print("=" * 50)
    print("分類器の評価")
    print("=" * 50)
    
    # 連続値をクラスに変換
    y_true = convert_steering_to_class(y_true_continuous)
    
    # 予測
    y_pred = model.predict(X)
    
    # 精度
    accuracy = model.score(X, y_true)
    print(f"\n全体精度: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # クラスごとの詳細レポート
    print("\n" + "=" * 50)
    print("クラスごとの性能")
    print("=" * 50)
    report = classification_report(y_true, y_pred, target_names=CLASS_NAMES, zero_division=0)
    print(report)
    
    # 混同行列
    cm = confusion_matrix(y_true, y_pred)
    
    # 混同行列のプロット
    fig, ax = plt.subplots(figsize=(10, 8))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=CLASS_NAMES)
    disp.plot(ax=ax, cmap='Blues', values_format='d')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    
    # 保存
    os.makedirs('results', exist_ok=True)
    plt.savefig('results/confusion_matrix.png', dpi=150, bbox_inches='tight')
    print("\n混同行列を保存: results/confusion_matrix.png")
    
    # 予測分布の可視化
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # 真値の分布
    axes[0].hist(y_true, bins=5, range=(-0.5, 4.5), alpha=0.7, label='True')
    axes[0].set_xlabel('Class')
    axes[0].set_ylabel('Count')
    axes[0].set_title('True Class Distribution')
    axes[0].set_xticks(range(5))
    axes[0].set_xticklabels(CLASS_NAMES, rotation=45)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 予測値の分布
    axes[1].hist(y_pred, bins=5, range=(-0.5, 4.5), alpha=0.7, color='orange', label='Predicted')
    axes[1].set_xlabel('Class')
    axes[1].set_ylabel('Count')
    axes[1].set_title('Predicted Class Distribution')
    axes[1].set_xticks(range(5))
    axes[1].set_xticklabels(CLASS_NAMES, rotation=45)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/class_distribution.png', dpi=150, bbox_inches='tight')
    print("クラス分布を保存: results/class_distribution.png")
    
    # サンプル予測の表示
    print("\n" + "=" * 50)
    print("サンプル予測（最初の10件）")
    print("=" * 50)
    print(f"{'True Class':<15} {'Pred Class':<15} {'Match':<10}")
    print("-" * 40)
    for i in range(min(10, len(y_true))):
        true_name = CLASS_NAMES[y_true[i]]
        pred_name = CLASS_NAMES[y_pred[i]]
        match = "✓" if y_true[i] == y_pred[i] else "✗"
        print(f"{true_name:<15} {pred_name:<15} {match:<10}")
    
    plt.show()


def evaluate_regressor(model, X, y_true):
    """回帰器の評価"""
    print("=" * 50)
    print("回帰器の評価")
    print("=" * 50)
    
    # 予測
    y_pred = model.predict(X)
    
    # R2スコア
    r2 = model.score(X, y_true)
    print(f"\nR2スコア: {r2:.4f}")
    
    # MAE/RMSE
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    print(f"MAE: {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    
    # 散布図
    plt.figure(figsize=(10, 6))
    plt.scatter(y_true, y_pred, alpha=0.5)
    plt.plot([-1, 1], [-1, 1], 'r--', label='Perfect Prediction')
    plt.xlabel('True Value')
    plt.ylabel('Predicted Value')
    plt.title('True vs Predicted')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    os.makedirs('results', exist_ok=True)
    plt.savefig('results/regression_scatter.png', dpi=150, bbox_inches='tight')
    print("\n散布図を保存: results/regression_scatter.png")
    
    plt.show()


def main():
    print("=" * 50)
    print("モデル評価")
    print("=" * 50)
    
    # データ読み込み
    X = np.load(f"{PROCESSED_DATA_PATH}/X_train.npy")
    y = np.load(f"{PROCESSED_DATA_PATH}/y_train.npy")
    
    print(f"データサイズ: X={X.shape}, y={y.shape}")
    
    # モデル読み込み
    model_path = f"{MODEL_SAVE_PATH}/model.pickle"
    
    if not os.path.exists(model_path):
        print(f"エラー: モデルが見つかりません: {model_path}")
        print("先に train.py を実行してください。")
        return
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    print(f"モデル読み込み: {model_path}")
    print(f"モデルタイプ: {MODEL_TYPE}")
    print()
    
    # モデルタイプに応じた評価
    if MODEL_TYPE == "mlp_classifier" or MODEL_TYPE == "random_forest":
        evaluate_classifier(model, X, y)
    elif MODEL_TYPE == "mlp_regressor":
        evaluate_regressor(model, X, y)
    else:
        print(f"エラー: 不明なモデルタイプ: {MODEL_TYPE}")


if __name__ == "__main__":
    main()
