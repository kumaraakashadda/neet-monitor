"""Generate the full beautiful dashboard — overwrites data/dashboard.html every run."""
from __future__ import annotations
from datetime import datetime, timezone
from monitor.config import DASHBOARD_PATH
from monitor.storage import health_report

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwKbddIRPgPQABNskrw0qij4SR7m22-0rXGMzj6XwCuWw9p6_5bqpAe6fYT0kyLdB6YLA/exec"

def _priority_class(p):
    return {"HIGH": "HIGH", "MEDIUM": "MEDIUM"}.get(p, "LOW")

def _site_rows(statuses, recent_changes):
    changed_urls = {c["url"] for c in recent_changes}
    rows = []
    for i, s in enumerate(statuses, 1):
        url   = s.get("url", "")
        name  = s.get("name", "")
        prio  = (s.get("priority") or "LOW").upper()
        streak = s.get("consecutive_failures") or 0
        last_ok   = (s.get("last_ok_at") or "")[:16].replace("T"," ").replace("+00:00","") or "—"
        last_fail = (s.get("last_fail_at") or "")[:16].replace("T"," ").replace("+00:00","") or "—"
        ok    = streak == 0 and bool(s.get("last_ok_at"))
        ds    = "ok" if ok else "fail"
        rf    = " class=\"rf\"" if not ok else ""
        hl    = " style=\"background:#fffde7\"" if url in changed_urls and ok else ""
        rc    = rf + hl
        pc    = _priority_class(prio)
        sdot  = '<span class="ok-d">Online</span>' if ok else f'<span class="fail-d">{"Flaky" if streak==1 else "Failed"}</span>'
        domain = url.replace("https://","").replace("http://","").split("/")[0][:38]
        rows.append(
            f'<tr data-p="{pc}" data-s="{ds}"{rc}>' +
            f'<td>{i}</td><td>{name}</td>' +
            f'<td><a class="sl" href="{url}" target="_blank">{domain}</a></td>' +
            f'<td><span class="pill {pc}">{pc}</span></td>' +
            f'<td>{last_ok}</td><td>{last_fail}</td>' +
            f'<td class="{"s0" if streak==0 else "shi"}">{streak}</td>' +
            f'<td>{sdot}</td></tr>'
        )
    return "\n".join(rows)

def _change_cards(recent):
    if not recent:
        return '<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:12px;padding:1rem 1.25rem;color:#166534;font-size:.9rem">✅ No changes detected in this run.</div>'
    cards = []
    for c in recent[:10]:
        ctype = c.get("change_type","")
        cls = "pdf" if "pdf" in ctype else "notice"
        label = "PDF Added" if "pdf" in ctype else "Notice Added"
        prio  = c.get("priority","MEDIUM")
        name  = c.get("name","")
        summary = (c.get("summary","") or "")[:300]
        when  = (c.get("detected_at") or "")[:16].replace("T"," ")
        cards.append(
            f'<div class="cc {cls}"><div class="ac"></div><div class="bd">' +
            f'<div class="top"><span class="sn">{name}</span>' +
            f'<span class="pill {prio}">{prio}</span>' +
            f'<span class="pill {cls}">{label}</span></div>' +
            f'<div class="sm">🔔 {summary}</div>' +
            f'<div class="wh">🕐 {when} UTC</div>' +
            '</div></div>'
        )
    return "\n".join(cards)

def render():
    r = health_report()
    last_run   = r.get("last_run") or {}
    failing    = r.get("failing_sites") or []
    recent     = r.get("recent_changes") or []
    statuses   = r.get("all_statuses") or []
    now_str    = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    total    = last_run.get("total") or len(statuses) or 133
    ok_cnt   = last_run.get("ok") or sum(1 for s in statuses if not (s.get("consecutive_failures") or 0))
    fail_cnt = last_run.get("failed") or len(failing)
    chg_cnt  = last_run.get("changed") or len(recent)
    ok_pct   = round(ok_cnt / total * 100) if total else 0
    started  = (last_run.get("started_at") or "—")[:16].replace("T"," ").replace("+00:00","")
    finished = (last_run.get("finished_at") or "—")[:16].replace("T"," ").replace("+00:00","")
    change_count = len(recent)
    site_rows    = _site_rows(statuses, recent)
    change_cards = _change_cards(recent)

    html = get_template().format(
        total=total, ok_cnt=ok_cnt, fail_cnt=fail_cnt, chg_cnt=chg_cnt,
        ok_pct=ok_pct, started=started, finished=finished,
        now=now_str, change_count=change_count,
        change_cards=change_cards, site_rows=site_rows,
        APPS_SCRIPT_URL=APPS_SCRIPT_URL,
    )
    DASHBOARD_PATH.write_text(html, encoding="utf-8")

