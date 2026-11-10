"""Offline, reversible product controls; fixtures contain synthetic data only."""
import copy
from pathlib import Path
import re
import shutil
import subprocess

import pytest
from fathom.connectors import CSVConnector
from fathom.profiler import profile
from fathom.renderers import render_html
from fathom.liftoff import build_liftoff, render_liftoff
from fathom.configure import render_page, build_schema
from fathom.report_style import PRODUCT_JS


def test_report_polish_preserves_artifact_fallback_and_script_contract():
    result = profile(CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load())
    before = result.to_json()
    page = render_html(result)
    assert render_html(result) == page
    assert result.to_json() == before
    assert 'class="product-header"' in page
    assert 'class="product-tools" hidden' in page
    assert 'class="dictionary-tools" hidden' in page
    assert page.count('class="column-entry"') == len(result.document['columns'])
    assert not re.search(r'<details[^>]*class="column-entry"[^>]*hidden', page)
    assert re.findall(r'<script([^>]*)>', page) == [' id="fathom-navigation"', ' id="fathom-transpose"']
    assert 'fetch(' not in page and 'localStorage' not in page
    assert 'aria-live="polite"' in page
    assert '.column-entry[hidden]{display:block!important}' in page
    assert 'prefers-reduced-motion:reduce' in page


def test_liftoff_shared_shell_is_unique_and_offline():
    result = build_liftoff(CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load())
    before = result.to_json()
    page = render_liftoff(result)
    assert page.count('id="fathom-theme"') == 1
    assert page.count('class="product-header"') == 1
    assert 'class="product-tools" hidden' in page
    assert result.to_json() == before
    assert page == render_liftoff(result)


def test_controls_repeated_filter_reset_theme_and_hash_recovery():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required to execute progressive-control behavior')
    harness = r'''
const assert=require('assert');
const events={}, clicks={};
function el(extra={}){return Object.assign({hidden:true,value:'',listeners:{},addEventListener(k,f){this.listeners[k]=f;},focus(){this.focused=true;}},extra);}
const tools=el(), themeTools=el(), theme=el({value:'system',closest:()=>themeTools});
const input=el(),reset=el(),count=el();
const entries=['Revenue numeric','Group categorical','<script> text'].map((text,i)=>el({id:'dictionary-column-'+i,open:false,querySelector:()=>({textContent:text}),closest(){return this;}}));
const nodes={'fathom-theme':theme,'dictionary-tools':tools,'dictionary-filter':input,'dictionary-reset':reset,'dictionary-count':count};entries.forEach(e=>nodes[e.id]=e);
const root={attrs:{},setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
global.document={documentElement:root,getElementById:id=>nodes[id]||null,querySelectorAll:()=>entries,addEventListener:(k,f)=>clicks[k]=f};
global.window={addEventListener:(k,f)=>events[k]=f};global.location={hash:''};
'''
    checks = r'''
assert.equal(themeTools.hidden,false);assert.equal(tools.hidden,false);
for(const value of ['dark','light','system','dark','system']){theme.value=value;theme.listeners.change();assert.equal(root.attrs['data-theme'],value==='system'?undefined:value);}
for(let i=0;i<3;i++){
input.value='  NUMERIC ';input.listeners.input();assert.deepEqual(entries.map(e=>e.hidden),[false,true,true]);assert.equal(count.textContent,'1 of 3 columns');
input.value='absent';input.listeners.input();assert(entries.every(e=>e.hidden));assert(count.textContent.includes('No matches'));
reset.listeners.click();assert(entries.every(e=>!e.hidden));assert.equal(input.value,'');assert(input.focused);
}
input.value='revenue';input.listeners.input();location.hash='#dictionary-column-1';events.hashchange();assert(!entries[1].hidden);assert(entries[1].open);assert.equal(input.value,'');
input.value='revenue';input.listeners.input();clicks.click({target:{closest:()=>({getAttribute:()=> '#dictionary-column-2'})}});assert(entries[2].open);assert(entries.every(e=>!e.hidden));
location.hash='#%broken';events.hashchange();
input.value='<script>';input.listeners.input();assert.deepEqual(entries.map(e=>e.hidden),[true,true,false]);
'''
    result = subprocess.run([node, '-e', harness + PRODUCT_JS + checks], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_standalone_configurator_keeps_schema_and_script_count():
    frame = CSVConnector(Path('tests/fixtures/liftoff/planted.csv')).load()
    result = profile(frame)
    schema = build_schema(result.document, frame.frame, None)
    before = copy.deepcopy(schema)
    page = render_page(schema)
    assert page.count('<script') == 3
    assert page.count('id="fathom-theme"') == 1
    assert 'class="product-tools" hidden' in page
    assert schema == before
    assert render_page(schema) == page


def test_dictionary_markup_escapes_column_names(tmp_path):
    source = tmp_path / 'synthetic.csv'
    source.write_text('<script>alert(1)</script>,plain\n1,a\n2,b\n')
    page = render_html(profile(CSVConnector(source).load()))
    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in page
    assert 'innerHTML' not in PRODUCT_JS
