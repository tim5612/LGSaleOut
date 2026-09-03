"""SQL Server repository for the LGSale prototype UI."""

from __future__ import annotations

import uuid
import base64
from datetime import date, datetime, timedelta
from typing import Any

import pytds
from lgsale_config import required


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def passkey_invitation(token_hash: bytes) -> dict[str, Any] | None:
    sql = """
    SELECT i.InvitationId,a.UserAccountId,a.AccountType,
           COALESCE(e.EmployeeNo,d.DealerCode),COALESCE(e.EmployeeName,d.DealerName)
      FROM dbo.PasskeyRegistrationInvitation i
      JOIN dbo.UserAccount a ON a.UserAccountId=i.UserAccountId
      LEFT JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId
      LEFT JOIN dbo.Dealer d ON d.DealerId=a.DealerId
     WHERE i.TokenHash=%s AND i.UsedAt IS NULL AND i.RevokedAt IS NULL
       AND i.ExpiresAt>SYSDATETIME() AND a.IsLoginEnabled=1 AND a.AccountStatus='ACTIVE'
    """
    with connect() as conn:
        row = _one(conn.cursor(), sql, (pytds.Binary(token_hash),))
    if row is None:
        return None
    return {"invitationId": int(row[0]), "userAccountId": int(row[1]), "accountType": row[2],
            "accountLabel": f"{row[2]}:{row[3]}", "displayName": row[4]}


def passkey_credentials(user_account_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT PasskeyCredentialId,CredentialId,DeviceName,CreatedAt,LastUsedAt,RevokedAt FROM dbo.PasskeyCredential WHERE UserAccountId=%s ORDER BY CreatedAt DESC", (user_account_id,))
        return [{"id": int(r[0]), "credentialId": bytes(r[1]), "deviceName": r[2],
                 "createdAt": r[3].isoformat(), "lastUsedAt": r[4].isoformat() if r[4] else None,
                 "revokedAt": r[5].isoformat() if r[5] else None} for r in cur.fetchall()]


def active_passkey_credential_ids(account_type: str) -> list[bytes]:
    """Return active credentials for one login entry (employee or dealer)."""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.CredentialId
              FROM dbo.PasskeyCredential p
              JOIN dbo.UserAccount a ON a.UserAccountId=p.UserAccountId
             WHERE a.AccountType=%s
               AND a.AccountStatus='ACTIVE'
               AND a.IsLoginEnabled=1
               AND p.RevokedAt IS NULL
             ORDER BY p.PasskeyCredentialId
        """, (account_type,))
        return [bytes(row[0]) for row in cur.fetchall()]


def save_passkey(*, invitation_id: int, user_account_id: int, credential_id: bytes,
                 public_key: bytes, sign_count: int, transports: str | None, device_name: str) -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""INSERT dbo.PasskeyCredential(UserAccountId,CredentialId,PublicKey,SignCount,Transports,DeviceName)
                       VALUES(%s,%s,%s,%s,%s,%s)""",
                    (user_account_id, pytds.Binary(credential_id), pytds.Binary(public_key), sign_count, transports, device_name))
        cur.execute("""UPDATE dbo.PasskeyRegistrationInvitation SET UsedAt=SYSDATETIME()
                        WHERE InvitationId=%s AND UserAccountId=%s AND UsedAt IS NULL AND RevokedAt IS NULL AND ExpiresAt>SYSDATETIME()""",
                    (invitation_id, user_account_id))
        if cur.rowcount != 1:
            raise ValueError("註冊邀請已失效")
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def passkey_for_login(raw_credential_id: str, account_type: str) -> dict[str, Any] | None:
    credential_id = _b64url_decode(raw_credential_id)
    sql = """
    SELECT p.PasskeyCredentialId,p.UserAccountId,p.PublicKey,p.SignCount,a.AccountType,
           a.EmployeeId,a.DealerId,COALESCE(e.EmployeeName,d.DealerName)
      FROM dbo.PasskeyCredential p
      JOIN dbo.UserAccount a ON a.UserAccountId=p.UserAccountId
      LEFT JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId
      LEFT JOIN dbo.Dealer d ON d.DealerId=a.DealerId
     WHERE p.CredentialId=%s AND p.RevokedAt IS NULL AND a.AccountType=%s
       AND a.IsLoginEnabled=1 AND a.AccountStatus='ACTIVE'
    """
    with connect() as conn:
        row = _one(conn.cursor(), sql, (pytds.Binary(credential_id), account_type))
    if row is None:
        return None
    return {"passkeyCredentialId": int(row[0]), "userAccountId": int(row[1]),
            "publicKey": bytes(row[2]), "signCount": int(row[3]), "accountType": row[4],
            "employeeId": int(row[5]) if row[5] is not None else None,
            "dealerId": int(row[6]) if row[6] is not None else None, "displayName": row[7]}


def record_passkey_login(passkey_id: int, account_id: int, new_sign_count: int) -> None:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE dbo.PasskeyCredential SET SignCount=CASE WHEN %s>SignCount THEN %s ELSE SignCount END,LastUsedAt=SYSDATETIME() WHERE PasskeyCredentialId=%s", (new_sign_count, new_sign_count, passkey_id))
        cur.execute("UPDATE dbo.UserAccount SET LastLoginAt=SYSDATETIME() WHERE UserAccountId=%s", (account_id,))
        conn.commit()


