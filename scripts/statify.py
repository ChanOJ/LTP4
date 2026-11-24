#!/usr/bin/env python3
"""Rebuild the LTP4 pre-party website (August 2000) as plain static HTML.

    python3 scripts/statify.py [--private PATH] [--out site]

The original site (ltp.ojuice.net, classic ASP + SSI) is not in the local archive in its
pre-party state: the pages come from the Wayback Machine (raw `id_` captures), a few images
and the Flash intro from the local archive (NAS copy). Both live OUTSIDE git, in `private/`:

    private/wayback/raw/<timestamp>/<path>   raw Wayback captures (see private/wayback/cdx-*.txt)
    private/nas/<path>                       files copied from the local archive (ltp/http/)
    private/gen/<file>                       files generated here (see SOURCES)
    private/vendor/ruffle-<version>/package  Ruffle (Flash emulator), npm tarball, integrity checked

Step 1 assembles `private/site-raw/` with the ORIGINAL names (index.asp, *.shtml), used by
scripts/verify_build.py for the link comparison. Step 2 renders `site/` from it: forms,
counters and dead plugins removed, personal data redacted, links renamed to `.html`.
`build-meta/` records where each published file comes from and the old -> new URLs.

Python 3.9+, standard library only. Files are read/written as iso-8859-1 (lossless round trip).
"""
import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

ENC = "iso-8859-1"

# ---- removal-request footer: added to every page that lists or describes people
REMOVAL_MARK = 'id="removal-note"'
REMOVAL_NOTE = (
    '<div id="removal-note" style="clear:both;margin:28px auto 8px;padding:6px 8px 0;width:760px;max-width:96%;box-sizing:border-box;'
    'border-top:1px solid #808080;text-align:center;font:10px/14px Verdana,Arial,Helvetica,sans-serif;'
    'color:#808080;background:transparent">To be removed from this page, '
    '<a href="mailto:chandra_oj@pm.me" style="color:#808080;text-decoration:underline">contact me</a>.</div>'
)
_BODY_END = re.compile(r"(?is)</body\s*>(?!.*</body\s*>)")


def add_removal_note(text):
    if REMOVAL_MARK in text:
        return text
    m = _BODY_END.search(text)
    if m:
        return text[: m.start()] + REMOVAL_NOTE + "\n" + text[m.start():]
    return text + "\n" + REMOVAL_NOTE + "\n"

# Pages that show a family name: every page with the left menu (it names the sponsoring contact,
# "Guillaume Nichols") plus the people lists. Not the Flash intro nor the two Java invitations.
NO_FOOTER_PAGES = {"index.html", "ltpeqx.html", "ltpeqxm.html"}


def is_people_page(rel):
    return rel.endswith(".html") and rel not in NO_FOOTER_PAGES

REPO = Path(__file__).resolve().parent.parent
PRIVATE_DEFAULT = REPO / "private"
MASK = "????"
RUFFLE_VERSION = "0.7.1"
CHIPTUNE_VERSION = "0.8.11-r25871"
FONT = 'face="Verdana, Arial, Helvetica, sans-serif"'

