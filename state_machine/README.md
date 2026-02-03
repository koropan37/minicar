# 状態機械ベース走行システム

左手法（左壁沿い）でコースを周回する自律走行プログラム。

## rule_based との違い

| 項目 | rule_based | state_machine |
|------|------------|---------------|
| 制御方式 | PD制御（連続補正） | 状態遷移（離散的） |
| 判断基準 | 距離の誤差量 | センサーパターン |
| コーナー | 閾値で即判断 | 状態＋タイマーで安定 |
| 拡張性 | if-elif追加 | 状態クラス追加 |

## ディレクトリ構成

```
state_machine/
├── main.py                  # メインプログラム
├── README.md
├── config/
│   ├── __init__.py
│   └── settings.py          # 設定（パラメータ調整はここ）
└── modules/
    ├── __init__.py
    ├── sensor.py            # センサー制御
    ├── motor.py             # モーター制御
    └── state_controller.py  # 状態機械コントローラー
```

## 使用方法

```bash
cd state_machine
python main.py
```

## 状態遷移図

```
  [INIT]
     │
     v
  [WALL_FOLLOW] ←──────────────────┐
     │                             │
     ├── 前方に壁 ──> [RIGHT_TURN] ─┤
     │                             │
     ├── 左壁なし ──> [LEFT_TURN] ──┤
     │                             │
     └── 危険 ──> [EMERGENCY] ──> [RECOVER] ──┘
```

### 各状態の説明

| 状態 | 説明 | 遷移条件 |
|------|------|----------|
| WALL_FOLLOW | 左壁沿い走行 | 基本状態 |
| LEFT_TURN | 左コーナー | 左壁がなくなった |
| RIGHT_TURN | 右コーナー | 前方に壁 |
| EMERGENCY | 緊急停止 | 非常に近い障害物 |
| RECOVER | 後退復帰 | 緊急後のリカバリー |

## センサー配置

```
                    [FL]      [C]      [FR]
                      ↖       ↑        ↗
                       \      |       /
[L] ← ──────────────────────────────────────── → [R]
                       +-----------+
                       |  ミニカー  |
                       +-----------+
```

## パラメータ調整

`config/settings.py` を編集:

### 距離閾値
```python
WALL_VERY_CLOSE = 100   # 緊急停止距離 (mm)
WALL_CLOSE = 200        # 近い
WALL_FAR = 500          # 遠い
WALL_NONE = 800         # 壁なし判定
```

### 状態遷移タイマー
```python
TURN_MIN_DURATION = 0.3   # 最小旋回時間 (秒)
TURN_MAX_DURATION = 2.0   # タイムアウト (秒)
```

### 速度
```python
THROTTLE_SLOW = 0.23    # コーナー時
THROTTLE_NORMAL = 0.30  # 通常
THROTTLE_FAST = 0.38    # 直線
```

## トラブルシューティング

| 症状 | 対処法 |
|------|--------|
| コーナーで曲がりきれない | `TURN_MIN_DURATION` を増やす |
| 左コーナーを見逃す | `LEFT_CORNER_OPEN_THRESHOLD` を小さく |
| 右コーナーで突っ込む | `FRONT_BLOCKED_THRESHOLD` を大きく |
| 壁に寄りすぎる | `TARGET_LEFT_DISTANCE` を大きく |
| 状態がバタつく | 各閾値にマージンを持たせる |
