"""Server-side capabilities and data scopes for LGSale.

PositionLevel supplies defaults. SQL overrides may change one role or one
account. Designer is a separate account designation that includes ADMIN access.
"""

from __future__ import annotations

from dataclasses import dataclass

import lgsale_db as db


CAPABILITIES = {
    "tasks.view": "查看巡店任務與照片",
    "tasks.create": "建立巡店任務",
    "tasks.toggle": "暫停或恢復任務",
    "tasks.photos.manage": "修改照片說明與設定樣本",
    "psi.view": "查看 PSI 月報",
    "psi.export": "匯出 PSI Excel",
    "reports.view": "查看實銷與陳列回報",
    "mobile.tasks.view": "手機查看任務",
    "mobile.tasks.execute": "手機執行任務與上傳照片",
    "mobile.reports.view": "手機查看實銷與陳列",
    "reports.create": "新增實銷與陳列回報",
    "reports.edit": "修改實銷與陳列回報",
    "employees.view": "查看員工與處所",
    "employees.manage": "維護員工與處所",
    "dealers.view": "查看經銷商主檔",
    "dealers.manage": "維護經銷商主檔",
    "assignments.view": "查看人員與經銷商異動",
    "assignments.manage": "處理人員與經銷商異動",
    "opening.manage": "期初庫存匯入",
    "sellin.manage": "SaleIn 匯入",
    "passkeys.manage": "管理 Passkey 帳號",
}

ROLE_NAMES = {
    "SALES": "業務", "DIRECTOR": "處長", "MANAGER": "經理",
    "ADMIN": "管理", "DEALER": "經銷商",
}

ROLE_DEFAULTS = {
    "SALES": {
        "tasks.view", "psi.view", "psi.export", "mobile.tasks.view",
        "mobile.tasks.execute", "mobile.reports.view", "reports.create", "reports.edit",
    },
    "DIRECTOR": {
        "tasks.view", "psi.view", "psi.export", "mobile.tasks.view",
        "mobile.reports.view",
    },
    "MANAGER": {"tasks.view", "psi.view", "psi.export"},
    "ADMIN": set(CAPABILITIES) - {"mobile.tasks.execute", "reports.create", "reports.edit"},
    "DEALER": {
        "psi.view", "psi.export", "mobile.reports.view",
    },
}

# Every operation also requires access to its enclosing read surface.
DEPENDENCIES = {
    "tasks.create": "tasks.view", "tasks.toggle": "tasks.view",
    "tasks.photos.manage": "tasks.view", "psi.export": "psi.view",
    "mobile.tasks.execute": "mobile.tasks.view", "reports.create": "mobile.reports.view",
    "reports.edit": "mobile.reports.view", "employees.manage": "employees.view",
    "dealers.manage": "dealers.view", "assignments.manage": "assignments.view",
}


@dataclass(frozen=True)
class Access:
    account_id: int
    account_type: str
    employee_id: int | None
    dealer_id: int | None
    role: str
    org_id: int | None
    designer: bool
    capabilities: frozenset[str]
    dealer_ids: frozenset[int]

    def can(self, capability: str) -> bool:
        return capability == "permissions.manage" and self.designer or capability in self.capabilities

    def has_dealer(self, dealer_id: int) -> bool:
        return dealer_id in self.dealer_ids

    def as_public(self) -> dict:
        return {
            "role": "DESIGNER" if self.designer else self.role,
            "baseRole": self.role, "roleName": "Designer" if self.designer else ROLE_NAMES[self.role],
            "designer": self.designer, "capabilities": sorted(self.capabilities),
            "scope": "ALL" if self.designer else
                     "DEALER" if self.account_type == "DEALER" else
                     "OWN" if self.role == "SALES" else
                     "ORG" if self.role == "DIRECTOR" else "ALL",
        }


def effective_capabilities(role: str, role_rules: dict[str, bool],
                           account_rules: dict[str, bool]) -> frozenset[str]:
    granted = set(ROLE_DEFAULTS.get(role, ()))
    for rules in (role_rules, account_rules):
        for key, allowed in rules.items():
            if key in CAPABILITIES:
                if allowed:
                    granted.add(key)
                else:
                    granted.discard(key)
    # A denied read surface cannot be bypassed by a write override.
    for key, prerequisite in DEPENDENCIES.items():
        if prerequisite not in granted:
            granted.discard(key)
    return frozenset(granted)


def resolve(user: dict) -> Access:
    principal = db.permission_principal(int(user["id"]))
    if principal is None or principal["accountType"] != user["type"]:
        raise PermissionError("登入帳號資料已變更，請重新登入")
    if principal["designer"] and user["type"] != "EMPLOYEE":
        raise PermissionError("Designer 必須是員工帳號")
    role = "DEALER" if user["type"] == "DEALER" else principal["position"]
    if role not in ROLE_DEFAULTS:
        raise PermissionError("尚未設定有效職級，請聯絡管理人員")
    role_rules, account_rules = db.permission_rules(role, int(user["id"]))
    capabilities = effective_capabilities(role, role_rules, account_rules)
    if principal["designer"]:
        admin_rules = role_rules if role == "ADMIN" else db.permission_rules("ADMIN", int(user["id"]))[0]
        capabilities |= effective_capabilities("ADMIN", admin_rules, {})
        # The visit records the signed-in Designer as author while retaining
        # the dealer's assigned employee as the responsible sales owner.
        capabilities |= {"mobile.reports.view", "reports.create"}
    dealer_ids = db.permission_dealer_ids(
        "ADMIN" if principal["designer"] else role,
        principal["employeeId"], principal["dealerId"], principal["orgId"]
    )
    return Access(
        account_id=int(user["id"]), account_type=user["type"],
        employee_id=principal["employeeId"], dealer_id=principal["dealerId"],
        role=role, org_id=principal["orgId"], designer=principal["designer"],
        capabilities=capabilities,
        dealer_ids=frozenset(dealer_ids),
    )