# Published path (original name) -> (source under private/, note). Order = build order.
W = "wayback/raw/"
SOURCES = {
    # Pages: last pre-party capture of each one (2000-08-29, the party was 2000-08-25..27,
    # the Wayback crawl ran two days after; the pages still show the pre-party content).
    "index.asp": (W + "20000829033106/index.asp", "Wayback 2000-08-29"),
    "forum.asp": (W + "20000829033113/forum.asp", "Wayback 2000-08-29"),
    "information.shtml": (W + "20000829033118/information.shtml", "Wayback 2000-08-29"),
    "legalinformation.shtml": (W + "20000829033123/legalinformation.shtml", "Wayback 2000-08-29"),
    "financial.shtml": (W + "20000829033129/financial.shtml", "Wayback 2000-08-29"),
    "howtocome.shtml": (W + "20000829033133/howtocome.shtml", "Wayback 2000-08-29"),
    "carbustrip.asp": (W + "20000829033140/carbustrip.asp", "Wayback 2000-08-29"),
    "howtoreserve.shtml": (W + "20000829033147/howtoreserve.shtml", "Wayback 2000-08-29"),
    "paid.shtml": (W + "20000829033152/paid.shtml", "Wayback 2000-08-29"),
    "compomachines.shtml": (W + "20000829033157/compomachines.shtml", "Wayback 2000-08-29"),
    "comporules.shtml": (W + "20000829033203/comporules.shtml", "Wayback 2000-08-29"),
    "sponsors.shtml": (W + "20000829033210/sponsors.shtml", "Wayback 2000-08-29"),
    "ltp2pic.shtml": (W + "20000829033215/ltp2pic.shtml", "Wayback 2000-08-29"),
    "ltp3pic.shtml": (W + "20000829033221/ltp3pic.shtml", "Wayback 2000-08-29"),
    "ltpeqxm.shtml": (W + "20000829033249/ltpeqxm.shtml", "Wayback 2000-08-29"),
    "ltpeqx.shtml": (W + "20000829033254/ltpeqx.shtml", "Wayback 2000-08-29"),
    "64.shtml": (W + "20000829033314/64.shtml", "Wayback 2000-08-29"),
    # Flash intro with mod player popup, earlier entry page of the site (local archive, 2000-08-29).
    "intro.htm": ("nas/img/index.htm", "local archive ltp/http/img/index.htm (2000-08-29)"),
    # Images.
    "_.gif": (W + "20000829033021/_.gif", "Wayback 2000-08-29"),
    "images/pixel.gif": (W + "20000829033011/images/pixel.gif", "Wayback 2000-08-29"),
    "images/hdo.gif": (W + "20000829033015/images/hdo.gif", "Wayback 2000-08-29"),
    **{"images/flags/%s.gif" % c: ("gen/flags/%s.gif" % c, "skin flag of Orange Juice v3 (originally ojuice.net/skins/tonic/pictures/flags/)")
       for c in ("be", "ca", "ch", "fi", "hu", "nl", "pt", "se", "uk")},
    "images/hgo.gif": ("gen/hgo.gif", "never captured: horizontal mirror of images/hdo.gif"),
    "images/bgo.gif": (W + "20000829033031/images/bgo.gif", "Wayback 2000-08-29"),
    "images/bdo.gif": (W + "20000829033035/images/bdo.gif", "Wayback 2000-08-29"),
    "images/_hg.gif": (W + "20000829033051/images/_hg.gif", "Wayback 2000-08-29"),
    "images/_hd.gif": (W + "20000829033056/images/_hd.gif", "Wayback 2000-08-29"),
    "images/_bg.gif": (W + "20000829033258/images/_bg.gif", "Wayback 2000-08-29"),
    "images/_bd.gif": (W + "20000829033303/images/_bd.gif", "Wayback 2000-08-29"),
    "images/spacer.gif": (W + "20000829033100/images/spacer.gif", "Wayback 2000-08-29"),
    "images/ltp4logo_b1.gif": (W + "20000829033026/images/ltp4logo_b1.gif", "Wayback 2000-08-29"),
    "images/btnoj2.gif": (W + "20000829033041/images/btnoj2.gif", "Wayback 2000-08-29"),
    "images/btnnecta.gif": (W + "20000829033046/images/btnnecta.gif", "Wayback 2000-08-29"),
    "images/ltp_banner.gif": (W + "20000829033308/images/ltp_banner.gif", "Wayback 2000-08-29"),
    "images/ltp4danfnl.jpg": ("nas/img/ltp4danfnl.jpg", "local archive ltp/http/img/ltp4danfnl.jpg"),
    "img/carte1b.jpg": ("nas/img/carte1b.jpg", "local archive ltp/http/img/carte1b.jpg"),
    "img/carte2.jpg": ("nas/img/carte2.jpg", "local archive ltp/http/img/carte2.jpg"),
    "img/carte3.jpg": (W + "20001002031908/img/carte3.jpg", "Wayback 2000-10-02 (same bytes as the local archive)"),
    "img/pano.jpg": ("nas/img/panoram.jpg", "never captured: local archive ltp/http/img/panoram.jpg (photo of the party place)"),
    "img/ltpintro.swf": ("nas/img/ltpintro.swf", "local archive ltp/http/img/ltpintro.swf"),
    # Tune of the intro ("Dis2them" = DisIsSid-theme 2 by Pink / Abyss, 8.3 name): never archived
    # with the site, taken from Modland (via Demozoo, music/254005).
    "music/dis2them.mod": ("music/disissid-2-theme.mod",
                           "never archived: ftp.modland.com Protracker/Pink/disissid-2-theme.mod"),
    # Downloads.
    "ltpform.zip": ("nas/ltpform.zip", "local archive ltp/http/ltpform.zip (blank entrance order form)"),
}
# Original page name -> published name.
# The Flash intro is the entry page (site root); the news page index.asp becomes news.html.
RENAMES = {"intro.htm": "index.html", "index.asp": "news.html"}
# Links whose target was never captured and is not in the local archive: left as plain text.
# (Also every gallery photo of ltp2pic/ and ltp3pic/ and the sponsor logos, found automatically.)
NOT_ARCHIVED_NOTE = "not archived"

