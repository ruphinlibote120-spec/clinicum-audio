#!/usr/bin/env python3
"""Prépare le texte parlé des fiches Clinicum (sigles, unités, symboles -> français oral).
Sortie : out/<id>.json (chapitres), out/manifest.json, out/unmapped.txt
"""
import json, re, hashlib, os, sys, collections, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lexique as LX

SJL = [('pts','Points clés'),('def','Définition'),('epi','Épidémiologie'),('cau','Causes et facteurs de risque'),
       ('phy','Physiopathologie'),('ana','Anatomopathologie'),('cli','Symptomatologie'),('dia','Diagnostic'),
       ('exp','Explorations'),('tt','Traitement'),('sui','Suivi et pronostic'),('pre','Prévention'),
       ('ref','Quand référer ou hospitaliser')]
SPOKEN = {'pts':'Les points clés.','def':'La définition.','epi':'L’épidémiologie.','cau':'Les causes et les facteurs de risque.',
 'phy':'La physiopathologie.','ana':'L’anatomopathologie.','cli':'La symptomatologie.','dia':'Le diagnostic.','exp':'Les explorations.',
 'tt':'Le traitement.','sui':'Le suivi et le pronostic.','pre':'La prévention.','ref':'Quand référer ou hospitaliser.'}
# Disciplines dites en phrase française (article + nom) pour que la voix les lise en français
SPEC = ["la cardiologie","la pneumologie","la gastro-entérologie et l'hépatologie","la néphrologie","l'endocrinologie et le métabolisme",
        "l'hématologie","l'infectiologie et les maladies tropicales","la neurologie","les urgences et la réanimation","la rhumatologie",
        "la dermatologie","la psychiatrie","la gynécologie et l'obstétrique","la pédiatrie","la toxicologie","la nutrition","l'oncologie",
        "l'oto-rhino-laryngologie","l'ophtalmologie","l'urologie et la chirurgie","la santé publique et la médecine légale",
        "la douleur, les soins palliatifs et la gériatrie"]
SJC = ["Cardiologie","Pneumologie","Gastro-entérologie et hépatologie","Néphrologie","Endocrinologie et métabolisme",
       "Hématologie","Infectiologie et maladies tropicales","Neurologie","Urgences et réanimation","Rhumatologie",
       "Dermatologie","Psychiatrie","Gynécologie-obstétrique","Pédiatrie","Toxicologie","Nutrition","Oncologie","ORL",
       "Ophtalmologie","Urologie et chirurgie","Santé publique et médecine légale","Douleur, soins palliatifs et gériatrie"]

LETTERS = {'A':'a','B':'bé','C':'cé','D':'dé','E':'eu','F':'effe','G':'gé','H':'ache','I':'i','J':'ji','K':'ka','L':'elle',
           'M':'emme','N':'enne','O':'o','P':'pé','Q':'ku','R':'erre','S':'esse','T':'té','U':'u','V':'vé','W':'double vé',
           'X':'ix','Y':'i grec','Z':'zède'}
DIG = {'0':'zéro','1':'un','2':'deux','3':'trois','4':'quatre','5':'cinq','6':'six','7':'sept','8':'huit','9':'neuf'}

