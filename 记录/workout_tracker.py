import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

# 配置常量
APP_CONFIG = {
    "title": "锻炼动作记录（含RM/RPE）",
    "window_size": "850x500",
    "font": ("Microsoft YaHei", 10),
    "data_file": "workout_data.json",
    "columns": ["动作名称", "重量(kg)", "组数", "次数", "RPE", "RIR", "备注", "记录时间"],
    "column_widths": [120, 80, 60, 60, 60, 60, 180, 150]
}

@dataclass
class WorkoutItem:
    """锻炼动作数据类（支持0重量）"""
    name: str
    weight: float  # 允许0
    sets: int      # 必须为正整数
    reps: int      # 必须为正整数
    rpe: int       # 1-10
    rir: float
    notes: str = ""
    record_time: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        # 兼容旧数据，为缺失的字段提供默认值
        data.setdefault('weight', 0.0)
        data.setdefault('rpe', 7)
        data.setdefault('rir', 3)
        data.setdefault('record_time', "")
        return cls(**data)

class WorkoutTracker:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.workout_items: List[WorkoutItem] = []
        self._initialize_app()

    def _initialize_app(self):
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._load_data()

    def _setup_window(self):
        self.root.title(APP_CONFIG["title"])
        self.root.geometry(APP_CONFIG["window_size"])
        self.root.resizable(True, True)

    def _create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.input_frame = self._create_input_frame()
        self.list_frame, self.tree = self._create_list_frame()
        self.button_frame = self._create_button_frame()

    def _setup_layout(self):
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        self.input_frame.grid(row=0, column=0, sticky="ew", pady=5)
        self.list_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.button_frame.grid(row=2, column=0, sticky="ew", pady=5)

    def _create_input_frame(self) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self.main_frame, text="添加锻炼动作", padding="10")
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(7, weight=1)

        # 输入控件变量（优化默认值）
        self.name_var = tk.StringVar()
        self.weight_var = tk.StringVar(value="0")  # 允许0重量
        self.sets_var = tk.StringVar(value="3")    # 默认3组
        self.reps_var = tk.StringVar(value="10")   # 默认10次
        self.rpe_var = tk.StringVar(value="7")
        self.notes_var = tk.StringVar()

        # RPE -> RIR 联动逻辑
        def on_rpe_change(*args):
            try:
                rpe = int(self.rpe_var.get())
                if 1 <= rpe <= 10:
                    rir = 10 - rpe
                    self.rir_display_var.set(f"{rir:.1f}" if rpe < 10 else "0")
            except ValueError:
                pass

        self.rpe_var.trace("w", on_rpe_change)
        self.rir_display_var = tk.StringVar(value="3.0")

        # UI布局
        # 第一行
        ttk.Label(frame, text="动作名称:", font=APP_CONFIG["font"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.name_var, font=APP_CONFIG["font"]).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frame, text="重量(kg):", font=APP_CONFIG["font"]).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.weight_var, font=APP_CONFIG["font"], width=10).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(frame, text="RPE:", font=APP_CONFIG["font"]).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        rpe_combo = ttk.Combobox(frame, textvariable=self.rpe_var, values=list(range(1, 11)), state="readonly", width=5)
        rpe_combo.grid(row=0, column=5, padx=5, pady=5)
        rpe_combo.current(6)  # 默认选中7

        ttk.Label(frame, text="备注:", font=APP_CONFIG["font"]).grid(row=0, column=6, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.notes_var, font=APP_CONFIG["font"]).grid(row=0, column=7, padx=5, pady=5, sticky="ew")

        # 第二行
        ttk.Label(frame, text="组数:", font=APP_CONFIG["font"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.sets_var, font=APP_CONFIG["font"], width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="次数:", font=APP_CONFIG["font"]).grid(row=1, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frame, textvariable=self.reps_var, font=APP_CONFIG["font"], width=10).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="RIR:", font=APP_CONFIG["font"]).grid(row=1, column=4, padx=5, pady=5, sticky="w")
        ttk.Label(frame, textvariable=self.rir_display_var, font=APP_CONFIG["font"]).grid(row=1, column=5, padx=5, pady=5)

        # 添加按钮
        ttk.Button(frame, text="添加", command=self.add_exercise).grid(row=0, column=8, rowspan=2, padx=10, pady=5)
        
        # 初始化RIR显示
        on_rpe_change()

        return frame

    def _create_list_frame(self) -> tuple[ttk.LabelFrame, ttk.Treeview]:
        frame = ttk.LabelFrame(self.main_frame, text="锻炼动作列表", padding="10")
        tree = ttk.Treeview(frame, columns=APP_CONFIG["columns"], show="headings")

        for col, width in zip(APP_CONFIG["columns"], APP_CONFIG["column_widths"]):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return frame, tree

    def _create_button_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self.main_frame)
        frame.columnconfigure(0, weight=1)
        ttk.Button(frame, text="删除选中项", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(frame, text="清空列表", command=self.clear_all).pack(side="left", padx=5)
        ttk.Button(frame, text="保存到本地", command=self.save_data).pack(side="right", padx=5)
        ttk.Button(frame, text="导出为CSV", command=self.export_to_csv).pack(side="right", padx=5)
        return frame

    def _validate_input(self) -> tuple[bool, Optional[WorkoutItem]]:
        try:
            name = self.name_var.get().strip()
            weight_str = self.weight_var.get().strip()
            sets_str = self.sets_var.get().strip()
            reps_str = self.reps_var.get().strip()
            rpe = int(self.rpe_var.get())
            rir = float(self.rir_display_var.get())
            notes = self.notes_var.get().strip()

            # 验证动作名称
            if not name:
                raise ValueError("动作名称不能为空！")
            
            # 验证重量（允许0，支持小数）
            try:
                weight = float(weight_str)
                if weight < 0:
                    raise ValueError("重量不能为负数！")
            except ValueError:
                raise ValueError("重量请输入有效的数字（如 0、2.5、10）！")
            
            # 验证组数（正整数）
            try:
                sets = int(sets_str)
                if sets <= 0:
                    raise ValueError("组数必须为正整数（如 1、3、5）！")
            except ValueError:
                raise ValueError("组数请输入有效的正整数！")
            
            # 验证次数（正整数）
            try:
                reps = int(reps_str)
                if reps <= 0:
                    raise ValueError("次数必须为正整数（如 5、10、15）！")
            except ValueError:
                raise ValueError("次数请输入有效的正整数！")
            
            # 验证RPE
            if not (1 <= rpe <= 10):
                raise ValueError("RPE值必须在 1-10 之间！")

            return True, WorkoutItem(
                name=name, weight=weight, sets=sets, reps=reps,
                rpe=rpe, rir=rir, notes=notes,
                record_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        except ValueError as e:
            messagebox.showerror("输入错误", str(e))
            return False, None

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for workout in self.workout_items:
            self.tree.insert("", "end", values=(
                workout.name, workout.weight, workout.sets, workout.reps,
                workout.rpe, workout.rir, workout.notes, workout.record_time
            ))

    def _clear_input(self):
        self.name_var.set("")
        self.notes_var.set("")
        # 保留重量、组数、次数的默认值，方便连续添加
        # self.weight_var.set("0")
        # self.sets_var.set("3")
        # self.reps_var.set("10")

    def add_exercise(self):
        valid, item = self._validate_input()
        if valid and item:
            self.workout_items.append(item)
            self._refresh_list()
            self._clear_input()
            self.input_frame.focus_set()

    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要删除的记录！")
            return
        if messagebox.askyesno("确认删除", "确定要删除选中的记录吗？"):
            for item_id in selected_items:
                del self.workout_items[self.tree.index(item_id)]
            self._refresh_list()

    def clear_all(self):
        if not self.workout_items:
            messagebox.showinfo("提示", "列表已经是空的！")
            return
        if messagebox.askyesno("确认清空", "确定要删除所有锻炼记录吗？此操作不可恢复！"):
            self.workout_items.clear()
            self._refresh_list()

    def save_data(self):
        if not self.workout_items:
            messagebox.showinfo("提示", "没有可保存的锻炼记录！")
            return
        try:
            with open(APP_CONFIG["data_file"], "w", encoding="utf-8") as f:
                json.dump([item.to_dict() for item in self.workout_items], f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"锻炼记录已保存到：{os.path.abspath(APP_CONFIG['data_file'])}")
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存数据：{str(e)}")

    def export_to_csv(self):
        if not self.workout_items:
            messagebox.showinfo("提示", "没有可导出的锻炼记录！")
            return
        file_path = filedialog.asksaveasfilename(
            title="导出为CSV文件", defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=f"锻炼记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(",".join(APP_CONFIG["columns"]) + "\n")
                for workout in self.workout_items:
                    row = [
                        f'"{workout.name}"' if "," in workout.name else workout.name,
                        str(workout.weight), str(workout.sets), str(workout.reps),
                        str(workout.rpe), str(workout.rir),
                        f'"{workout.notes}"' if "," in workout.notes else workout.notes,
                        workout.record_time
                    ]
                    f.write(",".join(row) + "\n")
            messagebox.showinfo("导出成功", f"CSV文件已保存到：{os.path.abspath(file_path)}")
        except Exception as e:
            messagebox.showerror("导出失败", f"无法导出CSV文件：{str(e)}")

    def _load_data(self):
        try:
            if os.path.exists(APP_CONFIG["data_file"]):
                with open(APP_CONFIG["data_file"], "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.workout_items = [WorkoutItem.from_dict(item) for item in data]
                self._refresh_list()
        except Exception as e:
            messagebox.showwarning("加载警告", f"无法加载保存的记录：{str(e)}")
            self.workout_items = []

def main():
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use("clam")
    app = WorkoutTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()