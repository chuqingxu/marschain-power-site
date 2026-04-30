#!/usr/bin/env python3
"""Build a standalone frontend-style MarsChain ranking dashboard."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path


def format_generated_at(ts: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def load_analytics_config() -> dict[str, str]:
    baidu_site_id = os.getenv("BAIDU_TONGJI_SITE_ID", "").strip()
    clarity_project_id = (
        os.getenv("MICROSOFT_CLARITY_PROJECT_ID", "").strip()
        or os.getenv("CLARITY_PROJECT_ID", "").strip()
    )
    return {
        "baidu_site_id": baidu_site_id,
        "clarity_project_id": clarity_project_id,
    }


def build_analytics_head() -> str:
    config = load_analytics_config()
    scripts: list[str] = []

    if config["baidu_site_id"]:
        scripts.append(
            """
  <script>
    window._hmt = window._hmt || [];
    (function() {
      var hm = document.createElement("script");
      hm.src = "https://hm.baidu.com/hm.js?%s";
      hm.defer = true;
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
    })();
  </script>
"""
            % config["baidu_site_id"]
        )

    if config["clarity_project_id"]:
        scripts.append(
            """
  <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
      c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
      t=l.createElement(r); t.async=1; t.src="https://www.clarity.ms/tag/" + i;
      y=l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "%s");
  </script>