# --- Lexique (prononciation écrite pour la voix) : à valider à l'oreille ---
LEX = {
 # mots lus comme des mots
 'SIDA':'sida','COVID':'covid','ELISA':'élisa','HELLP':'help','PrEP':'prép','PEP':'pép','WASH':'ouache','STEMI':'stémi',
 'KDIGO':'kédigo','GOLD':'gold','FAST':'faste','REACH':'ritche','SARS':'sarce','GABA':'gaba','NASH':'nache','TIPS':'tipse',
 'FIGO':'figo','NICE':'naïce','MUAC':'muak','ReSoMal':'ré so mal','HACEK':'assek','CPAP':'si pap','ECMO':'ecmo',
 'GeneXpert':'gène expert','FibroScan':'fibro scane','LoaScope':'loa scope','AMBITION':'ambicheune','HEARTS':'harts',
 'INVICTUS':'invictusse','WOMAN':'woman','CRASH':'crache','CROSS':'crosse','FOLFOX':'folfox','ABVD':'a b v d','CHOP':'tchop',
 'GLOBOCAN':'globocane','MOTIVE':'motive','ACTION':'acksione','WATERFALL':'waterfol','NECT':'nect','MenFive':'mène five',
 'McRoberts':'mac robertse','CATT':'catte','CANMAT':'canemate','DSM':'d s m','APRI':'apri','GINA':'djina','EASL':'e a s l',
 'ARNm':'a r n messager','PIDC':'p i d c','HIV':'v i h','TP53':'té pé cinquante-trois','ReSoMAL':'ré so mal',
 # mixtes / immunoglobulines / marqueurs
 'IgM':'i g emme','IgG':'i g gé','IgA':'i g a','IgE':'i g eu','IgIV':'i g i v','HbA1c':'hémoglobine glyquée','HbS':'hémoglobine s',
 'HbSS':'hémoglobine s s','HbSC':'hémoglobine s c','HbF':'hémoglobine f','HBsAg':'ag ache bé esse','CrAg':'antigène cryptococcique',
 'DNase':'dé nase','SpO2':'saturation en oxygène','PaO2':'pression artérielle en oxygène','FiO2':'fraction inspirée en oxygène',
 'O2':'oxygène','NaCl':'chlorure de sodium','HRP2':'h r p deux','CHA2DS2':'chade deux dèsse deux','VASc':'vasque',
 'CoV':'cov','HepB':'hépatite b','PlGF':'p l g f','T4L':'t quatre libre','NS1':'enne esse un','IS2404':'i s deux mille quatre cent quatre',
 'Ov16':'o v seize','LC16m8':'elle cé seize m huit','SGLT2':'esse gé elle té deux','ISGLT2':'i esse gé elle té deux',
 'R21':'r vingt et un','H1':'h un','C3':'c trois','C4':'c quatre','B1':'b un','B6':'b six','B12':'b douze','B19':'b dix-neuf',
 'B27':'b vingt-sept','E1':'e un','F1':'f un','L1':'l un','S1':'s un','D2':'d deux','G6PD':'gé six pé dé','CD4':'cé dé quatre',
 'CD20':'cé dé vingt','ARA2':'a r a deux','MEN2':'mène deux','NF1':'enne effe un','BRCA1':'bé erre cé a un','BCL6':'bé cé elle six',
 'RB1':'erre bé un','HER2':'her deux','MR':'emme erre','DT2':'dé té deux','T1':'t un','T2':'t deux','T3':'t trois','T4':'t quatre',
 'ABL1':'abeleun','BCR':'bé cé erre','NMDA':'enne emme dé a','MMSE':'emme emme esse eu','PHQ':'p ache ku',
 'RHZE':'erre ache zède eu','VRd':'v r d','CIN':'cé i enne','LEEP':'liip','LAL':'elle a elle',
 # unités/abréviations médicales fréquentes
 'IV':'i v','IM':'i m','SC':'sous-cutané','PO':'per os','OH':'alcool','UI':'unités internationales',
 'HTA':'h t a','AVC':'a v c','AINS':'a i n s','BPCO':'b p c o','TARV':'t a r v','ARV':'a r v','ACT':'a c t','SRO':'s r o',
 'OMS':'o m s','RDC':'r d c','VIH':'v i h','NFS':'n f s','IRM':'i r m','PCR':'p c r','ECG':'e c g','CRP':'c r p',
 'TSH':'t s h','TDR':'t d r','TDM':'t d m','VHB':'v h b','VHC':'v h c','TB':'t b','IEC':'i e c','INR':'i n r',
 'ALAT':'a l a t','ASAT':'a s a t','ECBU':'e c b u','LCR':'l c r','LDH':'l d h','DFG':'d f g','FEVG':'f e v g',
 'TARV ':'t a r v','OAP':'o a p','SDRA':'s d r a','CIVD':'c i v d','EEG':'e e g','EMG':'e m g','IMC':'i m c',
 'GCS':'g c s','PSA':'p s a','PTH':'p t h','BNP':'b n p','LAM':'l a m','CMV':'c m v','EBV':'e b v','HSV':'h s v',
 'HPV':'h p v','BCG':'b c g','PET':'p e t','TLD':'t l d','TEP':'t e p','CPK':'c p k','SARM':'sarm','BLSE':'b l s e',
 'RUTF':'r u t f','MAS':'m a s','MUI':'m u i','HPP':'h p p','TCA':'t c a','ACTH':'a c t h','TNF':'t n f','SNC':'s n c',
 'ESC':'e s c','AHA':'a h a','VRS':'v r s','CMI':'c m i','VZV':'v z v','IDSA':'i d s a','PAM':'p a m',
 'EAU':'e a u','AAP':'a a p','CPRE':'c p r e','JAK':'jak','ORL':'o r l','FVIII':'facteur huit','FIX':'facteur neuf',
 'EULAR':'eu lar','ASLO':'a s l o','GEU':'g e u','VDRL':'v d r l','RPM':'r p m','TSPT':'t s p t','HHV':'h h v',
 'FU':'f u','MSI':'m s i','COHb':'carboxyhémoglobine','HPLC':'h p l c','MTB':'m t b','RIF':'r i f','GLP':'g l p',
 'VHA':'v h a','VGM':'v g m','SIADH':'s i a d h','PL':'p l','MB':'m b','ICS':'i c s','TPO':'t p o','ACG':'a c g',
 'ISRS':'i s r s','PD':'p d','ASP':'a s p','VPI':'v p i','VPO':'v p o','DMPA':'d m p a','THM':'t h m','MICI':'m i c i',
 'NT':'n t','HGPO':'h g p o','EPI':'e p i','TT':'t t','LABA':'l a b a','VNI':'v n i','PFC':'p f c','QT':'q t',
 'ACR':'a c r','SGA':'s g a','VI':'v i','CATT':'catte','FISH':'fiche','LMC':'l m c','CAR':'car','ISS':'i s s',
 'BRCA':'bé erre cé a','RTS':'r t s','PTME':'p t m e','RR':'r r','PVVIH':'p v v i h','VG':'v g','ANCA':'a n c a',
 'LCS':'l c s','INRB':'i n r b','VD':'v d','HAS':'h a s','AVK':'a v k','AOD':'a o d','IGF':'i g f','CTA':'c t a',
 'ATA':'a t a','PCT':'p c t','ENL':'e n l','PR':'p r','TVP':'t v p','ABO':'a b o','IVA':'i v a','GAD':'g a d',
 'SIOP':'s i o p','BCLC':'b c l c','TNM':'t n m','WFH':'w f h','MU':'m u','DTC':'d t c','BCF':'b c f',
 'RCH':'r c h','DXA':'d x a','PIO':'p i o','TF':'t f','TRC':'t r c','G10':'g dix','SS':'s s','DTG':'d t g',
 'MAPA':'m a p a','SRAA':'s r a a','ISN':'i s n','ANA':'a n a','APOL1':'a p o l un','XDR':'x d r','BAAR':'baar',
 'PSBI':'p s b i','ST':'s t','VEMS':'vems','ACOG':'a c o g','MAM':'m a m','LAMA':'l a m a','ETA':'e t a',
 'GNAPS':'g n a p s','UV':'u v','ET':'e t','DAE':'d a e','ERC':'e r c','RCOG':'r c o g','RPR':'r p r','RPMP':'r p m p',
 'CGRP':'c g r p','ACTG':'a c t g','PSMA':'p s m a','HBP':'h b p','TI':'t i','BRAF':'b raf','NAPQI':'napqi',
 'ETT':'e t t','TS':'t s','CDC':'c d c','PEV':'p e v','PFA':'p f a','HTAP':'h t a p','EFR':'e f r','EGFR':'e g f r',
 'IRC':'i r c','OCT':'o c t','RACh':'r a c h','AAO':'a a o','CA':'c a','AES':'a e s','USA':'u s a','IA':'i a',
 'ARNI':'a r n i','HF':'h f','ARM':'a r m','MRC':'m r c','VEGF':'v e g f','VII':'sept','EMA':'e m a','TCV':'t c v',
 'AIT':'a i t','ATS':'a t s','SSC':'s s c','NSTE':'n s t e','ACS':'a c s','ACC':'a c c','RAI':'r a i','MTP':'m t p',
 'JJ':'j j','GH':'g h','CCA':'c c a','TRAb':'t r a b','WHF':'w h f','CCP':'c c p','DRB1':'d r b un','IIb':'deux b',
 'EAACI':'e a a c i','TV':'t v','RACS':'r a c s','TAK':'t a k','MMH':'m m h','HFNC':'h f n c','EDS':'e d s',
 'SOPK':'s o p k','AMIU':'a m i u','LGV':'l g v','TR':'t r','CAM':'cam','ICHD':'i c h d','SEP':'s e p',
 'LANA':'l a n a','ESPEN':'e s p e n','ICT':'i c t','FTS':'f t s','IDA':'i d a','MMDP':'m m d p','ELN':'e l n',
 'LLC':'l l c','MGUS':'m g u s','RADS':'r a d s','TP':'t p','WSES':'w s e s','EAN':'e a n','AMAN':'a m a n','MVA':'m v a',
 'BN':'b n','LC':'l c','DAI':'d a i','CMH':'c m h','ERS':'e r s','ALK':'a l k','RGO':'r g o','ISTH':'i s t h',
 'ACE':'a c e','ESMO':'e s m o','TAP':'t a p','VHL':'v h l','MIBG':'m i b g','IDH':'i d h','MSICS':'m s i c s',
 'IPSS':'i p s s','VVM':'v v m','ETO':'e t o','RH':'rhésus','PB':'p b','SA':'s a','FR':'f r','SP':'sulfadoxine-pyriméthamine','ET':'e t',
 'PA':'pression artérielle','TA':'tension artérielle','FC':'fréquence cardiaque','FE':'fraction d’éjection','FA':'fibrillation atriale',
 'IC':'insuffisance cardiaque','CO':'c o','IL':'interleukine','IPP':'inhibiteurs de la pompe à protons',
 'ADN':'a d n','ARN':'a r n','RT':'r t','HRP':'h r p','HLA':'h l a','ADA':'a d a','DIU':'d i u','VS':'vitesse de sédimentation',
 'IST':'i s t','PAS':'pression artérielle systolique','HPV':'h p v','EP':'e p','PP':'p p',
 'RCP':'r c p','DEC':'d e c','TCC':'t c c','PZQ':'praziquantel','RAA':'r a a','HTLV':'h t l v','IRIS':'iris',
 'VHD':'v h d','VHE':'v h e','MYC':'myc','PD1':'p d un','III':'trois','II':'deux','OMA':'o m a','TPIg':'t p i g',

 'LDL':'elle dé elle','HDL':'ache dé elle','AFP':'a f p','DHA':'dé ache a','SOFA':'sofa','CURB':'curbe','MoCA':'moka','CRAB':'crabe',
 'CIWA':'siwa','ABCDE':'a b c d e','ATLS':'a t l s','MELD':'meld','AKI':'a k i','CKD':'c k d','MODY':'modi','IGRA':'igra',
 'QTc':'q t c','UNICEF':'unicef','ZEBOV':'zébov','ATRA':'atra','TDAH':'t d a h','PCIME':'p c i m e','NPH':'n p h',
 'KCl':'chlorure de potassium','NEJM':'n e j m','FDG':'f d g','VATS':'vats','IDF':'i d f','AUC':'a u c','AUDIT':'odite','LH':'elle ache',
 'FSH':'effe esse ache','CRH':'c r h','EPDS':'e p d s','ECT':'e c t','EMDR':'e m d r','ADL':'a d l','IADL':'i a d l',
 'CT':'c t','DR':'d r','HBPM':'h b p m','NSTEMI':'n stémi','PCP':'p c p','LP':'p l','TG':'triglycérides','FIB':'fib',
 'HBs':'h b s','HBc':'h b c','HBeAg':'h b e a g','TPHA':'t p h a','FIV':'f i v','IT':'i t','TH1':'t h un','Th2':'t h deux',
 'PaCO2':'pression artérielle en gaz carbonique','CH50':'c h cinquante','AF':'a f','NO':'monoxyde d’azote','AS':'a s',
 'VIII':'huit','IX':'neuf','IVL':'i v l','IVB':'i v b','CIV':'c i v','CIA':'c i a','CVF':'c v f','TAS':'t a s','H5N1':'h cinq n un',
 'R0':'r zéro','O1':'o un','V2':'v deux','V3':'v trois','A2':'a deux','L3':'l trois','L5':'l cinq','P4':'p quatre','IA2':'i a deux',
 'CD10':'cé dé dix','FLT3':'f l t trois','NPM1':'n p m un','MEN1':'mène un','KRAS':'k ras','BCL2':'bé cé elle deux','PCSK9':'p c s k neuf',
 'CTNNB1':'c t n n b un','CDK4':'c d k quatre','WT1':'w t un','DAS28':'d a s vingt-huit','IB1':'i b un','IB3':'i b trois','EB3':'e b trois',
 'O139':'o cent trente-neuf','SCORE2':'score deux','VPO0':'v p o zéro','VPOn2':'v p o n deux','LAM3':'l a m trois',
 'CrCl':'clairance de la créatinine','MB':'m b','IDSA':'i d s a','SP':'s p','PTT':'p t t','HELLP':'help',
}

