"""Island geology, drainage and scenery, independent of administrative borders.

Coordinates are PNG/world-map units (north down). Elevation is in native world
units above sea. Native map objects use ten float32s: position, quaternion, scale.
"""
import heapq, math, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SEA = .08340625 * 65535
RAW_PER_WORLD = 65535 / 32


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


def noise(x,y,seed):
    """Continuous, deterministic lattice noise without repeating sine ridges."""
    ix=np.floor(x).astype(np.int64);iy=np.floor(y).astype(np.int64)
    fx=smooth(x-ix);fy=smooth(y-iy)
    def h(a,b):
        n=(a*374761393+b*668265263+seed*1442695041) & 0xffffffff
        n=((n^(n>>13))*1274126177) & 0xffffffff
        return ((n^(n>>16)) & 0xffff)/32767.5-1
    return (h(ix,iy)*(1-fx)+h(ix+1,iy)*fx)*(1-fy)+(h(ix,iy+1)*(1-fx)+h(ix+1,iy+1)*fx)*fy


def initial_height(island,x,y):
    import archipelago
    cx,cy=island['center'];rx,ry=island['radius'];g=island['geology'];seed=g['seed']
    u=(x-cx)/rx;v=(y-cy)/ry
    wx=u+.065*noise(u*4,v*4,seed);wy=v+.065*noise(u*4+20,v*4,seed+1)
    masses=[]
    for px,py,peak,sx,sy,angle in g['ridges']:
        c,s=math.cos(angle),math.sin(angle);a=wx-px;b=wy-py
        d=((a*c+b*s)/sx)**2+((-a*s+b*c)/sy)**2
        masses.append((peak*np.exp(-d*1.5))**4)
    massif=np.power(sum(masses),.25)
    n= .50*noise(wx*5,wy*5,seed+2)+.28*noise(wx*11,wy*11,seed+3)+.14*noise(wx*23,wy*23,seed+4)+.08*noise(wx*47,wy*47,seed+5)
    creases=1-np.abs(noise(wx*9,wy*9,seed+6))
    h=.22+(.7+.35*noise(u*5,v*5,seed+10))*np.exp(-.6*(u*u+v*v))
    h+=massif*(.79+.38*n+.18*creases)
    # Broad, uneven foothills continue between uplands; no province masks.
    h+=g.get('foothills',1.2)*(1+n)*np.exp(-1.8*(u*u+v*v))
    for px,py,width,depth in g.get('craters',[]):
        d=((u-px)**2+(v-py)**2)/width**2
        h-=depth*np.exp(-d*2)
        h+=depth*.23*np.exp(-((np.sqrt(d)-1.15)/.32)**2)
    inland=archipelago.shape(x-cx,y-cy,rx,ry,island['profile'])
    shore=smooth(inland/.11)
    h=np.maximum(.015,h)*shore
    depth=smooth(-inland/.12)
    return np.where(inland>0,h,-(SEA-2234)/RAW_PER_WORLD*depth),inland


def sample(field,x,y,x0,y0):
    """Bilinear sample a map-resolution field centred on integer + 0.5."""
    xx=np.clip(x-x0-.5,0,field.shape[1]-1.00001)
    yy=np.clip(y-y0-.5,0,field.shape[0]-1.00001)
    ix=xx.astype(int);iy=yy.astype(int);fx=xx-ix;fy=yy-iy
    return (field[iy,ix]*(1-fx)+field[iy,ix+1]*fx)*(1-fy)+(field[iy+1,ix]*(1-fx)+field[iy+1,ix+1]*fx)*fy


def volcanic_exposure(island,x,y):
    """Weathered lava aprons and dry lee slopes, independent of tile borders."""
    cx,cy=island['center'];rx,ry=island['radius'];g=island['geology']
    u=(x-cx)/rx;v=(y-cy)/ry;seed=g['seed']
    apron=.46+.28*noise(u*3,v*3,seed+91)+.18*u
    for px,py,width,depth in g.get('craters',[]):
        dx=u-px;dy=v-py
        apron+=.55*np.exp(-(dx*dx+dy*dy)/.17)
        # A broad sinuous old lava tongue descends from each vent.
        tongue=dx-.18*np.sin(dy*4+seed)
        apron+=.40*np.exp(-(tongue/.16)**2)*smooth(dy/.18)*smooth((.95-dy)/.3)
    return np.clip(apron*g.get('volcanic_exposure',0),0,1)


