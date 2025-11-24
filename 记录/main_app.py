import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("健身记录与分析系统")
        self.root.geometry("400x200")

        # 获取当前脚本所在的目录，确保能正确找到其他.py文件
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="健身记录与分析系统", font=("SimHei", 16, "bold"))
        title_label.pack(pady=10)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill=tk.X)

        # 按钮样式
        style = ttk.Style()
        style.configure("Main.TButton", font=("SimHei", 12))

        tracker_button = ttk.Button(button_frame, text="打开锻炼记录", command=self.open_tracker, style="Main.TButton")
        tracker_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        analyzer_button = ttk.Button(button_frame, text="打开数据分析", command=self.open_analyzer, style="Main.TButton")
        analyzer_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    def open_tracker(self):
        """启动锻炼记录程序"""
        tracker_path = os.path.join(self.current_dir, "workout_tracker.py")
        if os.path.exists(tracker_path):
            # 使用当前的Python解释器来运行脚本
            subprocess.Popen([sys.executable, tracker_path])
        else:
            messagebox.showerror("错误", f"未找到锻炼记录程序: {tracker_path}")

    def open_analyzer(self):
        """启动数据分析程序"""
        analyzer_path = os.path.join(self.current_dir, "workout_analyzer.py")
        if os.path.exists(analyzer_path):
            subprocess.Popen([sys.executable, analyzer_path])
        else:
            messagebox.showerror("错误", f"未找到数据分析程序: {analyzer_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()