def create_passkey_invitation(account_type: str, owner_ref: str, token_hash: bytes, creator_employee_id: int | None = None) -> datetime:
    if account_type not in {"EMPLOYEE", "DEALER"}:
        raise ValueError("account type must be EMPLOYEE or DEALER")
    conn = connect()
    try:
        cur = conn.cursor()
        if account_type == "EMPLOYEE":
            owner = _one(cur, "SELECT EmployeeId FROM dbo.Employee WHERE EmployeeNo=%s", (owner_ref,))
            owner_column = "EmployeeId"
        else:
            owner = _one(cur, "SELECT DealerId FROM dbo.Dealer WHERE DealerCode=%s", (owner_ref,))
            owner_column = "DealerId"
        if owner is None:
            raise ValueError(f"找不到 {owner_ref}")
        account = _one(cur, f"SELECT UserAccountId FROM dbo.UserAccount WHERE {owner_column}=%s", (owner[0],))
        if account is None:
            cur.execute(f"INSERT dbo.UserAccount(AccountType,{owner_column}) VALUES(%s,%s)", (account_type, owner[0]))
            account = _one(cur, f"SELECT UserAccountId FROM dbo.UserAccount WHERE {owner_column}=%s", (owner[0],))
        creator = (creator_employee_id,) if creator_employee_id is not None else _one(cur, "SELECT TOP 1 EmployeeId FROM dbo.Employee WHERE TerminationDate IS NULL ORDER BY EmployeeId")
        if creator is None or _one(cur, "SELECT 1 FROM dbo.Employee WHERE EmployeeId=%s AND TerminationDate IS NULL", (creator[0],)) is None:
            raise ValueError("沒有可用的邀請建立人")
        cur.execute("UPDATE dbo.UserAccount SET IsLoginEnabled=1,AccountStatus='ACTIVE' WHERE UserAccountId=%s", (account[0],))
        cur.execute("""UPDATE dbo.PasskeyRegistrationInvitation SET RevokedAt=SYSDATETIME()
                       WHERE UserAccountId=%s AND UsedAt IS NULL AND RevokedAt IS NULL""", (account[0],))
        row = _one(cur, """INSERT dbo.PasskeyRegistrationInvitation(UserAccountId,TokenHash,ExpiresAt,CreatedByEmployeeId)
                       OUTPUT inserted.ExpiresAt VALUES(%s,%s,DATEADD(minute,15,SYSDATETIME()),%s)""", (account[0], pytds.Binary(token_hash), creator[0]))
        conn.commit(); return row[0]
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def passkey_accounts(account_type: str) -> list[dict[str, Any]]:
    if account_type not in {"EMPLOYEE", "DEALER"}:
        raise ValueError("帳號類型不正確")
    if account_type == "EMPLOYEE":
        sql = """
        SELECT e.EmployeeNo,e.EmployeeName,CASE WHEN e.TerminationDate IS NULL THEN 1 ELSE 0 END,
               a.UserAccountId,a.IsLoginEnabled,a.AccountStatus,a.LastLoginAt,a.CreatedAt
          FROM dbo.Employee e
          LEFT JOIN dbo.UserAccount a ON a.EmployeeId=e.EmployeeId AND a.AccountType='EMPLOYEE'
         ORDER BY CASE WHEN e.TerminationDate IS NULL THEN 0 ELSE 1 END,e.EmployeeNo
        """
    else:
        sql = """
        SELECT d.DealerCode,d.DealerName,CAST(1 AS bit),
               a.UserAccountId,a.IsLoginEnabled,a.AccountStatus,a.LastLoginAt,a.CreatedAt
          FROM dbo.Dealer d
          LEFT JOIN dbo.UserAccount a ON a.DealerId=d.DealerId AND a.AccountType='DEALER'
         ORDER BY d.DealerCode
        """
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql);rows=cur.fetchall();result=[]
        for row in rows:
            account_id=int(row[3]) if row[3] is not None else None
            credentials=[];pending_until=None
            if account_id is not None:
                cur.execute("""SELECT PasskeyCredentialId,DeviceName,CreatedAt,LastUsedAt,RevokedAt
                                 FROM dbo.PasskeyCredential WHERE UserAccountId=%s ORDER BY RevokedAt,CreatedAt DESC""",(account_id,))
                credentials=[{"id":int(x[0]),"deviceName":x[1] or "未命名 Passkey",
                              "createdAt":x[2].isoformat(timespec="minutes"),
                              "lastUsedAt":x[3].isoformat(timespec="minutes") if x[3] else None,
                              "revokedAt":x[4].isoformat(timespec="minutes") if x[4] else None} for x in cur.fetchall()]
                invitation=_one(cur,"""SELECT TOP 1 ExpiresAt FROM dbo.PasskeyRegistrationInvitation
                                         WHERE UserAccountId=%s AND UsedAt IS NULL AND RevokedAt IS NULL
                                           AND ExpiresAt>SYSDATETIME() ORDER BY CreatedAt DESC""",(account_id,))
                pending_until=invitation[0].isoformat(timespec="minutes") if invitation else None
            result.append({"type":account_type,"ownerRef":row[0],"name":row[1],"ownerActive":bool(row[2]),
                           "accountId":account_id,"loginEnabled":bool(row[4]) and row[5]=="ACTIVE" if account_id is not None else False,
                           "accountStatus":row[5] if account_id is not None else "NOT_CREATED",
                           "lastLoginAt":row[6].isoformat(timespec="minutes") if row[6] else None,
                           "accountCreatedAt":row[7].isoformat(timespec="minutes") if row[7] else None,
                           "pendingInvitationUntil":pending_until,"credentials":credentials,
                           "activeCredentialCount":sum(1 for item in credentials if item["revokedAt"] is None)})
        return result


def set_passkey_account_enabled(account_type: str, owner_ref: str, enabled: bool) -> None:
    if account_type not in {"EMPLOYEE", "DEALER"}:raise ValueError("帳號類型不正確")
    conn=connect()
    try:
        cur=conn.cursor();table="Employee" if account_type=="EMPLOYEE" else "Dealer";id_column="EmployeeId" if account_type=="EMPLOYEE" else "DealerId";ref_column="EmployeeNo" if account_type=="EMPLOYEE" else "DealerCode"
        owner=_one(cur,f"SELECT {id_column} FROM dbo.{table} WHERE {ref_column}=%s",(owner_ref,))
        if owner is None:raise LookupError("找不到指定的帳號所有者")
        account=_one(cur,f"SELECT UserAccountId FROM dbo.UserAccount WHERE {id_column}=%s",(owner[0],))
        if account is None:
            if not enabled:raise LookupError("此對象尚未建立登入帳號")
            cur.execute(f"INSERT dbo.UserAccount(AccountType,{id_column},IsLoginEnabled,AccountStatus) VALUES(%s,%s,1,'ACTIVE')",(account_type,owner[0]))
        else:
            cur.execute("UPDATE dbo.UserAccount SET IsLoginEnabled=%s,AccountStatus=%s WHERE UserAccountId=%s",(enabled,"ACTIVE" if enabled else "DISABLED",account[0]))
            if not enabled:
                cur.execute("""UPDATE dbo.PasskeyRegistrationInvitation SET RevokedAt=SYSDATETIME()
                               WHERE UserAccountId=%s AND UsedAt IS NULL AND RevokedAt IS NULL""",(account[0],))
        conn.commit()
    except Exception:conn.rollback();raise
    finally:conn.close()


def revoke_passkey_credential(credential_id: int) -> bool:
    with connect() as conn:
        cur=conn.cursor();cur.execute("UPDATE dbo.PasskeyCredential SET RevokedAt=SYSDATETIME() WHERE PasskeyCredentialId=%s AND RevokedAt IS NULL",(credential_id,));changed=cur.rowcount>0;conn.commit();return changed


def account_login_allowed(user_account_id: int) -> bool:
    with connect() as conn:
        row=_one(conn.cursor(),"SELECT 1 FROM dbo.UserAccount WHERE UserAccountId=%s AND IsLoginEnabled=1 AND AccountStatus='ACTIVE'",(user_account_id,))
        return row is not None


POSITION_TO_UI = {"SALES": "業務", "DIRECTOR": "處長", "MANAGER": "經理"}
POSITION_TO_DB = {value: key for key, value in POSITION_TO_UI.items()}


def connect():
    return pytds.connect(
        required("LGSALEOUT_DB_HOST"),
        port=int(required("LGSALEOUT_DB_PORT")),
        database=required("LGSALEOUT_DB_NAME"),
        user=required("LGSALEOUT_DB_USER"),
        password=required("LGSALEOUT_DB_PASSWORD"),
        login_timeout=8,
        timeout=15,
    )


def _one(cur, sql: str, params=()):
    cur.execute(sql, params)
    return cur.fetchone()


def _optional_quantity(item: dict[str, Any], key: str, label: str) -> int | None:
    raw = item.get(key)
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}數量必須是整數") from exc
    if not 1 <= value <= 10:
        raise ValueError(f"{label}數量只能是 1～10")
    return value


