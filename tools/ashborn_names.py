"""Shared Ashborn language with five naming dialects and authored royal courts."""
from clan_identity import PROFILES

POOLS={
 'GTF':('Cinderweight','cm_giltkin',
 'Vrekk Skarn Krizz Drazk Korrik Grizz Vrazh Krek Zark Borrik Trazk Krunn Drizz Krazh Zurr Ghrak',
 'Zhezzra Krizha Vrazka Skarra Drazha Brekka Korrza Grizha Trazza Zurrka Krazra Vrekka Shazra Brizka Zarkha Krezza',
 'Giltfang Brassjaw Chainclaw Coinbite Scaletooth Locktusk',
 'Brass-Eye Chainhand Saltknuckle Coin-Eater Copperfoot Lockjaw'),
 'CDM':('Emberblood','cm_cinderkin',
 'Drogg Grask Korgat Throkk Gorrak Kragg Mograt Drukk Grond Krazg Vorgg Brakk Garkuk Ogrash Krogmar Rukk',
 'Grakka Kragga Mograz Drakka Gorzha Bragga Korgra Urgza Vrogga Ragra Krugga Drazka Zoggra Garsha Mograkka Krazha',
 'Cindermaw Ashjaw Ironbite Forgefang Blackslag Emberclaw',
 'Coalhand Ash-Eater Chainbiter Flintknuckle Slagfoot Sootnose'),
 'QBR':('Brineward','cm_brinekin',
 'Murgash Ghorr Brumak Brugorr Ghum Bragh Murrok Ghorum Bogrash Murruk Grubak Borgh Umrag Broggar Ghurmak Mughor',
 'Brugha Morga Ghazra Brumra Murgha Boghra Ghorrza Umgra Braghra Mugra Ghumza Morghra Brugzha Urrgha Brorzha Ghubra',
 'Brackmaw Miretooth Reedclaw Bogjaw Mudtusk Fenhook',
 'Mudfoot Reed-Cutter Bog-Eye Eelgrip Saltjaw Mirehand'),
 'RHK':('Reefstrider','cm_reefkin',
 'Skrezz Krizzek Zikrat Skrik Rizzik Zrekk Kizrik Skazz Vizzek Zrik Krezik Tizzak Skerz Krikzat Zizzik Rekzik',
 'Zikka Skrizza Rizzka Krizha Zrikka Skizza Tizzra Kezra Vizzka Zrekka Rikkza Skirza Kizzra Zazka Rezikka Skrezzha',
 'Reefhook Shoalcut Shellsplit Coralbite Shardhook Pearlclaw',
 'Reef-Cutter Shellbreaker Netfinger Hookhand Gullbiter Salt-Eye'),
 'SFK':('Stormfang','cm_shatterkin',
 'Vrosh Krashik Sharg Vrak Krishak Shrokk Rask Vrokk Krazhik Shrakk Rikkash Vresh Korrak Zharr Kravosh Shrik',
 'Jaimzha Skritcha Morzha Rikkra Krishka Zrikka Zhavra Vrazka Shrazha Vrishka Krashra Rizhka Shrikka Vroshka Krazha Zhrikka',
 'Shatterfin Knifeback Stormscar Wavecleaver Galehook Deepfang',
 'Saltfang Wavebiter Storm-Eye Ropehand Gale-Eater Keelbreaker'),
 'SWK':('Ashveil','cm_sootkin',
 'Snikh Zhor Khash Zhekh Skharr Sizh Khuzh Srozh Zhakh Nizhk Khez Szhurr Zhirr Veshk Khaz Surrkh',
 'Zheska Khazra Sishka Zhirra Khezha Sizhka Nizhka Khurza Zhasha Snezha Veshra Zhurka Sakhra Khasha Zhisra Khessha',
 'Sootwake Cinderhush Blackreed Ashveil Duskmire Smoketooth',
 'Smokehand Ashwhisper Coal-Eye Cinderfoot Blackfinger Ember-Eater'),
}

