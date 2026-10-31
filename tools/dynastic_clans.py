"""Native dynasty naming, scoped to the five Ashborn countries."""
LOCALIZATION={
 'cm_ironfang_monarchy_desc':'The Ironfang Crown rules for life. Its musters provide +50% monthly manpower. The strongest eligible adult Ashborn man of the ruling dynasty inherits. A new ruling dynasty gives the country its clan name. The succession law may be changed through normal monarchy institutions.',
 'cm_rule_of_the_strongest':'Strongest of the Ruling Clan',
 'cm_rule_of_the_strongest_desc':'Only eligible adult Ashborn men of the ruling dynasty may inherit. Military ability decides; Administrative ability and then age break ties. Foreign rulers, children and characters barred from ruling are excluded. No eligible dynasty member means no eligible heir under this law; unrelated courtiers are not a fallback.',
}

def build(b,game,out):
    native=b.read(game,'in_game/common/on_action/_hardcoded.txt')
    assert 'on_new_ruler = {' in native and 'change_country_dynastic_name = {}' in native
    # The native rename skips fiefdoms and unions (the ruler is the overlord's); so must we, or a crown
    # made a fiefdom takes its overlord's clan name (a Reefhook fiefdom of Cindermaw became "Cindermaw").
    assert 'any_union_partner' in native and 'overlord ?= {' in native
    tags=' '.join('tag = '+c['tag'] for c in b.CFG['countries'])
    restores='\n'.join(f"        if = {{ limit = {{ tag = {c['tag']} }} ga_restore_clan_country_name = {{ tag = {c['tag']} }} }}" for c in b.CFG['countries'])
    b.write(out,'in_game/common/scripted_triggers/goblins_dynastic_clans.txt','''# Mirrors the native on_new_ruler guard: this crown's ruler is also its overlord's or a union partner's.
ga_clan_ruler_is_shared = {
    has_ruler = yes
    OR = {
        AND = {
            is_subject = yes
            overlord ?= { ruler ?= { this = root.ruler } }
        }
        any_union_partner = { ruler ?= { this = root.ruler } }
    }
}
''')
    b.write(out,'in_game/common/scripted_effects/goblins_dynastic_clans.txt',f'''# Native effect updates the dynasty name and adjective. Stable country tags remain intact.
ga_update_dynastic_clan_name = {{
    # A shared ruler's clan is not this crown's: return to the crown's own name and flag once.
    if = {{
        limit = {{
            OR = {{ {tags} }}
            has_variable = ga_named_dynasty
            ga_clan_ruler_is_shared = yes
        }}
{restores}
        remove_variable = ga_named_dynasty
    }}
    if = {{
        limit = {{
            OR = {{ {tags} }}
            government_type = government_type:monarchy
            has_regent = no
            ga_clan_ruler_is_shared = no
            ruler ?= {{ has_dynasty = no }}
        }}
        ruler = {{ found_dynasty = random }}
    }}
    if = {{
        limit = {{
            OR = {{ {tags} }}
            government_type = government_type:monarchy
            has_regent = no
            ga_clan_ruler_is_shared = no
            ruler ?= {{ has_dynasty = yes }}
            OR = {{
                NOT = {{ has_variable = ga_named_dynasty }}
                NOT = {{ ruler = {{ dynasty = root.var:ga_named_dynasty }} }}
            }}
        }}
        ruler = {{ save_scope_as = new_ruler }}
        change_country_dynastic_name = {{}}
        set_variable = {{ name = ga_named_dynasty value = ruler.dynasty }}
    }}
}}
ga_restore_clan_country_name = {{
    change_country_name = $tag$
    hidden_effect = {{
        change_country_flag = $tag$
        change_country_adjective = $tag$_ADJ
    }}
}}
''')
    b.write(out,'in_game/common/on_action/goblins_dynastic_clans.txt',f'''# Additive hooks leave native on_new_ruler actions intact.
on_new_ruler = {{ on_actions = {{ ga_dynastic_clan_ruler }} }}
monthly_country_pulse = {{ on_actions = {{ ga_dynastic_clan_monthly }} }}
ga_dynastic_clan_ruler = {{
    trigger = {{ OR = {{ {tags} }} }}
    effect = {{ ga_update_dynastic_clan_name = yes }}
}}
# Reconciles first-month initialization, load/regency and later dynasty reassignment.
ga_dynastic_clan_monthly = {{
    trigger = {{ OR = {{ {tags} }} }}
    effect = {{ ga_update_dynastic_clan_name = yes }}
}}
''')

def verify(b,out):
    law=(out/'in_game/common/heir_selections/goblins_ashborn_isles.txt').read_text(encoding='utf-8-sig')
    assert 'all_in_dynasty = yes' in law and 'dynasty = scope:target.last_valid_ruler.dynasty' in law
    assert 'allow_female = no' in law and 'allow_children = no' in law and 'value = root.mil' in law
    effect=(out/'in_game/common/scripted_effects/goblins_dynastic_clans.txt').read_text(encoding='utf-8-sig')
    assert 'change_country_dynastic_name = {}' in effect and 'value = ruler.dynasty' in effect
    assert 'has_regent = no' in effect and 'change_tag' not in effect
    assert effect.count('ga_clan_ruler_is_shared = no')==2 and 'remove_variable = ga_named_dynasty' in effect
    shared=(out/'in_game/common/scripted_triggers/goblins_dynastic_clans.txt').read_text(encoding='utf-8-sig')
    assert 'overlord ?=' in shared and 'any_union_partner' in shared
    matriarchy=(out/'in_game/common/heir_selections/shatterfin.txt').read_text(encoding='utf-8-sig')
    assert 'allow_male = no' in matriarchy and 'value = root.character_age' in matriarchy
    return {'dynasty_only':True,'ranking':'military, administration, age','shatterfin_maternal_seniority_preserved':True,'native_dynamic_name_effect':True,'skips_fiefdoms_and_unions':True,'engine_tested':False}
