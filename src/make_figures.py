"""Three original finite-panel figures, with every plotted value retained."""
import csv,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from config import ROOT
from accounting import write_csv

def read(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#243447','axes.labelcolor':'#243447','pdf.fonttype':42,'svg.hashsalt':'road-denominators-v1'})
    plot=[]
    def save(fig,name):
        fig.savefig(ROOT/f'figures/{name}.png',dpi=180,bbox_inches='tight');fig.savefig(ROOT/f'figures/{name}.pdf',bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None});fig.savefig(ROOT/f'figures/{name}.svg',bbox_inches='tight',metadata={'Date':None});shutil.copy2(ROOT/f'figures/{name}.pdf',ROOT/f'paper/images/{name}.pdf');plt.close(fig)
    ranks=read('results/evaluation/exact_ranks.csv');lookup={(r['state'],r['denominator']):r for r in ranks};states=sorted({r['state'] for r in ranks});x=[float(lookup[s,'population']['midrank']) for s in states];y=[float(lookup[s,'vmt_millions']['midrank']) for s in states]
    fig,ax=plt.subplots(figsize=(7.6,6.3));ax.plot([1,51],[1,51],color='#aab5bf',ls='--',lw=1,label='Same ordering');ax.scatter(x,y,color='#006b72',s=32,alpha=.9,zorder=3)
    selected=sorted(states,key=lambda s:(-abs(float(lookup[s,'population']['midrank'])-float(lookup[s,'vmt_millions']['midrank'])),s))[:5]
    offsets={'District of Columbia':(-12,16),'Washington':(-80,-17),'Alabama':(10,10),'Oregon':(9,0),'Indiana':(9,7)}
    # Fixed largest-five annotation rule; offsets affect only label placement.
    for s in selected:
        px=float(lookup[s,'population']['midrank']);py=float(lookup[s,'vmt_millions']['midrank']);ax.annotate('DC' if s=='District of Columbia' else s,(px,py),xytext=offsets.get(s,(8,8)),textcoords='offset points',fontsize=9,arrowprops={'arrowstyle':'-','color':'#697784','lw':.6})
    ax.set_xlim(0,53);ax.set_ylim(0,53);ax.set_xticks([1,10,20,30,40,50]);ax.set_yticks([1,10,20,30,40,50]);ax.set_xlabel('Rank of fatalities per 100,000 population');ax.set_ylabel('Rank of fatalities per 100 million vehicle miles');ax.set_title('2023: denominator choice changes state ordering',loc='left',fontweight='bold');ax.text(.02,.97,'Rank 1 = higher recorded fatality intensity',transform=ax.transAxes,va='top',fontsize=9);ax.grid(color='#e2e7eb',lw=.7);ax.set_axisbelow(True);ax.legend(frameon=False,loc='lower right');fig.tight_layout();save(fig,'rank-scatter')
    for s,px,py in zip(states,x,y):
        for series,value in [('population_midrank',px),('vmt_midrank',py)]:plot.append({'figure':'rank-scatter','year':2023,'group':'all','denominator_a':'population','denominator_b':'vmt_millions','state':s,'series':series,'value':value})
    exact=[r for phase in ['development','evaluation'] for r in read(f'results/{phase}/exact_summary.csv')];pairs=[('population','licensed_drivers'),('population','vmt_millions'),('licensed_drivers','vmt_millions')];labels=['Population / licensed drivers','Population / vehicle miles','Licensed drivers / vehicle miles'];colors=['#835aa0','#006b72','#b84a18']
    fig,ax=plt.subplots(figsize=(9.4,4.6));base=np.arange(3);width=.24
    for index,(pair,label,color) in enumerate(zip(pairs,labels,colors)):
        rows=[next(r for r in exact if r['year']==str(y) and (r['denominator_a'],r['denominator_b'])==pair) for y in [2019,2021,2023]];vals=[int(r['reversal']) for r in rows];bars=ax.bar(base+(index-1)*width,vals,width,color=color,label=label);ax.bar_label(bars,padding=3,fontsize=9)
        plot.extend({'figure':'exact-reversals','year':r['year'],'group':'all','denominator_a':pair[0],'denominator_b':pair[1],'state':'','series':'strict_reversals','value':r['reversal']} for r in rows)
    ax.set_xticks(base,['2019 report','2021 report','2023 report']);ax.set_ylabel('Strict reversed state pairs (of 1,275)');ax.set_ylim(0,270);ax.set_title('Reversals persist in each separate report-year snapshot',loc='left',fontweight='bold');ax.grid(axis='y',color='#e2e7eb',lw=.7);ax.set_axisbelow(True);ax.legend(frameon=False,loc='upper left',fontsize=9);fig.tight_layout();save(fig,'exact-reversals')
    bounded=[r for phase in ['development','evaluation'] for r in read(f'results/{phase}/bounded_summary.csv') if r['denominator_a']=='population' and r['denominator_b']=='vmt_millions' and r['group']!='all'];fig,axes=plt.subplots(1,3,figsize=(11,4.8),sharey=True);categories=['guaranteed_same','guaranteed_reversal','unresolved'];colors=['#006b72','#b84a18','#dce2e7'];names=['Same order guaranteed','Reversal guaranteed','Unresolved by ranges']
    for ax,group,title in zip(axes,['motorcyclists','pedestrians','pedalcyclists'],['Motorcyclists','Pedestrians','Pedalcyclists']):
        rows=[next(r for r in bounded if r['year']==str(y) and r['group']==group) for y in [2019,2021,2023]];bottom=np.zeros(3)
        for category,color,label in zip(categories,colors,names):
            vals=[int(r[category]) for r in rows];ax.bar(np.arange(3),vals,bottom=bottom,color=color,label=label,width=.64);bottom+=vals
            plot.extend({'figure':'rounded-share-information','year':r['year'],'group':group,'denominator_a':'population','denominator_b':'vmt_millions','state':'','series':category,'value':r[category]} for r in rows)
        ax.set_xticks([0,1,2],['2019','2021','2023']);ax.set_ylim(0,1275);ax.set_yticks([0,255,510,765,1020,1275]);ax.set_title(title,loc='left',fontweight='bold');ax.set_xlabel('Report year');ax.grid(axis='y',color='#e2e7eb',lw=.7);ax.set_axisbelow(True)

        ax.tick_params(labelsize=12);ax.xaxis.label.set_size(12);ax.title.set_size(13)
    axes[0].set_ylabel('State pairs (of 1,275)',fontsize=12);handles,labs=axes[0].get_legend_handles_labels();fig.legend(handles,labs,loc='lower center',ncol=3,frameon=False,fontsize=12);fig.suptitle('Whole-percent shares leave some denominator comparisons unresolved',x=.06,ha='left',fontweight='bold',fontsize=14);fig.text(.06,.90,'Population vs vehicle miles; 2023 is an explicit coarsening of available exact counts',fontsize=11);fig.tight_layout(rect=[0,.08,1,.88]);save(fig,'rounded-share-information')
    write_csv(ROOT/'figures/PLOT_DATA.csv',plot);print('Saved3figures and138plotted values.')

if __name__=='__main__':main()
