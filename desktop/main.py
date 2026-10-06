"""WhatsApp Bulk Sender - واجهة Tkinter + Selenium (واتساب ويب)."""
import json
import os
import random
import re
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import quote

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "numbers.json")
PROFILE_DIR = os.path.join(BASE_DIR, "chrome_profile")


# ---------- التخزين الدائم ----------
def load_numbers():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_numbers(items):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def normalize(raw, country_code):
    """يرجع الرقم بصيغة دولية بدون + ، أو None لو غير صالح."""
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = country_code + digits[1:]
    elif not digits.startswith(country_code) and len(digits) <= 10:
        digits = country_code + digits
    return digits if 8 <= len(digits) <= 15 else None


# ---------- الإرسال ----------
class Sender:
    def __init__(self):
        self.driver = None

    def start(self):
        if self.driver:
            return
        opts = webdriver.ChromeOptions()
        opts.add_argument(f"--user-data-dir={PROFILE_DIR}")  # يحفظ تسجيل الدخول
        opts.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=opts)
        self.driver.get("https://web.whatsapp.com")
        WebDriverWait(self.driver, 180).until(
            EC.presence_of_element_located((By.ID, "pane-side"))
        )

    def send(self, number, message):
        self.driver.get(
            f"https://web.whatsapp.com/send?phone={number}&text={quote(message)}"
        )
        box = WebDriverWait(self.driver, 45).until(
            EC.presence_of_element_located(
                (By.XPATH, '//footer//div[@contenteditable="true"]')
            )
        )
        time.sleep(1.5)
        box.send_keys(Keys.ENTER)
        time.sleep(2)

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None


