import os
import sys
sys.path.append('/home/pi/togikai/togikai_function/')
import togikai_ultrasonic
import signal
import RPi.GPIO as GPIO
import Adafruit_PCA9685
import time
import numpy as np#障害物センサ測定関数

GPIO.setmode(GPIO.BOARD)
#初期設定
t_list=[15,13,35,32,36]
GPIO.setup(t_list,GPIO.OUT,initial=GPIO.LOW)
e_list=[26,24,37,31,38]
GPIO.setup(e_list,GPIO.IN)

#データ記録用配列作成
d = np.zeros(2)
# print('Input test name')
# test = input()
# print('Input No.')
# testno = input()
# filename = '/home/pi/code/record_data/'+str(test)+str(testno)+'.csv'
start_time = time.time()

if __name__ == "__main__":
    try:
        for i in range(100):
            dis = togikai_ultrasonic.Mesure(GPIO,time,15,26)
            #距離データを配列に記録
            d = np.vstack([d,[time.time()-start_time, dis]])
            print('{0:.2f}'.format(dis))
            time.sleep(0.1)
        GPIO.cleanup()
        # np.savetxt(filename, d, fmt='%.3e')
        print('average = ', np.mean(d[:,1]))

    except KeyboardInterrupt:
        # np.savetxt(filename, d, fmt='%.3e')
        print('stop!')
        GPIO.cleanup()


#togikai_ultrasonic.Mesure(GPIO, time, trig, echo) を呼んで距離を取得。
#GPIO モードを BOARD に設定し、複数の trig/e​​cho ピンを初期化。
#取得値を numpy 配列に積み上げて表示（'{0:.2f}' で小数 2 桁表示）、0.1s 間隔でループ、最後に GPIO.cleanup()。
#ファイル先頭で sys.path を追加して togikai_function をインポートしている。
#車体に複数の超音波センサ（前・左右・後ろなど）を置いていて、それぞれ別ピンに接続しているため。
#個々のセンサを個別にテスト・記録したい（故障診断やキャリブレーション）が目的。
# これらのロジックはセンサが違くても使えそう？