"""
            % config["clarity_project_id"]
        )

    if not scripts:
        return ""

    return "".join(scripts)


def build_html(payload: dict) -> str:
    meta = payload["meta"]
    rows = payload["rows"]
    title = "MarsChain 算力排行榜"
    coverage_target = float(meta.get("coverage_target", 0.80))
    target_met = bool(meta.get("target_met", meta.get("discovered_power_coverage", 0) >= coverage_target))
    threshold_label = f"{coverage_target * 100:.0f}%"
    rpc_blocks_scanned = int(meta.get("rpc_blocks_scanned", 0) or 0)
    rpc_log_blocks_scanned = int(meta.get("rpc_log_blocks_scanned", 0) or 0)
    rpc_logs_seen = int(meta.get("rpc_logs_seen", 0) or 0)
    subtitle = (
        f"基于公开 explorer API、官方 RPC 与 POWER 合约日志生成，当前扫描覆盖率已达到 {threshold_label} 目标线。"
        if target_met
        else f"基于公开 explorer API、官方 RPC 与 POWER 合约日志生成，本轮扫描覆盖率暂未达到 {threshold_label} 目标线。"
    )
    embedded = json.dumps(payload, ensure_ascii=False).replace("</script>", "<\\/script>")
    generated_at = format_generated_at(int(meta["generated_at"]))
    analytics_head = build_analytics_head()
    hero_meta_items = [f"生成时间：{generated_at}"]
    if int(meta.get("tx_pages", 0) or 0) > 0:
        hero_meta_items.append(f'交易扫描：{int(meta.get("tx_pages", 0))} 页')
    if int(meta.get("block_pages", 0) or 0) > 0:
        hero_meta_items.append(f'区块扫描：{int(meta.get("block_pages", 0))} 页')
    if rpc_blocks_scanned > 0:
        hero_meta_items.append(f"RPC 深扫：{rpc_blocks_scanned:,} 块")
    if rpc_log_blocks_scanned > 0:
        hero_meta_items.append(f"合约日志：{rpc_log_blocks_scanned:,} 块 / {rpc_logs_seen:,} 条")
    if int(meta.get("upline_depth", 0) or 0) > 0:
        hero_meta_items.append(f'上级递归深度：{int(meta.get("upline_depth", 0))}')
    hero_meta_html = "\n".join(f"            <span>{item}</span>" for item in hero_meta_items)
    warning_html = (
        ""
        if target_met
        else (
            '<div class="alert warn">'
            f'<strong>本轮覆盖率未达标</strong><span>当前覆盖率仅为 '
            f'{meta["discovered_power_coverage"] * 100:.2f}% ，低于 {threshold_label} 发布阈值。'
            "这版结果仍已发布，方便你继续查看，但需要按页面提示理解覆盖范围。</span>"
            "</div>"
        )
    )
    risk_html = (
        '<div class="alert info">'
        '<strong>口径与风险</strong>'
        '<span>本页不是 MarsChain 官方后台导出的排行榜，而是基于公开 explorer API、官方 RPC 与 POWER 合约日志生成的 best effort 看板。'
        '全网总算力来自浏览器公开统计，候选钱包来自 POWER 合约日志，单地址算力来自公开地址接口。'
        '如果公开 API 延迟、RPC 节点漏返回、合约日志解析口径变化或缓存 fallback，榜单可能与官方最终口径存在偏差。</span>'
        "</div>"
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{subtitle}">
  <meta name="theme-color" content="#07080d">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{subtitle}">
  <meta property="og:type" content="website">
{analytics_head}
  <style>
    :root {{
      --bg: #07080d;
      --bg-2: #0b0d14;
      --surface: rgba(16, 18, 26, 0.72);
      --surface-strong: rgba(23, 26, 36, 0.88);
      --surface-soft: rgba(255, 255, 255, 0.035);
      --line: rgba(255, 255, 255, 0.09);
      --line-strong: rgba(255, 255, 255, 0.16);
      --text: #f7f8fb;
      --muted: #9aa0ad;
      --muted-2: #6f7685;
      --accent: #8f92ff;
      --accent-2: #7dd3fc;
      --good: #64d98a;
      --warn: #f4c06a;
      --shadow: 0 22px 70px rgba(0, 0, 0, 0.38);
      --radius: 20px;
      --font: "Avenir Next", "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
      --mono: "SFMono-Regular", "JetBrains Mono", ui-monospace, Menlo, monospace;
    }}
    * {{ box-sizing: border-box; }}
    html {{ color-scheme: dark; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: var(--font);
      color: var(--text);
      background:
        radial-gradient(circle at 50% -10%, rgba(143, 146, 255, 0.18), transparent 34%),
        radial-gradient(circle at 8% 22%, rgba(125, 211, 252, 0.08), transparent 28%),
        radial-gradient(circle at 92% 12%, rgba(255, 255, 255, 0.08), transparent 20%),
        linear-gradient(180deg, var(--bg) 0%, var(--bg-2) 68%, #07080d 100%);
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px);
      background-size: 56px 56px;
      mask-image: linear-gradient(180deg, rgba(0,0,0,0.7), transparent 72%);
    }}
    .wrap {{
      position: relative;
      z-index: 1;
      width: min(1360px, calc(100vw - 36px));
      margin: 0 auto;
      padding: 32px 0 44px;
    }}
    .hero {{
      position: relative;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 28px;
      padding: 38px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.075), rgba(255,255,255,0.025)),
        radial-gradient(circle at 80% 5%, rgba(143, 146, 255, 0.22), transparent 30%),
        rgba(10, 11, 16, 0.82);
      box-shadow: var(--shadow), inset 0 1px 0 rgba(255,255,255,0.08);
      backdrop-filter: blur(20px);
    }}
    .hero::before {{
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
      opacity: 0.35;
      pointer-events: none;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      right: -130px;
      top: -130px;
      width: 320px;
      height: 320px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.08);
      background: radial-gradient(circle at center, rgba(143, 146, 255, 0.28), rgba(143, 146, 255, 0) 68%);
      pointer-events: none;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 14px;
      padding: 7px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255,255,255,0.035);
      color: #c5c8ff;
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    .eyebrow::before {{
      content: "";
      width: 6px;
      height: 6px;
      border-radius: 999px;
      background: var(--good);
      box-shadow: 0 0 18px rgba(100, 217, 138, 0.8);
    }}
    .hero-grid {{
      position: relative;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 300px;
      gap: 28px;
      align-items: end;
    }}
    h1 {{
      margin: 0;
      max-width: 820px;
      font-size: clamp(38px, 5.3vw, 72px);
      line-height: 0.96;
      letter-spacing: -0.07em;
      text-wrap: balance;
    }}
    .subtitle {{
      margin: 18px 0 0;
      max-width: 820px;
      color: #b4bac8;
      font-size: 15px;
      line-height: 1.8;
    }}
    .hero-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 24px;
      color: var(--muted);
      font-size: 12px;
    }}
    .hero-meta span {{
      padding: 7px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255,255,255,0.035);
      font-family: var(--mono);
    }}
    .coverage {{
      justify-self: end;
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 18px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)),
        rgba(7, 8, 13, 0.55);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
    }}
    .coverage-ring {{
      --pct: 0deg;
      width: 146px;
      height: 146px;
      margin: 0 auto 16px;
      border-radius: 999px;
      background:
        radial-gradient(circle at center, #0a0c12 0 57%, transparent 58%),
        conic-gradient(var(--accent) 0 var(--pct), rgba(255,255,255,0.08) var(--pct) 360deg);
      display: grid;
      place-items: center;
      position: relative;
      box-shadow: 0 0 50px rgba(143, 146, 255, 0.12);
    }}
    .coverage-ring::before {{
      content: "";
      position: absolute;
      inset: 13px;
      border-radius: inherit;
      border: 1px solid rgba(255,255,255,0.08);
      background: radial-gradient(circle, rgba(255,255,255,0.04), transparent 66%);
    }}
    .coverage-value {{
      position: relative;
      z-index: 1;
      text-align: center;
    }}
    .coverage-value strong {{
      display: block;
      font-size: 30px;
      line-height: 1;
      letter-spacing: -0.06em;
    }}
    .coverage-value span {{
      display: block;
      margin-top: 7px;
      color: var(--muted-2);
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    .stat-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin-top: 14px;
    }}
    .alert {{
      display: flex;
      gap: 12px;
      align-items: flex-start;
      margin-top: 12px;
      padding: 13px 15px;
      border-radius: 16px;
      border: 1px solid rgba(244, 192, 106, 0.2);
      background: rgba(244, 192, 106, 0.075);
      color: #f5d79a;
      line-height: 1.6;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
    }}
    .alert.info {{
      border-color: rgba(143, 146, 255, 0.2);
      background: rgba(143, 146, 255, 0.075);
      color: #d7dafd;
    }}
    .alert.info strong {{
      color: #cbcfff;
    }}
    .alert strong {{
      flex: 0 0 auto;
      color: #ffe0a3;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .alert span {{
      font-size: 12px;
    }}
    .stat-card, .section, .top-card, .table-shell {{
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--surface);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.055);
      backdrop-filter: blur(18px);
    }}
    .stat-card {{
      min-height: 150px;
      padding: 15px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.065), rgba(255,255,255,0.025)),
        rgba(13, 15, 22, 0.72);
      transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }}
    .stat-card:hover {{
      transform: translateY(-2px);
      border-color: var(--line-strong);
      background: rgba(18, 20, 30, 0.86);
    }}
    .stat-card .label-row {{
      display: flex;
      align-items: center;
      gap: 7px;
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 10px;
      letter-spacing: 0.03em;
    }}
    .info-dot {{
      display: inline-grid;
      place-items: center;
      width: 15px;
      height: 15px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.16);
      color: #c5c8ff;
      background: rgba(255,255,255,0.04);
      font-size: 10px;
      line-height: 1;
      cursor: help;
    }}
    .stat-card .value {{
      font-size: clamp(22px, 2.2vw, 34px);
      line-height: 1;
      letter-spacing: -0.055em;
      font-weight: 700;
    }}
    .stat-card .help {{
      margin-top: 12px;
      color: var(--muted-2);
      font-size: 11px;
      line-height: 1.55;
    }}
    .section {{
      margin-top: 14px;
      padding: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.052), rgba(255,255,255,0.02)),
        rgba(11, 13, 20, 0.66);
    }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 20px;
      margin-bottom: 16px;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
    }}
    .section-title {{
      margin: 0;
      font-size: 20px;
      line-height: 1.1;
      letter-spacing: -0.045em;
    }}
    .section-note {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.65;
      max-width: 760px;
    }}
    .top-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
    }}
    .top-card {{
      position: relative;
      overflow: hidden;
      padding: 16px;
      background:
        radial-gradient(circle at 100% 0%, rgba(143,146,255,0.14), transparent 42%),
        linear-gradient(180deg, rgba(255,255,255,0.065), rgba(255,255,255,0.024));
    }}
    .top-card::before {{
      content: "";
      position: absolute;
      inset: 0 0 auto;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.28), transparent);
    }}
    .top-rank {{
      color: var(--accent-2);
      font-family: var(--mono);
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .top-power {{
      margin-top: 14px;
      font-size: 28px;
      font-weight: 700;
      line-height: 1;
      letter-spacing: -0.055em;
    }}
    .top-address {{
      margin-top: 14px;
      font-family: var(--mono);
      font-size: 11px;
      color: #d8dafe;
      word-break: break-all;
    }}
    .top-sub {{
      margin-top: 10px;
      font-size: 11px;
      line-height: 1.5;
      color: var(--muted-2);
    }}
    .bar-list {{
      display: grid;
      gap: 11px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: 26px minmax(170px, 1.1fr) minmax(180px, 3fr) 96px;
      gap: 12px;
      align-items: center;
      padding: 8px 10px;
      border: 1px solid transparent;
      border-radius: 12px;
    }}
    .bar-row:hover {{
      border-color: rgba(255,255,255,0.08);
      background: rgba(255,255,255,0.03);
    }}
    .bar-rank {{
      color: var(--muted-2);
      font-family: var(--mono);
      font-size: 12px;
    }}
    .bar-label {{
      font-family: var(--mono);
      font-size: 11px;
      color: #d8dafe;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .bar-track {{
      position: relative;
      height: 8px;
      border-radius: 999px;
      background: rgba(255,255,255,0.07);
      overflow: hidden;
    }}
    .bar-fill {{
      position: absolute;
      inset: 0 auto 0 0;
      width: 0%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      box-shadow: 0 0 22px rgba(143,146,255,0.35);
    }}
    .bar-value {{
      text-align: right;
      font-family: var(--mono);
      font-size: 12px;
      color: var(--text);
    }}
    .toolbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-bottom: 14px;
    }}
    .action-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 9px;
      margin-top: 24px;
    }}
    .action-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 38px;
      padding: 0 13px;
      border-radius: 11px;
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(255,255,255,0.045);
      color: var(--text);
      text-decoration: none;
      font-size: 12px;
      transition: 0.18s ease;
    }}
    .action-btn:hover {{
      transform: translateY(-1px);
      border-color: rgba(143, 146, 255, 0.4);
      background: rgba(143, 146, 255, 0.12);
    }}
    .search {{
      flex: 1 1 360px;
      min-width: 260px;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(7, 8, 13, 0.65);
      color: var(--text);
      font: inherit;
      outline: none;
    }}
    .search:focus {{
      border-color: rgba(143, 146, 255, 0.45);
      box-shadow: 0 0 0 3px rgba(143, 146, 255, 0.12);
    }}
    .chip-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }}
    .chip {{
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(255,255,255,0.035);
      color: var(--muted);
      border-radius: 999px;
      padding: 9px 12px;
      cursor: pointer;
      font: inherit;
      font-size: 12px;
      transition: 0.18s ease;
    }}
    .chip:hover {{
      color: var(--text);
      border-color: rgba(255,255,255,0.18);
    }}
    .chip.active {{
      color: white;
      border-color: rgba(143,146,255,0.48);
      background: rgba(143,146,255,0.14);
    }}
    .table-shell {{
      overflow: hidden;
      background: rgba(9, 10, 15, 0.72);
    }}
    .table-wrap {{
      overflow: auto;
      max-height: 72vh;
    }}
    table {{
      width: 100%;
      min-width: 980px;
      border-collapse: collapse;
    }}
    th, td {{
      padding: 13px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.065);
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: rgba(15, 17, 24, 0.96);
      color: #dfe1ff;
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      backdrop-filter: blur(14px);
      font-size: 12px;
      font-weight: 600;
    }}
    tbody tr {{
      transition: background 0.14s ease;
    }}
    tbody tr:hover {{
      background: rgba(143,146,255,0.075);
    }}
    .mono {{
      font-family: var(--mono);
      font-size: 11px;
      color: #d8dafe;
      word-break: break-all;
    }}
    .pill {{
      display: inline-block;
      min-width: 56px;
      padding: 5px 9px;
      border: 1px solid rgba(100, 217, 138, 0.18);
      border-radius: 999px;
      background: rgba(100, 217, 138, 0.105);
      color: #b6f5c8;
      text-align: center;
      font-family: var(--mono);
      font-size: 11px;
    }}
    .muted {{
      color: var(--muted);
    }}
    .footer {{
      margin-top: 16px;
      color: var(--muted-2);
      font-size: 12px;
      line-height: 1.7;
    }}
    @media (max-width: 1180px) {{
      .hero-grid {{ grid-template-columns: 1fr; }}
      .coverage {{ justify-self: stretch; }}
      .stat-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .top-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 760px) {{
      .wrap {{ width: min(100vw - 20px, 1360px); padding-top: 12px; }}
      .hero, .section {{ padding: 18px; border-radius: 20px; }}
      h1 {{ font-size: clamp(34px, 12vw, 54px); }}
      .stat-grid, .top-grid {{ grid-template-columns: 1fr; }}
      .alert {{ flex-direction: column; }}
      .bar-row {{ grid-template-columns: 24px 1fr; }}
      .bar-track, .bar-value {{ grid-column: 2; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="hero-grid">
        <div>
          <p class="eyebrow">MarsChain 算力前端看板</p>
          <h1>{title}</h1>
          <p class="subtitle">{subtitle}</p>
          <div class="hero-meta">
{hero_meta_html}
          </div>
          <div class="action-row">
            <a class="action-btn" href="./downloads/latest.csv" download data-track="download_csv" data-label="latest.csv">下载 CSV</a>
            <a class="action-btn" href="./downloads/latest.xlsx" download data-track="download_xlsx" data-label="latest.xlsx">下载 Excel</a>
            <a class="action-btn" href="./data/latest.json" target="_blank" rel="noopener" data-track="open_json" data-label="latest.json">查看 JSON</a>
          </div>
        </div>
        <div class="coverage">
          <div class="coverage-ring" id="coverageRing">
            <div class="coverage-value">
              <strong id="coverageValue"></strong>
              <span>覆盖率</span>
            </div>
          </div>
          <div class="muted" style="text-align:center; font-size:13px; line-height:1.6;">
            已发现地址算力 / 浏览器公布总算力
          </div>
        </div>
      </div>
    </section>
    {warning_html}
    {risk_html}

    <section class="stat-grid" id="statGrid"></section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">头部地址概览</h2>
          <div class="section-note">先看头部集中度，再看完整榜单。这个区块更适合做快速判断，不用一下子扎进长表。</div>
        </div>
      </div>
      <div class="top-grid" id="topGrid"></div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">前 15 名横向分布</h2>
          <div class="section-note">用横向条形图看头部断层最直观。这里按当前榜单默认排序展示。</div>
        </div>
      </div>
      <div class="bar-list" id="barList"></div>
    </section>

    <section class="section">
      <div class="section-head">
        <div>
          <h2 class="section-title">榜单明细（前 100）</h2>
          <div class="section-note">支持搜索地址、快速筛选和列排序。页面展示前 100 名，统计卡片中的候选钱包和正算力钱包为本轮全量扫描口径。</div>
        </div>
      </div>
      <div class="toolbar">
        <input id="searchInput" class="search" type="search" placeholder="搜索地址 / 上级地址 / 关键字段">
        <div class="chip-row" id="chipRow"></div>
      </div>
      <div class="table-shell">
        <div class="table-wrap">
          <table>
            <thead>
              <tr id="tableHead"></tr>
            </thead>
            <tbody id="tableBody"></tbody>
          </table>
        </div>
      </div>
      <div class="footer" id="footerText"></div>
    </section>
  </div>

  <script id="rankData" type="application/json">{embedded}</script>
  <script>
    const analytics = {{
      track(eventName, detail = {{}}) {{
        try {{
          if (window._hmt && typeof window._hmt.push === 'function') {{
            const label = detail.label ? String(detail.label) : '';
            window._hmt.push(['_trackEvent', 'marschain_site', eventName, label]);
          }}
        }} catch (error) {{
          console.warn('Baidu analytics track failed:', error);
        }}
        try {{
          if (typeof window.clarity === 'function') {{
            window.clarity('event', eventName);
            if (detail.label) {{
              window.clarity('set', 'last_event_label', String(detail.label).slice(0, 120));
            }}
          }}
        }} catch (error) {{
          console.warn('Clarity analytics track failed:', error);
        }}
      }}
    }};

    const payload = JSON.parse(document.getElementById('rankData').textContent);
    const meta = payload.meta;
    const coverageTarget = Number(meta.coverage_target || 0.8);
    const targetMet = Boolean(meta.target_met ?? (meta.discovered_power_coverage >= coverageTarget));
    const rows = payload.rows.map((row, index) => ({{
      ...row,
      rank: index + 1,
      power_num: Number(row.power),
      burned_num: Number(row.total_burned_amount),
      tx_seen_num: Number(row.tx_seen),
      log_seen_num: Number(row.log_seen || 0),
      upline_seen_num: Number(row.upline_seen),
      search_blob: [
        row.address,
        row.upline1 || '',
        row.upline2 || '',
        row.power_display,
        row.total_burned_amount_display
      ].join(' ').toLowerCase()
    }}));

    const state = {{
      query: '',
      filter: 'all',
      sortKey: 'power',
      sortDir: 'desc'
    }};
    let searchTrackTimer = null;
    let lastTrackedQuery = '';

    const formatUnits = (raw) => {{
      raw = Number(raw || 0);
      if (raw >= 1e12) return (raw / 1e12).toFixed(2) + 'T';
      if (raw >= 1e9) return (raw / 1e9).toFixed(2) + 'B';
      if (raw >= 1e6) return (raw / 1e6).toFixed(2) + 'M';
      if (raw >= 1e3) return (raw / 1e3).toFixed(2) + 'K';
      return String(raw);
    }};
    const formatCoverage = (value) => (value * 100).toFixed(2) + '%';
    const formatGeneratedAt = (ts) => new Date(ts * 1000).toLocaleString('zh-CN', {{ hour12: false }});
    const formatCount = (value) => Number(value || 0).toLocaleString();
    const formatMaybeUnits = (value) => (value === null || value === undefined) ? '—' : formatUnits(value);
    const escapeAttr = (value) => String(value).replaceAll('&', '&amp;').replaceAll('"', '&quot;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');

    function renderHero() {{
      const coverage = meta.discovered_power_coverage;
      document.getElementById('coverageValue').textContent = formatCoverage(coverage);
      document.getElementById('coverageRing').style.setProperty('--pct', `${{coverage * 360}}deg`);
    }}

    function renderStats() {{
      const top100Power = rows.slice(0, 100).reduce((sum, row) => sum + row.power_num, 0);
      const cards = [
        {{
          label: '全网总算力',
          value: formatUnits(meta.network_total_power),
          help: '来自 explorer /power/stats 的公开总算力，是覆盖率计算的分母。'
        }},
        {{
          label: '已发现总算力',
          value: formatUnits(meta.discovered_total_power),
          help: '本轮扫描到的正算力钱包算力合计，是覆盖率计算的分子。'
        }},
        {{
          label: '覆盖率',
          value: formatCoverage(meta.discovered_power_coverage),
          help: '已发现总算力 ÷ 全网总算力。它不是官方完整率，只代表公开数据下的扫描覆盖程度。'
        }},
        {{
          label: '全链地址总数',
          value: formatCount(meta.explorer_total_addresses),
          help: '浏览器统计的链上地址总数，包含不一定参与算力系统的地址。',
          hidden: !Number(meta.explorer_total_addresses || 0)
        }},
        {{
          label: '算力候选钱包',
          value: formatCount(meta.candidate_count),
          help: '从 POWER 合约日志中识别出的候选钱包地址总数，包含当前算力为 0 的地址。'
        }},
        {{
          label: '正算力钱包',
          value: formatCount(meta.positive_power_count),
          help: '候选钱包里当前 power > 0 的地址数量，也就是实际进入榜单计算的地址。'
        }},
        {{
          label: `链上今日新增钱包${{meta.today_utc_date ? ' · ' + meta.today_utc_date + ' UTC' : ''}}`,
          value: meta.today_new_wallet_count === null || meta.today_new_wallet_count === undefined ? '—' : formatCount(meta.today_new_wallet_count),
          help: '按链上 UTC 日统计：今天第一次出现在 POWER 合约日志里的候选钱包地址数。'
        }},
        {{
          label: `链上今日新增总算力${{meta.today_utc_date ? ' · ' + meta.today_utc_date + ' UTC' : ''}}`,
          value: formatMaybeUnits(meta.today_new_power),
          help: '按链上 UTC 日统计：当前全网总算力减去上一 UTC 日合约日历史总算力。'
        }},
        {{
          label: '前 100 名总算力',
          value: formatUnits(top100Power),
          help: '当前榜单前 100 个地址的算力合计，用来观察头部集中度。'
        }},
        {{
          label: '合约日志扫描',
          value: `${{formatCount(meta.rpc_log_blocks_scanned)}} 块`,
          help: `本轮从 POWER 合约日志扫描候选地址，共读取 ${{formatCount(meta.rpc_logs_seen)}} 条日志。`
        }}
      ].filter((card) => !card.hidden);
      document.getElementById('statGrid').innerHTML = cards.map((card) => `
        <div class="stat-card">
          <div class="label-row">
            <span>${{card.label}}</span>
            <span class="info-dot" title="${{escapeAttr(card.help)}}">!</span>
          </div>
          <div class="value">${{card.value}}</div>
          <div class="help">${{card.help}}</div>
        </div>
      `).join('');
    }}

    function renderTopCards() {{
      const topFive = rows.slice(0, 5);
      document.getElementById('topGrid').innerHTML = topFive.map((row) => {{
        const parts = [`总燃烧 ${{row.total_burned_amount_display}}`];
        if (row.tx_seen_num > 0) parts.push(`交易命中 ${{row.tx_seen}}`);
        if (row.log_seen_num > 0) parts.push(`日志命中 ${{row.log_seen}}`);
        return `
        <article class="top-card">
          <div class="top-rank">第 ${{row.rank}} 名</div>
          <div class="top-power">${{row.power_display}}</div>
          <div class="top-address">${{row.address}}</div>
          <div class="top-sub">${{parts.join(' | ')}}</div>
        </article>
      `;
      }}).join('');
    }}

    function renderBars() {{
      const list = rows.slice(0, 15);
      const maxPower = list[0]?.power_num || 1;
      document.getElementById('barList').innerHTML = list.map((row) => `
        <div class="bar-row">
          <div class="bar-rank">${{row.rank}}</div>
          <div class="bar-label" title="${{row.address}}">${{row.address}}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${{(row.power_num / maxPower) * 100}}%"></div></div>
          <div class="bar-value">${{row.power_display}}</div>
        </div>
      `).join('');
    }}

    const filters = {{
      all: () => true,
      top20: (row) => row.rank <= 20,
      over10b: (row) => row.power_num >= 10_000_000_000,
      withUpline: (row) => Boolean(row.upline1 || row.upline2),
      activeTx: (row) => row.tx_seen_num >= 10
    }};

    function renderChips() {{
      const chips = [
        ['all', '全部'],
        ['top20', '前 20 名'],
        ['over10b', '≥ 10B']
      ];
      if (rows.some((row) => row.upline1 || row.upline2)) chips.push(['withUpline', '有上级']);
      if (rows.some((row) => row.tx_seen_num >= 10)) chips.push(['activeTx', '高频交易']);
      const row = document.getElementById('chipRow');
      row.innerHTML = chips.map(([key, label]) => `
        <button class="chip ${{state.filter === key ? 'active' : ''}}" data-filter="${{key}}">${{label}}</button>
      `).join('');
      row.querySelectorAll('[data-filter]').forEach((button) => {{
        button.addEventListener('click', () => {{
          state.filter = button.dataset.filter;
          analytics.track('filter_change', {{ label: state.filter }});
          renderTable();
          renderChips();
        }});
      }});
    }}

    function getTableColumns() {{
      const hasTxSeen = rows.some((row) => row.tx_seen_num > 0);
      const hasLogSeen = rows.some((row) => row.log_seen_num > 0);
      const hasUplineSeen = rows.some((row) => row.upline_seen_num > 0);
      const hasUpline1 = rows.some((row) => Boolean(row.upline1));
      const hasUpline2 = rows.some((row) => Boolean(row.upline2));
      return [
        {{ key: 'rank', label: '排名', help: '当前按算力排序后的名次。' }},
        {{ key: 'address', label: '地址', help: '候选钱包地址。' }},
        {{ key: 'power', label: '算力', help: '地址当前公开算力。' }},
        {{ key: 'total_burned_amount', label: '累计燃烧', help: '地址历史累计燃烧数量，来自公开地址接口。' }},
        {{ key: 'log_seen', label: '日志命中', help: '该地址在 POWER 合约日志中出现的次数。', visible: hasLogSeen }},
        {{ key: 'tx_seen', label: '交易命中', help: '仅在启用交易页扫描时显示；当前全链日志模式通常不需要。', visible: hasTxSeen }},
        {{ key: 'upline_seen', label: '上级命中', help: '仅在启用上级递归扫描时显示。', visible: hasUplineSeen }},
        {{ key: 'upline1', label: '一级上级', help: '公开接口返回的一级上级地址。', visible: hasUpline1 }},
        {{ key: 'upline2', label: '二级上级', help: '公开接口返回的二级上级地址。', visible: hasUpline2 }}
      ].filter((column) => column.visible !== false);
    }}

    function renderTableHead(columns) {{
      const head = document.getElementById('tableHead');
      head.innerHTML = columns.map((column) => `
        <th data-key="${{column.key}}">
          ${{column.label}}
          <span class="info-dot" title="${{escapeAttr(column.help)}}">!</span>
        </th>
      `).join('');
      head.querySelectorAll('th[data-key]').forEach((cell) => {{
        cell.addEventListener('click', () => {{
          const key = cell.dataset.key;
          if (state.sortKey === key) {{
            state.sortDir = state.sortDir === 'desc' ? 'asc' : 'desc';
          }} else {{
            state.sortKey = key;
            state.sortDir = key === 'address' || key.startsWith('upline') ? 'asc' : 'desc';
          }}
          analytics.track('table_sort', {{ label: `${{state.sortKey}}:${{state.sortDir}}` }});
          renderTable();
        }});
      }});
    }}

    function renderCell(row, key) {{
      const cells = {{
        rank: row.rank,
        address: `<span class="mono">${{row.address}}</span>`,
        power: `<span class="pill">${{row.power_display}}</span>`,
        total_burned_amount: row.total_burned_amount_display,
        tx_seen: row.tx_seen,
        log_seen: row.log_seen || 0,
        upline_seen: row.upline_seen,
        upline1: `<span class="mono">${{row.upline1 || '—'}}</span>`,
        upline2: `<span class="mono">${{row.upline2 || '—'}}</span>`
      }};
      return cells[key] ?? '';
    }}

    function getFilteredRows() {{
      const query = state.query.trim().toLowerCase();
      const filterFn = filters[state.filter] || filters.all;
      const list = rows.filter((row) => filterFn(row) && (!query || row.search_blob.includes(query)));
      const dir = state.sortDir === 'asc' ? 1 : -1;
      list.sort((a, b) => {{
        const key = state.sortKey;
        const map = {{
          rank: [a.rank, b.rank],
          address: [a.address, b.address],
          power: [a.power_num, b.power_num],
          total_burned_amount: [a.burned_num, b.burned_num],
          tx_seen: [a.tx_seen_num, b.tx_seen_num],
          log_seen: [a.log_seen_num, b.log_seen_num],
          upline_seen: [a.upline_seen_num, b.upline_seen_num],
          upline1: [a.upline1 || '', b.upline1 || ''],
          upline2: [a.upline2 || '', b.upline2 || '']
        }};
        const [left, right] = map[key] || [a.power_num, b.power_num];
        if (typeof left === 'number' && typeof right === 'number') return (left - right) * dir;
        return String(left).localeCompare(String(right)) * dir;
      }});
      return list;
    }}

    function renderTable() {{
      const columns = getTableColumns();
      renderTableHead(columns);
      const list = getFilteredRows();
      document.getElementById('tableBody').innerHTML = list.map((row) => `
        <tr>
          ${{columns.map((column) => `<td>${{renderCell(row, column.key)}}</td>`).join('')}}
        </tr>
      `).join('');

      document.getElementById('footerText').textContent =
        `当前显示 ${{list.length}} / ${{rows.length}} 行。最近更新时间：${{formatGeneratedAt(meta.generated_at)}}。` +
        `本轮覆盖率 ${{formatCoverage(meta.discovered_power_coverage)}}，目标阈值 ${{formatCoverage(coverageTarget)}}，` +
        `${{targetMet ? '已达标' : '未达标'}}。说明：候选钱包 ${{formatCount(meta.candidate_count)}} 个，正算力钱包 ${{formatCount(meta.positive_power_count)}} 个；` +
        `这是一份基于公开 explorer API、官方 RPC 和合约日志生成的 best effort 榜单，不是官方后端直接导出的全量榜。`;
    }}

    function bindEvents() {{
      document.querySelectorAll('[data-track]').forEach((node) => {{
        node.addEventListener('click', () => {{
          analytics.track(node.dataset.track || 'click', {{ label: node.dataset.label || '' }});
        }});
      }});
      document.getElementById('searchInput').addEventListener('input', (event) => {{
        state.query = event.target.value;
        if (searchTrackTimer) {{
          clearTimeout(searchTrackTimer);
        }}
        searchTrackTimer = setTimeout(() => {{
          const normalized = state.query.trim().toLowerCase();
          if (normalized.length >= 2 && normalized !== lastTrackedQuery) {{
            lastTrackedQuery = normalized;
            analytics.track('search_used', {{ label: normalized.slice(0, 60) }});
          }}
        }}, 600);
        renderTable();
      }});
    }}

    renderHero();
    renderStats();
    renderTopCards();
    renderBars();
    renderChips();
    renderTable();
    bindEvents();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a standalone frontend dashboard from a ranking JSON file.")
    parser.add_argument("input", help="Ranking JSON path.")
    parser.add_argument("output", help="Output HTML path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_html(payload))
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
