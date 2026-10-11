"""Build a version-bound native music-bank overlay from a wwiser XML dump.

Never modifies the installed game. XML supplies checked offsets into the native
bank, rather than guessing the layout of Wwise's variable-length structures.
"""
import argparse
import hashlib
import copy
import json
import struct
import subprocess
import xml.etree.ElementTree as ET
import uuid
from pathlib import Path
from ashborn_roster import COUNTRIES

ROOT = Path(__file__).resolve().parents[1]
BASE_HASH = '53ab8b27030abe1ddc5ba46c487df8f0beecd4c95878038644d87efca7fed1b7'
INIT_HASH = 'a10a30b594e11a210a736f74f135c94574689ffcd8d68b994dfab31000e87682'
TOPBAR_HASH = '078c2ef89afbc1a034b9d4ee1abd101b99b09351c96d8c0a7442ffd7439e1ae2'
BANK_PATH = 'loading_screen/sound/banks/windows'
MODE = 194639714
MUSIC_ROOT = 337896570
WAR_SWITCH = 481495805
P32 = lambda n: struct.pack('<I', n)

def ident(name):
    value = 2166136261
    for char in name.lower().encode('ascii'):
        value = ((value * 16777619) & 0xffffffff) ^ char
    return value

def internal_ident(name):
    """Internal object namespace; never apply this to named game syncs/media."""
    value = ident(name)
    return value & 0x3fffffff

def chunks(data):
    offset = 0
    while offset < len(data):
        key, size = struct.unpack_from('<4sI', data, offset)
        assert offset + 8 + size <= len(data)
        yield key, data[offset+8:offset+8+size]
        offset += 8 + size
    assert offset == len(data)

def chunk(key, data):
    return key + P32(len(data)) + data

def pcm_wem(master, ffmpeg):
    audio = subprocess.check_output([str(ffmpeg), '-v', 'error', '-i', str(master),
        '-ar', '48000', '-ac', '2', '-af', 'loudnorm=I=-20:TP=-2:LRA=9',
        '-c:a', 'pcm_s16le', '-f', 's16le', 'pipe:1'])
    # Wwise's 24-byte extensible PCM format, stereo channel layout.
    fmt = struct.pack('<HHIIHHHHI', 0xfffe, 2, 48000, 192000, 4, 16, 6, 0, 0x3102)
    body = b'WAVE' + chunk(b'fmt ', fmt) + chunk(b'JUNK', bytes(4)) + chunk(b'data', audio)
    return b'RIFF' + P32(len(body)) + body

