# -*- coding: utf-8 -*-
"""H-alpha Solar Analyzer – minimal Windows GUI (Tkinter)."""
import calendar
import re
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import halpha_engine as engine

LOCATION_DEFAULT = "Esztergom, Hungary"
TIME_ZONE = "Europe/Budapest"


def filename_datetime(filename):
    """Return an unambiguous local YYYY-MM-DD-HHMM[SS] timestamp, else None."""
    m = re.search(r"(20\d\d)[-_](\d{2})[-_](\d{2})[-_T ](\d{2})[:\-]?(\d{2})(?:[:\-]?(\d{2}))?(?!\d)", filename)
    if not m:
        return None
    try:
        return datetime(int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]), int(m[6] or 0))
    except ValueError:
        return None


class CalendarPopup(tk.Toplevel):
    def __init__(self, parent, initial, on_pick):
        super().__init__(parent)
        self.title("Select date")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.year, self.month = initial.year, initial.month
        self.on_pick = on_pick
        self.top = ttk.Frame(self, padding=8)
        self.top.pack()
        self.render()

    def render(self):
        for child in self.top.winfo_children():
            child.destroy()
        bar = ttk.Frame(self.top)
        bar.grid(row=0, column=0, columnspan=7, sticky='ew')
        ttk.Button(bar, text='◀', width=3, command=lambda: self.change(-1)).pack(side='left')
        ttk.Label(bar, text=f'{calendar.month_name[self.month]} {self.year}', width=20, anchor='center').pack(side='left')
        ttk.Button(bar, text='▶', width=3, command=lambda: self.change(1)).pack(side='left')
        for c, day in enumerate(('Mo','Tu','We','Th','Fr','Sa','Su')):
            ttk.Label(self.top, text=day, width=4, anchor='center').grid(row=1,column=c)
        for r, week in enumerate(calendar.monthcalendar(self.year,self.month),start=2):
            for c, day in enumerate(week):
                if day:
                    ttk.Button(self.top,text=str(day),width=3,command=lambda d=day:self.pick(d)).grid(row=r,column=c,padx=1,pady=1)

    def change(self, offset):
        month_index = self.year * 12 + self.month - 1 + offset
        self.year, m = divmod(month_index,12)
        self.month = m+1
        self.render()

    def pick(self, day):
        self.on_pick(datetime(self.year,self.month,day))
        self.destroy()


class HAlphaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('H-alpha Solar Analyzer')
        self.resizable(False, False)
        self.geometry('520x450')
        self.path = tk.StringVar()
        self.location = tk.StringVar(value=LOCATION_DEFAULT)
        self.auto = tk.BooleanVar(value=True)
        self.date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.time = tk.StringVar(value=datetime.now().strftime('%H:%M'))
        self.result = tk.StringVar(value='Filaments: —\nActive regions: —\nB0: —\nP0: —')
        self.status = tk.StringVar(value='Select an H-alpha image to begin.')
        self._build()
        self._toggle_time()

    def _build(self):
        frame = ttk.Frame(self,padding=16)
        frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='H-alpha Solar Analyzer',font=('Segoe UI',16,'bold')).pack(anchor='w',pady=(0,15))
        ttk.Label(frame,text='H-alpha image').pack(anchor='w')
        row = ttk.Frame(frame)
        row.pack(fill='x',pady=(3,12))
        ttk.Entry(row,textvariable=self.path,state='readonly',width=49).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Browse...',command=self.browse).pack(side='left',padx=(8,0))
        ttk.Label(frame,text='Observation location').pack(anchor='w')
        ttk.Entry(frame,textvariable=self.location).pack(fill='x',pady=(3,12))
        ttk.Checkbutton(frame,text='Read date and time from filename',variable=self.auto,command=self._toggle_time).pack(anchor='w',pady=(0,8))
        row = ttk.Frame(frame)
        row.pack(fill='x',pady=(0,4))
        left = ttk.Frame(row)
        left.pack(side='left',fill='x',expand=True)
        ttk.Label(left,text='Date').pack(anchor='w')
        drow = ttk.Frame(left)
        drow.pack(fill='x',pady=(3,0))
        self.date_entry = ttk.Entry(drow,textvariable=self.date,width=16)
        self.date_entry.pack(side='left',fill='x',expand=True)
        self.calendar_btn = ttk.Button(drow,text='📅',width=3,command=self.pick_date)
        self.calendar_btn.pack(side='left',padx=(4,0))
        right = ttk.Frame(row)
        right.pack(side='left',padx=(18,0))
        ttk.Label(right,text='Local time (HH:MM)').pack(anchor='w')
        self.time_entry = ttk.Entry(right,textvariable=self.time,width=15)
        self.time_entry.pack(pady=(3,0))
        ttk.Label(frame,text='Time zone: Europe/Budapest (CET/CEST)',foreground='#666').pack(anchor='w',pady=(2,16))
        self.analyze_btn = ttk.Button(frame,text='Analyze',command=self.analyze)
        self.analyze_btn.pack(fill='x',pady=(0,12))
        group = ttk.LabelFrame(frame,text='Results',padding=10)
        group.pack(fill='x')
        ttk.Label(group,textvariable=self.result,justify='left').pack(anchor='w')
        ttk.Label(frame,textvariable=self.status,foreground='#555',wraplength=480).pack(anchor='w',pady=(12,0))

    def browse(self):
        filename = filedialog.askopenfilename(title='Select H-alpha image',filetypes=[('Images','*.jpg *.jpeg *.png *.tif *.tiff'),('All files','*.*')])
        if not filename:
            return
        self.path.set(filename)
        if self.auto.get():
            self._read_filename()

    def _read_filename(self):
        if not self.path.get():
            return
        dt = filename_datetime(Path(self.path.get()).name)
        if dt is None:
            self.auto.set(False)
            self._toggle_time()
            messagebox.showinfo('Date and time','No complete timestamp was found in the filename. Please enter the observation date and local time manually.')
        else:
            self.date.set(dt.strftime('%Y-%m-%d'))
            self.time.set(dt.strftime('%H:%M:%S'))

    def _toggle_time(self):
        enabled = not self.auto.get()
        self.date_entry.configure(state='normal' if enabled else 'disabled')
        self.time_entry.configure(state='normal' if enabled else 'disabled')
        self.calendar_btn.configure(state='normal' if enabled else 'disabled')
        if self.auto.get() and self.path.get():
            self._read_filename()

    def pick_date(self):
        try:
            initial = datetime.strptime(self.date.get(),'%Y-%m-%d')
        except ValueError:
            initial = datetime.now()
        CalendarPopup(self,initial,lambda dt:self.date.set(dt.strftime('%Y-%m-%d')))

    def analyze(self):
        path = Path(self.path.get())
        if not path.is_file():
            messagebox.showerror('Input error','Please select a valid image.')
            return
        location = self.location.get().strip()
        if not location:
            messagebox.showerror('Input error','Please enter the observation location.')
            return
        try:
            if self.auto.get():
                dt = filename_datetime(path.name)
                if dt is None:
                    raise ValueError('No complete timestamp in filename. Uncheck the option and enter the time manually.')
            else:
                value = self.date.get().strip() + ' ' + self.time.get().strip()
                dt = None
                for fmt in ('%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M'):
                    try:
                        dt = datetime.strptime(value,fmt)
                        break
                    except ValueError:
                        pass
                if dt is None:
                    raise ValueError('Use YYYY-MM-DD and HH:MM (or HH:MM:SS).')
        except ValueError as exc:
            messagebox.showerror('Date/time error',str(exc))
            return
        self.analyze_btn.configure(state='disabled')
        self.status.set('Analyzing...')
        self.result.set('Filaments: —\nActive regions: —\nB0: —\nP0: —')
        threading.Thread(target=self._worker,args=(path,dt,location),daemon=True).start()

    def _worker(self,path,dt,location):
        try:
            result = engine.analyze_selected_image(path,dt,location,TIME_ZONE)
        except Exception as exc:
            self.after(0,lambda msg=str(exc):self._error(msg))
            return
        self.after(0,lambda:self._done(result))

    def _error(self,msg):
        self.analyze_btn.configure(state='normal')
        self.status.set('Analysis failed.')
        messagebox.showerror('Analysis error',msg)

    def _done(self,result):
        self.analyze_btn.configure(state='normal')
        self.result.set(f"Filaments: {result['filaments']}\nActive regions: {result['active_regions']}\nB0: {result['B0']:+.2f}°\nP0: {result['P0']:+.2f}°")
        self.status.set(f"Saved to: {result['folder']}")
        messagebox.showinfo('Analysis complete','Annotated image and two CSV files saved next to the input image.')


if __name__ == '__main__':
    HAlphaApp().mainloop()
