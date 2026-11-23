# LTP4

**LTP4, before the party (August 2000).** LTP (Lucky & Tigrou Party) was a French demoparty
series organised by Orange Juice. LTP4, "the demomaker party", took place on 25-27 August 2000
at Espace René Fallet in Crosne (France). This is its website as visitors saw it before the
event: news, forum, how to come and reserve, competition rules and machines, sponsors.
The post-party version of the same site (results, report) is a separate archive, `LTP4-postparty`.

Archive of an old dynamic website (classic ASP and SSI on `ltp.ojuice.net`), published as a
**100 % static, read-only site** on bunny.net at the hostname of [`site.json`](site.json).
Kept online for history, no longer developed. Visitors can never write anything: the pages
are the cleaned, redacted static pages committed in `site/`, the CDN only serves files, and every
method except GET/HEAD/OPTIONS is refused at the edge.

## Layout

| Path | Content |
| --- | --- |
| `site/` | The cleaned, redacted static site, exactly as served (raw sources are kept outside git) |
| `hosting/404.html` | Custom 404 page, deployed next to `site/` |
| `site.json` | The only site-specific settings: repository, storage zone, pull zone, hostname, 404 page |
| `build-meta/` | Written by `statify.py`: source of every published file, old -> new URLs, files never archived |
| `infra/` | OpenTofu: storage zone, pull zone, hostname, hardening edge rules (state encrypted, committed) |
| `infra/secrets.env` | Proton Pass **references** to the secrets (vault `OldSites`), no secret values |
| `scripts/statify.py` | Raw sources (`private/`, outside git) -> cleaned `site/` (run locally) |
| `scripts/verify_build.py` | Checks `site/`: no ASP/SSI, forms, e-mails, phone numbers, counters, broken links |
| `scripts/check_excludes.py` | Fails if `site/` holds a path of `scripts/exclude-globs.txt` |
| `scripts/preview.py` | Local preview of `site/` with the CSP of the edge rules |
| `scripts/deploy.py` | Sync `site/` to the storage zone, purge the CDN |
| `scripts/smoke_test.py` | Check the public site: pages as in `site/`, POST refused, security headers, charset, 404 |
| `scripts/bootstrap.sh` | One-time setup (`new` for this site, `github` for the repository and secrets) |

DNS is not managed here: the hostname is a CNAME to `<pull zone>.b-cdn.net` at Infomaniak.

## Where the pages come from

The local archive of the site only holds its later, post-party state. The pre-party pages were
recovered from the **Wayback Machine** (raw `id_` captures, no toolbar), crawl of 2000-08-29
(the home page was also captured on 2000-08-17, an older version with fewer news; the
2000-08-29 one is published). The captures of October 2000 and later are the post-party site.
`build-meta/sources.tsv` gives the source of every published file.

| Page (original URL) | Source |
| --- | --- |
| `index.asp` (news), `forum.asp`, `carbustrip.asp` | Wayback 2000-08-29 |
| `information`, `legalinformation`, `financial`, `howtocome`, `howtoreserve`, `paid` `.shtml` | Wayback 2000-08-29 |
| `compomachines`, `comporules`, `sponsors`, `ltp2pic`, `ltp3pic`, `ltpeqx`, `ltpeqxm`, `64` `.shtml` | Wayback 2000-08-29 |
| `index.html` (Flash intro, site root) | Local archive, `ltp/http/img/index.htm` (2000-08-29) |

Pages are renamed to `.html` (`index.asp` -> `news.html`, `forum.asp` -> `forum.html`,
`howtocome.shtml` -> `howtocome.html`...; list in `build-meta/redirects.tsv`).

## What was changed from the original

- **Forms**: the forum question form and the two car-trip forms ("add your trip", "modify")
  are replaced by a short "archived, read-only" notice; the forum posts and car-trip offers
  stay. The mailing-list form of every page (hidden fields only, no visible input) is removed.
- **Counters**: the cnxweb.com counter of every page is removed.
- **Personal data redacted**, layout kept: e-mail addresses (`mailto:` links become plain
  text, addresses become `name@????`), the ICQ badge (with its number) of a car-trip offer,
  the street of the association's postal address (`????`, town kept) and the organisers' mobile
  numbers in the news (`+336????`). Handles and the names in the "entrance fee received" list are
  kept, as published at the time.
