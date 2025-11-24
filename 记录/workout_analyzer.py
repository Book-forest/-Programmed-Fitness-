import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from collections import defaultdict

# 在 workout_analyzer.py 文件顶部附近
DATA_FILE = "workout_data.json" # <-- 确保这里是正确的文件名
# --- 全局设置 ---
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

DATA_FILE = "workout_data.json"

class WorkoutAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("锻炼数据可视化分析（次数/组数重点）")
        self.root.geometry("1000x700")

        self.workout_data = []
        self.action_stats = {}

        # 用于存储图表和画布的引用，以便在刷新时正确销毁
        self.figure = None
        self.canvas_widget = None

        self._load_data()
        self._create_widgets()

        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self._on_window_resize)

    def _load_data(self):
        """从JSON文件加载数据"""
        if not os.path.exists(DATA_FILE):
            messagebox.showwarning("提示", f"未找到数据文件 '{DATA_FILE}'。请先使用记录程序添加数据。")
            return
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.workout_data = json.load(f)
            self._calculate_action_stats()
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {e}")

    def _calculate_action_stats(self):
        """计算每个动作的统计信息（重点：单次最大次数）"""
        if not self.workout_data:
            return

        action_dict = defaultdict(list)
        for item in self.workout_data:
            action_name = item['name']
            action_dict[action_name].append(item)

        self.action_stats.clear()
        for name, entries in action_dict.items():
            # 计算总训练组数
            total_sets = sum(entry['sets'] for entry in entries)
            # 计算该动作记录中的最大单组次数
            max_reps_per_set = max(entry['reps'] for entry in entries)
            # 获取最近一次训练的时间
            last_date_str = max(entry['record_time'] for entry in entries)
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")

            self.action_stats[name] = {
                'total_sets': total_sets,
                'max_reps_per_set': max_reps_per_set,
                'last_trained': last_date,
                'entries': entries
            }

    def _create_widgets(self):
        """创建UI界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="刷新数据", command=self._on_refresh).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="选择数据文件", command=self._on_select_file).pack(side=tk.LEFT, padx=5)

        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        table_frame = ttk.LabelFrame(paned_window, text="动作库统计", padding="10")
        paned_window.add(table_frame, weight=1)
        self._create_action_table(table_frame)

        chart_frame = ttk.LabelFrame(paned_window, text="数据可视化", padding="10")
        paned_window.add(chart_frame, weight=2)
        self.chart_frame = chart_frame # 保存引用，用于后续绘制

        self._update_action_selector()
        self._update_chart() # 初始绘制图表

    def _create_action_table(self, parent):
        """创建动作库统计表格"""
        columns = ("动作名称", "总训练组数", "最大单组次数", "最近训练")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("动作名称", width=150, anchor=tk.W)
        self.tree.column("总训练组数", width=100, anchor=tk.E)
        self.tree.column("最大单组次数", width=120, anchor=tk.E)
        self.tree.column("最近训练", width=100, anchor=tk.CENTER)

        self.tree.bind("<Double-1>", self._on_action_double_click)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._populate_action_table()

    def _populate_action_table(self):
        """填充动作库表格数据"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for name, stats in self.action_stats.items():
            self.tree.insert("", tk.END, values=(
                name, stats['total_sets'], stats['max_reps_per_set'], stats['last_trained']
            ))

    def _update_chart(self):
        """根据选择更新图表"""
        # 如果已有图表，先销毁
        if self.canvas_widget:
            self.canvas_widget.destroy()

        chart_type = self.chart_type_var.get() if hasattr(self, 'chart_type_var') else "total_sets"

        # 根据当前frame大小动态调整图大小和字体
        width = self.chart_frame.winfo_width() / 100  # 转换为英寸
        height = self.chart_frame.winfo_height() / 100
        # 设置一个最小尺寸，避免窗口太小时出错
        width = max(width, 4)
        height = max(height, 3)

        # 计算基础字体大小
        base_font_size = min(width, height) * 4

        self.figure, self.ax = plt.subplots(figsize=(width, height))

        if chart_type == "total_sets":
            if not self.action_stats:
                self.ax.text(0.5, 0.5, '无数据可显示', horizontalalignment='center',
                             verticalalignment='center', transform=self.ax.transAxes, fontsize=base_font_size)
            else:
                action_names = list(self.action_stats.keys())
                total_sets = [self.action_stats[name]['total_sets'] for name in action_names]
                bars = self.ax.bar(action_names, total_sets, color='lightgreen')
                self.ax.set_title('各锻炼动作总训练组数', fontsize=base_font_size * 1.2)
                self.ax.set_ylabel('总组数', fontsize=base_font_size)
                self.ax.set_xlabel('锻炼动作', fontsize=base_font_size)
                self.ax.tick_params(axis='x', rotation=45, labelsize=base_font_size * 0.8)
                self.ax.tick_params(axis='y', labelsize=base_font_size * 0.8)
                for bar in bars:
                    height_val = bar.get_height()
                    self.ax.text(bar.get_x() + bar.get_width()/2., height_val + 0.5,
                                 f'{int(height_val)}', ha='center', va='bottom', fontsize=base_font_size * 0.7)

        elif chart_type == "reps_trend":
            selected_action = self.action_selector_var.get() if hasattr(self, 'action_selector_var') else ""
            if not selected_action or selected_action not in self.action_stats or not self.action_stats[selected_action]['entries']:
                self.ax.text(0.5, 0.5, '无数据可显示', horizontalalignment='center',
                             verticalalignment='center', transform=self.ax.transAxes, fontsize=base_font_size)
            else:
                entries = self.action_stats[selected_action]['entries']
                entries.sort(key=lambda x: x['record_time'])
                dates = [datetime.strptime(entry['record_time'], "%Y-%m-%d %H:%M:%S") for entry in entries]
                max_reps = [entry['reps'] for entry in entries]

                self.ax.plot(dates, max_reps, marker='o', linestyle='-', color='coral', markersize=base_font_size * 0.5)
                self.ax.set_title(f"'{selected_action}' 的单组最大次数变化趋势", fontsize=base_font_size * 1.1)
                self.ax.set_ylabel('单组最大次数', fontsize=base_font_size)
                self.ax.set_xlabel('日期', fontsize=base_font_size)
                self.ax.grid(True, linestyle='--', alpha=0.6)
                self.ax.tick_params(axis='x', rotation=45, labelsize=base_font_size * 0.7)
                self.ax.tick_params(axis='y', labelsize=base_font_size * 0.7)
                # 格式化x轴日期
                self.figure.autofmt_xdate()

        self.figure.tight_layout()

        canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

    def _create_chart_controls(self, parent):
        """创建图表控制组件（内部使用）"""
        chart_control_frame = ttk.Frame(parent)
        chart_control_frame.pack(fill=tk.X, pady=5)

        ttk.Label(chart_control_frame, text="选择图表类型:").pack(side=tk.LEFT, padx=(0, 5))

        self.chart_type_var = tk.StringVar(value="total_sets")
        ttk.Radiobutton(chart_control_frame, text="各动作总训练组数", variable=self.chart_type_var,
                        value="total_sets", command=self._update_chart).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(chart_control_frame, text="动作单次最大次数趋势", variable=self.chart_type_var,
                        value="reps_trend", command=self._update_chart).pack(side=tk.LEFT, padx=5)

        self.action_selector_var = tk.StringVar()
        self.action_selector = ttk.Combobox(chart_control_frame, textvariable=self.action_selector_var, state="readonly")
        self.action_selector.pack(side=tk.LEFT, padx=5)
        self.action_selector.bind("<<ComboboxSelected>>", lambda e: self._update_chart())

    def _update_action_selector(self):
        """更新趋势分析的动作选择下拉框"""
        if not hasattr(self, 'action_selector_var'):
             self._create_chart_controls(self.chart_frame)

        action_names = list(self.action_stats.keys())
        self.action_selector['values'] = action_names
        if action_names:
            self.action_selector_var.set(action_names[0])

    # --- 事件处理函数 ---
    def _on_window_resize(self, event):
        """当窗口大小改变时调用"""
        # 为了避免过于频繁地重绘，可以加一个判断，只有当窗口大小变化较大时才重绘
        if event.widget == self.root:
            # 使用after延迟执行，确保在窗口大小稳定后再重绘
            self.root.after(200, self._update_chart)

    def _on_refresh(self):
        """刷新数据"""
        self._load_data()
        self._populate_action_table()
        self._update_action_selector()
        self._update_chart()
        messagebox.showinfo("成功", "数据已刷新！")

    def _on_select_file(self):
        """选择数据文件"""
        file_path = filedialog.askopenfilename(
            title="选择锻炼数据文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if file_path:
            global DATA_FILE
            DATA_FILE = file_path
            self._on_refresh()

    def _on_action_double_click(self, event):
        """双击表格中的动作，查看其趋势"""
        selected_item = self.tree.focus()
        if not selected_item:
            return
        action_name = self.tree.item(selected_item, "values")[0]
        if action_name in self.action_stats:
            self.chart_type_var.set("reps_trend")
            self.action_selector_var.set(action_name)
            self._update_chart()

def main():
    root = tk.Tk()
    app = WorkoutAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()