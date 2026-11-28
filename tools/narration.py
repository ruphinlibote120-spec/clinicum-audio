#!/usr/bin/env python3
"""Style « conté » des audios Clinicum : ouverture, transitions, questions, listes racontées, mises en garde annoncées, récapitulatif final.
On n'ajoute QUE des phrases de liaison : les doses, chiffres et noms de médicaments viennent de la fiche, sans changement.
Utilise prep.clean_text (sigles, unités, prononciation) sur chaque élément de la fiche."""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep

SJL = prep.SJL
# « de la cardiologie » -> « sujet de cardiologie »
SPEC2 = ["de cardiologie","de pneumologie","de gastro-entérologie et d'hépatologie","de néphrologie","d'endocrinologie et de métabolisme",
 "d'hématologie","d'infectiologie et de maladies tropicales","de neurologie","d'urgences et de réanimation","de rhumatologie",
 "de dermatologie","de psychiatrie","de gynécologie et d'obstétrique","de pédiatrie","de toxicologie","de nutrition","d'oncologie",
 "d'oto-rhino-laryngologie","d'ophtalmologie","d'urologie et de chirurgie","de santé publique et de médecine légale",
 "de douleur, de soins palliatifs et de gériatrie"]
# (avec article, avec « de »), question posée avant le chapitre
TOP = {
 'pts':("les points clés","des points clés","Qu'est-ce qu'il faut absolument retenir ?"),
 'def':("la définition","de la définition","De quoi parle-t-on exactement ?"),
 'epi':("l'épidémiologie","de l'épidémiologie","Est-ce une maladie fréquente, et chez qui ?"),
 'cau':("les causes et les facteurs de risque","des causes et des facteurs de risque","Quelles en sont les causes ?"),
 'phy':("la physiopathologie","de la physiopathologie","Que se passe-t-il dans l'organisme ?"),
 'ana':("l'anatomopathologie","de l'anatomopathologie","Et du côté des lésions, que trouve-t-on ?"),
 'cli':("la symptomatologie","de la symptomatologie","Alors, quels sont les signes ?"),
 'dia':("le diagnostic","du diagnostic","Comment confirmer le diagnostic ?"),
 'exp':("les explorations","des explorations","Quels examens faut-il demander ?"),
 'tt':("le traitement","du traitement","Et comment traite-t-on ?"),
 'sui':("le suivi et le pronostic","du suivi et du pronostic","Et ensuite, comment suivre le patient ?"),
 'pre':("la prévention","de la prévention","Peut-on prévenir cette maladie ?"),
 'ref':("le moment de référer ou d'hospitaliser","du moment de référer ou d'hospitaliser","Quand faut-il référer ou hospitaliser ?"),
}
LEAD = ["Bien, maintenant parlons {de}.","Voilà. Passons à {def}.","Alors, voyons {def}.","Continuons avec {def}.","Abordons maintenant {def}."]
LEAD_FIRST = ["Commençons par {def}.","Pour commencer, voyons {def}."]
HEAD = ["Passons maintenant à ce point : {x}.","Voyons maintenant : {x}.","Autre point important : {x}.","Et maintenant : {x}."]
INTER = ["Voilà.","Bien.","Continuons.","Poursuivons."]
ORD = {1:"Premièrement,",2:"Deuxièmement,",3:"Troisièmement,",4:"Quatrièmement,",5:"Cinquièmement,"}
WARN_RX = re.compile(r"^\W*(danger|attention|ne pas|ne jamais|contre-indiqu|interdit)", re.I)
SRC_RX = re.compile(r"\s*\([^()]*(?:ePILLY|tableau|\b(?:19|20)\d\d\b)[^()]*\)")   # références bibliographiques entre parenthèses : inutiles à l'oral

def _pick(lst, k): return lst[k % len(lst)]

def _cleanitem(x):
    x = re.sub(r"^\s*•\s*", "", x)
    x = SRC_RX.sub("", x)
    return x.strip()

def _end(c):
    c = c.strip()
    if c and c[-1] not in ".!?": c += "."
    return c

