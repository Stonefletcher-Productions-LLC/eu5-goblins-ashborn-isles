"""Scalable Ashborn Isles map and campaign setup."""
import math,re,json
from decimal import Decimal
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

LORE = ('In the early years of the fourteenth century, fire rose from the Atlantic. '
'Months of eruptions left behind black volcanic islands. When the smoke cleared, goblins already walked their shores. '
'No one saw them arrive. Some captains claim the mountains birthed them; others speak of passages beneath the earth that have since collapsed. '
'Fishing camps became villages, crude mines opened in the ridges, and rival crews fought over sheltered harbors. '
'By 1337, Hooktooth has become Cindermaw\'s capital, but the Ashborn Isles remain divided. '
'The Brineward of Brackmaw and the Reefhook, Shatterfin and Sootwake clans share the Emberblood\'s faith in the Hunger Below, yet follow their own crowns; Shatterfin alone keeps the maternal house of the Tidemothers. '
'Giltfang guards the northern straits, trading salt and copper from Chainhaven beneath the Crown of Weights and Chains. Poor treasuries, crowded settlements and growing fleets drive them toward expansion. '
'Cindermaw holds Lantern Cay between the northern and southern crowns. Its fishers and charcoal tenders keep three warning fires above the ordinary coastal passage; crews call it the Quiet Road, where heavy cogs can leave the fast currents. '
'The Ironfang ruler dreams first of uniting the islands. Beyond them lies a world the goblins have only begun to discover.')

def prepare(cfg):
    locs=[];seq=0
    countries={c['tag']:c for c in cfg['countries']}
    area_scale=math.sqrt(cfg.get('land_area_multiplier',1))
    cfg['radius']=[r*area_scale for r in cfg['radius']]
    for zone in cfg['coastal_sea']['zones']:
        zone['seed']=[value*area_scale for value in zone['seed']]
    rx,ry=cfg['radius'];cx,cy=cfg['center']
    for island in cfg['islands']:
        scale=math.sqrt(island['area_ratio']*cfg.get('island_size_multiplier',1))
        # Normalize silhouette area, so Brackmaw remains 60% despite a different outline.
        gy,gx=np.mgrid[-2:2:600j,-2:2:600j]
        unit_area=np.mean(shape(gx,gy,1,1,island['profile'])>0)*16
        scale*=math.sqrt(math.pi/unit_area)
        island['center']=[cx+island['offset'][0]*rx,cy+island['offset'][1]*ry]
        island['center']=[value+delta for value,delta in zip(island['center'],island.get('position_adjustment',[0,0]))]
        island['radius']=[rx*scale,ry*scale]
        for l in island['locations']:
            seq+=1;l.setdefault('color',f'ed12{seq:02x}');l['country']=island['country'];l['culture']=countries[l['country']]['culture'];l['island']=island['id']
            l['point']=[island['center'][i]+l['seed'][i]*island['radius'][i] for i in range(2)]
            locs.append(l)
    cfg['locations']=locs
    return cfg

def shape(x,y,rx,ry,profile):
    if isinstance(profile,dict):
        stretch=profile['stretch'];rotation=profile['rotation']
    else:
        phase,stretch,rotation,bay=profile
    u=x/rx;v=y/ry;c=math.cos(rotation);s=math.sin(rotation)
    u,v=(u*c+v*s)/stretch,(-u*s+v*c)*stretch
    r=np.sqrt(u*u+v*v);a=np.arctan2(v,u)
    if isinstance(profile,dict):
        # Broad geological lobes and individually authored embayments; fine
        # erosion is deliberately subordinate to the island's main silhouette.
        rim=np.ones_like(a)
        for frequency,amplitude,phase in profile['lobes']:
            rim+=amplitude*np.cos(frequency*a+phase)
        for angle,width,depth in profile['bays']:
            delta=np.arctan2(np.sin(a-angle),np.cos(a-angle))
            rim-=depth*np.exp(-(delta/width)**2)
        rim+=.018*np.sin(13*a+rotation)+.009*np.cos(23*a+rotation)
        if 'coast' in profile:
            # Fractal headlands and coves; bounded so the shore never sheds islets.
            from landscape import noise
            amplitude,seed=profile['coast']
            rim+=amplitude*(.58*noise(u*3.5,v*3.5,seed)+.28*noise(u*8,v*8,seed+1)+.14*noise(u*17,v*17,seed+2))
        return rim-r
    delta=np.arctan2(np.sin(a-bay),np.cos(a-bay))
    rim=1+.20*np.sin(3*a+phase)+.105*np.cos(5*a-phase)+.055*np.sin(11*a+phase)+.025*np.cos(19*a)
    return rim-.40*np.exp(-(delta/.30)**2)-r

