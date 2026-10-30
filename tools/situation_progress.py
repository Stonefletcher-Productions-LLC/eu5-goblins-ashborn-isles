"""Read-only progress and native disabled-target explanations."""
TOOLTIPS = {
    'independent': 'This crown is an independent Ashborn kingdom (not a subject or junior union partner).',
    'peace': 'This crown is at peace.',
    'compact_free': 'This crown has no pending Compact talks. Finish or close the existing invitation; it expires 180 days after it was sent.',
    'harbor_free': 'This crown has no pending Harbor Bargain negotiation. Resolve it first, or wait for its 180-day expiry.',
    'legacy_free': 'This crown has no unresolved offer from the earlier diplomacy system. Close that saved offer first.',
    'quiet': 'This crown has completed its two-year quiet period after a Compact approach or live refusal.',
    'pair_wait': 'These two crowns have completed their five-year wait after the last Compact approach or live refusal.',
    'friendly': 'This crown does not regard the other crown as a rival or enemy.',
    'allied': 'An alliance currently exists with the other crown. Form one through ordinary diplomacy.',
    'bargain': 'This crown has recorded a completed five-year Harbor Bargain with this specific partner. A signed or unfinished bargain is not enough; older, untracked contracts earn no retroactive credit.',
    'alliance_age': 'This crown has recorded three years of alliance with this specific partner. The monthly check must observe the full term; an observed break resets it. This can overlap the five-year bargain.',
    'opinion': 'The prospective subject has at least 100 opinion of the patron.',
    'strength': 'The two crowns have sworn a pact, or the prospective subject has no more than 65% of the patron\'s strength.',
    'bound': 'The two crowns are bound by a Sworn Pact, or have both completed a five-year Harbor Bargain together and kept an alliance for three observed years.',
    'pact_free': 'This crown has no pending Sworn Pact offer. It expires 180 days after it was sent.',
    'pact_opinion': 'This crown has at least 50 opinion of the other crown.',
    'pact_foundation': 'The two crowns are allied, or have completed a five-year Harbor Bargain together.',
    'not_sworn': 'These crowns have not already sworn a pact.',
    'rank': 'The prospective subject has no higher country rank than the patron.',
}