# ---------- الواجهة ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("مرسل واتساب الجماعي")
        self.geometry("760x680")
        self.items = load_numbers()  # [{"number": "...", "name": "..."}]
        self.sender = Sender()
        self.stop_flag = False
        self.sending = False
        self._build()
        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        pad = {"padx": 8, "pady": 4}

        top = ttk.LabelFrame(self, text="الرسالة")
        top.pack(fill="x", **pad)
        self.msg = tk.Text(top, height=6, wrap="word")
        self.msg.pack(fill="x", padx=6, pady=6)

        add = ttk.LabelFrame(self, text="إضافة رقم")
        add.pack(fill="x", **pad)
        ttk.Label(add, text="كود الدولة:").grid(row=0, column=0, **pad)
        self.cc = ttk.Entry(add, width=5)
        self.cc.insert(0, "20")
        self.cc.grid(row=0, column=1, **pad)
        ttk.Label(add, text="الاسم:").grid(row=0, column=2, **pad)
        self.name_e = ttk.Entry(add, width=16)
        self.name_e.grid(row=0, column=3, **pad)
        ttk.Label(add, text="الرقم:").grid(row=0, column=4, **pad)
        self.num_e = ttk.Entry(add, width=18)
        self.num_e.grid(row=0, column=5, **pad)
        self.num_e.bind("<Return>", lambda e: self.add_number())
        ttk.Button(add, text="إضافة", command=self.add_number).grid(row=0, column=6, **pad)
        ttk.Button(add, text="استيراد من ملف", command=self.import_file).grid(row=0, column=7, **pad)

        lst = ttk.LabelFrame(self, text="قائمة الأرقام (اختر بعضها أو كلها)")
        lst.pack(fill="both", expand=True, **pad)
        self.tree = ttk.Treeview(
            lst, columns=("name", "number"), show="headings", selectmode="extended"
        )
        self.tree.heading("name", text="الاسم")
        self.tree.heading("number", text="الرقم")
        self.tree.column("name", width=250)
        self.tree.column("number", width=250)
        sb = ttk.Scrollbar(lst, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        sb.pack(side="right", fill="y", pady=6)

        tools = ttk.Frame(self)
        tools.pack(fill="x", **pad)
        ttk.Button(tools, text="تحديد الكل", command=self.select_all).pack(side="left", **pad)
        ttk.Button(tools, text="إلغاء التحديد", command=lambda: self.tree.selection_remove(self.tree.selection())).pack(side="left", **pad)
        ttk.Button(tools, text="حذف المحدد", command=self.delete_selected).pack(side="left", **pad)
        self.count_lbl = ttk.Label(tools, text="")
        self.count_lbl.pack(side="right", **pad)

        opt = ttk.Frame(self)
        opt.pack(fill="x", **pad)
        ttk.Label(opt, text="تأخير بين الرسائل (ثانية) من").pack(side="left", **pad)
        self.dmin = ttk.Spinbox(opt, from_=3, to=120, width=5)
        self.dmin.set(8)
        self.dmin.pack(side="left")
        ttk.Label(opt, text="إلى").pack(side="left", **pad)
        self.dmax = ttk.Spinbox(opt, from_=3, to=300, width=5)
        self.dmax.set(15)
        self.dmax.pack(side="left")

        act = ttk.Frame(self)
        act.pack(fill="x", **pad)
        self.btn_sel = ttk.Button(act, text="إرسال للمحدد", command=lambda: self.start_send(False))
        self.btn_sel.pack(side="left", expand=True, fill="x", **pad)
        self.btn_all = ttk.Button(act, text="إرسال للكل", command=lambda: self.start_send(True))
        self.btn_all.pack(side="left", expand=True, fill="x", **pad)
        self.btn_stop = ttk.Button(act, text="إيقاف", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", **pad)

        self.progress = ttk.Progressbar(self)
        self.progress.pack(fill="x", **pad)
        self.status = ttk.Label(self, text="جاهز")
        self.status.pack(fill="x", **pad)

    # --- إدارة القائمة ---
    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.items):
            self.tree.insert("", "end", iid=str(i), values=(it["name"], it["number"]))
        self.count_lbl.config(text=f"العدد: {len(self.items)}")

    def add_number(self):
        n = normalize(self.num_e.get(), self.cc.get().strip() or "20")
        if not n:
            messagebox.showwarning("خطأ", "رقم غير صالح")
            return
        if any(it["number"] == n for it in self.items):
            messagebox.showinfo("تنبيه", "الرقم موجود بالفعل")
            return
        self.items.append({"name": self.name_e.get().strip(), "number": n})
        save_numbers(self.items)
        self.num_e.delete(0, "end")
        self.name_e.delete(0, "end")
        self._refresh()

    def import_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text/CSV", "*.txt *.csv"), ("All", "*.*")])
        if not path:
            return
        cc = self.cc.get().strip() or "20"
        existing = {it["number"] for it in self.items}
        added = 0
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                parts = [p.strip() for p in re.split(r"[,;\t]", line) if p.strip()]
                if not parts:
                    continue
                num_raw, name = (parts[0], "") if len(parts) == 1 else (parts[-1], parts[0])
                n = normalize(num_raw, cc)
                if n and n not in existing:
                    self.items.append({"name": name, "number": n})
                    existing.add(n)
                    added += 1
        save_numbers(self.items)
        self._refresh()
        messagebox.showinfo("تم", f"تمت إضافة {added} رقم")

    def select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def delete_selected(self):
        sel = {int(i) for i in self.tree.selection()}
        if not sel:
            return
        self.items = [it for i, it in enumerate(self.items) if i not in sel]
        save_numbers(self.items)
        self._refresh()

    # --- الإرسال ---
    def start_send(self, all_numbers):
        if self.sending:
            return
        message = self.msg.get("1.0", "end").strip()
        if not message:
            messagebox.showwarning("خطأ", "اكتب الرسالة أولاً")
            return
        if all_numbers:
            targets = list(self.items)
        else:
            targets = [self.items[int(i)] for i in self.tree.selection()]
        if not targets:
            messagebox.showwarning("خطأ", "لا توجد أرقام للإرسال")
            return
        if not messagebox.askyesno("تأكيد", f"سيتم الإرسال إلى {len(targets)} رقم. متابعة؟"):
            return
        try:
            lo, hi = float(self.dmin.get()), float(self.dmax.get())
        except ValueError:
            lo, hi = 8, 15
        self.stop_flag = False
        self.sending = True
        self.btn_sel.config(state="disabled")
        self.btn_all.config(state="disabled")
        self.btn_stop.config(state="normal")
        threading.Thread(target=self._worker, args=(targets, message, lo, max(lo, hi)), daemon=True).start()

    def stop(self):
        self.stop_flag = True
        self._set_status("جارٍ الإيقاف...")

    def _set_status(self, text):
        self.after(0, lambda: self.status.config(text=text))

    def _worker(self, targets, message, lo, hi):
        ok, failed = 0, []
        total = len(targets)
        self.after(0, lambda: self.progress.config(maximum=total, value=0))
        try:
            self._set_status("جارٍ فتح واتساب ويب... امسح الـ QR إن طُلب منك")
            self.sender.start()
            for idx, it in enumerate(targets, 1):
                if self.stop_flag:
                    break
                self._set_status(f"({idx}/{total}) إرسال إلى {it['name'] or it['number']}")
                try:
                    name = it["name"] or ""
                    self.sender.send(it["number"], message.replace("{name}", name))
                    ok += 1
                except Exception:
                    failed.append(it["number"])
                self.after(0, lambda v=idx: self.progress.config(value=v))
                if idx < total and not self.stop_flag:
                    time.sleep(random.uniform(lo, hi))
            summary = f"تم: {ok} | فشل: {len(failed)}"
            if self.stop_flag:
                summary += " (تم الإيقاف)"
            self._set_status(summary)
            if failed:
                self.after(0, lambda: messagebox.showwarning("أرقام فشلت", "\n".join(failed[:50])))
        except Exception as e:
            self._set_status(f"خطأ: {e}")
        finally:
            self.sending = False
            self.after(0, lambda: (
                self.btn_sel.config(state="normal"),
                self.btn_all.config(state="normal"),
                self.btn_stop.config(state="disabled"),
            ))

    def _on_close(self):
        self.stop_flag = True
        self.sender.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
