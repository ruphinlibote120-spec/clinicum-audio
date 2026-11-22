# -*- coding: utf-8 -*-
"""Lexique de prononciation fondé sur le SENS des abréviations (voix Ariane).
Trois façons de dire un sigle :
  EXPAND : on dit le terme complet (le sigle n'est pas lu)
  WORD   : on le dit comme un mot (écriture phonétique pour la voix)
  sinon  : épelé lettre par lettre (comme on le dit à l'oral : « vé i ache »)
Les sigles à double sens sont réglés par CONTEXTE (voir ctx_rules dans prep.py)."""

# --- Termes complets (invariables en nombre autant que possible) ---
EXPAND = {
 # voies d'administration
 'IV':'intraveineuse','IM':'intramusculaire','SC':'sous-cutanée','PO':'par voie orale','SL':'sublinguale','ID':'intradermique',
 'IO':'intra-osseuse','SubQ':'sous-cutanée',
 # constantes
 'PA':'pression artérielle','PAS':'pression artérielle systolique','PAD':'pression artérielle diastolique','PAM':'pression artérielle moyenne',
 'TA':'tension artérielle','TAS':'tension artérielle systolique','FC':'fréquence cardiaque','FR':'fréquence respiratoire',
 'PIC':'pression intracrânienne','PIO':'pression intraoculaire','DEP':'débit expiratoire de pointe',
 'FE':'fraction d’éjection','FEVG':'fraction d’éjection du ventricule gauche','VEMS':'volume expiratoire maximal en une seconde','CVF':'capacité vitale forcée',
 'SA':'semaines d’aménorrhée','UI':'unités internationales','MUI':'millions d’unités internationales',
 'MU':'millions d’unités','TRC':'temps de recoloration cutanée','SCB':'surface corporelle brûlée','EVA':'échelle visuelle analogique',
 'PB':'périmètre brachial','MUAC':'périmètre brachial',
 'ECBC':'examen cytobactériologique des crachats',
 'TP':'taux de prothrombine','TCA':'temps de céphaline activée','VS':'vitesse de sédimentation','VSG':'vitesse de sédimentation',
 
 
 
 
 
 
 
 'TPIg':'traitement préventif intermittent pendant la grossesse','TPIn':'traitement préventif intermittent du nourrisson','CPS':'chimioprévention du paludisme saisonnier',
 'PMC':'chimioprévention périodique du paludisme','SP':'sulfadoxine-pyriméthamine','ROR':'rougeole, oreillons et rubéole','ARNI':'inhibiteurs de la néprilysine et du récepteur de l’angiotensine','DEC':'diéthylcarbamazine','PZQ':'praziquantel',
 'IPP':'inhibiteurs de la pompe à protons',
 
 
 'SHA':'solution hydro-alcoolique','RUSF':'aliment supplémentaire prêt à l’emploi',
 'MAS':'malnutrition aiguë sévère','MAM':'malnutrition aiguë modérée',
 
 
 
 
 
 
 
 
 'EFR ':'explorations fonctionnelles respiratoires',
 
 
 
 
 
 
 'HbA1c':'hémoglobine glyquée','COHb':'carboxyhémoglobine','ASLO':'antistreptolysines o','HGPRT':'hypoxanthine-guanine phosphoribosyltransférase',
 'RIF':'rifampicine','INH':'isoniazide','EMB':'éthambutol','PZA':'pyrazinamide',
 
 'ADN':'a d n','ARN':'a r n','ARNm':'a r n messager','HIV':'vé i ache','WHO':'Organisation mondiale de la Santé',
 
 'NaCl':'chlorure de sodium','KCl':'chlorure de potassium',
 'SpO2':'saturation en oxygène','PaO2':'pression artérielle en oxygène','PaCO2':'pression artérielle en gaz carbonique','FiO2':'fraction inspirée en oxygène','O2':'oxygène','CO2':'gaz carbonique',
 'IL':'interleukine','HBsAg':'antigène ache bé esse','HBs':'ache bé esse','HBeAg':'antigène ache bé e','HBc':'ache bé cé',
 'HLA':'h l a','BCG':'bé cé gé','HRP2':'h r p deux',
}