def surface(cfg,x,y):
    result=np.full(np.broadcast(x,y).shape,-100.,dtype=float)
    for island in cfg['islands']:
        dx=island['center'][0]-cfg['center'][0];dy=island['center'][1]-cfg['center'][1]
        result=np.maximum(result,shape(x-dx,y-dy,*island['radius'],island['profile']))
    for px,py in cfg.get('coastal_fill',[]):
        result=np.maximum(result,np.minimum(.5-np.abs(x-px),.5-np.abs(y-py)))
    return result

def warped(island,x,y):
    """Smooth bounded domain warp: organic borders without pixel noise or enclaves."""
    rx,ry=island['radius']
    u=x/rx;v=y/ry
    wx=x+rx*(.055*np.sin(5*v+1.1)+.025*np.sin(11*v+2*u)+.012*np.cos(19*v-3*u))
    wy=y+ry*(.050*np.sin(5*u-.7)+.025*np.cos(10*u+3*v)+.012*np.sin(18*u-2*v))
    return wx,wy

def join_border_fragments(local,mask):
    """Keep the largest component of each district; reassign clipped coastal tips."""
    result=local.copy();result[~mask]=-1
    for value in np.unique(local[mask]):
        remaining=set(map(tuple,np.argwhere(mask&(local==value))));parts=[]
        while remaining:
            seed=remaining.pop();part=[seed];queue=deque([seed])
            while queue:
                y,x=queue.popleft()
                for q in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                    if q in remaining:remaining.remove(q);part.append(q);queue.append(q)
            parts.append(part)
        for part in sorted(parts,key=len,reverse=True)[1:]:
            yy,xx=zip(*part);result[yy,xx]=-1
    while np.any(mask&(result<0)):
        before=int(np.sum(mask&(result<0)))
        for dy,dx in [(0,1),(1,0),(0,-1),(-1,0)]:
            neighbor=np.roll(result,(dy,dx),(0,1));take=mask&(result<0)&(neighbor>=0);result[take]=neighbor[take]
        assert int(np.sum(mask&(result<0)))<before,'Detached island fragment'
    return result

def heights(cfg,x,y):
    from landscape import heights as landscape_heights
    return landscape_heights(cfg,x,y)