SYM_FIX = [
 (r'≥', ' supérieur ou égal à '), (r'≤', ' inférieur ou égal à '), (r'>', ' supérieur à '), (r'<', ' inférieur à '),
 (r'±', ' plus ou moins '), (r'≈', ' environ '), (r'→', ', puis '), (r'↑', ' augmenté '), (r'↓', ' diminué '),
 (r'×', ' fois '), (r'−', ' moins '), (r'‰', ' pour mille '), (r'«', ''), (r'»', ''), (r'…', '.'),
]

NUM = r'(\d+(?:[.,]\d+)?)'
BASE = {'mg':('milligramme','milligrammes'),'µg':('microgramme','microgrammes'),'g':('gramme','grammes'),'kg':('kilo','kilos'),
        'mL':('millilitre','millilitres'),'dL':('décilitre','décilitres'),'L':('litre','litres'),'mmol':('millimole','millimoles'),
        'mEq':('milliéquivalent','milliéquivalents'),'UI':('unité internationale','unités internationales'),
        'mmHg':('millimètre de mercure','millimètres de mercure'),'cm':('centimètre','centimètres'),'mm':('millimètre','millimètres'),
        'min':('minute','minutes'),'bpm':('battement par minute','battements par minute'),'h':('heure','heures'),'j':('jour','jours'),
        'µmol':('micromole','micromoles'),'ng':('nanogramme','nanogrammes'),'pg':('picogramme','picogrammes'),'m':('mètre','mètres'),
        'cm2':('centimètre carré','centimètres carrés'),'m2':('mètre carré','mètres carrés'),'cp':('comprimé','comprimés'),
        'mUI':('milli-unité internationale','milli-unités internationales'),'kcal':('kilocalorie','kilocalories'),
        'mOsm':('milliosmole','milliosmoles'),'s':('seconde','secondes'),'ans':('an','ans')}
