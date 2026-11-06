"""PR34: numeric roles come from saved evidence, never sentence fragments."""
import copy,json,re
from html.parser import HTMLParser
from pathlib import Path
import pytest
from fathom.finding_view import finding_tree
from fathom.models import ProfilingResult
from fathom.connectors import CSVConnector
from fathom.config import load_config
from fathom.profiler import profile
from fathom.renderers import render_html,render_markdown
from fathom.verdicts import key_findings

@pytest.fixture(scope="module")
def films():
    return profile(CSVConnector(Path("tests/fixtures/polish/movies.csv")).load(),load_config("tests/fixtures/target/movies.yaml"))

class Headlines(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.depth=0;self.items=[]
    def handle_starttag(self,tag,attrs):
        if tag=="section" and dict(attrs).get("id")=="key-findings":self.active=True
        if self.active and tag=="li":
            self.depth+=1
            if self.depth==1:self.items.append({"parent":"","children":[]})
            else:self.items[-1]["children"].append("")
    def handle_endtag(self,tag):
        if self.active and tag=="li":self.depth-=1
        if self.active and tag=="section":self.active=False
    def handle_data(self,text):
        if self.active and self.depth:
            if self.depth==1:self.items[-1]["parent"]+=text
            else:self.items[-1]["children"][-1]+=text


def test_films_headline_roles_and_independent_relationships(films):
    before=films.to_json();reader=Headlines();reader.feed(render_html(films))
    pairs=[x for x in reader.items if "× Worldwide Gross" in x["parent"]]
    assert len(pairs)==2
    assert "US Gross × Worldwide Gross" in pairs[0]["parent"]
    assert "US DVD Sales × Worldwide Gross" in pairs[1]["parent"]
    assert "selected" in pairs[0]["parent"] and "(inferred)" in pairs[0]["parent"]
    assert "Pearson r: 0.940" in pairs[0]["children"]
    assert "complete cases: 3,194" in pairs[0]["children"]
    adventure=next(x for x in reader.items if "Adventure" in x["parent"])
    group=next(s for s in adventure["children"] if s.startswith("group:"))
    rest=next(s for s in adventure["children"] if s.startswith("rest:"))
    assert "241,171,386" in group and "274" in group
    assert "76,434,662" in rest and "2,652" in rest and "241,171,386" not in rest
    assert all(not re.search(r"\.(?:\s+|[A-Z])\S",s) for x in reader.items for s in x["children"])
    assert all("Selected relationship" not in s for x in reader.items for s in x["children"])
    assert len(reader.items)<=5 and films.to_json()==before
    assert render_html(ProfilingResult(json.loads(before)))==render_html(films)


def test_group_and_rest_decoy_do_not_follow_prose(films):
    f=copy.deepcopy(next(f for f in films.document["findings"] if f.get("rule")=="target_group_contrast" and f["kind"]=="observation"))
    g=f["evidence"][0]["value"];g["contrasts"]=[{"measure":"mean","group":12.5,"rest":987,"basis":"saved gate"}]
    f["message"]="rest mean 12.5. group mean 987; deliberately misleading stale text"
    tree=finding_tree(f);group=next(s for s in tree["children"] if s.startswith("group:"));rest=next(s for s in tree["children"] if s.startswith("rest:"))
    assert "12.5" in group and "987" not in group
    assert "987" in rest and "12.5" not in rest
    # Swapped values remain associated with their new structured roles.
    g["contrasts"][0].update(group=987,rest=12.5)
    tree=finding_tree(f)
    assert "987" in next(s for s in tree["children"] if s.startswith("group:"))
    assert "12.5" in next(s for s in tree["children"] if s.startswith("rest:"))


def test_unstructured_sentences_and_literal_decoys_stay_whole():
    for message in ["Before = 1; after = 2. Complete n=3. Descriptive, not causal.","x=y: 'a,b; c.d' is literal. Meaning unknown."]:
        f={"message":message,"id":"legacy","kind":"observation","evidence":[]}
        assert finding_tree(f)=={"text":message,"children":[]}


def test_raw_evidence_string_is_not_split_into_claims():
    from fathom.finding_view import evidence_html,evidence_markdown
    sentence='mean = 1; rest = 2. Complete n=3. Descriptive, not causal.'
    html=evidence_html({'note':sentence})
    assert html.count('<li>')==1 and sentence in html
    assert evidence_markdown(sentence).count('\n')==1


def test_relationship_precision_is_display_only_in_every_format(films):
    from fathom.exports import finding_topics
    d=copy.deepcopy(films.document);original=copy.deepcopy(d)
    f=next(f for f in d["findings"] if f.get("rule")=="selected_relation")
    f["message"]="Selected relationship: stale coefficient=999. Then a sentence."
    p=ProfilingResult(d)
    for text in [render_html(p),render_markdown(p),str(list(finding_topics(d)))]:
        assert "0.940" in text and "complete cases" in text
        assert "stale coefficient" not in text
    assert d["bivariate"]==original["bivariate"]
    assert f["evidence"]==next(x for x in original["findings"] if x["id"]==f["id"])["evidence"]
    assert len(key_findings(d))<=5
