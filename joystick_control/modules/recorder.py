"""
データ録画モジュール
センサーデータと操作履歴をCSVに保存
"""

import csv
import os
import time
from datetime import datetime

import sys
sys.path.append('..')
from config.settings import DATA_SAVE_PATH, CSV_HEADER


class DataRecorder:
    """データ録画クラス"""
    
    def __init__(self, save_path=None):
        """
        データレコーダーの初期化
        
        Args:
            save_path: 保存先パス（Noneの場合は設定ファイルのパスを使用）
        """
        self.save_path = save_path or DATA_SAVE_PATH
        self.recording = False
        self.data = []
        self.start_time = None
        self.file_path = None
        
    def start_recording(self):
        """録画を開始"""
        if self.recording:
            print("すでに録画中です")
            return False
        
        self.recording = True
        self.data = []
        self.start_time = time.time()
        
        # タイムスタンプ付きのファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # dataディレクトリを確保
        save_dir = os.path.dirname(self.save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # ファイル名にタイムスタンプを追加
        base_name = os.path.basename(self.save_path)
        name, ext = os.path.splitext(base_name)
        self.file_path = os.path.join(save_dir, f"{name}_{timestamp}{ext}")
        
        print(f"録画開始: {self.file_path}")
        return True
    
    def record(self, steering, throttle, distances):
        """
        データを記録
        
        Args:
            steering: ステアリング値
            throttle: スロットル値
            distances: センサー距離リスト [L2, L1, C, R1, R2]
        """
        if not self.recording:
            return
        
        elapsed_time = round(time.time() - self.start_time, 3)
        
        # [timestamp, steering, throttle, L2, L1, C, R1, R2]
        row = [elapsed_time, steering, throttle] + distances
        self.data.append(row)
    
    def stop_recording(self):
        """録画を停止してファイルに保存"""
        if not self.recording:
            print("録画していません")
            return False
        
        self.recording = False
        
        if len(self.data) == 0:
            print("保存するデータがありません")
            return False
        
        # CSVファイルに保存
        try:
            with open(self.file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADER)
                writer.writerows(self.data)
            
            print(f"録画停止: {len(self.data)}行のデータを保存しました")
            print(f"ファイル: {self.file_path}")
            return True
        except Exception as e:
            print(f"保存エラー: {e}")
            return False
    
    def is_recording(self):
        """録画中かどうか"""
        return self.recording
    
    def get_record_count(self):
        """記録済みのデータ数を取得"""
        return len(self.data)