def _parse_effective(value: Any) -> datetime:
    try:
        effective = datetime.fromisoformat(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("生效時間格式不正確") from exc
    if effective.tzinfo is not None:
        effective = effective.astimezone().replace(tzinfo=None)
    return effective.replace(second=0, microsecond=0)


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
           COUNT(DISTINCT CASE WHEN e.SubmittedAt IS NOT NULL OR p.TaskPhotoId IS NOT NULL THEN e.TaskExecutionId END),
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
              JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId AND e.TerminationDate IS NULL
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


def dealers(dealer_id: int | None = None) -> list[dict[str, Any]]:
    sql = """
    SELECT d.DealerId,d.DealerCode,d.DealerName,COALESCE(l.DealerStatus,'—'),COALESCE(e.EmployeeName,'未指派'),MAX(v.ReportDateTime),
           d.TaxId,d.Area,d.DealerCondition
      FROM dbo.Dealer d
      LEFT JOIN dbo.DealerLevelHistory l ON l.DealerId=d.DealerId AND l.EndDateTime IS NULL
      LEFT JOIN dbo.DealerAssignmentHistory a ON a.DealerId=d.DealerId AND a.EndDateTime IS NULL
      LEFT JOIN dbo.Employee e ON e.EmployeeId=a.EmployeeId
      LEFT JOIN dbo.StoreVisit v ON v.DealerId=d.DealerId AND v.RecordStatus='ACTIVE'
     WHERE (%s IS NULL OR d.DealerId=%s)
     GROUP BY d.DealerId,d.DealerCode,d.DealerName,l.DealerStatus,e.EmployeeName,d.TaxId,d.Area,d.DealerCondition
     ORDER BY d.DealerId
    """
    with connect() as conn:
        cur=conn.cursor(); cur.execute(sql, (dealer_id, dealer_id))
        return [{"id":int(r[0]),"code":r[1],"name":r[2],"level":r[3],"employee":r[4],"lastVisit":r[5].date().isoformat() if r[5] else None,
                 "taxId":r[6] or "","area":r[7] or "","condition":r[8]} for r in cur.fetchall()]


def create_dealer(data: dict[str, Any]) -> int:
    conn = connect()
    try:
        cur = conn.cursor(); creator_id = _creator_id(cur)
        row = _one(cur, """INSERT dbo.Dealer(DealerCode,DealerName,TaxId,Area,DealerCondition)
                           OUTPUT inserted.DealerId VALUES(%s,%s,%s,%s,%s)""",
                   (data["code"], data["name"], data["taxId"], data["area"], data["condition"]))
        dealer_id = int(row[0])
        cur.execute("""INSERT dbo.DealerLevelHistory(DealerId,DealerStatus,StartDateTime,ChangeReason)
                       VALUES(%s,%s,SYSDATETIME(),%s)""", (dealer_id, data["level"], "建立經銷商主檔"))
        employee_id = data.get("employeeId")
        if employee_id:
            cur.execute("""INSERT dbo.DealerAssignmentHistory
                           (DealerId,EmployeeId,StartDateTime,ChangeReason,CreatedByEmployeeId)
                           VALUES(%s,%s,SYSDATETIME(),%s,%s)""",
                        (dealer_id, int(employee_id), "建立經銷商並指派負責業務", creator_id))
        conn.commit(); return dealer_id
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


def update_dealer(dealer_id: int, data: dict[str, Any]) -> bool:
    conn = connect()
    try:
        cur = conn.cursor(); creator_id = _creator_id(cur)
        cur.execute("""UPDATE dbo.Dealer SET DealerCode=%s,DealerName=%s,TaxId=%s,Area=%s,DealerCondition=%s
                        WHERE DealerId=%s""",
                    (data["code"], data["name"], data["taxId"], data["area"], data["condition"], dealer_id))
        if cur.rowcount == 0:
            conn.rollback(); return False
        current_level = _one(cur, "SELECT DealerLevelHistoryId,DealerStatus FROM dbo.DealerLevelHistory WHERE DealerId=%s AND EndDateTime IS NULL", (dealer_id,))
        if current_level is None or current_level[1] != data["level"]:
            if current_level is not None:
                cur.execute("""UPDATE dbo.DealerLevelHistory
                                  SET EndDateTime=CASE WHEN SYSDATETIME()<=StartDateTime
                                                       THEN DATEADD(second,1,StartDateTime)
                                                       ELSE SYSDATETIME() END
                                WHERE DealerLevelHistoryId=%s""", (current_level[0],))
            cur.execute("INSERT dbo.DealerLevelHistory(DealerId,DealerStatus,StartDateTime,ChangeReason) VALUES(%s,%s,SYSDATETIME(),%s)",
                        (dealer_id, data["level"], "經銷商基本資料維護"))
        requested_employee = int(data["employeeId"]) if data.get("employeeId") else None
        current_owner = _one(cur, "SELECT DealerAssignmentId,EmployeeId FROM dbo.DealerAssignmentHistory WHERE DealerId=%s AND EndDateTime IS NULL", (dealer_id,))
        current_employee = int(current_owner[1]) if current_owner else None
        if current_employee != requested_employee:
            if current_owner:
                cur.execute("""UPDATE dbo.DealerAssignmentHistory
                                  SET EndDateTime=CASE WHEN SYSDATETIME()<=StartDateTime
                                                       THEN DATEADD(second,1,StartDateTime)
                                                       ELSE SYSDATETIME() END
                                WHERE DealerAssignmentId=%s""", (current_owner[0],))
            if requested_employee is not None:
                cur.execute("""INSERT dbo.DealerAssignmentHistory
                               (DealerId,EmployeeId,StartDateTime,ChangeReason,CreatedByEmployeeId)
                               VALUES(%s,%s,SYSDATETIME(),%s,%s)""",
                            (dealer_id, requested_employee, "經銷商基本資料維護", creator_id))
        conn.commit(); return True
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()


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
        cur=conn.cursor();current=_one(cur,"SELECT TerminationDate FROM dbo.Employee WHERE EmployeeId=%s",(employee_id,))
        if current is None:return False
        end_date=data.get("endDate") or None
        if current[0] is not None and end_date is None:raise ValueError("已離職員工不可直接取消離職，請建立復職流程")
        terminating=current[0] is None and end_date is not None
        cur.execute("UPDATE dbo.Employee SET EmployeeNo=%s,EmployeeName=%s,HireDate=%s,TerminationDate=%s WHERE EmployeeId=%s",(data["number"],data["name"],data["hireDate"],end_date,employee_id));changed=cur.rowcount>0
        if terminating:
            effective=datetime.now().replace(microsecond=0);creator_id=_creator_id(cur)
            org_row=_one(cur,"SELECT OrgUnitId FROM dbo.EmployeeOrgAssignmentHistory WHERE EmployeeId=%s AND EndDateTime IS NULL",(employee_id,))
            cur.execute("""UPDATE dbo.EmployeePositionHistory SET EndDateTime=CASE WHEN %s<=StartDateTime THEN DATEADD(second,1,StartDateTime) ELSE %s END WHERE EmployeeId=%s AND EndDateTime IS NULL""",(effective,effective,employee_id))
            cur.execute("""UPDATE dbo.EmployeeOrgAssignmentHistory SET EndDateTime=CASE WHEN %s<=StartDateTime THEN DATEADD(second,1,StartDateTime) ELSE %s END WHERE EmployeeId=%s AND EndDateTime IS NULL""",(effective,effective,employee_id))
            cur.execute("SELECT DealerAssignmentId,DealerId,StartDateTime FROM dbo.DealerAssignmentHistory WHERE EmployeeId=%s AND EndDateTime IS NULL",(employee_id,));assignments=cur.fetchall()
            for assignment_id,dealer_id,start_at in assignments:
                closed_at=effective if effective>start_at else start_at+timedelta(seconds=1)
                cur.execute("UPDATE dbo.DealerAssignmentHistory SET EndDateTime=%s WHERE DealerAssignmentId=%s",(closed_at,assignment_id))
                cur.execute("""UPDATE dbo.DealerTransferReview
                                  SET SourceDealerAssignmentId=%s,SourceEmployeeId=%s,TriggerType='TERMINATION',
                                      FromOrgUnitId=%s,ToOrgUnitId=NULL,TriggeredAt=%s
                                WHERE DealerId=%s AND ReviewStatus='OPEN'""",
                            (assignment_id,employee_id,org_row[0] if org_row else None,closed_at,dealer_id))
                cur.execute("""IF NOT EXISTS(SELECT 1 FROM dbo.DealerTransferReview WHERE DealerId=%s AND ReviewStatus='OPEN')
                               INSERT dbo.DealerTransferReview(DealerId,SourceDealerAssignmentId,SourceEmployeeId,TriggerType,FromOrgUnitId,TriggeredAt)
                               VALUES(%s,%s,%s,'TERMINATION',%s,%s)""",(dealer_id,dealer_id,assignment_id,employee_id,org_row[0] if org_row else None,closed_at))
            account=_one(cur,"SELECT UserAccountId FROM dbo.UserAccount WHERE EmployeeId=%s",(employee_id,))
            if account:
                cur.execute("UPDATE dbo.UserAccount SET IsLoginEnabled=0,AccountStatus='DISABLED' WHERE UserAccountId=%s",(account[0],))
                cur.execute("UPDATE dbo.PasskeyRegistrationInvitation SET RevokedAt=SYSDATETIME() WHERE UserAccountId=%s AND UsedAt IS NULL AND RevokedAt IS NULL",(account[0],))
        conn.commit();return changed
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


def photo_tasks(employee_id: int | None = None) -> list[dict[str,Any]]:
    sql="""SELECT e.TaskExecutionId,t.VisitTaskId,t.TaskTitle,t.Instruction,d.DealerId,d.DealerName,t.ValidFrom,t.DueDate,e.SubmittedAt,t.SampleTaskExecutionId,e.ExecutionNote FROM dbo.VisitTaskExecution e JOIN dbo.VisitTask t ON t.VisitTaskId=e.VisitTaskId JOIN dbo.Dealer d ON d.DealerId=e.DealerId WHERE t.RecordStatus='ACTIVE' AND (%s IS NULL OR e.ResponsibleEmployeeId=%s) ORDER BY t.DueDate,e.TaskExecutionId"""
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql,(employee_id,employee_id));rows=cur.fetchall();result=[]
        for r in rows:
            samples=[]
            if r[9] is not None:
                cur.execute("SELECT TaskPhotoId,PhotoDescription,StoredFileName,StoredFilePath,SortOrder FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=%s ORDER BY SortOrder,TaskPhotoId",(r[9],));samples=[{"photoId":int(x[0]),"description":x[1] or "樣本照片","fileName":x[2],"filePath":x[3],"sortOrder":int(x[4])} for x in cur.fetchall()]
            cur.execute("SELECT TaskPhotoId,PhotoDescription,StoredFileName,StoredFilePath,SortOrder,SampleTaskPhotoId FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=%s ORDER BY SortOrder,TaskPhotoId",(r[0],))
            photos=[{"photoId":int(x[0]),"description":x[1] or "照片","fileName":x[2],"filePath":x[3],"sortOrder":int(x[4]),"samplePhotoId":int(x[5]) if x[5] else None} for x in cur.fetchall()]
            edit_until = r[8] + timedelta(hours=72) if r[8] else None
            result.append({"executionId":int(r[0]),"taskId":int(r[1]),"title":r[2],"instruction":r[3],"dealerId":int(r[4]),"dealer":r[5],"validFrom":r[6].isoformat(),"dueDate":r[7].isoformat(),"sample":samples,"photos":photos,"completed":r[8] is not None,"submittedAt":r[8].isoformat(timespec="minutes") if r[8] else None,"editUntil":edit_until.isoformat(timespec="minutes") if edit_until else None,"canEdit":r[8] is None or datetime.now() < edit_until,"executionNote":r[10]})
        return result


