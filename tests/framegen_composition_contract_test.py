"""CPU contract for the conservative MetalFX composition influence patch.
Not a Metal shader/device test. Generated frames intentionally reuse current
composite pixels where nonlinear weapon/HUD influence exists.
"""
import math

def layer(clean,full,w,h):
    result=[]
    for y in range(h):
        for x in range(w):
            changed=False
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    q=max(0,min(h-1,y+dy))*w+max(0,min(w-1,x+dx))
                    a,b=clean[q],full[q]
                    changed |= a!=b or not all(map(math.isfinite,a+b))
            result.append((*full[y*w+x],1.) if changed else (0.,0.,0.,0.))
    return result

def main():
    clean=[(.2,.3,.4)]*25;full=clean.copy();full[12]=(.8,.5,.2)
    ui=layer(clean,full,5,5)
    assert sum(p[3] for p in ui)==9
    # The real scene reconstructed through this opaque influence layer is exact,
    # unlike separately tone-mapping a translucent weapon.
    assert [tuple(p[c]+clean[i][c]*(1-p[3]) for c in range(3)) for i,p in enumerate(ui)]==full
    assert all(p[3]==0 for p in layer(clean,clean,5,5))
    full=clean.copy();full[0]=(.1,.2,.3)
    assert sum(p[3] for p in layer(clean,full,5,5))==4
    tonemap=lambda v:v/(1+v)
    assert tonemap(.5*2+.5*8)!=.5*tonemap(2)+.5*tonemap(8)
    print('Influence composition identity/dilation contract passed (CPU only)')
if __name__=='__main__':main()
