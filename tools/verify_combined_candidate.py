from ashborn_roster import TAGS
"""Guard the prior release fixes alongside the newer gameplay candidate."""
import re
from verify_055 import parse, flatten

def verify(read):
    asset = read('in_game/gfx/models/portraits/ashborn/ashborn_features.asset')
    assert asset.count('shader = "portrait_skin"') == 3 * len(TAGS)
    assert asset.count('file = "ssao.dds" index = 3') == 3 * len(TAGS)
    assert asset.count('portrait_decal = { body_part = head }') == 3 * len(TAGS)
    assert 'portrait_attachment' not in asset
    assert 'ear_base.dds' in asset
    genes = read('in_game/common/genes/zz_ashborn_portraits.txt')
    assert 'cm_ashborn' in genes and 'old_forehead' in genes
    sites = read('in_game/common/holy_sites/ashen_covenant.txt')
    levels = re.findall(r'importance = (\d+)', sites)
    # 12 sites plus Maw Rock and The Kiln Stair (0.6.7)
    assert len(levels) == 14 and set(levels) == set('12345')
    panel = read('in_game/gui/panels/situation/ga_gathering_of_five.gui')
    for tag in TAGS:
        assert panel.count("[GetCountry('"+tag+"')]") == 1
    assert panel.count('text = "ga_gathering_annexed"') == len(TAGS)
    body = panel[panel.index('blockoverride "situation_panel_main_content"'):]
    assert 'ga_ui_compact_route' in body and 'ga_ui_homeland_progress' in body
    assert 'ga_commission_voyage' not in panel
    assert 'ga_commission_voyage' in read('in_game/gui/panels/situation/ga_ashborn_voyages.gui')
    values = dict((k,v) for k,_,v in parse(read('in_game/common/script_values/ga_gathering_ui.txt')))
    assert values['ga_gathering_realm_locations'] == [('value','=','ga_ui_homeland_count')]
    assert {v for k,_,v in flatten(values['ga_gathering_crown_status']) if k=='is_subject_type'} == {'vassal','ga_compact_autonomy','ga_compact_protection'}
    return {'skin_materials':3*len(TAGS),'holy_sites':len(levels),'founding_crown_rows':len(TAGS),
            'shared_current_ownership_counter':True,'dedicated_voyage_situation':True,
            'engine_visual_acceptance':False}
