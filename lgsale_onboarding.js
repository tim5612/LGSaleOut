(() => {
  const isMobile = /iPhone|iPad|Android/i.test(navigator.userAgent);
  const style = document.createElement("style");
  style.textContent = `
    .lg-help{position:fixed;right:18px;bottom:82px;z-index:80;border:1px solid #1769aa;background:#fff;color:#1769aa;border-radius:999px;padding:10px 14px;font:600 13px/1.2 "Segoe UI","Noto Sans TC",sans-serif;box-shadow:0 7px 24px #17324d24}
    .lg-guide-backdrop{position:fixed;inset:0;z-index:1000;background:#10283caa;display:grid;place-items:center;padding:18px;font:15px/1.6 "Segoe UI","Noto Sans TC",sans-serif;color:#172b3a}
    .lg-guide{width:min(440px,100%);background:#fff;border-radius:18px;padding:28px;box-shadow:0 24px 70px #0005}
    .lg-guide-top{display:flex;justify-content:space-between;align-items:center;color:#667085;font-size:13px}.lg-guide-skip{border:0;background:none;color:#1769aa;font:inherit;font-weight:700}
    .lg-guide-icon{width:72px;height:72px;margin:24px auto 18px;border-radius:50%;display:grid;place-items:center;background:#eaf4fb;color:#1769aa;font-size:30px;font-weight:800}
    .lg-guide h2{text-align:center;margin:0 0 10px;font-size:24px}.lg-guide-copy{min-height:145px;color:#475467}.lg-guide-copy p{margin:7px 0}.lg-guide-copy ul{padding-left:22px}
    .lg-guide-links{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}.lg-guide-links button{border:1px solid #7aaed3;border-radius:9px;padding:11px 8px;background:#f3f8fc;color:#155b8f;font-weight:700}.lg-guide-links button.copied{border-color:#18864b;background:#edf9f2;color:#126b3c}
    .lg-guide-actions{display:grid;grid-template-columns:1fr 1.7fr;gap:10px;margin-top:20px}.lg-guide-actions button{border:1px solid #1769aa;border-radius:9px;padding:12px;background:#fff;color:#1769aa;font-weight:700}.lg-guide-actions .primary{background:#1769aa;color:#fff}
    .lg-guide-dots{text-align:center;color:#98a2b3;letter-spacing:5px;margin-top:16px}.lg-guide-dots b{color:#1769aa}
  `;
  document.head.appendChild(style);

  const mobileSales = [
    ["手機可以做什麼？", "⌂", "<p>這支手機可以用來：</p><ul><li>查看待辦任務</li><li>執行巡店</li><li>填寫實銷與陳列</li><li>拍照並送出回報</li></ul>"],
    ["從今天的任務開始", "✓", "<p>開啟「任務」，選擇今天要拜訪的經銷商，再查看需要完成的項目。</p>"],
    ["完成一次巡店", "◎", "<p>依序填寫資料、拍攝任務照片，送出前再確認一次內容。</p><p>送出後可從紀錄查看結果。</p>"],
    ["電腦版可以做什麼？", "▤", "<p>在電腦版可以查看屬於自己的 PSI，以及其他已授權功能。</p><p>手機與電腦使用同一把 Passkey。</p>"],
    ["如何登入電腦？", "⌘", "<p>在電腦開啟 LGSale 員工登入頁，點「使用 iPhone 掃碼授權桌機」。</p><p>再用手機掃描 QR Code，並以 Face ID／Passkey 確認，電腦就會自動登入。</p>"]
  ];
  const desktopEmployee = [
    ["歡迎使用 LGSale 電腦版", "▤", "<p>電腦版會依照你的權限顯示功能。業務可在這裡查看屬於自己的 PSI。</p>"],
    ["手機負責巡店作業", "⌂", "<p>待辦任務、巡店、實銷與陳列回報，請使用手機版操作。</p>"],
    ["下次可用手機授權", "⌘", "<p>在登入頁點「使用 iPhone 掃碼授權桌機」，再用手機掃描 QR Code 並確認，不需要把一次性註冊網址傳到電腦。</p>"]
  ];

  const loginUrl = destination => {
    const url = new URL("/login/employee", location.origin);
    url.searchParams.set("next", destination);
    return url.href;
  };

  async function copyUrl(button, destination, label) {
    const url = loginUrl(destination);
    try {
      await navigator.clipboard.writeText(url);
      const original = button.textContent;
      button.textContent = `${label}已複製`;
      button.classList.add("copied");
      window.setTimeout(() => {
        button.textContent = original;
        button.classList.remove("copied");
      }, 2200);
    } catch {
      window.prompt(`請複製${label}`, url);
    }
  }

  function showGuide(cards, storageKey, start = 0) {
    let index = start;
    const backdrop = document.createElement("div");
    backdrop.className = "lg-guide-backdrop";
    backdrop.innerHTML = `<section class="lg-guide" role="dialog" aria-modal="true"><div class="lg-guide-top"><span class="lg-guide-count"></span><button class="lg-guide-skip">略過</button></div><div class="lg-guide-icon"></div><h2></h2><div class="lg-guide-copy"></div><div class="lg-guide-links"><button class="lg-copy-mobile">複製手機版連結</button><button class="lg-copy-desktop">複製電腦版連結</button></div><div class="lg-guide-actions"><button class="lg-guide-prev">上一步</button><button class="lg-guide-next primary">下一步</button></div><div class="lg-guide-dots"></div></section>`;
    document.body.appendChild(backdrop);
    const finish = () => { localStorage.setItem(storageKey, "1"); backdrop.remove(); };
    const render = () => {
      const card = cards[index];
      backdrop.querySelector("h2").textContent = card[0];
      backdrop.querySelector(".lg-guide-icon").textContent = card[1];
      backdrop.querySelector(".lg-guide-copy").innerHTML = card[2];
      backdrop.querySelector(".lg-guide-count").textContent = `使用說明 ${index + 1}／${cards.length}`;
      backdrop.querySelector(".lg-guide-prev").disabled = index === 0;
      backdrop.querySelector(".lg-guide-next").textContent = index === cards.length - 1 ? "開始使用" : "下一步";
      backdrop.querySelector(".lg-guide-dots").innerHTML = cards.map((_, i) => i === index ? "<b>●</b>" : "○").join(" ");
    };
    backdrop.querySelector(".lg-guide-skip").onclick = finish;
    backdrop.querySelector(".lg-copy-mobile").onclick = event => copyUrl(event.currentTarget, "/mobile", "手機版連結");
    backdrop.querySelector(".lg-copy-desktop").onclick = event => copyUrl(event.currentTarget, "/", "電腦版連結");
    backdrop.querySelector(".lg-guide-prev").onclick = () => { if (index) { index--; render(); } };
    backdrop.querySelector(".lg-guide-next").onclick = () => { if (index === cards.length - 1) finish(); else { index++; render(); } };
    render();
  }

  fetch("/api/auth/me").then(r => r.ok ? r.json() : null).then(me => {
    if (!me || me.type !== "EMPLOYEE") return;
    const caps = new Set(me.capabilities || []);
    const hasMobileWork = caps.has("mobile.tasks.view") || caps.has("mobile.reports.view");
    const cards = isMobile && hasMobileWork ? mobileSales : !isMobile ? desktopEmployee : null;
    if (!cards) return;
    const mode = isMobile ? "mobile" : "desktop";
    const key = `lgsale-guide-v2-${me.id}-${mode}`;
    const help = document.createElement("button");
    help.className = "lg-help";
    help.textContent = "？ 使用說明";
    help.onclick = () => showGuide(cards, key);
    document.body.appendChild(help);
    if (!localStorage.getItem(key)) showGuide(cards, key);
  }).catch(() => {});
})();
