"""Story-specific, bounded Covenant decisions; no additional event dispatch."""
import food_storage
# label, gold cost, Favor change, temporary modifiers
CHOICES = {
 1: [('Secure the fissure and hear the witnesses.',5,0,{'clergy_estate_target_satisfaction':.05}),
     ('Let the miners work; accept the Oathkeepers\' anger.',0,-3,{'global_production_efficiency':.05})],
 2: [('Pay for the repairs from the crown\'s treasury.',5,2,{'global_food_capacity_modifier':.10}),
     ('Enforce the wealthy house\'s repair oath.',0,0,{'global_food_capacity_modifier':.10,'nobles_estate_target_satisfaction':-.05})],
 3: [('Give the stranger a lamp and a stone.',5,0,{'tolerance_heathen':.5}),
     ('Reserve the observance for our own faithful.',0,3,{'tolerance_heathen':-.5})],
 4: [('Recognize the dependent branch and witness its names.',5,0,{'diplomatic_reputation':.5,'nobles_estate_target_satisfaction':-.025}),
     ('Leave authority with the senior households.',0,0,{'nobles_estate_target_satisfaction':.05,'clergy_estate_target_satisfaction':-.025})],
 5: [('Repair the pilgrimage path.',5,0,{'naval_morale_recovery':.05}),
     ('Let crews prove themselves on the dangerous climb.',0,0,{'naval_morale_modifier':.05,'global_sailors_modifier':-.05})],
 6: [('Buy timber elsewhere and protect the seed grove.',5,2,{'navy_maintenance_efficiency':.05}),
     ('Permit cutting in the sacred grove.',0,-3,{'global_production_efficiency':.05})],
 7: [('Compensate the missing sailors\' households.',5,0,{'global_sailors_modifier':.05}),
     ('Make the captain\'s patrons provide for the crews.',0,0,{'naval_morale_recovery':.05,'nobles_estate_target_satisfaction':-.05})],
 8: [('Sponsor a public feast under the Oathkeepers.',5,0,{'clergy_estate_target_satisfaction':.05}),
     ('Let each shrine settle the dispute in its own way.',0,0,{'stability_cost_efficiency':.05,'diplomatic_reputation':-.25})],
 9: [('Fund the captives\' memorial over the chiefs\' objections.',5,0,{'clergy_estate_target_satisfaction':.05,'nobles_estate_target_satisfaction':-.025}),
     ('Uphold the owners\' authority over the observance.',0,-3,{'nobles_estate_target_satisfaction':.05})],
 10:[('Send gifts and learn the foreign observances.',5,0,{'tolerance_heathen':.5}),
     ('Support the island shrines and turn the envoys away.',0,0,{'clergy_estate_target_satisfaction':.05,'diplomatic_reputation':-.25})],
 11:[('Provision the hungry households from the treasury.',5,0,{'global_monthly_food_modifier':.05}),
     ('Require contributions and put them into shared stores.',0,-3,{'global_food_capacity_modifier':.10})],
 12:[('Pay the smith and honor the offering.',5,5,{}),
     ('Send the blade to the muster despite the oath.',0,-3,{'land_morale_modifier':.03})],
 13:[('Break the false weight beneath the First Weight.',5,2,{'diplomatic_reputation':.5}),
     ('Fine the house quietly and keep its trade.',0,-3,{'global_production_efficiency':.05})],
}
# What the modifier tooltip says about each consequence; the numbers come from the game.
FLAVOR = {
 (1,0):'Ember-speakers keep watch over the reopened fissure, and the Oathkeepers remember who listened to them.',
 (1,1):'Miners follow the warm draft deeper every season. The Oathkeepers say the mountain is keeping count.',
 (2,0):'The crown paid to raise the tidal gates, and the Reed-witnesses cut a new notch for its honesty.',
 (2,1):'The wealthy house rebuilt the gates under protest. Its heirs have not forgotten who made them.',
 (3,0):'A stranger\'s name stone stands among our dead, and its lamp is never allowed to go out.',
 (3,1):'The Lantern Steps are lit for our own. Strangers are buried at the tideline.',
 (4,0):'The unmarked cord now carries knots of its own, and a branch that kept silent has a voice.',
 (4,1):'The senior households keep the cords and their memory, as they always have.',
 (5,0):'New steps climb to the Storm Teeth, and old captains make the pilgrimage again.',
 (5,1):'Only the bold climb the Storm Teeth now. Those who come back carry themselves like it.',
 (6,0):'Bought timber fills the yards while the seed grove at Emberroot Hollow grows untouched.',
 (6,1):'Stumps stand inside Emberroot Hollow. The forges burn hot, and the Root-wardens no longer speak to the cutters.',
 (7,0):'The crown feeds the households of the lost, and their sons sign onto the next voyage.',
 (7,1):'The captain\'s patrons now feed the families of his missing crew, and they watch him closely.',
 (8,0):'The Oathkeepers fed the town in the crown\'s name, and the preacher\'s crowd went home full.',
 (8,1):'Each shrine answered the preacher in its own way. Some answered louder than others.',
 (9,0):'A memorial for the captive dead stands beside the household hearth. Some chiefs will not look at it.',
 (9,1):'The owners keep their hearths for their own dead, and the captives mourn where no one sees.',
 (10,0):'Our crews leave small gifts at foreign shrines and come home with new prayers.',
 (10,1):'The island shrines receive the gifts that might have crossed the sea.',
 (11,0):'Crown stores fed the households that had nothing to bring to the feast.',
 (11,1):'Every household now gives to the common stores, whether it can spare the share or not.',
 (12,1):'The offered blade hangs at a captain\'s side. The smith who made it has stopped speaking to him.',
 (13,0):'A shaved weight lies broken beneath the First Weight. Foreign captains trust Chainhaven\'s scales a little more.',
 (13,1):'The house paid its fine in silence and its counting rooms never closed. The Oathkeepers have not forgiven the crown.',
}
# The neutral third choice, in the voice of each story.
DEFER = {
 1:'Seal the cavity until the mountain speaks again.',
 2:'Let the flood marks wait another season.',
 3:'Leave the stranger to the keepers\' own judgment.',
 4:'Leave the cord unknotted for now.',
 5:'Let the path wait for drier weather.',
 6:'Post wardens at the grove and decide after the rains.',
 7:'Hold the captain\'s account for another year.',
 8:'Let the preacher shout himself hoarse.',
 9:'Tell the speaker the crown will think on it.',
 10:'Let the crews tell their stories. Decide later.',
 11:'Promise to look into the stores after the harvest.',
 12:'Hang the blade in the hall until tempers cool.',
 13:'Seal the scales and hear the case next season.',
}
LABELS = {
 'clergy_estate_target_satisfaction':('Oathkeeper estate target satisfaction',100),
 'nobles_estate_target_satisfaction':('noble estate target satisfaction',100),
 'global_production_efficiency':('production efficiency',100),
 'global_food_capacity_modifier':('province food storage limit',100),
 'tolerance_heathen':('tolerance of heathens',1), 'diplomatic_reputation':('diplomatic reputation',1),
 'naval_morale_recovery':('naval morale recovery',100), 'naval_morale_modifier':('naval morale',100),
 'global_sailors_modifier':('monthly sailor gain',100), 'navy_maintenance_efficiency':('navy maintenance efficiency',100),
 'stability_cost_efficiency':('stability cost efficiency',100), 'global_monthly_food_modifier':('monthly food',100),
 'land_morale_modifier':('army morale',100),
}