def add_photo(execution_id:int,description:str,stored_file_name:str|None=None,stored_file_path:str|None=None,sample_photo_id:int|None=None,employee_id:int|None=None,replace_photo_id:int|None=None) -> tuple[int,datetime]:
    conn=connect()
    try:
        token=stored_file_name or uuid.uuid4().hex+".jpg";path=stored_file_path or "prototype://"+token;cur=conn.cursor()
        allowed=_one(cur,"""SELECT SubmittedAt FROM dbo.VisitTaskExecution
                            WHERE TaskExecutionId=%s
                              AND (%s IS NULL OR ResponsibleEmployeeId=%s)
                              AND (SubmittedAt IS NULL OR DATEADD(hour,72,SubmittedAt)>SYSDATETIME())""",(execution_id,employee_id,employee_id))
        if allowed is None:raise PermissionError("此任務不存在、不屬於目前登入人員或已超過 72 小時修改期限")
        if replace_photo_id is not None:
            row=_one(cur,"""UPDATE dbo.VisitTaskPhoto SET SampleTaskPhotoId=%s,PhotoDescription=%s,
                       StoredFileName=%s,StoredFilePath=%s,CapturedAt=SYSDATETIME()
                       OUTPUT inserted.TaskPhotoId WHERE TaskPhotoId=%s AND TaskExecutionId=%s""",
                     (sample_photo_id,description,token,path,replace_photo_id,execution_id))
            if row is None:raise LookupError("找不到要重拍的照片")
        else:
            row=_one(cur,"""INSERT dbo.VisitTaskPhoto(TaskExecutionId,SampleTaskPhotoId,PhotoDescription,StoredFileName,StoredFilePath,CapturedAt,SortOrder) OUTPUT inserted.TaskPhotoId VALUES(%s,%s,%s,%s,%s,SYSDATETIME(),(SELECT COUNT(*) FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=%s))""",(execution_id,sample_photo_id,description,token,path,execution_id))
        completed_by=employee_id or _one(cur,"SELECT ResponsibleEmployeeId FROM dbo.VisitTaskExecution WHERE TaskExecutionId=%s",(execution_id,))[0]
        submitted=_one(cur,"""UPDATE dbo.VisitTaskExecution
                              SET CompletedByEmployeeId=COALESCE(CompletedByEmployeeId,%s),
                                  SubmittedAt=COALESCE(SubmittedAt,SYSDATETIME())
                              OUTPUT inserted.SubmittedAt WHERE TaskExecutionId=%s""",(completed_by,execution_id))
        conn.commit();return int(row[0]),submitted[0]
    except Exception:conn.rollback();raise
    finally:conn.close()


def complete_execution(execution_id:int,note:str|None,employee_id:int|None=None) -> datetime:
    conn=connect()
    try:
        cur=conn.cursor();state=_one(cur,"""SELECT t.SampleTaskExecutionId,e.ResponsibleEmployeeId,e.SubmittedAt,
            (SELECT COUNT(*) FROM dbo.VisitTaskPhoto sp WHERE sp.TaskExecutionId=t.SampleTaskExecutionId),
            (SELECT COUNT(DISTINCT p.SampleTaskPhotoId) FROM dbo.VisitTaskPhoto p WHERE p.TaskExecutionId=e.TaskExecutionId AND p.SampleTaskPhotoId IS NOT NULL),
            (SELECT COUNT(*) FROM dbo.VisitTaskPhoto p WHERE p.TaskExecutionId=e.TaskExecutionId)
            FROM dbo.VisitTaskExecution e JOIN dbo.VisitTask t ON t.VisitTaskId=e.VisitTaskId WHERE e.TaskExecutionId=%s""",(execution_id,))
        if state is None:raise LookupError("找不到任務執行資料")
        if employee_id is not None and int(state[1]) != employee_id:raise PermissionError("此任務不屬於目前登入人員")
        if state[2] is not None:
            return state[2]
        if note is None and state[0] is not None and int(state[4]) < int(state[3]):raise ValueError("尚有樣本對應照片未完成")
        if note is None and int(state[5]) == 0:raise ValueError("請至少上傳一張照片，或填寫不拍照原因")
        if note is not None and int(state[5]) > 0:raise ValueError("已有上傳照片，不能改用不拍照完成")
        completed_by=employee_id or int(state[1])
        row=_one(cur,"""UPDATE dbo.VisitTaskExecution SET CompletedByEmployeeId=%s,ExecutionNote=%s,SubmittedAt=SYSDATETIME() OUTPUT inserted.SubmittedAt WHERE TaskExecutionId=%s""",(completed_by,note,execution_id));
        if row is None: raise LookupError("找不到任務執行資料")
        conn.commit();return row[0]
    except Exception:conn.rollback();raise
    finally:conn.close()


