/* ===================== GFA BASIC 3.x lister =====================
 * JavaScript port of gfalist / SKY, Copyright (C) 1992-2001 Peter Backes,
 * with later fixes by Markus Hoffmann and others (https://github.com/mmuman/gfalist).
 * That code is licensed under the GNU General Public License, version 2 only;
 * this section (token tables and gfaList/gfaLine) is a derived work under the same licence.
 * It comes with ABSOLUTELY NO WARRANTY. */
/*@@GFA_TABLES@@*/
const GFA_VST = ['#', '$', '%', '!', '#(', '$(', '%(', '!(', '&', '|', '', '', '&(', '|(', '', '$'];
const GFA_KIND = (() => {
  const m = new Map(), set = (codes, kind, arg) => { for (const c of codes) m.set(c, [kind, arg]); };
  set([456, 460, 464, 468], 'rem', 1); set([1644, 1016], 'rem', 0);
  set([192, 236, 420, 1020, 1072, 1108, 1128, 1136, 1140, 1144, 1236, 1276, 1300, 1364, 1416, 1420, 1592, 588, 1212, 1260], 'sp');
  set([124, 128, 132], 'next', 0); set([136, 140, 144], 'next', 2); set([148, 152, 156], 'next', 8); set([160, 164, 168], 'next', 9);
  set([304, 76, 80, 84, 256], 'veq', 0); set([308, 260], 'veq', 1); set([312, 88, 92, 96, 264], 'veq', 2); set([316, 268], 'veq', 3);
  set([320, 100, 104, 108, 272], 'veq', 8); set([324, 112, 116, 120, 276], 'veq', 9);
  set([328, 280, 656, 688, 720, 752, 784, 816], 'var', 4); set([332, 284], 'var', 5); set([336, 288, 660, 692, 724, 756, 788, 820], 'var', 6);
  set([340, 292], 'var', 7); set([344, 296, 664, 696, 728, 760, 792, 824], 'var', 12); set([348, 300, 668, 700, 732, 764, 796, 828], 'var', 13);
  set([240, 244, 248], 'var', 11); set([640, 672], 'var', 0); set([644, 676], 'var', 2); set([648, 680], 'var', 8); set([652, 684], 'var', 9);
  set([24, 216], 'proc', 11);
  set([704, 736, 768, 800], 'vcomma', 0); set([708, 740, 772, 804], 'vcomma', 2); set([712, 744, 776, 808], 'vcomma', 8); set([716, 748, 780, 812], 'vcomma', 9);
  set([4, 12, 16, 20, 32, 48, 56, 60, 64, 172, 176, 196, 200, 204, 208, 220, 224], 'skip4');
  return m;
})();
const GFA_OPEN = new Set([0, 8, 16, 24, 32, 40, 48, 76, 80, 84, 88, 92, 96, 100, 104, 108, 112, 116, 120, 176, 196, 200, 216]);
const GFA_CLOSE = new Set([4, 12, 20, 28, 36, 44, 52, 124, 128, 132, 136, 140, 144, 148, 152, 156, 160, 164, 168, 204, 208]);
const GFA_MID = new Set([56, 60, 64, 224, 252]);
const GFA_SKIP1 = new Set([46, 64, 68, 136, 137, 142, 144, 145, 146, 147, 148, 149, 150, 164, 165, 166, 169, 177, 178, 179, 180, 181, 197, 209, 210, 211, 212, 213, 214]);

/* Which kind of GFA BASIC file is this? null if it is not one. */
function gfaDetect(b) {
  if (b.length < 20 || (b[0] !== 0 && b[0] !== 0xFF)) return null;
  const mag = String.fromCharCode(...b.subarray(2, 12));
  if (mag === 'GFA-BASIC3') return { vers: b[1], prot: b[0] === 0xFF, ok: b[1] === 4 && b.length >= 166 };
  if (mag.startsWith('GfABASIC')) return { vers: b[1], prot: b[0] === 0xFF, ok: false };
  return null;
}

/* C printf("%G") with a chosen number of significant digits. */
function gfaNum(d, prec) {
  if (!isFinite(d)) return '?';
  if (d === 0) return '0';
  const e = parseInt(d.toExponential(prec - 1).split('e')[1], 10);
  const strip = s => s.indexOf('.') < 0 ? s : s.replace(/0+$/, '').replace(/\.$/, '');
  if (e < -4 || e >= prec) {
    const [m, x] = d.toExponential(prec - 1).split('e'), n = parseInt(x, 10);
    return strip(m) + 'E' + (n < 0 ? '-' : '+') + String(Math.abs(n)).padStart(2, '0');
  }
  return strip(d.toFixed(Math.max(0, prec - 1 - e)));
}
/* GFA 3 stores doubles with the exponent in the low 11 bits; rebuild the IEEE layout. */
function gfaDouble(b, o) {
  const s = i => (o + i < b.length ? b[o + i] : 0), d = new Uint8Array(8);
  for (let k = 2; k <= 7; k++) d[k] = ((s(k - 2) & 7) << 5) | (s(k - 1) >> 3);
  d[1] = ((s(0) & 0x78) >> 3) | ((s(7) << 4) & 0xFF);
  d[0] = ((s(6) & 7) << 4) | (s(7) >> 4);
  return new DataView(d.buffer).getFloat64(0);
}