NOTICE_FORM = (
    '<p><font %s size="2" color="#996600"><i>This website is an archive, kept online '
    "read-only: this form no longer works.</i></font></p>" % FONT)
NOTICE_APPLET = (
    '<font %s size="2" color="#996600"><i>[The Java invitation applet (Troisd.jar) was not '
    "archived.]</i></font>" % FONT)

# Personal data (see README, "What was changed from the original").
REDACT = [
    # Street of the association (a private home address), keep the town.
    (re.compile(r"26 quai Bizeau"), MASK),
    # Mobile numbers of the organisers (SMS line during the party): keep the country code.
    (re.compile(r"\+33(\d)\d{8}"), lambda m: "+33%s%s" % (m.group(1), MASK)),
]
EMAIL = re.compile(r"([A-Za-z0-9._+-]+)@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")


def read_text(p):
    return Path(p).read_bytes().decode(ENC)


def write_text(p, s):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(s.encode(ENC, errors="xmlcharrefreplace"))


def out_name(orig):
    if orig in RENAMES:
        return RENAMES[orig]
    return re.sub(r"(?i)\.(?:shtml|asp)$", ".html", orig)


def is_page(name):
    return name.lower().endswith((".asp", ".shtml", ".htm", ".html"))


# --------------------------------------------------------------------- transforms
MENU_END = re.compile(r"</td>\s*<td width=4><img src=images/spacer\.gif width=1 height=1></td>")


def restyle_menu(t):
    """The 2000-08-29 pages lost the fonts and colours of their left menu (hand-edited menu,
    plain <td>/<a>, so the browser default serif font and the orange BODY link colour). The
    2000-08-17 capture of the home page still has them: same markup applied, items unchanged."""
    start = t.find("<td>&#187;")
    if start < 0:
        return t
    m = MENU_END.search(t, start)
    if not m:
        return t
    block = t[start:m.start()]
    block = re.sub(r"<td>&#187; ([^<]*)</td>",
                   r'<td><FONT %s size="2"><B><FONT color="#FFFFFF">&#187; \1</FONT></B></FONT></td>' % FONT, block)

    def color_links(run):
        return re.sub(r"(?is)(<a\b[^>]*>)(.*?)</a>",
                      lambda a: a.group(0) if "<font" in a.group(2).lower()
                      else '%s<FONT color="#996600">%s</FONT></a>' % (a.group(1), a.group(2)), run)

    parts = re.split(r"(?i)(</table>)", block)
    out = []
    for i, part in enumerate(parts):
        if i and parts[i - 1].lower() == "</table>":
            nxt = re.search(r"(?i)<table\b", part)
            run, rest = (part[:nxt.start()], part[nxt.start():]) if nxt else (part, "")
            part = '<FONT %s size="2">%s<BR><BR></FONT>\n%s' % (FONT, color_links(run.rstrip()), rest)
        out.append(part)
    return t[:start] + "".join(out) + t[m.start():]