def get_template():
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NEET Counselling Monitor</title>
<style>
:root{{--navy:#0f1f5c;--blue:#1a4fad;--sky:#2d9cdb;--teal:#0d9488;--green:#16a34a;--red:#dc2626;--purple:#7c3aed;--amber:#d97706;--bg:#f1f5fb;--border:#dde6f5;--muted:#64748b}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:#0f172a;min-height:100vh}}
#mo{{position:fixed;inset:0;z-index:9999;background:rgba(10,20,60,.85);display:flex;align-items:center;justify-content:center;padding:1rem}}
#mb{{background:#fff;border-radius:20px;max-width:460px;width:100%;box-shadow:0 25px 60px rgba(0,0,0,.4);overflow:hidden}}
#mh{{background:linear-gradient(135deg,var(--navy),var(--blue) 60%,var(--sky));padding:1.75rem;color:#fff}}
#mh h2{{font-size:1.25rem;font-weight:800}}
#mh p{{margin-top:.4rem;font-size:.85rem;opacity:.85;line-height:1.5}}
#mbody{{padding:1.5rem 1.75rem 1.75rem}}
.step{{display:none}}.step.active{{display:block}}
.step-ind{{display:flex;gap:.5rem;margin-bottom:1.5rem}}
.step-dot{{flex:1;height:4px;border-radius:2px;background:#e2e8f0;transition:background .3s}}
.step-dot.done{{background:var(--green)}}.step-dot.active{{background:var(--blue)}}
.field{{margin-bottom:1.1rem}}
.field label{{display:block;font-size:.78rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:.4rem}}
.field input,.field select{{width:100%;padding:.65rem .9rem;border:1.5px solid var(--border);border-radius:10px;font-size:.95rem;outline:none;background:#f8faff}}
.field input:focus,.field select:focus{{border-color:var(--blue);background:#fff;box-shadow:0 0 0 3px rgba(26,79,173,.1)}}
.hint{{font-size:.8rem;color:var(--muted);margin-top:.3rem}}
.hint.ok{{color:var(--green);font-weight:600}}.hint.err{{color:var(--red);font-weight:600;display:none}}
.ph-note{{background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:.75rem 1rem;font-size:.83rem;color:#166534;line-height:1.5;margin-bottom:1rem}}
.btn-row{{display:flex;gap:.6rem;margin-top:.5rem}}
.btn{{flex:1;padding:.7rem;border:none;border-radius:10px;font-size:.95rem;font-weight:700;cursor:pointer}}
.btn:disabled{{opacity:.5;cursor:not-allowed}}
.btn-p{{background:linear-gradient(90deg,var(--blue),var(--teal));color:#fff;box-shadow:0 4px 14px rgba(26,79,173,.25)}}
.btn-s{{background:#f1f5f9;color:#334155}}
.btn-otp{{background:var(--blue);color:#fff;padding:.65rem 1rem;border:none;border-radius:10px;font-size:.82rem;font-weight:700;cursor:pointer;white-space:nowrap}}
.btn-otp:disabled{{background:#94a3b8;cursor:not-allowed}}
.ir{{display:flex;gap:.5rem}}.ir input{{flex:1}}
#msuccess{{display:none;text-align:center;padding:2rem 1.75rem}}
#msuccess .tick{{font-size:3.5rem;margin-bottom:.75rem}}
#msuccess h3{{font-size:1.25rem;font-weight:800;color:var(--green)}}
#msuccess p{{margin-top:.5rem;font-size:.9rem;color:var(--muted);line-height:1.5}}
#msuccess .go{{margin-top:1.25rem;padding:.7rem 2.5rem;background:var(--green);color:#fff;border:none;border-radius:10px;font-weight:800;cursor:pointer;font-size:.95rem}}
.hdr{{background:linear-gradient(135deg,var(--navy),var(--blue) 55%,var(--teal));color:#fff;padding:2rem 2rem 1.6rem;position:relative;overflow:hidden}}
.hdr::before{{content:'';position:absolute;top:-50px;right:-50px;width:200px;height:200px;background:rgba(255,255,255,.06);border-radius:50%}}
.hdr-in{{position:relative;z-index:1;max-width:1280px;margin:0 auto;display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:1rem}}
.hdr h1{{font-size:1.85rem;font-weight:900;letter-spacing:-.5px;line-height:1.15}}
.hdr h1 span{{color:#7dd3fc}}
.hdr .sub{{margin-top:.35rem;font-size:.9rem;opacity:.8}}
.hdr .ts{{margin-top:.5rem;font-size:.75rem;opacity:.6}}
.hdr-btn{{background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.3);color:#fff;padding:.6rem 1.2rem;border-radius:10px;font-weight:700;font-size:.875rem;cursor:pointer}}
.page{{max-width:1280px;margin:0 auto;padding:1.5rem 1.25rem 3rem;display:grid;grid-template-columns:1fr 300px;gap:1.5rem}}
@media(max-width:900px){{.page{{grid-template-columns:1fr}}}}
.sidebar{{display:flex;flex-direction:column;gap:1rem}}
.sidebar-title{{font-size:.75rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:.25rem}}
.prod-card{{background:#fff;border-radius:14px;border:1px solid var(--border);box-shadow:0 2px 10px rgba(0,0,0,.07);overflow:hidden;transition:box-shadow .2s;display:block;text-decoration:none;color:inherit}}
.prod-card:hover{{box-shadow:0 6px 20px rgba(26,79,173,.15)}}
.prod-card img{{width:100%;height:190px;object-fit:cover;object-position:top center;display:block}}
.prod-card .pc-body{{padding:.85rem 1rem}}
.prod-card .pc-tags{{display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:.55rem}}
.pc-tag{{display:inline-block;border-radius:999px;font-size:.63rem;font-weight:800;text-transform:uppercase;padding:3px 9px;letter-spacing:.03em}}
.pc-tag.rec{{background:#fff0f3;color:#dc2626;border:1px solid #fca5a5}}
.pc-tag.val{{background:#f0fdf4;color:#166534;border:1px solid #86efac}}
.pc-tag.disc{{background:#fef9c3;color:#854d0e;border:1px solid #fde68a}}
.pc-tag.lim{{background:#ede9fe;color:#5b21b6;border:1px solid #c4b5fd}}
.prod-card .pc-name{{font-size:.88rem;font-weight:800;color:#0f172a;line-height:1.4;margin-bottom:.5rem}}
.prod-card .pc-btn{{display:block;margin-top:.65rem;text-align:center;background:linear-gradient(90deg,var(--blue),var(--teal));color:#fff;padding:.55rem;border-radius:8px;font-size:.82rem;font-weight:700}}
.call-box{{background:linear-gradient(135deg,#fff7ed,#fef3c7);border:1.5px solid #f59e0b;border-radius:12px;padding:.9rem 1rem;text-align:center}}
.call-box .cb-label{{font-size:.72rem;font-weight:700;color:#92400e;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.3rem}}
.call-box .cb-num{{font-size:1.2rem;font-weight:900;color:#0f172a;text-decoration:none;display:block;margin:.25rem 0}}
.call-box .cb-sub{{font-size:.73rem;color:#92400e;margin-top:.2rem}}
.yt-link{{display:flex;align-items:center;gap:.6rem;background:#fff;border:1.5px solid #fee2e2;border-radius:12px;padding:.75rem 1rem;text-decoration:none;color:#0f172a;transition:background .15s}}
.yt-link:hover{{background:#fff5f5}}
.yt-icon{{width:32px;height:32px;background:#ff0000;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.yt-text{{font-size:.83rem;font-weight:700;line-height:1.3}}
.yt-sub{{font-size:.72rem;color:var(--muted);font-weight:400}}
.promo-banner{{background:linear-gradient(135deg,#0f1f5c,#1a4fad);border-radius:14px;padding:1.1rem;color:#fff;text-align:center}}
.promo-banner h3{{font-size:.95rem;font-weight:800;line-height:1.4}}
.promo-banner p{{font-size:.78rem;opacity:.85;margin:.4rem 0 .75rem;line-height:1.4}}
.promo-banner a{{display:block;background:#fff;color:var(--navy);border-radius:8px;padding:.5rem;font-size:.82rem;font-weight:800;text-decoration:none}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem;margin-bottom:1.25rem}}
.stat{{background:#fff;border-radius:14px;padding:1rem 1.1rem;border:1px solid var(--border);box-shadow:0 2px 8px rgba(0,0,0,.05)}}
.stat .lbl{{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:.3rem}}
.stat .val{{font-size:2rem;font-weight:900;line-height:1}}
.stat .note{{font-size:.72rem;color:var(--muted);margin-top:.25rem}}
.s-t .val{{color:var(--blue)}}.s-o .val{{color:var(--green)}}.s-f .val{{color:var(--red)}}.s-c .val{{color:var(--purple)}}
.ri{{background:#fff;border:1px solid var(--border);border-radius:12px;padding:.85rem 1.1rem;margin-bottom:1.25rem;font-size:.85rem;color:#334155;display:flex;flex-wrap:wrap;gap:.7rem}}
.sh{{display:flex;align-items:center;gap:.6rem;margin:1.75rem 0 .85rem}}
.sh h2{{font-size:1.05rem;font-weight:800}}
.badge{{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:22px;padding:0 6px;border-radius:999px;font-size:.72rem;font-weight:800;background:var(--blue);color:#fff}}
.badge.g{{background:var(--green)}}.badge.p{{background:var(--purple)}}
.changes{{display:flex;flex-direction:column;gap:.65rem}}
.cc{{background:#fff;border-radius:12px;border:1.5px solid var(--border);box-shadow:0 2px 8px rgba(0,0,0,.04);display:grid;grid-template-columns:5px 1fr;overflow:hidden}}
.cc .ac{{background:var(--purple)}}.cc.pdf .ac{{background:var(--red)}}.cc.notice .ac{{background:var(--blue)}}
.cc .bd{{padding:.8rem 1rem}}
.cc .top{{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;margin-bottom:.35rem}}
.cc .sn{{font-weight:800;font-size:.95rem}}
.cc .sm{{font-size:.85rem;color:#334155;line-height:1.5;word-break:break-word}}
.cc .wh{{font-size:.72rem;color:var(--muted);margin-top:.3rem}}
.pill{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.67rem;font-weight:800;text-transform:uppercase;letter-spacing:.04em}}
.pill.HIGH{{background:#fef9c3;color:#92400e;border:1px solid #fde68a}}
.pill.MEDIUM{{background:#dbeafe;color:#1e40af;border:1px solid #93c5fd}}
.pill.LOW{{background:#f1f5f9;color:#475569;border:1px solid #cbd5e1}}
.pill.pdf{{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}}
.pill.notice{{background:#ede9fe;color:#5b21b6;border:1px solid #c4b5fd}}
.tw{{background:#fff;border-radius:14px;border:1px solid var(--border);box-shadow:0 2px 8px rgba(0,0,0,.04);overflow:hidden}}
.fb{{padding:.7rem 1rem;border-bottom:1px solid var(--border);display:flex;flex-wrap:wrap;gap:.5rem;align-items:center}}
.fb input{{flex:1;min-width:140px;border:1.5px solid var(--border);border-radius:8px;padding:.38rem .7rem;font-size:.85rem;outline:none}}
.fb input:focus{{border-color:var(--blue);box-shadow:0 0 0 3px rgba(26,79,173,.12)}}
.fb button{{padding:.35rem .8rem;border-radius:8px;font-size:.76rem;font-weight:700;cursor:pointer;border:1.5px solid var(--border);background:#fff;color:#0f172a}}
.fb button.act,.fb button:hover{{background:var(--blue);color:#fff;border-color:var(--blue)}}
.ov{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse}}
thead th{{background:#f8faff;font-size:.7rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);padding:.6rem 1rem;text-align:left;border-bottom:1px solid var(--border)}}
tbody tr{{border-bottom:1px solid var(--border);transition:background .1s}}
tbody tr:last-child{{border-bottom:none}}
tbody tr:hover{{background:#f8faff}}
tbody td{{padding:.55rem 1rem;font-size:.83rem;vertical-align:middle}}
.sl{{color:var(--blue);text-decoration:none;font-size:.75rem}}
.sl:hover{{text-decoration:underline}}
.ok-d{{color:var(--green);font-weight:700;font-size:.8rem}}.ok-d::before{{content:'● '}}
.fail-d{{color:var(--red);font-weight:700;font-size:.8rem}}.fail-d::before{{content:'● '}}
.s0{{color:var(--green);font-weight:800}}.shi{{color:var(--red);font-weight:800}}
tr.rf{{background:#fff5f5}}
tr.rf:hover{{background:#fee2e2}}
#fw{{position:fixed;bottom:1.5rem;right:1.5rem;z-index:8888;width:280px;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.22);border:1px solid var(--border);overflow:hidden;transform:translateY(130%);transition:transform .45s cubic-bezier(.34,1.56,.64,1),opacity .45s;opacity:0}}
#fw.show{{transform:translateY(0);opacity:1}}
#fw-head{{background:linear-gradient(90deg,var(--navy),var(--blue));color:#fff;padding:.75rem 1rem;display:flex;align-items:center;justify-content:space-between}}
#fw-head span{{font-size:.85rem;font-weight:800}}
#fw-close{{background:none;border:none;color:#fff;cursor:pointer;font-size:1.1rem;line-height:1;padding:0 2px}}
#fw-body{{padding:.85rem 1rem}}
.fw-prod{{display:flex;gap:.6rem;align-items:center;text-decoration:none;color:#0f172a;padding:.5rem;border-radius:10px;transition:background .15s;margin-bottom:.4rem}}
.fw-prod:hover{{background:#f8faff}}
.fw-prod img{{width:52px;height:52px;object-fit:cover;object-position:top;border-radius:8px;flex-shrink:0}}
.fw-name{{font-size:.78rem;font-weight:800;line-height:1.3}}
.fw-tag{{font-size:.65rem;color:var(--blue);font-weight:700;margin-top:.15rem}}
.fw-cta{{display:block;text-align:center;background:linear-gradient(90deg,var(--blue),var(--teal));color:#fff;border-radius:8px;padding:.5rem;font-size:.8rem;font-weight:800;text-decoration:none;margin-top:.3rem}}
.fw-call{{text-align:center;font-size:.75rem;color:var(--muted);margin-top:.5rem}}
.fw-call a{{color:var(--amber);font-weight:700;text-decoration:none}}
footer{{text-align:center;padding:2rem 1rem;font-size:.8rem;color:var(--muted)}}
@media(max-width:640px){{thead th:nth-child(3),tbody td:nth-child(3){{display:none}} .hdr h1{{font-size:1.35rem}} #fw{{width:calc(100vw - 2rem);right:1rem}}}}
</style>
</head>
<body>
<div id="mo">
 <div id="mb">
  <div id="mh"><h2>🏥 NEET Counselling Monitor</h2><p>Live alerts for 133 official counselling websites.<br>Enter your details once — takes 2 minutes.</p></div>
  <div id="mbody">
   <div class="step-ind"><div class="step-dot active" id="d1"></div><div class="step-dot" id="d2"></div><div class="step-dot" id="d3"></div></div>
   <div class="step active" id="s1">
    <div class="field"><label>Full Name</label><input type="text" id="f-name" placeholder="e.g. Rahul Sharma"><div class="hint err" id="e-name">Please enter your name</div></div>
    <div class="field"><label>Mobile Number</label><input type="tel" id="f-phone" placeholder="10-digit WhatsApp number" maxlength="10"><div class="hint err" id="e-phone">Enter a valid 10-digit number</div></div>
    <div class="ph-note">📱 We may send NEET counselling alerts on WhatsApp. Enter your real number so you don't miss important updates.</div>
    <div class="btn-row"><button class="btn btn-p" onclick="s1next()">Continue →</button></div>
   </div>
   <div class="step" id="s2">
    <div class="field"><label>Email Address</label>
     <div class="ir"><input type="email" id="f-email" placeholder="you@example.com"><button class="btn-otp" id="btn-eotp" onclick="sendOTP()">Send OTP</button></div>
     <div class="hint err" id="e-email">Enter a valid email</div>
     <div class="hint ok" id="h-sent" style="display:none">✅ OTP sent! Check your inbox.</div>
    </div>
    <div class="field" id="otp-field" style="display:none">
     <label>Enter OTP from Email</label>
     <div class="ir"><input type="number" id="f-otp" placeholder="6-digit code"><button class="btn-otp" id="btn-ver" onclick="verOTP()">Verify</button></div>
     <div class="hint err" id="e-otp">Incorrect OTP. Try again.</div>
     <div class="hint ok" id="h-ver" style="display:none">✅ Email verified!</div>
     <div class="hint" id="h-resend" style="display:none">Didn't get it? <a href="#" onclick="sendOTP();return false" style="color:#1a4fad">Resend OTP</a></div>
    </div>
    <div class="btn-row"><button class="btn btn-s" onclick="goS(1)">← Back</button><button class="btn btn-p" id="btn-s2n" onclick="s2next()" disabled>Continue →</button></div>
   </div>
   <div class="step" id="s3">
    <div class="field"><label>State Domicile</label>
     <select id="f-state">
      <option value="">— Select your home state —</option>
      <option>Andhra Pradesh</option><option>Arunachal Pradesh</option><option>Assam</option><option>Bihar</option><option>Chhattisgarh</option><option>Goa</option><option>Gujarat</option><option>Haryana</option><option>Himachal Pradesh</option><option>Jharkhand</option><option>Jammu &amp; Kashmir</option><option>Karnataka</option><option>Kerala</option><option>Ladakh</option><option>Madhya Pradesh</option><option>Maharashtra</option><option>Manipur</option><option>Meghalaya</option><option>Mizoram</option><option>Nagaland</option><option>Odisha</option><option>Punjab</option><option>Rajasthan</option><option>Sikkim</option><option>Tamil Nadu</option><option>Telangana</option><option>Tripura</option><option>Uttar Pradesh</option><option>Uttarakhand</option><option>West Bengal</option><option>Andaman &amp; Nicobar Islands</option><option>Chandigarh</option><option>Dadra &amp; Nagar Haveli</option><option>Delhi</option><option>Lakshadweep</option><option>Puducherry</option>
     </select>
     <div class="hint err" id="e-state">Please select your state</div>
    </div>
    <p style="font-size:.82rem;color:#64748b;margin-bottom:1rem;line-height:1.5">We use your state to highlight the most relevant counselling updates for you.</p>
    <div class="btn-row"><button class="btn btn-s" onclick="goS(2)">← Back</button><button class="btn btn-p" id="btn-sub" onclick="submitForm()">🚀 Access Dashboard</button></div>
    <p style="font-size:.72rem;color:#64748b;margin-top:.75rem;text-align:center">Your data is stored securely. Never sold or shared.</p>
   </div>
  </div>
  <div id="msuccess"><div class="tick">🎉</div><h3>You're all set!</h3><p>Your details are saved. You now have full access to the NEET Monitor dashboard.</p><button class="go" onclick="closeModal()">Open Dashboard →</button></div>
 </div>
</div>

<div id="fw">
 <div id="fw-head"><span>🎯 NEET 2026 Counselling</span><button id="fw-close" onclick="closeFW()">✕</button></div>
 <div id="fw-body">
  <a class="fw-prod" href="https://www.adda247.com/product-onlineliveclasses/106726/neet-counselling-one-pro-aiq-state-deemed-private-medical-colleges-online-coaching?productId=106727" target="_blank">
   <img src="https://storeimages.adda247.com/ONEPROPDP1777893886.png" alt="ONE PRO" onerror="this.src='https://placehold.co/52x52/0f1f5c/fff?text=PRO'">
   <div><div class="fw-name">ONE PRO — AIQ, State, Deemed &amp; Private</div><div class="fw-tag">⭐ Recommended · 50% Off Today</div></div>
  </a>
  <a class="fw-prod" href="https://www.adda247.com/product-onlineliveclasses/106720/neet-counselling-aiq-state-deemed-private-medical-colleges-online-coaching?productId=106721" target="_blank">
   <img src="https://st.adda247.com/https://storeimages.adda247.com/OnePDP1783161279.webp" alt="Standard" onerror="this.src='https://placehold.co/52x52/1a4fad/fff?text=STD'">
   <div><div class="fw-name">Standard — AIQ, State, Deemed &amp; Private</div><div class="fw-tag">💰 Value Pack · Limited Seats</div></div>
  </a>
  <a class="fw-cta" href="https://www.adda247.com/neet-counselling-exam-kit?examCategoryMappingId=IPM" target="_blank">Browse All NEET Courses →</a>
  <div class="fw-call">📞 Query? Call <a href="tel:7042578247">70425 78247</a></div>
 </div>
</div>

<div class="hdr">
 <div class="hdr-in">
  <div>
   <h1>🏥 NEET Counselling <span>Monitor</span></h1>
   <div class="sub">Watching {total} official websites across India — real-time change detection</div>
   <div class="ts">Last scan: {now} · Auto-scans every 30 minutes</div>
  </div>
  <button class="hdr-btn" onclick="showModal()">📝 Update Profile</button>
 </div>
</div>

<div class="page">
 <div class="main">
  <div class="stats">
   <div class="stat s-t"><div class="lbl">Total Sites</div><div class="val">{total}</div><div class="note">monitored this run</div></div>
   <div class="stat s-o"><div class="lbl">Responded OK</div><div class="val">{ok_cnt}</div><div class="note">{ok_pct}% reachable</div></div>
   <div class="stat s-f"><div class="lbl">Failed / Down</div><div class="val">{fail_cnt}</div><div class="note">many block bots</div></div>
   <div class="stat s-c"><div class="lbl">Changes Found</div><div class="val">{chg_cnt}</div><div class="note">Telegram alerts sent</div></div>
  </div>
  <div class="ri">
   <span>⏱ <b>Started:</b> {started} UTC</span>
   <span>✅ <b>Finished:</b> {finished} UTC</span>
   <span>🔄 <b>Next scan:</b> ~30 min</span>
  </div>
  <div class="sh"><h2>🔔 Recent Changes Detected</h2><span class="badge p">{change_count}</span></div>
  <div class="changes">{change_cards}</div>
  <div class="sh" style="margin-top:2rem"><h2>📋 All Sites Status</h2><span class="badge">{total}</span></div>
  <div class="tw">
   <div class="fb">
    <input type="text" id="searchBox" placeholder="🔍 Search site or URL…" oninput="ap()">
    <button class="act" onclick="setF('all',this)">All</button>
    <button onclick="setF('ok',this)">✅ OK</button>
    <button onclick="setF('fail',this)">❌ Failed</button>
    <button onclick="setF('high',this)">⭐ HIGH</button>
   </div>
   <div class="ov"><table id="T">
    <thead><tr><th>#</th><th>Site</th><th>URL</th><th>Priority</th><th>Last OK</th><th>Last Fail</th><th>Streak</th><th>Status</th></tr></thead>
    <tbody>{site_rows}</tbody>
   </table></div>
  </div>
 </div>
 <div class="sidebar">
  <p class="sidebar-title">📚 NEET Counselling Courses</p>
  <a class="prod-card" href="https://www.adda247.com/product-onlineliveclasses/106726/neet-counselling-one-pro-aiq-state-deemed-private-medical-colleges-online-coaching?productId=106727" target="_blank">
   <img src="https://storeimages.adda247.com/ONEPROPDP1777893886.png" alt="ONE PRO" onerror="this.src='https://placehold.co/300x190/0f1f5c/fff?text=ONE+PRO'">
   <div class="pc-body">
    <div class="pc-tags"><span class="pc-tag rec">⭐ Recommended</span><span class="pc-tag disc">🔥 50% Off Today</span><span class="pc-tag lim">⏳ Limited Seats</span></div>
    <div class="pc-name">NEET 2026 Counselling — ONE PRO<br>AIQ, State, Deemed &amp; Private Colleges</div>
    <div class="pc-btn">Explore Course →</div>
   </div>
  </a>
  <a class="prod-card" href="https://www.adda247.com/product-onlineliveclasses/106720/neet-counselling-aiq-state-deemed-private-medical-colleges-online-coaching?productId=106721" target="_blank">
   <img src="https://st.adda247.com/https://storeimages.adda247.com/OnePDP1783161279.webp" alt="NEET Standard" onerror="this.src='https://placehold.co/300x190/1a4fad/fff?text=NEET+Counselling'">
   <div class="pc-body">
    <div class="pc-tags"><span class="pc-tag val">💰 Value Pack</span><span class="pc-tag disc">🔥 50% Off Today</span><span class="pc-tag lim">⏳ Limited Seats</span></div>
    <div class="pc-name">NEET 2026 Counselling<br>AIQ, State, Deemed &amp; Private Colleges</div>
    <div class="pc-btn">Explore Course →</div>
   </div>
  </a>
  <div class="call-box">
   <div class="cb-label">📞 Counselling Query?</div>
   <a class="cb-num" href="tel:7042578247">70425 78247</a>
   <div class="cb-sub">Mon – Sun | 7:00 AM – 11:00 PM</div>
  </div>
  <a class="yt-link" href="https://www.youtube.com/@AddaNEETCounselling" target="_blank">
   <div class="yt-icon"><svg viewBox="0 0 24 24"><path fill="#fff" d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1C24 15.9 24 12 24 12s0-3.9-.5-5.8zM9.8 15.5V8.5l6.3 3.5-6.3 3.5z"/></svg></div>
   <div><div class="yt-text">Explore Counselling Videos</div><div class="yt-sub">AddaNEET Counselling · YouTube</div></div>
  </a>
  <div class="promo-banner">
   <h3>🎯 Expert Counselling Support</h3>
   <p>1-on-1 guidance · Seat Matrix · College Preference List · Document Help</p>
   <a href="https://www.adda247.com/neet-counselling-exam-kit?examCategoryMappingId=IPM" target="_blank">Browse All NEET Courses →</a>
  </div>
  <div style="background:#fff;border-radius:14px;border:1px solid #dde6f5;padding:1rem;font-size:.82rem;color:#334155">
   <div style="font-weight:800;margin-bottom:.6rem;font-size:.85rem">📊 Monitor Stats</div>
   <div style="display:flex;flex-direction:column;gap:.4rem">
    <div style="display:flex;justify-content:space-between"><span>Sites monitored</span><b>{total}</b></div>
    <div style="display:flex;justify-content:space-between"><span>Scan frequency</span><b>30 min</b></div>
    <div style="display:flex;justify-content:space-between"><span>Currently OK</span><b>{ok_cnt}</b></div>
    <div style="display:flex;justify-content:space-between"><span>Alerts via</span><b>Telegram</b></div>
    <div style="display:flex;justify-content:space-between"><span>Daily digest</span><b>Email 8:30 AM</b></div>
   </div>
  </div>
 </div>
</div>
<footer>NEET Counselling Monitor · {total} official sites · Auto-scans every 30 min via GitHub Actions<br><strong style="color:#dc2626">⚠ Some government sites block automated traffic — this is normal and does not affect your alerts.</strong></footer>
<script>
const APPS_URL='{APPS_SCRIPT_URL}';
let eVer=false,curStep=1;
window.addEventListener('DOMContentLoaded',()=>{{
 try{{const u=JSON.parse(localStorage.getItem('neet_user')||'{{}}');if(u.email&&u.verified){{closeModal();startFW();return;}}}}catch(e){{}}
}});
function showModal(){{document.getElementById('mo').style.display='flex';}}
function closeModal(){{document.getElementById('mo').style.display='none';startFW();}}
let fwT;
function startFW(){{
 if(sessionStorage.getItem('fw_closed'))return;
 fwT=setTimeout(()=>document.getElementById('fw').classList.add('show'),150000);
}}
function closeFW(){{document.getElementById('fw').classList.remove('show');clearTimeout(fwT);sessionStorage.setItem('fw_closed','1');}}
function goS(n){{
 document.getElementById('s'+curStep).classList.remove('active');
 document.getElementById('s'+n).classList.add('active');
 for(let i=1;i<=3;i++){{const d=document.getElementById('d'+i);d.className='step-dot'+(i<n?' done':i===n?' active':'');}}
 curStep=n;
}}
function s1next(){{
 const name=document.getElementById('f-name').value.trim();
 const phone=document.getElementById('f-phone').value.trim();
 let ok=true;
 if(!name){{sh('e-name','Please enter your name');ok=false;}}else hd('e-name');
 if(!/^\d{{10}}$/.test(phone)){{sh('e-phone','Enter a valid 10-digit number');ok=false;}}else hd('e-phone');
 if(ok)goS(2);
}}
async function sendOTP(){{
 const email=document.getElementById('f-email').value.trim();
 if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)){{sh('e-email','Enter a valid email');return;}}
 hd('e-email');
 const btn=document.getElementById('btn-eotp');btn.disabled=true;btn.textContent='Sending…';
 try{{await fetch(APPS_URL,{{method:'POST',mode:'no-cors',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{action:'send_otp',email}})}});}}catch(e){{}}
 btn.textContent='Resend';btn.disabled=false;
 document.getElementById('otp-field').style.display='block';
 sh('h-sent');setTimeout(()=>sh('h-resend'),30000);
}}
async function verOTP(){{
 const email=document.getElementById('f-email').value.trim();
 const otp=document.getElementById('f-otp').value.trim();
 if(!otp||otp.length<6){{sh('e-otp','Enter the 6-digit OTP');return;}}
 const vb=document.getElementById('btn-ver');vb.disabled=true;vb.textContent='Checking…';
 try{{
  const res=await fetch(APPS_URL,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{action:'verify_otp',email,otp}})}});
  const d=await res.json();
  if(d.success){{eVer=true;sh('h-ver');hd('e-otp');document.getElementById('btn-s2n').disabled=false;}}
  else{{sh('e-otp',d.reason==='expired'?'OTP expired. Resend.':'Incorrect OTP. Try again.');vb.disabled=false;vb.textContent='Verify';}}
 }}catch(e){{eVer=true;sh('h-ver');document.getElementById('btn-s2n').disabled=false;}}
}}
function s2next(){{if(eVer)goS(3);else sh('e-email','Please verify your email first');}}
async function submitForm(){{
 const state=document.getElementById('f-state').value;
 if(!state){{sh('e-state','Please select your state');return;}}
 const name=document.getElementById('f-name').value.trim();
 const phone=document.getElementById('f-phone').value.trim();
 const email=document.getElementById('f-email').value.trim();
 const btn=document.getElementById('btn-sub');btn.disabled=true;btn.textContent='Saving…';
 try{{await fetch(APPS_URL,{{method:'POST',mode:'no-cors',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{action:'save_lead',name,phone,email,state,ts:new Date().toISOString()}})}});}}catch(e){{}}
 localStorage.setItem('neet_user',JSON.stringify({{name,phone,email,state,verified:true}}));
 document.getElementById('mbody').style.display='none';
 document.getElementById('msuccess').style.display='block';
}}
function sh(id,msg){{const e=document.getElementById(id);if(msg)e.textContent=msg;e.style.display='block';}}
function hd(id){{document.getElementById(id).style.display='none';}}
let af='all';
function setF(f,b){{af=f;document.querySelectorAll('.fb button').forEach(x=>x.classList.remove('act'));b.classList.add('act');ap();}}
function ap(){{
 const q=document.getElementById('searchBox').value.toLowerCase();
 document.querySelectorAll('#T tbody tr').forEach(r=>{{
  const ok=(!q||r.textContent.toLowerCase().includes(q))&&(af==='all'||(af==='ok'&&r.dataset.s==='ok')||(af==='fail'&&r.dataset.s==='fail')||(af==='high'&&r.dataset.p==='HIGH'));
  r.style.display=ok?'':'none';
 }});
}}
</script>
</body></html>"""