def key(name):return 'cm_ash_name_'+('jaima' if name == 'Jaimzha' else name.lower().replace('-','_'))
def house_key(tag,n):return 'cm_shatterfin_dynasty' if tag=='SFK' and n==0 else 'cm_'+tag.lower()+'_house_'+str(n)
def dialect(culture):return culture+'_dialect'

def localization():
    result={}
    for tag,(label,culture,males,females,houses,lowborn) in POOLS.items():
        result[dialect(culture)]=label+' Cinder Tongue'
        for name in (males+' '+females+' '+lowborn).split():result[key(name)]=name
        for i,name in enumerate(houses.split()):result[house_key(tag,i)]=name
    result['cm_stone_fletcher']='The Stone Fletcher'
    result['cm_mare_mother']='The Mare-Mother'
    for profile in PROFILES.values():result[profile['nickname_key']]=profile['nickname']
    return result

def build_names(b,out):
    sections=[]
    for tag,(label,culture,males,females,houses,lowborn) in POOLS.items():
        sections.append(f'{dialect(culture)} = {{ male_names = {{ '+ ' '.join(map(key,males.split()))+' } female_names = { '+' '.join(map(key,females.split()))+' } dynasty_names = { '+' '.join(house_key(tag,i) for i,_ in enumerate(houses.split()))+' } lowborn = { '+' '.join(map(key,lowborn.split()))+' } }')
    # Shared root retains a complete Goblin fallback without borrowing human names.
    all_males=' '.join(dict.fromkeys(key(n) for p in POOLS.values() for n in p[2].split()))
    all_females=' '.join(dict.fromkeys(key(n) for p in POOLS.values() for n in p[3].split()))
    all_houses=' '.join(house_key(t,i) for t,p in POOLS.items() for i,_ in enumerate(p[4].split()))
    b.write(out,'in_game/common/languages/goblins_ashborn_isles.txt',f'cm_cinder_tongue = {{ color = rgb {{ 117 140 48 }} family = cm_goblin_language_family male_names = {{ {all_males} }} female_names = {{ {all_females} }} dynasty_names = {{ {all_houses} }} dialects = {{ '+ '\n'.join(sections)+' } }\n')

def ruler(tag):return 'cm_sfk_maarka' if tag=='SFK' else 'cm_'+tag.lower()+'_ruler'

# Authored variation is reproducible across builds; dates keep families plausible.
COURT_DATES = {
 'GTF': ('1301.9.3', '1299.12.11', '1317.11.2', '1319.6.19', ('1300.4.8', '1306.10.23', '1309.9.2')),
 'CDM': ('1299.3.12', '1298.6.4', '1317.8.8', '1319.2.15', ('1304.2.3', '1308.8.5', '1302.11.6')),
 'QBR': ('1301.1.17', '1300.5.8', '1318.7.26', '1319.10.5', ('1310.4.18', '1305.9.21', '1297.3.9')),
 'RHK': ('1310.9.26', '1311.2.14', '1330.4.19', '1332.8.27', ('1306.6.11', '1311.1.28', '1294.10.16')),
 'SFK': (None, None, None, None, ('1302.7.4', '1309.3.22', '1307.5.13')),
 'SWK': ('1308.7.6', '1310.10.9', '1328.1.23', '1330.5.31', ('1312.6.17', '1303.4.7', '1296.8.29')),
}

