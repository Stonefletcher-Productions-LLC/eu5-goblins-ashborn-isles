"""Check native-object preservation and serialized client-local music routing."""
import argparse
import hashlib
import itertools
import json
import struct
from pathlib import Path
import xml.etree.ElementTree as ET
from build_goblin_music import ROOT, MODE, MUSIC_ROOT, BANK_PATH, chunks, ident, internal_ident
from ashborn_roster import COUNTRIES

def records(data):
    hirc = dict(chunks(data))[b'HIRC']
    count = struct.unpack_from('<I', hirc)[0]
    pos = 4
    result = {}
    for _ in range(count):
        size = struct.unpack_from('<I', hirc, pos+1)[0]
        oid = struct.unpack_from('<I', hirc, pos+5)[0]
        assert oid not in result, 'Duplicate object ID'
        result[oid] = hirc[pos:pos+5+size]
        pos += 5+size
    assert pos == len(hirc)
    return result

def objects(path):
    root = ET.parse(path).getroot()
    assert not list(root.iter('error')), 'wwiser reported an invalid structure'
    result = {}
    for obj in root.iter('object'):
        field = obj.find("field[@name='ulID']")
        if field is not None:
            result[int(field.get('value'))] = obj
    return result

def resolve(obj, states):
    groups = [int(f.get('value')) for f in obj.findall(".//object[@name='Arguments']//field[@name='ulGroup']")]
    current = obj.find(".//object[@name='AkDecisionTree']/list/object")
    for group in groups:
        children = current.findall('list/object')
        key = states.get(group, ident('None'))
        candidates = {int(n.find("field[@name='key']").get('value')):n for n in children}
        current = candidates.get(key, candidates.get(0))
        if current is None:
            return None
    return int(current.find("field[@name='audioNodeId']").get('value'))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--game',type=Path,required=True)
    ap.add_argument('--native-xml',type=Path,required=True)
    ap.add_argument('--built-xml',type=Path,required=True)
    ap.add_argument('--mod',type=Path,default=ROOT/'mod')
    ap.add_argument('--report',type=Path)
    args=ap.parse_args()
    object_id=lambda name: internal_ident(name)
    original=records((args.game/'game'/BANK_PATH/'sb_music_logic.bnk').read_bytes())
    built=records((args.mod/BANK_PATH/'sb_music_logic.bnk').read_bytes())
    assert len(built)==len(original)+10
    for oid, data in original.items():
        if oid not in (MODE,MUSIC_ROOT): assert built[oid]==data, f'Unexpected native change: {oid}'
    before=objects(args.native_xml);after=objects(args.built_xml)
    added_ids=set(built)-set(original)
    new_item_ids=[int(f.get('value')) for oid in added_ids for f in after[oid].findall(".//field[@name='playlistItemID']")]
    native_item_ids={int(f.get('value')) for obj in before.values() for f in obj.findall(".//field[@name='playlistItemID']")}
    assert len(set(new_item_ids))==len(new_item_ids)
    assert not set(new_item_ids)&(set(original)|native_item_ids|added_ids)
    internal_added={oid for oid in added_ids if built[oid][0]!=4}
    assert all(0<oid<=0x3fffffff for oid in internal_added|set(new_item_ids))
    load_order={oid:i for i,oid in enumerate(built)}
    for oid in (set(built)-set(original))|{MODE,MUSIC_ROOT}:
        for child in after[oid].findall(".//field[@name='ulChildID']"):
            child_id=int(child.get('value'))
            assert load_order[child_id]<load_order[oid], 'Music child must load before its container'
    modes=[0]+[ident('mus_systemType_'+m) for m in ('dynamic_all','dynamic_cinematic','dynamic_cultural','static_cinematic','static_cultural','noMusic')]
    cultures=[ident(x) for x in ('None','european_sfx','east_asian_sfx','african_sfx','middle_east_sfx','indian_sfx','north_american_sfx','south_american_sfx','D008_byzantine_sfx','unknown_future_culture')]
    mode_group=ident('mus_systemType');culture_group=ident('PlayerCulturePrimary')
    war_group=ident('ga_music_war_state')
    switch=object_id('ga_music_war_switch')
    def assert_goblin_destination(destination,states,war):
        expected=object_id('ga_music_'+('war' if war else 'peace')+'_playlist')
        assert destination==expected
    cases=0
    for mode,culture,war in itertools.product(modes,cultures,(False,True)):
        states={mode_group:mode,culture_group:culture,war_group:ident(str(war))}
        assert resolve(before[MODE],states)==resolve(after[MODE],states)
        cases+=1
    # Start at the actual playing root, including the campaign-entry event.
    # Testing only MODE misses the native cultural-intro bypass entirely.
    start_group=ident('Gamestate_startSequence')
    intro_group=ident('mus_culture_track_start')
    starts=[ident(s) for s in ('None','loadingscreen_first','loadingscreen_second','mainmenu','ingame','unknown_future_state')]
    intros=[ident(s) for s in ('None','False','True','unknown_future_state')]
    goblin_cultures={ident('ga_'+c['culture']+'_sfx') for c in COUNTRIES}
    for culture in goblin_cultures:
        startup={start_group:ident('ingame'),intro_group:ident('True'),culture_group:culture}
        old_intro=resolve(before[MUSIC_ROOT],startup)
        assert old_intro!=MODE and resolve(before[old_intro],startup) is None, 'Native startup regression fixture changed'
        assert resolve(after[MUSIC_ROOT],startup)==MODE
    root_cases=0
    for start,intro,culture,mode,war in itertools.product(starts,intros,cultures+sorted(goblin_cultures),modes,(False,True)):
        states={start_group:start,intro_group:intro,culture_group:culture,
                mode_group:mode,war_group:ident(str(war))}
        native=resolve(before[MUSIC_ROOT],states)
        actual=resolve(after[MUSIC_ROOT],states)
        if start==ident('ingame') and culture in goblin_cultures:
            assert actual==MODE, 'Goblin campaign entry must reach automatic mode routing'
            destination=resolve(after[actual],states)
            if mode==ident('mus_systemType_noMusic'):
                assert destination==resolve(before[MODE],states)
            else:
                assert_goblin_destination(destination,states,war)
        else:
            assert actual==native, 'Native root route changed outside goblin campaign entry'
            if actual==MODE:
                assert resolve(after[MODE],states)==resolve(before[MODE],states)
        root_cases+=1
    categories=(args.mod/'main_menu/music/audio_culture_types/goblins_music.txt').read_text(encoding='utf-8-sig')
    for country,mode,war in itertools.product(COUNTRIES,modes,(False,True)):
        culture=ident('ga_'+country['culture']+'_sfx')
        assert 'culture_tag = '+country['culture']+'_gfx' in categories
        states={mode_group:mode,culture_group:culture,war_group:ident(str(war))}
        first=resolve(after[MODE],states)
        if mode==ident('mus_systemType_noMusic'):
            assert first==resolve(before[MODE],states)
        else:
            assert_goblin_destination(first,states,war)
        cases+=1
    assert switch not in built
    native_rules=before[MODE].find(".//list[@name='pRules']")
    new_rules=after[MODE].find(".//list[@name='pRules']")
    def rule_values(rule):
        return [(f.get('name'),f.get('value')) for f in rule.iter('field')]
    assert [rule_values(r) for r in new_rules][:len(native_rules)]==[rule_values(r) for r in native_rules]
    expected_pairs={(object_id('ga_music_peace_playlist'),object_id('ga_music_war_playlist')),
                    (object_id('ga_music_war_playlist'),object_id('ga_music_peace_playlist'))}
    actual_pairs=set()
    for rule in list(new_rules)[len(native_rules):]:
        actual_pairs.add((int(rule.find("field[@name='srcID']").get('value')),
                          int(rule.find("field[@name='dstID']").get('value'))))
        assert rule.find(".//field[@name='eSyncType']").get('value')=='0'
        assert rule.find(".//field[@name='eJumpToType']").get('value')=='0'
    assert actual_pairs==expected_pairs
    for mood in ('peace','war'):
        playlist=after[object_id('ga_music_'+mood+'_playlist')]
        assert int(playlist.find(".//field[@name='DirectParentID']").get('value'))==MODE
        assert int(playlist.find(".//field[@name='OverrideBusId']").get('value'))==1397326711
    # Explicit round-trip mapping check; this does not simulate live Wwise time.
    for culture in goblin_cultures:
        states={culture_group:culture,mode_group:ident('mus_systemType_dynamic_all')}
        for war in (False,True,False):
            states[war_group]=ident(str(war))
            assert_goblin_destination(resolve(after[MODE],states),states,war)
    bank_chunks=dict(chunks((args.mod/BANK_PATH/'sb_music_logic.bnk').read_bytes()))
    embedded={wid:bank_chunks[b'DATA'][offset:offset+size] for wid,offset,size in struct.iter_unpack('<III',bank_chunks[b'DIDX'])}
    for mood in ('peace','war'):
        obj=after[object_id('ga_music_'+mood+'_track')]
        sources=obj.findall(".//field[@name='sourceID']")
        for source in sources:
            media_data=(args.mod/BANK_PATH/'Media'/(source.get('value')+'.wem')).read_bytes()
            assert embedded[int(source.get('value'))]==media_data
            assert int(obj.find(".//field[@name='uInMemoryMediaSize']").get('value'))==len(media_data)
            riff=dict(chunks(media_data[12:]))
            assert struct.unpack_from('<HHIIHH',riff[b'fmt '])==(0xfffe,2,48000,192000,4,16)
            assert len(riff[b'data']) % 4 == 0
            duration=len(riff[b'data'])/192000*1000
            assert abs(float(obj.find(".//field[@name='fSrcDuration']").get('value'))-duration)<0.01
        assert int(obj.find(".//field[@name='ulPluginID']").get('value'))==0x00010001
        assert obj.find(".//field[@name='StreamType']").get('value')=='0'
    catalog_path=Path(BANK_PATH)/'SoundbanksInfo.json'
    native_catalog=json.loads((args.game/'game'/catalog_path).read_text(encoding='utf-8-sig'))
    catalog=json.loads((args.mod/catalog_path).read_text(encoding='utf-8-sig'))
    bank=next(b for b in catalog['SoundBanksInfo']['SoundBanks'] if b['ShortName']=='sb_music_logic')
    added_ids={str(ident('ga_music_'+m+'_wem')) for m in ('peace','war')}
    new_media=[m for m in bank['Media'] if m['Id'] in added_ids]
    assert len(new_media)==2
    for media in new_media:
        assert (args.mod/BANK_PATH/media['Path']).is_file()
        assert media['Streaming']=='false' and media['Location']=='Memory'
    bank['Media']=[m for m in bank['Media'] if m['Id'] not in added_ids]
    for culture in goblin_cultures:
        states={culture_group:culture,mode_group:ident('mus_systemType_dynamic_all')}
        for local_war,native_war in ((False,True),(True,False),(False,True)):
            states.update({war_group:ident(str(local_war)),ident('PlayerAtWar'):ident(str(native_war))})
            assert_goblin_destination(resolve(after[MODE],states),states,local_war)
    for culture,local_war,native_war in itertools.product(goblin_cultures,(False,True),(False,True)):
        states={culture_group:culture,mode_group:ident('mus_systemType_dynamic_all'),
                war_group:ident(str(local_war)),ident('PlayerAtWar'):ident(str(native_war))}
        assert_goblin_destination(resolve(after[MODE],states),states,local_war)
    assert all(int(f.get('value'))!=ident('PlayerAtWar') for oid in (MODE,switch) if oid in after
               for f in after[oid].findall(".//object[@name='Arguments']//field[@name='ulGroup']"))
    for mood,state in [('peace','False'),('war','True')]:
        event=after[ident('ga_music_'+mood)]
        actions=event.findall(".//field[@name='ulActionID']")
        assert len(actions)==1
        action=after[int(actions[0].get('value'))]
        assert action.find("field[@name='ulActionType']").get('value')=='4612'
        assert int(action.find(".//field[@name='ulStateGroupID']").get('value'))==war_group
        assert int(action.find(".//field[@name='ulTargetStateID']").get('value'))==ident(state)
    init_original=dict(chunks((args.game/'game'/BANK_PATH/'Init.bnk').read_bytes()))
    init_built=dict(chunks((args.mod/BANK_PATH/'Init.bnk').read_bytes()))
    original_stmg=init_original[b'STMG'];new_stmg=bytearray(init_built[b'STMG'])
    old_count=struct.unpack_from('<I',original_stmg,10)[0]
    new_count=struct.unpack_from('<I',new_stmg,10)[0]
    assert new_count==old_count+1
    # This version's guarded native groups have zero custom transitions.
    entries=[struct.unpack_from('<III',new_stmg,14+12*i) for i in range(new_count)]
    assert all(e[2]==0 for e in entries)
    indexes=[i for i,e in enumerate(entries) if e[0]==war_group]
    assert len(indexes)==1 and entries[indexes[0]]==(war_group,0,0)
    pos=14+12*indexes[0];del new_stmg[pos:pos+12]
    struct.pack_into('<I',new_stmg,10,old_count)
    init_built[b'STMG']=bytes(new_stmg)
    assert init_built==init_original, 'Native Init content changed beyond one registered group'
    for short_name in ('Init','sb_music_logic'):
        meta=next(b for b in catalog['SoundBanksInfo']['SoundBanks'] if b['ShortName']==short_name)
        custom=[s for s in meta['StateGroups'] if s['Name']=='ga_music_war_state']
        assert len(custom)==1 and custom[0]['Id']==str(war_group)
        meta['StateGroups'].remove(custom[0])
    custom_events=[e for e in bank['Events'] if e['Name'] in ('ga_music_peace','ga_music_war')]
    assert len(custom_events)==2
    for event in custom_events:
        assert event['ActionSetState'][0]['GroupId']==str(war_group)
        bank['Events'].remove(event)
    gui_path=Path('in_game/gui/ingame_topbar.gui')
    native_gui=(args.game/'game'/gui_path).read_bytes()
    gui=(args.mod/gui_path).read_bytes()
    newline=b'\r\n' if b'\r\n' in gui else b'\n'
    begin=newline+b'\t# BEGIN GOBLIN LOCAL MUSIC WATCHERS'+newline
    end=b'\t# END GOBLIN LOCAL MUSIC WATCHERS'+newline
    assert gui.count(begin)==gui.count(end)==1
    start=gui.index(begin);stop=gui.index(end)+len(end)
    assert gui[:start]+gui[stop:]==native_gui, 'Native GUI changed outside watchers'
    watcher=gui[start:stop]
    assert b'Player.GetDiplomacy.IsAtWar' in watcher and b'IsPlayerValid' in watcher
    assert b"Audio_PlayEvent('ga_music_peace', 'music_manager')" in watcher
    assert b"Audio_PlayEvent('ga_music_war', 'music_manager')" in watcher
    assert catalog==native_catalog, 'Unrelated native audio metadata changed'
    report_path=args.report or (ROOT/'reports/goblin-music.json' if args.mod.resolve()==(ROOT/'mod').resolve()
                               else args.mod/'goblin-music-report.json')
    report=json.loads(report_path.read_text())
    report['validation']={'routing_cases':cases,'full_root_routing_cases':root_cases,'unchanged_native_objects':len(original)-2,
        'serialized_bank_parsed':True,'embedded_media_present':True,'media_registered':True,
        'note':'Independent state combinations verified; this is not a live multiplayer test.'}
    report['validation'].update(local_native_war_independence_cases=24,
        latched_native_war_roundtrip_cultures=len(goblin_cultures),
        init_native_content_preserved=True,native_gui_preserved=True,custom_events_set_state_only=True)
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation']))

if __name__=='__main__':main()