def strip_mailing_form(t):
    """The mailing-list form of every page only held hidden fields (no visible input): drop it."""
    return re.sub(r'(?is)<form action="m\.asp".*?</form>\s*', "", t)


def replace_forms(t, ctx, rel):
    n = len(re.findall(r"(?i)<form\b", t))
    if n:
        ctx["forms"].append("%s (%d)" % (rel, n))
    # Two consecutive forms of carbustrip.asp ("add" and "modify") each get the notice.
    return re.sub(r"(?is)<form\b.*?</form>", NOTICE_FORM, t)


def strip_counters(t):
    t = re.sub(r"(?is)<script[^>]*>(?:(?!</script>).)*cnxweb(?:(?!</script>).)*</script>\s*", "", t)
    t = re.sub(r"(?is)<noscript>(?:(?!</noscript>).)*cnxweb(?:(?!</noscript>).)*</noscript>\s*", "", t)
    return t


def strip_icq(t):
    """ICQ 'online' badge with the UIN of a visitor (dead mirabilis.com host)."""
    return re.sub(r'(?is)<a href="http://wwp\.mirabilis\.com/[^"]*">\s*<img [^>]*mirabilis[^>]*>\s*</a>\s*', "", t)


# E-mail addresses: shown in full, except when the local part is a family name (decided
# 2026-11-24): then the mailto link is dropped and the domain becomes ????. Local parts of nicks,
# first names and roles stay whole. Lower case.
FAMILY_LOCALS = {"nstefani", "etienne.jacques"}


def redact(t):
    def mailto(m):
        local = m.group(2).split("@")[0].lower()
        return "<a>" if local in FAMILY_LOCALS else m.group(0)
    t = re.sub(r'(?i)(<a\s+href\s*=\s*"?mailto:)([^">]*)("?\s*>)', lambda m: mailto(m), t)
    t = EMAIL.sub(lambda m: m.group(0) if m.group(1).lower() not in FAMILY_LOCALS else "%s@%s" % (m.group(1), MASK), t)
    for rx, rep in REDACT:
        t = rx.sub(rep, t)
    return t


def font_fallback(t):
    return re.sub(r'(?i)face="verdana"', 'face="Verdana, DejaVu Sans, Geneva, sans-serif"', t)


def self_links(t):
    """Absolute links to the site itself become relative."""
    t = re.sub(r'(?i)(href\s*=\s*")http://ltp\.ojuice\.net/?(")', r"\1index.asp\2", t)
    return re.sub(r'(?i)(href\s*=\s*")http://ltp\.ojuice\.net/', r"\1", t)


OJV3 = "https://orangejuicev3.sauthier.family"
NECTARINE = "https://nectarine.sauthier.family"


def ojuice_links(t):
    """Cross links to the dead www.ojuice.net: home -> Orange Juice v3, /nectarine -> Nectarine,
    skin flags -> local copies (OJv3 refuses cross-origin images). The /search/index.asp?s=... download links have
    no equivalent there and stay as they were."""
    t = re.sub(r'(?i)(href\s*=\s*")http://www\.ojuice\.net/nectarine/?(")', r"\1" + NECTARINE + r"/\2", t)
    t = re.sub(r'(?i)(href\s*=\s*")http://www\.ojuice\.net/?(")', r"\1" + OJV3 + r"/\2", t)
    t = re.sub(r'(?i)(src\s*=\s*"?)http://ojuice\.net/skins/tonic/pictures/flags/', r"\1images/flags/", t)
    return t


def fix_anchors(t):
    """Original bug: <a name="#old2"> (hash inside the name) never matched href="#old2"."""
    t = re.sub(r'(?i)(<a\s+name\s*=\s*")#', r"\1", t)
    return t.replace('href="#pc%20"', 'href="#pc"')   # 64.html: stray space in the anchor name


