# -*- coding: utf-8 -*-
"""Telegram 频道宣传/引流模块 —— 集中渲染函数（2026-11-18）

频道地址、名称、说明及四语文案集中在 scripts/telegram_config.json，本模块只负责读取并渲染，
避免把 t.me 链接硬编码散落到 build_v2.py / rebuild_home_v7.py 多处。

对外接口：
  TG                       已解析的配置 dict（含 _cfg 原始对象）
  banner_html(lang)        首页显著位置的引流 section（jv7 风格）
  footer_card_html(lang)   首页页脚的频道卡片（jv7 风格）
  footer_channels_html(lang) 页脚 TELEGRAM 频道列 —— 卡片式（首页 foot_cols 与内页 footer 共用）
  inner_footer_html(lang)  内页页脚的频道条目（design-system 风格，纯 <li>）
  inner_footer_channels(lang) 内页页脚的 TELEGRAM 频道列（委托给 footer_channels_html，卡片式）
  inner_topbar_link(lang)  内页顶栏的简短 Telegram 链接 <a>
  track_attrs(placement)   点击追踪 + 新标签页 + 无障碍的统一属性串

任何字段缺失都安全回落，绝不因为配置问题让构建脚本崩溃。
"""
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CFG_PATH = _ROOT / 'scripts' / 'telegram_config.json'
_LANGS = ('en', 'zh', 'ru', 'ar')

_DEFAULT = {
    'url': 'https://t.me/chinausedcarexport',
    'handle': '@chinausedcarexport',
    'qr': '',
    'track_event': 'telegram_click',
    'name': {}, 'kicker': {}, 'title': {}, 'desc': {},
    'bullets': {}, 'cta': {}, 'footer_note': {}, 'qr_caption': {},
}


def _load():
    cfg = dict(_DEFAULT)
    try:
        raw = json.loads(_CFG_PATH.read_text(encoding='utf-8'))
        for k, v in raw.items():
            if not k.startswith('_'):
                cfg[k] = v
    except Exception as e:  # noqa: BLE001 — 配置损坏不能中断整站构建
        print(f'[telegram_block] WARN 读取配置失败，使用默认值：{e}', flush=True)
    return cfg


_cfg = _load()


class _TG:
    """提供 TG.get('url') / TG.t('title','en') 两种取数方式。"""

    def get(self, key, fallback=''):
        return _cfg.get(key, fallback)

    def t(self, key, lang, fallback_lang='en'):
        field = _cfg.get(key, {})
        if not isinstance(field, dict):
            return str(field) if field else ''
        if lang in field and field[lang]:
            return field[lang]
        return field.get(fallback_lang, '')

    @property
    def url(self):
        return _cfg.get('url', _DEFAULT['url'])

    @property
    def qr(self):
        return _cfg.get('qr', '')

    @property
    def event(self):
        return _cfg.get('track_event', _DEFAULT['track_event'])


TG = _TG()


def _esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def track_attrs(placement, lang='en'):
    """统一的外链属性：新标签页 + 引荐隔离 + 点击追踪占位 + 无障碍标注。"""
    if lang not in _LANGS:
        lang = 'en'
    return (f'target="_blank" rel="noopener noreferrer" '
            f'data-track="{_esc(TG.event)}" data-placement="{_esc(placement)}" '
            f'data-lang="{_esc(lang)}" aria-label="{_aria_label(lang, TG.t("cta", lang))}"')


def _aria_label(lang, text):
    """屏幕阅读器读完整语义：'在 Telegram 加入频道（在新标签页打开）'。"""
    base = text or TG.t('cta', lang) or TG.t('name', lang)
    suffix = {
        'en': ' (opens in a new tab)', 'zh': '（在新标签页打开）',
        'ru': ' (откроется в новой вкладке)', 'ar': ' (يفتح في علامة تبويب جديدة)',
    }.get(lang, '')
    return _esc(f'{base}{suffix}')


def _link_attrs(lang, placement):
    return (f'href="{_esc(TG.url)}" target="_blank" rel="noopener noreferrer" '
            f'data-track="{_esc(TG.event)}" data-placement="{_esc(placement)}" '
            f'data-lang="{_esc(lang)}" aria-label="{_aria_label(lang, TG.t("cta", lang))}"')


_SVG_TG = ('<svg class="jb-tg-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
           '<path fill="currentColor" d="M21.9 4.3 18.8 20c-.23 1.02-.85 1.27-1.72.79l-4.75-3.5-2.29 2.2'
           'c-.25.25-.47.47-.96.47l.34-4.84 8.8-7.95c.38-.34-.08-.53-.59-.19L7.2 13.3l-4.69-1.47'
           'c-1.02-.32-1.04-1.02.21-1.51l18.36-7.08c.85-.32 1.6.2 1.82 1.09z"/></svg>')


