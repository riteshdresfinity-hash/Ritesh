import os
import time
import json
import threading
import webbrowser
import sqlite3
import hashlib
import secrets
import csv
import io
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (Flask, render_template_string, request, redirect,
                   url_for, session, g, Response, flash)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=365)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
FLASK_URL = 'http://127.0.0.1:5000'

# ─────────────────────────── DATABASE ────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def open_browser(url, delay=1.0):
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_open, daemon=True).start()

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'family',
            owner_id INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            shop TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(owner_id) REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_tx_owner ON transactions(owner_id);
        CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);
        """)
        cols = [row[1] for row in db.execute("PRAGMA table_info(transactions)").fetchall()]
        if 'payment_type' not in cols:
            db.execute("ALTER TABLE transactions ADD COLUMN payment_type TEXT NOT NULL DEFAULT 'cash'")

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()
def check_password(pw, h): return hash_password(pw) == h

# ─────────────────────────── AUTH HELPERS ────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'owner':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def get_owner_id():
    if session.get('role') == 'owner':
        return session['user_id']
    return session.get('owner_id')

# ─────────────────────────── HTML BASE ───────────────────────────

BASE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>HomeLedger</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{
  --cr:#faf7f2;--cw:#fff9f0;--ink:#1a1208;--inks:#3d3020;
  --mu:#8a7a68;--br:#e8dece;--am:#c9882a;--al:#f5e6c8;
  --ad:#9c6820;--gn:#3a7d5a;--gl:#d4ede0;--rd:#c0392b;--rl:#fde8e6;
  --sh:0 2px 16px rgba(100,80,40,.10);--sh2:0 1px 4px rgba(100,80,40,.08);
  --rr:12px;--sw:240px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:'DM Sans',sans-serif;background:var(--cr);color:var(--ink);font-size:15px;line-height:1.6}
h1,h2,h3,h4{font-family:'Fraunces',serif;font-weight:600;line-height:1.2}
a{color:inherit;text-decoration:none}

/* LAYOUT */
.shell{display:flex;min-height:100vh}
.sb{width:var(--sw);background:var(--ink);color:#e8dece;display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:100;overflow-y:auto}
.sb-logo{padding:28px 24px 20px;border-bottom:1px solid rgba(255,255,255,.08)}
.sb-logo h2{font-size:1.3rem;color:#fff;letter-spacing:-.3px}
.sb-logo span{color:var(--am)}
.sb-user{padding:16px 24px;font-size:.8rem;color:var(--mu);border-bottom:1px solid rgba(255,255,255,.06)}
.sb-user strong{color:#d0c8b8;display:block;font-size:.9rem}
.rb{display:inline-block;padding:2px 8px;border-radius:20px;font-size:.7rem;font-weight:500;margin-top:4px}
.ro{background:var(--am);color:var(--ink)}
.rf{background:var(--gn);color:#fff}
nav{flex:1;padding:12px 0}
.ni{display:flex;align-items:center;gap:10px;padding:11px 24px;color:#b0a898;text-decoration:none;font-size:.88rem;font-weight:400;transition:all .15s;border-left:3px solid transparent}
.ni:hover{background:rgba(255,255,255,.05);color:#fff}
.ni.active{background:rgba(201,136,42,.12);color:var(--am);border-left-color:var(--am)}
.ni-ico{font-size:1rem;width:18px;text-align:center}
.nb{margin:12px 16px;padding:10px 16px;background:rgba(192,57,43,.15);color:#e88;border:none;border-radius:8px;cursor:pointer;font-size:.85rem;font-family:inherit;width:calc(100% - 32px);text-align:left;transition:background .15s}
.nb:hover{background:rgba(192,57,43,.3)}
.main{margin-left:var(--sw);flex:1;min-height:100vh;background:var(--cr)}
.tb{background:var(--cw);border-bottom:1px solid var(--br);padding:18px 36px;display:flex;align-items:center;justify-content:space-between}
.tb h1{font-size:1.5rem}
.pb{padding:32px 36px;max-width:1100px}

/* CARDS */
.cr{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:32px}
.cd{background:var(--cw);border:1px solid var(--br);border-radius:var(--rr);padding:24px;box-shadow:var(--sh2)}
.cl{font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--mu);margin-bottom:8px}
.cv{font-size:1.8rem;font-family:'Fraunces',serif;font-weight:600}
.cv.gn{color:var(--gn)}.cv.am{color:var(--ad)}
.cs{font-size:.78rem;color:var(--mu);margin-top:4px}

/* TABLE */
.tw{background:var(--cw);border:1px solid var(--br);border-radius:var(--rr);overflow:hidden;box-shadow:var(--sh2)}
.th{padding:18px 24px;border-bottom:1px solid var(--br);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.th h3{font-size:1rem}
table{width:100%;border-collapse:collapse}
th{padding:12px 16px;background:#f5efea;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mu);text-align:left;font-weight:500;border-bottom:1px solid var(--br)}
td{padding:13px 16px;border-bottom:1px solid var(--br);font-size:.88rem;color:var(--inks)}
tr:last-child td{border-bottom:none}
tr:hover td{background:#fdf5ea}
.tto{font-weight:500;color:var(--ink);font-family:'Fraunces',serif}
.tf{padding:14px 24px;background:#f5efea;border-top:1px solid var(--br);display:flex;justify-content:space-between;align-items:center;font-size:.88rem;color:var(--inks)}
.tf strong{font-family:'Fraunces',serif;font-size:1.05rem;color:var(--ink)}
.es{padding:48px;text-align:center;color:var(--mu);font-size:.9rem}

/* BUTTONS */
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 18px;border-radius:8px;font-size:.85rem;font-weight:500;cursor:pointer;border:none;font-family:inherit;text-decoration:none;transition:all .15s}
.bp{background:var(--am);color:var(--ink)}.bp:hover{background:var(--ad);color:#fff}
.bg{background:transparent;border:1px solid var(--br);color:var(--inks)}.bg:hover{background:var(--br)}
.bd{background:var(--rl);color:var(--rd);border:1px solid #f0c0bb}.bd:hover{background:var(--rd);color:#fff}
.bsm{padding:5px 11px;font-size:.78rem}

/* FORMS */
.fc{background:var(--cw);border:1px solid var(--br);border-radius:var(--rr);padding:32px;max-width:580px;box-shadow:var(--sh2)}
.fg{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fm{margin-bottom:18px;display:flex;flex-direction:column}
.fm.full{grid-column:1/-1}
label{font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:var(--mu);margin-bottom:6px}
input,select{padding:10px 14px;border:1px solid var(--br);border-radius:8px;background:var(--cr);font-size:.9rem;font-family:inherit;color:var(--ink);outline:none;transition:border-color .15s}
input:focus,select:focus{border-color:var(--am);box-shadow:0 0 0 3px var(--al)}
.tp{padding:14px 18px;background:var(--al);border-radius:8px;font-family:'Fraunces',serif;font-size:1.2rem;color:var(--ad);margin-bottom:20px}

/* ALERTS */
.ae{padding:12px 18px;border-radius:8px;margin-bottom:20px;font-size:.88rem}
.aer{background:var(--rl);color:var(--rd);border:1px solid #f0c0bb}
.aes{background:var(--gl);color:var(--gn);border:1px solid #b0d8c4}

/* AUTH */
.aw{min-height:100vh;background:var(--cr);display:flex;align-items:center;justify-content:center;padding:32px}
.ac{background:var(--cw);border:1px solid var(--br);border-radius:16px;padding:44px;width:100%;max-width:400px;box-shadow:0 8px 40px rgba(100,80,40,.12)}
.ac h1{font-size:1.8rem;margin-bottom:4px}
.ac p{color:var(--mu);font-size:.9rem;margin-bottom:28px}
.afo{text-align:center;margin-top:20px;font-size:.85rem;color:var(--mu)}
.afo a{color:var(--ad)}

/* FILTERS */
.fr{display:flex;gap:12px;flex-wrap:wrap;padding:16px 24px;border-bottom:1px solid var(--br);background:#fdf8f2}
.fr input,.fr select{flex:1;min-width:150px}

/* CHART */
.cw2{background:var(--cw);border:1px solid var(--br);border-radius:var(--rr);padding:24px;margin-bottom:32px;box-shadow:var(--sh2)}
.ct{font-size:.95rem;font-weight:600;margin-bottom:16px}
.bc{display:flex;align-items:flex-end;gap:6px;height:120px}
.bco{display:flex;flex-direction:column;align-items:center;gap:4px;flex:1}
.bar{background:linear-gradient(180deg,var(--am) 0%,var(--ad) 100%);border-radius:4px 4px 0 0;width:100%;min-height:4px}
.bl{font-size:.65rem;color:var(--mu);text-align:center}

/* FAMILY */
.ml{display:flex;flex-direction:column;gap:10px}
.mr{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;background:var(--cw);border:1px solid var(--br);border-radius:var(--rr)}
.mi{display:flex;align-items:center;gap:12px}
.av{width:36px;height:36px;border-radius:50%;background:var(--al);display:flex;align-items:center;justify-content:center;font-size:.85rem;font-weight:600;color:var(--ad)}

@media(max-width:700px){
  .sb{width:200px}.main{margin-left:200px}
  .pb{padding:20px}.tb{padding:14px 20px}
  .fg{grid-template-columns:1fr}
}
</style>
</head>
<body>
CONTENT_PLACEHOLDER
</body>
</html>'''

def page(content):
    return BASE.replace('CONTENT_PLACEHOLDER', content)

def sidebar(active=''):
    role = session.get('role','')
    owner_links = ''
    if role == 'owner':
        owner_links = f'''
        <a href="/add" class="ni {'active' if active=='add' else ''}"><span class="ni-ico">➕</span> Add Transaction</a>
        <a href="/family" class="ni {'active' if active=='family' else ''}"><span class="ni-ico">👨‍👩‍👧</span> Manage Family</a>
        <a href="/export" class="ni"><span class="ni-ico">⬇️</span> Export CSV</a>'''
    rb_class = 'ro' if role == 'owner' else 'rf'
    return f'''<div class="shell">
<aside class="sb">
  <div class="sb-logo"><h2>Home<span>Ledger</span></h2></div>
  <div class="sb-user">
    <strong>{session.get('username','')}</strong>
    <span class="rb {rb_class}">{role.capitalize()}</span>
  </div>
  <nav>
    <a href="/dashboard" class="ni {'active' if active=='dashboard' else ''}"><span class="ni-ico">📊</span> Dashboard</a>
    {owner_links}
    <a href="/history" class="ni {'active' if active=='history' else ''}"><span class="ni-ico">📋</span> History</a>
  </nav>
  <form action="/logout" method="post" style="padding:0 0 20px">
    <button class="nb">🚪 Logout</button>
  </form>
</aside>
<div class="main">'''

# ─────────────────────────── ROUTES ──────────────────────────────

@app.route('/')
def index():
    return redirect('/dashboard' if 'user_id' in session else '/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session: return redirect('/dashboard')
    err = suc = ''
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','')
        row = get_db().execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
        if row and check_password(p, row['password_hash']):
            session.clear()
            session.permanent = True
            session['user_id'] = row['id']
            session['username'] = row['username']
            session['role'] = row['role']
            session['owner_id'] = row['owner_id']
            return redirect('/dashboard')
        err = 'Invalid username or password.'
    suc = request.args.get('msg','')
    return page(f'''<div class="aw"><div class="ac">
  <h1>Welcome back</h1>
  <p>Sign in to HomeLedger</p>
  {'<div class="ae aer">'+err+'</div>' if err else ''}
  {'<div class="ae aes">'+suc+'</div>' if suc else ''}
  <form method="post">
    <div class="fm"><label>Username</label><input name="username" type="text" placeholder="Your username" required autocomplete="username"></div>
    <div class="fm"><label>Password</label><input name="password" type="password" placeholder="Your password" required autocomplete="current-password"></div>
    <button class="btn bp" style="width:100%;justify-content:center;padding:12px" type="submit">Sign In</button>
  </form>
  <div class="afo">No account? <a href="/signup">Create one</a></div>
</div></div>''')

@app.route('/signup', methods=['GET','POST'])
def signup():
    err = ''
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','')
        p2 = request.form.get('password2','')
        if not u or not p: err='All fields required.'
        elif len(u)<3: err='Username min 3 chars.'
        elif len(p)<1: err='Password min 1 char.'
        elif p!=p2: err='Passwords do not match.'
        else:
            try:
                get_db().execute('INSERT INTO users(username,password_hash,role) VALUES(?,?,?)',
                    (u,hash_password(p),'owner'))
                get_db().commit()
                return redirect('/login?msg=Account created! Sign in now.')
            except sqlite3.IntegrityError:
                err='Username already taken.'
    return page(f'''<div class="aw"><div class="ac">
  <h1>Create Account</h1>
  <p>You will be the household Owner</p>
  {'<div class="ae aer">'+err+'</div>' if err else ''}
  <form method="post">
    <div class="fm"><label>Username</label><input name="username" type="text" placeholder="Choose a username" required></div>
    <div class="fm"><label>Password</label><input name="password" type="password" placeholder="Min 6 characters" required></div>
    <div class="fm"><label>Confirm Password</label><input name="password2" type="password" placeholder="Repeat password" required></div>
    <button class="btn bp" style="width:100%;justify-content:center;padding:12px" type="submit">Create Account</button>
  </form>
  <div class="afo">Have an account? <a href="/login">Sign in</a></div>
</div></div>''')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    oid = get_owner_id()
    s = db.execute('SELECT COUNT(*) cnt,COALESCE(SUM(total),0) tot,COALESCE(AVG(total),0) avg FROM transactions WHERE owner_id=?',(oid,)).fetchone()
    recent = db.execute('SELECT * FROM transactions WHERE owner_id=? ORDER BY date DESC,id DESC LIMIT 5',(oid,)).fetchall()
    monthly = list(reversed(db.execute("""SELECT strftime('%m/%y',date) mo,SUM(total) tot FROM transactions
        WHERE owner_id=? GROUP BY strftime('%Y-%m',date) ORDER BY strftime('%Y-%m',date) DESC LIMIT 6""",(oid,)).fetchall()))
    mx = max((r['tot'] for r in monthly),default=1)
    bars = ''.join(f'<div class="bco"><div class="bar" style="height:{max(4,int(r["tot"]/mx*110))}px" title="Rs{r["tot"]:,.0f}"></div><div class="bl">{r["mo"]}</div></div>' for r in monthly)
    chart = f'<div class="cw2"><div class="ct">Monthly Spending</div><div class="bc">{bars}</div></div>' if monthly else ''
    rows = ''.join(f'<tr><td>{r["date"]}</td><td>{r["shop"]}</td><td>{r["product"]}</td><td>{r["quantity"]}</td><td>Rs{r["price"]:,.2f}</td><td class="tto">Rs{r["total"]:,.2f}</td></tr>' for r in recent) or '<tr><td colspan="6" class="es">No transactions yet. Add one to get started!</td></tr>'
    return page(sidebar('dashboard')+f'''
  <div class="tb"><h1>Dashboard</h1></div>
  <div class="pb">
    <div class="cr">
      <div class="cd"><div class="cl">Total Spent</div><div class="cv am">Rs{s["tot"]:,.2f}</div><div class="cs">All time</div></div>
      <div class="cd"><div class="cl">Transactions</div><div class="cv gn">{s["cnt"]}</div><div class="cs">Total entries</div></div>
      <div class="cd"><div class="cl">Avg per Purchase</div><div class="cv">Rs{s["avg"]:,.2f}</div><div class="cs">Per transaction</div></div>
    </div>
    {chart}
    <div class="tw">
      <div class="th"><h3>Recent Transactions</h3><a href="/history" class="btn bg bsm">View All →</a></div>
      <table><thead><tr><th>Date</th><th>Shop</th><th>Product</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead>
      <tbody>{rows}</tbody></table>
    </div>
  </div>
</div></div>''')

@app.route('/add', methods=['GET','POST'])
@login_required
@owner_required
def add_transaction():
    err = suc = ''
    if request.method == 'POST':
        d    = request.form.get('date','').strip()
        shop = request.form.get('shop','').strip()
        payment_type = request.form.get('payment_type','cash')
        # collect items: names[], prices[], qtys[]
        names  = request.form.getlist('item_name[]')
        prices = request.form.getlist('item_price[]')
        qtys   = request.form.getlist('item_qty[]')
        if not d or not shop:
            err = 'Date and shop name are required.'
        elif payment_type not in ('cash','card'):
            err = 'Select a valid payment method.'
        elif not names or all(n.strip()=='' for n in names):
            err = 'Add at least one item.'
        else:
            db = get_db()
            saved = 0
            try:
                for name, price_s, qty_s in zip(names, prices, qtys):
                    name = name.strip()
                    if not name: continue
                    price = float(price_s) if price_s else 0.0
                    qty   = float(qty_s)   if qty_s   else 0.0
                    if price <= 0 or qty <= 0:
                        err = f'Item "{name}" has invalid price or quantity.'; break
                    total = round(price * qty, 2)
                    db.execute(
                        'INSERT INTO transactions(owner_id,date,shop,product,quantity,price,total,payment_type) VALUES(?,?,?,?,?,?,?,?)',
                        (session['user_id'], d, shop, name, qty, price, total, payment_type))
                    saved += 1
                if not err:
                    db.commit()
                    net = sum(float(p)*float(q) for p,q in zip(prices,qtys) if p and q)
                    suc = f'Purchase saved! {saved} item(s) · NET ₹{net:,.2f}'
            except (ValueError, TypeError):
                err = 'Invalid price or quantity value.'

    today_val = date.today().isoformat()
    ADD_CSS = '''
<style>
.lp-card{background:#fff;border-radius:18px;padding:28px 32px;max-width:820px;border:1px solid var(--br);box-shadow:0 2px 20px rgba(80,80,160,.07)}
.lp-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.lp-top h2{font-size:1.25rem;font-weight:700;color:var(--ink)}
.lp-plus{width:40px;height:40px;border-radius:50%;border:2px solid #6366f1;background:#f0f0ff;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#6366f1;font-size:1.3rem;font-weight:700;transition:all .15s;flex-shrink:0}
.lp-plus:hover{background:#6366f1;color:#fff}
.lp-meta{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid var(--br)}
.lp-mf{display:flex;align-items:center;gap:12px}
.lp-ml{font-size:.78rem;font-weight:700;color:var(--ink);white-space:nowrap;letter-spacing:.04em}
.lp-mf input{flex:1;padding:10px 16px;border:1.5px solid #e2e4ee;border-radius:10px;font-size:.9rem;font-family:inherit;color:var(--ink);background:#f7f8fc;outline:none;transition:border-color .15s}
.lp-mf input:focus{border-color:#6366f1;background:#fff;box-shadow:0 0 0 3px rgba(99,102,241,.12)}
.items-wrap{display:flex;flex-direction:column;gap:12px;margin-bottom:16px}
.item-row{display:flex;align-items:center;gap:10px;background:#f7f8fc;border:1.5px solid #e8eaf0;border-radius:12px;padding:14px 16px;transition:border-color .15s}
.item-row:focus-within{border-color:#6366f1}
.i-name{flex:1;display:flex;flex-direction:column;gap:4px}
.i-lbl{font-size:.62rem;font-weight:700;letter-spacing:.06em;color:#8b90aa;text-transform:uppercase}
.i-name input{border:none;background:transparent;font-size:.92rem;color:var(--ink);outline:none;font-family:inherit;width:100%}
.i-name input::placeholder{color:#b0b4c8}
.i-div{width:1px;height:40px;background:#e2e4ee;flex-shrink:0}
.i-num{display:flex;flex-direction:column;align-items:center;gap:4px}
.i-num input{width:80px;border:none;background:transparent;font-size:.95rem;color:var(--ink);text-align:center;outline:none;font-family:inherit}
.i-op{font-size:.9rem;color:#b0b4c8;font-weight:600;padding-top:20px}
.i-tot{font-size:1rem;font-weight:700;color:#6366f1;min-width:76px;text-align:right;padding-top:20px}
.i-del{background:none;border:none;cursor:pointer;color:#c0c4d8;font-size:1rem;padding:4px;padding-top:20px;transition:color .15s;flex-shrink:0;display:none}
.i-del:hover{color:#e24b4a}
.add-row-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:13px;border:none;background:none;color:#6366f1;font-size:.88rem;font-weight:700;cursor:pointer;font-family:inherit;transition:opacity .15s}
.add-row-btn:hover{opacity:.7}
.add-row-btn .ci{width:22px;height:22px;border-radius:50%;border:2px solid #6366f1;display:flex;align-items:center;justify-content:center;font-size:.85rem;font-weight:700}
.lp-bottom{display:flex;align-items:center;justify-content:space-between;padding-top:20px;border-top:1px solid var(--br);margin-top:8px;flex-wrap:wrap;gap:12px}
.lp-net{display:flex;align-items:baseline;gap:10px}
.lp-netlbl{font-size:.95rem;font-weight:700;color:var(--ink)}
.lp-netval{font-size:2rem;font-weight:800;color:#6366f1;letter-spacing:-.5px;font-family:'Fraunces',serif}
.lp-btns{display:flex;gap:12px}
.lp-save{padding:12px 28px;background:#6366f1;color:#fff;border:none;border-radius:12px;font-size:.9rem;font-weight:700;cursor:pointer;font-family:inherit;transition:background .15s}
.lp-save:hover{background:#4f52d4}
.lp-cancel{padding:12px 20px;background:#fff;color:var(--ink);border:1.5px solid #dde0ec;border-radius:12px;font-size:.9rem;font-weight:600;cursor:pointer;font-family:inherit;transition:all .15s;text-decoration:none;display:inline-flex;align-items:center}
.lp-cancel:hover{background:#f0f2f8}
</style>'''

    ADD_SCRIPT = '''
<script>
var rowCount = 0;
function addRow(name,price,qty){
  rowCount++;
  var id = rowCount;
  var row = document.createElement('div');
  row.className = 'item-row'; row.id = 'row_'+id;
  row.innerHTML = `
    <div class="i-name">
      <span class="i-lbl">Product Name -</span>
      <input type="text" name="item_name[]" placeholder="Item name" value="${name||''}" oninput="updRow(${id})">
    </div>
    <div class="i-div"></div>
    <div class="i-num">
      <span class="i-lbl">Price -</span>
      <input type="number" name="item_price[]" min="0" step="0.01" placeholder="0" value="${price||''}" oninput="updRow(${id})" style="width:80px">
    </div>
    <span class="i-op">x</span>
    <div class="i-num">
      <span class="i-lbl">Quantity -</span>
      <input type="number" name="item_qty[]" min="0.001" step="any" placeholder="1" value="${qty||1}" oninput="updRow(${id})" style="width:80px">
    </div>
    <span class="i-op">=</span>
    <div class="i-tot" id="itot_${id}">₹0.00</div>
    <button type="button" class="i-del" id="del_${id}" onclick="delRow(${id})">✕</button>`;
  document.getElementById('itemsWrap').appendChild(row);
  updDelBtns();
  if(name===undefined) row.querySelector('input[name="item_name[]"]').focus();
  updRow(id);
}
function delRow(id){
  document.getElementById('row_'+id).remove();
  updDelBtns(); updNet();
}
function updDelBtns(){
  var rows = document.querySelectorAll('.item-row');
  rows.forEach(function(r){
    var d = r.querySelector('.i-del');
    if(d) d.style.display = rows.length > 1 ? 'block' : 'none';
  });
}
function updRow(id){
  var row = document.getElementById('row_'+id);
  var p = parseFloat(row.querySelector('input[name="item_price[]"]').value)||0;
  var q = parseFloat(row.querySelector('input[name="item_qty[]"]').value)||0;
  document.getElementById('itot_'+id).textContent = '₹'+(p*q).toFixed(2);
  updNet();
}
function updNet(){
  var ps = document.querySelectorAll('input[name="item_price[]"]');
  var qs = document.querySelectorAll('input[name="item_qty[]"]');
  var net = 0;
  for(var i=0;i<ps.length;i++) net += (parseFloat(ps[i].value)||0)*(parseFloat(qs[i].value)||0);
  document.getElementById('netVal').textContent = '₹'+net.toFixed(2);
}
addRow();
</script>'''

    return page(sidebar('add') + ADD_CSS + f'''
  <div class="tb"><h1>Log New Purchase</h1></div>
  <div class="pb">
    {'<div class="ae aer">'+err+'</div>' if err else ''}
    {'<div class="ae aes">'+suc+'</div>' if suc else ''}
    <div class="lp-card">
      <div class="lp-top">
        <h2>Log New Purchase</h2>
        <div class="lp-plus" onclick="addRow()" title="Add item">+</div>
      </div>
      <form method="post" id="lpForm">
        <div class="lp-meta">
          <div class="lp-mf">
            <span class="lp-ml">DATE :-</span>
            <input type="date" name="date" value="{today_val}" required>
          </div>
          <div class="lp-mf">
            <span class="lp-ml">Shop name :-</span>
            <input type="text" name="shop" placeholder="e.g. Walmart" required>
          </div>
          <div class="lp-mf">
            <span class="lp-ml">Payment method :-</span>
            <div style="display:flex;gap:12px;align-items:center">
              <label style="display:inline-flex;align-items:center;gap:8px;font-size:.9rem;color:#4c4b57"><input type="radio" name="payment_type" value="cash" checked> Cash</label>
              <label style="display:inline-flex;align-items:center;gap:8px;font-size:.9rem;color:#4c4b57"><input type="radio" name="payment_type" value="card"> Card</label>
            </div>
          </div>
        </div>
        <div class="items-wrap" id="itemsWrap"></div>
        <button type="button" class="add-row-btn" onclick="addRow()">
          <span class="ci">+</span> ADD another item
        </button>
        <div class="lp-bottom">
          <div class="lp-net">
            <span class="lp-netlbl">NET total =</span>
            <span class="lp-netval" id="netVal">₹0.00</span>
          </div>
          <div class="lp-btns">
            <button type="submit" class="lp-save">Add to Budget</button>
            <a href="/dashboard" class="lp-cancel">Cancel</a>
          </div>
        </div>
      </form>
    </div>
  </div>
</div></div>
''' + ADD_SCRIPT)

@app.route('/edit/<int:tid>', methods=['GET','POST'])
@login_required
@owner_required
def edit_transaction(tid):
    db = get_db()
    tx = db.execute('SELECT * FROM transactions WHERE id=? AND owner_id=?',(tid,session['user_id'])).fetchone()
    if not tx: return redirect('/history')
    err = ''
    if request.method == 'POST':
        d=request.form.get('date',''); shop=request.form.get('shop','').strip(); product=request.form.get('product','').strip(); payment_type=request.form.get('payment_type','cash')
        try:
            qty=float(request.form.get('quantity',0)); price=float(request.form.get('price',0)); total=round(qty*price,2)
        except: err='Invalid values.'
        if payment_type not in ('cash','card'):
            err='Select a valid payment method.'
        if not err:
            db.execute('UPDATE transactions SET date=?,shop=?,product=?,quantity=?,price=?,total=?,payment_type=? WHERE id=? AND owner_id=?',
                (d,shop,product,qty,price,total,payment_type,tid,session['user_id']))
            db.commit(); return redirect('/history')
    payment_type = tx['payment_type'] if 'payment_type' in tx.keys() and tx['payment_type'] else 'cash'
    return page(sidebar('history')+f'''
  <div class="tb"><h1>Edit Transaction</h1></div>
  <div class="pb">
    {'<div class="ae aer">'+err+'</div>' if err else ''}
    <div class="fc">
      <form method="post">
        <div class="fg">
          <div class="fm"><label>Date *</label><input name="date" type="date" value="{tx['date']}" required></div>
          <div class="fm"><label>Shop *</label><input name="shop" type="text" value="{tx['shop']}" required></div>
          <div class="fm full"><label>Product *</label><input name="product" type="text" value="{tx['product']}" required></div>
          <div class="fm"><label>Quantity *</label><input name="quantity" type="number" step="0.001" value="{tx['quantity']}" required id="qty" oninput="calc()"></div>
          <div class="fm"><label>Price/Unit (Rs) *</label><input name="price" type="number" step="0.01" value="{tx['price']}" required id="ppu" oninput="calc()"></div>
          <div class="fm full"><label>Payment Method *</label><div style="display:flex;gap:12px;margin-top:8px"><label style="display:inline-flex;align-items:center;gap:8px;font-size:.9rem;color:#4c4b57"><input type="radio" name="payment_type" value="cash" {'checked' if payment_type=='cash' else ''}> Cash</label><label style="display:inline-flex;align-items:center;gap:8px;font-size:.9rem;color:#4c4b57"><input type="radio" name="payment_type" value="card" {'checked' if payment_type=='card' else ''}> Card</label></div></div>
        </div>
        <div class="tp">Total: Rs<span id="td">{tx['total']:.2f}</span></div>
        <input type="hidden" name="total" id="ti" value="{tx['total']}">
        <div style="display:flex;gap:12px">
          <button class="btn bp" type="submit">Update</button>
          <a href="/history" class="btn bg">Cancel</a>
        </div>
      </form>
    </div>
  </div>
</div></div>
<script>function calc(){{var q=parseFloat(document.getElementById('qty').value)||0,p=parseFloat(document.getElementById('ppu').value)||0,t=(q*p).toFixed(2);document.getElementById('td').textContent=t;document.getElementById('ti').value=t;}}</script>''')

@app.route('/delete/<int:tid>', methods=['POST'])
@login_required
@owner_required
def delete_transaction(tid):
    db = get_db()
    
    tx = db.execute(
        'SELECT date, shop, payment_type FROM transactions WHERE id=? AND owner_id=?',
        (tid, session['user_id'])
    ).fetchone()
    
    if tx:
        db.execute('''
            DELETE FROM transactions 
            WHERE owner_id=? AND date=? AND shop=? AND payment_type=?
        ''', (session['user_id'], tx['date'], tx['shop'], tx['payment_type']))
        
        db.commit()

    return redirect('/history')

@app.route('/history')
@login_required
def history():
    db = get_db(); oid = get_owner_id()
    q = request.args.get('q','').strip()
    df = request.args.get('from',''); dt = request.args.get('to','')
    params = [oid]; where = 'WHERE owner_id=?'
    if q: where+=' AND(LOWER(shop) LIKE ? OR LOWER(product) LIKE ?)'; params+=[f'%{q.lower()}%',f'%{q.lower()}%']
    if df: where+=' AND date>=?'; params.append(df)
    if dt: where+=' AND date<=?'; params.append(dt)
    txs = db.execute(f'SELECT * FROM transactions {where} ORDER BY date DESC,id DESC',params).fetchall()
    grouped = []
    grouped_map = {}
    for r in txs:
        payment_type = r['payment_type'] if 'payment_type' in r.keys() and r['payment_type'] else 'cash'
        key = (r['date'], r['shop'].strip().lower(), payment_type)
        if key not in grouped_map:
            grouped_map[key] = {
                'date': r['date'],
                'shop': r['shop'],
                'payment_type': payment_type,
                'products': [],
                'items': [],
                'total': 0.0,
                'last_id': r['id']
            }
            grouped.append(grouped_map[key])
        grouped_map[key]['items'].append({
            'product': r['product'],
            'quantity': r['quantity'],
            'price': r['price'],
            'total': r['total']
        })
        if r['product'] not in grouped_map[key]['products']:
            grouped_map[key]['products'].append(r['product'])
        grouped_map[key]['total'] += float(r['total'])
        grouped_map[key]['last_id'] = max(grouped_map[key]['last_id'], r['id'])
    tot = sum(g['total'] for g in grouped)
    is_owner = session.get('role')=='owner'
    rows = ''
    for g in grouped:
        shop_name = g['shop'].strip().title()
        products = ', '.join(p.strip().upper() for p in g['products'] if p.strip())
        method = g['payment_type'].capitalize() if g.get('payment_type') else 'Cash'
        breakdown = json.dumps(g['items'], ensure_ascii=False).replace("'", "&#39;")
        if is_owner:
            actions = f'<a href="/edit/{g["last_id"]}" class="hx-icon" title="Edit" onclick="event.stopPropagation()">✏️</a>'
        else:
            actions = '<span class="hx-muted">View only</span>'
        rows += f'''
        <tr onclick="showBreakdown(this)" data-date="{g['date']}" data-shop="{shop_name}" data-breakdown='{breakdown}'>
          <td class="hx-date">{g['date']}</td>
          <td class="hx-shopcell"><strong>{shop_name} ({method})</strong><div class="hx-sub">{products}</div></td>
          <td class="hx-total">₹{g['total']:,.2f}</td>
          <td class="hx-actions">{actions}</td>
        </tr>'''
    if not rows:
        rows = '<tr><td colspan="4" class="es" style="text-align:center;padding:48px;">No transactions found.</td></tr>'
    return page(sidebar('history')+'''
  <div class="pb">
    <style>
      .history-wrap{{max-width:1260px}}
      .history-card{{background:#f7efe2;border:1px solid #e8dcc8;border-radius:24px;box-shadow:0 10px 32px rgba(140,113,78,.12);overflow:hidden}}
      .history-top{{padding:30px 30px 18px}}
      .history-title{{font-family:'DM Sans',sans-serif;font-size:1.25rem;font-weight:700;color:#402a18;margin-bottom:28px}}
      .history-head{{display:flex;align-items:flex-start;justify-content:space-between;gap:24px}}
      .history-search{{position:relative;flex:1;max-width:650px}}
      .history-search::before{{content:'⌕';position:absolute;left:22px;top:50%;transform:translateY(-50%);font-size:1.5rem;color:#b58d5c}}
      .history-search input{{width:100%;height:64px;padding:0 20px 0 66px;border:1px solid #e5d4b8;border-radius:18px;background:#fff6ed;color:#5d4632;font-size:1rem;font-family:inherit;outline:none}}
      .history-search input:focus{{border-color:#c9882a;box-shadow:0 0 0 4px rgba(201,136,42,.15);background:#fff}}
      .history-summary{{min-width:220px;text-align:right;padding-top:4px}}
      .history-summary span{{display:block;font-size:.95rem;color:#8a7b62;margin-bottom:4px}}
      .history-summary strong{{display:block;font-size:2.05rem;line-height:1;color:#8f5c16;font-family:'DM Sans',sans-serif;font-weight:700}}
      .history-table{{position:relative}}
      .history-table::before,.history-table::after{{position:absolute;top:36px;color:#ebdfcf;font-size:2rem;line-height:1}}
      .history-table::before{{content:'‹';left:12px}}
      .history-table::after{{content:'›';right:12px}}
      .history-table table{{width:100%;border-collapse:collapse}}
      .history-table th, .history-table td{{padding:28px 30px;text-align:left}}
      .history-table th{{font-size:.9rem;font-weight:700;color:#7e6546;border-top:1px solid #f0e5d5;border-bottom:1px solid #f0e5d5;background:#fff8ef}}
      .history-table tbody tr{{border-bottom:1px solid #f0e5d5;cursor:pointer}}
      .history-table tbody tr:hover{{background:#fff2dd}}
      .history-table tbody tr:last-child{{border-bottom:none}}
      .history-table td{{font-size:.98rem;color:#4b3420}}
      .hx-date{{width:24%;white-space:nowrap;color:#6d5439}}
      .hx-shopcell strong{{display:block;font-size:1.18rem;color:#3d2916;font-weight:700;letter-spacing:-.02em;margin-bottom:2px}}
      .hx-sub{{font-size:.8rem;color:#937b5f;font-style:italic;letter-spacing:.01em}}
      .hx-total{{font-size:1.05rem;font-weight:700;color:#6d4a18;white-space:nowrap}}
      .hx-actions{{width:120px;white-space:nowrap}}
      .hx-icon{{display:inline-flex;align-items:center;justify-content:center;width:42px;height:42px;border-radius:12px;border:1px solid #e0c7a1;background:#fff3e6;color:#c9882a;text-decoration:none;font-size:1rem}}
      .hx-icon:hover{{background:#fff1dc}}
      .hx-muted{{color:#9b8b79;font-size:.85rem}}
      .hx-modal{position:fixed;inset:0;background:rgba(15,23,42,.58);display:none;align-items:center;justify-content:center;z-index:9999;backdrop-filter:blur(4px);padding:24px;}
      .hx-modal.active{display:flex !important;}
      .hx-modal-card{background:#ffffff;border-radius:32px;max-width:560px;width:100%;box-shadow:0 40px 80px rgba(15,23,42,.18);overflow:hidden;min-width:320px;}
      .hx-modal-header{position:relative;padding:28px 28px 16px;display:flex;flex-direction:column;gap:6px;background:#f8fafc;}
      .hx-modal-title{font-size:1.7rem;font-weight:800;color:#111827;margin:0;line-height:1.05;}
      .hx-modal-sub{font-size:.95rem;color:#6b7280;}
      .hx-modal-close{position:absolute;top:20px;right:20px;width:38px;height:38px;border:none;border-radius:50%;background:#e2e8f0;color:#475569;font-size:1.1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;}
      .hx-modal-close:hover{background:#cbd5e1;}
      .hx-modal-body{padding:22px 24px 0;display:grid;gap:16px;max-height:calc(100vh - 240px);overflow-y:auto;}
      .hx-item-card{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:18px 20px;background:#f8f9ff;border:1px solid #e5e7f0;border-radius:22px;}
      .hx-item-left{display:flex;flex-direction:column;gap:6px;min-width:0;}
      .hx-item-name{font-size:1rem;font-weight:800;color:#111827;}
      .hx-item-meta{font-size:.9rem;color:#6b7280;}
      .hx-item-total{font-size:1.05rem;font-weight:800;color:#4338ca;white-space:nowrap;}
      .hx-modal-footer{margin-top:22px;padding:22px 24px 24px;background:#3730a3;color:#fff;display:flex;align-items:center;justify-content:space-between;gap:16px;border-top:1px solid rgba(255,255,255,.12);}
      .hx-footer-label{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.75);font-weight:700;}
      .hx-footer-total{font-size:1.7rem;font-weight:800;}
      @media(max-width:520px){.hx-modal-card{margin:16px}.hx-modal-header{padding:22px 20px 14px}.hx-modal-body{padding:18px 20px 0}.hx-modal-footer{padding:18px 20px 20px}.hx-item-card{flex-direction:column;align-items:flex-start;}}
      @media(max-width:500px){.hx-item-card{flex-direction:column;align-items:flex-start;gap:12px}}
      @media(max-width:900px){.history-head{flex-direction:column}.history-summary{text-align:left}}
      @media(max-width:700px){.history-top{padding:22px 20px 14px}.history-table{overflow-x:auto}.history-table th,.history-table td{padding:20px}}
    </style>
    <div class="history-wrap">
      <div class="history-card">
        <div class="history-top">
          <div class="history-title">Transaction History</div>
          <div class="history-head">
            <form method="get" class="history-search">
              <input name="q" type="text" placeholder="Search shop or product..." value="{q}">
            </form>
            <div class="history-summary">
              <span>Total Filtered</span>
              <strong>₹{tot:,.2f}</strong>
            </div>
          </div>
        </div>
        <div class="history-table">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Shop & Products</th>
                <th>Total</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  <div class="hx-modal" id="hxModal">
    <div class="hx-modal-card">
      <div class="hx-modal-header">
        <div>
          <div class="hx-modal-title" id="hxModalTitle">Transaction breakdown</div>
          <div class="hx-modal-sub" id="hxModalSub" style="font-size:.9rem;color:#8a7f67;margin-top:4px"></div>
        </div>
        <button class="hx-modal-close" onclick="closeBreakdown()">×</button>
      </div>
      <div class="hx-modal-body" id="hxModalBody"></div>
      <div class="hx-modal-footer">
        <span class="hx-footer-label">Net total</span>
        <span class="hx-footer-total" id="hxFooterTotal">₹0.00</span>
      </div>
    </div>
  </div>
  <script>
    function showBreakdown(row) {
      var breakdown;
      try { breakdown = JSON.parse(row.dataset.breakdown || '[]'); }
      catch (e) { breakdown = []; }
      var title = row.dataset.shop || 'Transaction';
      var date = row.dataset.date || '';
      var body = document.getElementById('hxModalBody');
      var subtitle = document.getElementById('hxModalSub');
      subtitle.textContent = date;
      body.innerHTML = '';
      var total = 0;
      if (!breakdown.length) {
        body.innerHTML = '<div style="padding:16px;color:#6b7280;">No details available.</div>';
      } else {
        breakdown.forEach(function(item) {
          total += parseFloat(item.total) || 0;
          var rowEl = document.createElement('div');
          rowEl.className = 'hx-item-card';
          rowEl.innerHTML = '<div class="hx-item-left"><div class="hx-item-name">' + item.product + '</div><div class="hx-item-meta">Rs' + parseFloat(item.price).toFixed(2) + ' × ' + item.quantity + '</div></div><div class="hx-item-total">Rs' + parseFloat(item.total).toFixed(2) + '</div>';
          body.appendChild(rowEl);
        });
      }
      document.getElementById('hxFooterTotal').textContent = '₹' + total.toFixed(2);
      document.getElementById('hxModalTitle').textContent = title;
      var modal = document.getElementById('hxModal');
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
    function closeBreakdown() {
      var modal = document.getElementById('hxModal');
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closeBreakdown();
    });
    document.getElementById('hxModal').addEventListener('click', function(e) {
      if (e.target === this) closeBreakdown();
    });
  </script>
</div></div>'''
    .replace('{q}', q)
    .replace('{tot}', f"{tot:,.2f}")
    .replace('{rows}', rows))

@app.route('/family', methods=['GET','POST'])
@login_required
@owner_required
def family():
    db = get_db(); err = suc = ''
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            u=request.form.get('username','').strip(); p=request.form.get('password','')
            if not u or not p: err='All fields required.'
            elif len(p)<1: err='Password min 1 char.'
            else:
                try:
                    db.execute('INSERT INTO users(username,password_hash,role,owner_id) VALUES(?,?,?,?)',
                        (u,hash_password(p),'family',session['user_id']))
                    db.commit(); suc=f'"{u}" added as family member.'
                except sqlite3.IntegrityError: err='Username already taken.'
        elif action=='remove':
            mid=request.form.get('mid')
            db.execute('DELETE FROM users WHERE id=? AND owner_id=? AND role=?',(mid,session['user_id'],'family'))
            db.commit(); suc='Member removed.'
    members = db.execute('SELECT id,username,created_at FROM users WHERE owner_id=? AND role=?',(session['user_id'],'family')).fetchall()
    mrows = ''.join(f'''<div class="mr">
      <div class="mi"><div class="av">{m["username"][0].upper()}</div>
      <div><div style="font-weight:500">{m["username"]}</div><div style="font-size:.75rem;color:var(--mu)">Family · Read only</div></div></div>
      <form method="post" onsubmit="return confirm('Remove {m['username']}?')">
        <input type="hidden" name="action" value="remove">
        <input type="hidden" name="mid" value="{m['id']}">
        <button class="btn bd bsm">Remove</button>
      </form></div>''' for m in members) or '<div class="es" style="padding:32px">No family members yet.</div>'
    return page(sidebar('family')+f'''
  <div class="tb"><h1>Manage Family</h1></div>
  <div class="pb">
    {'<div class="ae aer">'+err+'</div>' if err else ''}
    {'<div class="ae aes">'+suc+'</div>' if suc else ''}
    <div style="display:grid;grid-template-columns:1fr 1.2fr;gap:28px;align-items:start">
      <div class="fc">
        <h3 style="margin-bottom:16px">Add Family Member</h3>
        <p style="font-size:.85rem;color:var(--mu);margin-bottom:20px">Family members can view all transactions but cannot add, edit, or delete.</p>
        <form method="post">
          <input type="hidden" name="action" value="add">
          <div class="fm"><label>Username</label><input name="username" type="text" placeholder="e.g. mom_viewer" required></div>
          <div class="fm"><label>Password (min 6 chars)</label><input name="password" type="password" required></div>
          <button class="btn bp" type="submit">Add Member</button>
        </form>
      </div>
      <div>
        <h3 style="margin-bottom:16px">Members ({len(members)})</h3>
        <div class="ml">{mrows}</div>
      </div>
    </div>
  </div>
</div></div>''')

@app.route('/export')
@login_required
@owner_required
def export_csv():
    txs = get_db().execute('SELECT date,shop,product,quantity,price,total,payment_type FROM transactions WHERE owner_id=? ORDER BY date DESC',(session['user_id'],)).fetchall()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['Date','Shop','Product','Quantity','Price/Unit','Total','Payment Type'])
    for r in txs: w.writerow([r['date'],r['shop'],r['product'],r['quantity'],r['price'],r['total'],r['payment_type']])
    fname=f"budget_{session['username']}_{date.today().isoformat()}.csv"
    return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment;filename={fname}'})

# ─────────────────────────── MAIN ────────────────────────────────

if __name__ == '__main__':
    init_db()
    app.run()
