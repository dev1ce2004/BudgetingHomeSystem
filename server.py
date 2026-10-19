import argparse, datetime as dt, ipaddress, json, os, secrets, socket, sqlite3, ssl, threading, uuid
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
BASE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('BHS_DATA',str(BASE/'data'))); DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'budget.sqlite3'
LOCK=threading.RLock()
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
def init():
 with db() as c:
  c.executescript('''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,name TEXT NOT NULL,token TEXT UNIQUE,admin INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS entries(id TEXT PRIMARY KEY,owner TEXT REFERENCES users(id),version INTEGER NOT NULL,payload TEXT NOT NULL); CREATE TABLE IF NOT EXISTS ops(id TEXT PRIMARY KEY,result TEXT NOT NULL); CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL);''')
  if not c.execute('SELECT 1 FROM users').fetchone():
   c.execute('INSERT INTO users VALUES(?,?,?,1)',(str(uuid.uuid4()),'Administrator',secrets.token_urlsafe(32)))
  c.execute('INSERT OR IGNORE INTO settings VALUES(1,?)',(json.dumps({'categories':['Hrana','Stanovanje','Prijevoz','Zdravlje','Zabava','Ostalo','Plaća'],'accounts':['Gotovina','Banka'],'budget':0}),))
def backup():
 folder=DATA/'backups'; folder.mkdir(exist_ok=True)
 with db() as src, sqlite3.connect(folder/(dt.date.today().isoformat()+'.sqlite3')) as dst: src.backup(dst)
