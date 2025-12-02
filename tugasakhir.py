import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import date, datetime, timedelta
from abc import ABC, abstractmethod
import calendar
import random

DATA_FILE = 'restobook_data.json'
TOTAL_TABLES = 10

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'reservations': []}
    return {'reservations': []}

def save_data(d):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)

def gen_id():
    return datetime.now().strftime('%Y%m%d%H%M%S%f')

def count_assigned(reservations, target_date):
    count = 0
    for r in reservations:
        if r.get('date') == target_date and r.get('table') is not None:
            count += 1
    return count

def available_tables(reservations, target_date):
    used = count_assigned(reservations, target_date)
    return max(0, TOTAL_TABLES - used)

def get_unused_tables(reservations, target_date):
    used_tables = []
    for r in reservations:
        if r.get('date') == target_date and r.get('table') is not None:
            used_tables.append(r['table'])
    all_tables = list(range(1, TOTAL_TABLES + 1))
    unused = []
    for t in all_tables:
        if t not in used_tables:
            unused.append(t)
    return unused

class User(ABC):
    @abstractmethod
    def open_view(self):
        pass

class Staff(User):
    def __init__(self, username, password):
        self.__username = username
        self.__password = password

    def get_username(self):
        return self.__username

    def set_username(self, new_username):
        if isinstance(new_username, str) and new_username.strip():
            self.__username = new_username.strip()
        else:
            raise ValueError("Username tidak valid")

    def check(self, u, p):
        return u == self.__username and p == self.__password

    def open_view(self):
        App.show_staff_panel()

class Customer(User):
    def open_view(self):
        App.show_customer_form()

class CalendarPopup(tk.Toplevel):
    def __init__(self, master, set_callback, init_date=None):
        super().__init__(master)
        self.set_callback = set_callback
        self.transient(master)
        self.title('Pilih Tanggal')
        self.resizable(False, False)
        self.selected = init_date or date.today()
        self.year = self.selected.year
        self.month = self.selected.month
        self.build()

    def build(self):
        header = tk.Frame(self)
        header.pack(padx=8, pady=6)
        tk.Button(header, text='<', width=3, command=self.prev).grid(row=0, column=0)
        self.title_lbl = tk.Label(header, text=f'{calendar.month_name[self.month]} {self.year}', font=('Helvetica', 11, 'bold'))
        self.title_lbl.grid(row=0, column=1, padx=8)
        tk.Button(header, text='>', width=3, command=self.next).grid(row=0, column=2)
        body = tk.Frame(self)
        body.pack(padx=8, pady=6)
        self.body = body
        self.draw()

    def draw(self):
        for w in self.body.winfo_children():
            w.destroy()
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, d in enumerate(days):
            tk.Label(self.body, text=d).grid(row=0, column=i, padx=4, pady=2)
        cal = calendar.Calendar(firstweekday=6)
        row = 1
        for week in cal.monthdayscalendar(self.year, self.month):
            col = 0
            for day in week:
                if day == 0:
                    tk.Label(self.body, text='').grid(row=row, column=col, padx=3, pady=3)
                else:
                    btn = tk.Button(self.body, text=str(day), width=4, command=lambda d=day: self.select(d))
                    dt = date(self.year, self.month, day)
                    if dt < date.today():
                        btn.config(state='disabled')
                    btn.grid(row=row, column=col, padx=3, pady=3)
                col += 1
            row += 1

    def select(self, day):
        chosen = date(self.year, self.month, day)
        self.set_callback(chosen.strftime('%Y-%m-%d'))
        self.destroy()

    def prev(self):
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.title_lbl.config(text=f'{calendar.month_name[self.month]} {self.year}')
        self.draw()

    def next(self):
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.title_lbl.config(text=f'{calendar.month_name[self.month]} {self.year}')
        self.draw()

