"""Render curated dependency panels and the complete result index from JSON."""
from pathlib import Path
import json,re,math,html
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'theorem_graph/theorems.json').read_text())
N={n['id']:n for n in D['nodes']}
EDGES={(e['source'],e['target']) for e in D['edges']}
W,H=landscape(A4);c=canvas.Canvas(str(R/'7_theorem_graph.pdf'),pagesize=(W,H))
c.setTitle('Abelian sixfolds: theorem dependency atlas')
INK=colors.HexColor('#17394A');MUTED=colors.HexColor('#526574');RED=colors.HexColor('#A33A2B');GREEN=colors.HexColor('#16803C');PALE=colors.HexColor('#F0F4F6')
styles={k:ParagraphStyle(k,fontName='Helvetica',fontSize=s,leading=l,textColor=INK) for k,s,l in [('small',8,10.5),('body',10,14),('tiny',7,9)]}
page_no=0
def para(text,x,y,w,style='small'):
 p=Paragraph(text,styles[style]);_,h=p.wrap(w,1000);p.drawOn(c,x,y-h);return h
def page(title,subtitle):
 global page_no
 page_no+=1;c.setFillColor(INK);c.setFont('Helvetica-Bold',22);c.drawString(35,H-43,title)
 para(subtitle,35,H-58,W-70,'body')
 c.setStrokeColor(colors.HexColor('#D8E1E6'));c.line(35,35,W-35,35)
 c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(35,22,'Theorem graph / 11 October 2026 / dependency -> dependent / curated routes, not formal certification')
 c.drawRightString(W-35,22,str(page_no))
def node_color(nid):
 n=N[nid]
 if n.get('status','').startswith('withdrawn'):return RED
 if n.get('curated_transitive_conditional_inputs'):return colors.HexColor('#8A5B22')
 return INK
def panel(positions,labels=None,width=168,height=48):
 labels=labels or {}
 visible={(a,b) for a,b in EDGES if a in positions and b in positions}
 def alternate_path(src,dst):
  todo=[b for a,b in visible if a==src and b!=dst];seen=set()
  while todo:
   v=todo.pop()
   if v==dst:return True
   if v in seen:continue
   seen.add(v);todo.extend(b for a,b in visible if a==v)
  return False
 # Each visual arrow is an actual curated edge in the JSON. Off-panel edges are omitted.
 for src,dst in sorted(EDGES):
  if src not in positions or dst not in positions:continue
  if alternate_path(src,dst):continue
  x,y=positions[src];a,b=positions[dst];dx=a-x;dy=b-y
  if abs(dx)>abs(dy):
   start=(x+math.copysign(width/2,dx),y);end=(a-math.copysign(width/2,dx),b)
  else:start=(x,y+math.copysign(height/2,dy));end=(a,b-math.copysign(height/2,dy))
  points=[start,end]
  if abs(dx)<1 and any(n not in [src,dst] and abs(v[0]-x)<width and min(y,b)<v[1]<max(y,b) for n,v in positions.items()):
   side=1 if x+width/2+18<W-20 else -1;road=x+side*(width/2+18)
   points=[(x+side*width/2,y),(road,y),(road,b),(a+side*width/2,b)]
  elif abs(dy)<1 and any(n not in [src,dst] and abs(v[1]-y)<height and min(x,a)<v[0]<max(x,a) for n,v in positions.items()):
   road=y-height/2-18;points=[(x,y-height/2),(x,road),(a,road),(a,b-height/2)]
  c.setStrokeColor(colors.HexColor('#AAB8C1'));c.setLineWidth(.8)
  for p0,p1 in zip(points,points[1:]):c.line(*p0,*p1)
  start,end=points[-2:]
  angle=math.atan2(end[1]-start[1],end[0]-start[0]);p=c.beginPath();p.moveTo(*end)
  for d in [-.48,.48]:p.lineTo(end[0]-6*math.cos(angle+d),end[1]-6*math.sin(angle+d))
  p.close();c.setFillColor(colors.HexColor('#8798A3'));c.drawPath(p,fill=1,stroke=0)
 for nid,(x,y) in positions.items():
  color=node_color(nid);c.setFillColor(colors.white);c.setStrokeColor(color);c.setLineWidth(1.1)
  c.roundRect(x-width/2,y-height/2,width,height,6,fill=1,stroke=1)
  c.setFillColor(color);c.setFont('Helvetica-Bold',8.3);c.drawCentredString(x,y+8,nid)
  text=labels.get(nid,N[nid].get('title') or N[nid].get('title_latex',''))
  text=re.sub(r'\\[A-Za-z]+|[{}$]','',text)
  para(html.escape(text),x-width/2+8,y+1,width-16,'tiny')
