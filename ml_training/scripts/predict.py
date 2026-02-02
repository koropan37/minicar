#!/usr/bin/env python3
"""
学習済みモデルを使った予測モジュール
"""

import os
import sys
import pickle
import numpy as np

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from config.settings import (
    MODEL_SAVE_PATH, PROCESSED_DATA_PATH, MODEL_TYPE, CLASS_NAMES
)


class MLPredictor:
    """機械学習予測クラス"""
    
    def __init__(self):
        """初期化"""
        self.model = None
        self.norm_params = None
        self._load_model()
        self._load_normalization_params()
    
    def _load_model(self):
        """モデルの読み込み"""
        model_path = os.path.join(project_root, MODEL_SAVE_PATH, "model.pickle")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"モデルが見つかりません: {model_path}")
        
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)
        
        print(f"✓ モデル読み込み完了: {MODEL_TYPE}")
    
    def _load_normalization_params(self):
        """正規化パラメータの読み込み"""
        params_path = os.path.join(project_root, PROCESSED_DATA_PATH, "norm_params.npy")
        
        if not os.path.exists(params_path):
            raise FileNotFoundError(f"正規化パラメータが見つかりません: {params_path}")
        
        self.norm_params = np.load(params_path, allow_pickle=True).item()
        print(f"✓ 正規化パラメータ読み込み完了")
    
    def _normalize_sensors(self, sensor_values):
        """センサー値の正規化"""
        mean = self.norm_params['mean']
        std = self.norm_params['std']
        
        # 0除算防止
        std_safe = np.where(std == 0, 1, std)
        normalized = (sensor_values - mean) / std_safe
        
        return normalized
    
    def _class_to_steering(self, class_id):
        """クラスIDをステアリング値に変換"""
        # 各クラスの代表値（-1.0〜1.0）
        class_to_value = {
            0: -0.8,  # hard_left
            1: -0.4,  # left
            2: 0.0,   # straight
            3: 0.4,   # right
            4: 0.8,   # hard_right
        }
        return class_to_value.get(class_id, 0.0)
    
    def predict(self, l2, l1, c, r1, r2):
        """
        センサー値からステアリングを予測
        
        Args:
            l2, l1, c, r1, r2: センサー値（距離 mm）
        
        Returns:
            tuple: (steering_value, class_name)
                steering_value: -1.0〜1.0
                class_name: クラス名
        """
        # センサー値を配列に（cmに変換：学習データがcmの場合）
        # 注意: 学習データの単位に合わせる
        sensor_values = np.array([[l2/10, l1/10, c/10, r1/10, r2/10]], dtype=float)
        
        # 正規化
        normalized = self._normalize_sensors(sensor_values)
        
        # 予測
        class_id = self.model.predict(normalized)[0]
        steering = self._class_to_steering(class_id)
        
        # クラス名
        if class_id < len(CLASS_NAMES):
            class_name = CLASS_NAMES[class_id]
        else:
            class_name = f"class_{class_id}"
        
        return steering, class_name


def test_prediction():
    """予測のテスト"""
    print("=" * 50)
    print("予測テスト")
    print("=" * 50)
    
    predictor = MLPredictor()
    
    # テストケース（mm単位）
    test_cases = [
        # (L2, L1, C, R1, R2, 説明)
        (1200, 1500, 700, 400, 300, "右が近い → 左に曲がる？"),
        (300, 400, 700, 1500, 1200, "左が近い → 右に曲がる？"),
        (800, 900, 1500, 900, 800, "前方開けている → 直進？"),
        (1000, 1000, 300, 500, 400, "前方が近い → 曲がる？"),
        (600, 700, 1000, 700, 600, "バランス良い → 直進？"),
    ]
    
    print()
    for l2, l1, c, r1, r2, description in test_cases:
        steering, class_name = predictor.predict(l2, l1, c, r1, r2)
        
        print(f"センサー: L2={l2:4d} L1={l1:4d} C={c:4d} R1={r1:4d} R2={r2:4d}")
        print(f"  → {description}")
        print(f"  → 予測: steering={steering:+.2f} ({class_name})")
        print()


if __name__ == "__main__":
    test_prediction()