def ident(number,index): return f'ac_story_{number}_{index}'
def modifier_ids(): return [ident(n,i) for n,rows in CHOICES.items() for i,row in enumerate(rows) if row[3]]
def cleanup(): return ' '.join('remove_country_modifier = '+key for key in modifier_ids())
def terms(row):
    _,cost,favor,mods=row
    parts=[f'Pay {cost} gold.' if cost else 'No gold cost.']
    if favor: parts.append(f'{favor:+g} Covenant Favor immediately.')
    for key,value in mods.items():
        name,scale=LABELS[key];unit='%' if scale==100 else ''
        parts.append(f'{value*scale:+g}{unit} {name} for three years.')
    parts.append('Replaces any earlier Covenant story consequences. No prestige reward.')
    if 'global_food_capacity_modifier' in mods:
        parts.append('\\n\\n' + food_storage.REFERENCE)
    return ' '.join(parts)


def modifiers(loc):
    result=[]
    for n,rows in CHOICES.items():
        for i,row in enumerate(rows):
            if not row[3]: continue
            key=ident(n,i)
            loc('STATIC_MODIFIER_NAME_'+key,row[0].rstrip('.'))
            loc('STATIC_MODIFIER_DESC_'+key,FLAVOR[n,i])
            result.append(key+' = { '+' '.join(f'{k} = {v:g}' for k,v in row[3].items())+' }')
    return '\n'.join(result)