- **Images never archived** (neither by the Wayback Machine nor in the local archive) are shown as
  a dotted box of their original size saying what they were (`[photo: ... not archived]`): every
  photo of the LTP2 and LTP3 galleries (`ltp2pic/`, `ltp3pic/`), and the logos of the sponsors
  (Cyperus, Periscope, Supernova, prizes, Madeleines, Semaphora, Kalisto, Quantic Dream,
  Deliplayer, Utram). Links to files never archived become plain text marked "(not archived)":
  `screen.zip` (compo splash-screen program) and `jff-ltp3report.zip` (the Wayback copy of the
  LTP3 report is truncated, an unreadable zip). Full list: `build-meta/not-archived.txt`.
- **Taken from the local archive** because the Wayback Machine lacks them: `img/carte1b.jpg`,
  `img/carte2.jpg` (maps), `images/ltp4danfnl.jpg` (logo of the gallery pages, stored in `img/`
  locally), `ltpform.zip` (blank entrance order form), the Flash intro. `img/pano.jpg` (photo of
  the party place) was never captured: the local `img/panoram.jpg`, the same panorama of
  Espace René Fallet, is published under that name. `img/carte3.jpg` is the Wayback capture of
  2000-10-02 (byte-identical to the local copy).
- **Generated**: `images/hgo.gif` (top-left corner of the boxes, never captured) is the
  horizontal mirror of `images/hdo.gif`.
- **Java invitation** (`ltpeqx.html`, `ltpeqxm.html`): the applet `Troisd.jar` was never captured;
  a one-line notice replaces it.