# --- Sigles dits comme des mots (écriture phonétique : le français uniquement) ---
WORD = {
 'SIDA':'sida','COVID':'covid','ELISA':'élisa','HELLP':'elpe','STEMI':'stémi','NSTEMI':'enne stémi','KDIGO':'kédigo','GOLD':'golde','FAST':'faste',
 'GABA':'gaba','NASH':'nache','TIPS':'tipse','FIGO':'figo','NICE':'naïce','HACEK':'assek','SOFA':'sofa','IRIS':'iris','CATT':'catte','MUAC':'muak',
 'CAR':'cé a erre','SARS':'sarce','WASH':'ouache','GLOBOCAN':'globocane','EULAR':'eu lar','CURB':'curbe','MoCA':'moka','CIWA':'siwa','MELD':'meld',
 'MODY':'modi','IGRA':'igra','AUDIT':'odite','CHOP':'tchop','FOLFOX':'folfox','ABVD':'a b v d','LEEP':'liip','BPaLM':'bé pé a elle emme',
 'McRoberts':'mac robertse','McDonald':'mac donald','McIsaac':'mac aïzak','ReSoMal':'ré so mal','JAK':'jak','MYC':'myc','KRAS':'k ras','BRAF':'b raf',
 'ZEBOV':'zébov','ATRA':'atra','NAPQI':'napqi','VATS':'vats','TRAb':'t r a b','MenAfriVac':'mène africa vac','ZMapp':'zi map',
 'GeneXpert':'gène expert','FibroScan':'fibro scane','LoaScope':'loa scope','CheckMate':'tchèque mate','PrEP':'prépe',
}

# --- Mots courants écrits en capitales ---
CAPS_WORDS = {'ET':'et','OU':'ou','NE':'ne','PAS':None,'EST':'est','DE':'de','LA':'la','LE':'le','EN':'en','UN':'un','OK':'o k'}

ORDINAL = {2:'deuxième',3:'troisième',4:'quatrième',5:'cinquième',6:'sixième',7:'septième',8:'huitième',9:'neuvième',10:'dixième',
 11:'onzième',12:'douzième',13:'treizième',14:'quatorzième',15:'quinzième',16:'seizième',17:'dix-septième',18:'dix-huitième',
 19:'dix-neuvième',20:'vingtième',21:'vingt et unième',24:'vingt-quatrième',28:'vingt-huitième',30:'trentième',36:'trente-sixième',72:'soixante-douzième'}

# --- Règles de contexte (sigles à double sens) : (mots-clés dans le paragraphe, {sigle: lecture}) ---
CTX = [
 (r'trachom|trichiasis|CHANCE|\bSAFE\b', {'TF':'inflammation trachomateuse folliculaire','TI':'inflammation trachomateuse intense',
                                          'TS':'cicatrisation conjonctivale','TT':'trichiasis trachomateux','CO':'opacité cornéenne'}),
 (r'lèpre|lépr|paucibacill|multibacill|borderline|tuberculoïde|clofazimine|dapsone|polychimiothérapie|PB/MB|PB et MB', {'PB':'paucibacillaire','MB':'multibacillaire','TT':'tuberculoïde','LL':'lépromateuse',
                                          'BT':'borderline tuberculoïde','BB':'borderline borderline','BL':'borderline lépromateuse','ENL':'érythème noueux lépreux'}),
 (r'tubercul|rifampicine|isoniazide|BPaLM|TB-', {'RR':'résistance à la rifampicine','MR':'multirésistante'}),
 (r'monoxyde|intoxication|carboxy|manganèse|MPTP', {'CO':'monoxyde de carbone'}),
 (r'hémostase|coagulation|prothrombine|fibrinogène|plaquettes|héparine|TCA|hémophilie|saignement', {'TT':'temps de thrombine','TS':'temps de saignement'}),
 (r'anorexie|boulimie|hyperphagie|alimentaire|psychiatr|DSM', {'TCA':'troubles du comportement alimentaire'}),
 (r'risque relatif|odds|intervalle de confiance|IC à 95|étude|méta-analyse|exposés', {'RR':'risque relatif','IC':'intervalle de confiance'}),
 (r'récepteur', {'EP':'e p'}),
 (r'vaccin|rougeole|rubéole', {'RR':'rougeole-rubéole'}),
 (r'anti-CCP|ACPA|polyarthrite|rhumato', {'FR':'facteur rhumatoïde'}),
 (r'drépano|HbS|HbAS|HbSC|trait ', {'SS':'s s','AS':'a s'}),
 (r'écart|-3|-2|poids/taille|P/T', {'ET':'écarts-types'}),
]
# Lectures par défaut quand aucun contexte ne s'applique (sens le plus fréquent dans l'app)
DEFAULT = {'CO':'monoxyde de carbone','PB':'périmètre brachial',
           'IC':'insuffisance cardiaque','EP':'embolie pulmonaire','TCA':'temps de céphaline activée','MB':'m b','ET':'et',
           'MR':'libération modifiée','VI':'six','VII':'sept','VIII':'huit','IX':'neuf','II':'deux','III':'trois'}

# Noms qui changent selon le nombre : (singulier, pluriel) ; singulier si précédé de un/une/la/le/l'/cette
SGPL = {'ACT':('combinaison thérapeutique à base d’artémisinine','combinaisons thérapeutiques à base d’artémisinine')}
