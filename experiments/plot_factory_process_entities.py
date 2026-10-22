"""Code-grounded experimental environment figure; run from any directory.

The six-step route is a process sequence. Panel c is a grouped, undirected
view of factory_bn/graph.py, NOT a causal graph or physical dispatch map.
The screenshot is clipped by the plotting viewport; the source is unchanged.
"""
from pathlib import Path
import importlib.util
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / '_isaac_factory/source/isaaclab_tasks/isaaclab_tasks/direct/hc_factory'
OUT = ROOT / 'figures'
C = dict(red='#CB001C', orange='#F26121', gold='#FCB84D', cream='#FFF2C7',
         cyan='#A6DCED', blue='#5BA7D9', navy='#3D6EB4', ink='#243D50', gray='#647888')
plt.rcParams.update({'font.family':'Arial', 'font.size':11, 'svg.fonttype':'none',
                     'pdf.fonttype':42, 'savefig.facecolor':'white'})

def text(ax,x,y,s,size=11,weight='normal',ha='center',color=None,**kw):
    return ax.text(x,y,s,fontsize=size,fontweight=weight,ha=ha,va='center',
                   color=color or C['ink'],**kw)

def box(ax,x,y,w,h,label='',fc='white',size=11,ec='none',weight='normal'):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.012',
                              facecolor=fc,edgecolor=ec,linewidth=1.1,zorder=2))
    if label: text(ax,x+w/2,y+h/2,label,size,weight,zorder=3)

def edge(ax,a,b,color=None,arrow=False,style='-',lw=1.5,rad=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>' if arrow else '-',
        mutation_scale=11,linewidth=lw,color=color or C['navy'],linestyle=style,
        connectionstyle=f'arc3,rad={rad}',zorder=1,shrinkA=1,shrinkB=1))

def panel(fig,rect,title,shade):
    ax=fig.add_axes(rect); ax.set(xlim=(0,1),ylim=(0,1)); ax.axis('off')
    ax.add_patch(Rectangle((0,0.91),1,.09,facecolor=shade,edgecolor='none'))
    text(ax,.015,.956,title,13,'bold','left')
    return ax