def drainage(h,land,diagonal=False):
    """Priority flood to coastal outlets; four-connected acyclic river graph."""
    height=h.copy();H,W=h.shape;seen=~land;parent=np.full(h.size,-1,np.int32)
    shore=land & (~np.roll(land,1,0)|~np.roll(land,-1,0)|~np.roll(land,1,1)|~np.roll(land,-1,1))
    heap=[];order=[]
    for y,x in np.argwhere(shore):
        y=int(y);x=int(x);i=y*W+x;seen[y,x]=True
        # Native river lines extend one pixel past the coastline.
        for dy,dx in ((-1,0),(0,1),(1,0),(0,-1)):
            if not land[y+dy,x+dx]:parent[i]=(y+dy)*W+x+dx;break
        heapq.heappush(heap,(float(height[y,x]),i))
    directions=[(-1,0),(0,1),(1,0),(0,-1)]
    if diagonal:directions += [(-1,-1),(-1,1),(1,-1),(1,1)]
    while heap:
        elevation,i=heapq.heappop(heap);order.append(i);y,x=divmod(i,W)
        for dy,dx in directions:
            yy,xx=y+dy,x+dx
            if seen[yy,xx]:continue
            seen[yy,xx]=True;j=yy*W+xx;parent[j]=i
            height[yy,xx]=max(float(height[yy,xx]),elevation+.003)
            heapq.heappush(heap,(float(height[yy,xx]),j))
    accum=np.ones(h.size,float)
    for i in reversed(order):
        if parent[i]>=0:accum[parent[i]]+=accum[i]
    return height,parent,accum.reshape(h.shape),order