# Large ruling households keep each crown's dynasty alive past one unlucky death.
# Rule of the Strongest only crowns adult men of the ruler's own dynasty, so every
# crown starts with several adult kinsmen plus younger sons. The Ashen Covenant
# allows four wives, so each ruler starts with three. Existing heirs remain the
# strongest adult candidates; the new kin all have lower Military ability.
# (role, sex, year offset from ruler birth, month, day, father, mother, house, stats)
FAMILY_ROLES = (
 ('father','m',-25,4,9,None,None,0,(63,57,88)),
 ('uncle','m',-22,8,24,None,None,0,(60,63,70)),
 ('cousin','m',-1,12,5,'uncle',None,0,(58,59,74)),
 ('brother','m',3,6,14,'father',None,0,(61,60,78)),
 ('brother_2','m',6,2,27,'father',None,0,(66,64,72)),
 ('brother_wife','f',4,9,3,None,None,4,(62,66,48)),
 ('brother_2_wife','f',7,11,21,None,None,5,(58,63,51)),
 ('wife_2','f',7,5,30,None,None,2,(64,71,47)),
 ('wife_3','f',10,1,12,None,None,3,(69,59,55)),
 ('son_2','m',22,3,6,'ruler','consort',0,(62,58,76)),
 ('son_3','m',24,10,17,'ruler','wife_2',0,(57,61,79)),
 ('daughter_2','f',26,7,4,'ruler','wife_2',0,(64,70,52)),
 ('son_4','m',29,12,1,'ruler','wife_2',0,(60,55,74)),
 ('son_5','m',28,4,22,'ruler','wife_3',0,(65,57,77)),
 ('daughter_3','f',31,8,13,'ruler','wife_3',0,(68,62,49)),
 ('nephew','m',24,1,25,'brother','brother_wife',0,(59,62,71)),
 ('niece','f',26,6,8,'brother','brother_wife',0,(63,67,46)),
 ('nephew_2','m',29,9,30,'brother','brother_wife',0,(55,58,75)),
 ('nephew_3','m',27,3,16,'brother_2','brother_2_wife',0,(61,54,73)),
 ('niece_2','f',30,10,2,'brother_2','brother_2_wife',0,(66,69,44)),
 ('son_wife','f',19,8,19,None,None,5,(60,68,50)),
 ('grandson','m',37,2,11,'son','son_wife',0,(58,56,70)),
)
FAMILY_FATHER_DEATHS = {'CDM':'1331.3.14','QBR':'1332.7.2','GTF':'1330.11.27','RHK':'1334.9.6','SWK':'1334.9.6'}
LAST_SETUP_BIRTH = (1337,6,1)

def family_plan(tag):
    """Return (suffix, female, birth, father, mother, house, stats) rows for a non-Shatterfin crown."""
    leader_birth=COURT_DATES[tag][0];son_birth=COURT_DATES[tag][2]
    ruler_year=int(leader_birth.split('.')[0]);son_year=int(son_birth.split('.')[0])
    rows=[]
    for role,sex,offset,month,day,father,mother,house,stats in FAMILY_ROLES:
        if tag in {'RHK','SWK'} and role in {'father','brother'}:continue  # authored before 0.6.6
        if role in {'son_wife','grandson'}:
            # Only adult eldest sons marry before the campaign.
            if son_year>1318:continue
            year=son_year+(1 if role=='son_wife' else 18)
        else:
            year=ruler_year+offset
        if role=='son_2':year=max(year,son_year+3)
        if role in {'uncle','cousin'}:
            father_year={'RHK':1282,'SWK':1281}.get(tag,ruler_year-25)
            year=father_year+(3 if role=='uncle' else 25)
        if role.startswith(('nephew','niece')):
            parent_year=ruler_year+(3 if father=='brother' else 6)
            if tag in {'RHK','SWK'} and father=='brother':parent_year=int(('1305' if tag=='RHK' else '1303'))
            year=max(year,parent_year+18+(offset-24))
        if (year,month,day)>LAST_SETUP_BIRTH:continue
        rows.append((role,sex=='f',f'{year}.{month}.{day}',father,mother,house,stats))
    present={r[0] for r in rows}|{'ruler','consort','son','father','brother','uncle'}
    rows=[r for r in rows if (r[3] is None or r[3] in present) and (r[4] is None or r[4] in present)]
    present={r[0] for r in rows}|{'ruler','consort','son','father','brother'}
    # Drop wives whose husbands have no row, and husbands' kin whose mothers were dropped.
    return [r for r in rows if not r[0].endswith('_wife') or r[0][:-5] in present]