def note(text,y=85):para(text,35,y,W-70,'small')

page('Dependency atlas','A visual atlas generated from the companion JSON, with exact source locations and external-input status.')
counts={k:sum(n['kind']==k for n in D['nodes']) for k in ['case_contract','external_input']}
para(f'<b>{len(D["nodes"])} nodes / {len(D["edges"])} curated logical edges / {len(D["reference_edges"])} indexed references.</b> The 21 case contracts use stable S/N IDs. All numbered statements retain their original labels or receive result:&lt;number&gt; IDs.',35,H-110,W-70,'body')
cols=[(35,'01 / Original', '1_paper.pdf<br/>Complete human-readable narrative.<br/>latex/paper.tex: frozen source snapshot.'),
 (295,'02 / AI edition','2_AI_paper.pdf<br/>Four takeaway pages, then full proof text.<br/>Original theorem numbers preserved.'),
 (555,'03 / JSON','theorem_graph/theorems.json<br/>LaTeX statements, source lines, PDF pages,<br/>logical dependencies and external status.')]
for x,title,text in cols:
 c.setFillColor(PALE);c.roundRect(x,285,245,145,8,fill=1,stroke=0)
 para('<b>'+title+'</b>',x+14,412,217,'body');para(text,x+14,380,217,'body')
para('<b>How to read the graph</b><br/>Arrows run from a prerequisite to a dependent. Each panel is a selected subgraph of the same JSON; omitted arrows are not evidence of independence. Red borders mark withdrawn external assertions. Ochre borders mark conclusions whose curated route uses a conditional input. Blue marks the other indexed routes, including cited geometric theorems that are not reproved here.',35,251,W-70,'body')
para('<b>Two different edge sets</b><br/>Curated logical edges describe sufficient central proof routes. Reference edges only record explicit LaTeX references; they can be forward pointers, examples or alternative routes. They are not automatically promoted to proof dependencies. Uncurated results are explicitly marked references_indexed_only.',35,156,W-70,'body')
c.showPage()

page('Polarization and CM routes','The key S9 and S11 constructions use the cited split sixfold theorem, not the withdrawn eightfold/KS/Aux assertions.')
pos={'EXT:Markman6':(130,470),'p:markman':(130,350),'p:oddscale':(365,425),'N1':(690,465),'N4':(690,390),
 'p:quartic-scale':(365,315),'S9':(690,315),'p:CMsplit':(130,210),'p:CMrankfive':(365,210),
 'p:CMsixrank':(365,105),'p:CMcomplete':(600,170),'S11':(745,105)}
panel(pos,{'p:oddscale':'Positive scaling on an odd-rank factor','p:quartic-scale':'Positive real-quadratic correction','p:CMsplit':'Inverse-derivative trace polarization','p:CMrankfive':'Rank five or six: invariant generators','p:CMsixrank':'Exclude rank four via plane relations','p:CMcomplete':'All simple CM sixfolds; all powers','EXT:Markman6':'Split Weil sixfolds: discriminant -1'},width=168,height=48)
note('N4 also uses the actual Hodge-circle test; S9 also uses determinant invariants. Only their polarization branch is shown. The S11 rank bound does not itself prove cycle algebraicity.',67)
c.showPage()

page('Stabilization and unitary generators','The eightfold assertion is used only as a conditional geometric input. The contraction back to the sixfold is an explicit algebraic operation.')
pos={'EXT:Weil8':(140,430),'p:hyperbolic-test':(140,300),'p:all-sixfold-weil':(400,370),
 't:S7structure':(400,220),'t:S7complete':(670,220),'t:S8':(670,345),
 'p:polarization':(400,470),'p:coupled-det':(400,115),'S7':(670,115),'S8':(670,450),'S10':(140,115)}
panel(pos,{'EXT:Weil8':'Withdrawn assertion; assumed only','p:hyperbolic-test':'Rational Hermitian hyperbolicity','p:all-sixfold-weil':'Stabilize, then contract by a divisor','t:S7structure':'Seven-dimensional volume contribution','t:S7complete':'Quaternionic sum-map generation','t:S8':'Full U / special U dichotomy','p:polarization':'Weil generators on powers','p:coupled-det':'Coupled determinant invariants'},width=176)
note('The general-linear branches need no Weil algebraicity. Split subfamilies can use Markman directly. The complete S7, S8 and S10 routes shown in the case contracts use EXT:Weil8.',67)
c.showPage()

