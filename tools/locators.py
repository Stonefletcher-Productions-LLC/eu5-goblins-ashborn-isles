"""Append native map anchors; choose actual interior pixels, not unverified seeds."""
import re
import numpy as np

def build_locators(b,game,out,labels,seawater,sea_labels,box,height,ports):
    anchors={};sets={k:[] for k in ['city','unit_stack','combat','vfx','dock']}
    def entry(name,x,y):
        return f'{{ id={name} position={{ {x:.3f} 0 {b.H-y:.3f} }} rotation={{ 0 0 0 1 }} scale={{ 1 1 1 }} }}'
    for i,loc in enumerate(b.CFG['locations']):
        mask=labels==i;inner=mask.copy()
        for _ in range(4):
            inner=inner&np.roll(inner,1,0)&np.roll(inner,-1,0)&np.roll(inner,1,1)&np.roll(inner,-1,1)
        assert inner.any(),loc['id']+' has no interior anchor'
        ys,xs=np.where(inner)
        gy,gx=np.gradient(height.astype(float))
        score=(gx[ys,xs]**2+gy[ys,xs]**2)*.02+height[ys,xs]*.15+(xs+box[0]-loc['point'][0])**2+(ys+box[1]-loc['point'][1])**2
        j=int(score.argmin());x=float(xs[j]+box[0]+.5);y=float(ys[j]+box[1]+.5)
        anchors[loc['id']]={'x':x,'png_y':y,'height':int(height[ys[j],xs[j]])}
        for kind in ['city','unit_stack','combat','vfx']:sets[kind].append(entry(loc['id'],x,y))
    for zi,zone in enumerate(b.CFG['coastal_sea']['zones']):
        ys,xs=np.where(seawater&(sea_labels==zi));mx=np.median(xs);my=np.median(ys)
        j=int(((xs-mx)**2+(ys-my)**2).argmin())
        for kind in ['unit_stack','combat','vfx']:sets[kind].append(entry(zone['id'],xs[j]+box[0]+.5,ys[j]+box[1]+.5))
    for port in ports:sets['dock'].append(entry(port['land'],port['x']+.5,port['png_y']+.5))
    for kind,rows in sets.items():
        rel=f'in_game/gfx/map/map_objects/generated_map_object_locators_{kind}.txt'
        text=b.read(game,rel)
        for name,(x,y) in native_water_anchors(b,game,out,box,text).items():
            text=re.sub(r'(id='+name+r'\s*\n\s*position=\{ )[-\d.]+ ([-\d.]+) [-\d.]+( \})',
                        lambda m:f'{m[1]}{x:.6f} {m[2]} {b.H-y:.6f}{m[3]}',text)
        b.write(out,rel,b.inject(text,'instances','\n'.join(rows)))
    return anchors

def native_water_anchors(b,game,out,box,vanilla):
    """Native sea zones trimmed for the islands keep their vanilla anchors, which
    can now lie outside the zone (EU5 logs "Map object locator too far outside of
    its province's bounding box"). Move each such anchor to the pixel of the
    remaining zone nearest its median; returns {zone id: (x, png_y)}."""
    pad=400
    region=(box[0]-pad,box[1]-pad,box[2]+pad,box[3]+pad)
    from PIL import Image
    Image.MAX_IMAGE_PIXELS=None
    image=Image.open(out/'in_game/map_data/locations.png').convert('RGB')
    pixels=np.array(image.crop(region))
    names=b.parse_names(game)
    templates=b.read(game,'in_game/map_data/location_templates.txt')
    top=dict(re.findall(r'(?m)^\s*(\w+)\s*=\s*\{[^\n]*?topography\s*=\s*(\w+)',templates))
    full=None
    moved={}
    for m in re.finditer(r'id=(\w+)\s*\n\s*position=\{ ([-\d.]+) [-\d.]+ ([-\d.]+) \}',vanilla):
        name,x,y=m[1],float(m[2]),b.H-float(m[3])
        # Only anchors in or near the repainted rectangle can have lost their zone.
        if name not in names or top.get(name) not in b.WATER|{'ocean_wasteland'}: continue
        if not (region[0]<=x<region[2] and region[1]<=y<region[3]): continue
        color=names[name]
        if image.getpixel((int(x),int(y)))==color: continue
        ys,xs=np.where(np.all(pixels==color,axis=2));x0,y0=region[0],region[1]
        if not len(xs):
            # The zone now lies wholly outside the nearby region.
            if full is None: full=np.array(image)
            ys,xs=np.where(np.all(full==color,axis=2));x0,y0=0,0
        assert len(xs),(name,'water zone has no pixels left')
        j=int(((xs-np.median(xs))**2+(ys-np.median(ys))**2).argmin())
        moved[name]=(float(xs[j]+x0+.5),float(ys[j]+y0+.5))
    return moved
