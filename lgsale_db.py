"""SQL Server repository for the LGSale prototype UI."""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime
from typing import Any

import pytds


POSITION_TO_UI = {"SALES": "業務", "DIRECTOR": "處長", "MANAGER": "經理"}
POSITION_TO_DB = {value: key for key, value in POSITION_TO_UI.items()}


def connect():
    return pytds.connect(
        os.getenv("LGSALEOUT_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("LGSALEOUT_DB_PORT", "49172")),
        database=os.getenv("LGSALEOUT_DB_NAME", "LGSaleOut"),
        user=os.getenv("LGSALEOUT_DB_USER", "Tim"),
        password=os.getenv("LGSALEOUT_DB_PASSWORD", "561202"),
        login_timeout=8,
        timeout=15,
    )


def _one(cur, sql: str, params=()):
    cur.execute(sql, params)
    return cur.fetchone()


def _creator_id(cur) -> int:
    row = _one(cur, "SELECT TOP 1 EmployeeId FROM dbo.Employee WHERE EmployeeName=%s ORDER BY EmployeeId", ("林怡君",))
    if row is None:
        row = _one(cur, "SELECT TOP 1 EmployeeId FROM dbo.Employee WHERE TerminationDate IS NULL ORDER BY EmployeeId")
    if row is None:
        raise ValueError("資料庫中沒有可用的任務建立者")
    return int(row[0])


def health() -> dict[str, Any]:
    with connect() as conn:
        row = _one(conn.cursor(), "SELECT DB_NAME(), SYSDATETIME()")
        return {"status": "ok", "mode": "sql-server", "database": row[0], "serverTime": row[1].isoformat(timespec="seconds")}


def tasks() -> list[dict[str, Any]]:
    sql = """
    SELECT t.VisitTaskId,t.TaskTitle,t.Instruction,t.ValidFrom,t.DueDate,t.RecordStatus,t.CreatedAt,
           creator.EmployeeName,
           t.SampleTaskExecutionId,t.SampleApprovedAt,sampleDealer.DealerName,
           COUNT(DISTINCT e.TaskExecutionId),
           COUNT(DISTINCT CASE WHEN e.SubmittedAt IS NOT NULL THEN e.TaskExecutionId END),
           COUNT(DISTINCT p.TaskPhotoId),
           COUNT(DISTINCT samplePhoto.TaskPhotoId)
      FROM dbo.VisitTask t
      JOIN dbo.Employee creator ON creator.EmployeeId=t.CreatedByEmployeeId
      LEFT JOIN dbo.VisitTaskExecution e ON e.VisitTaskId=t.VisitTaskId
      LEFT JOIN dbo.VisitTaskPhoto p ON p.TaskExecutionId=e.TaskExecutionId
      LEFT JOIN dbo.VisitTaskExecution sampleExecution ON sampleExecution.TaskExecutionId=t.SampleTaskExecutionId
      LEFT JOIN dbo.Dealer sampleDealer ON sampleDealer.DealerId=sampleExecution.DealerId
      LEFT JOIN dbo.VisitTaskPhoto samplePhoto ON samplePhoto.TaskExecutionId=t.SampleTaskExecutionId
     GROUP BY t.VisitTaskId,t.TaskTitle,t.Instruction,t.ValidFrom,t.DueDate,t.RecordStatus,t.CreatedAt,
              creator.EmployeeName,t.SampleTaskExecutionId,t.SampleApprovedAt,sampleDealer.DealerName
     ORDER BY t.CreatedAt DESC,t.VisitTaskId DESC
    """
    with connect() as conn:
        cur = conn.cursor(); cur.execute(sql); rows = cur.fetchall()
    result = []
    for row in rows:
        task_id, title, instruction, valid_from, due_date, status, created_at, creator, sample_execution, approved_at, sample_dealer, total, completed, photo_count, sample_photos = row
        today = date.today()
        phase = "VOIDED" if status == "VOIDED" else "UPCOMING" if today < valid_from else "CLOSED" if today > due_date else "ACTIVE"
        result.append({
            "id": int(task_id), "code": f"VT-{created_at:%Y%m}-{int(task_id):03d}", "title": title,
            "instruction": instruction, "validFrom": valid_from.isoformat(), "dueDate": due_date.isoformat(),
            "recordStatus": status, "phase": phase, "creator": creator,
            "sampleStatus": "APPROVED" if sample_execution is not None and approved_at is not None else "PENDING",
            "sampleDealer": sample_dealer, "samplePhotos": int(sample_photos), "completed": int(completed),
            "total": int(total), "photoCount": int(photo_count),
            "progress": round(int(completed) / int(total) * 100) if total else 0,
        })
    return result


def create_task(data: dict[str, Any]) -> dict[str, Any]:
    conn = connect()
    try:
        cur = conn.cursor(); creator_id = _creator_id(cur)
        row = _one(cur, """
            INSERT dbo.VisitTask(TaskTitle,Instruction,ValidFrom,DueDate,RecordStatus,CreatedByEmployeeId)
            OUTPUT inserted.VisitTaskId,inserted.CreatedAt
            VALUES(%s,%s,%s,%s,'ACTIVE',%s)
        """, (data["title"], data["instruction"], data["validFrom"], data["dueDate"], creator_id))
        task_id, created_at = int(row[0]), row[1]
        limit = int(data.get("total") or 2147483647)
        cur.execute("""
            SELECT TOP (%s) d.DealerId,a.EmployeeId
              FROM dbo.Dealer d
              JOIN dbo.DealerAssignmentHistory a ON a.DealerId=d.DealerId AND a.EndDateTime IS NULL
             ORDER BY d.DealerId
        """, (limit,))
        assignments = cur.fetchall()
        for dealer_id, employee_id in assignments:
            cur.execute("INSERT dbo.VisitTaskExecution(VisitTaskId,DealerId,ResponsibleEmployeeId) VALUES(%s,%s,%s)", (task_id, dealer_id, employee_id))
        conn.commit()
        return {"id": task_id, "code": f"VT-{created_at:%Y%m}-{task_id:03d}", "executionCount": len(assignments)}
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def toggle_task(task_id: int) -> bool:
    conn = connect()
    try:
        cur = conn.cursor(); creator_id = _creator_id(cur)
        cur.execute("""
            UPDATE dbo.VisitTask
               SET RecordStatus=CASE RecordStatus WHEN 'ACTIVE' THEN 'VOIDED' ELSE 'ACTIVE' END,
                   UpdatedByEmployeeId=%s,UpdatedAt=SYSDATETIME()
             WHERE VisitTaskId=%s
        """, (creator_id, task_id))
        changed = cur.rowcount > 0; conn.commit(); return changed
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def dealers() -> list[dict[str, Any]]:
    sql = """
    SELECT d.DealerId,d.DealerCode,d.DealerName,COALESCE(l.DealerStatus,'—'),COALESCE(e.EmployeeName,'未指派'),MAX(v.ReportDateTime)
      FROM dbo.Dealer d
      LEFT JOIN dbo.DealerLevelHistory l ON l.DealerId=d.DealerId AND l.EndDateTime IS NULL
      LEFT JOIN dbo.DealerAssignmentHistory a ON a.DealerId=d.DealerId AND a.EndDateTime IS NULL
      LEFT JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId
      LEFT JOIN dbo.StoreVisit v ON v.DealerId=d.DealerId AND v.RecordStatus='ACTIVE'
     GROUP BY d.DealerId,d.DealerCode,d.DealerName,l.DealerStatus,e.EmployeeName
     ORDER BY d.DealerId
    """
    with connect() as conn:
        cur=conn.cursor(); cur.execute(sql)
        return [{"id":int(r[0]),"code":r[1],"name":r[2],"level":r[3],"employee":r[4],"lastVisit":r[5].date().isoformat() if r[5] else None} for r in cur.fetchall()]


def products() -> list[dict[str, Any]]:
    with connect() as conn:
        cur=conn.cursor(); cur.execute("SELECT ProductId,ProductCode,ProductName,COALESCE(CategoryLevel1,''),COALESCE(CategoryLevel2,'') FROM dbo.Product WHERE IsActive=1 ORDER BY ProductId")
        return [{"id":int(r[0]),"code":r[1],"name":r[2],"category":r[3] or r[4]} for r in cur.fetchall()]


def create_assignment(data: dict[str, Any]) -> int:
    conn = connect()
    try:
        cur = conn.cursor(); creator_id = _creator_id(cur)
        employee = _one(cur, "SELECT EmployeeId FROM dbo.Employee WHERE EmployeeName=%s", (data["employee"],))
        receiver = _one(cur, "SELECT EmployeeId FROM dbo.Employee WHERE EmployeeName=%s", (data.get("receiver"),))
        org = _one(cur, "SELECT OrgUnitId FROM dbo.OrganizationUnit WHERE OrgUnitName=%s AND IsActive=1", (data.get("newOrg"),))
        if employee is None or org is None:
            raise ValueError("找不到異動員工或啟用中的新處所")
        effective_at, reason = data["effectiveAt"], data.get("reason") or "人員與經銷商異動"
        current_org = _one(cur, "SELECT EmployeeOrgAssignmentId,OrgUnitId FROM dbo.EmployeeOrgAssignmentHistory WHERE EmployeeId=%s AND EndDateTime IS NULL", (employee[0],))
        if current_org and int(current_org[1]) != int(org[0]):
            cur.execute("UPDATE dbo.EmployeeOrgAssignmentHistory SET EndDateTime=%s WHERE EmployeeOrgAssignmentId=%s", (effective_at, current_org[0]))
            cur.execute("INSERT dbo.EmployeeOrgAssignmentHistory(EmployeeId,OrgUnitId,StartDateTime,ChangeReason,CreatedByEmployeeId) VALUES(%s,%s,%s,%s,%s)", (employee[0], org[0], effective_at, reason, creator_id))
        dealer_count = int(data.get("dealerCount") or 0)
        moved = 0
        if dealer_count and receiver is not None:
            cur.execute("SELECT TOP (%s) DealerAssignmentId,DealerId FROM dbo.DealerAssignmentHistory WHERE EmployeeId=%s AND EndDateTime IS NULL ORDER BY DealerId", (dealer_count, employee[0]))
            for assignment_id, dealer_id in cur.fetchall():
                cur.execute("UPDATE dbo.DealerAssignmentHistory SET EndDateTime=%s WHERE DealerAssignmentId=%s", (effective_at, assignment_id))
                cur.execute("INSERT dbo.DealerAssignmentHistory(DealerId,EmployeeId,StartDateTime,ChangeReason,CreatedByEmployeeId) VALUES(%s,%s,%s,%s,%s)", (dealer_id, receiver[0], effective_at, reason, creator_id))
                moved += 1
        conn.commit()
        return moved
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def employees() -> list[dict[str, Any]]:
    sql = """
    SELECT e.EmployeeId,e.EmployeeNo,e.EmployeeName,e.HireDate,e.TerminationDate,
           p.PositionLevel,p.StartDateTime,o.OrgUnitName,h.StartDateTime
      FROM dbo.Employee e
      LEFT JOIN dbo.EmployeePositionHistory p ON p.EmployeeId=e.EmployeeId AND p.EndDateTime IS NULL
      LEFT JOIN dbo.EmployeeOrgAssignmentHistory h ON h.EmployeeId=e.EmployeeId AND h.EndDateTime IS NULL
      LEFT JOIN dbo.OrganizationUnit o ON o.OrgUnitId=h.OrgUnitId
     ORDER BY e.EmployeeId
    """
    with connect() as conn:
        cur=conn.cursor(); cur.execute(sql); base=cur.fetchall(); result=[]
        for r in base:
            employee_id=int(r[0])
            cur.execute("""SELECT p.PositionLevel,p.StartDateTime,p.EndDateTime,p.ChangeReason,c.EmployeeName FROM dbo.EmployeePositionHistory p JOIN dbo.Employee c ON c.EmployeeId=p.CreatedByEmployeeId WHERE p.EmployeeId=%s ORDER BY p.StartDateTime DESC""",(employee_id,))
            position_history=[{"position":POSITION_TO_UI.get(x[0],x[0]),"start":x[1].isoformat(sep=" ",timespec="minutes"),"end":x[2].isoformat(sep=" ",timespec="minutes") if x[2] else None,"reason":x[3],"creator":x[4]} for x in cur.fetchall()]
            cur.execute("""SELECT o.OrgUnitName,h.StartDateTime,h.EndDateTime,h.ChangeReason,c.EmployeeName FROM dbo.EmployeeOrgAssignmentHistory h JOIN dbo.OrganizationUnit o ON o.OrgUnitId=h.OrgUnitId JOIN dbo.Employee c ON c.EmployeeId=h.CreatedByEmployeeId WHERE h.EmployeeId=%s ORDER BY h.StartDateTime DESC""",(employee_id,))
            org_history=[{"org":x[0],"start":x[1].isoformat(sep=" ",timespec="minutes"),"end":x[2].isoformat(sep=" ",timespec="minutes") if x[2] else None,"reason":x[3],"creator":x[4]} for x in cur.fetchall()]
            result.append({"id":employee_id,"number":r[1],"name":r[2],"hireDate":r[3].isoformat(),"endDate":r[4].isoformat() if r[4] else None,"status":"INACTIVE" if r[4] else "ACTIVE","position":POSITION_TO_UI.get(r[5],r[5] or "—"),"positionSince":r[6].date().isoformat() if r[6] else "—","org":r[7] or "—","orgSince":r[8].date().isoformat() if r[8] else "—","positionHistory":position_history,"orgHistory":org_history})
        return result


def create_employee(data: dict[str, Any]) -> int:
    conn=connect()
    try:
        cur=conn.cursor(); creator_id=_creator_id(cur)
        org=_one(cur,"SELECT OrgUnitId FROM dbo.OrganizationUnit WHERE OrgUnitName=%s AND IsActive=1",(data["org"],))
        if org is None: raise ValueError("找不到啟用中的所屬處所")
        row=_one(cur,"INSERT dbo.Employee(EmployeeNo,EmployeeName,HireDate) OUTPUT inserted.EmployeeId VALUES(%s,%s,%s)",(data["number"],data["name"],data["hireDate"])); employee_id=int(row[0]); start=str(data["hireDate"])+" 09:00"
        cur.execute("INSERT dbo.EmployeePositionHistory(EmployeeId,PositionLevel,StartDateTime,ChangeReason,CreatedByEmployeeId) VALUES(%s,%s,%s,%s,%s)",(employee_id,POSITION_TO_DB[data["position"]],start,"新進人員任用",creator_id))
        cur.execute("INSERT dbo.EmployeeOrgAssignmentHistory(EmployeeId,OrgUnitId,StartDateTime,ChangeReason,CreatedByEmployeeId) VALUES(%s,%s,%s,%s,%s)",(employee_id,org[0],start,"新進人員任用",creator_id)); conn.commit(); return employee_id
    except Exception:
        conn.rollback(); raise
    finally: conn.close()


def update_employee(employee_id:int,data:dict[str,Any]) -> bool:
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute("UPDATE dbo.Employee SET EmployeeNo=%s,EmployeeName=%s,HireDate=%s,TerminationDate=%s WHERE EmployeeId=%s",(data["number"],data["name"],data["hireDate"],data.get("endDate"),employee_id)); changed=cur.rowcount>0; conn.commit(); return changed
    except Exception: conn.rollback(); raise
    finally: conn.close()


def organizations() -> list[dict[str,Any]]:
    sql="""SELECT o.OrgUnitId,o.OrgUnitCode,o.OrgUnitName,o.IsActive,COUNT(CASE WHEN e.TerminationDate IS NULL THEN 1 END),COUNT(CASE WHEN e.TerminationDate IS NULL AND p.PositionLevel='DIRECTOR' THEN 1 END) FROM dbo.OrganizationUnit o LEFT JOIN dbo.EmployeeOrgAssignmentHistory h ON h.OrgUnitId=o.OrgUnitId AND h.EndDateTime IS NULL LEFT JOIN dbo.Employee e ON e.EmployeeId=h.EmployeeId LEFT JOIN dbo.EmployeePositionHistory p ON p.EmployeeId=e.EmployeeId AND p.EndDateTime IS NULL GROUP BY o.OrgUnitId,o.OrgUnitCode,o.OrgUnitName,o.IsActive ORDER BY o.OrgUnitId"""
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql);return [{"id":int(r[0]),"code":r[1],"name":r[2],"active":bool(r[3]),"employees":int(r[4]),"directors":int(r[5])} for r in cur.fetchall()]


