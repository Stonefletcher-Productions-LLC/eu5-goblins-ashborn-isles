"""Native-style Gathering presentation; read-only live values, no saved counters."""
import sworn_pacts

def build(write, loc, out, homeland, tags):
    write(out, 'in_game/common/script_values/ga_gathering_ui.txt', 'ga_gathering_realm_locations = { value = ga_ui_homeland_count }\nga_gathering_crown_status = {\n    value = 0\n    if = { limit = { ga_independent_goblin = yes } add = 1 }\n    else_if = { limit = { is_junior_partner = yes } add = 3 }\n    else_if = { limit = { OR = { is_subject_type = vassal is_subject_type = ga_compact_autonomy is_subject_type = ga_compact_protection } } add = 2 }\n    else = { add = 4 }\n}\n' + sworn_pacts.step_values())
    status = "Country.MakeScope.ScriptValue('ga_gathering_crown_status')"
    independent = "EqualTo_CFixedPoint(%s, '(CFixedPoint)1')" % status
    # One line per ladder step; only the viewer's current step with this crown shows.
    pact_steps = ''.join(f'''                        text_single = {{
                            visible = "[And(Country.Exists, EqualTo_CFixedPoint(GetPlayer.MakeScope.ScriptValue('ga_pact_step_TAG'), '(CFixedPoint){i}'))]"
                            layoutpolicy_horizontal = expanding
                            fontsize = 13
                            autoresize = yes
                            text = "ga_pact_step_{key}"
                            tooltip = "ga_pact_step_{key}_tt"
                        }}
''' for i, (key, _, _) in enumerate(sworn_pacts.STEPS))
    rows = []
    for tag in tags:
        # Fixed founding-country contexts survive annexation and restored countries;
        # they do not depend on a start-only saved participant list.
        rows.append('''
            vbox = {
                datacontext = "[GetCountry('TAG')]"
                layoutpolicy_horizontal = expanding
                using = bg_paper_card
                using = bg_cabinet_card_frame
                margin = { 8 6 }
                spacing = 3
                hbox = {
                    layoutpolicy_horizontal = expanding
                    spacing = 8
                    country_flag_small = {
                        size = { 42 28 }
                        tooltipwidget = { using = CountryTooltip }
                    }
                    vbox = {
                        layoutpolicy_horizontal = expanding
                        text_single = {
                            layoutpolicy_horizontal = expanding
                            autoresize = yes
                            text = "[Country.GetName]"
                        }
                        text_single = {
                            visible = "[Country.Exists]"
                            layoutpolicy_horizontal = expanding
                            fontsize = 13
                            autoresize = yes
                            text = "[Country.GetGovernment.GetRulerOrRegent.GetName]"
                        }
PACT_STEPS                    }
                    text_single = {
                        visible = "[Not(Country.Exists)]"
                        text = "ga_gathering_annexed"
                        tooltip = "ga_gathering_annexed_tt"
                    }
                    text_single = {
                        visible = "[And(Country.Exists, INDEPENDENT)]"
                        text = "ga_gathering_realm_count"
                        tooltip = "ga_gathering_progress_tt"
                    }
                    text_single = {
                        visible = "[And(Country.Exists, EqualTo_CFixedPoint(STATUS, '(CFixedPoint)2'))]"
                        text = "ga_gathering_vassal"
                        tooltip = "ga_gathering_dependent_tt"
                    }
                    text_single = {
                        visible = "[And(Country.Exists, EqualTo_CFixedPoint(STATUS, '(CFixedPoint)3'))]"
                        text = "ga_gathering_junior"
                        tooltip = "ga_gathering_dependent_tt"
                    }
                    text_single = {
                        visible = "[And(Country.Exists, EqualTo_CFixedPoint(STATUS, '(CFixedPoint)4'))]"
                        text = "ga_gathering_subject"
                        tooltip = "ga_gathering_other_subject_tt"
                    }
                }
                progressbar = {
                    visible = "[And(Country.Exists, INDEPENDENT)]"
                    layoutpolicy_horizontal = expanding
                    size = { -1 8 }
                    min = 0
                    max = TOTAL
                    value = "[FixedPointToFloat(Country.MakeScope.ScriptValue('ga_gathering_realm_locations'))]"
                    progresstexture = "gfx/interface/progressbars/progress_bar_yellow.dds"
                    noprogresstexture = "gfx/interface/icons/unit_view/moral_bar_transparent.dds"
                    tooltip = "ga_gathering_progress_tt"
                }
            }
'''.replace('PACT_STEPS', pact_steps).replace('TAG', tag).replace('INDEPENDENT', independent).replace('STATUS', status).replace('TOTAL', str(len(homeland))))
    panel = '''
situation_panel = {
    blockoverride "situation_subheader_content" {}
    blockoverride "situation_header_left" {
        visible = yes
        text_single = { text = "ga_gathering_header" fontsize = 13 }
    }
    blockoverride "situation_panel_main_content" {
        situation_card_common = {
            blockoverride "common_header_icon" {}
            blockoverride "common_header_text" { text = "ga_gathering_race" }
            blockoverride "common_bottom_content" {
                text_multi = {
                    layoutpolicy_horizontal = expanding
                    max_width = 460
                    autoresize = yes
                    text = "ga_gathering_of_five_desc"
                }
            }
        }
        vbox = {
            layoutpolicy_horizontal = expanding
            spacing = 4
            text_single = { text = "ga_gathering_standings" fontsize = 13 }
            ROWS
        }
        situation_card_expandable = {
            blockoverride "header_text" { text = "ga_gathering_rules" }
            blockoverride "header_icon" { texture = "gfx/interface/icons/disasters/end_requirements_green.dds" }
            blockoverride "header_button_onclick" { onclick = "[SituationView.Vars.Toggle('ga_rules_collapsed')]" }
            blockoverride "bottom_content_onclick" { visible = "[Not(SituationView.Vars.Exists('ga_rules_collapsed'))]" }
            blockoverride "icon_replace_visible_yes" { visible = "[Not(SituationView.Vars.Exists('ga_rules_collapsed'))]" }
            blockoverride "icon_replace_visible_not" { visible = "[SituationView.Vars.Exists('ga_rules_collapsed')]" }
            blockoverride "bottom_content" {
                vbox = {
                    layoutpolicy_horizontal = expanding
                    spacing = 8
                    text_multi = {
                        layoutpolicy_horizontal = expanding
                        max_width = 460
                        autoresize = yes
                        text = "ga_gathering_paths"
                    }
                    TooltipRequirementsList = {
                        textcontext = "[SituationView.GetActiveSituation.GetSituation.GetEndConditions]"
                    }
                }
            }
        }
    }
}
'''.replace('ROWS', ''.join(rows))
    write(out, 'in_game/gui/panels/situation/ga_gathering_of_five.gui', panel)
    for key, value in {
        'ga_gathering_header': 'Six Crowns - One Realm',
        'ga_gathering_race': 'The Race for the Isles',
        'ga_gathering_of_five_desc': 'Six crowns share the Ashborn Isles. Only one can unite them. Bring every homeland location beneath an independent crown, by conquest or by binding other kingdoms to your realm.',
        'ga_gathering_realm_count': "[Country.MakeScope.ScriptValue('ga_gathering_realm_locations')|0] / %s" % len(homeland),
        'ga_gathering_progress_tt': 'Homeland locations within this independent crown\'s realm. Counts direct ownership, vassals, Compact charters and junior union partners, including eligible nested vassals. Alliances, tributaries and foreign conquests do not contribute. Updates from current ownership; occupation alone does not count.',
        'ga_gathering_annexed': 'Annexed',
        'ga_gathering_annexed_tt': 'This founding crown no longer exists. Its former homeland now contributes according to current ownership. A restored kingdom will reappear here automatically.',
        'ga_gathering_standings': 'Founding crowns - Homeland locations in each realm',
        'ga_gathering_vassal': 'Vassal crown',
        'ga_gathering_junior': 'Junior crown',
        'ga_gathering_subject': 'Subject crown',
        'ga_gathering_dependent_tt': 'This crown cannot claim unification while dependent. Its homeland locations contribute to its senior crown only where the vassal or union chain satisfies the unification rules.',
        'ga_gathering_other_subject_tt': 'This crown cannot claim unification while dependent. Tributary ties do not add its homeland to an overlord\'s unification progress.',
        'ga_gathering_rules': 'The Path to One Crown',
        'ga_gathering_paths': '#bold Conquest#! - own the homeland directly.\\n#bold Pacts#! - climb the pact ladder: Bargain, Sworn Pact, then a Compact charter that makes a crown your subject.\\n#bold Submission#! - bring kingdoms into your realm as vassals by war.\\n#bold Union#! - lead junior union partners.\\nAlliances and Sworn Pacts build trust, but only subjects and unions unite the Isles.',
    }.items(): loc(key, value)
    for key, name, tip in sworn_pacts.STEPS:
        loc('ga_pact_step_' + key, 'Our pact: #Y ' + name + '#!')
        loc('ga_pact_step_' + key + '_tt', tip)