def create_visit(data:dict[str,Any]) -> tuple[int,datetime]:
    conn=connect()
    try:
        cur=conn.cursor();dealer_id=int(data["dealerId"]);assignment=_one(cur,"SELECT DealerAssignmentId FROM dbo.DealerAssignmentHistory WHERE DealerId=%s AND EndDateTime IS NULL",(dealer_id,));account=(data.get("userAccountId"),) if data.get("userAccountId") else _one(cur,"SELECT TOP 1 UserAccountId FROM dbo.UserAccount WHERE AccountType='EMPLOYEE' AND IsLoginEnabled=1 ORDER BY UserAccountId")
        if account is None:raise ValueError("找不到可用的員工帳號")
        row=_one(cur,"""INSERT dbo.StoreVisit(DealerId,DealerAssignmentId,EntrySourceType,CreatedByUserAccountId) OUTPUT inserted.StoreVisitId,inserted.ReportDateTime VALUES(%s,%s,%s,%s)""",(dealer_id,assignment[0] if assignment else None,data.get("entrySourceType","EMPLOYEE"),account[0]));visit_id=int(row[0])
        for item in data["details"]:
            sell=_optional_quantity(item,"sellOutQuantity","實銷");display=_optional_quantity(item,"displayQuantity","陳列")
            cur.execute("INSERT dbo.StoreVisitProductDetail(StoreVisitId,ProductId,SellOutQuantity,SellOutDate,DisplayQuantity) VALUES(%s,%s,%s,%s,%s)",(visit_id,int(item["productId"]),sell,item.get("sellOutDate") if sell else None,display))
        conn.commit();return visit_id,row[1]
    except Exception:conn.rollback();raise
    finally:conn.close()


def mobile_dashboard(employee_id: int | None = None, dealer_id: int | None = None) -> dict[str, Any]:
    """Return the mobile home data without inventing data outside the ERD."""
    with connect() as conn:
        cur = conn.cursor()
        if dealer_id is not None:
            dealer_rows = dealers(dealer_id)
        else:
            cur.execute("""
                SELECT d.DealerId,d.DealerCode,d.DealerName,COALESCE(l.DealerStatus,'—'),
                       COALESCE(owner.EmployeeName,'未指派'),MAX(v.ReportDateTime)
                  FROM dbo.Dealer d
                  JOIN dbo.DealerAssignmentHistory a ON a.DealerId=d.DealerId AND a.EndDateTime IS NULL
                  LEFT JOIN dbo.DealerLevelHistory l ON l.DealerId=d.DealerId AND l.EndDateTime IS NULL
                  LEFT JOIN dbo.Employee owner ON owner.EmployeeId=a.EmployeeId
                  LEFT JOIN dbo.StoreVisit v ON v.DealerId=d.DealerId AND v.RecordStatus='ACTIVE'
                 WHERE (%s IS NULL OR a.EmployeeId=%s)
                 GROUP BY d.DealerId,d.DealerCode,d.DealerName,l.DealerStatus,owner.EmployeeName
                 ORDER BY MAX(v.ReportDateTime),d.DealerName
            """, (employee_id, employee_id))
            dealer_rows = [{"id":int(r[0]),"code":r[1],"name":r[2],"level":r[3],"employee":r[4],
                            "lastVisit":r[5].isoformat(timespec="minutes") if r[5] else None}
                           for r in cur.fetchall()]
        visit_rows = visits(employee_id=employee_id, dealer_id=dealer_id, limit=200)
        editable = sum(1 for item in visit_rows if item["canEdit"] and item["entrySourceType"] == "EMPLOYEE")
        dealer_reports = sum(1 for item in visit_rows if item["entrySourceType"] == "DEALER")
        locked = sum(1 for item in visit_rows if not item["canEdit"])
        return {"dealers": dealer_rows, "counts": {"editable": editable, "dealer": dealer_reports, "locked": locked}}


def dealer_summary(dealer_id: int) -> dict[str, Any]:
    with connect() as conn:
        cur = conn.cursor()
        row = _one(cur, """
            SELECT TOP 1 v.StoreVisitId,v.ReportDateTime,v.EntrySourceType,
                   COUNT(pd.StoreVisitProductDetailId),COALESCE(SUM(pd.SellOutQuantity),0),
                   COALESCE(SUM(pd.DisplayQuantity),0)
              FROM dbo.StoreVisit v
              LEFT JOIN dbo.StoreVisitProductDetail pd ON pd.StoreVisitId=v.StoreVisitId
             WHERE v.DealerId=%s AND v.RecordStatus='ACTIVE'
             GROUP BY v.StoreVisitId,v.ReportDateTime,v.EntrySourceType
             ORDER BY v.ReportDateTime DESC
        """, (dealer_id,))
        if row is None:
            return {"lastVisit": None, "detailCount": 0, "sellOutTotal": 0, "displayTotal": 0, "entrySourceType": None}
        return {"lastVisitId":int(row[0]), "lastVisit":row[1].isoformat(timespec="minutes"),
                "entrySourceType":row[2], "detailCount":int(row[3]),
                "sellOutTotal":int(row[4]), "displayTotal":int(row[5])}


def reportable_products(dealer_id: int) -> list[dict[str, Any]]:
    """Products in the latest effective Official opening-inventory batch."""
    sql = """
    WITH LatestBatch AS (
        SELECT TOP 1 ImportBatchId
          FROM dbo.ImportBatch
         WHERE ImportType='OPENING_INVENTORY' AND ImportStatus='Official'
         ORDER BY DataMonth DESC,ImportedAt DESC,ImportBatchId DESC
    )
    SELECT p.ProductId,p.ProductCode,p.ProductName,COALESCE(p.CategoryLevel1,''),COALESCE(p.CategoryLevel2,'')
      FROM dbo.MonthlyOpeningInventoryDetail d
      JOIN LatestBatch b ON b.ImportBatchId=d.ImportBatchId
      JOIN dbo.Product p ON p.ProductId=d.ProductId AND p.IsActive=1
     WHERE d.DealerId=%s
     ORDER BY p.ProductCode
    """
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql,(dealer_id,));rows=cur.fetchall()
    return [{"id":int(r[0]),"code":r[1],"name":r[2],"category":r[3] or r[4]} for r in rows]


