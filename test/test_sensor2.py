import time
import board
import adafruit_vl53l4cd

# I2C接続（ラズパイの標準ピンを使用）
i2c = board.I2C()

# センサーを初期化
vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)
# 安定化: timing_budget を設定し、それ以上の inter_measurement にする
vl53.timing_budget = 50      # ms（測定に要する時間）
vl53.inter_measurement = 60  # ms（次の測定までの待ち時間） >= timing_budget

# 測定開始は1回だけ
vl53.start_ranging()
print("測定を開始します (Ctrl+Cで終了)")

# 起動直後に「何もない」状態でベースラインを測る（例: 1秒間）
def measure_baseline(samples=10, delay=0.05):
    vals = []
    for _ in range(samples):
        while not vl53.data_ready:
            pass
        vl53.clear_interrupt()
        v = vl53.distance
        if v != 0:
            vals.append(v)
        time.sleep(delay)
    return 0.0 if not vals else sorted(vals)[len(vals)//2]  # 中央値

baseline = measure_baseline()
THRESH = 10.0  # baseline + この閾値(cm) を超えたら対象あり（適宜調整）
print(f"baseline={baseline:.2f} cm, threshold={THRESH:.2f} cm")

from collections import deque
buf = deque(maxlen=5)

try:
    while True:
        while not vl53.data_ready:
            pass

        vl53.clear_interrupt()
        # ライブラリが提供するステータスを取得（存在すれば）
        status = getattr(vl53, "range_status", None)
        d = vl53.distance

        # ステータス表示用文字列
        status_str = "N/A" if status is None else str(status)

        # ステータスが取得できて、0（OK）でなければスキップして表示
        if status is not None and status != 0:
            print(f"ステータス: {status_str} (異常) をスキップ — 距離: {d:.2f} cm")
            time.sleep(0.05)
            continue

        # 0（無効）やベースライン内の値はスキップ（ステータス含め表示）
        if d == 0 or d <= baseline + THRESH:
            print(f"ステータス: {status_str} 対象なし/無効 — 距離: {d:.2f} cm")
            time.sleep(0.05)
            continue

        buf.append(d)
        avg = sum(buf) / len(buf)
        print(f"ステータス: {status_str} 距離: {d:.2f} cm    平均: {avg:.2f} cm")

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n終了します")

finally:
    try:
        vl53.stop_ranging()
    except Exception:
        pass