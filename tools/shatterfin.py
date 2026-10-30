"""Shatterfin's maternal dynasty and seniority succession setup."""
from pathlib import Path

DYNASTY='cm_shatterfin_dynasty'
FAMILY=[
    ('cm_sfk_savra','cm_name_savra','1278.2.9',True,None,'1329.6.3',65,60,45),
    ('cm_sfk_maarka','cm_name_maarka','1298.3.12',True,'cm_sfk_savra',None,66,58,52),
    ('cm_sfk_ishra','cm_name_ishra','1301.8.4',True,'cm_sfk_savra',None,59,71,35),
    ('cm_sfk_korr','cm_name_korr','1316.1.6',False,'cm_sfk_maarka',None,70,55,98),
    ('cm_sfk_veshka','cm_name_veshka','1317.5.19',True,'cm_sfk_maarka',None,74,62,86),
    ('cm_sfk_neshri','cm_name_neshri','1318.9.2',True,'cm_sfk_maarka',None,61,76,44),
    ('cm_sfk_rikka','cm_name_rikka','1319.4.23',True,'cm_sfk_ishra',None,57,65,63),
    ('cm_sfk_sella','cm_name_sella','1335.7.11',True,'cm_sfk_veshka',None,48,54,39),
    # 0.6.6: a wider maternal house, so seniority always has adult women to call on.
    ('cm_sfk_zhrikka','cm_ash_name_zhrikka','1304.12.1',True,'cm_sfk_savra',None,63,67,48),
    ('cm_sfk_krashra','cm_ash_name_krashra','1321.6.28',True,'cm_sfk_ishra',None,60,69,52),
    ('cm_sfk_shrazha','cm_ash_name_shrazha','1322.2.17',True,'cm_sfk_maarka',None,68,61,57),
    ('cm_sfk_vresh','cm_ash_name_vresh','1323.7.7',False,'cm_sfk_maarka',None,58,56,80),
    ('cm_sfk_krazha','cm_ash_name_krazha','1324.3.30',True,'cm_sfk_zhrikka',None,57,64,55),
    ('cm_sfk_vrishka','cm_ash_name_vrishka','1325.10.3',True,'cm_sfk_maarka',None,62,73,41),
    ('cm_sfk_zharr','cm_ash_name_zharr','1334.2.12',False,'cm_sfk_veshka',None,52,50,66),
    ('cm_sfk_vroshka','cm_ash_name_vroshka','1335.11.20',True,'cm_sfk_rikka',None,55,58,47),
    ('cm_sfk_rizhka','cm_ash_name_rizhka','1336.3.9',True,'cm_sfk_veshka',None,51,60,44),
    ('cm_sfk_shrikka','cm_ash_name_shrikka','1337.1.5',True,'cm_sfk_neshri',None,49,57,46),
]
LOCALIZATION={
    'cm_tidemother_monarchy':'Tidemother Monarchy',
    'cm_tidemother_monarchy_desc':'Shatterfin is ruled by a maternal clan house. The Tidemother reigns for life; the eldest eligible adult woman of her dynasty succeeds, provided her mother belonged to that house. The crown retains normal monarchy institutions. Its succession law may be changed.',
    'cm_tidemother_seniority':'Seniority of the Tidemothers',
    'cm_tidemother_seniority_desc':'The eldest eligible adult Stormfang woman of the ruling dynasty inherits, with age measured to the day. Her mother must also belong to that dynasty. Sisters and maternal cousins may precede daughters. Men, children, foreign rulers and those barred from rule are excluded. Births into the maternal ruling house in Shatterfin retain their mother\'s dynasty while this law is active. No eligible adult woman means no eligible heir; the law does not admit men as a fallback.',
    'cm_tidemother_age_score':'Seniority within the maternal ruling house',
    'cm_shatterfin_dynasty':'Shatterfin',
    'cm_name_savra':'Zhavra','cm_name_maarka':'Jaimzha','cm_name_ishra':'Skritcha',
    'cm_name_korr':'Vrosh','cm_name_veshka':'Morzha','cm_name_neshri':'Rikkra',
    'cm_name_rikka':'Krishka','cm_name_sella':'Zrikka',
}

def dynasty_row():return f'{DYNASTY} = {{ name = {{ name = {DYNASTY} }} home = cm_shatterfin }}'

def family_rows():
    rows=[]
    for ident,name,born,female,mother,died,adm,dip,mil in FAMILY:
        row=f'{ident} = {{ first_name = {{ name = {name} }} culture = cm_shatterkin religion = cm_hunger_below dynasty = {DYNASTY} tag = SFK birth = cm_shatterfin birth_date = {born} adm = {adm} dip = {dip} mil = {mil}'
        if ident=='cm_sfk_maarka':row+=' nickname = { name = cm_mare_mother }'
        if female:row+=' female = yes'
        if mother:row+=' mother = '+mother
        if died:row+=' death_date = '+died
        rows.append(row+' }')
    return rows

def build(b,game,out):
    rel='main_menu/setup/1337/04_dynasties.txt'
    b.write(out,rel,b.inject(b.read(game,rel),'dynasty_manager',dynasty_row()))
    rel='main_menu/setup/1337/05_characters.txt'
    b.write(out,rel,b.inject(b.read(game,rel),'character_db','\n'.join(family_rows())))

def verify(b,out):
    names=(out/'main_menu/localization/english/goblins_ashborn_isles_l_english.yml').read_text(encoding='utf-8-sig')
    assert 'cm_name_maarka: "Jaimzha"' in names
    assert 'cm_ash_name_jaima: "Jaimzha"' in names
    law=(out/'in_game/common/heir_selections/shatterfin.txt').read_text(encoding='utf-8-sig')
    assert 'allow_male = no' in law and 'allow_children = no' in law
    assert 'value = root.character_age' in law and 'root.mil' not in law
    assert 'dynasty = scope:target.last_valid_ruler.dynasty' in law
    setup=(out/'main_menu/setup/1337/10_countries.txt').read_text(encoding='utf-8-sig')
    for tag in ['CDM','QBR','RHK','SFK','SWK']:
        a,z=b.block_span(setup,tag);country=setup[a:z]
        assert ('heir_selection = cm_tidemother_seniority' if tag=='SFK' else 'heir_selection = cm_rule_of_the_strongest') in country
        if tag=='SFK':assert 'ruler = cm_sfk_maarka' in country and 'include = "cm_tidemothers"' in country
    seen=set()
    for ident,_,born,female,mother,died,*_ in FAMILY:
        if mother:assert mother in seen,'Parents must precede children'
        seen.add(ident)
    from datetime import date
    def birthday(row):return date(*map(int,row[2].split('.')))
    now=date(1337,11,11)
    eligible=sorted((r for r in FAMILY if r[0]!='cm_sfk_maarka' and r[3] and r[4] and r[5] is None and (now-birthday(r)).days>=18*365.25),key=birthday)
    assert [r[0] for r in eligible]==['cm_sfk_ishra','cm_sfk_zhrikka','cm_sfk_veshka','cm_sfk_neshri','cm_sfk_rikka']
    return {'starting_ruler':'Jaimzha Shatterfin','starting_heir':'Skritcha Shatterfin','eligible_starting_women':5,'male_and_minor_exclusion':True,'parents_before_children':True,'engine_succession_tested':False}
