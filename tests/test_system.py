import importlib.util,json,os,tempfile,threading,unittest,urllib.request,urllib.error,uuid,sqlite3
from pathlib import Path
class SystemTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();os.environ['BHS_DATA']=cls.tmp.name
  spec=importlib.util.spec_from_file_location('bhs',Path(__file__).resolve().parents[1]/'server.py');cls.app=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.app);cls.app.init()
  with cls.app.db() as c:cls.admin=c.execute('SELECT token FROM users').fetchone()[0]
  cls.server=cls.app.ThreadingHTTPServer(('127.0.0.1',0),cls.app.Handler);threading.Thread(target=cls.server.serve_forever,daemon=True).start();cls.url='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.tmp.cleanup()
 def request(self,path,data=None,token=None):
  r=urllib.request.Request(self.url+'/api/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+(token or self.admin),'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(r) as f:return f.status,json.load(f)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def op(self):return {'id':str(uuid.uuid4()),'opId':str(uuid.uuid4()),'baseVersion':0,'payload':{'type':'expense','cents':3500,'date':'2026-10-09','category':'Hrana','account':'Banka','note':'Test','deleted':False}}
 def test_auth(self):self.assertEqual(self.request('state',token='bad')[0],401)
 def test_duplicate_and_conflict(self):
  p=self.op();a=self.request('op',p);self.assertEqual(a[0],200);self.assertEqual(a,self.request('op',p));p['opId']=str(uuid.uuid4());self.assertEqual(self.request('op',p)[0],409)
 def test_permissions_and_visibility(self):
  _,u=self.request('users',{'name':'Član'});p=self.op();self.assertEqual(self.request('op',p)[0],200);_,state=self.request('state',token=u['token']);self.assertTrue(any(x['id']==p['id'] for x in state['entries']));p.update(opId=str(uuid.uuid4()),baseVersion=1);self.assertEqual(self.request('op',p,token=u['token'])[0],403);self.assertEqual(self.request('settings',{},token=u['token'])[0],403)
 def test_own_edit_delete_and_revoke(self):
  _,u=self.request('users',{'name':'Drugi'});p=self.op();self.assertEqual(self.request('op',p,token=u['token'])[0],200);p.update(opId=str(uuid.uuid4()),baseVersion=1);p['payload']['deleted']=True;self.assertEqual(self.request('op',p,token=u['token'])[1]['version'],2);self.assertEqual(self.request('revoke',{'id':u['id']})[0],200);self.assertEqual(self.request('state',token=u['token'])[0],401)
 def test_validation(self):
  for value in [0,-1,1.5,True]:
   p=self.op();p['payload']['cents']=value;self.assertEqual(self.request('op',p)[0],400)
  p=self.op();p['payload'].update(type='transfer',toAccount='Banka');self.assertEqual(self.request('op',p)[0],400)
 def test_backup_restore_integrity(self):
  self.assertEqual(self.request('backup',{})[0],200);backup=next((Path(self.tmp.name)/'backups').glob('*.sqlite3'))
  with sqlite3.connect(backup) as c:self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
 def test_settings_and_export(self):
  p={'categories':['Hrana'],'accounts':['Banka','Gotovina'],'budget':50000};self.assertEqual(self.request('settings',p)[0],200);self.assertEqual(self.request('state')[1]['settings'],p);self.assertNotIn('token',json.dumps(self.request('export')[1]))
if __name__=='__main__':unittest.main()