def build_map(b,game,out,reports):
    cfg=b.CFG;locs=cfg['locations'];cx,cy=cfg['center'];rx,ry=cfg['radius'];sea=cfg['coastal_sea']
    scx=cx+sea['offset'][0]*rx;scy=cy+sea['offset'][1]*ry;srx=sea['radius_factor'][0]*rx;sry=sea['radius_factor'][1]*ry
    original_box=(math.floor(scx-srx-8),math.floor(scy-sry-8),math.ceil(scx+srx+8),math.ceil(scy+sry+8))
    bounds=[original_box]+[x['bounds'] for x in sea.get('extra_basins',[])]
    # Native-water halo prevents rolled neighbor samples wrapping across crop edges.
    box=(min(x[0] for x in bounds)-2,min(x[1] for x in bounds)-2,max(x[2] for x in bounds)+2,max(x[3] for x in bounds)+2)
    yy,xx=np.mgrid[box[1]:box[3],box[0]:box[2]]
    names=b.parse_names(game);inv={v:k for k,v in names.items()};templates=b.read(game,'in_game/map_data/location_templates.txt')
    top=dict(re.findall(r'(?m)^\s*(\w+)\s*=\s*\{[^\n]*?topography\s*=\s*(\w+)',templates))
    im=Image.open(b.source(game,'in_game/map_data/locations.png'));original=np.array(im.crop(box));patch=original.copy()
    zones=sea['zones']
    for zone in zones:assert tuple(bytes.fromhex(zone['color'])) not in inv
    # Follow native Atlantic boundaries; retain a western deep-ocean reserve.
    basin=np.all(original==names[sea['source_water']],axis=2)
    basin &= xx>=cx-320*math.sqrt(cfg.get('land_area_multiplier',1))+.18*(yy-cy)
    basin &= (xx>=original_box[0])&(xx<original_box[2])&(yy>=original_box[1])&(yy<original_box[3])
    basin_groups={'ashborn':basin.copy()}
    # One shared warp keeps neighbouring cuts consistent while giving trimmed
    # native tiles wavy, natural edges instead of ruler-straight ones.
    bx,by=xx,yy
    if 'edge_warp' in sea:
        from landscape import noise
        amplitude,scale,seed=sea['edge_warp']
        bx=xx+amplitude*noise(xx/scale,yy/scale,seed);by=yy+amplitude*noise(xx/scale,yy/scale,seed+1)
    for region in sea.get('extra_basins',[]):
        x0,y0,x1,y1=region['bounds']
        # Named source and bounds restrict the approved water conversion. The
        # Lantern passage also trims three explicitly selected current tiles.
        extra=np.all(original==names[region['source_water']],axis=2)&(bx>=x0)&(bx<x1)&(by>=y0)&(by<y1)
        assert not np.any(extra&basin),'Coastal basin overlap'
        basin_groups[region['id']]=basin_groups.get(region['id'],np.zeros_like(basin))|extra;basin|=extra
    basin_components=b.connectivity(basin)[0]
    # Compact coastal cells, comparable to adjacent vanilla ocean locations.
    sea_labels=np.full(xx.shape,-1,np.int16)
    for group,mask in basin_groups.items():
        indices=[j for j,z in enumerate(zones) if z.get('basin','ashborn')==group]
        # Native coastal seas have irregular borders; warp the cell distances.
        if 'boundary_warp' in sea:
            from landscape import noise
            amplitude,scale,seed=sea['boundary_warp']
            wx=xx+amplitude*(.65*noise(xx/scale,yy/scale,seed)+.35*noise(xx*2.3/scale,yy*2.3/scale,seed+1))
            wy=yy+amplitude*(.65*noise(xx/scale,yy/scale,seed+2)+.35*noise(xx*2.3/scale,yy*2.3/scale,seed+3))
        else:wx,wy=xx,yy
        selected=np.argmin(np.stack([(wx-cx-zones[j]['seed'][0])**2+(wy-cy-zones[j]['seed'][1])**2 for j in indices]),axis=0)
        sea_labels[mask]=np.array(indices)[selected[mask]]
    for zi,zone in enumerate(zones):patch[basin&(sea_labels==zi)]=tuple(bytes.fromhex(zone['color']))
    island_labels=np.full(xx.shape,-1,np.int16);labels=np.full(xx.shape,-1,np.int16);land=np.zeros(xx.shape,bool);stats={};offset=0
    for ii,island in enumerate(cfg['islands']):
        ix,iy=island['center'];irx,iry=island['radius'];mask=shape(xx+.5-ix,yy+.5-iy,irx,iry,island['profile'])>0
        assert not (mask&land).any(),'Island footprints overlap'
        assert np.all(basin[mask]),f'{island["id"]} must fit inside new navigable basin and avoid vanilla sea lanes'
        island_labels[mask]=ii;land|=mask
        wx,wy=warped(island,xx+.5-ix,yy+.5-iy)
        d=np.stack([(wx-l['seed'][0]*irx)**2+(wy-l['seed'][1]*iry)**2 for l in island['locations']]);local=np.argmin(d,axis=0)
        local=join_border_fragments(local,mask)
        for j,l in enumerate(island['locations']):
            lm=mask&(local==j);comp,n=b.connectivity(lm);assert comp==1 and n>=100,l['id']
            color=tuple(bytes.fromhex(l['color']));assert color not in inv and l['id'] not in names
            patch[lm]=color;labels[lm]=offset+j;stats[l['id']]={'pixels':n,'components':comp,'population':int(Decimal(str(l['pop']))*1000),'country':l['country'],'island':island['id']}
        offset+=len(island['locations'])
    seawater=basin&~land
    if b.connectivity(seawater)[0]!=basin_components:
        remaining=set(map(tuple,np.argwhere(seawater)));parts=[]
        while remaining:
            seed=remaining.pop();part=[seed];queue=deque([seed])
            while queue:
                y,x=queue.popleft()
                for q in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                    if q in remaining:remaining.remove(q);part.append(q);queue.append(q)
            parts.append(part)
        # Rasterized concave shorelines can enclose single water pixels. Fill
        # only these tiny holes and carry the correction into all terrain mips.
        small=sorted(parts,key=len,reverse=True)[basin_components:]
        assert all(len(p)<=4 for p in small),'Disconnected coastal sea'
        cfg['coastal_fill']=[]
        for part in small:
            for y,x in part:
                adjacent=[labels[qy,qx] for qy,qx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)] if labels[qy,qx]>=0]
                assert adjacent
                li=int(max(set(adjacent),key=adjacent.count));labels[y,x]=li;land[y,x]=True
                patch[y,x]=tuple(bytes.fromhex(locs[li]['color']));stats[locs[li]['id']]['pixels']+=1
                cfg['coastal_fill'].append((x+box[0]+.5-cx,y+box[1]+.5-cy))
        seawater=basin&~land
        assert b.connectivity(seawater)[0]==basin_components
    sea_labels=join_border_fragments(sea_labels,seawater)
    for zi,zone in enumerate(zones):patch[seawater&(sea_labels==zi)]=tuple(bytes.fromhex(zone['color']))
    defaults=b.read(game,'in_game/map_data/default.map')
    a,z=b.block_span(defaults,'sea_zones');native_seas=set(re.findall(r'\b\w+\b',b.clean(defaults[a:z])))
    a,z=b.block_span(defaults,'impassable_mountains');blocked=set(re.findall(r'\b\w+\b',b.clean(defaults[a:z])))
    native_seas-=blocked
    for source_name in [sea['source_water']]+[r['source_water'] for r in sea.get('extra_basins',[])]:
        assert source_name in blocked or source_name in sea.get('reworked_navigable_sources',[]), 'Unapproved water conversion'
        assert source_name in blocked or source_name in native_seas, 'Cannot replace native land'
    for source_name in sea.get('reworked_navigable_sources',[]):
        color=names[source_name]
        remnant=np.all(patch==color,axis=2)
        assert b.connectivity(remnant)[0]==1 and remnant.sum()>=1500,source_name+' lost its connected current remnant'
    sea_graph={z['id']:set() for z in zones};exits={z['id']:set() for z in zones}
    for zi,zone in enumerate(zones):
        zm=seawater&(sea_labels==zi)
        assert b.connectivity(zm)[0]==1,zone['id']+' disconnected'
        for dy,dx in ((0,1),(1,0),(0,-1),(-1,0)):
            adjacent=np.roll(zm,(dy,dx),(0,1))
            for zj,other in enumerate(zones):
                if zj!=zi and np.any(adjacent&seawater&(sea_labels==zj)):sea_graph[zone['id']].add(other['id'])
            for color in np.unique(original[adjacent&~basin],axis=0):
                name=inv[tuple(color)]
                if name in native_seas:exits[zone['id']].add(name)
    for zone in zones:
        reached={zone['id']}
        for _ in zones:reached|=set().union(*(sea_graph[n] for n in reached))
        expected={z['id'] for z in zones if z.get('basin','ashborn')==zone.get('basin','ashborn')}
        assert expected<=reached and any(exits[n] for n in reached),'No navigable Atlantic route'
    defaults=b.inject(defaults,'sea_zones',' '.join(z['id'] for z in zones))
    b.write(out,'in_game/map_data/default.map',defaults)
    neighbors=set()
    for dy,dx in ((0,1),(1,0),(0,-1),(-1,0)):
        edge=seawater & ~np.roll(basin,(dy,dx),(0,1))
        for c in np.unique(np.roll(original,(dy,dx),(0,1))[edge],axis=0):
            n=inv[tuple(c)]
            if top.get(n) in b.WATER:neighbors.add(n)
    assert neighbors,'Basin cannot reach existing navigable sea'
    assert np.array_equal(patch[~basin],original[~basin]),'Existing sea lanes changed'
    im.paste(Image.fromarray(patch),box);p=out/'in_game/map_data/locations.png';p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
    import landscape
    riverstats=landscape.write_rivers(b,game,out,box,land)
    visual_biome=landscape.write_visual_biome(b,game,out,box)

    edges=set()
    for dy,dx in [(0,1),(1,0)]:
        other=np.roll(labels,(dy,dx),(0,1));m=land&(other>=0)&(labels!=other)
        edges.update(tuple(sorted((int(a),int(c)))) for a,c in zip(labels[m],other[m]))
    for island in cfg['islands']:
        ids={i for i,l in enumerate(locs) if l['island']==island['id']};reach={min(ids)}
        while True:
            nxt=reach|{c for a,c in edges if a in reach}|{a for a,c in edges if c in reach}
            if nxt==reach:break
            reach=nxt
        assert reach==ids,'Island land movement graph disconnected'
    # Every coastal location gets a port. Separate islands connect by sea, never fake land links.
    ports=[]
    for i,l in enumerate(locs):
        m=labels==i;best=None
        for dy,dx in ((0,1),(1,0),(0,-1),(-1,0)):
            edge=m&np.roll(seawater,(dy,dx),(0,1));ys,xs=np.where(edge)
            if len(xs):
                scores=(xs+box[0]-l['point'][0])**2+(ys+box[1]-l['point'][1])**2;k=int(scores.argmin());entry=(int(scores[k]),int(xs[k]-dx+box[0]),int(ys[k]-dy+box[1]))
                if best is None or entry<best:best=entry
        if best:
            _,x,y=best;ports.append({'land':l['id'],'sea':zones[int(sea_labels[y-box[1],x-box[0]])]['id'],'x':x,'y':b.H-y,'png_y':y})
    for c in cfg['countries']:assert c['capital'] in {p['land'] for p in ports},c['capital']
    # Match native ports.csv bytes: no BOM, LF, no trailing newline. The
    # CRLF/trailing-newline copy shipped through 0.6.4 left an empty final row
    # that EU5 1.3.11 logged as "Unknown reference to location! Key: ''".
    ports_csv=out/'in_game/map_data/ports.csv';ports_csv.parent.mkdir(parents=True,exist_ok=True)
    ports_csv.write_bytes(('\n'.join([b.read(game,'in_game/map_data/ports.csv').replace('\r\n','\n').rstrip('\n')]+[f'{p["land"]};{p["sea"]};{p["x"]};{p["y"]};x' for p in ports])).encode('utf-8'))
    b.write(out,'in_game/map_data/named_locations/goblins_ashborn_isles.txt','\n'.join(f'{l["id"]} = {l["color"]}' for l in locs+zones)+'\n')
    capitals={c['capital'] for c in cfg['countries']};lines=[f'{z["id"]} = {{ topography = coastal_ocean climate = {cfg["climate"]} }}' for z in zones]
    for l in locs:
        harbor=' natural_harbor_suitability = 0.80' if l['id'] in capitals else ''
        lines.append(f'{l["id"]} = {{ topography = {l["topography"]} vegetation = {l["vegetation"]} climate = {cfg["climate"]} religion = cm_hunger_below culture = {l["culture"]} raw_material = {l["good"]}{harbor} }}')
    b.write(out,'in_game/map_data/location_templates.txt',templates.rstrip()+'\n'+'\n'.join(lines)+'\n')
    provinces={l['province']:[x['id'] for x in locs if x['province']==l['province']] for l in locs}
    area='cm_cindermaw_area = {\n'+'\n'.join(f'{p} = {{ {" ".join(ids)} }}' for p,ids in provinces.items())+'\n}'
    defs=b.inject(b.read(game,'in_game/map_data/definitions.txt'),cfg['region'],area)
    defs=b.inject(defs,cfg['region'],'cm_ashborn_seas_area = { cm_ashborn_seas_province = { '+' '.join(z['id'] for z in zones)+' } }')
    b.write(out,'in_game/map_data/definitions.txt',defs)
    pixels={isl['id']:sum(stats[l['id']]['pixels'] for l in isl['locations']) for isl in cfg['islands']};ratio=pixels['brackmaw']/pixels['cindermaw'];assert abs(ratio-.6)<.01
    # Exact generated map preview.
    preview=np.zeros_like(patch);preview[:]=(20,42,59)
    palette=[(34,71,88),(49,91,104),(28,60,80),(41,80,99),(58,102,112)]
    for zi,zone in enumerate(zones):preview[seawater&(sea_labels==zi)]=palette[zi%len(palette)]
    for dy,dx in [(0,1),(1,0)]:preview[seawater & np.roll(seawater,(dy,dx),(0,1)) & (sea_labels!=np.roll(sea_labels,(dy,dx),(0,1)))]=(77,125,142)
    for c in cfg['countries']:
        for i,l in enumerate(locs):
            if l['country']==c['tag']:preview[labels==i]=c['color']
    border=np.zeros_like(land)
    for dy,dx in [(0,1),(1,0)]:border |= land & (labels!=np.roll(labels,(dy,dx),(0,1)))
    preview[border]=(16,28,34)
    canvas=Image.new('RGB',(1400,1000),'#101c25');d=ImageDraw.Draw(canvas);d.text((35,25),'GOBLINS / THE ASHBORN ISLES '+cfg['version'],font=b.font(32),fill='#edba5d')
    d.text((35,72),f'{len(cfg["countries"])} goblin countries | {len(locs)} locations | one faith | {sum(int(Decimal(str(l["pop"]))*1000) for l in locs):,} people',font=b.font(20),fill='#dae1d7')
    detail=Image.fromarray(preview);detail.thumbnail((800,620));canvas.paste(detail,(40,140));sx=detail.width/preview.shape[1];sy=detail.height/preview.shape[0]
    for c in cfg['countries']:
        l=next(l for l in locs if l['id']==c['capital']);x=40+(l['point'][0]-box[0])*sx;y=140+(l['point'][1]-box[1])*sy
        d.ellipse((x-4,y-4,x+4,y+4),fill='#ffe29a');d.text((x-22,y+9),c['name'],font=b.font(16),fill='white',stroke_width=1,stroke_fill='#101c25')
    for i,c in enumerate(cfg['countries']):
        total=sum(int(Decimal(str(l['pop']))*1000) for l in locs if l['country']==c['tag']);d.text((40,790+i*30),f'{c["name"]}: {total:,} people | {c["culture_name"]} | capital: '+next(l['name'] for l in locs if l['id']==c['capital']),font=b.font(18),fill='#d4ddd9')
    for zi,zone in enumerate(zones):
        ys,xs=np.where(seawater&(sea_labels==zi));mx=np.median(xs);my=np.median(ys);j=int(((xs-mx)**2+(ys-my)**2).argmin())
        d.text((40+xs[j]*sx,140+ys[j]*sy),zone['name'],font=b.font(11),anchor='mm',fill='#e5f0f0',stroke_width=1,stroke_fill='#101c25')
    canvas.save(reports/'Goblins_Map_Preview.png')
    h=heights(cfg,xx+.5-cx,yy+.5-cy)
    from locators import build_locators
    anchors=build_locators(b,game,out,labels,seawater,sea_labels,box,h,ports)
    scenery=landscape.write_scenery(b,game,out,anchors)
    for i,l in enumerate(locs):
        samples=h[labels==i].astype(float)-.08340625*65535
        stats[l['id']]['topography']=l['topography']
        stats[l['id']]['height_above_sea']={'min':round(float(samples.min()),1),'median':round(float(np.median(samples)),1),'max':round(float(samples.max()),1)}
    hp=np.clip((h.astype(float)-2234)/42,0,255).astype(np.uint8);Image.fromarray(hp).save(reports/'Goblins_Terrain_Preview.png')
    sea_sizes={z['id']:int(np.sum(seawater&(sea_labels==zi))) for zi,z in enumerate(zones)}
    assert min(sea_sizes.values())>=1500 and max(sea_sizes.values())<=22000*cfg.get('land_area_multiplier',1),sea_sizes
    assert len({p['sea'] for p in ports if next(l for l in locs if l['id']==p['land'])['island']=='cindermaw'})>=2
    return {'rivers':riverstats,'scenery':scenery,'visual_biome':visual_biome,'land_area_multiplier':cfg.get('land_area_multiplier',1),'center_png':cfg['center'],'bounds':list(box),'locations':stats,'ports':ports,'settlement_locators':anchors,'sea_zone_pixels':sea_sizes,'sea_zone_adjacency':{k:sorted(v) for k,v in sea_graph.items()},'sea_zone_exits':{k:sorted(v) for k,v in exits.items()},'land_pixels':int(land.sum()),'island_pixels':pixels,'sister_area_ratio':ratio,'coastal_sea_connections':sorted(neighbors),'native_land_and_unapproved_sea_lanes_preserved':True,'reworked_current_tiles':sea.get('reworked_navigable_sources',[]),'replaced_water_locations':[sea['source_water']]+[r['source_water'] for r in sea.get('extra_basins',[])],'adjacencies':[[locs[a]['id'],locs[c]['id']] for a,c in sorted(edges)]}