- **Flash intro** (`index.html`, the site root): the original entry page of the site (Flash 4
  intro, mod player popup). It plays again with [Ruffle](https://ruffle.rs) 0.7.1, self-hosted in
  `site/ruffle/` (npm `@ruffle-rs/ruffle`, integrity checked, MIT/Apache-2.0 licences kept): the
  `<object>`/`<embed>` pair becomes a Ruffle player created from script (canvas renderer). The
  mod player popup (`popup.shtml`, Modplug plugin) was never archived: its `onload` call is
  removed and the tune plays in the page with [chiptune3](https://github.com/DrSnuggles/chiptune)
  0.8.11 (libopenmpt in WebAssembly, MIT, self-hosted in `site/chiptune/`), from the first click
  or key press (browsers block sound before; a one-line hint says so, and a click on the tune
  line pauses it). The tune, "Dis2them by Pink / Absys", is most likely *DisIsSid-theme 2* by
  Pink / Abyss (1994, 4-channel MOD, "Dis2them" being its 8.3 file name); it was never archived
  with the site and comes from Modland (`Protracker/Pink/disissid-2-theme.mod`, listed by
  Demozoo), published as `music/dis2them.mod`. In August 2000 the root already served the news
  (crawl of 2000-08-17); the intro is made the root again, "Enter" leads to `news.html`.
- **Left menu**: in the 2000-08-29 pages the menu had lost its fonts and colours (plain
  `<td>`/`<a>`: default serif font, orange body link colour, no space between sections). The
  markup of the 2000-08-17 capture is applied again (Verdana size 2, `#996600` links, white bold
  section titles, blank line after each section); the items of 2000-08-29 are kept.
- `face="Verdana"` gets sans-serif fallbacks (`DejaVu Sans, Geneva, sans-serif`).
- Links to `http://ltp.ojuice.net/...` become relative; other external links are left as they
  were (most hosts are dead).

## Regenerating `site/`

`site/` is generated: never edit it by hand, fix `scripts/statify.py` and regenerate. The raw
sources live in `private/` (git-ignored, keep that folder: it is the only assembled copy):

- `private/wayback/raw/<timestamp>/<path>`: Wayback captures, and the CDX listings
  `private/wayback/cdx-*.txt` (queries over 1999-2001 with `collapse=digest`);
- `private/nas/`: files copied from the local archive (`Sites web/ltp/http/`);
- `private/music/disissid-2-theme.mod` (Modland);
- `private/gen/hgo.gif`; `private/vendor/ruffle-0.7.1/`, `private/vendor/chiptune3-0.8.11-r25871/`
  (npm tarballs, unpacked).

```bash
python3 scripts/statify.py && python3 scripts/verify_build.py
```

Local preview with the CSP of the CDN (needed to check the Flash intro):

```bash
python3 scripts/preview.py 3227
```

## Security (`infra/main.tf`)

- Edge rule 1: any method other than GET, HEAD, OPTIONS is blocked at the edge, before the
  origin (bunny.net answers 403; edge rules cannot return 405). `block_post_requests` is also on.
- Edge rule 2: `Content-Security-Policy` (same-origin, inline script/style allowed for the 2000
  HTML, `wasm-unsafe-eval`, `connect-src 'self'` and `worker-src 'self' blob:` for Ruffle and the mod player,
  `object-src 'none'`, `form-action 'none'`), `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy`, HSTS, `Permissions-Policy`.
- Edge rules 3-4: `Content-Type` with `charset=iso-8859-1` for `.htm/.html/.shtml` and
  `.txt/.inc/.ini` (the pages are ISO-8859-1).
- Archives (`zip`): `application/octet-stream` + `Content-Disposition: attachment`.
- Browser cache 7 days for images, archives, `.swf`, `.wasm` and `.mod`, 1 hour for pages; CDN cache 30
  days, purged on each deployment. `.wasm` served as `application/wasm`.
- COOP/CORP `same-origin`. Search engines are allowed (no `X-Robots-Tag`, no `robots.txt`).
- CI (deploy workflow), before upload: excluded-paths check, `scripts/verify_build.py --build site`
  and a ClamAV scan of `site/`.
- Cookies are stripped before the origin; TLS "Compatible"; forced HTTPS.
- Custom 404: `hosting/404.html` (`not_found_page` in `site.json`).

## Deploying

- **Website**: push a change under `site/` or `hosting/` to `main` -> workflow *Website: deploy*
  runs the checks, uploads the changed files, deletes the removed ones, purges the CDN and
  runs the smoke test. A manual run allows a dry run. While the storage zone does not exist
  (before the first infra apply), it deploys nothing and only reports a notice.
- **Infra**: pull requests touching `infra/` show the plan; apply is a manual run of
  *Infra: bunny.net* (action `apply`, from `main`), which commits the encrypted state, deploys
  `site/` and runs the smoke test.

GitHub secrets: `BUNNY_API_KEY` (bunny.net account API key) and `TF_VAR_STATE_PASSPHRASE`
(state encryption), both from Proton Pass vault `OldSites`.

Locally (Proton Pass CLI logged in):

```bash
pass-cli run --env-file infra/secrets.env -- python3 scripts/deploy.py --dry-run
```

```bash
cd infra && pass-cli run --env-file secrets.env -- tofu plan
```

## First setup (done on 2026-11-23, kept as a record)

1. Write `site.json` and validate offline (secrets are the shared ones of the other old sites:
   same Proton Pass references, `OrangeJuice97-tofu-state-passphrase`), done on 2026-11-23:

   ```bash
   scripts/bootstrap.sh new LTP4 ltp4 ltp4 ltp4.sauthier.family
   ```

2. Create the GitHub repository and its secrets, push, open the PR (done on 2026-11-23):

   ```bash
   scripts/bootstrap.sh github
   ```

3. After merge, run the *Infra: bunny.net* workflow with action `apply` (done on 2026-11-23): it creates the zones,
   hostname and edge rules, deploys `site/` and runs the smoke test.
4. At Infomaniak (Manager > Domaines > sauthier.family > Zone DNS), add a CNAME (done on 2026-11-23)
   `ltp4` -> `ltp4.b-cdn.net`. The certificate is issued once DNS answers;
   re-run the smoke test (*Monitoring: weekly smoke test*, manual run) after a few minutes.

## Manual steps in the bunny.net dashboard (only if the apply cannot do it)

If the apply rejects an edge rule or the 404 path, set it by hand (CDN > pull zone `ltp4`):

1. *Edge rules* > *Add Edge Rule*: condition *Request Method* is none of `GET`, `HEAD`,
   `OPTIONS` -> action *Block Request*.
2. *Edge rules* > *Add Edge Rule*: condition *URL* `*` -> one *Set Response Header* action per
   header listed above (values in `infra/main.tf`, `local.csp` and the rule 2 block).
3. *Edge rules*: condition *URL Extension* `htm`, `html`, `shtml` -> *Set Response Header*
   `Content-Type: text/html; charset=iso-8859-1`.
4. Storage > storage zone `ltp4` > *Error pages*: set the 404 file to `/404.html`.