/* Lists one tokenised line. Returns an array of bytes (Atari character set), or null for the end marker. */
function gfaLine(line, st) {
  const bot = line.length, dst = [];
  const at = i => (i < bot ? line[i] : 0);
  const str = s => { if (s) for (let i = 0; i < s.length; i++) dst.push(s.charCodeAt(i) & 255); };
  /* marks: flat list of [from, to, class] triples used only for colouring the listing */
  const marks = []; dst.marks = marks;
  const seg = (cls, from) => { if (dst.length > from) marks.push(from, dst.length, cls); };
  const tok = s => { const m = dst.length; str(s); if (s && /[A-Za-z]/.test(s)) seg('fn', m); };
  const pushVar = (t, v) => {
    const m = dst.length, name = st.prot ? null : (st.ident[t] || [])[v];
    if (name) for (const c of name) dst.push(c); else str('v' + t.toString(16).toUpperCase() + '_' + v.toString(16).toUpperCase());
    str(GFA_VST[t]);
    seg(t === 11 ? 'proc' : 'var', m);
  };
  const indent = n => { for (let i = 0; i < n; i++) dst.push(32, 32); };
  let src = 0;
  const lcp = (at(0) << 8) | at(1); src = 2;
  st.lcp = lcp;

  if (GFA_OPEN.has(lcp)) { indent(st.depth); st.depth++; }
  else if (lcp === 1796) indent(st.depth);            /* "> FUNCTION": GFA itself does not indent after it */
  else if (GFA_CLOSE.has(lcp)) { st.depth--; indent(st.depth); }
  else if (GFA_MID.has(lcp)) indent(st.depth - 1);
  else indent(st.depth);

  const m0 = dst.length;
  str(GFA_LCT[lcp >> 2]); seg('kw', m0);
  if (lcp === 180) return null;

  const kind = GFA_KIND.get(lcp);
  if (kind) {
    const [k, arg] = kind;
    const v16 = () => { const v = (at(src) << 8) | at(src + 1); src += 2; return v; };
    if (k === 'rem') {
      if (arg && at(src) !== 0x0D) dst.push(32);
      while (src < bot && line[src] !== 0x0D) dst.push(line[src++]);
      src++; src += src & 1;
      if (lcp === 456 || lcp === 460 || lcp === 464) { marks.length = 0; seg('rem', m0); } else if (lcp === 468) seg('str', marks.length ? marks[1] : m0);
    } else if (k === 'sp') { if (at(src) !== 0x46) dst.push(32); }
    else if (k === 'next') { src += 4; pushVar(arg, v16()); }
    else if (k === 'veq') { pushVar(arg, v16()); dst.push(0x3D); }
    else if (k === 'var') pushVar(arg, v16());
    else if (k === 'proc') { pushVar(arg, v16()); if (at(src) !== 0x46) dst.push(0x28); }
    else if (k === 'vcomma') { pushVar(arg, v16()); dst.push(0x2C); }
    else if (k === 'skip4') src += 4;
  }

  const i32 = () => { const v = ((at(src) << 24) | (at(src + 1) << 16) | (at(src + 2) << 8) | at(src + 3)); src += 4; return v; };
  const big = base => { const d = gfaDouble(line, src); src += 8; str(d >= 0 && isFinite(d) ? BigInt(Math.trunc(d)).toString(base).toUpperCase() : '0'); };
  while (src < bot) {
    const pft = line[src++];
    if (pft === 70) {
      src += src & 1;
      if (src >= bot) break;
      if (lcp !== 1668) {
        for (let i = line[src++]; i > 0; i--) dst.push(32);
        const m = dst.length;
        dst.push(0x21);
        let mrk = src; while (mrk < bot && line[mrk] !== 0x0D) mrk++;
        if (mrk < bot) { while (src < mrk) dst.push(line[src++]); src++; src += src & 1; } else src = mrk;
        seg('rem', m);
      } else { st.inline = bot - src; src = bot; }
    } else if (pft === 198 || pft === 199) {
      if (pft === 199) src++;
      const m = dst.length;
      dst.push(0x22);
      const mrk = src + 4; while (src < mrk && at(src) === 0) src++;
      while (src < mrk) dst.push(at(src++));
      dst.push(0x22); seg('str', m);
    } else if (pft === 208) tok(GFA_SFT[at(src++)]);
    else if (GFA_SKIP1.has(pft)) src++;
    else if (pft >= 200 && pft <= 221 || pft === 223) {
      const m = dst.length;
      if (pft === 200 || pft === 201) { if (pft === 201) src++; str(String(i32())); }
      else if (pft === 202 || pft === 203) { if (pft === 203) src++; str('&H' + (i32() >>> 0).toString(16).toUpperCase()); }
      else if (pft === 204 || pft === 205) { if (pft === 205) src++; str('&O' + (i32() >>> 0).toString(8)); }
      else if (pft === 206 || pft === 207) { if (pft === 207) src++; str('&X' + (i32() >>> 0).toString(2)); }
      else if (pft === 215 || pft === 216) { if (pft === 215) src++; str('&O'); big(8); }
      else if (pft === 217 || pft === 218) { if (pft === 217) src++; str('&X'); big(2); }
      else if (pft === 219 || pft === 220) { if (pft === 219) src++; str('&H'); big(16); }
      else if (pft === 221 || pft === 223) { if (pft === 221) src++; str(gfaNum(gfaDouble(line, src), st.prec)); src += 8; }
      else tok(GFA_PFT[pft]);
      if (pft !== 208 && (pft <= 207 || pft >= 215)) seg('num', m);
    } else if (pft === 222) {
      const m = dst.length;
      dst.push(0x22);
      for (let i = at(src++); i > 0 && src < bot; i--) { const c = line[src++]; dst.push(c); if (c === 0x22) dst.push(0x22); }
      dst.push(0x22); seg('str', m);
    } else if (pft >= 224 && pft <= 239) pushVar(pft - 224, at(src++));
    else if (pft >= 240) { const v = (at(src) << 8) | at(src + 1); src += 2; pushVar(pft - 240, v); }
    else tok(GFA_PFT[pft]);
  }
  return dst;
}