def banner_html(lang):
    """首页显著位置的 Telegram 引流 section —— jv7 视觉风格。"""
    name = _esc(TG.t('name', lang))
    kicker = _esc(TG.t('kicker', lang))
    title = _esc(TG.t('title', lang))
    desc = _esc(TG.t('desc', lang))
    cta = _esc(TG.t('cta', lang))
    bullets = TG.get('bullets', {}).get(lang) or TG.get('bullets', {}).get('en', [])
    items = ''.join(
        f'<li><svg viewBox="0 0 20 20" aria-hidden="true" focusable="false">'
        f'<path fill="currentColor" d="M8.2 13.6 4.5 9.9l1.4-1.4 2.3 2.3 5.9-5.9 1.4 1.4z"/></svg>'
        f'<span>{_esc(b)}</span></li>' for b in bullets)
    qr_html = ''
    if TG.qr:
        cap = _esc(TG.t('qr_caption', lang))
        qr_html = (f'<div class="jb-tg-qr"><img src="{_esc(TG.qr)}" '
                   f'alt="{name} QR" width="132" height="132" loading="lazy" decoding="async">'
                   f'<span>{cap}</span></div>')
    return f'''<section class="jb-tg" id="telegram" aria-labelledby="jb-tg-title-{lang}">
  <div class="jb-tg-inner">
    <div class="jb-tg-copy">
      <p class="jb-tg-kicker">{_SVG_TG}<span>{kicker}</span></p>
      <h2 class="jb-tg-title" id="jb-tg-title-{lang}">{title}</h2>
      <p class="jb-tg-desc">{desc}</p>
      <ul class="jb-tg-list">{items}</ul>
      <a class="jb-tg-btn" {_link_attrs(lang, 'home_banner')}>
        {_SVG_TG}<span>{cta}</span>
        <svg class="jb-tg-ext" viewBox="0 0 20 20" aria-hidden="true" focusable="false"><path fill="currentColor" d="M7 3h10v10h-2V6.4L5.7 15.7 4.3 14.3 13.6 5H7z"/></svg>
      </a>
      <span class="jb-tg-handle">{_esc(TG.get('handle',''))}</span>
    </div>
    {qr_html}
  </div>
</section>'''


def footer_card_html(lang):
    """首页页脚的频道横向卡片条 —— jv7 风格，含二维码占位（放在 footgrid 与 footbar 之间）。"""
    name = _esc(TG.t('name', lang))
    note = _esc(TG.t('footer_note', lang))
    cta = _esc(TG.t('cta', lang))
    qr_html = ''
    if TG.qr:
        qr_html = (f'<img class="jb-tg-footqr" src="{_esc(TG.qr)}" '
                   f'alt="{name} QR" width="64" height="64" loading="lazy" decoding="async">')
    return (f'<div class="jb-tg-footstrip">'
            f'<div class="jb-tg-footstrip-main">'
            f'<h4>{_SVG_TG}<span>{name}</span></h4>'
            f'<p>{note}</p>'
            f'</div>'
            f'<a class="jb-tg-footlink" {_link_attrs(lang, "home_footer")}>'
            f'{cta} <span aria-hidden="true">&#8599;</span></a>'
            f'{qr_html}</div>')


def _fc_text(field, lang, fallback_lang='en'):
    """取 footer_channels 里某字段的某语言文案（dict 或纯字符串）。"""
    if isinstance(field, dict):
        return field.get(lang) or field.get(fallback_lang, '')
    return str(field) if field else ''


def _channel_attrs(url, placement, lang, label):
    """频道/机器人卡片的外链属性：新标签页 + 追踪 + 以频道名作无障碍标注。"""
    if lang not in _LANGS:
        lang = 'en'
    suffix = {
        'en': ' (opens in a new tab)', 'zh': '（在新标签页打开）',
        'ru': ' (откроется в новой вкладке)', 'ar': ' (يفتح في علامة تبويب جديدة)',
    }.get(lang, '')
    return (f'href="{_esc(url)}" target="_blank" rel="noopener noreferrer" '
            f'data-track="{_esc(TG.event)}" data-placement="{_esc(placement)}" '
            f'data-lang="{_esc(lang)}" aria-label="{_esc(label)}{_esc(suffix)}"')