def _comma_parens(c):
    """Les parenthèses sont conservées (elles portent des précisions cliniques) ; on nettoie seulement les espaces."""
    c = re.sub(r"\(\s+", "(", c); c = re.sub(r"\s+\)", ")", c)
    return re.sub(r"\s+", " ", c).strip()

def chapter_text(fid, ci, key, items, first):
    de, defn = TOP[key][1], TOP[key][0]
    tmpl = _pick(LEAD_FIRST if first else LEAD, fid + ci)
    out = [tmpl.format(de=de, **{"def": defn}), TOP[key][2]]
    nitem = nwarn = nh = 0
    pend_inter = 0
    for idx, raw in enumerate(items):
        if raw.startswith("## "):
            x = prep.clean_text(_cleanitem(raw[3:]))
            x = _comma_parens(x).rstrip(".")
            if nh == 0 and idx == 0:
                out.append(x + ".")
            else:
                out.append(_pick(HEAD, fid + ci + nh).format(x=x))
            nh += 1; pend_inter = 0
            continue
        t = _cleanitem(raw)
        m = re.match(r"^(\d+)\)\s*", t)
        pre = ""
        if m:
            n = int(m.group(1)); t = t[m.end():]
            pre = ORD.get(n, "Ensuite,") + " "
        c = prep.clean_text(t)
        c = _comma_parens(c)
        if not c: continue
        # mise en garde annoncée juste avant la proposition concernée (ne pas ..., contre-indiqué ...)
        cl = c.split("; ")
        if key != "pts" and nwarn < 2 and len(cl) > 0:
            for q, x in enumerate(cl):
                if WARN_RX.match(x) and (q > 0 or True):
                    if q == 0:
                        out.append("Attention, point important.")
                    else:
                        cl[q - 1] = cl[q - 1] + ".|Attention, point important."
                    nwarn += 1; break
            c = "; ".join(cl).replace(".|Attention, point important.; ", ". Attention, point important. ")
        out.append(pre + _end(c))
        nitem += 1; pend_inter += 1
        nxt = items[idx + 1] if idx + 1 < len(items) else None
        if pend_inter >= 3 and nxt and not nxt.startswith("## ") and idx + 2 < len(items):
            out.append(_pick(INTER, fid + ci + idx)); pend_inter = 0
    return " ".join(out)

def recap(items):
    firsts = []
    for raw in items:
        if raw.startswith("## "): continue
        c = _comma_parens(prep.clean_text(_cleanitem(raw)))
        m = re.search(r"[.!?](?= [A-ZÀ-Ý])", c)
        s = c[:m.end()] if m else c
        if 25 <= len(s) <= 230: firsts.append(_end(s))
        if len(firsts) == 3: break
    return firsts

def narrate(fid, s):
    name, spec, short, body = s[0], s[1], s[2], s[4]
    sp = SPEC2[spec] if spec < len(SPEC2) else ""
    intro = (f"Bonjour. Aujourd'hui, au programme : {prep.clean_text(name)}. " + (f"C'est un sujet {sp}. " if sp else "") +
             f"Alors, de quoi s'agit-il ? {_end(_comma_parens(prep.clean_text(short)))} Bien, voyons tout cela dans l'ordre.")
    chapters = [{"key": "intro", "title": "Introduction", "text": intro}]
    keys = [(k, t) for k, t in SJL if body.get(k)]
    for ci, (k, t) in enumerate(keys):
        chapters.append({"key": k, "title": t, "text": chapter_text(fid, ci, k, body[k], ci == 0)})
    r = recap(body.get("pts", []))
    fin = "Voilà, nous avons fait le tour du sujet."
    if r:
        fin += " Pour résumer, retenez ceci. " + " ".join(f"{ORD[i+1]} {x}" for i, x in enumerate(r))
    fin += " Ce contenu est indicatif : à vérifier avant tout usage clinique. Merci de votre écoute, et à bientôt."
    chapters[-1]["text"] += " " + fin
    return {"id": fid, "name": name, "chapters": chapters}

if __name__ == "__main__":
    import json
    d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sujets.json")))
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    rec = narrate(fid, d[fid])
    for c in rec["chapters"]:
        print("\n=== %s (%d car.)\n%s" % (c["key"], len(c["text"]), c["text"]))