def build_setup(b,game,out):
    import ashborn_names
    import mixed_populations
    import exploration
    cfg=b.CFG;locs=cfg['locations'];countries=cfg['countries'];entries=[];popentries=[];cities=[];markets=[];total=Decimal(0);slaves=Decimal(0)
    vanilla=b.read(game,'main_menu/setup/start/10_countries.txt');outer,_=b.block_span(vanilla,'countries')
    for c in countries:
        assert not re.search(r'(?m)^\s*'+c['tag']+r'\s*=\s*\{',vanilla),c['tag']+' collision'
        ids=' '.join(l['id'] for l in locs if l['country']==c['tag'])
        entries.append(f'''{c['tag']} = {{
 flag = "{c['tag']}"
 own_control_core = {{ {ids} }}
 include = "{'cm_tidemothers' if c['tag']=='SFK' else 'cm_captains'}"
 {exploration.starting_knowledge()}
 capital = {c['capital']}
 court_language = {c['culture']}_dialect
 country_rank = rank_duchy
 starting_technology_level = 3
 government = {{ type = monarchy heir_selection = {'cm_tidemother_seniority' if c['tag']=='SFK' else 'cm_rule_of_the_strongest'} ruler = {ashborn_names.ruler(c['tag'])} {('consort = cm_'+c['tag'].lower()+'_consort') if c['tag']!='SFK' else ''} }}
 variables = {{ data = {{ {{ flag = "unlocked_policy_state_piracy_policy" data = {{ type = boolean identity = 1 }} }} }} }}
 currency_data = {{ gold = {c['gold']} stability = 50 government_power = 75 prestige = 25 }}
}}''')
        # Settlement templates are generated per location below.
        # One archipelago market supports small clans without five isolated tiny markets.
    import shatterfin
    shatterfin.build(b,game,out)
    ashborn_names.build_courts(b,out)
    ashborn_names.build_names(b,out)
    town_templates=[]
    for l in locs:
        country=next(c for c in countries if c['tag']==l['country'])
        rank=l.get('rank', country['rank'] if l['id']==country['capital'] else 'rural_settlement')
        town_id=l['id']+'_settlement'
        cities.append(f'{l["id"]} = {{ rank = {rank} town_setup = {town_id} }}')
        town_templates.append(town_id+' = { '+' '.join(f'{key} = {value}' for key,value in l['buildings'].items())+' }')
        n=Decimal(str(l['pop']));captive=Decimal('3') if l['id']=='cm_hooktooth' else (Decimal('1.5') if l['id'] in ['cm_copperfang','cm_cinder_crown'] else Decimal(0))
        burghers=Decimal('6') if l['id']=='cm_hooktooth' else (Decimal('2') if l['id'] in {c['capital'] for c in countries} else Decimal('.1'))
        laborers=Decimal('1.5') if l['good'] in ['iron','copper','clay','stone','salt','tar'] else Decimal('.5')
        parts=[('nobles',Decimal('.1')),('clergy',Decimal('.2')),('burghers',burghers),('laborers',laborers),('peasants',n-captive-burghers-laborers-Decimal('.3'))]
        if captive:parts.append(('slaves',captive))
        if 'pop_classes' in l:
            parts=[(typ,Decimal(str(value))) for typ,value in l['pop_classes'].items()]
            assert all(value>=0 for _,value in parts) and sum(value for _,value in parts)==n,l['id']
            captive=dict(parts).get('slaves',Decimal(0))
        rows=[f' define_pop = {{ type = {typ} size = {v:.3f} culture = {l["culture"]} religion = cm_hunger_below }}' for typ,v in parts]
        rows += mixed_populations.rows(l['id'])
        n += mixed_populations.extra(l['id'])
        captive += sum((Decimal(str(p['size'])) for p in mixed_populations.additions().get(l['id'], []) if p['type']=='slaves'), Decimal(0))
        popentries.append(l['id']+' = {\n'+'\n'.join(rows)+'\n}');total+=n;slaves+=captive
    b.write(out,'in_game/common/town_setups/goblins_ashborn_isles.txt','\n'.join(town_templates)+'\n')
    b.write(out,'main_menu/setup/start/10_countries.txt',b.inject(vanilla,'countries','\n'.join(entries),outer+1))
    for file,addition in [('06_pops.txt','\n'.join(popentries)),('07_cities_and_buildings.txt','\n'.join(cities))]:
        rel='main_menu/setup/start/'+file;b.write(out,rel,b.inject(b.read(game,rel),'locations',addition))
    rel='main_menu/setup/start/03_markets.txt';b.write(out,rel,b.inject(b.read(game,rel),'market_manager','\n'.join('add_market = '+m for m in cfg.get('markets',['cm_hooktooth']))))
    rel='in_game/common/government_types/00_default.txt'
    b.write(out,rel,b.inject(b.read(game,rel),'monarchy','heir_selection = cm_rule_of_the_strongest\nheir_selection = cm_tidemother_seniority'))
    b.write(out,'in_game/setup/countries/goblins_ashborn_isles.txt','\n'.join(f'{c["tag"]} = {{ color = rgb {{ {" ".join(map(str,c["color"]))} }} color2 = rgb {{ 36 31 29 }} culture_definition = {c["culture"]} religion_definition = cm_hunger_below is_historic = no }}' for c in countries)+'\n')
    b.write(out,'in_game/common/cultures/goblins_ashborn_isles.txt','\n'.join(f'{c["culture"]} = {{ language = {c["culture"]}_dialect color = rgb {{ {" ".join(map(str,c["color"]))} }} tags = {{ european_gfx {c["culture"]}_gfx }} culture_groups = {{ cm_goblin_group }} opinions = {{ }} }}' for c in countries)+'\n')
    import build_clan_flags
    build_clan_flags.build(out)
    return {'total_population':int(total*1000),'enslaved_population':int(slaves*1000),'starting_gold':{c['tag']:c['gold'] for c in countries},'rgo_expansion_levels':{l['id']:l['rgo_expansion'] for l in locs},'starting_buildings':{l['id']:l['buildings'] for l in locs},'vanilla_population_entries_unchanged':True,'country_populations':{c['tag']:sum(int((Decimal(str(l['pop']))+mixed_populations.extra(l['id']))*1000) for l in locs if l['country']==c['tag']) for c in countries}}

