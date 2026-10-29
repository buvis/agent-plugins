"""Committed target packages remain complete and usable without their author."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zlib

from test_resource_closure import closure_errors

import yaml


ROOT = Path(__file__).resolve().parents[2]
FORMATS = ["review-policy-v1", "review-evidence-v1", "review-fixtures-v1"]
CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
INVENTORY_SHA = "f55c98bba2b4b3c94ce588b6c616258186dd0bb2164800b2d34271acc25dfb5d"
EDGE_SHA = "b10e71c1b359f953f028cf9d84b7063e826c5df51e4791c3b7f89aa388ca8a93"
# Original 202 identities from 491ebd7; compressed JSON lines, independent of current map.
FROZEN_EDGES = (
    'c-'
    'rlpTaV+m6@cISD~x$cfNGa_Qh95W4G?r&1Wk)R6oo;Nl&y{|Ig&h+L6HAmO7_gy)`gTMIS<{3#qR8o{KUh<a}EzL'
    'zdjTuHigNQdHCkx^AF#C`rA*R9{%`H=7&O=b(&=M{~;!C|Ff6X)|UMHr$2r7*H0gI`r)@f{Cd%b+?cE?Kgu*wrvC'
    'j^TL@e?RX!$ZT7E3dQ(~Tj=e&3fRKDA%rb_bc<6G0V$-3nr$)0j0>)+i%CuAJ{r@#F0`SUHHFzf-vvaEutkm~W~#'
    ')WXVeI~b5W+u={Y0IkZ04_@9V;2qsF}*K+jZ-'
    '@Bfb?+$x`*CHdDNv02;U6P57quq1#w>NWL1twley*Fjp@_&y7}|&s9c+0tSl?DDQ*<z95buC>4oN%l117%G;H3X>'
    'EU1irVFg6ZHn(Pt9sxI4VQW9vL6tNdvvu2PSHKP%Ej{LsvAAKx$4GXID-vIo@CY~y-'
    ';}C!i}s<5X&Sz6lOe!a!*WIy`(0nVdEjp*RGd`=&0o$T4#UXH73XtWq%tKrZ{B5zOaf=b&?KMzE9G;T9@`8>usJt'
    'e%QafBW0$xc~L%m^Y33Dj{mlm;>4sn(56&HvahwPv=vOI&vkQaq)xJpE&Y96diC99=_{SJ-'
    '}v?=mqStyeW|u)Cr_f-'
    'N<^8hiVTSe1uB9e)D#;?6^9_yG6XCJh*5zR(9nJcAXvmo%2*H@g+eGsLWS$LDp^#o+Q`sv|9R_nWVZ4t$%}QOE$W'
    '~D_~CN^0BK1tN^|wNwsW{1i$l3}i|**wZGSfxB7>Zti|pIF)aq2qQ&c-'
    '!Ck;}mwJEMdr2&ei{Sy<RFwh(d!Ug3BDihKeBPN&tG6FP`gvSICOaxS6gs2JuMCMvl&?zd`BdUF#rt37%_vIH+ok'
    'YcZL{-'
    'mb+r_oc)nRAN!MZRyDU7PVi0)N%q9r<$9Vg>+kyK_~s(f$U(z3!WUV?pYgY8R0#xBJ5sV=tq@wM2Hz}`IKnRplk8'
    'Y2p*WID2TNk@t?psg9>k<r|64H-'
    '}ZsYnqbQAk+C5x0UOl*^dGEAde3kPZed>BKU!4$gk+hjQzZ$y4od>*DlMg~+8$p3Lg2@9T0a`gL0<HwAp>Dizb1n'
    'lMxphcx7jbB2W$LUR)F&?u+~6i^BlGlL*78gjt3uw|@-G14uSA}*n!meA^WU~`a#w(?L-'
    'z^2TX8F&&`+jwn~YI}%+#&NsVEUF`*KuPQ11N%okUPuc=crL9!*M(P2;nizlPoeF%vNS<-'
    'NK$<zGpGSTh)GS5jF^E6MIyGE1WbehrcxOlOU59DG!~2qgpm~(6x;?BjDq+|W=Oc^C27ygEU%LI#jRA&TUj+Jfvl'
    'b@GEHA<Ilq*FT})i686xL``<Jb^x~R8m>aC9TTA9i-'
    '@mP_FkkTlQ7)Fs4n&FVZ7)KD>DF#AeHHU>pa!F8a&WMVmm|K+#IT2b%*D3|DLp&6=#ItXHSXX(Te(`;;VxlcE{rq'
    'e)KjZ%Y8NbtZP<rl(^phz{StK$IDr48S?`x*(r8gr(3$WhRu-oljtXjoP>-!eAFq@>bp-cyqz~2E%7flzP7q2Q~h'
    'crm@&Bm&BXYLBjl#&>U4JT`q8-k#3-'
    'oO+=CCkU)I0BQ&*f#;wSTIM*dlb1haePgV6YCZOYXOotnMs!zm@^}Ejy~w50iTkGU1JS;)6L!MlxaBZM{C7nI?r5'
    '_=NKRsW}g>T{|6vM#(u%IXPW#CnEuW}z?9B5=*q5lnki8xS=lA<K9mhAl1&zrd3x~n5Ou^B{CtpUQoRJ`7g?M7PH'
    '3-Idz;A%)V@eEl`ISUB}nS-)Crut=-fh>-'
    '{JUhQSS&&HBUZt49Pu&OBZrHoqMybohUH1i&~c3C~q<ky@sBW+2;H^?qnNZGBpb6-!Y?-'
    '(uysJ3%N6OwJseY^Z76@V0fbe_llBEcJZh#GVR_tT_is9B8M}I+KofL8-'
    'Jxq<9eN%=KFy?tdVrGn4k8bqy8n<eY6bmKD)F}W!C6bIoCj=1=g@$Sbm#~-'
    '|~ag_#93)kSAAbg_G5L?A4eM>|lG+cql(qeu%1*b_K;DDiYNhTk_c~ME6>&Wh3}P@rf6nOwaLnahPuu*0J6kU|$D'
    '|t)LSv;%Z#jkS?_xcaV{{Zyl>m4lt$5M4%2Vo9D=jKTu3Ic^k7!vcwToW5A|zS|`3*&I3(2@pKJ(uQSRO&)}!rcr'
    'iL_Qy7)oN%`V~F7q_+v;knjOwAA(f%$^mK@JO-'
    '8`X|2sQX2iE;uC%DU<_D=UXVYPi3}N4{U5FFO+2pn}7wjXPi_XPTZe4-'
    '})K&kd9E}ZeHBYCJ0USJnb_Gm$Qd0Xc&jt_$HOUbS`&>d(5X{EFlY8N(VYz$W9JpIh)N)US>pE3BvFm`qW2fi;rs'
    '$84<Mj4DLhspB9*B7WHuPXkmBlCf-VCWM+l#wf<0qiw|wT+aqGRfYQYd7fY5p$eiD6a6`C|IsW-'
    'z$~q((+S7F13#*f|UY+bpAhd2L&y)G}Kw&s}_sfGq;Ud|y^WkkBtQfs~y<WWB2*#tG%d>nk<pkoQHg5oo;9@psfQ'
    'r$4rzeImoXj%`2N-0*w9){Uh6_es1Kf}-8*UaxAJ3-'
    'Wb(>;{+MhV|wys0XFSIF9nBz5@G*R8t9?YNJI91ij&SdogfX)PmxKDzkXbv6(wLj?eEa5^@AEa_VS(Ezq43Q&S71'
    '?4seVGO!Xu%uUJ|94DPmf(shyi@}L5Nn20G2ve;l;;d@-gPJKG5~H=@;x|rcZlQtsKha<9Qu-'
    '6TG73$xCVnc)|F`MW%Q`7w&+QrFIV-'
    'T)sqH?O=vz!BvEdJzt!AxqIB&=_B(WZ5<>MAg0@df%f@QrxymP!Z#XgZY|jX+~$R+QSS;#eXZd1PW#Y9KJK}s%j3'
    'Wk>HcS=N1opBgNp^Gj}I8n`9jr5I9?_Q_CXWh;HlXtjPipGO>FqKwINC#$8&tZ<WRi#%dSaO%z_%oYm(l*+L3vV2'
    '2|Rhu&TQ6Ss`zo88K0uR3awFpVnTN{lPTh3j^kTvFI9mTHEyZj?B=z4tICABLjYTJULPG7Hzi9?9X@VrH^sLwxT-'
    ')oMitss#?FEY+lz_&3tb4ABzWd@n$`3f2fy;g$YiDF0QcG8&~JI{g1U*b?wzx@6}gt)xW;sNf&7pH!4=hNKiijK('
    '+mwaYiB~;)rMhAc%wsqd4M5LuQ!f5iywH2*5Z3*KbEa*V_@S{dUChR(|>M;`N5hGm~S-'
    'u<PDYAGXOMu6Jga7cc95VW)m=T+fH|^($`64P0`XK-spqORio)@_8A}&3Jt|;^GAb$5jUJ3y(e&JlBPZSJ>%PZ8t'
    '3(xIl2M=mykl@ItTOjAnaKU^uG@eg|iEDZD<J-m$tcky=)Tk-'
    'H8m!eW|L_60Gr<gB*y_^>l;YnwKvOSllwxw`29p}F_6-pTchS~nRaJO1sL4_^m#-'
    'ZbDVzRa`CRDEWEPqJf;4^~y$(VeMxDqj(G^s|0{JMuV;ODakOth>K1@<S7ocfhdk(zWXn*A%jMqQJETd4t+$#oG6'
    '_IG3FDJy61D8p31qO(wI;V3XNz26&RkpT`_8)%9~B_j_y6Wtu#7&J@q?yTyFS%z&!)U!j>SX6N)o3rtVf%=FFbT<'
    'w$IiksUIICwmqF+=%eb+g`XvrchmBkc9A+_)EJG&q(H)K+F2bNP}OX5xGqMn9~+Z3?g63lBNC^Vc&YLMVocMvCYV'
    'Qx%C2#sI`RwlM-=Va%aGFtk5Kv56Gsk_u(CQc_@Su9sSvFvn6$(1+jt2k>cY0R'
)
OWNER_SHA = "d7ded009798a6d0437bda8384b0e8ac02bdd258e17bda0d098611160ab30fa52"
GATE_SIZE = 742
GATE_SHA = "2ea4600b2ec6756640e2e23a8d761160afc889c0a3c6af0caa6fac6d0edaec75"

# External boundaries only: deny network, process launches, and author-home reads.
GUARD = '''
import os, pathlib, socket, sys
home = pathlib.Path(os.environ["FORBIDDEN_AUTHOR_HOME"]).resolve()
allowed = [pathlib.Path(p).resolve() for p in
           (sys.prefix, sys.base_prefix, os.environ["ISOLATED_TARGET"])]
for directory in sys.path:
    if pathlib.Path(directory).name == "site-packages" and pathlib.Path(directory).is_dir():
        allowed.extend(p.resolve() for p in pathlib.Path(directory).iterdir())
def audit(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn"}:
        raise PermissionError("isolated target forbids process launch")
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = pathlib.Path(os.fsdecode(args[0])).resolve()
        if path.is_relative_to(home) and not any(path.is_relative_to(p) for p in allowed):
            raise PermissionError("isolated target forbids author/source reads")
def denied(*args, **kwargs):
    raise PermissionError("isolated target forbids network")
socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
socket.getaddrinfo = denied
sys.addaudithook(audit)
'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TargetPackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="autopilot-target-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.target = Path(cls.temp.name) / "target"
        cls.target.mkdir()
        archive = Path(cls.temp.name) / "target.tar"
        with archive.open("wb") as stream:
            subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"], cwd=ROOT,
                stdout=stream, stderr=subprocess.PIPE, check=True, timeout=60,
            )
        with tarfile.open(archive) as bundle:
            bundle.extractall(cls.target, filter="data")
        cls.package = cls.target / "plugins/autopilot"
        cls.mapping = json.loads((cls.target / "tools/autopilot/source-map.json").read_text())
        cls.inventory = json.loads(
            (cls.target / "tools/autopilot/source-inventory.json").read_text()
        )
        cls.guard = Path(cls.temp.name) / "guard"
        cls.guard.mkdir()
        (cls.guard / "sitecustomize.py").write_text(GUARD)
        cls.home = cls.target / "empty-home"
        cls.home.mkdir()
        cls.cwd = cls.target / "unrelated-cwd"
        cls.cwd.mkdir()
        cls.env = {
            "PATH": os.defpath, "HOME": str(cls.home), "USERPROFILE": str(cls.home),
            "PYTHONPATH": str(cls.guard), "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1", "FORBIDDEN_AUTHOR_HOME": str(Path.home()),
            "ISOLATED_TARGET": str(cls.target),
        }

    def child(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *map(str, args)], cwd=self.cwd, env=self.env,
            text=True, capture_output=True, timeout=60,
        )

    def facade(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self.child(self.package / "scripts/autopilot.py", *args)

    def validator(self) -> subprocess.CompletedProcess[str]:
        return self.child(self.target / "scripts/validate.py")

    def assert_acceptance_cases(self, cases: list[dict], *, exercise: bool = False) -> None:
        self.assertTrue(cases)
        identities = [case["case_id"] for case in cases]
        self.assertEqual(len(identities), len(set(identities)))
        for case in cases:
            for field in ("case_id", "expected_outcome") + (("exercise",) if exercise else ()):
                self.assertTrue(case[field].strip())

    def assert_delivery_evidence(self, evidence: dict) -> None:
        self.assertEqual(evidence["status"], "passed")
        artifact = self.target / evidence["artifact_id"]
        self.assertTrue(artifact.resolve().is_relative_to(self.target.resolve()))
        self.assertTrue(artifact.is_file())
        self.assertEqual(digest(artifact.read_bytes()), evidence["artifact_sha256"])
        # This .git-free archive checks revision format; the coordinator separately
        # verified README/changelog git show REV:path bytes against artifact_sha256.
        self.assertRegex(evidence["tested_package_revision"], r"^[0-9a-f]{40}$")

    def assert_assignment_evidence(self, evidence: dict) -> None:
        receipts = [evidence, *evidence["profile_evidence"].values()]
        for receipt in receipts:
            self.assertIn(receipt["status"], {"planned", "unavailable", "failed", "passed"})
            for field in ("artifact_id", "artifact_sha256", "tested_package_revision"):
                self.assertIn(field, receipt)
            if receipt["status"] == "passed":
                self.assertTrue(receipt["artifact_id"])
                self.assertRegex(receipt["artifact_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(receipt["tested_package_revision"], r"^[0-9a-f]{40}$")
        if evidence["status"] == "passed":
            self.assertTrue(evidence["profile_evidence"])
            self.assertTrue(all(r["status"] == "passed"
                                for r in evidence["profile_evidence"].values()))

    def assert_assignments(self) -> None:
        bindings = [r["owner_repository"] for r in self.mapping["owner_bindings"]]
        self.assertEqual(set(bindings), {"buvis/agent-plugins", "buvis/ovcaq", "buvis/lantern"})
        self.assertEqual(len(bindings), 3)
        for collection, identity, frozen_ids in (
            ("behaviors", "source_behavior_id", "expected_behavior_ids"),
            ("regression_cases", "source_regression_id", "source_regression_ids"),
        ):
            rows = self.mapping[collection]
            ids = [r[identity] for r in rows]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(set(ids), set(self.inventory[frozen_ids]))
            sources = {r[identity]: r for r in self.inventory[collection]}
            for row in rows:
                with self.subTest(identity=row[identity]):
                    self.assertIn(row["owner_repository"], bindings)
                    self.assertRegex(row["delivery_prd"], r"^[0-9]{5}$")
                    self.assert_assignment_evidence(row["evidence"])
                    source = sources[row[identity]]
                    if collection == "behaviors":
                        self.assert_behavior(row, source)
                    else:
                        self.assert_regression(row, source)

    def assert_behavior(self, row: dict, source: dict) -> None:
        self.assertEqual(row["source_anchors"], source["source_anchors"])
        self.assertTrue(row["source_anchors"])
        self.assertIn(row["classification"], {"port", "redesign"})
        if "classification" in source:
            self.assertEqual(row["classification"], source["classification"])
        for field in ("reason", "destination_procedure", "destination_operation"):
            self.assertTrue(row[field].strip())
        profiles = row["required_profiles"]
        self.assertTrue(profiles)
        self.assertEqual(len(profiles), len(set(profiles)))
        self.assertEqual(set(profiles), set(row["evidence"]["profile_evidence"]))
        self.assert_acceptance_cases(row["acceptance_cases"], exercise=True)

    def assert_regression(self, row: dict, source: dict) -> None:
        for field in ("source_path", "test_identity", "source_blob_sha256", "case_sha256"):
            self.assertEqual(row[field], source[field])
        self.assertIn(row["disposition"], {"retained", "replaced", "obsolete"})
        self.assertTrue(row["expected_outcome"].strip())
        if row["disposition"] == "replaced":
            self.assertTrue(row["equivalent_target_scenario"].strip())
        if row["disposition"] == "obsolete":
            self.assertEqual(row["evidence"]["status"], "passed")

    def assert_authored_owners_and_history(self) -> None:
        owners = self.mapping["authored_file_owners"]
        paths = [r["path"] for r in owners]
        self.assertEqual(len(paths), 21)
        self.assertEqual(len(set(paths)), 21)
        self.assertEqual(digest("\n".join(sorted(paths)).encode()), OWNER_SHA)
        for row in owners:
            self.assertIsNone(row["source_asset_id"])
            self.assertIsNone(row["source_blob_sha256"])
            self.assertEqual(row["owner_repository"], "buvis/agent-plugins")
            self.assertEqual(row["delivery_prd"], "00012")
            self.assertTrue((self.target / row["path"]).is_file())
            self.assert_acceptance_cases(row["acceptance_cases"])
        history = " ".join((self.package / "CHANGELOG.md").read_text().split())
        self.assertIn("## [Unreleased]", history)
        # Public pre-integration history, independent of the mutable asset digest.
        for bullet in (
            "Add read-only local PRD prerequisite diagnostics based on completed PRD filenames.",
            "Add the local contract-capabilities and canonical policy-export facade, with packaged-policy digest and integer-domain checks and a delegating maintainer exporter.",
            "Add the explicit pinned-source provenance audit for source files, asset sections, behavior anchors, and regression identities and digests.",
            "Add 55 self-contained golden review evidence fixtures and alternate policy binding, covering complete lane rosters, fallback and retry histories, stale bindings, input isolation, attribution, artifacts, and rubric verdicts. No host execution or certification is claimed.",
            "Add the draft 2020-12 review evidence schema and expected-context definition, with closed wire shapes and conditional validation. No host execution or certification is claimed.",
            "Add gated review policy foundation data with pinned source bindings and test-only dependencies. No host execution or certification is claimed.",
        ):
            self.assertIn(bullet, history)

    def assert_readme_content(self, text: str, sections: list[dict]) -> None:
        matches = list(re.finditer(r"^#{1,6}[^\S\n]+(.+?)[^\S\n]*#*[^\S\n]*$", text, re.MULTILINE))
        topics = {
            "autopilot": r"autopilot|PRD|review",
            "What's inside": r"skill|contract|persona|reference",
            "Recursion guard": r"recurs|nested|guard",
            "Paths": r"package|resource|root|path",
            "Install": r"gated|local|unavailable|certif",
            "Update": r"update|version|replace|gated",
            "Alternative: install directly from this repo": r"gated|local|clone|certif",
            "What intentionally stays out": r"controller|host|external|unavailable",
            "Development": r"test|pytest|validat",
            "License": r"MIT",
            "Autoclaude role effort": r"role|effort|gated",
        }
        for section in sections:
            found = [i for i, match in enumerate(matches) if match[1] == section["heading"]]
            self.assertEqual(len(found), 1, section["heading"])
            index = found[0]
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[matches[index].end():end].strip()
            self.assertRegex(body, r"[A-Za-z]+[^\n]*\s+[A-Za-z]+", section["heading"])
            self.assertRegex(body, "(?i)" + topics[section["heading"]])
        # Structural bodies alone do not prove source semantics; independent review does.
        for option in ("--list-capabilities", "--export-policy"):
            self.assertRegex(text, r"python3[^\n]*scripts/autopilot\.py[^\n]*" + option)
        self.assertIn("--out", text)
        for contract_format in FORMATS:
            self.assertIn(contract_format, text)
        self.assertRegex(text, r"(?i)gat(?:ed|ing)")
        self.assertRegex(text, r"(?is)(?:no|not|unavailable|uncertified)[^.]*\b(?:host|certif\w*)")
        root_readme = (self.target / "README.md").read_text()
        rows = [line for line in root_readme.splitlines()
                if line.lstrip().startswith("|") and re.search(
                    r"\[autopilot\]\(\.?/?plugins/autopilot(?:/README\.md|/)?\)", line)]
        self.assertEqual(len(rows), 1)
        self.assertIn("0.10.0", rows[0])
        self.assertRegex(rows[0], r"(?i)gated")

    def assert_unconditional(self, item: dict) -> None:
        # These integration gates and their setup must run on every configured event.
        condition = item.get("if", True)
        self.assertIn(condition, (True, "true", "${{ true }}", "success()", "${{ success() }}"))
        self.assertFalse(item.get("continue-on-error", False))

    def test_content_roster_matches_frozen_inventory_and_actual_package_bytes(self) -> None:
        mapping, inventory = self.mapping, self.inventory
        self.assertEqual(mapping["schema_version"], 1)
        inventory_bytes = (self.target / "tools/autopilot/source-inventory.json").read_bytes()
        self.assertEqual(mapping["source_inventory_sha256"], digest(inventory_bytes))
        self.assertEqual(digest(inventory_bytes), INVENTORY_SHA)
        self.assert_assignments()
        self.assert_authored_owners_and_history()
        source_rows = [a for a in mapping["assets"] if a["source_asset_id"] is not None]
        source_ids = [a["source_asset_id"] for a in source_rows]
        self.assertEqual(len(source_ids), 92)
        self.assertEqual(len(set(source_ids)), len(source_ids))
        self.assertEqual(set(source_ids), set(inventory["required_asset_ids"]))
        self.assertEqual(len(mapping["behaviors"]), 1381)
        self.assertEqual(len(mapping["regression_cases"]), 4950)
        expected = {a["destination_path"] for a in mapping["assets"]}
        actual = {p.relative_to(self.target).as_posix()
                  for p in self.package.rglob("*") if p.is_file()}
        self.assertEqual(actual, expected)
        for row in mapping["assets"]:
            with self.subTest(asset=row["destination_path"]):
                path = self.target / row["destination_path"]
                self.assertTrue(path.resolve().is_relative_to(self.package.resolve()))
                self.assertEqual(digest(path.read_bytes()), row["destination_blob_sha256"])
                self.assertNotEqual(row["disposition"], "planned")
                if row["disposition"] == "preserved":
                    self.assertEqual(row["destination_blob_sha256"], row["source_blob_sha256"])

    def test_reference_tree_and_all_eleven_first_body_gates_preserve_source_bytes(self) -> None:
        rows = self.mapping["assets"]
        personas = [r for r in rows if "/references/personas/" in r["destination_path"]]
        skills = [r for r in rows if r["destination_path"].endswith("/SKILL.md")]
        self.assertEqual(len(personas), 18)
        self.assertEqual(len(skills), 11)
        self.assertTrue(all(r["disposition"] == "preserved" for r in rows
                            if "/references/" in r["destination_path"]))
        for row in skills:
            with self.subTest(skill=row["destination_path"]):
                data = (self.target / row["destination_path"]).read_bytes()
                frontmatter_end = data.index(b"\n---\n", 4) + len(b"\n---\n")
                self.assertEqual(digest(data[frontmatter_end:frontmatter_end + GATE_SIZE]), GATE_SHA)
                restored = data[:frontmatter_end] + data[frontmatter_end + GATE_SIZE:]
                self.assertEqual(digest(restored), row["source_blob_sha256"])

    def test_readme_retains_every_source_heading_with_completed_adaptation_receipts(self) -> None:
        source = next(a for a in self.inventory["assets"] if a["source_asset_id"] == "README.md")
        row = next(a for a in self.mapping["assets"] if a["source_asset_id"] == "README.md")
        text = (self.package / "README.md").read_text()
        headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE)
        self.assert_readme_content(text, source["sections"])
        self.assert_delivery_evidence(row["evidence"])
        self.assertEqual(len(row["section_plan"]), len(source["sections"]))
        self.assertTrue(row["acceptance_cases"])
        self.assertEqual(row["disposition"], "adapted")
        self.assertEqual({s["source_anchor"] for s in row["section_plan"]},
                         {s["anchor"] for s in source["sections"]})
        for section in source["sections"]:
            with self.subTest(section=section["anchor"]):
                self.assertIn(section["heading"], headings)
                receipt = next(s for s in row["section_plan"]
                               if s["source_anchor"] == section["anchor"])
                self.assertEqual(receipt["source_sha256"], section["sha256"])
                self.assertTrue(receipt["action"].strip())
                self.assertTrue(receipt["reason"].strip())
                self.assertTrue(receipt["delivery_note"].strip())
        self.assertEqual(row["evidence"]["status"], "passed")
        self.assertTrue(all(c["status"] == "passed" for c in row["acceptance_cases"]))

    def test_resource_closure_declares_inside_resources_and_external_failure_rules(self) -> None:
        edges = self.mapping["resource_edges"]
        fields = ("source_path", "source_line", "source_behavior_id", "source_anchors", "reference")
        identities = [json.dumps({k: e[k] for k in fields if k in e},
                                 sort_keys=True, separators=(",", ":")) for e in edges]
        frozen = zlib.decompress(base64.b85decode(FROZEN_EDGES)).decode().splitlines()
        self.assertEqual(len(frozen), 202)
        self.assertEqual(digest("\n".join(frozen).encode()), EDGE_SHA)
        self.assertEqual(len(identities), len(set(identities)))
        self.assertTrue(set(frozen).issubset(identities))
        self.assertEqual(closure_errors(self.package, edges), [])
        self.assertEqual({e["kind"] for e in edges}, {
            "packaged-resource", "external-capability", "informational-provenance",
        })
        for edge in edges:
            with self.subTest(edge=edge["reference"], source=edge.get("source_path", edge.get("source_behavior_id"))):
                if edge["kind"] == "packaged-resource":
                    path = self.target / edge["destination_path"]
                    self.assertTrue(path.is_file())
                    self.assertTrue(path.resolve().is_relative_to(self.package.resolve()))
                    self.assertTrue(edge["failure_rule"].strip())
                elif edge["kind"] == "external-capability":
                    self.assertTrue(edge["capability"].strip())
                    self.assertTrue(edge["failure_rule"].strip())
                else:
                    self.assertRegex(edge["runtime_rule"], r"(?i)(must not|never).*(runtime|content)")

    def test_public_validator_accepts_contained_links_and_rejects_external_helpers(self) -> None:
        baseline = self.validator()
        self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)
        for folder, name in (("scripts", "external-helper.py"),
                             ("references", "external-reference.md")):
            link = self.package / folder / name
            link.parent.mkdir(exist_ok=True)
            outside = self.target / ("autopilot-near-miss-" + name)
            outside.write_text("External content must never satisfy packaged resources.\n")
            try:
                link.symlink_to(self.package / "LICENSE")
                valid = self.validator()
                self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
                link.unlink()
                link.symlink_to(outside)
                invalid = self.validator()
                self.assertNotEqual(invalid.returncode, 0, invalid.stdout + invalid.stderr)
                self.assertTrue((invalid.stdout + invalid.stderr).strip())
            finally:
                link.unlink(missing_ok=True)
                outside.unlink(missing_ok=True)

    def test_target_only_checkout_denies_source_home_and_network_but_exports_policy(self) -> None:
        self.assertFalse((self.target / ".git").exists())
        self.assertEqual(list(self.home.iterdir()), [])
        probe = self.child("-c", '''
import os, pathlib, socket
assert pathlib.Path.home() == pathlib.Path(os.environ["HOME"])
for path in [pathlib.Path(os.environ["FORBIDDEN_AUTHOR_HOME"])/".claude/AGENTS.md",
             pathlib.Path(os.environ["FORBIDDEN_AUTHOR_HOME"])/"git/src/github.com/buvis/claude-autopilot/README.md"]:
    try: path.read_bytes()
    except PermissionError: pass
    else: raise AssertionError("author/source boundary escaped")
try: socket.create_connection(("127.0.0.1", 1), timeout=0.1)
except PermissionError: pass
else: raise AssertionError("network boundary escaped")
print("isolated")
''')
        self.assertEqual((probe.returncode, probe.stdout), (0, "isolated\n"), probe.stderr)
        capabilities = self.facade("--list-capabilities")
        self.assertEqual(capabilities.returncode, 0, capabilities.stderr)
        self.assertEqual(capabilities.stdout, json.dumps(FORMATS, separators=(",", ":")) + "\n")
        expected = json.loads((self.package / "contracts/review-policy-v1.json").read_text())
        exported = self.facade("--export-policy")
        self.assertEqual(exported.returncode, 0, exported.stderr)
        self.assertEqual(json.loads(exported.stdout), expected)
        for relative in ("policy-one.json", "nested/policy-two.json"):
            destination = self.cwd / relative
            destination.parent.mkdir(exist_ok=True)
            result = self.facade("--export-policy", "--out", relative)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(destination.read_bytes(), exported.stdout.encode())
        for args in ((), ("--list-capabilities-extra",), ("--export-policy", "--out", str(self.cwd))):
            result = self.facade(*args)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((result.stdout + result.stderr).strip())

    def test_target_only_semantic_oracle_checks_every_committed_fixture_without_skip(self) -> None:
        result = self.child("-c", '''
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root / "tests/autopilot"))
from test_contract_semantics import validate_review
document = json.loads((root / "plugins/autopilot/contracts/review-fixtures-v1.json").read_text())
assert len(document["cases"]) == 55
outcomes = set()
for case in document["cases"]:
    actual = validate_review(document["policies"][case["policy"]], case["expected_context"], case["input"])
    assert actual == case["expect"], (case["name"], actual, case["expect"])
    outcomes.add(actual["outcome"])
assert outcomes == {"accepted", "rejected"}
print("55 fixtures validated")
''', self.target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "55 fixtures validated\n")

    def test_ci_autopilot_wired_with_python312_and_complete_pinned_plugins_job(self) -> None:
        document = yaml.safe_load((self.target / ".github/workflows/validate.yml").read_text())
        self.assertEqual(document["permissions"], {"contents": "read"})
        triggers = document.get("on", document.get(True))  # PyYAML YAML 1.1 parses on as True.
        self.assertIsInstance(triggers, dict)
        self.assertEqual(triggers["push"]["branches"], ["master"])
        self.assertIn("pull_request", triggers)
        jobs = document["jobs"]
        for job in (jobs["plugins"], jobs["autopilot"]):
            self.assert_unconditional(job)
            for step in job["steps"]:
                self.assert_unconditional(step)
        plugins = jobs["plugins"]
        self.assertEqual(plugins["runs-on"], "ubuntu-latest")
        self.assertEqual(plugins["env"], {"PYTHONDONTWRITEBYTECODE": "1"})
        steps = plugins["steps"]
        self.assertEqual([s.get("uses") for s in steps[:2]], [CHECKOUT, SETUP])
        self.assertEqual(steps[0]["with"], {"persist-credentials": False})
        self.assertEqual(steps[1]["with"], {"python-version": "3.10"})
        self.assertEqual([s["run"] for s in steps[2:]], [
            "python3 -m unittest discover -s scripts", "python3 scripts/validate.py",
            *[f"python3 -m unittest discover -s tests/specflow/{area}"
              for area in ("release", "contract", "rules", "review")],
            "python3 tools/specflow/check_rules.py --area VAL,SKL,DLG,INT,REQ,DSN,TSK,IMP,VER,RVC,RVR,RVD,RVX,CNV",
            "python3 tools/specflow/verify_release.py",
        ])
        steps = jobs["autopilot"]["steps"]
        self.assertTrue(any(s.get("uses") == CHECKOUT and
                            s.get("with", {}).get("persist-credentials") is False for s in steps))
        self.assertTrue(any(s.get("uses") == SETUP and
                            s.get("with", {}).get("python-version") == "3.12" for s in steps))
        commands = [s["run"] for s in steps if "run" in s]
        self.assertTrue(any(re.search(r"(?:^|\s)(?:-r|--requirement)\s+tools/autopilot/requirements-test\.txt(?:\s|$)", c)
                            and "pip install" in c for c in commands))
        self.assertTrue(any(shlex.split(c) == ["python", "-m", "pytest", "tests/autopilot", "-q"]
                            for c in commands))


if __name__ == "__main__":
    unittest.main()
