import os
import sys
import RPi.GPIO as GPIO
import Adafruit_PCA9685
import time
import numpy as np
import smbus            # use I2C
import math
from time import sleep  # time module

def writetofile(path,STEERING_RIGHT_PWM,STEERING_CENTER_PWM,STEERING_LEFT_PWM,THROTTLE_FORWARD_PWM,THROTTLE_STOPPED_PWM,THROTTLE_REVERSE_PWM):
    f = open(path,'w')
    f.write('DO NOT CHANGE PARAMETER!!\n')
    f.write('STEERING_RIGHT_PWM\n')
    f.write(str(STEERING_RIGHT_PWM))
    f.write('\n')
    f.write('STEERING_CENTER_PWM\n')
    f.write(str(STEERING_CENTER_PWM))
    f.write('\n')
    f.write('STEERING_LEFT_PWM\n')
    f.write(str(STEERING_LEFT_PWM))
    f.write('\n\n')
    f.write('THROTTLE_FORWARD_PWM\n')
    f.write(str(THROTTLE_FORWARD_PWM))
    f.write('\n')
    f.write('THROTTLE_STOPPED_PWM\n')
    f.write(str(THROTTLE_STOPPED_PWM))
    f.write('\n')
    f.write('THROTTLE_REVERSE_PWM\n')
    f.write(str(THROTTLE_REVERSE_PWM))
    f.write('\n\n')
    f.close()

THROTTLE_CHANNEL = 13   # PCA9685 channel for throttle (0-15)
STEERING_CHANNEL = 14   # PCA9685 channel for steering

def Accel(Duty):
    if Duty >= 0:
        throttle_pwm = int(THROTTLE_STOPPED_PWM - (THROTTLE_STOPPED_PWM - THROTTLE_FORWARD_PWM)*Duty/100)
        pwm.set_pwm(THROTTLE_CHANNEL, 0, throttle_pwm)
    elif Duty == 0:
        pwm.set_pwm(THROTTLE_CHANNEL, 0, THROTTLE_STOPPED_PWM)
        time.sleep(0.01)
    else:
        #Need to Reverse -> Stop -> Reverse
        pwm.set_pwm(THROTTLE_CHANNEL, 0, THROTTLE_REVERSE_PWM)
        time.sleep(0.05)
        pwm.set_pwm(THROTTLE_CHANNEL, 0, THROTTLE_STOPPED_PWM)
        time.sleep(0.05)
        throttle_pwm = int(THROTTLE_STOPPED_PWM + (THROTTLE_REVERSE_PWM - THROTTLE_STOPPED_PWM)*abs(Duty)/100)
        pwm.set_pwm(THROTTLE_CHANNEL, 0, throttle_pwm)
    #print('Throttle = ',throttle_pwm)
    #print(type(throttle_pwm))

def Steer(Duty):
    if Duty >= 0:
        steer_pwm = int(STEERING_CENTER_PWM + (STEERING_RIGHT_PWM - STEERING_CENTER_PWM)*Duty/100)
        pwm.set_pwm(STEERING_CHANNEL, 0, steer_pwm)
    else:
        steer_pwm = int(STEERING_CENTER_PWM - (STEERING_CENTER_PWM - STEERING_LEFT_PWM)*abs(Duty)/100)
        pwm.set_pwm(STEERING_CHANNEL, 0, steer_pwm)


path = '/home/pi/togikai/alignment_parameter.txt'

try:
    with open(path) as f:
        l = f.readlines()
        STEERING_RIGHT_PWM = int(l[2])
        STEERING_CENTER_PWM = int(l[4])
        STEERING_LEFT_PWM = int(l[6])
        THROTTLE_FORWARD_PWM = int(l[9])
        THROTTLE_STOPPED_PWM = int(l[11])
        THROTTLE_REVERSE_PWM = int(l[13])
except:
    STEERING_RIGHT_PWM = 490
    STEERING_CENTER_PWM = 390
    STEERING_LEFT_PWM = 290
    THROTTLE_FORWARD_PWM = 470
    THROTTLE_STOPPED_PWM = 390
    THROTTLE_REVERSE_PWM = 310
    writetofile(path,STEERING_RIGHT_PWM,STEERING_CENTER_PWM,STEERING_LEFT_PWM,THROTTLE_FORWARD_PWM,THROTTLE_STOPPED_PWM,THROTTLE_REVERSE_PWM)