class AppClass(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('RestoBook')
        self.geometry('820x520')
        self.configure(bg='#EFE6DB')
        self.data = load_data()
        self.reservations = self.data.get('reservations', [])
        self.staff_account = Staff('admin', '1234')
        self.build_header()
        self.main_frame = tk.Frame(self, bg=self['bg'])
        self.main_frame.pack(fill='both', expand=True, padx=16, pady=12)
        self.show_home()

    def build_header(self):
        header = tk.Frame(self, bg='#4B2E22', height=64)
        header.pack(fill='x')
        tk.Label(header, text='RestoBook', bg=header['bg'], fg='#F7EDE2', font=('Georgia', 20, 'bold')).pack(side='left', padx=12)
        tk.Label(header, text='Reservasi Online', bg=header['bg'], fg='#F7EDE2', font=('Helvetica', 10)).pack(side='left')
        btn_frame = tk.Frame(header, bg=header['bg'])
        btn_frame.pack(side='right', padx=12)
        tk.Button(btn_frame, text='Masuk sebagai Pelanggan', command=self.show_customer_form, bg='#C69C6D', fg='white', relief='flat').pack(side='left', padx=6)
        tk.Button(btn_frame, text='Masuk sebagai Staf', command=self.staff_login_popup, bg='#C69C6D', fg='white', relief='flat').pack(side='left', padx=6)
        tk.Button(btn_frame, text='Export CSV', command=self.export_csv, bg='#C69C6D', fg='white', relief='flat').pack(side='left', padx=6)

    def clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def show_home(self):
        self.clear_main()
        frame = tk.Frame(self.main_frame, bg=self['bg'])
        frame.pack(fill='both', expand=True)
        tk.Label(frame, text='Selamat datang di RestoBook', font=('Helvetica', 26, 'bold'), bg=self['bg']).pack(pady=(80, 8))
        tk.Label(frame, text='Reservasi meja restoran secara online', font=('Helvetica', 12), bg=self['bg']).pack(pady=(0, 6))
        tk.Label(frame, text=f'Total meja per hari: {TOTAL_TABLES}', font=('Helvetica', 11), bg=self['bg']).pack(pady=(0, 24))
        btn_frame = tk.Frame(frame, bg=self['bg'])
        btn_frame.pack()
        tk.Button(btn_frame, text='Masuk sebagai Pelanggan', font=('Helvetica', 12), width=22, height=2, bg='#C69C6D', fg='white', command=self.show_customer_form).grid(row=0, column=0, padx=12, pady=8)
        tk.Button(btn_frame, text='Masuk sebagai Staf', font=('Helvetica', 12), width=22, height=2, bg='#C69C6D', fg='white', command=self.staff_login_popup).grid(row=0, column=1, padx=12, pady=8)

    def staff_login_popup(self):
        dlg = tk.Toplevel(self)
        dlg.title('Login Staff')
        dlg.geometry('340x220')
        dlg.transient(self)
        tk.Label(dlg, text='Username').pack(pady=6)
        ue = tk.Entry(dlg)
        ue.pack()
        tk.Label(dlg, text='Password').pack(pady=6)
        pe = tk.Entry(dlg, show='*')
        pe.pack()

        def attempt():
            if self.staff_account.check(ue.get().strip(), pe.get().strip()):
                dlg.destroy()
                messagebox.showinfo('Sukses', 'Login berhasil')
                self.show_staff_panel()
            else:
                messagebox.showerror('Gagal', 'Username atau password salah')

        tk.Button(dlg, text='Login', command=attempt, bg='#8C5E3C', fg='white', width=12).pack(pady=12)

    def export_csv(self):
        rows = self.reservations
        if not rows:
            messagebox.showinfo('Info', 'Tidak ada data untuk diekspor')
            return
        path = 'restobook_export.csv'
        with open(path, 'w', encoding='utf-8') as f:
            f.write('id,name,phone,jumlah_orang,date,time,type,table,created_at\n')
            for r in rows:
                f.write(f"{r.get('id')},{r.get('name')},{r.get('phone')},{r.get('jumlah_orang', '1')},{r.get('date')},{r.get('time')},{r.get('type')},{r.get('table')},{r.get('created_at')}\n")
        messagebox.showinfo('Export', 'Data berhasil diekspor ke restobook_export.csv')

    def show_customer_form(self):
        self.clear_main()
        left = tk.Frame(self.main_frame, bg=self['bg'])
        left.pack(side='left', fill='both', expand=True, padx=12, pady=12)
        right = tk.Frame(self.main_frame, bg=self['bg'], width=260)
        right.pack(side='right', fill='y', padx=12, pady=12)
        tk.Label(left, text='Form Reservasi', font=('Helvetica', 18, 'bold'), bg=self['bg']).pack(anchor='w', pady=6)
        form = tk.Frame(left, bg=self['bg'])
        form.pack(anchor='w', pady=4)
        tk.Label(form, text='Nama:', bg=self['bg']).grid(row=0, column=0, sticky='w', pady=6)
        name_e = tk.Entry(form, width=28)
        name_e.grid(row=0, column=1, pady=6, padx=6)
        tk.Label(form, text='No HP:', bg=self['bg']).grid(row=1, column=0, sticky='w', pady=6)
        phone_e = tk.Entry(form, width=28)
        phone_e.grid(row=1, column=1, pady=6, padx=6)
        tk.Label(form, text='Jumlah Orang:', bg=self['bg']).grid(row=2, column=0, sticky='w', pady=6)
        jumlah_e = tk.Entry(form, width=28)
        jumlah_e.grid(row=2, column=1, pady=6, padx=6)
        tk.Label(form, text='Tanggal:', bg=self['bg']).grid(row=3, column=0, sticky='w', pady=6)
        date_e = tk.Entry(form, width=20)
        date_e.grid(row=3, column=1, pady=6, padx=6, sticky='w')

        def open_cal():
            CalendarPopup(self, lambda s: date_e.delete(0, 'end') or date_e.insert(0, s))

        tk.Button(form, text='Pilih', command=open_cal, bg='#8C5E3C', fg='white', relief='flat').grid(row=3, column=2, padx=6)
        tk.Label(form, text='Jam (HH:MM):', bg=self['bg']).grid(row=4, column=0, sticky='w', pady=6)
        time_e = tk.Entry(form, width=20)
        time_e.grid(row=4, column=1, pady=6, padx=6, sticky='w')
        tk.Label(form, text='Tipe:', bg=self['bg']).grid(row=5, column=0, sticky='w', pady=6)
        tipe_var = tk.StringVar(value='Umum')
        tk.Radiobutton(form, text='Umum', variable=tipe_var, value='Umum', bg=self['bg']).grid(row=5, column=1, sticky='w')
        tk.Radiobutton(form, text='VIP', variable=tipe_var, value='VIP', bg=self['bg']).grid(row=5, column=1, sticky='e')

        def submit():
            name = name_e.get().strip()
            phone = phone_e.get().strip()
            jumlah_orang = jumlah_e.get().strip()
            tanggal = date_e.get().strip()
            waktu = time_e.get().strip()
            tipe = tipe_var.get()
            if not (name and phone and jumlah_orang and tanggal and waktu):
                messagebox.showwarning('Data kurang', 'Isi semua kolom')
                return
            try:
                jumlah = int(jumlah_orang)
                if jumlah < 1 or jumlah > 20:
                    messagebox.showwarning('Jumlah Orang', 'Jumlah orang harus antara 1–20')
                    return
            except ValueError:
                messagebox.showwarning('Format', 'Jumlah orang harus berupa angka')
                return
            try:
                dt = datetime.strptime(tanggal, '%Y-%m-%d').date()
                if dt < date.today():
                    messagebox.showwarning('Tanggal salah', 'Pilih tanggal yang valid')
                    return
            except:
                messagebox.showwarning('Format', 'Format tanggal harus YYYY-MM-DD')
                return
            if available_tables(self.reservations, tanggal) <= 0:
                messagebox.showinfo('Penuh', 'Maaf, meja pada hari itu sudah habis.')
                return
            newr = {
                'id': gen_id(),
                'name': name,
                'phone': phone,
                'jumlah_orang': jumlah_orang,
                'date': tanggal,
                'time': waktu,
                'type': tipe,
                'table': None,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.reservations.append(newr)
            self.data['reservations'] = self.reservations
            save_data(self.data)
            self.show_confirmation(newr)
            name_e.delete(0, 'end')
            phone_e.delete(0, 'end')
            jumlah_e.delete(0, 'end')
            date_e.delete(0, 'end')
            time_e.delete(0, 'end')

        tk.Button(left, text='Submit Reservasi', command=submit, bg='#C69C6D', fg='white', width=20, relief='flat').pack(pady=12)
        tk.Label(right, text='Info & Sisa Meja', font=('Helvetica', 12, 'bold'), bg=self['bg']).pack(pady=6)
        lb = tk.Listbox(right, width=30, height=10)
        lb.pack(pady=4)
        for i in range(7):
            d = date.today() + timedelta(days=i)
            dstr = d.strftime('%Y-%m-%d')
            lb.insert('end', f"{dstr} — Sisa meja: {available_tables(self.reservations, dstr)}")

    def show_confirmation(self, reservation):
        d = tk.Toplevel(self)
        d.title('Konfirmasi')
        d.geometry('420x160')
        tk.Label(d, text='Reservasi telah berhasil.', font=('Helvetica', 14, 'bold')).pack(pady=8)
        tk.Label(d, text=f"Harap hadir pada {reservation['date']} pukul {reservation['time']}.\nJumlah orang: {reservation['jumlah_orang']}", font=('Helvetica', 11)).pack(pady=4)
        tk.Button(d, text='Tutup', command=d.destroy, bg='#8C5E3C', fg='white').pack(pady=8)

    def show_staff_panel(self):
        self.clear_main()
        top = tk.Frame(self.main_frame, bg=self['bg'])
        top.pack(fill='x', pady=6)
        tk.Label(top, text='Data Reservasi', bg=self['bg'], font=('Helvetica', 16, 'bold')).pack(side='left')
        filter_entry = tk.Entry(top, width=14)
        filter_entry.pack(side='left', padx=8)

        def fill_today():
            filter_entry.delete(0, 'end')
            filter_entry.insert(0, date.today().strftime('%Y-%m-%d'))

        tk.Button(top, text='Hari Ini', command=fill_today, bg='#8C5E3C', fg='white').pack(side='left', padx=6)

        tree = ttk.Treeview(
            self.main_frame,
            columns=('id', 'name', 'phone', 'jumlah_orang', 'date', 'time', 'type', 'table', 'created'),
            show='headings',
            height=12
        )

        headers = {
            'id': 'ID',
            'name': 'Nama',
            'phone': 'HP',
            'jumlah_orang': 'Jml Orang',
            'date': 'Tanggal',
            'time': 'Jam',
            'type': 'Tipe',
            'table': 'Meja',
            'created': 'Dibuat'
        }

        for col, title in headers.items():
            tree.heading(col, text=title)
            if col == 'jumlah_orang':
                tree.column(col, width=80, anchor='center')
            elif col == 'phone':
                tree.column(col, width=100)
            elif col == 'name':
                tree.column(col, width=120)
            else:
                tree.column(col, width=90)

        tree.pack(fill='both', expand=True, pady=10)

        def refresh():
            target = filter_entry.get().strip()
            for r in tree.get_children():
                tree.delete(r)
            rows = []
            if not target:
                rows = self.reservations
            else:
                for r in self.reservations:
                    if r.get('date') == target:
                        rows.append(r)
            for r in rows:
                tableval = r['table'] if r['table'] is not None else '-'
                tree.insert('', 'end', values=(
                    r['id'], r['name'], r['phone'], r.get('jumlah_orang', '1'), r['date'], r['time'],
                    r['type'], tableval, r['created_at']
                ))

        refresh()

        def assign_table():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("Pilih Data", "Pilih reservasi dahulu")
                return
            values = tree.item(sel, 'values')
            rid = values[0]
            for r in self.reservations:
                if r['id'] == rid:
                    if r['table'] is None:
                        free = get_unused_tables(self.reservations, r['date'])
                        if not free:
                            messagebox.showerror("Error", "Tidak ada meja kosong!")
                            return
                        assigned = random.choice(free)
                        r['table'] = assigned
                        save_data(self.data)
                        refresh()
                        messagebox.showinfo("Sukses", f"Otomatis memberi meja: {assigned}")
                        return
                    else:
                        messagebox.showinfo("Info", "Meja sudah ditetapkan.")
                        return

        tk.Button(self.main_frame, text='Assign Meja Otomatis', bg='#C69C6D', fg='white', command=assign_table).pack(pady=10)

        def delete_reservation():
            sel = tree.focus()
            if not sel:
                messagebox.showwarning("Pilih Data", "Pilih reservasi dahulu")
                return
            values = tree.item(sel, 'values')
            rid = values[0]
            confirm = messagebox.askyesno("Konfirmasi", "Yakin ingin menghapus reservasi ini?")
            if not confirm:
                return
            new_reservations = []
            for r in self.reservations:
                if r['id'] != rid:
                    new_reservations.append(r)
            self.reservations = new_reservations
            self.data['reservations'] = self.reservations
            save_data(self.data)
            refresh()
            messagebox.showinfo("Sukses", "Reservasi berhasil dihapus.")

        tk.Button(self.main_frame, text='Hapus Reservasi', bg='#8C3C3C', fg='white', command=delete_reservation).pack(pady=6)

App = AppClass()
App.mainloop()
