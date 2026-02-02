#!/usr/bin/env python3
"""
正規化パラメータと学習データの統計を確認
"""

import os
import sys
import numpy as np

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import PROCESSED_DATA_PATH

# データ読み込み
X_train = np.load(f"{project_root}/{PROCESSED_DATA_PATH}/X_train.npy")
norm_params = np.load(f"{project_root}/{PROCESSED_DATA_PATH}/norm_params.npy", allow_pickle=True).item()

print("=" * 50)
print("学習データの統計")
print("=" * 50)
print(f"\nデータ数: {len(X_train)}")
print(f"\nセンサー値の範囲（cm）:")
print(f"  L2  : {X_train[:, 0].min():.1f} 〜 {X_train[:, 0].max():.1f}")
print(f"  L1  : {X_train[:, 1].min():.1f} 〜 {X_train[:, 1].max():.1f}")
print(f"  C   : {X_train[:, 2].min():.1f} 〜 {X_train[:, 2].max():.1f}")
print(f"  R1  : {X_train[:, 3].min():.1f} 〜 {X_train[:, 3].max():.1f}")
print(f"  R2  : {X_train[:, 4].min():.1f} 〜 {X_train[:, 4].max():.1f}")

print(f"\n正規化パラメータ:")
print(f"  Mean: {norm_params['mean']}")
print(f"  Std : {norm_params['std']}")

# サンプルデータで正規化をテスト
print("\n" + "=" * 50)
print("正規化のテスト（学習データの最初の3行）")
print("=" * 50)
for i in range(min(3, len(X_train))):
    original = X_train[i]
    normalized = (original - norm_params['mean']) / norm_params['std']
    print(f"\n[{i+1}] 元データ: {original}")
    print(f"    正規化後: {normalized}")