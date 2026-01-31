"""
モデル学習スクリプト
前処理済みデータを使ってモデルを学習
"""

import os
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    PROCESSED_DATA_PATH, MODEL_SAVE_PATH, MODEL_TYPE,
    HIDDEN_LAYERS, MAX_ITER, RANDOM_STATE, TEST_SIZE
)


def load_processed_data():
    """前処理済みデータを読み込み"""
    X = np.load(os.path.join(PROCESSED_DATA_PATH, "X_train.npy"))
    y = np.load(os.path.join(PROCESSED_DATA_PATH, "y_train.npy"))
    norm_params = np.load(os.path.join(PROCESSED_DATA_PATH, "norm_params.npy"), allow_pickle=True).item()
    return X, y, norm_params


def create_model(model_type):
    """モデルを作成"""
    if model_type == "mlp_classifier":
        return MLPClassifier(
            hidden_layer_sizes=HIDDEN_LAYERS,
            max_iter=MAX_ITER,
            random_state=RANDOM_STATE,
            verbose=True
        )
    elif model_type == "mlp_regressor":
        return MLPRegressor(
            hidden_layer_sizes=HIDDEN_LAYERS,
            max_iter=MAX_ITER,
            random_state=RANDOM_STATE,
            verbose=True
        )
    elif model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=100,
            random_state=RANDOM_STATE,
            verbose=1
        )
    else:
        raise ValueError(f"未対応のモデルタイプ: {model_type}")


def main():
    print("=" * 50)
    print("モデル学習を開始")
    print("=" * 50)
    
    # データ読み込み
    X, y, norm_params = load_processed_data()
    print(f"データサイズ: X={X.shape}, y={y.shape}")
    
    # yが2次元で1列の場合は1次元に変換
    if len(y.shape) > 1 and y.shape[1] == 1:
        y = y.ravel()
    
    # 学習/テストデータに分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    print(f"学習データ: {X_train.shape[0]}件")
    print(f"テストデータ: {X_test.shape[0]}件")
    
    # モデル作成・学習
    print(f"\nモデルタイプ: {MODEL_TYPE}")
    model = create_model(MODEL_TYPE)
    model.fit(X_train, y_train)
    
    # 評価
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"\n学習データスコア: {train_score:.4f}")
    print(f"テストデータスコア: {test_score:.4f}")
    
    # モデル保存
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    model_path = os.path.join(MODEL_SAVE_PATH, "model.pickle")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # 正規化パラメータも保存
    np.save(os.path.join(MODEL_SAVE_PATH, "norm_params.npy"), norm_params)
    
    print(f"\nモデル保存完了: {model_path}")


if __name__ == "__main__":
    main()