def update_organization(org_id:int,data:dict[str,Any]) -> bool:
    conn=connect()
    try:
        cur=conn.cursor();cur.execute("UPDATE dbo.OrganizationUnit SET OrgUnitCode=%s,OrgUnitName=%s,IsActive=%s WHERE OrgUnitId=%s",(data["code"],data["name"],bool(data["active"]),org_id));changed=cur.rowcount>0;conn.commit();return changed
    except Exception:conn.rollback();raise
    finally:conn.close()


def photo_tasks() -> list[dict[str,Any]]:
    sql="""SELECT e.TaskExecutionId,t.VisitTaskId,t.TaskTitle,t.Instruction,d.DealerId,d.DealerName,t.DueDate,e.SubmittedAt,t.SampleTaskExecutionId FROM dbo.VisitTaskExecution e JOIN dbo.VisitTask t ON t.VisitTaskId=e.VisitTaskId JOIN dbo.Dealer d ON d.DealerId=e.DealerId WHERE t.RecordStatus='ACTIVE' ORDER BY t.DueDate,e.TaskExecutionId"""
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql);rows=cur.fetchall();result=[]
        for r in rows:
            samples=[]
            if r[8] is not None:
                cur.execute("SELECT PhotoDescription FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=%s ORDER BY SortOrder,TaskPhotoId",(r[8],));samples=[x[0] or "樣本照片" for x in cur.fetchall()]
            result.append({"executionId":int(r[0]),"taskId":int(r[1]),"title":r[2],"instruction":r[3],"dealerId":int(r[4]),"dealer":r[5],"dueDate":r[6].isoformat(),"sample":samples,"completed":r[7] is not None})
        return result


