from flask import Flask,jsonify,request,session,render_template
from functools import wraps
from datetime import datetime
from backend.database import connect_db,init_db,log,verify
app=Flask(__name__,template_folder='../frontend/templates',static_folder='../frontend/static'); app.secret_key='academic-demo-change-before-deployment'; init_db()
def me():
 if not session.get('uid'): return None
 c=connect_db(); u=c.execute('SELECT id,name,username,role FROM users WHERE id=?',(session['uid'],)).fetchone(); c.close(); return dict(u) if u else None
def auth(fn):
 @wraps(fn)
 def w(*a,**k):
  if not me(): return jsonify(error='Please log in'),401
  return fn(*a,**k)
 return w
def roles(*allowed):
 def dec(fn):
  @wraps(fn)
  def w(*a,**k):
   u=me()
   if not u:return jsonify(error='Please log in'),401
   if u['role'] not in allowed:return jsonify(error='Permission denied'),403
   return fn(*a,**k)
  return w
 return dec
@app.get('/')
def home(): return render_template('index.html')
@app.get('/api/health')
def health(): return jsonify(status='OK')
@app.post('/api/login')
def login():
 d=request.get_json() or {}; c=connect_db(); u=c.execute('SELECT * FROM users WHERE username=?',(d.get('username',''),)).fetchone()
 if not u or not verify(u['password_hash'],d.get('password','')): c.close(); return jsonify(error='Invalid username or password'),401
 session['uid']=u['id']; log(c,u['id'],'Login','User logged in'); c.commit(); c.close(); return jsonify(id=u['id'],name=u['name'],role=u['role'])
@app.post('/api/logout')
@auth
def logout(): session.clear(); return jsonify(message='Signed out')
@app.get('/api/me')
@auth
def get_me(): return jsonify(me())
@app.get('/api/dashboard')
@auth
def dashboard():
 c=connect_db(); d={'facilities':c.execute('SELECT COUNT(*) FROM facilities').fetchone()[0],'bookings':c.execute('SELECT COUNT(*) FROM bookings').fetchone()[0],'pending':c.execute("SELECT COUNT(*) FROM bookings WHERE status='Requested'").fetchone()[0],'tickets':c.execute("SELECT COUNT(*) FROM tickets WHERE status NOT IN ('Closed','Resolved')").fetchone()[0]}; c.close(); return jsonify(d)
@app.get('/api/facilities')
@auth
def facilities():
 c=connect_db(); r=c.execute('SELECT * FROM facilities').fetchall(); c.close(); return jsonify([dict(x) for x in r])
@app.get('/api/bookings')
@auth
def bookings():
 c=connect_db(); r=c.execute('SELECT b.*,u.name user_name,f.name facility_name FROM bookings b JOIN users u ON u.id=b.user_id JOIN facilities f ON f.id=b.facility_id ORDER BY b.id DESC').fetchall(); c.close(); return jsonify([dict(x) for x in r])
@app.post('/api/bookings')
@auth
def add_booking():
 d=request.get_json() or {}; fields=['facility_id','booking_date','start_time','end_time','purpose']
 if any(not d.get(k) for k in fields): return jsonify(error='Complete all booking fields'),400
 try:
  datetime.strptime(d['booking_date'],'%Y-%m-%d'); s=datetime.strptime(d['start_time'],'%H:%M'); e=datetime.strptime(d['end_time'],'%H:%M'); fid=int(d['facility_id'])
  if s>=e:return jsonify(error='End time must be after start time'),400
 except (ValueError,TypeError):return jsonify(error='Invalid date, time or facility'),400
 u=me(); c=connect_db()
 if not c.execute('SELECT id FROM facilities WHERE id=?',(fid,)).fetchone():c.close();return jsonify(error='Facility not found'),404
 cur=c.execute('INSERT INTO bookings(user_id,facility_id,booking_date,start_time,end_time,purpose) VALUES(?,?,?,?,?,?)',(u['id'],fid,d['booking_date'],d['start_time'],d['end_time'],d['purpose'])); bid=cur.lastrowid; log(c,u['id'],'Booking requested',f'Booking #{bid}'); c.commit(); c.close(); return jsonify(message='Booking request submitted',booking_id=bid,status='Requested'),201
