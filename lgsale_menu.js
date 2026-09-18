"use strict";
// Standalone PSI/import pages share the same permission-derived navigation.
(async function () {
  const nav = document.querySelector("aside.side nav");
  if (!nav) return;
  const style = document.createElement("style");
  style.textContent = `
    .side{box-sizing:border-box;padding:24px 12px;display:flex;flex-direction:column}
    .side .brand{padding:0 14px 28px;font:700 22px/1.5 "Segoe UI","Noto Sans TC",sans-serif}
    .side .brand small{display:block;color:#a9c0d4;font:400 12px/1.5 "Segoe UI","Noto Sans TC",sans-serif}
    .side nav{display:grid;gap:5px;overflow-y:auto;align-content:start;min-height:0;scrollbar-width:none}
    .side nav::-webkit-scrollbar{display:none}
    .side nav a{box-sizing:border-box;display:block;margin:0;padding:11px 16px;border-radius:8px;color:#c8d6e3;text-decoration:none;font:400 14px/1.5 "Segoe UI","Noto Sans TC",sans-serif}
    .side nav a.active,.side nav a:hover{background:#27577d;color:#fff}
    .side nav .nav-heading{margin:15px 0 5px;padding:8px 12px;background:#284760;border-left:3px solid #79cbee;border-radius:5px;color:#f5fbff;font:700 13px/1.5 "Segoe UI","Noto Sans TC",sans-serif;letter-spacing:.03em}
    .side nav .nav-heading:first-child{margin-top:0}
    @media(max-width:650px){.side nav .nav-heading{white-space:nowrap;margin:0 5px 0 0;flex:none}}
  `;
  document.head.append(style);
  try {
    const response = await fetch("/api/auth/me", {cache: "no-store"});
    if (!response.ok) return;
    const user = await response.json();
    const allowed = new Set(user.capabilities || []);
    const entries = [
      ["工作資料", "巡店任務", "/", "tasks.view"],
      ["工作資料", "實銷與陳列", "/?view=reports", "reports.view"],
      ["工作資料", "PSI 月報", "/psi", "psi.view"],
      ["主檔與異動", "員工與處所", "/?view=employees", "employees.view"],
      ["主檔與異動", "經銷商", "/?view=dealerMaster", "dealers.view"],
      ["主檔與異動", "人員與經銷商異動", "/?view=assignment", "assignments.view"],
      ["匯入與帳號", "期初庫存匯入", "/opening-import", "opening.manage"],
      ["匯入與帳號", "SaleIn 匯入", "/sellin-import", "sellin.manage"],
      ["匯入與帳號", "Passkey 帳號", "/?view=passkeys", "passkeys.manage"],
      ["其他", "手機巡店介面", "/mobile", "mobile.reports.view"],
      ["其他", "手機任務介面", "/photo", "mobile.tasks.view"],
    ];
    if (user.designer) {
      entries.push(["Designer 專用", "權限與 Menu", "/permissions", null]);
      entries.push(["Designer 專用", "初始化主檔匯入", "/initial-import", null]);
    }
    let group = "";
    nav.replaceChildren();
    for (const [section, label, href, capability] of entries) {
      if (capability && !allowed.has(capability)) continue;
      if (section !== group) {
        group = section;
        const heading = document.createElement("div");
        heading.textContent = section;
        heading.className = "nav-heading";
        nav.append(heading);
      }
      const link = document.createElement("a");
      link.href = href;
      link.textContent = label;
      if (location.pathname === href) link.className = "active";
      nav.append(link);
    }
    const profile = document.querySelector("aside.side .profile");
    if (profile) profile.textContent = `${user.name}｜${user.roleName}｜Passkey 已登入`;
    const exportButton = document.querySelector("#export");
    if (exportButton && !allowed.has("psi.export")) {
      exportButton.hidden = true;
      const photoChoice = document.querySelector("#exportPhotos");
      if (photoChoice) photoChoice.hidden = true;
    }
    if (user.baseRole === "DEALER") {
      for (const id of ("org", "employee")) {
        const field = document.getElementById(id);
        if (field) field.hidden = true;
      }
    }
  } catch (_) {
    // The page's own API request will show its usual error state.
  }
})();
