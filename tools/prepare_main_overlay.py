"""Refresh only authored runtime art, culture tags and text for the main installer.

No terrain rebuild or user mod installation. The bundled release is immutable;
the main installer applies these checksum-listed files before normal installation.
"""
import hashlib,json
from pathlib import Path
import build as b,archipelago,export_goblin_models,verify_goblin_models,build_goblin_portraits
ROOT=b.ROOT

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--game',type=Path);args=ap.parse_args()
    output=ROOT/'mod'
    import exploration
    if not args.game:
        ap.error('--game is required to validate exploration locations and areas')
    exploration.build(b,args.game,output,validate_setup=False)
    import economy
    economy.starting_trades(b,args.game,output)
    import export_event_art
    export_event_art.build(output)
    import build_clan_flags
    build_clan_flags.build(output)
    report=export_goblin_models.build(output)
    portraits=build_goblin_portraits.build(output)
    import verify_goblin_portraits
    portraits["validation"]=verify_goblin_portraits.verify(output,args.game)
    verification=verify_goblin_models.verify(output,args.game)
    countries=b.CFG['countries']
    b.write(output,'in_game/common/cultures/goblins_ashborn_isles.txt','\n'.join(
        f'{c["culture"]} = {{ language = {c["culture"]}_dialect color = rgb {{ {" ".join(map(str,c["color"]))} }} tags = {{ european_gfx {c["culture"]}_gfx }} culture_groups = {{ cm_goblin_group }} opinions = {{ }} }}' for c in countries)+'\n')
    import ashborn_names
    ashborn_names.build_names(b,output)
    b.localization(output);archipelago.add_localization(b,output)
    import dynastic_clans,ashen_covenant
    dynastic_clans.build(b,args.game,output)
    ashen_covenant.build(output)
    import goblin_longevity
    goblin_longevity.build(b,args.game,output)
    paths=[p for prefix in ['in_game/gfx/models/units/ashborn_goblins','in_game/gfx/models/schematics','in_game/gfx/graphical_culture_types','main_menu/gfx/unit_graphics/units','main_menu/gfx/animation_state_machines'] for p in (output/prefix).rglob('*') if p.is_file()]
    paths.extend([output/'in_game/common/cultures/goblins_ashborn_isles.txt',output/'main_menu/localization/english/goblins_ashborn_isles_l_english.yml',output/'main_menu/gfx/unit_graphics/attachments/zz_ashborn_goblins.txt'])
    paths.append(output/export_goblin_models.TEXTURE_REGISTRATION)
    paths.extend(p for prefix in ['in_game/gfx/models/portraits/ashborn','in_game/common/ethnicities','main_menu/gfx/portraits'] for p in (output/prefix).rglob('*') if p.is_file())
    paths.append(output/'in_game/common/genes/zz_ashborn_portraits.txt')
    paths.append(output/'in_game/common/genes/zz_ashborn_outfits.txt')
    paths.append(output/'in_game/common/languages/goblins_ashborn_isles.txt')
    paths.append(output/'in_game/common/auto_modifiers/goblins_longevity.txt')
    paths.extend(output/p for p in ['main_menu/common/modifier_type_definitions/ashen_covenant.txt',
                                   'in_game/common/religions/goblins_ashborn_isles.txt',
                                   'main_menu/localization/english/ashen_covenant_l_english.yml'])
    paths.extend(output/p for p in ['in_game/common/on_action/goblins_exploration.txt','in_game/events/goblins_exploration.txt','main_menu/localization/english/goblins_exploration_l_english.yml'])
    from event_art import runtime_paths
    paths.extend(output / p for p in runtime_paths())
    paths.extend(output / p for p in build_clan_flags.runtime_paths())
    paths.append(output / 'in_game/events/goblins_ashborn_isles.txt')
    # 0.6.4.1: normalized ports.csv (LF, no trailing empty row) ships as an
    # overlay over the 0.6.4 terrain/map base. archipelago.build_map now emits
    # the same bytes; after any full map rebuild, copy its ports.csv here.
    paths.append(output / 'in_game/map_data/ports.csv')
    # 0.6.5: three goblin locations used 'tar', which has no raw-material RGO in
    # EU5 1.3.11 (they could not be built up). The corrected location_templates.txt
    # ships as an overlay over the reused map base; archipelago.build_map emits the
    # same lines from data/island.json. After any full map rebuild, copy it here.
    paths.append(output / 'in_game/map_data/location_templates.txt')
    # Retain the authored gameplay/UI modules when refreshing portrait assets.
    # A partial manifest previously dropped the Gathering and Covenant panels.
    for prefix in ['in_game/common','in_game/events','in_game/gui','main_menu/common','main_menu/localization']:
        paths.extend(p for p in (output/prefix).rglob('*')
                     if p.is_file() and p.name.startswith(('goblins_','ga_','ashen_covenant')))
    for prefix in ['loading_screen/sound','main_menu/music/audio_culture_types']:
        paths.extend(p for p in (output/prefix).rglob('*') if p.is_file())
    if (output/'loading_screen/sound/goblins_music_manifest.json').exists():
        paths.append(output/'in_game/gui/ingame_topbar.gui')
    paths=sorted(set(paths),key=lambda p:p.relative_to(output).as_posix())
    manifest={'base_release':b.CFG['version'],'stage':'development-models-and-culture-names','engine_tested':False,
              'files':[{'path':p.relative_to(output).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
    (ROOT/'data/main_overlay.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    import build_infantry_art
    infantry=build_infantry_art.build(args.game,output)
    build_infantry_art.update_manifest(output,infantry)
    manifest_path=ROOT/'data/main_overlay.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['files'].sort(key=lambda item:item['path'])
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (ROOT/'art/infantry/validation.json').write_text(json.dumps(infantry,indent=2)+'\n')
    (ROOT/'art/models/goblins/native_validation.json').write_text(json.dumps(verification,indent=2)+'\n')
    (ROOT/'art/models/goblins/native_export.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'art/models/goblins/portrait_export.json').write_text(json.dumps(portraits,indent=2)+'\n')
    print(json.dumps({'overlay_files':len(paths),'verification':verification},indent=2))

if __name__=='__main__':main()