LINK_ATTR = re.compile(r"""(?i)\b(href|src|background)(\s*=\s*)("([^"]*)"|([^\s">]+))""")


def is_internal(v):
    return v and not re.match(r"(?i)^(?:[a-z][a-z0-9+.-]*:|//|#)", v)


def target_of(v, rel):
    path = v.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return None
    path = unquote(html.unescape(path), encoding=ENC)
    base = rel.rsplit("/", 1)[0] + "/" if "/" in rel else ""
    parts = []
    for seg in (base + path).split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    return "/".join(parts)


def rename_links(t, rel, published):
    def sub(m):
        attr, eq, _whole, q, bare = m.groups()
        v = q if q is not None else bare
        if not is_internal(v):
            return m.group(0)
        tgt = target_of(v, rel)
        if tgt in SOURCES and is_page(tgt):
            new = out_name(tgt)
            frag = "#" + v.split("#", 1)[1] if "#" in v else ""
            v = new + frag
        return '%s%s"%s"' % (attr, eq, v)
    return LINK_ATTR.sub(sub, t)


def placeholder(label, w=None, h=None):
    """A box of the size of the lost image (layout kept), with what it showed."""
    text = "[%s %s]" % (html.escape(label, quote=False), NOT_ARCHIVED_NOTE)
    if not (w and h):
        return '<font %s size="1" color="#996600">%s</font>' % (FONT, text)
    return ('<span style="display:inline-block;box-sizing:border-box;width:%spx;height:%spx;overflow:hidden;'
            'border:1px dotted #996600;font:9px Verdana,Arial,Helvetica,sans-serif;color:#996600;'
            'vertical-align:middle;text-align:center">%s</span>' % (w, h, text))


def drop_missing(t, rel, published, ctx):
    """Images never captured become a short text; links to missing files become plain text."""
    def img(m):
        tag = m.group(0)
        s = re.search(r"""(?i)\bsrc\s*=\s*(?:"([^"]*)"|([^\s">]+))""", tag)
        v = (s.group(1) if s.group(1) is not None else s.group(2)) if s else ""
        if not is_internal(v) or target_of(v, rel) in published:
            return tag
        tgt = target_of(v, rel)
        ctx["missing"].add(tgt)
        alt = re.search(r'(?i)\balt\s*=\s*"([^"]*)"', tag)
        stem = html.unescape(tgt.rsplit("/", 1)[-1].rsplit(".", 1)[0]).replace("_", " ")
        generic = ("", "Prizes", "Video", "Help", "Tshirts", "Moral support :)")
        if "pic/" in tgt:
            label = "photo: " + stem
        else:
            label = "logo: " + (alt.group(1) if alt and alt.group(1) not in generic else stem)
        w = re.search(r'(?i)\bwidth\s*=\s*"?(\d+)', tag)
        h = re.search(r'(?i)\bheight\s*=\s*"?(\d+)', tag)
        return placeholder(label, w and w.group(1), h and h.group(1))
    t = re.sub(r"(?i)<img\b[^>]*>", img, t)

    def anchor(m):
        open_tag, inner = m.group(1), m.group(2)
        h = re.search(r"""(?i)\bhref\s*=\s*(?:"([^"]*)"|([^\s">]+))""", open_tag)
        if not h:
            return m.group(0)
        v = h.group(1) if h.group(1) is not None else h.group(2)
        if not is_internal(v):
            return m.group(0)
        tgt = target_of(v, rel)
        if tgt is None or tgt in published:
            return m.group(0)
        ctx["missing"].add(tgt)
        if NOT_ARCHIVED_NOTE in inner:      # photo thumbnail already replaced
            return inner
        return inner + ' <font size="1">(%s)</font>' % NOT_ARCHIVED_NOTE
    return re.sub(r"(?is)(<a\b[^>]*>)(.*?)</a>", anchor, t)


def replace_applet(t):
    return re.sub(r"(?is)<applet\b.*?</applet>", NOTICE_APPLET, t)