pwm = Adafruit_PCA9685.PCA9685(address=0x40) #address:PCA9685のI2C Channel 0x40
pwm.set_pwm_freq(60)

Accel(0)
Steer(0)

print('========================================')
print('      Steer Adjustment(zero set)')
print('========================================')
while True:
    print('----------------------------------------')
    print('Write number and return to adjust.')
    print('After adjustment, press  e  and return.')
    print('----------------------------------------')
    print('----------------------------------------')
    print('The normal cneter value is around 370!')
    print('So start from near numbers please!')
    print('----------------------------------------')
    ad = input()
    if ad == 'e':
        STEERING_RIGHT_PWM = STEERING_CENTER_PWM + 100 #210522
        STEERING_LEFT_PWM = STEERING_CENTER_PWM - 100 #210522
        break
    else:
        STEERING_CENTER_PWM = int(ad)
    pwm.set_pwm(14, 0, STEERING_CENTER_PWM)

print('========================================')
print('      Accel Adjustment(zero set)')
print('========================================')
while True:
    print('----------------------------------------')
    print('Write number and return to adjust.')
    print('After adjustment, press  e  and return.')
    print('----------------------------------------')
    print('----------------------------------------')
    print('The normal cneter value is around 370!')
    print('So start from near numbers please!')
    print('----------------------------------------')
    ad = input()
    if ad == 'e':
        THROTTLE_FORWARD_PWM = THROTTLE_STOPPED_PWM + 80 #210522
        THROTTLE_REVERSE_PWM = THROTTLE_STOPPED_PWM - 80 #210522
        break
    else:
        THROTTLE_STOPPED_PWM = int(ad)
    pwm.set_pwm(13, 0, THROTTLE_STOPPED_PWM)

writetofile(path,STEERING_RIGHT_PWM,STEERING_CENTER_PWM,STEERING_LEFT_PWM,THROTTLE_FORWARD_PWM,THROTTLE_STOPPED_PWM,THROTTLE_REVERSE_PWM)

print(path,STEERING_RIGHT_PWM,STEERING_CENTER_PWM,STEERING_LEFT_PWM,THROTTLE_FORWARD_PWM,THROTTLE_STOPPED_PWM,THROTTLE_REVERSE_PWM)

#adjust_alignment.py：セッティング調整時に Raspberry Pi 上で直接実行して微調整する。

# 役割：adjust_alignment.py は「キャリブレーション（PWM 値の調整）ツール」です。
# サーボ／ESC の中心値・最大値等を調整して alignment_parameter.txt に保存するために使います。

# 初回セットアップ時（サーボ位置を合わせるとき）
# サーボ交換や配線変更、電源変更で再調整が必要になったとき
# 値がずれたときの再キャリブレーション

# PWM値とは「パルス幅変調（PWM）」で出す信号のオン期間を数値化したものです。サーボやESCはそのパルス幅（通常は数百〜数千µs）で位置や速度を決めます。

# PCA9685での意味合い PCA9685は内部で12bit分解能（0..4095）を使ってPWMを表現します。pwm.set_pwm(channel, on, off) の off 値がここでの「PWM値」に相当することが多いです。

# 周波数と変換（重要）周波数 f[Hz] のとき周期は period_us = 1e6 / f マイクロ秒。パルス幅 pulse_us を 0..4095 に変換する式は：
# 例: pulse_us を PCA9685 の 12bit カウントに変換
# period_us = 1_000_000.0 / freq_hz
# count = int(pulse_us * 4096.0 / period_us)

# パルス幅変調（PWM）は「一定周期で繰り返すパルス信号のうち、HIGH（オン）になっている時間の割合（デューティ比）を変えることで平均出力や制御対象の動作を決める方式」です。

# 周期（T）と周波数（f = 1/T）を決めておく。
# デューティ比 = ON時間 / 周期（%）。
# デューティ比を変えると出力の平均電圧や機器の指示が変わる（モータ速度、LED明るさ、等）。
# サーボ/ESCでは「パルス幅（µs）」自体が位置・スロットルを決める（典型的に50Hzで1000–2000µs、1.5msが中立）。