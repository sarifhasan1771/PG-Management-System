import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector

# ================== CONFIG ==================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "your_password_here"   
DB_NAME = "pg_db"

PRIMARY = "#1f6aa5"
PRIMARY_DARK = "#144870"

# ================== DATABASE ==================
try:
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cur.execute(f"USE {DB_NAME}")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS boys (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        room_no VARCHAR(20) NOT NULL,
        address VARCHAR(255),
        phone VARCHAR(15)
    )
    """)
    conn.commit()
except mysql.connector.Error as err:
    print("MySQL connection error:", err)
    raise SystemExit

selected_id = None

# ================== APP SETUP ==================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("PG Management System")
root.geometry("1100x680")
root.minsize(1000, 620)


# ================== FUNCTIONS ==================
def style_table():
    dark = ctk.get_appearance_mode() == "Dark"
    bg = "#2b2b2b" if dark else "#ffffff"
    fg = "#ffffff" if dark else "#1a1a1a"
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background=bg, fieldbackground=bg, foreground=fg,
                    rowheight=34, borderwidth=0, font=("Segoe UI", 11))
    style.configure("Treeview.Heading", background=PRIMARY, foreground="white",
                    font=("Segoe UI", 11, "bold"), relief="flat", padding=8)
    style.map("Treeview", background=[("selected", PRIMARY_DARK)],
              foreground=[("selected", "white")])
    style.map("Treeview.Heading", background=[("active", PRIMARY_DARK)])
    table.tag_configure("odd", background="#333333" if dark else "#eef3f8")
    table.tag_configure("even", background=bg)


def fill_table(rows):
    for item in table.get_children():
        table.delete(item)
    for i, r in enumerate(rows):
        table.insert("", "end", values=r, tags=("odd" if i % 2 else "even",))


def update_stats():
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT room_no) FROM boys")
    total, rooms = cur.fetchone()
    lbl_total.configure(text=str(total))
    lbl_rooms.configure(text=str(rooms))
    lbl_footer.configure(text=f"Total records: {total}")


def load_data():
    cur.execute("SELECT id, name, room_no, address, phone FROM boys ORDER BY id")
    fill_table(cur.fetchall())
    update_stats()


def clear_fields():
    global selected_id
    selected_id = None
    for e in (e_name, e_room, e_addr, e_phone):
        e.delete(0, "end")
    table.selection_remove(table.selection())
    e_name.focus()


def validate():
    name, room = e_name.get().strip(), e_room.get().strip()
    phone = e_phone.get().strip()
    if not name or not room:
        messagebox.showwarning("Missing Data", "Name and Room No are required.")
        return False
    if phone and (not phone.isdigit() or len(phone) != 10):
        messagebox.showwarning("Invalid Phone", "Phone number must be 10 digits.")
        return False
    return True


def add_boy():
    if not validate():
        return
    cur.execute("INSERT INTO boys (name, room_no, address, phone) VALUES (%s,%s,%s,%s)",
                (e_name.get().strip(), e_room.get().strip(),
                 e_addr.get().strip(), e_phone.get().strip()))
    conn.commit()
    load_data()
    clear_fields()
    messagebox.showinfo("Success", "Record added successfully.")


def on_select(event):
    global selected_id
    sel = table.focus()
    if not sel:
        return
    v = table.item(sel, "values")
    selected_id = v[0]
    for e in (e_name, e_room, e_addr, e_phone):
        e.delete(0, "end")
    e_name.insert(0, v[1])
    e_room.insert(0, v[2])
    e_addr.insert(0, v[3])

    e_phone.insert(0, v[4])


def update_boy():
    if selected_id is None:
        messagebox.showwarning("Select", "Please select a row from the table first.")
        return
    if not validate():
        return
    cur.execute("UPDATE boys SET name=%s, room_no=%s, address=%s, phone=%s WHERE id=%s",
                (e_name.get().strip(), e_room.get().strip(),
                 e_addr.get().strip(), e_phone.get().strip(), selected_id))
    conn.commit()
    load_data()
    clear_fields()
    messagebox.showinfo("Success", "Record updated successfully.")


def delete_boy():
    if selected_id is None:
        messagebox.showwarning("Select", "Please select a row from the table first.")
        return
    if messagebox.askyesno("Confirm Delete", "Do you  want to delete this record?"):
        cur.execute("DELETE FROM boys WHERE id=%s", (selected_id,))
        conn.commit()
        load_data()
        clear_fields()


def search_boy(event=None):
    key = f"%{e_search.get().strip()}%"
    cur.execute("""SELECT id, name, room_no, address, phone FROM boys
                   WHERE name LIKE %s OR room_no LIKE %s OR phone LIKE %s
                   ORDER BY id""", (key, key, key))
    fill_table(cur.fetchall())


def toggle_theme():
    ctk.set_appearance_mode("light" if theme_switch.get() == 0 else "dark")
    style_table()
    search_boy()


# ================== HEADER ==================
header = ctk.CTkFrame(root, height=70, corner_radius=0, fg_color=PRIMARY)
header.pack(fill="x")
header.pack_propagate(False)

ctk.CTkLabel(header, text="🏠  PG Management System",
             font=ctk.CTkFont("Segoe UI", 24, "bold"),
             text_color="white").pack(side="left", padx=25)

theme_switch = ctk.CTkSwitch(header, text="Dark Mode", text_color="white",
                             command=toggle_theme, progress_color="#0d3a5c")
theme_switch.select()
theme_switch.pack(side="right", padx=25)

# ================== BODY ==================
body = ctk.CTkFrame(root, fg_color="transparent")
body.pack(fill="both", expand=True, padx=20, pady=15)
body.grid_columnconfigure(1, weight=1)
body.grid_rowconfigure(0, weight=1)

# ---------- LEFT PANEL ----------
left = ctk.CTkFrame(body, width=330, corner_radius=14)
left.grid(row=0, column=0, sticky="ns", padx=(0, 15))
left.grid_propagate(False)

# Stat cards
stats = ctk.CTkFrame(left, fg_color="transparent")
stats.pack(fill="x", padx=15, pady=(15, 5))
stats.grid_columnconfigure((0, 1), weight=1)


def make_card(parent, col, title, color):
    card = ctk.CTkFrame(parent, corner_radius=12, fg_color=color)
    card.grid(row=0, column=col, padx=5, sticky="ew")
    value = ctk.CTkLabel(card, text="0", font=ctk.CTkFont("Segoe UI", 26, "bold"),
                         text_color="white")
    value.pack(pady=(10, 0))
    ctk.CTkLabel(card, text=title, font=ctk.CTkFont("Segoe UI", 12),
                 text_color="white").pack(pady=(0, 10))
    return value


lbl_total = make_card(stats, 0, "Total Boys", "#2e9e5b")
lbl_rooms = make_card(stats, 1, "Rooms Used", "#e08a1e")

ctk.CTkLabel(left, text="Boy Details", font=ctk.CTkFont("Segoe UI", 16, "bold")
             ).pack(anchor="w", padx=20, pady=(15, 5))


def make_field(parent, label, placeholder):
    ctk.CTkLabel(parent, text=label, font=ctk.CTkFont("Segoe UI", 12)
                 ).pack(anchor="w", padx=20, pady=(8, 0))
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=36, corner_radius=8)
    entry.pack(fill="x", padx=20, pady=(2, 0))
    return entry


e_name = make_field(left, "Full Name", "e.g. Sarif Hasan")
e_room = make_field(left, "Room No", "e.g. 101")
e_addr = make_field(left, "Address", "Home address")
e_phone = make_field(left, "Phone No", "10 digit number")

# Buttons
btns = ctk.CTkFrame(left, fg_color="transparent")
btns.pack(fill="x", padx=15, pady=20)
btns.grid_columnconfigure((0, 1), weight=1)


def make_btn(text, cmd, color, hover, r, c):
    ctk.CTkButton(btns, text=text, command=cmd, height=38, corner_radius=8,
                  fg_color=color, hover_color=hover,
                  font=ctk.CTkFont("Segoe UI", 13, "bold")
                  ).grid(row=r, column=c, padx=5, pady=5, sticky="ew")


make_btn("➕  Add", add_boy, "#2e9e5b", "#238048", 0, 0)
make_btn("✏️  Update", update_boy, PRIMARY, PRIMARY_DARK, 0, 1)
make_btn("🗑  Delete", delete_boy, "#d64545", "#a93232", 1, 0)
make_btn("🧹  Clear", clear_fields, "#6b7280", "#4b5563", 1, 1)

# ---------- RIGHT PANEL ----------
right = ctk.CTkFrame(body, corner_radius=14)
right.grid(row=0, column=1, sticky="nsew")
right.grid_rowconfigure(1, weight=1)
right.grid_columnconfigure(0, weight=1)

top = ctk.CTkFrame(right, fg_color="transparent")
top.grid(row=0, column=0, sticky="ew", padx=15, pady=15)
top.grid_columnconfigure(0, weight=1)

e_search = ctk.CTkEntry(top, placeholder_text="🔍  Search by name, room or phone...",
                        height=38, corner_radius=8)
e_search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
e_search.bind("<KeyRelease>", search_boy)

ctk.CTkButton(top, text="Show All", width=100, height=38, corner_radius=8,
              command=lambda: (e_search.delete(0, "end"), load_data())
              ).grid(row=0, column=1)

# Table
table_frame = ctk.CTkFrame(right, fg_color="transparent")
table_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))
table_frame.grid_rowconfigure(0, weight=1)
table_frame.grid_columnconfigure(0, weight=1)

cols = ("id", "name", "room_no", "address", "phone")
table = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
widths = {"id": 50, "name": 180, "room_no": 90, "address": 250, "phone": 130}
for c in cols:
    table.heading(c, text=c.replace("_", " ").title())
    table.column(c, width=widths[c], anchor="w" if c in ("name", "address") else "center")
table.grid(row=0, column=0, sticky="nsew")

scroll = ctk.CTkScrollbar(table_frame, command=table.yview)
scroll.grid(row=0, column=1, sticky="ns")
table.configure(yscrollcommand=scroll.set)
table.bind("<<TreeviewSelect>>", on_select)

lbl_footer = ctk.CTkLabel(right, text="Total records: 0", text_color="gray")
lbl_footer.grid(row=2, column=0, sticky="e", padx=20, pady=(0, 10))

# ================== START ==================
style_table()
load_data()
root.mainloop()