def intro_page(t):
    """Flash intro: the mod player popup (popup.shtml) was never archived; Ruffle plays the SWF."""
    t = t.replace(" Onload=\"play('popup.shtml'); return true;\"", "")
    t = re.sub(r'(?is)\s*<SCRIPT language="JavaScript">\s*<!--\s*function play\(.*?</SCRIPT>', "", t)
    # The <object>/<embed> pair is replaced by a Ruffle player created from script: the browser
    # itself never tries to load a plugin (the CSP has object-src 'none'), Ruffle plays the SWF.
    player = ('<div id="ltpintro" style="width:740px;height:260px"></div>\n'
              '<script>window.addEventListener("load", function () {\n'
              '  var player = window.RufflePlayer.newest().createPlayer();\n'
              '  player.style.width = "740px"; player.style.height = "260px";\n'
              '  document.getElementById("ltpintro").appendChild(player);\n'
              '  player.ruffle().load({url: "img/ltpintro.swf", quality: "high", preferredRenderer: "canvas", backgroundColor: "#000000"});\n'
              '});</script>')
    t, n = re.subn(r"(?is)<object\b.*?</object>", lambda m: player, t)
    assert n == 1, "intro: flash object not found"
    # Mod player: the popup (popup.shtml, Modplug plugin) is gone; chiptune3 (libopenmpt) plays
    # the tune in the page, from the first click or key press (browsers block sound before).
    t, n = re.subn(r"Tune : Dis2them by Pink / Absys",
                   '<a href="music/dis2them.mod" id="tune">Tune : Dis2them by Pink / Absys</a><br>'
                   '<font size="1" id="tunehint">[click the page or press a key to hear the tune]</font>', t)
    assert n == 1, "intro: tune line not found"
    music = ('<script type="module">\n'
             'import { ChiptuneJsPlayer } from "./chiptune/chiptune3.js";\n'
             'const tune = document.getElementById("tune"), hint = document.getElementById("tunehint");\n'
             'let player = null, paused = false, skipClick = false;\n'
             'function say(m) { hint.textContent = "[" + m + "]"; }\n'
             'function start(e) {\n'
             '  if (player) return;\n'
             '  if (e && e.target.closest && e.target.closest("#tune")) skipClick = true;  // this gesture only starts it\n'
             '  say("loading the tune...");\n'
             '  player = new ChiptuneJsPlayer({ repeatCount: -1 });\n'
             '  player.onInitialized(() => { player.context.resume(); player.load("music/dis2them.mod"); say("playing: click the tune to pause"); });\n'
             '  player.onError(() => say("the tune cannot be played in this browser"));\n'
             '}\n'
             'addEventListener("pointerdown", start, { once: true });\n'
             'addEventListener("keydown", start, { once: true });\n'
             'tune.addEventListener("click", (e) => {\n'
             '  e.preventDefault();\n'
             '  if (skipClick) { skipClick = false; return; }\n'
             '  if (!player) return start();\n'
             '  paused = !paused; player.togglePause();\n'
             '  say(paused ? "paused: click the tune to resume" : "playing: click the tune to pause");\n'
             '});\n'
             '</script>\n')
    t = t.replace("</body>", music + "</body>", 1)
    t = t.replace('href="home.shtml"', 'href="index.asp"')
    ruffle = ('<script>window.RufflePlayer = window.RufflePlayer || {}; window.RufflePlayer.config = '
              '{"publicPath": "ruffle/", "polyfills": false, "preferredRenderer": "canvas", "autoplay": "on", "unmuteOverlay": "hidden", '
              '"splashScreen": false, "contextMenu": "off"};</script>\n'
              '<script src="ruffle/ruffle.js"></script>\n')
    return t.replace("</head>", ruffle + "</head>", 1)