@app.put('/api/bookings/<int:bid>/decision')
@auth
@roles('Facility Manager','Administrator','Approver')
def decision(bid):
 d=request.get_json() or {}; choice=d.get('decision')
 if choice not in ('approve','reject'):return jsonify(error='Choose approve or reject'),400
 u=me(); c=connect_db()
 try:
  c.execute('BEGIN IMMEDIATE'); b=c.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone()
  if not b or b['status']!='Requested':c.rollback();return jsonify(error='Request not found or already processed'),404
  status='Rejected'
  if choice=='approve':
   clash=c.execute("SELECT id FROM bookings WHERE facility_id=? AND booking_date=? AND status IN ('Approved','Confirmed','In Use') AND start_time < ? AND end_time > ?",(b['facility_id'],b['booking_date'],b['end_time'],b['start_time'])).fetchone()
   if clash:c.rollback();return jsonify(error='Overlapping approved booking exists'),409
   status='Approved'
  c.execute('UPDATE bookings SET status=? WHERE id=?',(status,bid)); log(c,u['id'],'Booking '+status,f'Booking #{bid}'); c.commit(); return jsonify(message='Booking '+status.lower(),status=status)
 finally:c.close()
@app.get('/api/tickets')
@auth
def tickets():
 c=connect_db();r=c.execute('SELECT t.*,u.name reporter,tech.name technician FROM tickets t JOIN users u ON u.id=t.reported_by LEFT JOIN users tech ON tech.id=t.assigned_to ORDER BY t.id DESC').fetchall();c.close();return jsonify([dict(x) for x in r])
@app.post('/api/tickets')
@auth
def add_ticket():
 d=request.get_json() or {}; title=d.get('title','').strip(); desc=d.get('description','').strip()
 if not title or not desc:return jsonify(error='Enter title and description'),400
 txt=(title+' '+desc).lower(); priority='High' if any(x in txt for x in ['urgent','danger','fire','electric','leak']) else 'Medium' if any(x in txt for x in ['broken','fault','not working','damage']) else 'Low'
 u=me();c=connect_db();cur=c.execute('INSERT INTO tickets(reported_by,title,description,priority) VALUES(?,?,?,?)',(u['id'],title,desc,priority));tid=cur.lastrowid;log(c,u['id'],'Ticket created',f'Ticket #{tid}');c.commit();c.close();return jsonify(message='Ticket created',ticket_id=tid,priority=priority),201
@app.put('/api/tickets/<int:tid>')
@auth
def update_ticket(tid):
 u=me();d=request.get_json() or {};c=connect_db();t=c.execute('SELECT * FROM tickets WHERE id=?',(tid,)).fetchone()
 if not t:c.close();return jsonify(error='Ticket not found'),404
 if u['role'] not in ('Facility Manager','Administrator','Technician'):c.close();return jsonify(error='Permission denied'),403
 if u['role']=='Technician' and t['assigned_to']!=u['id']:c.close();return jsonify(error='Ticket is not assigned to you'),403
 status=d.get('status',t['status']); allowed=['Intake','Assigned','Inspection','Pending Work','Resolved','Closed']
 if status not in allowed:c.close();return jsonify(error='Invalid status'),400
 if status=='Closed' and u['role'] not in ('Facility Manager','Administrator'):c.close();return jsonify(error='Only manager/admin can close'),403
 assignee=d.get('assigned_to',t['assigned_to'])
 if assignee is not None and not c.execute("SELECT id FROM users WHERE id=? AND role='Technician'",(assignee,)).fetchone():c.close();return jsonify(error='Invalid technician'),400
 c.execute('UPDATE tickets SET assigned_to=?,status=?,notes=? WHERE id=?',(assignee,status,d.get('notes',t['notes']),tid));log(c,u['id'],'Ticket updated',f'Ticket #{tid}: {status}');c.commit();c.close();return jsonify(message='Ticket updated',status=status)
@app.get('/api/audit')
@auth
@roles('Facility Manager','Administrator','Approver')
def audit():
 c=connect_db();r=c.execute('SELECT a.*,u.name user_name FROM audit a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC').fetchall();c.close();return jsonify([dict(x) for x in r])
if __name__=='__main__':app.run(host='0.0.0.0',port=5000)