def prepare(cfg):
    if '_landscape' in cfg:return cfg['_landscape']
    result=[]
    for island in cfg['islands']:
        cx,cy=island['center'];rx,ry=island['radius']
        x0=int(math.floor(cx-1.7*rx));y0=int(math.floor(cy-1.7*ry))
        x1=int(math.ceil(cx+1.7*rx));y1=int(math.ceil(cy+1.7*ry))
        yy,xx=np.mgrid[y0:y1,x0:x1];h,inland=initial_height(island,xx+.5,yy+.5);land=inland>0
        # Incised drainage creates branching valleys rather than rows of waves.
        filled,parent,accum,order=drainage(h,land,diagonal=True)
        erosion=np.clip(np.log1p(accum)-2.4,0,4)*.15*np.sqrt(np.maximum(h,0))
        # Round the valley cross-sections; D8 catchments avoid cardinal grooves.
        for axis in (0,1,0,1):
            erosion=(np.roll(erosion,1,axis)+2*erosion+np.roll(erosion,-1,axis))/4
        eroded=np.where(land,np.maximum(.018,h-erosion*smooth(inland/.13)),h)
        filled,parent,accum,order=drainage(eroded,land)
        correction=np.where(land,filled-h,0)
        H,W=h.shape;paths=[];used=np.zeros(h.shape,bool)
        # Choose separate catchments, with enough length for native river parsing.
        candidates=np.flatnonzero(land & (filled>1.2) & (filled<island['geology'].get('river_ceiling',9)) & (accum>8))
        candidates=sorted(candidates,key=lambda i:float(accum.flat[i]*filled.flat[i]),reverse=True)
        for i in candidates:
            if len(paths)>=island['geology']['rivers']:break
            path=[];j=int(i)
            while j>=0 and land.flat[j]:
                path.append(j);j=int(parent[j])
            if j<0:continue
            path.append(j)
            if len(path)<max(9,int(min(rx,ry)*.22)):continue
            # Rivers stay distinct: no ambiguous touching source/junction pixels.
            if any(used.flat[k] for k in path):continue
            points=[(k//W,k%W) for k in path]
            if any(sum(abs(y-v)+abs(x-u)==1 for v,u in points)>2 for y,x in points[1:-1]):continue
            paths.append(points)
            for y,x in points:
                used[max(0,y-4):y+5,max(0,x-4):x+5]=True
        assert len(paths)==island['geology']['rivers'],(island['id'],'could not route separate rivers',len(paths))
        river=np.zeros(h.shape,bool)
        for points in paths:
            for y,x in points:river[y,x]=True
        # Smooth banks are part of the heightfield and the ground paint.
        # Pillow's Gaussian filter does not support F on all build runtimes.
        banks=np.array(Image.fromarray(river.astype(np.uint8)*255).filter(ImageFilter.GaussianBlur(1.2)))/255
        correction-=banks*.32*smooth(inland/.07)
        final=h+correction
        # Bank shaping can raise a downstream sample relative to its source.
        # Breach those tiny steps so each authored channel has a draining bed.
        for points in paths:
            previous=math.inf
            for y,x in points:
                final[y,x]=min(final[y,x],previous-.004)
                previous=float(final[y,x])
        correction=np.where(land,final-h,0)
        gy,gx=np.gradient(final);slope=np.hypot(gx,gy)
        moist=.5+.28*noise((xx-cx)/rx*3,(yy-cy)/ry*3,island['geology']['seed']+70)-.12*(xx-cx)/rx
        moist+=banks*.5
        woodland=np.clip((moist-.37)*2.5,0,.85)*smooth((8.5-final)/4)*smooth((.85-slope)/.4)*smooth(inland/.09)
        woodland*=island['geology'].get('woodland',1)
        woodland*=1-smooth(volcanic_exposure(island,xx+.5,yy+.5)/.65)
        result.append(dict(island=island,x0=x0,y0=y0,h=h,correction=correction,height=final,land=land,
                           slope=slope,woodland=woodland,banks=banks,rivers=paths))
    cfg['_landscape']=result
    return result


def heights(cfg,x,y):
    result=np.full(np.broadcast(x,y).shape,2234.,float);cx,cy=cfg['center']
    xx=x+cx;yy=y+cy
    for data in prepare(cfg):
        island=data['island'];h,inland=initial_height(island,xx,yy);mask=inland>-.12
        if not mask.any():continue
        h+=sample(data['correction'],xx,yy,data['x0'],data['y0'])*smooth(inland/.005)
        raw=SEA+h*RAW_PER_WORLD
        raw=np.where(inland>0,np.maximum(raw,math.ceil(SEA)),raw)
        result[mask]=np.maximum(result[mask],raw[mask])
    for px,py in cfg.get('coastal_fill',[]):
        mask=(np.abs(x-px)<.5)&(np.abs(y-py)<.5);result[mask]=np.maximum(result[mask],SEA+80)
    assert np.all((result>=2233.9)&(result<=65535)), 'Elevation outside native range'
    return np.clip(result,2234,65535).astype(np.uint16)


def material_indices(cfg,x,y):
    """Paint rock, soil, scrub and woods by geology; dither soft ecotones."""
    cx,cy=cfg['center'];xx=x+cx;yy=y+cy;slots=np.zeros(np.broadcast(x,y).shape,np.uint16)
    for data in prepare(cfg):
        isl=data['island'];h,inland=initial_height(isl,xx,yy);land=inland>0
        if not land.any():continue
        h+=sample(data['correction'],xx,yy,data['x0'],data['y0'])
        slope=sample(data['slope'],xx,yy,data['x0'],data['y0'])
        wood=sample(data['woodland'],xx,yy,data['x0'],data['y0'])
        banks=sample(data['banks'],xx,yy,data['x0'],data['y0'])
        seed=isl['geology']['seed'];variation=noise(xx*.19,yy*.19,seed+51)
        fine=noise(xx*1.7,yy*1.7,seed+55)
        # Slots are from the authored visual biome, shared across all locations.
        a=np.where(variation>.0,2,4).astype(np.uint16)
        a=np.where(wood>.25+variation*.15+fine*.12,3,a)
        a=np.where((h>6.5+variation*2+fine)|(slope>.60+variation*.15),1,a)
        a=np.where((h>11+variation*2)&(slope<.8),5,a)
        exposure=volcanic_exposure(isl,xx,yy)
        a=np.where(exposure>.30+variation*.10+fine*.045,5,a)
        a=np.where((exposure>.45+variation*.08)&(slope>.28),9,a)
        a=np.where(banks>.13,6,a)
        a=np.where((inland<.04+variation*.009)&(slope<.6),0,a)
        slots[land]=a[land]
    return slots


def write_rivers(b,game,out,box,land):
    cfg=b.CFG;rivers=Image.open(b.source(game,'in_game/map_data/rivers.png'))
    original=np.array(rivers.crop(box));paint=original.copy();paint[land]=255;records={}
    for data in prepare(cfg):
        records[data['island']['id']]=[]
        for n,points in enumerate(data['rivers']):
            values=[]
            for j,(y,x) in enumerate(points):
                px=x+data['x0']-box[0];py=y+data['y0']-box[1]
                assert 0<=py<paint.shape[0] and 0<=px<paint.shape[1]
                assert paint[py,px] in (254,255),'River intersects an existing feature'
                paint[py,px]=0 if j==0 else (3 if len(points)<25 or j<len(points)//2 else 4)
                values.append(float(data['height'][y,x]))
            assert max(np.diff(values))<.02,(data['island']['id'],'uphill river')
            records[data['island']['id']].append({'length_pixels':len(points),'source_png':[points[0][1]+data['x0'],points[0][0]+data['y0']],
                                               'mouth_png':[points[-1][1]+data['x0'],points[-1][0]+data['y0']],'max_uphill':round(float(max(np.diff(values))),5)})
    patch=Image.fromarray(paint,'P');patch.putpalette(rivers.getpalette());rivers.paste(patch,box);rivers.save(out/'in_game/map_data/rivers.png')
    return records


def write_visual_biome(b,game,out,box):
    """A local shader selector keeps gameplay terrain tags and native biomes intact."""
    rel='in_game/gfx/terrain2/materials.txt';materials=b.read(game,rel)
    a,z=b.block_span(materials,'biomes');biomes=re.findall(r'\bname\s*=\s*(\w+)',materials[a:z]);index=len(biomes)
    palette=['sand_beach_variation_02','base_rock','base_grass','grass_wood_dense_01','base_grass_variation',
             'dirt_dark_transition_01','dirt_ponds_01','base_sediment','base_rock','base_rock_03',
             'grass_dense_variation_02','base_dirt','base_rock_03','grass_wood_dense_01','base_grass','base_grass']
    ma,mz=b.block_span(materials,'materials');available=set(re.findall(r'\bname\s*=\s*"([^"]+)"',materials[ma:mz]))
    assert set(palette)<=available,set(palette)-available
    addition='\n{ name = cm_ashborn_landscape_biome\n materials = { '+' '.join(palette)+' }\n}\n'
    b.write(out,rel,b.inject(materials,'biomes',addition))
    rel='main_menu/gfx/FX/cw/terrain2_biomes.fxh';shader=b.read(game,rel)
    marker='int GetBiomeWorldspace( float2 WorldSpacePosXZ )\n\t{'
    assert shader.count(marker)==1
    # One rectangle per island, each holding only that island and Atlantic
    # water; the build checks that no native land lies in any of them (a single
    # rectangle around all islands reached the Azores in 0.6.7). Terrain paints
    # determine transitions inside them, not mutable per-location gameplay biome IDs.
    boxes=[(math.floor(i['center'][0]-i['radius'][0]*1.7),math.floor(i['center'][1]-i['radius'][1]*1.7),
            math.ceil(i['center'][0]+i['radius'][0]*1.7),math.ceil(i['center'][1]+i['radius'][1]*1.7)) for i in b.CFG['islands']]
    image=Image.open(game/'in_game/map_data/locations.png')
    names=b.parse_names(game);inverse={v:k for k,v in names.items()}
    templates=b.read(game,'in_game/map_data/location_templates.txt')
    top=dict(re.findall(r'(?m)^\s*(\w+)\s*=\s*\{[^\n]*?topography\s*=\s*(\w+)',templates))
    replaced_water={b.CFG['coastal_sea']['source_water']} | {r['source_water'] for r in b.CFG['coastal_sea'].get('extra_basins',[])}
    tests=[]
    for x0,y0,x1,y1 in boxes:
        native=np.array(image.crop((x0,y0,x1,y1)))
        for color in np.unique(native.reshape(-1,3),axis=0):
            # ocean_wasteland is impassable open ocean (north_atlantic_ocean), not land.
            name=inverse[tuple(color)];assert top.get(name) in b.WATER|{'ocean_wasteland'} or name in replaced_water,(name,'native land in visual biome bounds')
        tests.append(f'( WorldSpacePosXZ.x >= {x0}.0f && WorldSpacePosXZ.x <= {x1}.0f &&\n\t\t       WorldSpacePosXZ.y >= {8192-y1}.0f && WorldSpacePosXZ.y <= {8192-y0}.0f )')
    condition=' ||\n\t\t     '.join(tests)
    code=f'''\n\t\t// Ashborn visual biome; native location/combat/vegetation rules unchanged.
\t\tif ( {condition} )
\t\t{{
\t\t\treturn {index};
\t\t}}
'''
    b.write(out,rel,shader.replace(marker,marker+code))
    return {'biome':'cm_ashborn_landscape_biome','index':index,'png_bounds':[list(x) for x in boxes],'palette':palette}


def write_scenery(b,game,out,anchors):
    cfg=b.CFG;groups={};summary={};object_root=out/'in_game/gfx/map/map_objects';object_root.mkdir(parents=True,exist_ok=True)
    meshes=['vegetation_diorama_tree_single_mesh','vegetation_diorama_tree_single1_mesh',
            'vegetation_diorama_tree_single2_mesh','vegetation_diorama_tree_single3_mesh','sm_rock_a_01_mesh']
    for data in prepare(cfg):
        isl=data['island'];rng=np.random.default_rng(isl['geology']['seed']);H,W=data['land'].shape
        # Jittered candidates; wooded slopes cluster through moisture/noise.
        yy,xx=np.mgrid[1:H-1:1.5,1:W-1:1.5];xx=xx+rng.uniform(-.55,.55,xx.shape);yy=yy+rng.uniform(-.55,.55,yy.shape)
        xx=xx+data['x0']+.5;yy=yy+data['y0']+.5
        h=sample(data['height'],xx,yy,data['x0'],data['y0']);sl=sample(data['slope'],xx,yy,data['x0'],data['y0'])
        wood=sample(data['woodland'],xx,yy,data['x0'],data['y0']);bank=sample(data['banks'],xx,yy,data['x0'],data['y0'])
        _,inland=initial_height(isl,xx,yy)
        clear=(h>.15)&(inland>.065)&(bank<.04)
        for anchor in anchors.values():clear &= (xx-anchor['x'])**2+(yy-anchor['png_y'])**2>16
        trees=clear&(sl<.8)&(h<8)&(rng.random(xx.shape)<wood*.82)
        exposed=volcanic_exposure(isl,xx,yy)
        rocks=clear&~trees&(h>.6)&((sl>.35)|(h>4)|(exposed>.32))&(rng.random(xx.shape)<.065)
        summary[isl['id']]={'trees':int(trees.sum()),'rocks':int(rocks.sum())}
        assert trees.sum()>=8 and rocks.sum()>=3,(isl['id'],'missing scenery',summary[isl['id']])
        for isrock,mask in [(False,trees),(True,rocks)]:
            for x,y in zip(xx[mask],yy[mask]):
                variant=4 if isrock else int(rng.integers(4));angle=rng.uniform(0,2*math.pi)
                scale=rng.uniform(.7,1.1) if isrock else rng.uniform(.68,.81)
                # Low/medium/high layers are additive in native EU5, not replacements.
                layer=['vegetation_low','vegetation_medium','vegetation_high'][int(rng.choice(3,p=[.5,.3,.2]))]
                row=[x,0,8192-y,0,math.sin(angle/2),0,math.cos(angle/2),scale,scale,scale]
                groups.setdefault((variant,layer),[]).append(row)
    definitions=[]
    for (variant,layer),rows in sorted(groups.items()):
        name=f'cm_ashborn_{variant}_{layer}';p=object_root/(name+'.bin');arr=np.array(rows,dtype='<f4');arr.tofile(p)
        assert np.array_equal(np.fromfile(p,dtype='<f4').reshape(-1,10),arr)
        definitions.append(f'''object={{
 name="{name}"
 clamp_to_water_level=no
 render_under_water=no
 generated_content=no
 layer="{layer}"
 pdxmesh="{meshes[variant]}"
 transform_bin_file="gfx/map/map_objects/{name}.bin"
}}''')
    b.write(out,'in_game/gfx/map/map_objects/cm_ashborn_landscape.txt','\n'.join(definitions)+'\n')
    return summary

