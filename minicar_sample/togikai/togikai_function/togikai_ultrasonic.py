#障害物センサ測定関数
def Mesure(GPIO,time,trig,echo):
    dis = 0
    n = 1
    for i in range(n):
        sigoff = 0 #low(ピンの立ち上がり直前)
        sigon = 0 #high(ピンの立ち上がり直後)
        GPIO.output(trig,GPIO.HIGH) #センサの発信準備
        time.sleep(0.00001) #10µs 以上で発信
        GPIO.output(trig,GPIO.LOW) #low に戻す
        kijyun=time.time()
        while(GPIO.input(echo)==GPIO.LOW):
            sigoff=time.time()
            if sigoff - kijyun > 0.02:
            #     print("break1")
                 break
        while(GPIO.input(echo)==GPIO.HIGH):
            sigon=time.time()
            if sigon - sigoff > 0.02:
            #     print("break2")
                 break
        d = (sigon - sigoff)*34000/2
        if d > 200:
            dis += 200/n
        else:
            dis += d/n
    return dis

# 1.trig に短いパルスを送る（発信）。
# 2.echo が HIGH になる（立ち上がり）→ 音波を戻り側で受け取り始めた合図。
# 3.echo が LOW になる（立ち下がり）→ 受信終了。
# 4.立ち上がりから立ち下がりまでの時間（パルス幅）が音が往復する時間なので、距離 = (パルス幅[s] * 音速[m/s]) / 2 で求める。

# センサが変わるなら実装の変換が必須
# 赤外アナログセンサ (例：Sharp)：アナログ出力 → ADC (MCP3008 等) が必要。ADC 読み取り→電圧→距離変換（キャリブレーション必須）。
# デジタル赤外（デジタル近接）：単純 HIGH/LOW → API を少し変える可能性あり（boolean や閾値）。