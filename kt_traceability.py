#!/usr/bin/env python3
"""
Deterministic Service -> Fragment traceability matrix for Kotlin/Android codebases.

Evidence-only: every reported link is backed by a file path, a line number and the
exact symbol. Nothing is inferred from naming patterns. Anything that cannot be
proven from code is written as "-" in the matrix and logged in the Unresolved sheet.

Usage:
    python3 kt_traceability.py --root /path/to/kotlin/project --out matrix.xlsx

Structure (one function per search, build_flows is the only combiner):
    filter_files()
    extract_service_endpoints()
    map_service_to_usecase()
    map_service_to_repository()
    map_usecase_to_repository()
    map_usecase_to_viewmodel()
    map_repository_to_viewmodel()
    resolve_repository_entry_function()
    map_viewmodel_to_fragment()
    build_flows()
    export_excel()
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field

DASH = "-"

# --------------------------------------------------------------------------- #
# Step 0 configuration
# --------------------------------------------------------------------------- #

LAYER_SUFFIXES = [
    # (layer, suffix) -- order matters only for reporting; matching is exact & case-sensitive
    ("Service", "Service"),
    ("Repository", "Repository"),
    ("Repository", "RepoImpl"),
    ("Repository", "RepositoryImpl"),
    ("Repository", "Repo"),
    ("UseCase", "UseCase"),
    ("ViewModel", "ViewModel"),
    ("Fragment", "Fragment"),
    ("Activity", "Activity"),
]

EXCLUDED_PATH_PARTS = ("/test/", "/androidtest/", "/build/", "/generated/",
                       "/.git/", "/gen/", "/intermediates/")

IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
RETROFIT_ANNOTATIONS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HTTP", "HEAD", "OPTIONS")


# --------------------------------------------------------------------------- #
# Low-level Kotlin text handling
# --------------------------------------------------------------------------- #

def neutralize(text):
    """Return text of identical length with comment bodies and string contents
    replaced by spaces, so braces/parens inside them never affect scanning."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            out[i] = out[i + 1] = " "
            i += 2
            depth = 1
            while i < n and depth:
                if text[i] == "/" and i + 1 < n and text[i + 1] == "*":
                    out[i] = out[i + 1] = " "
                    i += 2
                    depth += 1
                elif text[i] == "*" and i + 1 < n and text[i + 1] == "/":
                    out[i] = out[i + 1] = " "
                    i += 2
                    depth -= 1
                else:
                    if text[i] != "\n":
                        out[i] = " "
                    i += 1
        elif text.startswith('"""', i):
            i += 3
            while i < n and not text.startswith('"""', i):
                if text[i] != "\n":
                    out[i] = " "
                i += 1
            i = min(n, i + 3)
        elif c == '"':
            i += 1
            while i < n and text[i] != '"' and text[i] != "\n":
                if text[i] == "\\":
                    out[i] = " "
                    i += 1
                    if i < n:
                        out[i] = " "
                        i += 1
                    continue
                out[i] = " "
                i += 1
            i = min(n, i + 1)
        elif c == "'":
            i += 1
            while i < n and text[i] != "'" and text[i] != "\n":
                if text[i] == "\\":
                    out[i] = " "
                    i += 1
                    if i < n:
                        out[i] = " "
                        i += 1
                    continue
                out[i] = " "
                i += 1
            i = min(n, i + 1)
        else:
            i += 1
    return "".join(out)


def match_pair(neutral, start, open_ch, close_ch):
    """Index just past the balanced close for the opener at `start`."""
    depth = 0
    i = start
    n = len(neutral)
    while i < n:
        if neutral[i] == open_ch:
            depth += 1
        elif neutral[i] == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def split_top_level(s, sep=","):
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch in "([<{":
            depth += 1
        elif ch in ")]>}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #

@dataclass
class KtFunction:
    name: str
    owner: str                 # class/interface/object name
    file: "KtFile"
    decl_line: int
    modifiers: tuple = ()
    body_start: int = -1       # char offsets into file text
    body_end: int = -1
    params_text: str = ""
    annotations: tuple = ()     # (name, args_text, line)

    @property
    def is_private(self):
        return "private" in self.modifiers

    @property
    def is_entry(self):
        if self.is_private:
            return False
        return "override" in self.modifiers or "suspend" in self.modifiers

    def body(self):
        if self.body_start < 0:
            return ""
        return self.file.neutral[self.body_start:self.body_end]


@dataclass
class KtClass:
    name: str
    kind: str                  # class | interface | object
    file: "KtFile"
    decl_line: int
    supertypes: tuple = ()
    ctor_params: tuple = ()     # (name, type, line)
    properties: tuple = ()      # (name, type, line, link_type, snippet)
    functions: list = field(default_factory=list)
    body_start: int = -1
    body_end: int = -1