page('Residual mixed-cycle routes','N2 and N3 have a common invariant model, but their geometric inputs and constructions differ. A CM transfer is not a consequence of KS alone.')
pos={'EXT:Aux':(125,470),'EXT:CM':(125,360),'p:N2auxiliary':(365,425),'N2':(700,450),
 'p:quartic-mixed':(125,230),'p:mixed-allpowers':(365,250),
 'EXT:KS':(125,110),'p:N3spin-descent':(365,110),'p:N3KS':(605,180),'N3':(735,85),
 'p:N3onecycle':(605,315),'p:N3residual':(605,405)}
panel(pos,{'EXT:Aux':'Withdrawn four-slot assertion; assumed','EXT:CM':'Unverified CM assertion; assumed','EXT:KS':'Withdrawn specified map; assumed','p:N2auxiliary':'Complementary periods, spin block, CM transfer','p:quartic-mixed':'Four-dimensional mixed space Q','p:mixed-allpowers':'Tensor slots and polarization contractions','p:N3spin-descent':'Square character, then rational descent','p:N3KS':'Full Clifford factors and matrix extraction','p:N3onecycle':'Rank one over a quartic field','p:N3residual':'Actual joint group and generators'},width=174)
note('The full N2/N3 case contracts also include independent, repeated-factor and CM strata. Their full-row conclusion is sixfold algebraicity; the displayed residual models additionally have all-powers results.',62)
c.showPage()

page('Cover geometry and specialization','These routes treat the represented geometric families and marked one-dimensional PEL components; they do not establish arbitrary rational Hermitian types.')
pos={'p:lowdim':(125,435),'p:cyclic-transfer':(365,435),'p:weighted-families':(690,435),
 'EXT:MilneCMproducts':(125,285),'p:fermat18':(365,285),'p:S10cyclic18':(690,285),
 'p:curve-specialization':(125,140),'p:mixed-allpowers':(365,140),'p:PELcompletion':(690,140)}
panel(pos,{'p:lowdim':'Products of surface/elliptic factors','p:cyclic-transfer':'Fermat domination + algebraic retraction','p:weighted-families':'Weighted quartic-cover families','EXT:MilneCMproducts':'Cited CM threefold / elliptic theorem','p:fermat18':'Fermat-eighteen Jacobian powers','p:S10cyclic18':'Nonsplit sextic-center family','p:curve-specialization':'Only a fixed (p,p) subvariation','p:mixed-allpowers':'Residual invariant-generation mechanism','p:PELcompletion':'Complete the same marked PEL component'},width=178)
note('For specialization, only classes in the fixed subvariation are transported. New Hodge classes appearing solely at special fibers are not covered by that statement. Not all classical prerequisites are drawn.',67)
c.showPage()

# Complete case ledger, including all 21 IDs and exact scope contracts.
cases=[x for x in D['nodes'] if x['kind']=='case_contract']
for start in [0,11]:
 page('The 21 case contracts',f'Rows {start+1}-{min(start+11,21)}. A star marks a whole-row route using a new conditional input; it does not mark every stratum.')
 y=H-110
 for n in cases[start:start+11]:
  ext=n['curated_transitive_conditional_inputs'];star=' *' if ext else ''
  para('<b>'+n['id']+star+'</b>',35,y,55)
  para(html.escape(n['title']),95,y,120)
  para(html.escape(n['strategy']),220,y,405)
  scope='all powers' if n['powers_scope']=='all_powers' else ('sixfold + residual powers' if 'residual' in n['powers_scope'] else 'sixfold as stated')
  para(scope,635,y,175)
  y-=32
 note('Conditional input ledger: S7/S8/S10 -> Weil8; N2 -> Aux + CM; N3 -> KS + CM. Sixfold-only labels are conservative records of the stated full-row scope, not counterexamples to all-powers extensions.',75)
 c.showPage()

# Full theorem/lemma/proposition index, including supporting examples and remarks.
items=[n for n in D['nodes'] if n['kind'] not in ['case_contract','external_input']]
for start in range(0,len(items),23):
 page('Complete statement index',f'Original result numbers and stable JSON IDs / entries {start+1}-{min(start+23,len(items))} of {len(items)}. O = original PDF page; A = AI PDF page.')
 y=H-108
 for n in items[start:start+23]:
  a=n['source'];loc=f'O {a.get("original_pdf_page") or "-"} / A {a.get("ai_pdf_page") or "-"}'
  para(html.escape(n['number']+' '+n['kind'].replace('pre','')),35,y,115,'tiny')
  para(html.escape(n['id']),155,y,245,'tiny')
  para(html.escape(n['title_latex']),405,y,285,'tiny')
  para(loc,700,y,100,'tiny');y-=18
 note('JSON preserves the full LaTeX statement, including assumptions, and one-based statement/proof source lines. references_indexed_only means no claim of a complete audited logical dependency list for that individual statement.',64)
 c.showPage()
c.save()
print('Graph PDF rendered:',page_no,'pages')
