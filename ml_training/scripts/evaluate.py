"""
モデル評価スクリプト
学習済みモデルの性能を可視化・評価
"""

import os
import pickle
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import PROCESSED_DATA_PATH, MODEL_SAVE_PATH


def load_model():
    """学習済みモデルを読み込み"""
    model_path = os.path.join(MODEL_SAVE_PATH, "model.pickle")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    norm_params = np.load(os.path.join(MODEL_SAVE_PATH, "norm_params.npy"), allow_pickle=True).item()
    return model, norm_params


def load_data():
    """評価用データを読み込み"""
    X = np.load(os.path.join(PROCESSED_DATA_PATH, "X_train.npy"))
    y = np.load(os.path.join(PROCESSED_DATA_PATH, "y_train.npy"))
    if len(y.shape) > 1 and y.shape[1] == 1:
        y = y.ravel()
    return X, y


def evaluate_and_plot(model, X, y):
    """評価と可視化"""
    # 予測
    y_pred = model.predict(X)
    
    # 評価指標
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    r2 = model.score(X, y)
    
    print("=" * 50)
    print("評価結果")
    print("=" * 50)
    print(f"MSE (平均二乗誤差): {mse:.4f}")
    print(f"MAE (平均絶対誤差): {mae:.4f}")
    print(f"R² スコア: {r2:.4f}")
    
    # プロット
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    # 1. 実際 vs 予測
    axes[0].scatter(y, y_pred, alpha=0.5, s=10)
    axes[0].plot([-1, 1], [-1, 1], 'r--', label='理想')
    axes[0].set_xlabel('実際のステアリング')
    axes[0].set_ylabel('予測のステアリング')
    axes[0].set_title('実際 vs 予測')
    axes[0].legend()
    axes[0].set_xlim(-1.1, 1.1)
    axes[0].set_ylim(-1.1, 1.1)
    
    # 2. 誤差分布
    errors = y - y_pred
    axes[1].hist(errors, bins=50, edgecolor='black')
    axes[1].set_xlabel('誤差')
    axes[1].set_ylabel('頻度')
    axes[1].set_title(f'誤差分布 (MAE={mae:.3f})')
    axes[1].axvline(0, color='r', linestyle='--')
    
    # 3. 時系列比較（最初の500点）
    n_points = min(500, len(y))
    axes[2].plot(range(n_points), y[:n_points], label='実際', alpha=0.7)
    axes[2].plot(range(n_points), y_pred[:n_points], label='予測', alpha=0.7)
    axes[2].set_xlabel('サンプル')
    axes[2].set_ylabel('ステアリング')
    axes[2].set_title('時系列比較')
    axes[2].legend()
    
    plt.tight_layout()
    
    # 保存
    plot_path = os.path.join(MODEL_SAVE_PATH, "evaluation.png")
    plt.savefig(plot_path, dpi=150)
    print(f"\nグラフを保存: {plot_path}")
    plt.show()


def main():
    model, norm_params = load_model()
    X, y = load_data()
    evaluate_and_plot(model, X, y)


if __name__ == "__main__":
    main()
