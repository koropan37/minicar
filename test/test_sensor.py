import time
import board
import adafruit_vl53l4cd

# I2C接続（ラズパイの標準ピンを使用）
i2c = board.I2C()

# センサーを初期化
vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)

# 精度を上げる設定 (タイミングバジェット)
# デフォルトは速さ優先ですが、これを増やすと速度は落ちますが安定します
#vl53.inter_measurement = 0
#vl53.timing_budget = 200 # 単位はミリ秒 (デフォルトはもっと短い)

vl53.start_ranging()
# 測定開始
vl53.start_ranging()
print("測定を開始します (Ctrl+Cで終了)")

try:
    while True:
        # データが来るまで待機
        while not vl53.data_ready:
            pass
            
        # 割り込みをクリアしてデータを取得
        vl53.clear_interrupt()
        
        # 距離を表示
        print(f"距離: {vl53.distance:.2f} cm")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n終了します")