PER = {'kg':'kilo','j':'jour','h':'heure','min':'minute','dose':'dose','L':'litre','dL':'décilitre','mL':'millilitre','m2':'mètre carré',
       'm':'mètre','24h':'vingt-quatre heures','semaine':'semaine','mois':'mois','cp':'comprimé','prise':'prise','g':'gramme','mg':'milligramme'}
_ub='|'.join(sorted(BASE,key=len,reverse=True))
_up='|'.join(sorted(PER,key=len,reverse=True))
UNIT_RX = re.compile(NUM+r'\s?('+_ub+r')((?:\s?/\s?(?:'+_up+r'))*)(?![A-Za-zÀ-ÿµ])')
def unit_rep(m):
    n,b,rest=m.group(1),m.group(2),m.group(3)
    sing,plur=BASE[b]
    out=n+' '+(plur if num_is_plural(n) else sing)
    pers=[p.strip() for p in rest.split('/') if p.strip()]
    for i,p in enumerate(pers):
        out+=(' par ' if i==0 else ' et par ')+PER[p]
    return out


# --- Noms se terminant par « r » : le r final doit être prononcé (artéméther -> artéméthère) ---
RFIX = {
 'artéméther':'artéméthère','scanner':'scannère','angioscanner':'angioscannère','cancer':'cancère','précancer':'précancère',
 'ringer':'ringuère','doppler':'dopplère','cathéter':'cathétère','transcathéter':'transcathétère','laser':'lazère',
 'campylobacter':'campylobactère','helicobacter':'hélicobactère','enterobacter':'entérobactère','aggregatibacter':'agrégatibactère',
 'alzheimer':'alzaïmère','holter':'holtère','osler':'oslère','herxheimer':'herxaïmère','turner':'turnère','sphincter':'sphinctère',
 'trochanter':'trochantère','peyer':'peyère','biermer':'biermère','zollinger':'zollingère','löffler':'lœfflère','patiromer':'patiromère',
 'miller':'millère','fisher':'fichère','eisenmenger':'aïzenmengère','flutter':'flutère','baker':'bakère','crigler':'criglère',
 'kramer':'kramère','silver':'silvère','tanner':'tannère','kleihauer':'klaïhaouère','dressler':'dresslère','koebner':'kœbnère',
 'wegener':'végénère','flexner':'flexnère','schober':'chobère','jacquemier':'jacquemière',
}
def rfix(t):
    def rep(m):
        w = m.group(0); r = RFIX.get(w.lower())
        if not r: return w
        return r.capitalize() if w[0].isupper() else r
    return re.sub(r"\b[A-Za-zÀ-ÿ]+er\b", rep, t)