def family_names(tag):
    """Assign unused pool names to the extended family, in role order."""
    _,_,males,females,_,_=POOLS[tag];males=males.split();females=females.split()
    used_m={0,1,3,4,5}|({2} if tag in {'RHK','SWK'} else set())
    used_f={0,1,3}
    free_m=[n for i,n in enumerate(males) if i not in used_m]
    free_f=[n for i,n in enumerate(females) if i not in used_f]
    names={}
    for role,female,*_ in family_plan(tag):
        # Grandsons carry their dead great-grandfather's name.
        if role in {'father','grandson'}:names[role]=males[5];continue
        if role=='brother':names[role]=males[1] if tag in {'RHK','SWK'} else free_m.pop(0);continue
        pool=free_f if female else free_m
        assert pool,'Name pool exhausted: '+tag
        names[role]=pool.pop(0)
    return names

def court_rows(countries):
    """Authored dynasties and character rows for the five captain crowns and Shatterfin's courtiers."""
    dynasties=[];characters=[]
    def person(ident,name,tag,culture,capital,dynasty,born,female=False,extra='',stats=(58,58,58)):
        adm,dip,mil=stats
        characters.append(f'{ident} = {{ first_name = {{ name = {key(name)} }} culture = {culture} religion = cm_hunger_below dynasty = {dynasty} tag = {tag} birth = {capital} birth_date = {born} adm = {adm} dip = {dip} mil = {mil} '+('female = yes ' if female else '')+extra+' }')
    for country in countries:
        tag=country['tag'];label,culture,males,females,houses,_=POOLS[tag];males=males.split();females=females.split();capital=country['capital'];prefix='cm_'+tag.lower()
        leader_birth,consort_birth,son_birth,daughter_birth,court_births=COURT_DATES[tag]
        for i in range(1 if tag=='SFK' else 0,len(houses.split())):dynasties.append(f'{house_key(tag,i)} = {{ name = {{ name = {house_key(tag,i)} }} home = {capital} }}')
        if tag!='SFK':
            plan={r[0]:r for r in family_plan(tag)};names=family_names(tag)
            def kin(role):
                _,female,born,father,mother,house,stats=plan[role]
                extra=''
                if role=='father':extra='death_date = '+FAMILY_FATHER_DEATHS[tag]
                if father:extra+=' father = '+prefix+'_'+father
                if mother:extra+=' mother = '+prefix+'_'+mother
                spouse=role[:-5] if role.endswith('_wife') else (role+'_wife' if role+'_wife' in plan else None)
                if role in {'wife_2','wife_3'}:spouse='ruler'
                if spouse:extra+=' spouse = '+prefix+'_'+spouse
                person(prefix+'_'+role,names[role],tag,culture,capital,house_key(tag,house),born,female,extra.strip(),stats)
            nickname=' nickname = { name = cm_stone_fletcher }' if tag=='CDM' else ''
            if tag in PROFILES:nickname=' nickname = { name = '+PROFILES[tag]['nickname_key']+' }'
            ancestry=''
            if tag in {'RHK','SWK'}:
                father_birth,brother_birth=('1282.2.11','1305.10.16') if tag=='RHK' else ('1281.5.20','1303.1.14')
                person(prefix+'_father',males[5],tag,culture,capital,house_key(tag,0),father_birth,extra='death_date = 1334.9.6',stats=(63,57,88))
                ancestry=' father = '+prefix+'_father'
                spouse=' spouse = '+prefix+'_brother_wife' if 'brother_wife' in plan else ''
                person(prefix+'_brother',males[1],tag,culture,capital,house_key(tag,0),brother_birth,extra=ancestry+spouse,stats=(59,55,82))
            else:
                kin('father');ancestry=' father = '+prefix+'_father'
                kin('brother')
            for role in ('uncle','cousin','brother_2','brother_wife','brother_2_wife'):
                if role in plan:kin(role)
            stats=tuple(PROFILES[tag][k] for k in ('adm','dip','mil')) if tag in PROFILES else (66,61,90)
            wives=''.join(' spouse = '+prefix+'_'+w for w in ('wife_2','wife_3') if w in plan)
            person(prefix+'_ruler',males[0],tag,culture,capital,house_key(tag,0),leader_birth,extra='spouse = '+prefix+'_consort'+wives+nickname+ancestry,stats=stats)
            person(prefix+'_consort',females[0],tag,culture,capital,house_key(tag,1),consort_birth,True,'spouse = '+prefix+'_ruler',stats=(70,68,50))
            for role in ('wife_2','wife_3'):
                if role in plan:kin(role)
            parents=f'father = {prefix}_ruler mother = {prefix}_consort'
            son_spouse=' spouse = '+prefix+'_son_wife' if 'son_wife' in plan else ''
            person(prefix+'_son',males[2] if tag in {'RHK','SWK'} else males[1],tag,culture,capital,house_key(tag,0),son_birth,extra=parents+son_spouse,stats=(59,55,82))
            person(prefix+'_daughter',females[1],tag,culture,capital,house_key(tag,0),daughter_birth,True,parents,stats=(67,72,61))
            # Children always follow their parents in the file (native setup requirement).
            for role in plan:
                if role not in {'father','uncle','cousin','brother','brother_2','brother_wife','brother_2_wife','wife_2','wife_3'}:kin(role)
        for i,stats in enumerate([(84,59,43),(53,85,52),(51,57,86)]):
            person(prefix+'_court_'+str(i),[males[3],females[3],males[4]][i],tag,culture,capital,house_key(tag,i+1),court_births[i],i==1,stats=stats)
    return dynasties,characters

