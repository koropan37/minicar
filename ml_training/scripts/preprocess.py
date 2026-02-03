"""
データ前処理スクリプト
生データを学習用に加工する
"""

import os
import glob
import numpy as np
import pandas as pd
import sys
from sklearn.model_selection import train_test_split

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    RAW_DATA_PATH, PROCESSED_DATA_PATH, CSV_COLUMNS,
    SENSOR_COLUMNS, TARGET_COLUMNS, SENSOR_INVALID,
    SENSOR_MIN, SENSOR_MAX, NORMALIZATION, TEST_SIZE, RANDOM_STATE
)


def load_raw_data(raw_path):
    """生データを読み込んで結合"""
    csv_files = glob.glob(os.path.join(raw_path, "*.csv"))
    
    if not csv_files:
        print(f"エラー: {raw_path} にCSVファイルがありません")
        return None
    
    print(f"読み込むファイル数: {len(csv_files)}")
    
    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        df['source_file'] = os.path.basename(f)
        dfs.append(df)
        print(f"  - {os.path.basename(f)}: {len(df)}行")
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"合計: {len(combined)}行")
    return combined


def clean_data(df):
    """データのクリーニング"""
    original_len = len(df)
    
    # 無効なセンサー値を含む行を削除
    for col in SENSOR_COLUMNS:
        df = df[df[col] != SENSOR_INVALID]
        df = df[(df[col] >= SENSOR_MIN) & (df[col] <= SENSOR_MAX)]
    
    # NaNを削除
    df = df.dropna()
    
    print(f"クリーニング: {original_len}行 → {len(df)}行")
    return df


def normalize_data(df):
    """センサー値を正規化"""
    X = df[SENSOR_COLUMNS].values
    
    if NORMALIZATION == "standard":
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        X_norm = (X - mean) / std
        norm_params = {"mean": mean, "std": std}
    else:  # minmax
        min_val = np.min(X, axis=0)
        max_val = np.max(X, axis=0)
        X_norm = (X - min_val) / (max_val - min_val)
        norm_params = {"min": min_val, "max": max_val}
    
    return X_norm, norm_params


def main():
    print("=" * 50)
    print("データ前処理を開始")
    print("=" * 50)
    
    # 生データ読み込み
    df = load_raw_data(RAW_DATA_PATH)
    if df is None:
        return
    
    # クリーニング
    df = clean_data(df)
    
    # 特徴量とターゲットを分離
    X_all = df[SENSOR_COLUMNS].values
    y_all = df[TARGET_COLUMNS].values
    
    # 正規化パラメータを計算
    mean = X_all.mean(axis=0)
    std = X_all.std(axis=0)
    
    # 正規化パラメータを保存
    norm_params = {'mean': mean, 'std': std}
    np.save(f"{PROCESSED_DATA_PATH}/norm_params.npy", norm_params)
    print(f"正規化パラメータ保存: norm_params.npy")
    
    # ⚠️ ここでは正規化せずに保存
    # X_normalized = (X_all - mean) / (std + 1e-8)  ← コメントアウト
    
    # データ分割
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all,  # ← 正規化前のデータを使う
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE
    )
    
    # 保存（正規化前）
    np.save(f"{PROCESSED_DATA_PATH}/X_train.npy", X_train)
    np.save(f"{PROCESSED_DATA_PATH}/X_test.npy", X_test)
    np.save(f"{PROCESSED_DATA_PATH}/y_train.npy", y_train)
    np.save(f"{PROCESSED_DATA_PATH}/y_test.npy", y_test)
    
    print(f"\nX_train: {X_train.shape}")
    print(f"X_test:  {X_test.shape}")
    print(f"y_train: {y_train.shape}")
    print(f"y_test:  {y_test.shape}")
    
    print("\n前処理完了！")


if __name__ == "__main__":
    main()