unmapped = collections.Counter()

def spell(tok):
    out = []
    for ch in tok:
        if ch in LETTERS: out.append(LETTERS[ch])
        elif ch in DIG: out.append(DIG[ch])
        elif ch.islower(): out.append(LETTERS.get(ch.upper(), ch))
    return ' '.join(out)

def num_is_plural(n):
    try:
        return float(n.replace(',', '.')) >= 2
    except Exception:
        return True

def clean_text(t):
    t = t.replace('’', "'").replace('Kisangani','Kissangani')
    t = re.sub(r'^\s*•\s*', '', t)
    t = re.sub(r'^(\d+)\)\s*', lambda m: 'Numéro ' + DIG.get(m.group(1), m.group(1)) + ' : ', t)
    # composés et doubles sens réglés avant la lecture des sigles
    t = re.sub(r'\bNE PAS\b', 'ne pas', t)
    t = re.sub(r'\bhrp2\b', 'h r p deux', t)
    t = re.sub(r'\bCK-MB\b', 'créatine kinase m b', t)
    t = re.sub(r'\bP/T\b', 'poids pour taille', t)
    t = re.sub(r'\bRTS,S\b', 'erre té esse, esse', t)
    t = re.sub(r'\b(de la|de l’|de l\') ?LH-RH\b', 'de l’hormone de libération de l’hormone lutéinisante', t)
    t = re.sub(r'\bLH-RH\b', 'hormone de libération de l’hormone lutéinisante', t)
    t = re.sub(r'\bTB-(?:MR|MDR)/RR\b|\bTB-RR/MR\b', 'tuberculose multirésistante ou résistante à la rifampicine', t)
    t = re.sub(r'\bTB-(MR|MDR)\b', 'tuberculose multirésistante', t)
    t = re.sub(r'\bTB-RR\b', 'tuberculose résistante à la rifampicine', t)
    t = re.sub(r'\b(I{1,3}|VI{0,3}|X)(\s?(?:[-–/]|à|ou)\s?)IV\b', lambda m: m.group(1)+m.group(2)+'quatre', t)
    # H0, H12, J7, S1, M72 : repères temporels
    t = re.sub(r'\bH(\d+)\b', lambda m: 'heure ' + m.group(1), t)
    t = re.sub(r'\bJ(\d+)\b', lambda m: 'jour ' + m.group(1), t)
    t = re.sub(r'\bM(\d+)\b', lambda m: 'mois ' + m.group(1), t)
    t = re.sub(r'\bS(\d+)\b', lambda m: 'semaine ' + m.group(1), t)
    t = re.sub(r'(\d)\s?SA\b', r'\1 semaines d’aménorrhée', t)
    t = re.sub(r'\bFR(?=\s?[≥≤<>])', 'fréquence respiratoire', t)
    t = re.sub(r'\b(stades?|grades?|classes?|types?|NYHA|phase|Child-Pugh|Child|facteur|niveau|score|catégorie|degré|groupe)\s(VIII|VII|VI|IV|V|III|II|I)\b',
               lambda m: m.group(1)+' '+{'I':'un','II':'deux','III':'trois','IV':'quatre','V':'cinq','VI':'six','VII':'sept','VIII':'huit'}[m.group(2)], t)
    t = re.sub(r'\bIL-(\d+)', lambda m: 'interleukine '+m.group(1), t)
    t = t.replace('P. falciparum','Plasmodium falciparum').replace('P. vivax','Plasmodium vivax').replace('P. ovale','Plasmodium ovale').replace('P. malariae','Plasmodium malariae')
    # pourcentage
    t = re.sub(r'(\d)\s?%', r'\1 pour cent', t)
    t = t.replace('°C', ' degrés Celsius').replace('°', ' degrés')
    # tensions 140/90 -> 140 sur 90
    t = re.sub(r'(\d{2,3})/(\d{2,3})(?!\d)', r'\1 sur \2', t)
    # plages 5-14, 120-139 (chiffres) -> « à »
    t = re.sub(r'(\d)\s?[-–]\s?(\d)', r'\1 à \2', t)
    # unités après nombre
    t = UNIT_RX.sub(unit_rep, t)
    t = re.sub(r'(\d)\s?/\s?min\b', r'\1 par minute', t)
    for rx, r in SYM_FIX:
        t = re.sub(rx, r, t)
    t = t.replace('+', ' plus ').replace('=', ' égale ').replace('*', '')
    t = re.sub(r'\b(\d+)\s?(?:er|re|e|ème)\b', lambda m: m.group(1) + ' ' , t) if False else t
    t = re.sub(r'\b1er\b', 'premier', t); t = re.sub(r'\b1re\b', 'première', t)
    t = re.sub(r'\b(\d+)e\b', lambda m: LX.ORDINAL.get(int(m.group(1)), m.group(1) + ' ième'), t)
    t = t.replace(' vs ', ' versus ').replace('etc.', 'et cetera.').replace('ex.', 'par exemple')
    t = re.sub(r'\bn°\s?', 'numéro ', t)
    # slash entre mots
    t = re.sub(r'(?<=[A-Za-zÀ-ÿ])\s?/\s?(?=[A-Za-zÀ-ÿ])', ' ou ', t)
    t = re.sub(r'éther\b', 'étère', t)  # le r final doit se prononcer (artéméther -> artémétère)
    # sigles : lecture fondée sur le SENS (lexique.py), avec règles de contexte pour les doubles sens
    ctxmap = {}
    for kw, mp in LX.CTX:
        if re.search(kw, t, re.I):
            for k, v in mp.items(): ctxmap.setdefault(k, v)
    def _na(s): return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    def acr(m):
        tok = m.group(0)
        sp = ctxmap.get(tok) or LX.EXPAND.get(tok) or LX.DEFAULT.get(tok)
        if tok in LX.SGPL:
            sg, pl = LX.SGPL[tok]
            sp = sg if re.search(r"(?:\bun|\bune|\bla|\ble|\bcette|l['’])\s?$", m.string[:m.start()], re.I) else pl
        if sp and tok in ctxmap and m.string[m.end():m.end()+2] == ' (':
            return spell(tok)   # « TF (inflammation folliculaire) » : le sigle est expliqué juste après
        if sp:
            # « terme complet (SIGLE) » : le sigle entre parenthèses n'est pas répété
            pre, post = m.string[:m.start()], m.string[m.end():]
            if pre.endswith('(') and re.match(r'\s?[):;]', post):
                words = [w for w in re.findall(r"[A-Za-zÀ-ÿ]+", sp) if len(w) >= 5]
                if words and _na(words[0])[:5] in _na(pre[-90:]):
                    return ''
            return sp
        if tok in LX.WORD: return LX.WORD[tok]
        if tok in LEX: return LEX[tok]
        if tok == 'UNIQUEMENT': return 'uniquement'
        mm = re.fullmatch(r'([A-Z]{1,4})(\d+[A-Za-z]*\d*[A-Za-z]*)', tok)   # CD36, CCR5, P2Y12, H1N1 : lettres épelées + chiffres
        if mm and tok not in unmapped:
            unmapped[tok] += 1
            return ' '.join(LETTERS.get(ch, ch) for ch in mm.group(1)) + ' ' + re.sub(r'([A-Za-z])', lambda x: ' ' + LETTERS.get(x.group(1).upper(), x.group(1)) + ' ', mm.group(2)).strip()
        unmapped[tok] += 1
        if re.fullmatch(r'[A-Z]{2,5}', tok):
            return spell(tok)
        return tok
    t = re.sub(r"\b[A-Z][A-Za-z]*[A-Z0-9][A-Za-z0-9]*\b", acr, t)
    t = re.sub(r'\(\s*\)', '', t); t = re.sub(r'\(\s*[:;]\s*', '(', t); t = re.sub(r'\s+([,;.:)])', r'\1', t)
    t = rfix(t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def build():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sujets.json')
    d = json.load(open(src if os.path.exists(src) else '/tmp/vid4/sujets.json'))
    os.makedirs('out', exist_ok=True)
    manifest = []
    for i, s in enumerate(d):
        name, spec, short = s[0], s[1], s[2]
        body = s[4]
        chapters = []
        intro = f"Voici la fiche : {clean_text(name)}. Spécialiter : {SPEC[spec] if spec < len(SPEC) else ''}. {clean_text(short)} Contenu indicatif, à vérifier."
        chapters.append({'key': 'intro', 'title': 'Introduction', 'text': intro})
        for key, title in SJL:
            items = body.get(key, [])
            if not items: continue
            paras = []
            for x in items:
                if x.startswith('## '):
                    paras.append(clean_text(x[3:]) + '.')
                else:
                    c = clean_text(x)
                    if c and c[-1] not in '.!?': c += '.'
                    paras.append(c)
            chapters.append({'key': key, 'title': title, 'text': SPOKEN[key] + ' ' + ' '.join(paras)})
        h = hashlib.sha256(json.dumps(s[:5], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
        rec = {'id': i, 'name': name, 'hash': h, 'chapters': chapters}
        json.dump(rec, open(f'out/{i:03d}.json', 'w'), ensure_ascii=False)
        manifest.append({'id': i, 'name': name, 'hash': h, 'chars': sum(len(c['text']) for c in chapters), 'chapters': [c['key'] for c in chapters]})
    json.dump(manifest, open('out/manifest.json', 'w'), ensure_ascii=False)
    open('out/unmapped.txt', 'w').write('\n'.join(f'{k}\t{v}' for k, v in unmapped.most_common()))
    tot = sum(m['chars'] for m in manifest)
    print('fiches', len(manifest), 'caractères', tot, 'sigles non lexiqués', len(unmapped))

if __name__ == '__main__':
    build()