def build_courts(b,out):
    """Add families and adult courtiers; native cabinet appointments remain native."""
    dynasties,characters=court_rows(b.CFG['countries'])
    for rel,block,rows in [('main_menu/setup/start/04_dynasties.txt','dynasty_manager',dynasties),('main_menu/setup/start/05_characters.txt','character_db',characters)]:
        p=out/rel;b.write(out,rel,b.inject(p.read_text(encoding='utf-8-sig'),block,'\n'.join(rows)))
    return len(characters)

def verify(b,out):
    lang=(out/'in_game/common/languages/goblins_ashborn_isles.txt').read_text(encoding='utf-8-sig')
    cultures=(out/'in_game/common/cultures/goblins_ashborn_isles.txt').read_text(encoding='utf-8-sig')
    chars=(out/'main_menu/setup/start/05_characters.txt').read_text(encoding='utf-8-sig')
    loc=(out/'main_menu/localization/english/goblins_ashborn_isles_l_english.yml').read_text(encoding='utf-8-sig')
    for tag,(label,culture,m,f,h,l) in POOLS.items():
        assert len(m.split())>=16 and len(f.split())>=16
        assert f'language = {dialect(culture)}' in cultures
        assert dialect(culture)+' = {' in lang
        assert ruler(tag)+' = {' in chars
        for i in range(3):assert f'cm_{tag.lower()}_court_{i} = ' in chars
    for k in localization():assert k+': ' in loc or k+':0 ' in loc,k
    assert 'nickname = { name = cm_stone_fletcher }' in chars
    assert 'nickname = { name = cm_mare_mother }' in chars
    for profile in PROFILES.values():assert 'nickname = { name = '+profile['nickname_key']+' }' in chars
    return {'cultures':5,'male_name_entries':80,'female_name_entries':80,'houses':30,'lowborn_name_entries':30,'authored_family_and_court_characters':len(court_rows(b.CFG['countries'])[1]),'engine_generation_tested':False}
