"""
走行データログ記録モジュール
センサーデータと制御コマンドをCSVファイルに記録
"""

import os
import csv
from datetime import datetime


class DataLogger:
    """走行データをCSVに記録するクラス"""

    # ヘッダー定義
    HEADERS = [
        'timestamp',      # 経過時間(秒)
        'steering',       # ステアリング角度
        'throttle',       # スロットル値
        'sensor_l2',      # 左センサー (mm)
        'sensor_l1',      # 左前センサー (mm)
        'sensor_c',       # 正面センサー (mm)
        'sensor_r1',      # 右前センサー (mm)
        'sensor_r2',      # 右センサー (mm)
        'state'           # 走行状態
    ]

    def __init__(self, output_dir='/home/pi/driving_logs', enabled=True):
        """
        初期化

        Args:
            output_dir: ログ出力ディレクトリ
            enabled: ログ記録を有効にするか
        """
        self.enabled = enabled
        self.output_dir = output_dir
        self.file_path = None
        self.file = None
        self.writer = None
        self.start_time = None
        self.record_count = 0

    def start(self):
        """ログ記録を開始"""
        if not self.enabled:
            return

        # 出力ディレクトリを作成
        os.makedirs(self.output_dir, exist_ok=True)

        # ファイル名をタイムスタンプで生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.file_path = os.path.join(self.output_dir, f'driving_log_{timestamp}.csv')

        # ファイルを開いてヘッダーを書き込み
        self.file = open(self.file_path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(self.HEADERS)

        self.start_time = datetime.now()
        self.record_count = 0

        print(f"[DataLogger] 記録開始: {self.file_path}")

    def log(self, steering, throttle, distances, state=''):
        """
        1行分のデータを記録

        Args:
            steering: ステアリング角度
            throttle: スロットル値
            distances: センサー値のリスト [l2, l1, c, r1, r2]
            state: 走行状態の文字列
        """
        if not self.enabled or self.writer is None:
            return

        # 経過時間を計算
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # センサー値を展開
        if len(distances) >= 5:
            l2, l1, c, r1, r2 = distances[:5]
        else:
            l2, l1, c, r1, r2 = 0, 0, 0, 0, 0

        # 行を書き込み
        row = [
            f'{elapsed:.3f}',
            f'{steering:.2f}',
            f'{throttle:.3f}',
            f'{l2:.0f}',
            f'{l1:.0f}',
            f'{c:.0f}',
            f'{r1:.0f}',
            f'{r2:.0f}',
            state
        ]
        self.writer.writerow(row)
        self.record_count += 1

        # 定期的にフラッシュ（10件ごと）
        if self.record_count % 10 == 0:
            self.file.flush()

    def stop(self):
        """ログ記録を終了"""
        if not self.enabled:
            return

        if self.file:
            self.file.close()
            self.file = None
            self.writer = None

            print(f"[DataLogger] 記録終了: {self.record_count}件")
            print(f"[DataLogger] 保存先: {self.file_path}")

    def __enter__(self):
        """コンテキストマネージャー対応"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー対応"""
        self.stop()
        return False