# --------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--private", default=str(PRIVATE_DEFAULT), help="folder of the raw sources (outside git)")
    ap.add_argument("--out", default=str(REPO / "site"))
    ap.add_argument("--meta-dir", default=str(REPO / "build-meta"))
    a = ap.parse_args(argv)
    priv, out, meta = Path(a.private), Path(a.out), Path(a.meta_dir)

    missing_src = [s for s, _ in SOURCES.values() if not (priv / s).is_file()]
    ruffle_dir = priv / "vendor" / ("ruffle-%s" % RUFFLE_VERSION) / "package"
    chip_dir = priv / "vendor" / ("chiptune3-%s" % CHIPTUNE_VERSION) / "package"
    missing_src += [str(d) for d in (ruffle_dir, chip_dir) if not d.is_dir()]
    if missing_src:
        print("missing sources under %s:" % priv, *missing_src, sep="\n  ")
        return 2

    # 1. raw tree with the original names
    raw = priv / "site-raw"
    if raw.exists():
        shutil.rmtree(raw)
    for orig, (src, _note) in SOURCES.items():
        (raw / orig).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(priv / src, raw / orig)

    # 2. site/
    if out.exists():
        shutil.rmtree(out)
    published = {o for o in SOURCES}          # original names that exist (targets of links)
    ctx = {"forms": [], "missing": set()}
    rows, redirects = [], []
    for orig, (src, note) in SOURCES.items():
        new = out_name(orig) if is_page(orig) else orig
        rows.append((new, note))
        if not is_page(orig):
            (out / new).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(raw / orig, out / new)
            continue
        t = read_text(raw / orig)
        if orig == "intro.htm":
            t = intro_page(t)
        t = restyle_menu(t)
        t = strip_mailing_form(t)
        t = replace_forms(t, ctx, orig)
        t = strip_counters(t)
        t = strip_icq(t)
        t = replace_applet(t)
        t = redact(t)
        t = font_fallback(t)
        t = self_links(t)
        t = ojuice_links(t)
        t = fix_anchors(t)
        t = drop_missing(t, orig, published, ctx)
        t = rename_links(t, orig, published)
        write_text(out / new, add_removal_note(t) if is_people_page(new) else t)
        if new != orig:
            redirects.append(("/" + orig, "/" + new))

    # Ruffle (self-hosted Flash emulator): runtime files only, no source maps.
    rdir = out / "ruffle"
    rdir.mkdir(parents=True, exist_ok=True)
    for f in sorted(ruffle_dir.iterdir()):
        if f.suffix in (".js", ".wasm") or f.name.startswith("LICENSE"):
            name = f.name + ".txt" if f.name.startswith("LICENSE") else f.name
            shutil.copyfile(f, rdir / name)
            rows.append(("ruffle/" + name, "Ruffle %s (npm @ruffle-rs/ruffle)" % RUFFLE_VERSION))

    # chiptune3 (libopenmpt in WebAssembly, mod player of the intro): runtime files only.
    cdir = out / "chiptune"
    cdir.mkdir(parents=True, exist_ok=True)
    for f in sorted(chip_dir.iterdir()):
        if f.suffix == ".js" or f.name == "LICENSE":
            name = "LICENSE.txt" if f.name == "LICENSE" else f.name
            shutil.copyfile(f, cdir / name)
            rows.append(("chiptune/" + name, "chiptune3 %s (npm chiptune3)" % CHIPTUNE_VERSION))

    meta.mkdir(parents=True, exist_ok=True)
    (meta / "sources.tsv").write_text("".join("%s\t%s\n" % r for r in rows), encoding="utf-8")
    (meta / "redirects.tsv").write_text("".join("%s\t%s\n" % r for r in redirects), encoding="utf-8")
    (meta / "not-archived.txt").write_text("".join(sorted(m + "\n" for m in ctx["missing"])), encoding="utf-8")
    print("pages: %d, files: %d, forms replaced: %s" % (
        sum(1 for o in SOURCES if is_page(o)), sum(1 for p in out.rglob("*") if p.is_file()),
        ", ".join(ctx["forms"]) or "none"))
    print("targets never archived (links/images dropped): %d (build-meta/not-archived.txt)" % len(ctx["missing"]))
    # Crawlers and frames: sitemap.xml, robots.txt and the frame-restore script tag (scripts/seo.py).
    subprocess.run([sys.executable, "-I", str(REPO / "scripts" / "seo.py"), "--site", str(out)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