@dataclass
class KtFile:
    path: str
    rel: str
    name: str                  # filename without .kt
    layer: str
    text: str = ""
    neutral: str = ""
    line_starts: tuple = ()
    imports: tuple = ()
    classes: list = field(default_factory=list)

    def line_of(self, offset):
        lo, hi = 0, len(self.line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    def snippet(self, line):
        try:
            raw = self.text.splitlines()[line - 1]
        except IndexError:
            return ""
        return " ".join(raw.split())[:300]


@dataclass
class Edge:
    """(source_file, source_function, target_file, target_function, file_path, line)

    Source = the upstream symbol being used. Target = the using (downstream) symbol.
    """
    source_file: str
    source_function: str
    target_file: str
    target_function: str
    file_path: str
    line: int
    source_class: str = ""
    target_class: str = ""
    link_type: str = "Direct call"
    snippet: str = ""
    direction: str = "downstream-calls-upstream"

    def key(self):
        return (self.source_file, self.source_function, self.source_class,
                self.target_file, self.target_function, self.target_class,
                self.file_path, self.line, self.link_type)


UNRESOLVED = []          # (item, type, file_path, line, reason)
EVIDENCE = []            # Edge-like evidence rows


def log_unresolved(item, kind, file_path, line, reason):
    row = (str(item), kind, file_path, line if line else "", reason)
    if row not in UNRESOLVED:
        UNRESOLVED.append(row)


def log_evidence(frm, to, link_type, file_path, line, snippet):
    row = (frm, to, link_type, file_path, line, snippet)
    if row not in EVIDENCE:
        EVIDENCE.append(row)


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

def _modifiers_before(neutral, fun_kw_offset):
    line_start = neutral.rfind("\n", 0, fun_kw_offset) + 1
    head = neutral[line_start:fun_kw_offset]
    for brk in ("}", "{", ";"):
        if brk in head:
            head = head.rsplit(brk, 1)[1]
    return tuple(t for t in re.split(r"[^A-Za-z]+", head) if t)


def _annotations_before(text, neutral, decl_offset):
    """Collect annotations on the lines directly above (and on) the declaration."""
    anns = []
    cursor = neutral.rfind("\n", 0, decl_offset) + 1
    # annotations on the same line, before the modifiers
    seg_start = cursor
    # walk upwards over contiguous annotation-only lines
    probe = cursor
    while probe > 0:
        prev_line_start = neutral.rfind("\n", 0, probe - 1) + 1
        line = neutral[prev_line_start:probe - 1].strip()
        if line.startswith("@"):
            seg_start = prev_line_start
            probe = prev_line_start
        else:
            break
    segment_neutral = neutral[seg_start:decl_offset]
    for m in re.finditer(r"@(" + IDENT + r")", segment_neutral):
        abs_at = seg_start + m.start()
        args = ""
        after = abs_at + m.end() - m.start()
        j = after
        while j < len(neutral) and neutral[j] in " \t":
            j += 1
        if j < len(neutral) and neutral[j] == "(":
            end = match_pair(neutral, j, "(", ")")
            if end > 0:
                args = text[j + 1:end - 1]
        anns.append((m.group(1), args, abs_at))
    return tuple(anns)


def _parse_functions(kf, cls, body_start, body_end):
    funcs = []
    neutral = kf.neutral
    for m in re.finditer(r"\bfun\b", neutral[body_start:body_end]):
        kw = body_start + m.start()
        # skip nested-function-in-function? keep all: ownership is the class.
        after = kw + 3
        mm = re.match(r"\s*(?:<[^>]*>\s*)?(?:" + IDENT + r"\s*\.\s*)?(" + IDENT + r")\s*\(",
                      neutral[after:after + 400])
        if not mm:
            continue
        name = mm.group(1)
        paren = after + neutral[after:after + 400].index("(", mm.end() - 1 - 0) \
            if False else after + mm.end() - 1
        pend = match_pair(neutral, paren, "(", ")")
        if pend < 0:
            continue
        params_text = kf.text[paren + 1:pend - 1]
        mods = _modifiers_before(neutral, kw)
        anns = _annotations_before(kf.text, neutral, kw)
        # locate body
        j = pend
        n = len(neutral)
        bstart = bend = -1
        while j < n and neutral[j] in " \t\r\n":
            j += 1
        if j < n and neutral[j] == ":":           # return type
            j += 1
            while j < n and neutral[j] not in "{=\n":
                if neutral[j] == "<":
                    k = match_pair(neutral, j, "<", ">")
                    j = k if k > 0 else j + 1
                    continue
                j += 1
            while j < n and neutral[j] in " \t\r\n":
                j += 1
        if j < n and neutral[j] == "{":
            bend = match_pair(neutral, j, "{", "}")
            bstart = j
        elif j < n and neutral[j] == "=":
            # expression body: until the next declaration at this level, or class end
            k = j + 1
            depth = 0
            while k < body_end:
                c = neutral[k]
                if c in "([{":
                    depth += 1
                elif c in ")]}":
                    if depth == 0:
                        break
                    depth -= 1
                elif c == "\n" and depth == 0:
                    tail = neutral[k + 1:k + 200]
                    if re.match(r"\s*(@|\}|(?:(?:public|private|internal|protected|override|"
                                r"suspend|open|abstract|final|inline|operator|external|"
                                r"infix|tailrec|annotation|companion|data|sealed)\s+)*"
                                r"(fun|val|var|class|object|interface)\b)", tail):
                        break
                k += 1
            bstart, bend = j, min(k, body_end)
        funcs.append(KtFunction(name=name, owner=cls, file=kf,
                                decl_line=kf.line_of(kw), modifiers=mods,
                                body_start=bstart, body_end=bend,
                                params_text=params_text, annotations=anns))
    return funcs


def _parse_properties(kf, body_start, body_end):
    props = []
    neutral = kf.neutral
    for m in re.finditer(r"\b(?:val|var)\s+(" + IDENT + r")\s*(?::\s*([^=\n{]+?))?\s*(=|by\b|\n)",
                         neutral[body_start:body_end]):
        off = body_start + m.start()
        line = kf.line_of(off)
        name = m.group(1)
        declared = (m.group(2) or "").strip()
        tail_start = body_start + m.start(3)
        tail = neutral[tail_start:neutral.find("\n", tail_start) if neutral.find("\n", tail_start) > 0 else body_end]
        decl_text = kf.snippet(line)
        link_type = None
        type_name = _bare_type(declared)
        if re.search(r"\bby\s+viewModels\s*(<|\()", tail) or re.search(r"\bby\s+viewModels", tail):
            link_type = "Delegation (by viewModels())"
        elif re.search(r"\bby\s+activityViewModels", tail):
            link_type = "Delegation (by activityViewModels())"
        elif re.search(r"\bby\s+navGraphViewModels", tail):
            link_type = "Delegation (by navGraphViewModels())"
        elif "hiltViewModel" in tail:
            link_type = "Delegation (hiltViewModel())"
        elif re.search(r"\bby\s+(inject|viewModel)\s*\(", tail):
            link_type = "Property injection (by inject())"
        elif "@Inject" in decl_text or "@Inject" in kf.snippet(max(1, line - 1)):
            link_type = "Property injection (@Inject)"
        if not type_name:
            g = re.search(r"<\s*(" + IDENT + r")\s*>", tail)
            if g:
                type_name = g.group(1)
        if type_name:
            props.append((name, type_name, line, link_type or "Property declaration", decl_text))
    # @Inject lateinit var
    for m in re.finditer(r"@Inject[\s\S]{0,80}?\b(?:lateinit\s+)?(?:val|var)\s+(" + IDENT +
                         r")\s*:\s*([^=\n]+)", neutral[body_start:body_end]):
        off = body_start + m.start()
        line = kf.line_of(off)
        t = _bare_type(m.group(2))
        if t:
            entry = (m.group(1), t, line, "Property injection (@Inject)", kf.snippet(line))
            props = [p for p in props if not (p[0] == entry[0] and p[2] == entry[2])] + [entry]
    return tuple(props)


def _bare_type(t):
    t = (t or "").strip().rstrip("?")
    if not t:
        return ""
    m = re.match(r"^(?:" + IDENT + r"\s*\.\s*)*(" + IDENT + r")", t)
    if not m:
        return ""
    base = m.group(1)
    # unwrap single generic wrappers e.g. Lazy<UserRepo>, Provider<X>
    g = re.match(r"^(?:" + IDENT + r"\s*\.\s*)*" + IDENT + r"\s*<\s*(" + IDENT + r")\s*>", t)
    if g and base in ("Lazy", "Provider", "Flow", "StateFlow", "LiveData", "Optional"):
        return g.group(1)
    return base


def parse_file(kf):
    kf.text = open(kf.path, "r", encoding="utf-8", errors="replace").read()
    kf.neutral = neutralize(kf.text)
    starts = [0]
    for i, ch in enumerate(kf.text):
        if ch == "\n":
            starts.append(i + 1)
    kf.line_starts = tuple(starts)
    kf.imports = tuple(re.findall(r"^\s*import\s+([\w.]+(?:\.\*)?)", kf.text, re.M))

    neutral = kf.neutral
    for m in re.finditer(r"\b(class|interface|object)\s+(" + IDENT + r")", neutral):
        kind, name = m.group(1), m.group(2)
        decl_off = m.start()
        if re.search(r"\bcompanion\s+$", neutral[max(0, decl_off - 20):decl_off]):
            continue
        cursor = m.end()
        ctor_params, supers = [], []
        # primary constructor
        j = cursor
        while j < len(neutral) and neutral[j] in " \t":
            j += 1
        if j < len(neutral) and neutral[j] == "<":
            k = match_pair(neutral, j, "<", ">")
            j = k if k > 0 else j
            while j < len(neutral) and neutral[j] in " \t":
                j += 1
        # skip constructor modifiers/annotations e.g. "@Inject constructor"
        k2 = j
        probe = neutral[j:j + 200]
        cm = re.match(r"((?:@" + IDENT + r"(?:\([^)]*\))?\s*|private\s*|internal\s*|"
                      r"protected\s*|public\s*|constructor\s*)*)\(", probe)
        if cm:
            k2 = j + cm.end() - 1
        if k2 < len(neutral) and neutral[k2] == "(":
            pend = match_pair(neutral, k2, "(", ")")
            if pend > 0:
                ptext = kf.text[k2 + 1:pend - 1]
                base_off = k2 + 1
                for part in split_top_level(ptext):
                    pm = re.search(r"\b(?:val|var)\s+(" + IDENT + r")\s*:\s*([^=]+)", part) or \
                        re.search(r"\b(" + IDENT + r")\s*:\s*([^=]+)", part)
                    if pm:
                        rel = ptext.find(pm.group(1) + ":")
                        if rel < 0:
                            rel = ptext.find(pm.group(1))
                        poff = base_off + (rel if rel >= 0 else 0)
                        ctor_params.append((pm.group(1), _bare_type(pm.group(2)),
                                            kf.line_of(poff)))
                cursor = pend
        # supertypes
        brace = neutral.find("{", cursor)
        colon = neutral.find(":", cursor)
        seg_end = brace if brace > 0 else len(neutral)
        nl2 = neutral.find("\n\n", cursor)
        if 0 < colon < seg_end:
            sup_text = kf.text[colon + 1:seg_end]
            for part in split_top_level(sup_text):
                t = _bare_type(part.split("(")[0])
                if t:
                    supers.append(t)
        bstart = bend = -1
        if brace > 0 and (nl2 < 0 or brace < nl2 + 2 or True):
            bend = match_pair(neutral, brace, "{", "}")
            bstart = brace
        cls = KtClass(name=name, kind=kind, file=kf, decl_line=kf.line_of(decl_off),
                      supertypes=tuple(supers), ctor_params=tuple(ctor_params),
                      body_start=bstart, body_end=bend if bend > 0 else len(neutral))
        if bstart > 0:
            cls.properties = _parse_properties(kf, cls.body_start, cls.body_end)
            cls.functions = _parse_functions(kf, name, cls.body_start, cls.body_end)
        kf.classes.append(cls)
    # drop nested classes' duplicated functions: keep outermost owner per offset
    return kf


# --------------------------------------------------------------------------- #
# filter_files  (Step 0)
# --------------------------------------------------------------------------- #

def filter_files(root):
    """Step 0 file filter. Returns the accepted KtFile list (parsed), sorted."""
    accepted = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        norm = ("/" + os.path.relpath(dirpath, root).replace(os.sep, "/") + "/").lower()
        if any(p in norm for p in EXCLUDED_PATH_PARTS):
            dirnames[:] = []
            continue
        for fn in sorted(filenames):
            if not fn.endswith(".kt"):
                continue
            stem = fn[:-3]
            layer = None
            for lay, suf in LAYER_SUFFIXES:
                if stem.endswith(suf) and stem != suf:
                    layer = lay
                    break
                if stem == suf:
                    layer = lay
                    break
            if layer is None:
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            if any(p in ("/" + rel.lower()) for p in EXCLUDED_PATH_PARTS):
                continue
            accepted.append(KtFile(path=path, rel=rel, name=stem, layer=layer))
    accepted.sort(key=lambda f: (f.layer, f.name, f.rel))
    for kf in accepted:
        parse_file(kf)
    return accepted


def all_kt_files(root):
    """Every .kt file (used ONLY to resolve URL constants via imports, per rule (b))."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        norm = ("/" + os.path.relpath(dirpath, root).replace(os.sep, "/") + "/").lower()
        if any(p in norm for p in EXCLUDED_PATH_PARTS):
            dirnames[:] = []
            continue
        for fn in sorted(filenames):
            if fn.endswith(".kt"):
                out.append(os.path.join(dirpath, fn))
    return out


# --------------------------------------------------------------------------- #
# Const index + URL resolution
# --------------------------------------------------------------------------- #

class ConstIndex:
    def __init__(self, root):
        self.by_file = {}        # path -> {name: (expr, line)}
        self.by_owner = {}       # ownerName -> {name: (expr, line, path)}
        self.global_ = {}        # name -> list of (expr, line, path)
        for path in all_kt_files(root):
            text = open(path, "r", encoding="utf-8", errors="replace").read()
            neutral = neutralize(text)
            starts = [0] + [i + 1 for i, c in enumerate(text) if c == "\n"]

            def line_of(off):
                lo, hi = 0, len(starts) - 1
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if starts[mid] <= off:
                        lo = mid
                    else:
                        hi = mid - 1
                return lo + 1

            owners = []
            for m in re.finditer(r"\b(?:object|class|interface)\s+(" + IDENT + r")", neutral):
                b = neutral.find("{", m.end())
                if b < 0:
                    continue
                e = match_pair(neutral, b, "{", "}")
                owners.append((m.group(1), b, e if e > 0 else len(neutral)))
            for m in re.finditer(r"\b(?:const\s+)?val\s+(" + IDENT + r")\s*(?::\s*String\s*)?=\s*([^\n]+)",
                                 neutral):
                name = m.group(1)
                expr = text[m.start(2):m.start(2) + len(m.group(2))].strip().rstrip(";")
                off, line = m.start(), line_of(m.start())
                self.by_file.setdefault(path, {})[name] = (expr, line)
                self.global_.setdefault(name, []).append((expr, line, path))
                for oname, b, e in owners:
                    if b < off < e:
                        self.by_owner.setdefault(oname, {})[name] = (expr, line, path)

    def lookup(self, name, same_file, imports, owner=None):
        if owner and owner in self.by_owner and name in self.by_owner[owner]:
            e, l, p = self.by_owner[owner][name]
            return e, l, p
        ff = self.by_file.get(same_file, {})
        if name in ff:
            e, l = ff[name]
            return e, l, same_file
        for imp in imports:
            segs = imp.split(".")
            if segs[-1] == name and len(segs) >= 2:
                o = segs[-2]
                if o in self.by_owner and name in self.by_owner[o]:
                    e, l, p = self.by_owner[o][name]
                    return e, l, p
            if segs[-1] == "*" and len(segs) >= 2:
                o = segs[-2]
                if o in self.by_owner and name in self.by_owner[o]:
                    e, l, p = self.by_owner[o][name]
                    return e, l, p
        cands = self.global_.get(name, [])
        if len(cands) == 1:
            e, l, p = cands[0]
            return e, l, p
        if len(cands) > 1:
            return None, None, "AMBIGUOUS"
        return None, None, None

    def resolve_expr(self, expr, same_file, imports, depth=0):
        """Returns (value_or_None, const_names, notes)."""
        names, parts_out, notes = [], [], []
        if depth > 6:
            return None, names, ["const recursion too deep"]
        for part in split_top_level(expr, "+"):
            part = part.strip()
            sm = re.fullmatch(r'"([^"]*)"', part)
            if sm:
                parts_out.append(sm.group(1))
                continue
            qm = re.fullmatch(r"(" + IDENT + r")\s*\.\s*(" + IDENT + r")", part)
            im = re.fullmatch(IDENT, part)
            if qm or im:
                owner = qm.group(1) if qm else None
                nm = qm.group(2) if qm else part
                e, l, p = self.lookup(nm, same_file, imports, owner=owner)
                if p == "AMBIGUOUS":
                    notes.append("const '%s' declared in multiple files" % nm)
                    names.append(nm)
                    return None, names, notes
                if e is None:
                    notes.append("const declaration for '%s' not found" % nm)
                    names.append(nm)
                    return None, names, notes
                names.append(nm)
                sub, subnames, subnotes = self.resolve_expr(e, p, imports, depth + 1)
                notes.extend(subnotes)
                for s in subnames:
                    if s not in names:
                        names.append(s)
                if sub is None:
                    return None, names, notes
                parts_out.append(sub)
                continue
            notes.append("expression part '%s' is not a literal or const" % part)
            return None, names, notes
        return "".join(parts_out), names, notes


# --------------------------------------------------------------------------- #
# extract_service_endpoints
# --------------------------------------------------------------------------- #

def extract_service_endpoints(files, const_index):
    """Service functions carrying a Retrofit annotation, with resolved URL + const names."""
    out = []
    for kf in [f for f in files if f.layer == "Service"]:
        for cls in kf.classes:
            for fn in cls.functions:
                ann = None
                for name, args, off in fn.annotations:
                    if name in RETROFIT_ANNOTATIONS:
                        ann = (name, args, off)
                        break
                if not ann:
                    continue
                method, args, off = ann
                line = kf.line_of(off)
                has_url_param = "@Url" in fn.params_text
                url_expr = args.strip()
                if method == "HTTP":
                    pm = re.search(r"path\s*=\s*([^,]+)", args)
                    url_expr = pm.group(1).strip() if pm else ""
                    if not pm:
                        pos = split_top_level(args)
                        url_expr = pos[1].strip() if len(pos) > 1 else ""
                if has_url_param:
                    url, consts = "Dynamic (@Url)", DASH
                    log_evidence("%s.%s" % (cls.name, fn.name), "Dynamic (@Url)",
                                 "Retrofit @%s + @Url" % method, kf.rel, line, kf.snippet(line))
                elif not url_expr:
                    url, consts = "Unresolved", DASH
                    log_evidence("%s.%s" % (cls.name, fn.name), "Unresolved URL",
                                 "Retrofit @%s" % method, kf.rel, line, kf.snippet(line))
                    log_unresolved("%s.%s" % (kf.name, fn.name), "Unresolved const", kf.rel, line,
                                   "@%s has no path argument" % method)
                else:
                    value, names, notes = const_index.resolve_expr(url_expr, kf.path, kf.imports)
                    if value is None:
                        url = "Unresolved"
                        consts = ", ".join(names) if names else DASH
                        log_evidence("%s.%s" % (cls.name, fn.name), "Unresolved URL",
                                     "Retrofit @%s" % method, kf.rel, line, kf.snippet(line))
                        log_unresolved("%s.%s -> @%s(%s)" % (kf.name, fn.name, method, url_expr),
                                       "Unresolved const", kf.rel, line,
                                       "; ".join(notes) or "could not resolve path expression")
                    else:
                        url = value
                        consts = ", ".join(names) if names else DASH
                        log_evidence("%s.%s" % (cls.name, fn.name), url,
                                     "Retrofit @%s" % method, kf.rel, line, kf.snippet(line))
                out.append({
                    "service_file": kf.name + ".kt",
                    "service_rel": kf.rel,
                    "service_class": cls.name,
                    "function": fn.name,
                    "method": method,
                    "url": url,
                    "url_const": consts,
                    "line": line,
                })
    out.sort(key=lambda r: (r["service_file"], r["function"], r["line"]))
    return out


# --------------------------------------------------------------------------- #
# Shared call-search helper (used by one mapping function each)
# --------------------------------------------------------------------------- #

def _class_index(files):
    idx = {}
    for kf in files:
        for cls in kf.classes:
            idx.setdefault(cls.name, []).append(cls)
    return idx


def _impl_index(files, layer):
    """interfaceName -> [implementing classes in the same layer]"""
    out = {}
    for kf in [f for f in files if f.layer == layer]:
        for cls in kf.classes:
            for sup in cls.supertypes:
                out.setdefault(sup, []).append(cls)
    return out


def _bindings(cls):
    """name -> (type, line, link_type, snippet) proven by injection or delegation."""
    b = {}
    for pname, ptype, pline in cls.ctor_params:
        if ptype:
            b[pname] = (ptype, pline, "Constructor injection", cls.file.snippet(pline))
    for pname, ptype, pline, link, snip in cls.properties:
        if ptype:
            b[pname] = (ptype, pline, link, snip)
    return b


def _find_calls(caller_files, callee_files, link_label):
    """Generic one-search engine: proven bindings + cited call sites.

    Returns a list of Edge (source = callee/upstream, target = caller/downstream).
    """
    callee_classes = {}
    for kf in callee_files:
        for cls in kf.classes:
            callee_classes[cls.name] = cls
    impls = {}
    for kf in callee_files:
        for cls in kf.classes:
            for sup in cls.supertypes:
                if sup in callee_classes:
                    impls.setdefault(sup, []).append(cls)
    edges = []
    for kf in caller_files:
        for cls in kf.classes:
            binds = _bindings(cls)
            used = set()
            for inst, (tname, bline, link, snip) in sorted(binds.items()):
                if tname not in callee_classes:
                    continue
                decl_cls = callee_classes[tname]
                targets = [decl_cls]
                impl_list = impls.get(tname, [])
                if decl_cls.kind == "interface":
                    if len(impl_list) == 1:
                        targets = [impl_list[0], decl_cls]
                    elif len(impl_list) > 1:
                        log_unresolved(
                            "%s -> %s" % (cls.name, tname), "Ambiguous binding", kf.rel, bline,
                            "interface %s has %d implementations in scope (%s); cannot prove "
                            "which one %s uses" % (tname, len(impl_list),
                                                   ", ".join(sorted(c.name for c in impl_list)),
                                                   cls.name))
                        continue
                callee_funcs = {}
                for t in targets:
                    for f in t.functions:
                        callee_funcs.setdefault(f.name, []).append(f)
                for caller_fn in cls.functions:
                    body = caller_fn.body()
                    if not body:
                        continue
                    for m in re.finditer(r"\b" + re.escape(inst) + r"\s*(?:\?)?\s*\.\s*(" +
                                         IDENT + r")\s*\(", body):
                        fname = m.group(1)
                        if fname not in callee_funcs:
                            continue
                        off = caller_fn.body_start + m.start()
                        cline = kf.line_of(off)
                        src = sorted(callee_funcs[fname],
                                     key=lambda f: (f.body_start < 0, f.file.rel, f.decl_line))[0]
                        edges.append(Edge(
                            source_file=src.file.name + ".kt", source_function=fname,
                            target_file=kf.name + ".kt", target_function=caller_fn.name,
                            file_path=kf.rel, line=cline,
                            source_class=src.owner, target_class=cls.name,
                            link_type="Direct call", snippet=kf.snippet(cline)))
                        log_evidence("%s.%s" % (src.owner, fname),
                                     "%s.%s" % (cls.name, caller_fn.name),
                                     "Direct call", kf.rel, cline, kf.snippet(cline))
                        log_evidence("%s" % tname, "%s.%s" % (cls.name, inst),
                                     link, kf.rel, bline, snip)
                        used.add(inst)
                if inst not in used:
                    log_unresolved(
                        "%s.%s : %s" % (cls.name, inst, tname), "Unresolved link", kf.rel, bline,
                        "%s is injected into %s but no call to one of its functions was found "
                        "in %s (%s)" % (tname, cls.name, kf.name + ".kt", link_label))
    uniq, seen = [], set()
    for e in sorted(edges, key=lambda e: e.key()):
        if e.key() not in seen:
            seen.add(e.key())
            uniq.append(e)
    return uniq


# --------------------------------------------------------------------------- #
# One function per search
# --------------------------------------------------------------------------- #

def map_service_to_usecase(files):
    return _find_calls([f for f in files if f.layer == "UseCase"],
                       [f for f in files if f.layer == "Service"], "Service -> UseCase")


def map_service_to_repository(files):
    return _find_calls([f for f in files if f.layer == "Repository"],
                       [f for f in files if f.layer == "Service"], "Service -> Repository")


def map_usecase_to_repository(files):
    uc = [f for f in files if f.layer == "UseCase"]
    repo = [f for f in files if f.layer == "Repository"]
    edges = []
    for e in _find_calls(repo, uc, "UseCase -> Repository"):
        e.direction = "repository-calls-usecase"
        edges.append(e)
    for e in _find_calls(uc, repo, "Repository -> UseCase"):
        e.direction = "usecase-calls-repository"
        edges.append(e)
    return sorted(edges, key=lambda e: (e.direction,) + e.key())


def map_usecase_to_viewmodel(files):
    return _find_calls([f for f in files if f.layer == "ViewModel"],
                       [f for f in files if f.layer == "UseCase"], "UseCase -> ViewModel")


def map_repository_to_viewmodel(files):
    return _find_calls([f for f in files if f.layer == "ViewModel"],
                       [f for f in files if f.layer == "Repository"], "Repository -> ViewModel")


def map_viewmodel_to_fragment(files):
    frag = _find_calls([f for f in files if f.layer == "Fragment"],
                       [f for f in files if f.layer == "ViewModel"], "ViewModel -> Fragment")
    act = _find_calls([f for f in files if f.layer == "Activity"],
                      [f for f in files if f.layer == "ViewModel"], "ViewModel -> Activity")
    vm_with_fragment = {e.source_class for e in frag}
    for e in act:
        if e.source_class not in vm_with_fragment:
            log_unresolved("%s.%s -> %s" % (e.source_class, e.source_function, e.target_class),
                           "Unresolved link", e.file_path, e.line,
                           "ViewModel function is used by an Activity, not a Fragment; the "
                           "matrix has no Activity columns so this path has no Fragment cell")
    return frag


def resolve_repository_entry_function(files, repo_edge):
    """Repository public-entry rule: a private function never appears in the matrix.

    Walks up callers inside the same Repository class until an `override fun` or
    `suspend fun` is reached. Returns (function_name, evidence_line) or (None, None).
    """
    cls = None
    for kf in [f for f in files if f.layer == "Repository"]:
        for c in kf.classes:
            if c.name == repo_edge.target_class and kf.name + ".kt" == repo_edge.target_file:
                cls = c
                break
    if cls is None:
        return None, None
    fns = {f.name: f for f in cls.functions}
    start = fns.get(repo_edge.target_function)
    if start is None:
        return None, None
    if not start.is_private:
        if start.is_entry:
            return start.name, start.decl_line
        # public but neither override nor suspend: still a public entry point
        return start.name, start.decl_line
    seen, frontier = {start.name}, [start.name]
    while frontier:
        nxt = []
        for cur in sorted(frontier):
            for f in sorted(cls.functions, key=lambda x: (x.decl_line, x.name)):
                if f.name in seen:
                    continue
                body = f.body()
                if not body:
                    continue
                if re.search(r"(?<![\w.])" + re.escape(cur) + r"\s*\(", body):
                    if f.is_entry:
                        off = body.find(cur)
                        cline = cls.file.line_of(f.body_start + max(off, 0))
                        log_evidence("%s.%s (private)" % (cls.name, cur),
                                     "%s.%s (entry)" % (cls.name, f.name),
                                     "Private -> entry walk-up", cls.file.rel, cline,
                                     cls.file.snippet(cline))
                        return f.name, cline
                    seen.add(f.name)
                    nxt.append(f.name)
        frontier = nxt
    log_unresolved("%s.%s" % (cls.name, repo_edge.target_function), "No override-suspend entry",
                   cls.file.rel, start.decl_line,
                   "upstream call sits in a private function and no override/suspend function in "
                   "the same class reaches it")
    return None, None


# --------------------------------------------------------------------------- #
# build_flows -- the ONLY place edges are combined
# --------------------------------------------------------------------------- #

def build_flows(files, endpoints, svc_uc, svc_repo, uc_repo, uc_vm, repo_vm, vm_frag):
    """Walks every proven chain from each Service function.

    Returns (rows, broken):
      rows   -- complete Pattern A / B / C paths (Traceability Matrix)
      broken -- every dead end: only proven cells are filled, the rest is "-",
                with the layer where the chain stopped and the missing link.
    """
    rows, broken = [], []
    ep_by = {}
    for ep in endpoints:
        ep_by.setdefault((ep["service_file"], ep["function"]), ep)

    def repo_entry(edge):
        return resolve_repository_entry_function(files, edge)

    def frag_edges(vm_cls, vm_fn):
        return [e for e in vm_frag if e.source_class == vm_cls and e.source_function == vm_fn]

    def dead_end(ep, possible, stopped_at, missing, where, **cells):
        r = _row(ep, DASH, **{k: cells.get(k, DASH) for k in (
            "uc_file", "uc_fn", "repo_name", "repo_fn", "vm", "vm_fn", "vm_src", "frag", "frag_fn")})
        del r["Pattern"]
        r["Possible Pattern"] = possible
        r["Stopped At"] = stopped_at
        r["Missing Link"] = missing
        r["_names"] = cells.get("names", ())
        r["_types"] = cells.get("types", None)
        broken.append(r)
        log_unresolved("%s.%s -> stopped at %s" % (ep["service_file"], ep["function"], stopped_at),
                       "Unresolved link", where[0], where[1], missing)

    supers = {}
    for kf in files:
        for c in kf.classes:
            supers.setdefault(c.name, set()).update(c.supertypes)

    def _with_supers(cls_name):
        return tuple(sorted({cls_name} | supers.get(cls_name, set())))

    for key, ep in sorted(ep_by.items()):
        svc_file, svc_fn = key
        here = (ep["service_rel"], ep["line"])
        uc_hits = [e for e in svc_uc if e.source_file == svc_file and e.source_function == svc_fn]
        repo_hits = [e for e in svc_repo if e.source_file == svc_file and e.source_function == svc_fn]

        if not uc_hits and not repo_hits:
            dead_end(ep, "A / B / C", "Service",
                     "no proven UseCase or Repository function calls %s.%s" % (ep["service_class"], svc_fn),
                     here, names=("%s.%s" % (ep["service_class"], svc_fn),))

        # ---- UseCase branch: Pattern A and Pattern B
        for e1 in uc_hits:
            uc = dict(uc_file=e1.target_file, uc_fn=e1.target_function)
            at_uc = (e1.file_path, e1.line)
            a_hits = [e for e in uc_repo
                      if (e.direction == "repository-calls-usecase" and e.source_file == e1.target_file
                          and e.source_function == e1.target_function)
                      or (e.direction == "usecase-calls-repository" and e.target_file == e1.target_file
                          and e.target_function == e1.target_function)]
            b_hits = [e for e in uc_vm if e.source_file == e1.target_file
                      and e.source_function == e1.target_function]
            if not a_hits and not b_hits:
                dead_end(ep, "A / B", "UseCase",
                         "no proven Repository or ViewModel function uses %s.%s"
                         % (e1.target_class, e1.target_function), at_uc,
                         names=("%s.%s" % (e1.target_class, e1.target_function),), **uc)

            # Pattern A: Service > UseCase > Repository > ViewModel > Fragment
            for e2 in a_hits:
                if e2.direction == "repository-calls-usecase":
                    repo_cls, repo_edge = e2.target_class, e2
                else:
                    repo_cls = e2.source_class
                    repo_edge = Edge(source_file=e2.source_file, source_function=e2.source_function,
                                     target_file=e2.source_file, target_function=e2.source_function,
                                     file_path=e2.file_path, line=e2.line,
                                     source_class=e2.source_class, target_class=e2.source_class)
                entry_fn, _ = repo_entry(repo_edge)
                if entry_fn is None:
                    dead_end(ep, "A", "Repository",
                             "%s.%s is private and no override/suspend function in %s reaches it"
                             % (repo_cls, repo_edge.target_function, repo_cls),
                             (e2.file_path, e2.line), repo_name=repo_cls, **uc,
                             names=("%s.%s" % (repo_cls, repo_edge.target_function),))
                    continue
                rp = dict(repo_name=repo_cls, repo_fn=entry_fn)
                vm_hits = [e for e in repo_vm if e.source_class == repo_cls
                           and e.source_function == entry_fn]
                if not vm_hits:
                    dead_end(ep, "A", "Repository",
                             "no proven ViewModel function calls %s.%s" % (repo_cls, entry_fn),
                             (e2.file_path, e2.line), **uc, **rp,
                             names=_with_supers(repo_cls), types=BINDING_TYPES)
                for e3 in vm_hits:
                    vm = dict(vm=e3.target_class, vm_fn=e3.target_function, vm_src=repo_cls)
                    f_hits = frag_edges(e3.target_class, e3.target_function)
                    if not f_hits:
                        dead_end(ep, "A", "ViewModel",
                                 "no proven Fragment function calls %s.%s"
                                 % (e3.target_class, e3.target_function),
                                 (e3.file_path, e3.line), **uc, **rp, **vm,
                                 names=("%s.%s" % (e3.target_class, e3.target_function),))
                    for e4 in f_hits:
                        rows.append(_row(ep, "A", frag=e4.target_class, frag_fn=e4.target_function,
                                         **uc, **rp, **vm))

            # Pattern B: Service > UseCase > ViewModel > Fragment
            for e2 in b_hits:
                vm = dict(vm=e2.target_class, vm_fn=e2.target_function, vm_src=e2.source_class)
                f_hits = frag_edges(e2.target_class, e2.target_function)
                if not f_hits:
                    dead_end(ep, "B", "ViewModel",
                             "no proven Fragment function calls %s.%s"
                             % (e2.target_class, e2.target_function),
                             (e2.file_path, e2.line), **uc, **vm,
                             names=("%s.%s" % (e2.target_class, e2.target_function),))
                for e3 in f_hits:
                    rows.append(_row(ep, "B", repo_name=DASH, repo_fn=DASH,
                                     frag=e3.target_class, frag_fn=e3.target_function, **uc, **vm))

        # ---- Pattern C: Service > Repository > ViewModel > Fragment
        for e1 in repo_hits:
            entry_fn, _ = repo_entry(e1)
            if entry_fn is None:
                dead_end(ep, "C", "Repository",
                         "%s.%s is private and no override/suspend function in %s reaches it"
                         % (e1.target_class, e1.target_function, e1.target_class),
                         (e1.file_path, e1.line), repo_name=e1.target_class,
                         names=("%s.%s" % (e1.target_class, e1.target_function),))
                continue
            rp = dict(repo_name=e1.target_class, repo_fn=entry_fn)
            vm_hits = [e for e in repo_vm if e.source_class == e1.target_class
                       and e.source_function == entry_fn]
            if not vm_hits:
                dead_end(ep, "C", "Repository",
                         "no proven ViewModel function calls %s.%s" % (e1.target_class, entry_fn),
                         (e1.file_path, e1.line), **rp,
                         names=_with_supers(e1.target_class), types=BINDING_TYPES)
            for e2 in vm_hits:
                vm = dict(vm=e2.target_class, vm_fn=e2.target_function, vm_src=e1.target_class)
                f_hits = frag_edges(e2.target_class, e2.target_function)
                if not f_hits:
                    dead_end(ep, "C", "ViewModel",
                             "no proven Fragment function calls %s.%s"
                             % (e2.target_class, e2.target_function),
                             (e2.file_path, e2.line), **rp, **vm,
                             names=("%s.%s" % (e2.target_class, e2.target_function),))
                for e3 in f_hits:
                    rows.append(_row(ep, "C", uc_file=DASH, uc_fn=DASH,
                                     frag=e3.target_class, frag_fn=e3.target_function, **rp, **vm))

    # Related Unresolved: entries whose Item names the exact symbol where the chain stopped
    # (or, for a Repository nobody calls, a binding problem on that class or its interface).
    for r in broken:
        names, types = r.pop("_names"), r.pop("_types")
        related = sorted({"%s: %s" % (u[1], u[0]) for u in UNRESOLVED
                          if "stopped at" not in u[0]
                          and (types is None or u[1] in types)
                          and any(re.search(r"(?<![\w.])%s(?![\w])" % re.escape(n), u[0])
                                  for n in names)})
        r["Related Unresolved"] = "; ".join(related) if related else DASH

    def dedup(items, cols):
        out, seen = [], set()
        for r in items:
            k = tuple(r[c] for c in cols)
            if k not in seen:
                seen.add(k)
                out.append(r)
        return out

    sort_key = lambda r: (r["Service Filename"], r["Service Function"], r["ViewModel Name"],
                          r["UseCase Filename"], r["UseCase Function"], r["Repository Name"],
                          r["Repository Function"], r["ViewModel Function"],
                          r["Fragment Name"], r["Fragment Function"], r["URL"])
    rows = sorted(dedup(rows, COLUMNS), key=sort_key)
    broken = sorted(dedup(broken, BROKEN_COLUMNS), key=lambda r: sort_key(r) + (r["Stopped At"],))
    return rows, broken


COLUMNS = ["Service Filename", "URL", "URL Const", "Service Function",
           "UseCase Filename", "UseCase Function", "Repository Name", "Repository Function",
           "ViewModel Name", "ViewModel Function", "ViewModel Function Source Name",
           "Fragment Name", "Fragment Function", "Pattern"]

BINDING_TYPES = ("Ambiguous binding", "Unresolved link")

BROKEN_COLUMNS = [c for c in COLUMNS if c != "Pattern"] + [
    "Possible Pattern", "Stopped At", "Missing Link", "Related Unresolved"]


def _row(ep, pattern, uc_file=DASH, uc_fn=DASH, repo_name=DASH, repo_fn=DASH, vm=DASH, vm_fn=DASH,
         vm_src=DASH, frag=DASH, frag_fn=DASH):
    return {
        "Service Filename": ep["service_file"],
        "URL": ep["url"],
        "URL Const": ep["url_const"],
        "Service Function": ep["function"],
        "UseCase Filename": uc_file,
        "UseCase Function": uc_fn,
        "Repository Name": repo_name,
        "Repository Function": repo_fn,
        "ViewModel Name": vm,
        "ViewModel Function": vm_fn,
        "ViewModel Function Source Name": vm_src,
        "Fragment Name": frag,
        "Fragment Function": frag_fn,
        "Pattern": pattern,
    }


# --------------------------------------------------------------------------- #
# Final check + export
# --------------------------------------------------------------------------- #

def final_check(files, rows, broken=()):
    problems = []
    every = list(rows) + list(broken)
    allowed = {f.name + ".kt" for f in files} | {f.name for f in files}
    for r in every:
        for col in ("Service Filename", "UseCase Filename"):
            v = r[col]
            if v != DASH and v not in allowed:
                problems.append("row references non-filtered file: %s=%s" % (col, v))
        if r.get("Pattern") == "A" and (r["UseCase Filename"] == DASH or r["Repository Name"] == DASH):
            problems.append("Pattern A row missing UseCase or Repository: %s" % r)
        if r.get("Pattern") == "B" and r["Repository Name"] != DASH:
            problems.append("Pattern B row has a Repository: %s" % r)
        if r.get("Pattern") == "C" and r["UseCase Filename"] != DASH:
            problems.append("Pattern C row has a UseCase: %s" % r)
    # no private repository function
    privates = set()
    for kf in [f for f in files if f.layer == "Repository"]:
        for c in kf.classes:
            for fn in c.functions:
                if fn.is_private:
                    privates.add((c.name, fn.name))
    for r in every:
        if (r["Repository Name"], r["Repository Function"]) in privates:
            problems.append("private repository function reported: %s.%s"
                            % (r["Repository Name"], r["Repository Function"]))
    # every non-dash symbol cell backed by evidence
    ev_blob = "\n".join("%s|%s|%s" % (e[0], e[1], e[2]) for e in EVIDENCE)
    for r in every:
        for col in ("Service Function", "UseCase Function", "Repository Function",
                    "ViewModel Function", "Fragment Function"):
            v = r[col]
            if v != DASH and v and v not in ev_blob:
                problems.append("cell not backed by Evidence: %s=%s" % (col, v))
    return problems


def export_excel(out_path, filtered, rows, endpoints, broken=()):
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="31506E")

    def write(ws, header, data):
        ws.append(header)
        for c in ws[1]:
            c.font = head_font
            c.fill = head_fill
            c.alignment = Alignment(vertical="center")
        for row in data:
            ws.append(row)
        ws.freeze_panes = "A2"
        for i, h in enumerate(header, start=1):
            width = max([len(str(h))] + [len(str(r[i - 1])) for r in data] or [0]) + 2
            ws.column_dimensions[get_column_letter(i)].width = min(max(width, 10), 60)
        if data:
            ws.auto_filter.ref = ws.dimensions

    ws1 = wb.active
    ws1.title = "Traceability Matrix"
    write(ws1, COLUMNS, [[r[c] for c in COLUMNS] for r in rows])

    ws_b = wb.create_sheet("Broken Paths")
    write(ws_b, BROKEN_COLUMNS, [[r[c] for c in BROKEN_COLUMNS] for r in broken])

    ws2 = wb.create_sheet("Evidence")
    write(ws2, ["Row #", "From", "To", "Link Type", "File Path", "Line", "Code Snippet"],
          [[i] + list(e) for i, e in enumerate(sorted(EVIDENCE), start=1)])

    ws3 = wb.create_sheet("Unresolved")
    write(ws3, ["Item", "Type", "File Path", "Line", "Reason"], sorted(UNRESOLVED))

    ws4 = wb.create_sheet("Filtered Files")
    write(ws4, ["Layer", "File", "Path"],
          [[f.layer, f.name + ".kt", f.rel] for f in filtered])

    ws5 = wb.create_sheet("Service Endpoints")
    write(ws5, ["Service Filename", "Service Function", "HTTP", "URL", "URL Const", "Line", "Path"],
          [[e["service_file"], e["function"], "@" + e["method"], e["url"], e["url_const"],
            e["line"], e["service_rel"]] for e in endpoints])

    wb.save(out_path)
    return out_path


# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", default="traceability_matrix.xlsx")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    filtered = filter_files(root)
    print("STEP 0 - filtered files (%d):" % len(filtered))
    for f in filtered:
        print("  %-11s %s" % (f.layer, f.rel))
    if not filtered:
        print("No .kt files matched the Step 0 filter under %s" % root)

    const_index = ConstIndex(root)
    endpoints = extract_service_endpoints(filtered, const_index)
    svc_uc = map_service_to_usecase(filtered)
    svc_repo = map_service_to_repository(filtered)
    uc_repo = map_usecase_to_repository(filtered)
    uc_vm = map_usecase_to_viewmodel(filtered)
    repo_vm = map_repository_to_viewmodel(filtered)
    vm_frag = map_viewmodel_to_fragment(filtered)
    rows, broken = build_flows(filtered, endpoints, svc_uc, svc_repo, uc_repo, uc_vm, repo_vm,
                               vm_frag)

    problems = final_check(filtered, rows, broken)
    print("\nendpoints=%d  svc->uc=%d  svc->repo=%d  uc<->repo=%d  uc->vm=%d  repo->vm=%d  "
          "vm->frag=%d  rows=%d  broken=%d  evidence=%d  unresolved=%d"
          % (len(endpoints), len(svc_uc), len(svc_repo), len(uc_repo), len(uc_vm),
             len(repo_vm), len(vm_frag), len(rows), len(broken), len(EVIDENCE), len(UNRESOLVED)))
    if problems:
        print("\nFINAL CHECK FAILURES:")
        for p in problems:
            print("  - %s" % p)
    else:
        print("FINAL CHECK: passed")

    export_excel(args.out, filtered, rows, endpoints, broken)
    print("\nwrote %s" % args.out)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