def visits(*, employee_id: int | None = None, dealer_id: int | None = None,
           account_id: int | None = None, account_type: str = "EMPLOYEE", limit: int = 500) -> list[dict[str, Any]]:
    sql = """
    SELECT TOP (%s) v.StoreVisitId,v.DealerId,d.DealerCode,d.DealerName,v.EntrySourceType,
           v.ReportDateTime,v.RecordStatus,v.CreatedByUserAccountId,
           owner.EmployeeName,COALESCE(writerE.EmployeeName,writerD.DealerName),
           COUNT(pd.StoreVisitProductDetailId),COALESCE(SUM(pd.SellOutQuantity),0),
           COALESCE(SUM(pd.DisplayQuantity),0),v.UpdatedAt
      FROM dbo.StoreVisit v
      JOIN dbo.Dealer d ON d.DealerId=v.DealerId
      LEFT JOIN dbo.DealerAssignmentHistory a ON a.DealerAssignmentId=v.DealerAssignmentId
      LEFT JOIN dbo.Employee owner ON owner.EmployeeId=a.EmployeeId
      JOIN dbo.UserAccount ua ON ua.UserAccountId=v.CreatedByUserAccountId
      LEFT JOIN dbo.Employee writerE ON writerE.EmployeeId=ua.EmployeeId
      LEFT JOIN dbo.Dealer writerD ON writerD.DealerId=ua.DealerId
      LEFT JOIN dbo.StoreVisitProductDetail pd ON pd.StoreVisitId=v.StoreVisitId
     WHERE (%s IS NULL OR v.DealerId=%s)
       AND (%s IS NULL OR a.EmployeeId=%s)
       AND (%s<>'DEALER' OR (v.DealerId=%s AND v.CreatedByUserAccountId=%s))
     GROUP BY v.StoreVisitId,v.DealerId,d.DealerCode,d.DealerName,v.EntrySourceType,
              v.ReportDateTime,v.RecordStatus,v.CreatedByUserAccountId,owner.EmployeeName,
              writerE.EmployeeName,writerD.DealerName,v.UpdatedAt
     ORDER BY v.ReportDateTime DESC
    """
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql,(limit,dealer_id,dealer_id,employee_id,employee_id,
                                          account_type,dealer_id,account_id));rows=cur.fetchall()
    now=datetime.now();result=[]
    for r in rows:
        deadline=r[5]+timedelta(hours=72)
        can_edit=r[6]=='ACTIVE' and now < deadline and (
            (account_type=='EMPLOYEE' and r[4]=='EMPLOYEE') or
            (account_type=='DEALER' and account_id is not None and int(r[7])==account_id)
        )
        result.append({"id":int(r[0]),"code":f"RPT-{r[5]:%y%m%d}-{int(r[0]):03d}","dealerId":int(r[1]),
                       "dealerCode":r[2],"dealer":r[3],"entrySourceType":r[4],
                       "reportDateTime":r[5].isoformat(timespec="minutes"),"recordStatus":r[6],
                       "responsibleEmployee":r[8] or "未指派","createdBy":r[9] or "—",
                       "detailCount":int(r[10]),"sellOutTotal":int(r[11]),"displayTotal":int(r[12]),
                       "updatedAt":r[13].isoformat(timespec="seconds") if r[13] else None,
                       "editableUntil":deadline.isoformat(timespec="minutes"),"canEdit":can_edit,
                       "remainingMinutes":max(0,int((deadline-now).total_seconds()//60))})
    return result


def visit_detail(visit_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        cur=conn.cursor();row=_one(cur,"""
            SELECT v.StoreVisitId,v.DealerId,d.DealerCode,d.DealerName,v.EntrySourceType,v.ReportDateTime,
                   v.RecordStatus,v.CreatedByUserAccountId,owner.EmployeeName,
                   COALESCE(writerE.EmployeeName,writerD.DealerName),v.UpdatedAt
              FROM dbo.StoreVisit v JOIN dbo.Dealer d ON d.DealerId=v.DealerId
              LEFT JOIN dbo.DealerAssignmentHistory a ON a.DealerAssignmentId=v.DealerAssignmentId
              LEFT JOIN dbo.Employee owner ON owner.EmployeeId=a.EmployeeId
              JOIN dbo.UserAccount ua ON ua.UserAccountId=v.CreatedByUserAccountId
              LEFT JOIN dbo.Employee writerE ON writerE.EmployeeId=ua.EmployeeId
              LEFT JOIN dbo.Dealer writerD ON writerD.DealerId=ua.DealerId
             WHERE v.StoreVisitId=%s
        """,(visit_id,))
        if row is None:return None
        cur.execute("""SELECT pd.ProductId,p.ProductCode,p.ProductName,pd.SellOutQuantity,pd.SellOutDate,pd.DisplayQuantity
                         FROM dbo.StoreVisitProductDetail pd JOIN dbo.Product p ON p.ProductId=pd.ProductId
                        WHERE pd.StoreVisitId=%s ORDER BY p.ProductCode""",(visit_id,))
        details=[{"productId":int(x[0]),"code":x[1],"name":x[2],"sellOutQuantity":x[3],
                  "sellOutDate":x[4].isoformat() if x[4] else None,"displayQuantity":x[5]} for x in cur.fetchall()]
    deadline=row[5]+timedelta(hours=72)
    return {"id":int(row[0]),"dealerId":int(row[1]),"dealerCode":row[2],"dealer":row[3],
            "entrySourceType":row[4],"reportDateTime":row[5].isoformat(timespec="minutes"),
            "recordStatus":row[6],"createdByUserAccountId":int(row[7]),"responsibleEmployee":row[8] or "未指派",
            "createdBy":row[9] or "—","updatedAt":row[10].isoformat(timespec="seconds") if row[10] else None,
            "editableUntil":deadline.isoformat(timespec="minutes"),"details":details}


def update_visit(visit_id: int, details: list[dict[str, Any]], *, account_id: int, account_type: str) -> None:
    conn=connect()
    try:
        cur=conn.cursor();row=_one(cur,"SELECT EntrySourceType,CreatedByUserAccountId,ReportDateTime,RecordStatus FROM dbo.StoreVisit WHERE StoreVisitId=%s",(visit_id,))
        if row is None:raise LookupError("找不到巡店回報")
        if row[3] != 'ACTIVE' or _one(cur,"SELECT CASE WHEN SYSDATETIME()<DATEADD(hour,72,%s) THEN 1 ELSE 0 END",(row[2],))[0] != 1:
            raise PermissionError("此筆回報已超過 72 小時修改期限或已作廢")
        if account_type=='EMPLOYEE' and row[0] != 'EMPLOYEE':raise PermissionError("業務帳號不可修改經銷商自行回報")
        if account_type=='DEALER' and int(row[1]) != account_id:raise PermissionError("只能修改由自己的帳號建立的回報")
        cur.execute("DELETE dbo.StoreVisitProductDetail WHERE StoreVisitId=%s",(visit_id,))
        for item in details:
            sell=_optional_quantity(item,'sellOutQuantity','實銷')
            display=_optional_quantity(item,'displayQuantity','陳列')
            if sell is None and display is None:continue
            cur.execute("""INSERT dbo.StoreVisitProductDetail(StoreVisitId,ProductId,SellOutQuantity,SellOutDate,DisplayQuantity)
                           VALUES(%s,%s,%s,%s,%s)""",(visit_id,int(item['productId']),sell,item.get('sellOutDate') if sell else None,display))
        cur.execute("UPDATE dbo.StoreVisit SET UpdatedAt=SYSDATETIME(),UpdatedByUserAccountId=%s WHERE StoreVisitId=%s",(account_id,visit_id))
        conn.commit()
    except Exception:conn.rollback();raise
    finally:conn.close()


def task_detail(task_id: int) -> dict[str, Any] | None:
    task=next((x for x in tasks() if x['id']==task_id),None)
    if task is None:return None
    with connect() as conn:
        cur=conn.cursor();cur.execute("""
            SELECT e.TaskExecutionId,d.DealerId,d.DealerCode,d.DealerName,emp.EmployeeName,
                   COALESCE(e.SubmittedAt,(SELECT MIN(p.UploadedAt) FROM dbo.VisitTaskPhoto p WHERE p.TaskExecutionId=e.TaskExecutionId)),
                   e.ExecutionNote,CASE WHEN t.SampleTaskExecutionId=e.TaskExecutionId THEN 1 ELSE 0 END
              FROM dbo.VisitTaskExecution e JOIN dbo.VisitTask t ON t.VisitTaskId=e.VisitTaskId
              JOIN dbo.Dealer d ON d.DealerId=e.DealerId JOIN dbo.Employee emp ON emp.EmployeeId=e.ResponsibleEmployeeId
             WHERE e.VisitTaskId=%s ORDER BY e.SubmittedAt DESC,d.DealerName
        """,(task_id,));executions=[]
        for r in cur.fetchall():
            cur.execute("SELECT TaskPhotoId,PhotoDescription,StoredFileName,StoredFilePath,SortOrder,SampleTaskPhotoId FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=%s ORDER BY SortOrder,TaskPhotoId",(r[0],))
            photos=[{"id":int(p[0]),"description":p[1] or "照片","fileName":p[2],"filePath":p[3],"sortOrder":int(p[4]),"samplePhotoId":int(p[5]) if p[5] else None} for p in cur.fetchall()]
            executions.append({"executionId":int(r[0]),"dealerId":int(r[1]),"dealerCode":r[2],"dealer":r[3],"employee":r[4],
                               "submittedAt":r[5].isoformat(timespec="minutes") if r[5] else None,"note":r[6],"isSample":bool(r[7]),"photos":photos})
    return {**task,"executions":executions}


def report_details(limit: int = 1000) -> list[dict[str, Any]]:
    sql="""
    SELECT TOP (%s) v.StoreVisitId,v.ReportDateTime,d.DealerName,v.EntrySourceType,
           owner.EmployeeName,COALESCE(writerE.EmployeeName,writerD.DealerName),
           p.ProductCode,p.ProductName,pd.SellOutQuantity,pd.SellOutDate,pd.DisplayQuantity,
           v.RecordStatus,DATEADD(hour,72,v.ReportDateTime)
      FROM dbo.StoreVisitProductDetail pd
      JOIN dbo.StoreVisit v ON v.StoreVisitId=pd.StoreVisitId
      JOIN dbo.Dealer d ON d.DealerId=v.DealerId
      JOIN dbo.Product p ON p.ProductId=pd.ProductId
      LEFT JOIN dbo.DealerAssignmentHistory a ON a.DealerAssignmentId=v.DealerAssignmentId
      LEFT JOIN dbo.Employee owner ON owner.EmployeeId=a.EmployeeId
      JOIN dbo.UserAccount ua ON ua.UserAccountId=v.CreatedByUserAccountId
      LEFT JOIN dbo.Employee writerE ON writerE.EmployeeId=ua.EmployeeId
      LEFT JOIN dbo.Dealer writerD ON writerD.DealerId=ua.DealerId
     ORDER BY v.ReportDateTime DESC,v.StoreVisitId DESC,p.ProductCode
    """
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql,(limit,));rows=cur.fetchall()
    return [{"visitId":int(r[0]),"code":f"RPT-{r[1]:%y%m%d}-{int(r[0]):03d}","reportDateTime":r[1].isoformat(timespec="minutes"),
             "dealer":r[2],"entrySourceType":r[3],"responsibleEmployee":r[4] or "未指派","createdBy":r[5] or "—",
             "productCode":r[6],"productName":r[7],"sellOutQuantity":r[8],"sellOutDate":r[9].isoformat() if r[9] else None,
             "displayQuantity":r[10],"recordStatus":r[11],"editableUntil":r[12].isoformat(timespec="minutes")} for r in rows]


def update_task_photos(task_id:int,execution_id:int,photos:list[dict[str,Any]],*,set_sample:bool,employee_id:int) -> None:
    conn=connect()
    try:
        cur=conn.cursor();belongs=_one(cur,"SELECT 1 FROM dbo.VisitTaskExecution WHERE VisitTaskId=%s AND TaskExecutionId=%s",(task_id,execution_id))
        if belongs is None:raise LookupError("找不到指定的任務回報")
        known=[]
        cur.execute("SELECT TaskPhotoId FROM dbo.VisitTaskPhoto WHERE TaskExecutionId=%s",(execution_id,));known=[int(r[0]) for r in cur.fetchall()]
        if set(int(p['id']) for p in photos) != set(known):raise ValueError("照片清單已變更，請重新載入")
        if set_sample and not known:raise ValueError("沒有照片，不能設定為樣本任務")
        for order,p in enumerate(photos):
            description=str(p.get('description') or '').strip()
            if not description:raise ValueError("所有照片說明必填")
            cur.execute("UPDATE dbo.VisitTaskPhoto SET PhotoDescription=%s,SortOrder=%s WHERE TaskPhotoId=%s AND TaskExecutionId=%s",(description,order,int(p['id']),execution_id))
        if set_sample:
            cur.execute("""UPDATE dbo.VisitTask SET SampleTaskExecutionId=%s,SampleApprovedByEmployeeId=%s,SampleApprovedAt=SYSDATETIME(),UpdatedByEmployeeId=%s,UpdatedAt=SYSDATETIME() WHERE VisitTaskId=%s""",(execution_id,employee_id,employee_id,task_id))
        conn.commit()
    except Exception:conn.rollback();raise
    finally:conn.close()


def create_change(data:dict[str,Any]) -> dict[str,int]:
    """Apply org and/or dealer assignment changes using one effective timestamp."""
    conn=connect()
    try:
        cur=conn.cursor();creator_id=_creator_id(cur);employee_id=int(data['employeeId']);reason=str(data.get('reason') or '').strip()
        if not reason:raise ValueError("異動原因必填")
        effective=_parse_effective(data['effectiveAt'])
        org_changed=0;dealer_changed=0
        if data.get('moveOrg'):
            new_org_id=int(data['newOrgId']);current=_one(cur,"SELECT EmployeeOrgAssignmentId,OrgUnitId,StartDateTime FROM dbo.EmployeeOrgAssignmentHistory WHERE EmployeeId=%s AND EndDateTime IS NULL",(employee_id,))
            if current is None:raise ValueError("找不到員工目前有效的處所歷程")
            if int(current[1]) != new_org_id:
                if effective <= current[2]:raise ValueError("生效時間必須晚於目前處所歷程的開始時間")
                cur.execute("UPDATE dbo.EmployeeOrgAssignmentHistory SET EndDateTime=%s WHERE EmployeeOrgAssignmentId=%s",(effective,current[0]))
                cur.execute("INSERT dbo.EmployeeOrgAssignmentHistory(EmployeeId,OrgUnitId,StartDateTime,ChangeReason,CreatedByEmployeeId) VALUES(%s,%s,%s,%s,%s)",(employee_id,new_org_id,effective,reason,creator_id));org_changed=1
                cur.execute("""UPDATE r SET FromOrgUnitId=%s,ToOrgUnitId=%s,TriggeredAt=%s
                                  FROM dbo.DealerTransferReview r
                                  JOIN dbo.DealerAssignmentHistory a ON a.DealerId=r.DealerId AND a.EndDateTime IS NULL
                                 WHERE r.ReviewStatus='OPEN' AND r.TriggerType='ORG_MOVE' AND a.EmployeeId=%s""",
                            (current[1],new_org_id,effective,employee_id))
                cur.execute("""INSERT dbo.DealerTransferReview(DealerId,SourceDealerAssignmentId,SourceEmployeeId,TriggerType,FromOrgUnitId,ToOrgUnitId,TriggeredAt)
                               SELECT a.DealerId,a.DealerAssignmentId,a.EmployeeId,'ORG_MOVE',%s,%s,%s
                                 FROM dbo.DealerAssignmentHistory a
                                WHERE a.EmployeeId=%s AND a.EndDateTime IS NULL
                                  AND NOT EXISTS(SELECT 1 FROM dbo.DealerTransferReview r WHERE r.DealerId=a.DealerId AND r.ReviewStatus='OPEN')""",(current[1],new_org_id,effective,employee_id))
        if data.get('moveDealers'):
            receiver_id=int(data['receiverEmployeeId']);dealer_ids=[int(x) for x in data.get('dealerIds') or []]
            for dealer_id in dealer_ids:
                current=_one(cur,"SELECT DealerAssignmentId,EmployeeId,StartDateTime FROM dbo.DealerAssignmentHistory WHERE DealerId=%s AND EndDateTime IS NULL",(dealer_id,))
                if current is not None and int(current[1]) != employee_id:raise ValueError(f"經銷商 {dealer_id} 的目前負責人已變更，請重新載入")
                if current is not None and int(current[1]) == receiver_id:
                    continue
                if current is not None:
                    if effective <= current[2]:raise ValueError(f"經銷商 {dealer_id} 的生效時間必須晚於目前負責歷程的開始時間")
                    cur.execute("UPDATE dbo.DealerAssignmentHistory SET EndDateTime=%s WHERE DealerAssignmentId=%s",(effective,current[0]))
                cur.execute("INSERT dbo.DealerAssignmentHistory(DealerId,EmployeeId,StartDateTime,ChangeReason,CreatedByEmployeeId) VALUES(%s,%s,%s,%s,%s)",(dealer_id,receiver_id,effective,reason,creator_id));dealer_changed+=1
        conn.commit();return {'orgChanged':org_changed,'dealerChanged':dealer_changed}
    except Exception:conn.rollback();raise
    finally:conn.close()


def dealer_transfer_candidates() -> list[dict[str,Any]]:
    sql="""
    SELECT d.DealerId,d.DealerCode,d.DealerName,d.Area,
           a.DealerAssignmentId,a.EmployeeId,owner.EmployeeName,owner.EmployeeNo,owner.TerminationDate,
           r.DealerTransferReviewId,r.TriggerType,r.SourceEmployeeId,source.EmployeeName,
           fromOrg.OrgUnitName,toOrg.OrgUnitName,r.TriggeredAt,
           lastOwner.EmployeeId,lastEmployee.EmployeeName
      FROM dbo.Dealer d
      LEFT JOIN dbo.DealerAssignmentHistory a ON a.DealerId=d.DealerId AND a.EndDateTime IS NULL
      LEFT JOIN dbo.Employee owner ON owner.EmployeeId=a.EmployeeId
      LEFT JOIN dbo.DealerTransferReview r ON r.DealerId=d.DealerId AND r.ReviewStatus='OPEN'
      LEFT JOIN dbo.Employee source ON source.EmployeeId=r.SourceEmployeeId
      LEFT JOIN dbo.OrganizationUnit fromOrg ON fromOrg.OrgUnitId=r.FromOrgUnitId
      LEFT JOIN dbo.OrganizationUnit toOrg ON toOrg.OrgUnitId=r.ToOrgUnitId
      OUTER APPLY(SELECT TOP 1 h.EmployeeId FROM dbo.DealerAssignmentHistory h WHERE h.DealerId=d.DealerId ORDER BY h.StartDateTime DESC,h.DealerAssignmentId DESC) lastOwner
      LEFT JOIN dbo.Employee lastEmployee ON lastEmployee.EmployeeId=lastOwner.EmployeeId
     ORDER BY CASE WHEN r.DealerTransferReviewId IS NOT NULL OR a.DealerAssignmentId IS NULL OR owner.TerminationDate IS NOT NULL THEN 0 ELSE 1 END,d.DealerId
    """
    with connect() as conn:
        cur=conn.cursor();cur.execute(sql);rows=cur.fetchall()
        cur.execute("""SELECT h.DealerId,e.EmployeeId,e.EmployeeNo,e.EmployeeName,
                              h.StartDateTime,h.EndDateTime,h.ChangeReason
                         FROM dbo.DealerAssignmentHistory h
                         JOIN dbo.Employee e ON e.EmployeeId=h.EmployeeId
                        ORDER BY h.DealerId,h.StartDateTime DESC,h.DealerAssignmentId DESC""")
        history_rows=cur.fetchall()
    histories:dict[int,list[dict[str,Any]]]={}
    for h in history_rows:
        histories.setdefault(int(h[0]),[]).append({
            "employeeId":int(h[1]),"employeeNo":h[2],"employee":h[3],
            "start":h[4].isoformat(sep=" ",timespec="minutes"),
            "end":h[5].isoformat(sep=" ",timespec="minutes") if h[5] else None,
            "reason":h[6] or "—",
        })
    result=[]
    for x in rows:
        trigger=x[10] or ("UNASSIGNED" if x[4] is None else "TERMINATED" if x[8] is not None else "NONE")
        needs_attention=trigger!="NONE"
        result.append({"id":int(x[0]),"code":x[1],"name":x[2],"area":x[3] or "—",
                       "currentAssignmentId":int(x[4]) if x[4] else None,"currentEmployeeId":int(x[5]) if x[5] else None,
                       "currentEmployee":x[6] or "未指派","currentEmployeeNo":x[7],"currentEmployeeTerminated":x[8].isoformat() if x[8] else None,
                       "reviewId":int(x[9]) if x[9] else None,"triggerType":trigger,
                       "sourceEmployeeId":int(x[11]) if x[11] else (int(x[16]) if x[16] else None),
                       "sourceEmployee":x[12] or x[17] or x[6] or "—","fromOrg":x[13],"toOrg":x[14],
                       "triggeredAt":x[15].isoformat(timespec="minutes") if x[15] else None,"needsAttention":needs_attention,
                       "assignmentHistory":histories.get(int(x[0]),[])})
    return result


def transfer_dealers(data:dict[str,Any]) -> int:
    dealer_ids=sorted({int(x) for x in data.get('dealerIds') or []})
    if not dealer_ids:raise ValueError("請至少選擇一家經銷商")
    receiver_id=int(data['receiverEmployeeId']);effective=_parse_effective(data['effectiveAt']);reason=str(data.get('reason') or '').strip()
    if not reason:raise ValueError("轉移原因必填")
    conn=connect()
    try:
        cur=conn.cursor();creator_id=_creator_id(cur);receiver=_one(cur,"SELECT 1 FROM dbo.Employee WHERE EmployeeId=%s AND TerminationDate IS NULL",(receiver_id,))
        if receiver is None:raise ValueError("新負責員工不存在或已離職")
        changed=0
        for dealer_id in dealer_ids:
            current=_one(cur,"SELECT DealerAssignmentId,EmployeeId,StartDateTime FROM dbo.DealerAssignmentHistory WHERE DealerId=%s AND EndDateTime IS NULL",(dealer_id,))
            if current and int(current[1])==receiver_id:
                raise ValueError(f"經銷商 {dealer_id} 已由所選員工負責")
            if current:
                if effective<=current[2]:raise ValueError(f"經銷商 {dealer_id} 的生效時間必須晚於目前負責歷程")
                cur.execute("UPDATE dbo.DealerAssignmentHistory SET EndDateTime=%s WHERE DealerAssignmentId=%s",(effective,current[0]))
            cur.execute("INSERT dbo.DealerAssignmentHistory(DealerId,EmployeeId,StartDateTime,ChangeReason,CreatedByEmployeeId) VALUES(%s,%s,%s,%s,%s)",(dealer_id,receiver_id,effective,reason,creator_id))
            cur.execute("""UPDATE dbo.DealerTransferReview SET ReviewStatus='TRANSFERRED',ResolvedEmployeeId=%s,ResolvedAt=SYSDATETIME(),ResolvedByEmployeeId=%s,ResolutionNote=%s WHERE DealerId=%s AND ReviewStatus='OPEN'""",(receiver_id,creator_id,reason,dealer_id));changed+=1
        conn.commit();return changed
    except Exception:conn.rollback();raise
    finally:conn.close()


def retain_dealers(data:dict[str,Any]) -> int:
    dealer_ids=sorted({int(x) for x in data.get('dealerIds') or []});reason=str(data.get('reason') or '').strip()
    if not dealer_ids:raise ValueError("請至少選擇一家經銷商")
    if not reason:raise ValueError("保留原因必填")
    conn=connect()
    try:
        cur=conn.cursor();creator_id=_creator_id(cur);changed=0
        for dealer_id in dealer_ids:
            cur.execute("""UPDATE r SET ReviewStatus='RETAINED',ResolvedEmployeeId=r.SourceEmployeeId,ResolvedAt=SYSDATETIME(),ResolvedByEmployeeId=%s,ResolutionNote=%s
                              FROM dbo.DealerTransferReview r
                             WHERE r.DealerId=%s AND r.TriggerType='ORG_MOVE' AND r.ReviewStatus='OPEN'
                               AND EXISTS(SELECT 1 FROM dbo.DealerAssignmentHistory a WHERE a.DealerId=r.DealerId AND a.EmployeeId=r.SourceEmployeeId AND a.EndDateTime IS NULL)""",(creator_id,reason,dealer_id));changed+=max(0,cur.rowcount)
        if changed!=len(dealer_ids):raise ValueError("只有處所異動產生、且仍由原業務負責的待確認項目可以保留")
        conn.commit();return changed
    except Exception:conn.rollback();raise
    finally:conn.close()
