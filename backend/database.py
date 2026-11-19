import os, sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
BASE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB=os.path.join(BASE,'database','smartcampus.db')
def connect_db():
 os.makedirs(os.path.dirname(DB),exist_ok=True); c=sqlite3.connect(DB,timeout=15); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def init_db():
 c=connect_db(); c.executescript('''
 CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,username TEXT UNIQUE,password_hash TEXT,role TEXT);
 CREATE TABLE IF NOT EXISTS facilities(id INTEGER PRIMARY KEY,name TEXT,facility_type TEXT,location TEXT);
 CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),facility_id INTEGER REFERENCES facilities(id),booking_date TEXT,start_time TEXT,end_time TEXT,purpose TEXT,status TEXT DEFAULT 'Requested',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY,reported_by INTEGER REFERENCES users(id),title TEXT,description TEXT,priority TEXT,status TEXT DEFAULT 'Intake',assigned_to INTEGER REFERENCES users(id),notes TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,user_id INTEGER,action TEXT,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 ''')
 if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]==0:
  for n,u,p,r in [('Admin','admin','admin123','Administrator'),('Faculty User','faculty','faculty123','Faculty'),('Facility Manager','manager','manager123','Facility Manager'),('Technician','technician','tech123','Technician'),('Approver','approver','approve123','Approver'),('Student User','student','student123','Student')]: c.execute('INSERT INTO users(name,username,password_hash,role) VALUES(?,?,?,?)',(n,u,generate_password_hash(p),r))
 if c.execute('SELECT COUNT(*) FROM facilities').fetchone()[0]==0: c.executemany('INSERT INTO facilities(name,facility_type,location) VALUES(?,?,?)',[('Computer Lab 1','Laboratory','Block A'),('Seminar Hall','Hall','Block B'),('Classroom 101','Classroom','Block A'),('Computer Lab 2','Laboratory','Block C')])
 c.commit(); c.close()
def log(c,uid,action,details): c.execute('INSERT INTO audit(user_id,action,details) VALUES(?,?,?)',(uid,action,details))
def verify(pwh,p): return check_password_hash(pwh,p)
