# ミニカー ジョイスティック制御システム

ジョイスティック（ゲームコントローラー）でミニカーを操作し、センサーデータと操作履歴を記録するシステムです。

## 📋 目次

- [機能概要](#機能概要)
- [システム構成](#システム構成)
- [操作方法](#操作方法)
- [録画機能](#録画機能)
- [セットアップ](#セットアップ)
- [設定のカスタマイズ](#設定のカスタマイズ)
- [トラブルシューティング](#トラブルシューティング)

---

## 機能概要

このシステムでは以下のことができます：

1. **手動操作**: ジョイスティックでミニカーを直感的に操作
2. **センサー監視**: 5つの距離センサー（VL53L4CD）のリアルタイム表示
3. **データ録画**: 操作内容とセンサーデータをCSV形式で記録
4. **機械学習用データ収集**: 録画したデータを使って自動運転の学習が可能

### 用途

- **手動運転の練習**: コースを覚えたり、操作感を掴む
- **学習データ収集**: 機械学習モデルのトレーニング用データを作成
- **デバッグ**: センサーの動作確認や調整
- **コース分析**: 障害物との距離や操作のタイミングを後から分析

---

## システム構成

```
joystick_control/
├── main.py                 # メインプログラム
├── config/
│   └── settings.py         # 設定ファイル（速度、センサー、ボタン配置など）
├── modules/
│   ├── sensor.py           # センサー管理（VL53L4CD x5）
│   ├── motor.py            # モーター制御（ステアリング＋スロットル）
│   ├── joystick.py         # ジョイスティック入力処理
│   └── recorder.py         # データ録画機能
└── data/                   # 録画データ保存先（CSV）
```

### ハードウェア要件

- **Raspberry Pi**（GPIO、I2C対応）
- **距離センサー**: VL53L4CD x 5個
  - 配置: [左外、左内、正面、右内、右外]
- **モーター制御**: PCA9685（サーボ＋ESC）
- **ジョイスティック**: USB/Bluetooth接続のゲームコントローラー
  - 動作確認済み: Xbox/PlayStation互換コントローラー

---

## 操作方法

### 基本操作

| 入力 | 動作 |
|------|------|
| **左スティック（左右）** | ステアリング操作 |
| **右トリガー（RT）** | 前進（押し込み具合で速度調整） |
| **左トリガー（LT）** | 後退（押し込み具合で速度調整） |
| **何も押さない** | 自動停止 |

### ボタン操作

| ボタン | 機能 |
|--------|------|
| **Aボタン** | 録画開始 |
| **Bボタン** | 録画停止・保存 |
| **Xボタン** | 緊急停止 |
| **Ctrl+C** | プログラム終了 |

### 速度調整

トリガーの押し込み具合で速度が変わります：

- **前進（RT）**: 0.23（軽く押す）〜 0.50（全押し）
- **後退（LT）**: -0.13（軽く押す）〜 -0.25（全押し）
- **停止**: トリガーを離すと自動的に停止

---

## 録画機能

### 何が記録されるか

録画されるデータ（CSV形式）：

| 列名 | 内容 | 範囲 |
|------|------|------|
| `timestamp` | 録画開始からの経過時間（秒） | 0.000〜 |
| `steering` | ステアリング値 | -1.0（左）〜 +1.0（右） |
| `throttle` | スロットル値 | -1.0（後退）〜 +1.0（前進） |
| `L2` | 左外側センサー距離（cm） | 0〜999 |
| `L1` | 左内側センサー距離（cm） | 0〜999 |
| `C` | 正面センサー距離（cm） | 0〜999 |
| `R1` | 右内側センサー距離（cm） | 0〜999 |
| `R2` | 右外側センサー距離（cm） | 0〜999 |

### 録画の使い方

1. **プログラム起動**
   ```bash
   cd ~/minicar/joystick_control
   python main.py
   ```

2. **録画開始**: Aボタンを押す
   - 画面に `●REC` と表示される

3. **コースを走行**: ジョイスティックで操作

4. **録画停止**: Bボタンを押す
   - データが `data/record_data_YYYYMMDD_HHMMSS.csv` に保存される

### 録画データの活用例

#### 1. 機械学習の学習データ

```python
import pandas as pd

# データ読み込み
df = pd.read_csv('data/record_data_20260201_143022.csv')

# 入力: センサーデータ
X = df[['L2', 'L1', 'C', 'R1', 'R2']]

# 出力: 操作値
y_steering = df['steering']
y_throttle = df['throttle']

# 学習モデルに投入
# model.fit(X, [y_steering, y_throttle])
```

#### 2. 操作の分析

```python
import matplotlib.pyplot as plt

# ステアリングの変化を可視化
plt.plot(df['timestamp'], df['steering'])
plt.xlabel('Time (s)')
plt.ylabel('Steering')
plt.show()

# センサーと操作の関係を分析
plt.scatter(df['C'], df['throttle'])
plt.xlabel('Front Distance (cm)')
plt.ylabel('Throttle')
plt.show()
```

#### 3. コース特性の理解

- どのタイミングで減速しているか
- 壁との距離をどう保っているか
- カーブでのステアリング角度の変化

### 録画時の注意点

✅ **やること**
- 安全な場所で録画する
- データ保存先のディスク容量を確認（1分≒600行≒30KB程度）
- 複数回録画してデータのバリエーションを増やす
- 良い走行と悪い走行の両方を記録（学習の多様性）

⚠️ **気をつけること**
- 録画中でも緊急停止（Xボタン）は有効
- Ctrl+Cで終了すると録画中のデータは自動保存される
- センサーの無効値（999）が多い場合は配線やアドレスを確認
- 同じファイル名の上書きはされない（タイムスタンプで区別）

---

## セットアップ

### 1. 必要なライブラリのインストール

```bash
# Raspberry Pi上で実行
sudo apt update
sudo apt install python3-pip

pip3 install pygame adafruit-circuitpython-vl53l4cd adafruit-circuitpython-pca9685 adafruit-circuitpython-motor
```

### 2. ジョイスティックの接続確認

```bash
cd ~/minicar/test
python check_axes.py
```

軸番号を確認し、必要に応じて `config/settings.py` を調整。

### 3. センサーの動作確認

```bash
cd ~/minicar/test
python test_sensor.py
```

5つのセンサーすべてが初期化されることを確認。

### 4. プログラムの実行

```bash
cd ~/minicar/joystick_control
python main.py
```

---

## 設定のカスタマイズ

`config/settings.py` で調整可能：

### 速度の変更

```python
# 前進の範囲を変更（例: もっと速く）
THROTTLE_FORWARD_MIN = 0.25  # 最小
THROTTLE_FORWARD_MAX = 0.60  # 最大

# 後退の範囲を変更
THROTTLE_BACKWARD_MIN = -0.15
THROTTLE_BACKWARD_MAX = -0.30
```

### ステアリングの調整

```python
# サーボの角度範囲（実測値に合わせる）
SERVO_CENTER = 114  # 真っ直ぐ
SERVO_LEFT = 92     # 左
SERVO_RIGHT = 140   # 右
```

### ジョイスティックの軸番号

コントローラーによって軸の割り当てが異なる場合：

```python
AXIS_STEERING = 0        # 左スティック X軸
AXIS_TRIGGER_RIGHT = 5   # 右トリガー（前進）
AXIS_TRIGGER_LEFT = 2    # 左トリガー（後退）
```

### ボタン配置の変更

```python
BUTTON_RECORD_START = 0     # Aボタン
BUTTON_RECORD_STOP = 1      # Bボタン
BUTTON_EMERGENCY_STOP = 2   # Xボタン
```

### センサーの設定

```python
# センサーのGPIOピン（XSHUTピン）
XSHUT_PINS = [17, 27, 22, 23, 24]  # [L2, L1, C, R1, R2]

# センサーI2Cアドレスのベース
SENSOR_BASE_ADDRESS = 0x30
```

### 録画の設定

```python
# サンプリング間隔（秒）
RECORD_INTERVAL = 0.05  # 20Hz = 1秒間に20回記録

# 保存先
DATA_SAVE_PATH = "data/record_data.csv"
```

---

## トラブルシューティング

### Q1. コントローラーが認識されない

```bash
# コントローラーの接続確認
ls /dev/input/js*
# → /dev/input/js0 が表示されればOK

# Pygameで確認
python test/check_axes.py
```

### Q2. トリガーを離しても止まらない

→ `AXIS_TRIGGER_LEFT` と `AXIS_TRIGGER_RIGHT` の軸番号が間違っている可能性。  
→ `test/check_axes.py` で軸番号を確認して `settings.py` を修正。

### Q3. センサーが初期化できない

```
エラー: センサーが1つも初期化できませんでした
```

**原因と対処**:
- I2C配線の確認（SDA/SCL、電源）
- XSHUTピンの配線確認
- I2Cアドレスの競合 → `i2cdetect -y 1` で確認

### Q4. 録画ファイルが保存されない

- `data/` ディレクトリの書き込み権限を確認
- ディスク容量を確認: `df -h`
- エラーメッセージを確認

### Q5. 速度が遅い/速すぎる

→ `config/settings.py` の以下を調整:
```python
THROTTLE_FORWARD_MIN = 0.23
THROTTLE_FORWARD_MAX = 0.50  # ← ここを変更
```

少しずつ変更して安全にテスト。

### Q6. ステアリングが逆方向

→ モーター配線またはサーボの向きを確認。  
→ または `motor.py` の `set_steering()` で値を反転:
```python
def set_steering(self, value):
    value = -value  # 反転
    # ...existing code...
```

---

## ライセンス・参考

### 元になったファイル

- `test/test_sensor.py`: センサー制御の基礎
- `test/joystick.py`: ジョイスティック入力のテスト

### 開発者向け

- `modules/` 以下のモジュールは独立しているので、他のプロジェクトでも再利用可能
- センサー追加やボタン機能の拡張も容易

---

## サポート

問題が解決しない場合:
1. エラーメッセージをコピーして保存
2. `python main.py` の出力全体を確認
3. ハードウェアの配線を再確認

---

**Happy Driving! 🚗💨**