/* Lists a whole .GFA file. Returns { bytes, lines, prot } with CR LF line ends, or { error }. */
function gfaList(b, prec) {
  const info = gfaDetect(b);
  if (!info || !info.ok) return { error: 'Nepodporovaná verze souboru GFA BASIC.' };
  const sep = []; for (let i = 0; i < 38; i++) sep.push(u32be(b, 12 + i * 4));
  const base = 164, poolLen = sep[16] - sep[0], poolEnd = Math.min(b.length, base + poolLen);
  if (poolLen < 0 || base + poolLen > b.length) return { error: 'Hlavička souboru GFA je poškozená.' };
  const ident = []; let q = base;
  for (let t = 0; t < 16; t++) {
    const n = Math.max(0, Math.floor((sep[20 + t] - sep[19 + t]) / 4)), top = q, names = [];
    for (let j = 0; j < n && q < poolEnd; j++) {
      const name = [];
      for (let len = b[q++]; len > 0 && q < poolEnd; len--) { const c = b[q++]; name.push(c >= 0x41 && c <= 0x5A ? c + 32 : c); }
      names.push(name);
    }
    q += (q - top) & 1; ident.push(names);
  }
  const st = { ident, prot: info.prot, depth: 0, prec: prec || 13, inline: 0, lcp: 0 }, out = [], rows = [];
  const HEADS = new Set([24, 216, 40, 1796]);
  let lp = base + poolLen, remaining = sep[19] - sep[16], lines = 0;
  while (remaining > 0 && lp + 2 <= b.length && lines < 100000) {
    const size = u16be(b, lp); if (size < 2) break;
    remaining -= size;
    const line = b.subarray(lp + 2, Math.min(b.length, lp + size)); lp += size;
    st.inline = 0;
    let r; try { r = gfaLine(line, st); } catch (e) { r = [0x27, 0x20, 0x3F, 0x3F, 0x3F]; }
    if (r) { rows.push({ o: out.length, n: r.length, marks: r.marks || [], head: HEADS.has(st.lcp) }); for (const c of r) out.push(c); out.push(13, 10); lines++; }
    if (st.inline) { const s = "' ## INLINE: " + st.inline + ' Bytes'; rows.push({ o: out.length, n: s.length, marks: [0, s.length, 'rem'], head: false }); for (let i = 0; i < s.length; i++) out.push(s.charCodeAt(i)); out.push(13, 10); }
  }
  return { bytes: Uint8Array.from(out), lines, prot: info.prot, rows };
}