def add_photo(execution_id:int,description:str) -> int:
    conn=connect()
    try:
        token=uuid.uuid4().hex+".jpg";cur=conn.cursor();row=_one(cur,"""INSERT dbo.VisitTaskPhoto(TaskExecutionId,PhotoDescription,StoredFileName,StoredFilePath,CapturedAt,SortOrder) OUTPUT inserted.TaskPhotoId VALUES(%s,%s,%s,%s,SYSDATETIME(),(SELECT COUNT(*) FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=%s))""",(execution_id,description,token,"prototype://"+token,execution_id));conn.commit();return int(row[0])
    except Exception:conn.rollback();raise
    finally:conn.close()


def complete_execution(execution_id:int,note:str|None) -> datetime:
    conn=connect()
    try:
        cur=conn.cursor();row=_one(cur,"""UPDATE dbo.VisitTaskExecution SET CompletedByEmployeeId=ResponsibleEmployeeId,ExecutionNote=%s,SubmittedAt=SYSDATETIME() OUTPUT inserted.SubmittedAt WHERE TaskExecutionId=%s""",(note,execution_id));
        if row is None: raise LookupError("找不到任務執行資料")
        conn.commit();return row[0]
    except Exception:conn.rollback();raise
    finally:conn.close()


def create_visit(data:dict[str,Any]) -> tuple[int,datetime]:
    conn=connect()
    try:
        cur=conn.cursor();dealer_id=int(data["dealerId"]);assignment=_one(cur,"SELECT DealerAssignmentId FROM dbo.DealerAssignmentHistory WHERE DealerId=%s AND EndDateTime IS NULL",(dealer_id,));account=_one(cur,"SELECT TOP 1 UserAccountId FROM dbo.UserAccount WHERE AccountType='EMPLOYEE' AND IsLoginEnabled=1 ORDER BY UserAccountId")
        if account is None:raise ValueError("找不到可用的員工帳號")
        row=_one(cur,"""INSERT dbo.StoreVisit(DealerId,DealerAssignmentId,EntrySourceType,CreatedByUserAccountId) OUTPUT inserted.StoreVisitId,inserted.ReportDateTime VALUES(%s,%s,%s,%s)""",(dealer_id,assignment[0] if assignment else None,data.get("entrySourceType","EMPLOYEE"),account[0]));visit_id=int(row[0])
        for item in data["details"]:
            sell=int(item["sellOutQuantity"]) if item.get("sellOutQuantity") else None;display=int(item["displayQuantity"]) if item.get("displayQuantity") else None
            cur.execute("INSERT dbo.StoreVisitProductDetail(StoreVisitId,ProductId,SellOutQuantity,SellOutDate,DisplayQuantity) VALUES(%s,%s,%s,%s,%s)",(visit_id,int(item["productId"]),sell,item.get("sellOutDate") if sell else None,display))
        conn.commit();return visit_id,row[1]
    except Exception:conn.rollback();raise
    finally:conn.close()