SESSION='has_variable = ac_story_open exists = scope:ac_story_token var:ac_story_serial = scope:ac_story_token'
def event(row,loc):
    num,title,desc,eligibility,art,*_=row
    prefix=f'ashen_covenant.{num}'
    loc(prefix+'.title',title)
    loc(prefix+'.desc',desc)
    loc('ac_story_available_tt','This is the current Covenant story, its circumstances still apply, and the required gold or Favor is available.')
    options=[]
    for i,data in enumerate(CHOICES[num]):
        label,cost,favor,mods=data;suffix='ab'[i]
        loc(prefix+'.'+suffix,label);tip=loc(prefix+'.'+suffix+'_terms',terms(data))
        gate=f'{SESSION} religion = religion:cm_hunger_below {eligibility}'
        if cost: gate+=f' gold >= {cost} OR = {{ is_ai = no gold >= {cost+20} }}'
        if favor<0: gate+=f' religious_influence >= {-favor}'
        effects=cleanup()+' remove_variable = ac_story_open'
        if cost: effects+=f' add_gold = {-cost}'
        if favor: effects+=f' add_religious_influence = {favor}'
        if mods: effects+=f' add_country_modifier = {{ modifier = {ident(num,i)} years = 3 mode = replace }}'
        options.append(f'''option = {{ name = {prefix}.{suffix}
            trigger = {{ custom_tooltip = {{ text = ac_story_available_tt {gate} }} }}
            ai_chance = {{ factor = 2 }} custom_tooltip = {tip}
            hidden_effect = {{ if = {{ limit = {{ {gate} }} {effects} }} }}
        }}''')
    loc(prefix+'.c',DEFER[num])
    loc(prefix+'.c_terms','Make no commitment. No gold, Favor, prestige or modifier change. This closes the story; it does not schedule a follow-up. The normal three-year story cooldown remains.')
    options.append(f'''option = {{ name = {prefix}.c trigger = {{ }} ai_chance = {{ factor = 1 }}
        custom_tooltip = {prefix}.c_terms
        hidden_effect = {{ if = {{ limit = {{ {SESSION} }} remove_variable = ac_story_open }} }}
    }}''')
    return f'''{prefix} = {{
        type = country_event category = situation_event outcome = neutral
        title = {prefix}.title desc = {prefix}.desc
        image = "gfx/interface/illustrations/event/ashborn/{art}.dds"
        trigger = {{ religion = religion:cm_hunger_below NOT = {{ has_variable = ac_story_cooldown }} {eligibility} }}
        immediate = {{
            set_variable = {{ name = ac_story_cooldown value = yes years = 3 }}
            if = {{ limit = {{ NOT = {{ has_variable = ac_story_serial }} }} set_variable = {{ name = ac_story_serial value = 0 }} }}
            change_variable = {{ name = ac_story_serial add = 1 }}
            save_scope_value_as = {{ name = ac_story_token value = var:ac_story_serial }}
            set_variable = {{ name = ac_story_open value = yes }}
        }}
        {chr(10).join(options)}
    }}'''