def tree_bytes(node):
    nodes = [None]
    def emit(index, key, value):
        if isinstance(value, dict):
            start = len(nodes)
            ordered = sorted(value.items())
            nodes.extend([None] * len(ordered))
            nodes[index] = struct.pack('<IHHHH', key, start, len(ordered), 50, 100)
            for i, (k, v) in enumerate(ordered):
                emit(start+i, k, v)
        else:
            nodes[index] = struct.pack('<IIHH', key, value, 50, 100)
    emit(0, 0, node)
    return b''.join(nodes)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', type=Path, required=True)
    ap.add_argument('--xml', type=Path, required=True)
    ap.add_argument('--init-xml', type=Path, required=True, help='Native Init XML for custom state registration')
    ap.add_argument('--output', type=Path, default=ROOT/'mod')
    ap.add_argument('--report', type=Path, help='Report destination; custom outputs default to their own report')
    ap.add_argument('--ffmpeg', type=Path, help='Regenerate PCM WEM derivatives from the approved MP3 masters')
    args = ap.parse_args()
    base = (args.game/'game'/BANK_PATH/'sb_music_logic.bnk').read_bytes()
    assert hashlib.sha256(base).hexdigest() == BASE_HASH, 'Unsupported native bank; re-audit before rebuilding'
    xml = ET.parse(args.xml).getroot()
    objects = {}
    for obj in xml.iter('object'):
        field = obj.find("field[@name='ulID']")
        if field is not None:
            objects[int(field.get('value'))] = obj

    def fields(obj, name):
        return [f for f in obj.iter('field') if f.get('name') == name and f.get('offset')]

    def offset(obj, name):
        return int(fields(obj, name)[0].get('offset'))

    def edits_for(obj, name, data):
        return [(int(f.get('offset')), len(data), data) for f in fields(obj, name)]

    def children(obj, ids):
        start = offset(obj, 'ulNumChilds')
        oldcount = int(fields(obj, 'ulNumChilds')[0].get('value'))
        return (start, 4+4*oldcount, P32(len(ids))+b''.join(map(P32, ids)))

    def switch_tail(obj, groups, mapping):
        start = offset(obj, 'bIsContinuePlayback')
        end = offset(obj, 'ulID') + int(fields(obj, 'dwSectionSize')[0].get('value'))
        tree = tree_bytes(mapping)
        data = b'\x01' + P32(len(groups)) + b''.join(map(P32, groups))
        data += b'\x01'*len(groups) + P32(len(tree)) + b'\x00' + tree
        return (start, end-start, data)

    def render(objid, newid, edits):
        obj = objects[objid]
        start = offset(obj, 'ulID')
        size = int(fields(obj, 'dwSectionSize')[0].get('value'))
        data = bytearray(base[start:start+size])
        assert struct.unpack_from('<I', data)[0] == objid
        edits = [(start, 4, P32(newid))] + edits
        for pos, length, replacement in sorted(edits, reverse=True):
            data[pos-start:pos-start+length] = replacement
        kind = int(fields(obj, 'eHircType')[0].get('value'))
        return bytes([kind])+P32(len(data))+data

    goblin_states = {ident('ga_'+c['culture']+'_sfx') for c in COUNTRIES}
    object_id = lambda name: internal_ident(name)
    war_group = ident('ga_music_war_state')
    internal_names = ['ga_music_'+m+'_'+kind for m in ('peace','war') for kind in ('track','segment','playlist')]
    internal_names += ['ga_'+m+'_'+kind for m in ('peace','war') for kind in ('root','leaf')]
    internal_names += ['ga_music_'+m+'_set_state_action' for m in ('peace','war')]
    internal_ids = [object_id(name) for name in internal_names]
    native_internal_ids = set(objects) | {int(f.get('value')) for f in xml.iter('field') if f.get('name')=='playlistItemID'}
    assert len(set(internal_ids))==len(internal_ids) and 0 not in internal_ids, 'Custom internal ID collision'
    assert not (set(internal_ids)&native_internal_ids), 'Custom internal ID collides with native object/item'
    playlist_ids = {m: object_id('ga_music_'+m+'_playlist') for m in ('peace','war')}
    additions = []
    output = args.output/BANK_PATH
    output.mkdir(parents=True, exist_ok=True)
    media = []
    for mood, filename in [('peace','ashen_harbors'), ('war','black_sails_ashen_teeth')]:
        track = object_id('ga_music_'+mood+'_track')
        segment = object_id('ga_music_'+mood+'_segment')
        wemid = ident('ga_music_'+mood+'_wem')
        wem_path = ROOT/'art/music'/f'{filename}.wem'
        if args.ffmpeg:
            wem_path.write_bytes(pcm_wem(wem_path.with_suffix('.mp3'), args.ffmpeg))
        wem = wem_path.read_bytes()
        riff = dict(chunks(wem[12:]))
        fmt = riff[b'fmt ']
        assert len(fmt) == 24 and struct.unpack_from('<HHIIHH', fmt) == (0xfffe, 2, 48000, 192000, 4, 16), 'Expected tested Wwise PCM format; rebuild with --ffmpeg'
        duration = len(riff[b'data']) / 192000 * 1000
        assert 59000 <= duration <= 61000
        dest = output/'Media'/f'{wemid}.wem'
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(wem)
        media.append({'Id':str(wemid),'ShortName':dest.name,'Path':'Media/'+dest.name})
        obj = objects[0x13771d69]
        edits = edits_for(obj,'sourceID',P32(wemid))
        edits += edits_for(obj,'ulPluginID',P32(0x00010001))
        edits += edits_for(obj,'uInMemoryMediaSize',P32(len(dest.read_bytes())))
        edits += edits_for(obj,'DirectParentID',P32(segment))
        edits += edits_for(obj,'fSrcDuration',struct.pack('<d',duration))
        # Embed the short prototype tracks to avoid loose-stream lookup dependencies.
        edits += edits_for(obj,'StreamType',b'\x00')
        additions.append(render(0x13771d69,track,edits))
        # Match the direct-playback control: no inherited loudness-analysis
        # requirement on PCM media that has no Wwise analysis chunk.
        obj = objects[1052937988]
        edits = [children(obj,[track])]
        edits += edits_for(obj,'DirectParentID',P32(playlist_ids[mood]))
        edits += edits_for(obj,'OverrideBusId',P32(0))
        edits += edits_for(obj,'fDuration',struct.pack('<d',duration))
        positions = fields(obj,'fPosition')
        edits += [(int(positions[-1].get('offset')),8,struct.pack('<d',duration))]
        additions.append(render(1052937988,segment,edits))
        obj = objects[0x3de374bf]
        edits = [children(obj,[segment])]
        edits += edits_for(obj,'DirectParentID',P32(MODE))
        edits += edits_for(obj,'OverrideBusId',P32(1397326711))
        start = offset(obj,'numPlaylistItems')
        end = offset(obj,'ulID')+int(fields(obj,'dwSectionSize')[0].get('value'))
        # Infinite sequence of one segment. State changes interrupt via switch rules.
        item = struct.Struct('<IIIiHHHIHBB')
        playlist = P32(2)+item.pack(0,object_id('ga_'+mood+'_root'),1,0,0,0,0,1,0,0,0)
        playlist += item.pack(segment,object_id('ga_'+mood+'_leaf'),0,-1,1,0,0,1,0,0,0)
        edits.append((start,end-start,playlist))
        additions.append(render(0x3de374bf,playlist_ids[mood],edits))

    obj = objects[WAR_SWITCH]
    # Clone the native immediate transition as a symmetric goblin crossfade.
    rules = obj.find(".//list[@name='pRules']")
    first = list(rules)[0]
    rule_start = int(next(first.iter('field')).get('offset'))
    rule = bytearray(base[rule_start:rule_start+64])
    for f in first.iter('field'):
        if f.get('name')=='transitionTime':
            rel=int(f.get('offset'))-rule_start
            rule[rel:rel+4]=struct.pack('<i',1500)
    obj = objects[MODE]
    native_tree = obj.find(".//object[@name='AkDecisionTree']")
    mapping = {}
    for node in native_tree.iter('object'):
        leaf = node.find("field[@name='audioNodeId']")
        if leaf is not None:
            key=int(node.find("field[@name='key']").get('value'))
            native=int(leaf.get('value'))
            mapping[key]={0:{0:native}}
            if key != ident('mus_systemType_noMusic'):
                mapping[key].update({g:{0:playlist_ids['peace'],ident('None'):playlist_ids['peace'],
                    ident('False'):playlist_ids['peace'],ident('True'):playlist_ids['war']} for g in goblin_states})
    oldchildren = [int(f.get('value')) for f in fields(obj,'ulChildID')]
    mode_groups = [ident('mus_systemType'),ident('PlayerCulturePrimary')]
    mode_edits = []
    mode_groups.append(war_group)
    # Keep native rules byte-for-byte and append only explicit goblin pairs.
    start = offset(obj,'numRules')
    end = offset(obj,'bIsContinuePlayback')
    native_count = int(fields(obj,'numRules')[0].get('value'))
    extra_rules = []
    for source, target in [(playlist_ids['peace'],playlist_ids['war']),
                           (playlist_ids['war'],playlist_ids['peace'])]:
        explicit = bytearray(rule)
        explicit[4:8] = P32(source)
        explicit[12:16] = P32(target)
        extra_rules.append(explicit)
    mode_edits.append((start,end-start,P32(native_count+2)+base[start+4:end]+b''.join(extra_rules)))
    mode_children = list(playlist_ids.values())
    changed = render(MODE, MODE, mode_edits+[children(obj,oldchildren+mode_children),
        switch_tail(obj,mode_groups,mapping)])
    # EnterGameCoA posts mus_culture_track_start, making the native root
    # bypass MODE for its culture intro. That intro has no goblin fallback.
    # Intercept only goblin ingame intros; retain every native route otherwise.
    obj = objects[MUSIC_ROOT]
    root_node = obj.find(".//object[@name='AkDecisionTree']/list/object")
    root_mapping = {}
    for game_node in root_node.findall('list/object'):
        game_key = int(game_node.find("field[@name='key']").get('value'))
        root_mapping[game_key] = {}
        for intro_node in game_node.findall('list/object'):
            intro_key = int(intro_node.find("field[@name='key']").get('value'))
            target = int(intro_node.find("field[@name='audioNodeId']").get('value'))
            routes = {0: target}
            if game_key == ident('ingame') and intro_key == ident('True'):
                routes.update({g: MODE for g in goblin_states})
            root_mapping[game_key][intro_key] = routes
    changed_root = render(MUSIC_ROOT, MUSIC_ROOT, [switch_tail(obj,
        [ident('Gamestate_startSequence'), ident('mus_culture_track_start'),
         ident('PlayerCulturePrimary')], root_mapping)])
    replacements = {MODE: changed, MUSIC_ROOT: changed_root}
    for mood,state in [('peace','False'),('war','True')]:
        action_id=object_id('ga_music_'+mood+'_set_state_action')
        obj=objects[481567279]
        action_edits=edits_for(obj,'idExt',P32(ident(state)))
        action_edits+=edits_for(obj,'ulStateGroupID',P32(war_group))
        action_edits+=edits_for(obj,'ulTargetStateID',P32(ident(state)))
        additions.append(render(481567279,action_id,action_edits))
        obj=objects[13097112]
        additions.append(render(13097112,ident('ga_music_'+mood),edits_for(obj,'ulActionID',P32(action_id))))
    result = []
    original_ids=set()
    for kind,payload in chunks(base):
        if kind==b'HIRC':
            count=struct.unpack_from('<I',payload)[0]; pos=4; records=[]
            for _ in range(count):
                size=struct.unpack_from('<I',payload,pos+1)[0]
                oid=struct.unpack_from('<I',payload,pos+5)[0]
                original_ids.add(oid)
                # Music containers resolve their children during bank loading.
                # Emit tracks -> segments -> playlists before MODE.
                if oid==MODE:
                    records.extend(additions)
                records.append(replacements.get(oid, payload[pos:pos+5+size]))
                pos+=5+size
            assert pos==len(payload)
            for record in additions:
                oid=struct.unpack_from('<I',record,5)[0]
                assert oid not in original_ids, 'ID collision'
                original_ids.add(oid)
            payload=P32(count+len(additions))+b''.join(records)
        result.append(chunk(kind,payload))
    embedded = bytearray(); index = bytearray()
    for entry in sorted(media, key=lambda x: int(x['Id'])):
        embedded.extend(b'\0' * (-len(embedded) % 16))
        data = (output/entry['Path']).read_bytes()
        index.extend(struct.pack('<III',int(entry['Id']),len(embedded),len(data)))
        embedded.extend(data)
    result[1:1] = [chunk(b'DIDX',bytes(index)),chunk(b'DATA',bytes(embedded))]
    (output/'sb_music_logic.bnk').write_bytes(b''.join(result))
    # Preserve the complete native catalogue while registering the embedded tracks.
    catalog = json.loads((args.game/'game'/BANK_PATH/'SoundbanksInfo.json').read_text(encoding='utf-8-sig'))
    bank = next(b for b in catalog['SoundBanksInfo']['SoundBanks'] if b['ShortName']=='sb_music_logic')
    bank['Media'].extend(dict(m, Language='SFX', Streaming='false', Location='Memory') for m in media)
    init=(args.game/'game'/BANK_PATH/'Init.bnk').read_bytes()
    assert hashlib.sha256(init).hexdigest()==INIT_HASH, 'Unsupported Init bank; re-audit before rebuilding'
    init_tree=ET.parse(args.init_xml).getroot()
    settings=init_tree.find("object[@name='GlobalSettingsChunk']")
    count_field=settings.find("field[@name='ulNumStateGroups']")
    count_pos=int(count_field.get('offset'))
    group_list=settings.find("list[@name='StateGroups']")
    assert all(int(g.find("field[@name='ulStateGroupID']").get('value'))!=war_group for g in group_list)
    insert_pos=int(settings.find("field[@name='ulNumSwitchGroups']").get('offset'))
    for g in group_list:
        field=g.find("field[@name='ulStateGroupID']")
        if int(field.get('value'))>war_group:
            insert_pos=int(field.get('offset'));break
    patched=bytearray(init)
    chunk_size=int(settings.find("field[@name='dwChunkSize']").get('offset'))
    struct.pack_into('<I',patched,count_pos,len(group_list)+1)
    struct.pack_into('<I',patched,chunk_size,struct.unpack_from('<I',init,chunk_size)[0]+12)
    patched[insert_pos:insert_pos]=struct.pack('<III',war_group,0,0)
    (output/'Init.bnk').write_bytes(patched)
    init_sha=hashlib.sha256(patched).hexdigest()
    def guid(name):
        return '{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'goblins-music/'+name)).upper()+'}'
    state_meta=copy.deepcopy(next(s for s in bank['StateGroups'] if s['Name']=='PlayerAtWar'))
    state_meta.update(Id=str(war_group),Name='ga_music_war_state',GUID=guid('ga_music_war_state'))
    for state in state_meta['States']:
        state['GUID']=guid('ga_music_war_state/'+state['Name'])
    bank['StateGroups'].append(state_meta)
    init_meta=next(b for b in catalog['SoundBanksInfo']['SoundBanks'] if b['ShortName']=='Init')
    init_meta['StateGroups'].append(copy.deepcopy(state_meta))
    template=next(e for e in bank['Events'] if e['Name']=='mus_culture_track_start')
    for mood,state in [('peace','False'),('war','True')]:
        event=copy.deepcopy(template);name='ga_music_'+mood
        event.update(Id=str(ident(name)),Name=name,GUID=guid(name))
        event['ActionSetState']=[{'GroupId':str(war_group),'Id':str(ident(state)),
            'Name':state,'GUID':guid('ga_music_war_state/'+state)}]
        bank['Events'].append(event)
    gui_path=Path('in_game/gui/ingame_topbar.gui')
    gui=(args.game/'game'/gui_path).read_bytes()
    assert hashlib.sha256(gui).hexdigest()==TOPBAR_HASH, 'Unsupported native topbar; re-audit before rebuilding'
    newline=b'\r\n' if b'\r\n' in gui else b'\n'
    watcher='\n\t# BEGIN GOBLIN LOCAL MUSIC WATCHERS\n'
    for mood,condition in [('peace','Not(Player.GetDiplomacy.IsAtWar)'),('war','Player.GetDiplomacy.IsAtWar')]:
        watcher+=f'''\twidget = {{
\t\tname = "ga_music_{mood}_watcher"
\t\tsize = {{ 1 1 }}
\t\talwaystransparent = yes
\t\tfilter_mouse = none
\t\tvisible = "[And(IsPlayerValid, {condition})]"
\t\tstate = {{
\t\t\tname = _show
\t\t\tduration = 0.01
\t\t\ton_start = "[Audio_PlayEvent('ga_music_{mood}', 'music_manager')]"
\t\t}}
\t}}
'''
    watcher+='\t# END GOBLIN LOCAL MUSIC WATCHERS\n'
    anchor=b'\tname = "ingame_topbar"'+newline+b'\tlayer = topbar'+newline
    assert gui.count(anchor)==1
    gui_output=args.output/gui_path
    gui_output.parent.mkdir(parents=True,exist_ok=True)
    gui_output.write_bytes(gui.replace(anchor,anchor+watcher.encode().replace(b'\n',newline),1))
    (output/'SoundbanksInfo.json').write_text(json.dumps(catalog,separators=(',',':')),encoding='utf-8')
    loc = args.output/'main_menu/localization/english/goblins_music_l_english.yml'
    loc.parent.mkdir(parents=True,exist_ok=True)
    loc.write_text('l_english:\n ga_music_peace:0 "Ashen Harbors"\n ga_music_war:0 "Black Sails, Ashen Teeth"\n',encoding='utf-8-sig')
    (args.output/'loading_screen/sound/goblins_music_manifest.json').write_text(
        json.dumps({'base_sha256':BASE_HASH,'init_base_sha256':INIT_HASH,
                    'topbar_base_sha256':TOPBAR_HASH,'supported_game_version':'1.3.11'},indent=2)+'\n')
    # Keep native bank name/ID for deterministic virtual-filesystem replacement.
    # Existing native media references are untouched; new media live alongside them.
    categories='\n'.join('ga_'+c['culture']+'_sfx = { priority = 200 culture_tag = '+c['culture']+'_gfx }' for c in COUNTRIES)+'\n'
    path=args.output/'main_menu/music/audio_culture_types/goblins_music.txt'
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(categories,encoding='utf-8-sig')
    report={'base_sha256':BASE_HASH,'bank_sha256':hashlib.sha256(b''.join(result)).hexdigest(),
        'modified_native_objects':[MODE,MUSIC_ROOT],'added_objects':len(additions),
        'goblin_states':sorted(goblin_states),'routes':{str(k):v for k,v in mapping.items()},
        'playlists':playlist_ids,'media':media,'runtime_verified':False,'multiplayer_verified':False}
    report['init_base_sha256']=INIT_HASH
    report['init_sha256']=init_sha
    report_path = args.report or (ROOT/'reports/goblin-music.json' if args.output.resolve()==(ROOT/'mod').resolve()
                                  else args.output/'goblin-music-report.json')
    report_path.parent.mkdir(parents=True,exist_ok=True)
    if report_path.exists():
        prior = json.loads(report_path.read_text())
        if 'runtime_observations' in prior:
            # Historical observations remain labelled by candidate; a rebuild
            # always resets current runtime acceptance above.
            report['runtime_observations'] = prior['runtime_observations']
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'added_objects':len(additions),'cultures':len(goblin_states)}))

if __name__=='__main__': main()