def validate(p):
 if not isinstance(p,dict): raise ValueError('Neispravan unos')
 if p.get('type') not in ['expense','income','transfer']: raise ValueError('Neispravna vrsta')
 if type(p.get('cents')) is not int or not 0<p['cents']<=100000000000: raise ValueError('Neispravan iznos')
 dt.date.fromisoformat(p['date'])
 for k in ['category','account','note','toAccount']:
  if not isinstance(p.get(k,''),str) or len(p.get(k,''))>1000: raise ValueError('Neispravan tekst')
 if not p.get('account'): raise ValueError('Odaberi račun')
 if p['type']=='transfer' and (not p.get('toAccount') or p['toAccount']==p['account']): raise ValueError('Odaberi različite račune')
 if type(p.get('deleted',False)) is not bool: raise ValueError('Neispravno brisanje')
 return {k:p.get(k,False if k=='deleted' else '') for k in ['type','cents','date','category','account','note','toAccount','deleted']}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw): super().__init__(*a,directory=str(BASE/'web'),**kw)
 def log_message(self,*a): pass
 def send_json(self,status,p):
  b=json.dumps(p,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
 def user(self,c): return c.execute('SELECT * FROM users WHERE token=?',(self.headers.get('Authorization','').removeprefix('Bearer '),)).fetchone()
 def do_GET(self):
  if self.path.startswith('/api/'):
   with db() as c:
    u=self.user(c)
    if not u: return self.send_json(401,{'error':'Provjeri pristupni ključ'})
    if self.path=='/api/state':
     entries=[dict(json.loads(r['payload']),id=r['id'],owner=r['owner'],version=r['version']) for r in c.execute('SELECT * FROM entries')]
     return self.send_json(200,{'me':{'id':u['id'],'name':u['name'],'admin':bool(u['admin'])},'users':[dict(r) for r in c.execute('SELECT id,name,admin FROM users')],'entries':entries,'settings':json.loads(c.execute('SELECT payload FROM settings').fetchone()[0])})
    if self.path=='/api/export':
     return self.send_json(200,{'exported':dt.datetime.now(dt.timezone.utc).isoformat(),'entries':[dict(json.loads(r['payload']),id=r['id'],owner=r['owner'],version=r['version']) for r in c.execute('SELECT * FROM entries')],'users':[dict(r) for r in c.execute('SELECT id,name,admin FROM users')],'settings':json.loads(c.execute('SELECT payload FROM settings').fetchone()[0])})
    return self.send_json(404,{'error':'Nepoznati zahtjev'})
  allowed=['/','/index.html','/app.js','/style.css','/sw.js','/manifest.json','/icon.svg','/icon-192.png','/icon-512.png']
  if self.path.split('?')[0] not in allowed: return self.send_error(404)
  self.path=self.path.split('?')[0]; return super().do_GET()
 def do_POST(self):
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n<=0 or n>100000: raise ValueError('Neispravna veličina zahtjeva')
   p=json.loads(self.rfile.read(n))
   with LOCK,db() as c:
    u=self.user(c)
    if not u: return self.send_json(401,{'error':'Provjeri pristupni ključ'})
    if self.path=='/api/op':
     op=str(uuid.UUID(p['opId'])); eid=str(uuid.UUID(p['id'])); payload=validate(p['payload'])
     prev=c.execute('SELECT result FROM ops WHERE id=?',(op,)).fetchone()
     if prev: return self.send_json(200,json.loads(prev[0]))
     row=c.execute('SELECT * FROM entries WHERE id=?',(eid,)).fetchone()
     if row and row['owner']!=u['id'] and not u['admin']: return self.send_json(403,{'error':'Možeš uređivati samo svoje unose'})
     if p.get('baseVersion')!=(row['version'] if row else 0): return self.send_json(409,{'error':'Sukob izmjena. Preuzmi verziju računala ili spremi svoju nakon pregleda.','current':dict(json.loads(row['payload']),id=eid,owner=row['owner'],version=row['version']) if row else None})
     version=(row['version'] if row else 0)+1; owner=row['owner'] if row else u['id']
     c.execute('INSERT OR REPLACE INTO entries VALUES(?,?,?,?)',(eid,owner,version,json.dumps(payload)))
     result={'id':eid,'version':version,'owner':owner}; c.execute('INSERT INTO ops VALUES(?,?)',(op,json.dumps(result))); c.commit()
     return self.send_json(200,result)
    if not u['admin']: return self.send_json(403,{'error':'Potreban je administrator'})
    if self.path=='/api/users':
     name=p.get('name','').strip()
     if not name or len(name)>80: raise ValueError('Neispravno ime')
     uid=str(uuid.uuid4()); token=secrets.token_urlsafe(32); c.execute('INSERT INTO users VALUES(?,?,?,0)',(uid,name,token)); c.commit(); return self.send_json(200,{'id':uid,'name':name,'token':token})
    if self.path=='/api/revoke':
     if p['id']==u['id']: raise ValueError('Ne možeš opozvati vlastiti pristup')
     c.execute('UPDATE users SET token=NULL WHERE id=?',(p['id'],)); c.commit(); return self.send_json(200,{'ok':True})
    if self.path=='/api/settings':
     if type(p.get('budget')) is not int or p['budget']<0: raise ValueError('Neispravan budžet')
     for k in ['categories','accounts']:
      if not isinstance(p.get(k),list) or not p[k] or len(p[k])>100 or any(not isinstance(x,str) or not x.strip() or len(x)>80 for x in p[k]): raise ValueError('Neispravan popis')
     c.execute('UPDATE settings SET payload=? WHERE id=1',(json.dumps({k:p[k] for k in ['categories','accounts','budget']}),)); c.commit(); return self.send_json(200,{'ok':True})
    if self.path=='/api/backup': backup(); return self.send_json(200,{'ok':True})
    return self.send_json(404,{'error':'Nepoznati zahtjev'})
  except (ValueError,KeyError,TypeError,json.JSONDecodeError): return self.send_json(400,{'error':'Neispravan zahtjev ili podaci'})
  except Exception: return self.send_json(500,{'error':'Pogreška spremanja; pokušaj ponovno'})
def certificate(ip):
 from cryptography import x509
 from cryptography.x509.oid import NameOID
 from cryptography.hazmat.primitives import hashes,serialization
 from cryptography.hazmat.primitives.asymmetric import rsa
 meta=DATA/'cert-ip.txt'
 if meta.exists() and meta.read_text()==ip and (DATA/'server.pem').exists(): return
 now=dt.datetime.now(dt.timezone.utc); cakey=rsa.generate_private_key(public_exponent=65537,key_size=2048); name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'BudgetingHomeSystem Local CA')])
 ca=x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(cakey.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-dt.timedelta(days=1)).not_valid_after(now+dt.timedelta(days=3650)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True).add_extension(x509.KeyUsage(False,False,False,False,False,True,True,False,False),critical=True).sign(cakey,hashes.SHA256())
 key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
 cert=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'BudgetingHomeSystem')])).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-dt.timedelta(days=1)).not_valid_after(now+dt.timedelta(days=365)).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1')),x509.IPAddress(ipaddress.ip_address(ip))]),critical=False).add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True).sign(cakey,hashes.SHA256())
 (DATA/'server.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM)); (DATA/'server-key.pem').write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())); (DATA/'BudgetingHomeSystem-CA.crt').write_bytes(ca.public_bytes(serialization.Encoding.PEM)); meta.write_text(ip)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--ip'); ap.add_argument('--http',action='store_true',help='Samo za lokalno testiranje, bez PWA'); ap.add_argument('--port',type=int,default=8443); args=ap.parse_args(); init(); backup()
 ip=args.ip
 if not ip:
  try: ip=socket.gethostbyname(socket.gethostname())
  except OSError: ip='127.0.0.1'
 server=ThreadingHTTPServer(('127.0.0.1' if args.http else '0.0.0.0',args.port),Handler)
 if not args.http:
  certificate(ip); ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(DATA/'server.pem',DATA/'server-key.pem'); server.socket=ctx.wrap_socket(server.socket,server_side=True)
 with db() as c: token=c.execute('SELECT token FROM users WHERE admin=1').fetchone()[0]
 (DATA/'admin-access.txt').write_text(f'https://{ip}:{args.port}/#token={token}',encoding='utf-8')
 print(f'Hub: https://{ip}:{args.port}\nAdmin pristup: data/admin-access.txt\nCertifikat: data/BudgetingHomeSystem-CA.crt',flush=True)
 def routine():
  while True:
   threading.Event().wait(3600)
   try: backup()
   except Exception: pass
 threading.Thread(target=routine,daemon=True).start()
 try: server.serve_forever()
 except KeyboardInterrupt: server.server_close()
if __name__=='__main__': main()