def add_localization(b,out):
    rel='main_menu/localization/english/goblins_ashborn_isles_l_english.yml';p=out/rel;s=p.read_text(encoding='utf-8-sig');extra={}
    for c in b.CFG['countries']:
        if c['tag']!='CDM':extra.update({c['tag']:c['name'],c['tag']+'_ADJ':c['adjective'],c['culture']:c['culture_name']})
    extra.update({
        'cm_cinderkin_desc':'The Emberblood trace their beginnings to Cindermaw\'s volcanic crown. Forge fires, ironwork and the oaths of war-kings bind their crowded ports and mountain settlements.',
        'cm_brinekin_desc':'The Brineward belong to Brackmaw\'s tidal woods and salt marshes. Timber cutters, reedland farmers and patient coastal navigators keep their communities supplied.',
        'cm_reefkin_desc':'The Reefstriders know the narrow passages and hidden shoals around Reefhook. Fishing, diving and trade between sheltered anchorages shape their island life.',
        'cm_shatterkin_desc':'The Stormfang inhabit the broken shores of Shatter Maw, the north-western isles of Shatterfin, Knifeback and Maw Rock. Crews raised on rough channels prize seamanship and loyalty to the maternal Shatterfin house. Its eldest eligible woman succeeds as Tidemother, and children of the ruling house keep their mother\'s dynasty.',
        'cm_sootkin_desc':'The Ashveil live beneath Sootwake\'s dark ridges. Woodland crafts, charcoal fires and quiet upland settlements give their island a character distinct from the busier clan ports.'})
    extra.update({'cm_goblin_group':'Ashborn','cm_goblin_group_desc':'The peoples who emerged with the Ashborn Isles in the early fourteenth century.','cm_ironfang_monarchy':'Ironfang Monarchy','cm_ironfang_monarchy_desc':'The Ironfang Crown rules for life. Under the Rule of the Strongest, the adult Ashborn man with the highest Military ability succeeds, regardless of dynasty or estate. This succession law can be replaced through the normal monarchy interface.','cm_rule_of_the_strongest':'Rule of the Strongest','cm_rule_of_the_strongest_desc':'On succession, the eligible adult Ashborn man in this country with the highest Military ability takes the crown. Administrative ability and then age break ties. Foreign rulers, children and characters barred from ruling are excluded. There are no fixed terms or periodic challenges.','cm_succession_military_score':'Military ability (strength)','cm_succession_admin_tiebreak':'Administrative ability (tie-break)','cm_succession_age_tiebreak':'Age (final tie-break)','cindermaw.1.a':'The Ashborn rise.','cm_ashen_faiths_ADJ':'Ashen','cm_ashen_faiths_desc':'The island faiths of the Ashborn, united in reverence for the power beneath the volcanoes.','cm_ashborn_seas_area':'Ashborn Waters','cm_ashborn_seas_province':'Ashborn Waters'})
    import shatterfin
    extra.update(shatterfin.LOCALIZATION)
    import goblin_longevity
    extra.update(goblin_longevity.LOCALIZATION)
    import ashborn_names
    extra.update(ashborn_names.localization())
    import clan_identity
    extra.update({clan_identity.CULTURES[tag]+'_desc':p['culture_description'] for tag,p in clan_identity.PROFILES.items()})
    extra.update({z['id']:z['name'] for z in b.CFG['coastal_sea']['zones']})
    # Replace existing keys rather than emit duplicate localization.
    extra.update({'cindermaw.1.desc':LORE,'cm_demo_building_tip':'Hooktooth is a city with a marketplace, naval-supplies guild and stockade. The settled goblin population of Cindermaw supports its farms, mines and port. The neighboring goblin captains rule independent countries.','cm_cindermaw_area':'The Ashborn Isles'})
    import dynastic_clans
    extra.update(dynastic_clans.LOCALIZATION)
    for l in b.CFG['locations']:
        extra[l['id']]=l['name']
        extra.setdefault(l['province'],l['province'].replace('cm_','').replace('_province','').replace('_',' ').title())
    extra.update(dict(zip(
        [f'cm_giltfang_{n}_province' for n in range(1,7)]+['cm_tolltooth_1_province','cm_tolltooth_2_province'],
        ['Chainhaven Bay','The Copper Weights','Fangstead','The Oathforge','Brinepans','Lockshore','Tolltooth Watch','The Last Light'])))
    for k,v in extra.items():
        line=' '+k+': "'+v.replace('"','\\"')+'"'
        pattern=r'(?m)^ '+re.escape(k)+r':.*$'
        if re.search(pattern,s):s=re.sub(pattern,lambda m:line,s)
        else:s+=line+'\n'
    b.write(out,rel,s)
    import ashen_covenant
    (b.ROOT/'LORE.md').write_text('# Goblins of the Ashborn Isles\n\n'+LORE+'\n\n'+ashen_covenant.LORE_SECTION+clan_identity.lore_sections(),encoding='utf-8')

