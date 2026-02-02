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


def convert_steering_to_class(y_steering):
    """ステアリング値をクラスに変換"""
    from config.settings import STEER_THRESHOLDS
    
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


def main():
    print("=" * 50)
    print("モデル学習を開始")
    print("=" * 50)
    
    # データ読み込み
    X_train_full = np.load(f"{PROCESSED_DATA_PATH}/X_train.npy")
    y_train_full = np.load(f"{PROCESSED_DATA_PATH}/y_train.npy")
    
    print(f"データサイズ: X={X_train_full.shape}, y={y_train_full.shape}")
    
    # データ分割
    X_train, X_test, y_train, y_test = train_test_split(
        X_train_full, y_train_full,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE
    )
    
    print(f"学習データ: {len(X_train)}件")
    print(f"テストデータ: {len(X_test)}件")
    print()
    
    # モデル作成
    print(f"モデルタイプ: {MODEL_TYPE}")
    
    if MODEL_TYPE == "mlp_classifier":
        # 分類器の場合、連続値をクラスに変換
        y_train_class = convert_steering_to_class(y_train)
        y_test_class = convert_steering_to_class(y_test)
        
        model = MLPClassifier(
            hidden_layer_sizes=HIDDEN_LAYERS,
            max_iter=MAX_ITER,
            random_state=RANDOM_STATE,
            verbose=True
        )
        model.fit(X_train, y_train_class)
        
        # 評価
        train_score = model.score(X_train, y_train_class)
        test_score = model.score(X_test, y_test_class)
        
    elif MODEL_TYPE == "mlp_regressor":
        model = MLPRegressor(
            hidden_layer_sizes=HIDDEN_LAYERS,
            max_iter=MAX_ITER,
            random_state=RANDOM_STATE,
            verbose=True
        )
        model.fit(X_train, y_train)
        
        # 評価
        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)
        
    elif MODEL_TYPE == "random_forest":
        # Random Forestの場合も分類
        y_train_class = convert_steering_to_class(y_train)
        y_test_class = convert_steering_to_class(y_test)
        
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(
            n_estimators=100,
            random_state=RANDOM_STATE,
            verbose=1
        )
        model.fit(X_train, y_train_class)
        
        # 評価
        train_score = model.score(X_train, y_train_class)
        test_score = model.score(X_test, y_test_class)
    
    else:
        raise ValueError(f"不明なモデルタイプ: {MODEL_TYPE}")
    
    print()
    print(f"学習データスコア: {train_score:.4f}")
    print(f"テストデータスコア: {test_score:.4f}")
    print()
    
    # モデル保存
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    model_path = f"{MODEL_SAVE_PATH}/model.pickle"
    
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    
    print(f"モデル保存完了: {model_path}")


if __name__ == "__main__":
    main()
