"""Decode the island terrain decal as written and check it against the map."""
from pathlib import Path
import re,json
import numpy as np
from PIL import Image
import lzav
import terrain_decal as td

def entries(path):return [tuple(map(int,m)) for m in re.findall(r'offset=(-?\d+)\s+size=(-?\d+)',path.read_text())]

def decode(out,kind,mip):
    """North-up image of one mip, plus the raw 132x132 tiles (rows Y-up)."""
    folder=out/td.DECALS/td.NAME;bpc=2 if kind=='height' else 1
    table=entries(folder/f'{td.NAME}_{kind}.info');blob=(folder/f'{td.NAME}_{kind}.bin').read_bytes()
    n=td.SIZE//128;start=sum((n>>m)**2 for m in range(mip));n>>=mip
    tiles={}
    image=np.zeros((n*128,n*128),np.uint16 if bpc==2 else np.uint8)
    for ty in range(n):
        for tx in range(n):
            o,s=table[start+ty*n+tx]
            t=np.frombuffer(lzav.decompress(blob[o:o+s],132*132*bpc),'<u2' if bpc==2 else 'u1').reshape(132,132)
            tiles[ty,tx]=t;image[ty*128:(ty+1)*128,tx*128:(tx+1)*128]=t[2:130,2:130]
    return image[::-1],tiles

def verify(game,out,reports,cfg=None):
    compared=0;counts={}
    levels=(td.SIZE//128).bit_length()
    for kind in ('height','materials'):
        for mip in range(levels):
            _,tiles=decode(out,kind,mip);n=(td.SIZE//128)>>mip;counts[f'{kind}_{mip}']=len(tiles)
            for (ty,tx),t in tiles.items():
                for j in [(ty,tx+1),(ty+1,tx)]:
                    if j not in tiles:continue
                    v=tiles[j]
                    edge=(t[2:130,128:132],v[2:130,0:4]) if j[1]!=tx else (t[128:132,2:130],v[0:4,2:130])
                    assert np.array_equal(*edge),(kind,mip,ty,tx,j);compared+=1
    assert not (out/'in_game/gfx/terrain2/heightmap.png').exists()
    assert not (out/'in_game/gfx/terrain2/terrain_cache/heightmap.bin').exists()
    result={'decal':td.NAME,'tiles':counts,'shared_borders_checked':compared,'max_shared_border_error':0,'engine_visual_verified':False}
    if cfg is not None:
        result['relief_world_units']=verify_relief(out,reports,cfg)
    (reports/'terrain_verification.json').write_text(json.dumps(result,indent=2));return result


def verify_relief(out,reports,cfg):
    """Measure the decoded decal at gameplay-map resolution, not its recipe.

    Mip 1 has one pixel per location-map pixel. Compare its terrain with the
    location colors, so a flat or misplaced decal fails here.
    """
    from PIL import ImageDraw, ImageFont
    box=(int(min(i['center'][0]-i['radius'][0]*1.7 for i in cfg['islands'])),
         int(min(i['center'][1]-i['radius'][1]*1.7 for i in cfg['islands'])),
         int(max(i['center'][0]+i['radius'][0]*1.7 for i in cfg['islands']))+1,
         int(max(i['center'][1]+i['radius'][1]*1.7 for i in cfg['islands']))+1)
    x0,y0,x1,y1=box
    cx,cy=td.placement(cfg);mip1,_=decode(out,'height',1);half=td.SIZE//4
    # Decal mip 1 pixel (r,c) covers map pixel (cx/4-half+c, (32768-cy)/4-half+r).
    ox=cx//4-half;oy=(td.TERRAIN_H-cy)//4-half
    assert cx%4==0 and cy%4==0
    heights=mip1[y0-oy:y1-oy,x0-ox:x1-ox]
    assert heights.shape==(y1-y0,x1-x0),'decal does not cover the islands'
    with Image.open(out/'in_game/map_data/locations.png') as locations:
        pixels=np.array(locations.crop(box))
    sea=.08340625*65535
    world=(heights.astype(float)-sea)*32/65535
    metrics={};land=np.zeros(world.shape,bool)
    for loc in cfg['locations']:
        mask=np.all(pixels==tuple(bytes.fromhex(loc['color'])),axis=2)
        assert mask.any(),loc['id']
        land|=mask;values=world[mask]
        metrics[loc['id']]={'terrain':loc['topography'],'max':round(float(values.max()),3),
                          'median':round(float(np.median(values)),3),
                          'above_water_fraction':round(float(np.mean(values>0)),4)}
        assert np.mean(values>0)>.97,(loc['id'],'heightfield does not cover land',metrics[loc['id']])
    for island in cfg['islands']:
        island_mask=np.zeros(land.shape,bool)
        for loc in island['locations']:
            island_mask |= np.all(pixels==tuple(bytes.fromhex(loc['color'])),axis=2)
        values=world[island_mask]
        # Reefhook and Lantern Cay are low islands; neither claims a mountain
        # district. Keep a real relief floor without requiring a volcanic peak.
        minimum=4 if island['id'] in {'reefhook','lantern_cay'} else (12 if island['id']=='cindermaw' else 7)
        assert values.max()>=minimum,(island['id'],'missing island mountain spine',float(values.max()))
        assert np.mean(values<1.5)>.06,(island['id'],'no coastal lowlands')
    # Native heightfield values are shown in true world units. This is an
    # offline diagnostic, not a claim that the engine rendered this result.
    gy,gx=np.gradient(world)
    shade=np.clip((.8-.8*gx-.6*gy)/np.sqrt(1+gx*gx+gy*gy),.25,1.0)
    low=np.array([111,118,79]);high=np.array([172,161,144])
    blend=np.clip(world/18,0,1)[...,None]
    colors=(low*(1-blend)+high*blend)*shade[...,None]
    rgb=np.clip(colors,0,255).astype(np.uint8);rgb[~land]=[20,40,56]
    preview=Image.fromarray(rgb).resize((1080,round(rgb.shape[0]*1080/rgb.shape[1])),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(1120,preview.height+100),'#101c25');canvas.paste(preview,(20,80))
    draw=ImageDraw.Draw(canvas)
    font_path=Path('C:/Windows/Fonts/segoeui.ttf')
    heading=ImageFont.truetype(str(font_path),25) if font_path.exists() else ImageFont.load_default()
    small=ImageFont.truetype(str(font_path),16) if font_path.exists() else ImageFont.load_default()
    draw.text((20,12),'ASHBORN ISLES '+cfg['version']+' / DECODED TERRAIN DECAL',font=heading,fill='#edba5d')
    draw.text((20,47),'Offline heightfield preview; native vertical scale. In-game appearance still requires verification.',font=small,fill='#d4ddd9')
    canvas.save(reports/'Goblins_Decal_Relief.png')
    return metrics


def verify_center_continuity(cfg):
    """Reject the angular shoreline function being reused as interior height.

    Probe a tiny ring around each island's origin: the old formula jumped
    hundreds of uint16 units even as radius approached zero. Two units
    allow 16-bit quantization without accepting a directional discontinuity.
    """
    import archipelago
    angles=np.linspace(0,2*np.pi,32,endpoint=False)
    jumps={}
    for island in cfg['islands']:
        x=island['center'][0]-cfg['center'][0]+.0001*np.cos(angles)
        y=island['center'][1]-cfg['center'][1]+.0001*np.sin(angles)
        values=archipelago.heights(cfg,x,y).astype(int)
        jumps[island['id']]=int(np.ptp(values))
        assert jumps[island['id']]<=2,(island['id'],'radial height singularity',jumps[island['id']])
    return jumps
