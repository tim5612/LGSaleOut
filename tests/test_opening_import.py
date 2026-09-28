import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from flask import Flask
import openpyxl
import lgsale_opening as o


def source():
    return [dict(row=5,code='TW1',dealer='測試店',category1='AC',category2='Deh',product='P1',display=1,quantity=-1,excluded=True,employee='測試業務')]


def state():
    return dict(dealers=[[1,'TW1','測試店']],employees=[[2,'E2','測試業務',date(2020,1,1),None]],products=[[3,'P1','P1','AC','Deh']],assignments=[],orgs=[[1,'台北']],existing=[],schemaReady=True)


class ReviewTests(unittest.TestCase):
    def test_missing_employee_is_allowed_only_in_historical_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            book=openpyxl.Workbook();sheet=book.active;sheet.title='工作表1';sheet.append(o.OPENING_HEADERS)
            sheet.append(['202603','富基(Costco)','TW019257A1','富基電通股份有限公司','TV','OLED 70吋↓','OLED65B5PTA',72,None,'TW005141富基(Costco)','MMCS'])
            path=Path(temp)/'2603.xlsx';book.save(path);book.close()
            rows,parse_errors=o.parse_workbook(path)
        self.assertEqual(parse_errors,[]);self.assertEqual(rows[0]['employee'],'')
        s=state();s['dealers']=[[1,'TW019257A1','富基電通股份有限公司']];s['products']=[];s['employees']=[]
        historical=o.build_review(rows,parse_errors,s,'2026-03',import_mode='historical')
        self.assertEqual(historical['errors'],[]);self.assertEqual(len(historical['importRows']),1)
        standard=o.build_review(rows,parse_errors,s,'2026-03',import_mode='standard')
        self.assertEqual(standard['errors'],['第 2 列缺少業務姓名；一般期初匯入必須填寫，或改用歷史庫存模式'])

    def test_historical_mode_skips_people_and_pairings_but_keeps_products_and_inventory(self):
        row={**source()[0],'employee':'不在主檔的歷史業務','product':'NEW-PRODUCT'}
        s=state();s['products']=[];s['employees']=[]
        review=o.build_review([row],[],s,'2026-09',import_mode='historical')
        self.assertFalse(review['errors'])
        self.assertEqual(review['employees'],[])
        self.assertEqual(review['assignments'],[])
        self.assertEqual([product['code'] for product in review['products']],['NEW-PRODUCT'])
        self.assertEqual(review['importRows'][0]['quantity'],-1)
        self.assertEqual(review['exclusions'],[])
        self.assertIn('歷史庫存模式：已略過業務主檔與經銷商配對',review['notices'])

    def test_historical_mode_combines_duplicate_inventory_split_between_old_employees(self):
        with tempfile.TemporaryDirectory() as temp:
            book=openpyxl.Workbook();sheet=book.active;sheet.title='工作表1';sheet.append(o.OPENING_HEADERS)
            sheet.append(['202609','A','TW1','測試店','AC','RAC','P1',3,'舊業務 A','TW1A','CE'])
            sheet.append(['202609','B','TW1','測試店','AC','RAC','P1',4,'舊業務 B','TW1B','CE'])
            file=Path(temp)/'2609.xlsx';book.save(file)
            rows,errors=o.parse_workbook(file)
            self.assertEqual(errors,[]);self.assertEqual(rows[0]['quantity'],7)
            historical=o.build_review(rows,[],state(),'2026-09',import_mode='historical')
            standard=o.build_review(rows,[],state(),'2026-09')
            self.assertFalse(historical['errors'])
            self.assertTrue(any('檔案業務不同' in error for error in standard['errors']))

    def test_import_mode_is_part_of_preview_proof(self):
        s=state()
        standard=o.build_review(source(),[],s,'2026-09')['proof']
        historical=o.build_review(source(),[],s,'2026-09',import_mode='historical')['proof']
        self.assertNotEqual(standard,historical)

    def test_missing_dealer_is_skipped_and_never_treated_as_new_master_data(self):
        s=state();s['dealers']=[]
        review=o.build_review(source(),[],s,'2026-09')
        self.assertFalse(review['errors'])
        self.assertEqual(review['dealers'][0]['status'],'略過（主檔無此 TW CODE）')
        self.assertEqual(review['changes'],dict(inserted=0,corrected=0,skipped=1,skippedDealerRows=1))
        self.assertEqual(review['assignments'],[])
        self.assertEqual(review['employees'],[])
        self.assertEqual(review['products'],[])

    def test_unmatched_tongsheng_does_not_create_employee_product_or_assignment(self):
        row=dict(row=8,code='TW219209A1',dealer='統勝電器有限公司',category1='AC',category2='RAC',product='ONLY-TONGSHENG',display=0,quantity=3,excluded=False,employee='沈勇良')
        review=o.build_review([row],[],state(),'2026-09')
        self.assertFalse(review['errors'])
        self.assertEqual(review['changes']['skippedDealerRows'],1)
        self.assertEqual(review['employees'],[])
        self.assertEqual(review['products'],[])
        self.assertEqual(review['assignments'],[])

    def test_same_current_employee_needs_no_employee_or_assignment_but_product_is_added(self):
        s=state();s['products']=[];s['assignments']=[[1,1,2,datetime(2020,1,1),None]]
        review=o.build_review(source(),[],s,'2026-09')
        self.assertFalse(review['errors'])
        self.assertEqual(review['employees'],[])
        self.assertEqual(review['assignments'],[])
        self.assertEqual([product['code'] for product in review['products']],['P1'])

    def test_different_current_employee_creates_missing_employee_and_pairing_after_confirmation(self):
        row={**source()[0],'employee':'新業務'}
        s=state();s['assignments']=[[1,1,2,datetime(2020,1,1),None]]
        edits={'新業務':dict(number='E9',hireDate='2026-08-01',orgId='1',position='SALES')}
        action={'TW1':{'action':'transfer','effectiveAt':'2026-09-01T00:00'}}
        review=o.build_review([row],[],s,'2026-09',edits,action)
        self.assertFalse(review['errors'])
        self.assertEqual([employee['name'] for employee in review['employees']],['新業務'])
        self.assertEqual([(item['code'],item['employee'],item['status']) for item in review['assignments']],[('TW1','新業務','移轉')])

    def test_year_selection_and_filename_months_are_not_fixed_to_2026(self):
        self.assertEqual(o.month_date('2025-10'),datetime(2025,10,1))
        self.assertEqual(o.month_date('2027-01'),datetime(2027,1,1))
        self.assertEqual(o.filename_month('2601.xlsx',opening_format=True),'2026-01')
        self.assertEqual(o.filename_month('2512.xlsx',opening_format=True),'2025-12')
        self.assertEqual(o.filename_month('202608期末.xlsx'),'2026-09')

    def test_opening_inventory_layout_is_supported_and_month_is_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            book=openpyxl.Workbook();sheet=book.active;sheet.title='工作表1';sheet.append(o.OPENING_HEADERS)
            sheet.append(['202601','ONLINE','TW1','測試店','AC','RAC','P1',3,'測試業務','TW1ONLINE','CE'])
            sheet.append(['202601','ONLINE','XXX','網路店','HE','TV','P2',4,'測試業務','TW2ONLINE','HE'])
            file=Path(temp)/'2601.xlsx';book.save(file)
            rows,errors=o.parse_workbook(file)
            self.assertEqual(errors,[])
            self.assertEqual([(r['code'],r['quantity'],r['sourceMonth']) for r in rows],[('TW1',3,'202601'),('TW2',4,'202601')])
            review=o.build_review(rows,[],state(),'2026-02')
            self.assertTrue(any('檔案年月為 202601' in error for error in review['errors']))

    def test_import_lock_skips_sql_server_non_row_results(self):
        cur=MagicMock()
        type(cur).description=PropertyMock(side_effect=[None,None,('LockResult',)])
        cur.nextset.return_value=True;cur.fetchone.return_value=(0,)
        o.acquire_import_lock(cur)
        self.assertEqual(cur.nextset.call_count,2)
        cur.fetchone.assert_called_once()

    def test_import_lock_missing_result_is_actionable(self):
        cur=MagicMock();cur.description=None;cur.nextset.return_value=None
        with self.assertRaisesRegex(ValueError,'鎖定結果'):o.acquire_import_lock(cur)

    def test_real_source_reconciles(self):
        rows,errors=o.parse_workbook(o.BASE/'期初與實銷資料/202608期末.xlsx')
        self.assertEqual(errors,[])
        self.assertEqual((len(rows),sum(x['quantity'] for x in rows),sum(x['display'] for x in rows)),(3823,9242,1547))
        self.assertEqual(sum(x['excluded'] for x in rows),471)
        self.assertEqual(sum(x['quantity']<0 for x in rows),2)

    def test_invalid_source_does_not_silently_import(self):
        with tempfile.TemporaryDirectory() as temp:
            book=openpyxl.Workbook();sheet=book.active;sheet.title='期末';sheet.append(o.HEADERS)
            sheet.append(['TW1','店','AC','Deh','P1',None,0,0,'業務'])
            sheet.append(['TW1','店','AC','Deh','P1',0,2,0,'業務'])
            sheet.append(['TW2','店','AC','Deh','P1',0,'=1+1',0,'業務'])
            sheet.append(['TW3','店','AC','Deh','P1',0,1.5,0,'業務'])
            file=Path(temp)/'source.xlsx';book.save(file)
            rows,errors=o.parse_workbook(file)
            self.assertEqual(len(rows),1);self.assertEqual(len(errors),3)

    def test_existing_records_and_effective_date(self):
        s=state();r=o.build_review(source(),[],s,'2026-09')
        self.assertFalse(r['errors']);self.assertEqual(r['dealers'],[])
        self.assertEqual(r['assignments'][0]['start'],'2026-09-01 00:00:00')
        s['assignments']=[[1,1,2,datetime(2020,1,1),None]]
        self.assertEqual(o.build_review(source(),[],s,'2026-09')['assignments'],[])

    def test_same_month_duplicate_blocked(self):
        s=state();s['existing']=[['TW1','P1',10,5,20,'old.xlsx',datetime(2026,9,1)]]
        self.assertIn('請選擇',o.build_review(source(),[],s,'2026-09')['errors'][0])

    def test_duplicate_keep_does_not_create_dependencies_or_exclusions(self):
        s=state();s['existing']=[['TW1','P1',10,5,20,'old.xlsx',datetime(2026,9,1)]]
        s['employees']=[]
        r=o.build_review(source(),[],s,'2026-09',decisions={'5':'keep'})
        self.assertFalse(r['errors']);self.assertEqual(r['changes'],dict(inserted=0,corrected=0,skipped=1))
        self.assertEqual(r['employees'],[]);self.assertEqual(r['exclusions'],[])

    def test_duplicate_replace_keeps_lineage_and_signed_quantity(self):
        s=state();s['existing']=[['TW1','P1',10,5,20,'old.xlsx',datetime(2026,9,1)]]
        r=o.build_review(source(),[],s,'2026-09',decisions={'5':'replace'})
        self.assertFalse(r['errors']);self.assertEqual(r['importRows'],[])
        self.assertEqual(r['corrections'][0]['oldQuantity'],5);self.assertEqual(r['corrections'][0]['newQuantity'],-1)
        self.assertEqual(r['duplicates'][0]['fileName'],'old.xlsx')

    def test_assignment_conflict_requires_explicit_action(self):
        s=state();s['employees'].append([4,'E4','原業務',date(2020,1,1),None]);s['assignments']=[[1,1,4,datetime(2020,1,1),None]]
        r=o.build_review(source(),[],s,'2026-09');self.assertTrue(r['errors'])
        action={'TW1':{'action':'retain','effectiveAt':'2026-09-01T00:00'}}
        r=o.build_review(source(),[],s,'2026-09',assignment_actions=action);self.assertFalse(r['errors']);self.assertEqual(r['assignments'],[])

    def test_assignment_transfer_closes_open_history(self):
        s=state();s['employees'].append([4,'E4','原業務',date(2020,1,1),None]);s['assignments']=[[1,1,4,datetime(2020,1,1),None]]
        action={'TW1':{'action':'transfer','effectiveAt':'2026-09-01T00:00'}}
        r=o.build_review(source(),[],s,'2026-09',assignment_actions=action)
        self.assertFalse(r['errors']);self.assertEqual(r['assignments'][0]['status'],'移轉')
        self.assertIsNone(r['assignments'][0]['end'])

    def test_assignment_bridge_preserves_later_transfer(self):
        s=state();s['employees'].extend([[4,'E4','原業務',date(2020,1,1),None],[5,'E5','後續業務',date(2020,1,1),None]])
        s['assignments']=[[1,1,4,datetime(2020,1,1),datetime(2026,9,11)],[2,1,5,datetime(2026,9,11),None]]
        action={'TW1':{'action':'bridge','effectiveAt':'2026-09-01T00:00'}}
        r=o.build_review(source(),[],s,'2026-09',assignment_actions=action)
        self.assertFalse(r['errors']);item=r['assignments'][0]
        self.assertEqual((item['status'],item['oldAssignmentId'],item['end']),('補登歷史',1,'2026-09-11 00:00:00'))

    def test_future_assignment_and_employee_dates_block(self):
        s=state();s['assignments']=[[1,1,2,datetime(2026,10,1),None]]
        self.assertTrue(o.build_review(source(),[],s,'2026-09')['errors'])
        s=state();s['employees'][0][4]=date(2026,8,31)
        self.assertTrue(o.build_review(source(),[],s,'2026-09')['errors'])

    def test_same_employee_assignment_later_in_month_is_reused(self):
        s=state();s['assignments']=[[1,1,2,datetime(2026,9,19,10,10,51),None]]
        review=o.build_review(source(),[],s,'2026-09')
        self.assertFalse(review['errors']);self.assertEqual(review['assignments'],[])
        self.assertIn('1 家經銷商在本月稍後已有相同業務配對，本次沿用主檔且不新增配對',review['notices'])

    def test_different_employee_assignment_later_in_month_has_clear_error(self):
        s=state();s['employees'].append([3,'E3','後續業務',date(2020,1,1),None])
        s['assignments']=[[1,1,3,datetime(2026,9,19,10,10,51),None]]
        review=o.build_review(source(),[],s,'2026-09')
        self.assertEqual(review['errors'],['TW1 在期初日尚無有效配對；主檔自 2026-09-19 10:10 起由「後續業務」負責，檔案業務為「測試業務」，請先確認配對期間'])

    def test_new_employee_requires_complete_data_and_unique_number(self):
        s=state();s['employees']=[]
        self.assertEqual(len(o.build_review(source(),[],s,'2026-09')['errors']),3)
        edits={'測試業務':dict(number='E1',hireDate='2026-08-01',orgId='1',position='SALES')}
        r=o.build_review(source(),[],s,'2026-09',edits);self.assertFalse(r['errors']);self.assertEqual(len(r['employees']),1)

    def test_proof_detects_master_and_input_changes(self):
        s=state();proof=o.build_review(source(),[],s,'2026-09')['proof'];s['dealers'][0][2]='改名'
        self.assertNotEqual(proof,o.build_review(source(),[],s,'2026-09')['proof'])

    def test_exclusions_deduplicate_products_and_keep_all_inventory(self):
        rows=source()+[{**source()[0],'row':6,'code':'TW2','quantity':10,'excluded':False},{**source()[0],'row':7,'code':'TW3','quantity':4}]
        review=o.build_review(rows,[],state(),'2026-09')
        self.assertEqual(review['summary']['quantity'],13)
        self.assertEqual(len(review['rows']),3)
        self.assertEqual(review['exclusions'],[dict(code='P1',scope='ALL',reason='PSIRemove',fromMonth='202609',toMonth=None,status='新增')])

    def test_existing_exclusion_reuse_or_conflict(self):
        s=state();s['exclusions']=[['P1','202609',None,'PSIRemove']]
        review=o.build_review(source(),[],s,'2026-09');self.assertFalse(review['errors']);self.assertEqual(review['exclusions'][0]['status'],'沿用')
        s['exclusions'][0][3]='Other'
        self.assertIn('不同的全通路排除設定',o.build_review(source(),[],s,'2026-09')['errors'][0])

    def test_exclusion_changes_invalidate_preview(self):
        s=state();first=o.build_review(source(),[],s,'2026-09')['proof']
        s['exclusions']=[['P1','202609',None,'PSIRemove']]
        self.assertNotEqual(first,o.build_review(source(),[],s,'2026-09')['proof'])


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.app=Flask(__name__);self.app.secret_key='test-only';self.app.register_blueprint(o.bp)
        self.client=self.app.test_client()
        with self.client.session_transaction() as session:
            session['user']=dict(id=1,type='EMPLOYEE',employeeId=2,name='測試')
            session['opening_csrf']='test-csrf'
        self.headers={'X-Opening-CSRF':'test-csrf'}

    def test_context_returns_opening_history(self):
        conn=MagicMock();cur=conn.cursor.return_value
        cur.fetchall.return_value=[(31,'2510.xlsx',datetime(2025,11,2,9,30),17590,17400,'202510')]
        with patch.object(o.db,'connect',return_value=conn):
            response=self.client.get('/api/opening-import/context')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['history'],[dict(batchId=31,fileName='2510.xlsx',importedAt='2025-11-02 09:30:00',sourceRows=17590,rows=17400,month='2025-10')])
        self.assertEqual(response.headers['Cache-Control'],'no-store');conn.close.assert_called_once()

    def test_batch_rows_returns_insertions_and_corrections(self):
        conn=MagicMock();cur=conn.cursor.return_value
        cur.fetchone.return_value=(31,2)
        cur.fetchall.return_value=[
            ('INSERT',101,6,'TW1','測試店','P1','產品一',8,None),
            ('CORRECTION',202,9,'TW2','第二店','P2','產品二',5,3),
        ]
        with patch.object(o.db,'connect',return_value=conn):
            response=self.client.get('/api/opening-import/batches/31/rows?page=1')
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['total'],2)
        self.assertEqual(response.json['rows'][0]['action'],'INSERT')
        self.assertIsNone(response.json['rows'][0]['previousQuantity'])
        self.assertEqual(response.json['rows'][1]['previousQuantity'],3)
        self.assertEqual(cur.execute.call_args_list[1].args[1],(31,31,0,50))
        conn.close.assert_called_once()

    def test_batch_rows_rejects_unknown_batch(self):
        conn=MagicMock();conn.cursor.return_value.fetchone.return_value=None
        with patch.object(o.db,'connect',return_value=conn):
            response=self.client.get('/api/opening-import/batches/999/rows')
        self.assertEqual(response.status_code,404);self.assertIn('找不到',response.json['error'])

    def test_csrf_and_dealer_access(self):
        self.assertEqual(self.client.post('/api/opening-import/commit',json={}).status_code,403)
        with self.client.session_transaction() as session:session['user']={**session['user'],'type':'DEALER'}
        self.assertEqual(self.client.get('/opening-import').status_code,403)

    def test_preview_never_commits(self):
        conn=MagicMock();review=o.build_review(source(),[],state(),'2026-09')
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'get_review',return_value=(review,{'name':'x.xlsx'},Path('x'))):
            res=self.client.post('/api/opening-import/preview',json={},headers=self.headers)
        self.assertEqual(res.status_code,200);conn.commit.assert_not_called()

    def test_commit_rolls_back_after_insert_failure(self):
        conn=MagicMock();cur=conn.cursor.return_value
        review=o.build_review(source(),[],state(),'2026-09')
        # lock; no completed batch; inserted batch id
        cur.fetchone.side_effect=[(0,),None,(100,)]
        cur.fetchall.side_effect=[[('TW1',1)],[('P1',3)],[('測試業務',2)]]
        cur.executemany.side_effect=RuntimeError('injected insert failure')
        meta={'name':'x.xlsx','hash':'test','size':10}
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'load_upload',return_value=(meta,Path('x.xlsx'))),patch.object(o,'get_review',return_value=(review,meta,Path('x.xlsx'))),self.assertLogs(self.app.logger,level='ERROR'):
            res=self.client.post('/api/opening-import/commit',json={'token':'x','month':'2026-09','confirmed':True,'proof':review['proof']},headers=self.headers)
        self.assertEqual(res.status_code,503);conn.rollback.assert_called_once();conn.commit.assert_not_called()

    def test_success_preserves_negative_and_writes_psi_exclusion(self):
        conn=MagicMock();cur=conn.cursor.return_value
        review=o.build_review(source(),[],state(),'2026-09')
        cur.fetchone.side_effect=[(0,),None,(100,),(1,-1)]
        cur.fetchall.side_effect=[[('TW1',1)],[('P1',3)],[('測試業務',2)]]
        meta={'name':'x.xlsx','hash':'test','size':10}
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'load_upload',return_value=(meta,Path('x.xlsx'))),patch.object(o,'get_review',return_value=(review,meta,Path('x.xlsx'))):
            res=self.client.post('/api/opening-import/commit',json={'token':'x','confirmed':True,'proof':review['proof']},headers=self.headers)
        self.assertEqual(res.status_code,200);conn.commit.assert_called_once();conn.rollback.assert_not_called()
        self.assertEqual(cur.executemany.call_args.args[1],[(100,5,1,3,-1)])
        exclusion_calls=[call for call in cur.execute.call_args_list if 'INSERT dbo.OpeningInventoryProductExclusion' in call.args[0]]
        self.assertEqual(len(exclusion_calls),1)
        self.assertEqual(exclusion_calls[0].args[1],(3,'202609',2))
        self.assertIn("'ALL',NULL,%s,NULL,'PSIRemove'",exclusion_calls[0].args[0])
        self.assertEqual(res.json['exclusionsCreated'],1)

    def test_stale_preview_prevents_writes(self):
        conn=MagicMock();conn.cursor.return_value.fetchone.side_effect=[(0,),None]
        review=o.build_review(source(),[],state(),'2026-09');meta={'name':'x.xlsx'}
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'load_upload',return_value=(meta,Path('x'))),patch.object(o,'get_review',return_value=(review,meta,Path('x'))):
            res=self.client.post('/api/opening-import/commit',json={'token':'x','confirmed':True,'proof':'old'},headers=self.headers)
        self.assertEqual(res.status_code,400);conn.commit.assert_not_called();conn.cursor.return_value.executemany.assert_not_called()

    def test_exclusion_failure_rolls_back_inventory_too(self):
        conn=MagicMock();cur=conn.cursor.return_value
        review=o.build_review(source(),[],state(),'2026-09');meta={'name':'x.xlsx','hash':'test','size':10}
        cur.fetchone.side_effect=[(0,),None,(100,)]
        cur.fetchall.side_effect=[[('TW1',1)],[('P1',3)],[('測試業務',2)]]
        def execute(sql,*args):
            if 'INSERT dbo.OpeningInventoryProductExclusion' in sql:raise RuntimeError('exclusion failure')
        cur.execute.side_effect=execute
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'load_upload',return_value=(meta,Path('x.xlsx'))),patch.object(o,'get_review',return_value=(review,meta,Path('x.xlsx'))),self.assertLogs(self.app.logger,level='ERROR'):
            response=self.client.post('/api/opening-import/commit',json={'token':'x','confirmed':True,'proof':review['proof']},headers=self.headers)
        self.assertEqual(response.status_code,503);cur.executemany.assert_called_once();conn.rollback.assert_called_once();conn.commit.assert_not_called()

    def test_correction_updates_once_and_keeps_audit(self):
        conn=MagicMock();cur=conn.cursor.return_value;cur.rowcount=1
        s=state();s['existing']=[['TW1','P1',10,5,20,'old.xlsx',datetime(2026,9,1)]]
        review=o.build_review(source(),[],s,'2026-09',decisions={'5':'replace'})
        cur.fetchone.side_effect=[(0,),None,(100,),(0,None)]
        cur.fetchall.side_effect=[[('TW1',1)],[('P1',3)],[('測試業務',2)]]
        meta={'name':'new.xlsx','hash':'test','size':10}
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'load_upload',return_value=(meta,Path('new.xlsx'))),patch.object(o,'get_review',return_value=(review,meta,Path('new.xlsx'))):
            response=self.client.post('/api/opening-import/commit',json={'token':'x','confirmed':True,'proof':review['proof']},headers=self.headers)
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['corrected'],1)
        cur.executemany.assert_not_called();conn.commit.assert_called_once()
        writes=[x.args for x in cur.execute.call_args_list]
        self.assertTrue(any('INSERT dbo.OpeningInventoryCorrection' in x[0] and x[1]==(100,10,5,5,-1) for x in writes))
        self.assertTrue(any('UPDATE dbo.MonthlyOpeningInventoryDetail' in x[0] and x[1]==(-1,10,5) for x in writes))

    def test_all_keep_does_not_create_batch(self):
        conn=MagicMock();cur=conn.cursor.return_value;cur.fetchone.side_effect=[(0,),None]
        s=state();s['existing']=[['TW1','P1',10,5,20,'old.xlsx',datetime(2026,9,1)]]
        review=o.build_review(source(),[],s,'2026-09',decisions={'5':'keep'})
        meta={'name':'x.xlsx'}
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'load_upload',return_value=(meta,Path('x'))),patch.object(o,'get_review',return_value=(review,meta,Path('x'))):
            response=self.client.post('/api/opening-import/commit',json={'token':'x','confirmed':True,'proof':review['proof']},headers=self.headers)
        self.assertTrue(response.json['noChanges']);conn.commit.assert_not_called()
        self.assertFalse(any('INSERT' in x.args[0] for x in cur.execute.call_args_list))

    def test_commit_retries_are_idempotent(self):
        conn=MagicMock();conn.cursor.return_value.fetchone.side_effect=[(0,),(12,3823,'202609')]
        with patch.object(o.db,'connect',return_value=conn),patch.object(o,'load_upload',return_value=({},Path('x'))),patch.object(o,'get_review') as recheck:
            res=self.client.post('/api/opening-import/commit',json={'token':'x','confirmed':True},headers=self.headers)
        self.assertTrue(res.json['alreadyImported']);recheck.assert_not_called();conn.commit.assert_not_called()


if __name__=='__main__':unittest.main()