def footer_channels_html(lang):
    """页脚 TELEGRAM 频道列 —— 卡片式（首页 foot_cols 与内页 footer 共用）。

    4 个频道 + 投稿机器人，每张卡片含 Telegram 图标、频道名、@handle 与语言标签；
    机器人卡片用品牌橙强调。桌面端为页脚列内纵向卡片，手机端整列堆叠、卡片通栏可点。
    配置缺失时安全回落，绝不因为配置问题让构建脚本崩溃。
    """
    if lang not in _LANGS:
        lang = 'en'
    fc = TG.get('footer_channels', {}) or {}
    title = _esc(_fc_text(fc.get('title', {}), lang) or 'TELEGRAM')
    subtitle = _esc(_fc_text(fc.get('subtitle', {}), lang))
    bot_url = _esc(fc.get('bot_url', '')) or _esc(TG.url)
    bot_name = _esc(_fc_text(fc.get('bot_name', {}), lang)
                    or _fc_text(fc.get('bot_label', {}), lang)
                    or TG.t('cta', lang))
    bot_handle = _esc(fc.get('bot_handle', ''))
    bot_tag = _esc(_fc_text(fc.get('bot_tag', {}), lang))
    cards = []
    for ch in (fc.get('channels', []) or []):
        name = _esc(ch.get('name', ''))
        url = _esc(ch.get('url', ''))
        if not url or not name:
            continue
        handle = _esc(ch.get('handle', ''))
        tag = _esc(_fc_text(ch.get('tag', {}), lang))
        handle_html = f'<span class="jb-tg-ch-handle">{handle}</span>' if handle else ''
        tag_html = f'<span class="jb-tg-ch-tag">{tag}</span>' if tag else ''
        cards.append(
            f'<a class="jb-tg-ch" {_channel_attrs(url, "footer_channel", lang, ch.get("name", ""))}>'
            f'<span class="jb-tg-ch-ic">{_SVG_TG}</span>'
            f'<span class="jb-tg-ch-tx"><span class="jb-tg-ch-name">{name}</span>{handle_html}</span>'
            f'{tag_html}</a>')
    bot_handle_html = f'<span class="jb-tg-ch-handle">{bot_handle}</span>' if bot_handle else ''
    bot_tag_html = f'<span class="jb-tg-ch-tag">{bot_tag}</span>' if bot_tag else ''
    cards.append(
        f'<a class="jb-tg-ch jb-tg-ch-bot" {_channel_attrs(bot_url, "footer_bot", lang, _fc_text(fc.get("bot_name", {}), lang) or "JinbaCarsBot")}>'
        f'<span class="jb-tg-ch-ic">{_SVG_TG}</span>'
        f'<span class="jb-tg-ch-tx"><span class="jb-tg-ch-name">{bot_name}</span>{bot_handle_html}</span>'
        f'{bot_tag_html}</a>')
    sub_html = f'<p class="jb-tg-col-sub">{subtitle}</p>' if subtitle else ''
    return (f'<div class="jv7-footcol jb-tg-col"><h4>{title}</h4>{sub_html}'
            f'<div class="jb-tg-channels">{"".join(cards)}</div></div>')


def inner_topbar_link(lang):
    """内页顶栏的简短 Telegram 文字链接 <a>。"""
    return (f'<a {_link_attrs(lang, "inner_topbar")}>'
            f'{_esc({"en":"Telegram","zh":"Telegram","ru":"Telegram","ar":"تيليجرام"}.get(lang, "Telegram"))} &#8599;</a>')


def inner_footer_link(lang):
    """内页页脚的 Telegram 文字链接 <a>（放进现有 footergrid 的联系列）。"""
    return (f'<a {_link_attrs(lang, "inner_footer")}>'
            f'{_SVG_TG}<span>{_esc(TG.t("name", lang))} &#8599;</span></a>')


def inner_footer_channels(lang):
    """内页页脚的 TELEGRAM 频道列（4 频道 + 投稿 Bot）—— 卡片式，与首页同款。

    委托给 footer_channels_html，内容与首页 foot_cols 的 TELEGRAM 列完全一致。
    作为 .footergrid 的第 5 列插入（共用模板 footer() 里只写一次）。
    """
    return footer_channels_html(lang)


def inner_footer_cta(lang):
    """内页页脚的独立频道介绍块（<div>，design-system 风格）。"""
    name = _esc(TG.t('name', lang))
    note = _esc(TG.t('footer_note', lang))
    cta = _esc(TG.t('cta', lang))
    qr_html = ''
    if TG.qr:
        qr_html = (f'<img class="jb-tg-inner-qr" src="{_esc(TG.qr)}" '
                   f'alt="{name} QR" width="72" height="72" loading="lazy" decoding="async">')
    return (f'<div class="jb-tg-card">'
            f'<h4>{_SVG_TG}<span>{name}</span></h4>'
            f'<p>{note}</p>'
            f'<a class="jb-tg-card-btn" {_link_attrs(lang, "inner_footer_cta")}>{cta} <span aria-hidden="true">&#8599;</span></a>'
            f'{qr_html}</div>')