def build(out, homeland, write, loc):
    for key, value in TOOLTIPS.items(): loc('ga_ui_'+key+'_tt', value)
    loc('ga_ui_no_crown', '@trigger_no! No eligible crown. Inspect the listed crowns for unmet requirements. Annexed crowns and your own crown are not listed.')
    loc('ga_ui_homeland_progress', f"Your qualifying realm: [GetPlayer.MakeScope.ScriptValue('ga_ui_homeland_count')|0] / {len(homeland)} homeland locations")
    loc('ga_ui_homeland_rules', 'Unification requires every homeland location, not just the six capitals. Direct ownership, qualifying vassals, Compact charters and junior union partners count. Allies, tributaries, occupation and foreign land do not. A dependent crown cannot claim unification; its count is shown as zero.')
    loc('ga_ui_compact_heading', '#bold The Pact Ladder#! - Bargain, Sworn Pact, Compact')
    loc('ga_ui_compact_route', '#Y 1. Trust#! - ally a crown, or complete a five-year Harbor Bargain with it.\n#Y 2. Swear#! - with 50+ opinion both ways, use Swear a Sworn Pact.\n#Y 3. Bind#! - when the sworn crown holds 100+ opinion of you and no higher rank, use Open Compact Talks. It becomes your subject under a charter and its homeland counts toward unification.\nYour pacts list and each founding crown below show your current step. Inspect a crown in any action to see which checks are still unmet.')
    loc('ga_ui_history_note', 'History updates monthly. Existing saves start alliance observation with this update; only newly tracked bargains earn completion credit. A missing check means the full requirement has not yet been recorded, not that progress is lost. An observed alliance break resets its three-year term.')
    loc('ga_ui_eastern_route', 'Keep the homeland united under the same realm rules. For the Eastern Hunger, secure a genuinely foreign European coastal location through normal play. The Ashborn homeland itself never counts as that foothold.')
    rows = '\n'.join(f'if = {{ limit = {{ location:{x} = {{ exists = owner owner = {{ ga_owner_in_claimant_realm = yes }} }} }} add = 1 }}' for x in homeland)
    write(out, 'in_game/common/script_values/goblins_gathering.txt', '''ga_ui_homeland_count = {
        value = 0
        if = { limit = { ga_independent_goblin = yes }
            save_temporary_scope_as = ga_claimant
            ''' + rows + '''
        }
    }''')
    loc('ga_ui_guide_header', 'How to unite the Isles')
    loc('ga_ui_hunger_guide_header', 'How the Eastern Hunger works')
    for situation in ['ga_gathering_of_five', 'ga_eastern_hunger']:
        def paragraph(key, indent=8, width=400):
            pad = ' '*indent
            return f'''text_multi = {{
{pad}    layoutpolicy_horizontal = expanding
{pad}    max_width = {width}
{pad}    autoresize = yes
{pad}    text = "{key}"
{pad}}}
{pad}'''
        content = '''text_single = {
            layoutpolicy_horizontal = expanding
            text = "ac_favor_current"
            tooltip = "ac_favor_explanation"
        }
        ''' + paragraph('ga_ui_homeland_progress')
        # Long rules text lives in the dropdown that 1.4 puts at the top of every
        # situation (vanilla fills it with outcomes; ours have none), collapsed by default.
        if situation == 'ga_gathering_of_five':
            header, var = 'ga_ui_guide_header', 'ga_guide_open'
            guide = ['ga_ui_homeland_rules', 'ga_ui_compact_heading', 'ga_ui_compact_route', 'ga_ui_history_note']
        else:
            header, var = 'ga_ui_hunger_guide_header', 'ga_hunger_guide_open'
            guide = ['ga_eastern_hunger_desc', 'ga_ui_eastern_route', 'ga_ui_homeland_rules']
        top = f'''blockoverride "situation_panel_main_content_top" {{
        situation_card_expandable = {{
            blockoverride "card_expandable_size" {{ minimumsize = {{ 500 -1 }} }}
            blockoverride "header_text" {{ text = "{header}" }}
            blockoverride "header_icon" {{ texture = "gfx/interface/icons/disasters/end_requirements_green.dds" }}
            blockoverride "header_button_onclick" {{ onclick = "[SituationView.Vars.Toggle('{var}')]" }}
            blockoverride "bottom_content_onclick" {{ visible = "[SituationView.Vars.Exists('{var}')]" }}
            blockoverride "icon_replace_visible_yes" {{ visible = "[SituationView.Vars.Exists('{var}')]" }}
            blockoverride "icon_replace_visible_not" {{ visible = "[Not(SituationView.Vars.Exists('{var}'))]" }}
            blockoverride "bottom_content" {{
                vbox = {{
                    layoutpolicy_horizontal = expanding
                    spacing = 8
                    ''' + ''.join(paragraph(k, 20, 460) for k in guide).rstrip() + '''
                }
            }
        }
    }
    '''
        path = 'in_game/gui/panels/situation/'+situation+'.gui'
        text = (out/path).read_text(encoding='utf-8-sig')
        if situation == 'ga_eastern_hunger':
            # The description paragraph moves into the dropdown.
            moved = '\n        ' + paragraph('ga_eastern_hunger_desc').rstrip()
            assert text.count(moved) == 1
            text = text.replace(moved, '', 1)
        anchor = 'blockoverride "situation_panel_main_content" {'
        assert text.count(anchor) == 1 and 'situation_panel_main_content_top' not in text
        text = text.replace(anchor, top+anchor+'\n        '+content.rstrip(), 1)
        write(out, path, '\n'.join(line.rstrip() for line in text.splitlines())+'\n')