def main():
    # Import only the lightweight graph module, without importing Isaac Sim.
    spec=importlib.util.spec_from_file_location('factory_graph',SRC/'PDFormer/factory_bn/graph.py')
    graph=importlib.util.module_from_spec(spec); spec.loader.exec_module(graph)
    assert len(graph.PROCESS_CHAIN)==7
    fig=plt.figure(figsize=(11,12.2),facecolor='white')
    a=panel(fig,[.035,.645,.93,.325],'(a)  Digital-twin production environment', '#EAF4FA')
    photo=fig.add_axes([.035,.665,.615,.268])
    im=Image.open(ROOT/'figures/camera_views/env_screen_shot.png')
    photo.imshow(im); photo.set_xlim(0,im.width*.475)
    photo.set_ylim(im.height*.96,im.height*.18); photo.axis('off')
    # Locations refer to visible equipment, not workstation coordinates in the simulator.
    pins=[(.265,.65,'1'),(.388,.65,'2'),(.255,.365,'3 / 6'),(.423,.31,'4'),(.10,.65,'5')]
    for x,y,label in pins:
        photo.annotate(label,(x*im.width,y*im.height),xytext=(0,22),textcoords='offset points',
          ha='center',va='center',fontsize=11,fontweight='bold',color='white',
          bbox=dict(boxstyle='round,pad=.28',fc=C['navy'],ec='none'),
          arrowprops=dict(arrowstyle='-',color=C['navy'],lw=1.6))
    labels=[('1','CNC pipe cutting'),('2','Pipe grooving'),('3 / 6','Shared workbenches'),
            ('4','Robotic root welding'),('5','Rotary surface welding')]
    for i,(num,label) in enumerate(labels):
        y=.815-i*.116
        box(a,.69,y-.032,.068,.066,num,C['cyan'],10,weight='bold')
        text(a,.775,y,label,10.8,ha='left')
    text(a,.69,.19,'Overhead gantries • transport robots\nWorkers • storage / buffers',10,ha='left',linespacing=1.7)
    text(a,.69,.045,'Left-side detail of the full scene',9,ha='left',color=C['gray'])

    b=panel(fig,[.035,.365,.93,.265],'(b)  Six-step manufacturing route and handling dependencies', '#FFF2C7')
    names=['Pipe\ncutting','Pipe\ngrooving','Assembly &\nspot welding','Argon-arc\nroot welding','MIG surface\nwelding','Rust-proof\npainting']
    devices=['Cutting machine','Grooving machine','Workbench','Welding robot','Rotary welder','Workbench']
    xs=[.012+i*.165 for i in range(6)]
    for i,x in enumerate(xs):
        box(b,x,.49,.135,.26,fc='#EAF4FA' if i not in (2,5) else C['cream'])
        text(b,x+.0675,.715,f'{i+1:02}',11,'bold',color=C['navy'])
        text(b,x+.0675,.61,names[i],11,'bold')
        text(b,x+.0675,.505,devices[i],8.7)
        if i<5: edge(b,(x+.144,.61),(xs[i+1]-.009,.61),arrow=True)
    text(b,.012,.835,'Raw pipe',10,ha='left')
    text(b,.418,.835,'Pipe + flange + elbow',10)
    edge(b,(.418,.805),(.418,.755),C['orange'],True)
    text(b,.988,.835,'Finished water pipe',10,ha='right')
    text(b,.5,.405,'Steps 3 and 6 reuse the workbench resource family.',10,color=C['gray'])
    box(b,.012,.08,.976,.245,fc='#F4F8FB')
    text(b,.029,.265,'Material transfer between processing steps',11,'bold','left')
    text(b,.029,.185,'Same zone:  worker-assisted gantry transfer',10.5,ha='left')
    text(b,.029,.108,'Cross zone:  source gantry → transport robot → destination gantry',10.5,ha='left')

    c=panel(fig,[.035,.035,.93,.315],'(c)  Multi-entity structural dependencies used by the model', '#EAF4FA')
    # Agent-to-machine edges are bundled at the machine group boundary.
    groups=[(.025,'Gantries × 4',C['gold']),(.355,'Transport robots × 4',C['cyan']),(.685,'Workers × 5',C['cream'])]
    for x,label,color in groups:
        box(c,x,.735,.29,.105,label,color,11.5,weight='bold')
        edge(c,(x+.145,.735),(x+.145,.625),C['gray'],style='--')
    text(c,.5,.675,'Each worker / gantry / transport robot is connected to all seven stations',9.5,
         bbox=dict(facecolor='white',edgecolor='none',pad=2),zorder=5)
    box(c,.015,.395,.97,.23,fc='#F2F7FB',ec='#D2E3EF')
    c.patches[-1].set_zorder(0)
    text(c,.03,.595,'Machines / workstations × 7',10.5,'bold','left')
    short=['Cutting','Grooving','Bench 0','Bench 1','Root weld','Rotary 0','Rotary 1']
    mx=[.032+i*.137 for i in range(7)]
    for i,x in enumerate(mx):
        box(c,x,.435,.10,.10,short[i],C['blue'],9.5,weight='bold')
        if i<6: edge(c,(x+.109,.485),(mx[i+1]-.009,.485))
    for x,w,label,targets in [(.025,.27,'BlackStorage\nCutting · grooving',[0,1]),
                              (.365,.27,'GroundStorage\nCutting · grooving · Bench 0',[0,1,2]),
                              (.705,.27,'YellowStorage\nBenches · root / rotary welding',[2,3,4,5,6])]:
        box(c,x,.135,w,.135,label,'#FFF2C7',9.8)
        edge(c,(x+w/2,.27),(x+w/2,.395),C['gold'],lw=2)
    text(c,.5,.335,'18 buffer nodes, grouped by the affinity rules in the implementation',10,
         bbox=dict(facecolor='white',edgecolor='none',pad=2),zorder=5)
    text(c,.015,.065,'Solid: station / buffer relations     Dashed: bundled agent–station relations',9.5,ha='left')
    text(c,.015,.012,'Undirected, grouped view; within-type gantry / robot links and self-loops omitted.',9.2,ha='left',color=C['gray'])
    for ext in ['pdf','svg','png']:
        fig.savefig(OUT/f'fig_factory_process_entities.{ext}',dpi=300)
    plt.close(fig)
    print('Saved figures/fig_factory_process_entities.{pdf,svg,png}')

if __name__=='__main__': main()
