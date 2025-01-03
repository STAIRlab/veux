#!/bin/env python
import sys
import math


def _list_equal(l1:list, l2:list, verbose=False)->bool:
    match = True
    for _i,_j in zip(l1,l2):
        if match != True:
            break
        else:
            i,j = _i,_j

        if isinstance(i,list):
            if isinstance(j,list):
                match = _list_equal(i,j)
            else:
                match = False

        elif isinstance(i,dict):
            if isinstance(j,dict):
                match = _dict_equal(i,j)
            else:
                match = False

        elif isinstance(i,float):
            match = match and math.isclose(i,j)

        else:
            match = match and (i==j)

    if verbose and match != True:
        print(f"{verbose}{i}\n\t{j}")

    return match


def _dict_equal(d1:bool, d2:bool,verbose=False)->bool:
    match = True

    for _k,_v in d1.items():
        if match != True: break
        else: k,v = _k,_v

        if k in {"name", "nodes", "instances", "crdTransformation"}:
            continue
        elif isinstance(v,dict):
            match = match and _dict_equal(v, d2[k])
        elif isinstance(v,list):
            match = match and _list_equal(v, d2[k])
        elif isinstance(v,float):
            match = match and math.isclose(v,d2[k])
        else:
            match = match and (v == d2[k])

    if verbose and not match:
        print(f"{verbose}{k}: {v}, {d2[k]}")

    return match

def sections(dat, mat_remap, sec_remap=None, sec_types = None):
    sec_types = [] if sec_types is None else sec_types
    sec_remap = {} if sec_remap is None else sec_remap
    secs = dat["StructuralAnalysisModel"]["properties"]["sections"]

    for el in secs:
        match = False
        if "section" in el and el["section"] in sec_remap:
            el["section"] = sec_remap[el["section"]]

        if "materials" in el:
            el["materials"] = [mat_remap[m] for m in el["materials"]]

        if "fibers" in el:
            for fib in el["fibers"]:
                fib["material"] = mat_remap[fib["material"]]

        # Test equality
        for typ in sec_types:
            if el["type"] == typ["type"] and _dict_equal(el,typ)==True:
                match = True
                break

        if not match:
            sec_types.append(el)
            el["instances"] = [el["name"]]
            sec_remap[el["name"]] = el["name"]

        else:
            sec_remap[el["name"]] = typ["name"]
            #if el in sec_types:
            #    sec_types.pop(sec_types.index(el))

    print(f"sections:\t{len(secs)}\t{len(sec_types)}", file=sys.stderr)
    return sec_remap, sec_types

def transfms(dat, crd_remap=None, crd_types = None):
    crd_types = [] if crd_types is None else crd_types
    crd_remap = {} if crd_remap is None else crd_remap
    secs = dat["StructuralAnalysisModel"]["properties"]["crdTransformations"]
    for el in secs:
        match = False
        # Test equality
        for typ in crd_types:
            if el["type"] == typ["type"] and _dict_equal(el,typ)==True:
                match = True
                break

        if not match:
            crd_types.append(el)
            el["instances"] = [el["name"]]
            crd_remap[el["name"]] = el["name"]

        else:
            crd_remap[el["name"]] = typ["name"]
            #if el in crd_types:
            #    crd_types.pop(crd_types.index(el))

    print(f"transforms:\t{len(secs)}\t{len(crd_types)}", file=sys.stderr)
    return crd_remap, crd_types

def materials(dat):
    mat_types = []
    mat_remap = {}
    mats = dat["StructuralAnalysisModel"]["properties"]["uniaxialMaterials"]
    for el in mats:
        match = False
        for typ in mat_types:
            if el["type"] == typ["type"] and _dict_equal(el,typ)==True:
                match = True
                break
        if not match:
            mat_types.append(el)
            el["instances"] = [el["name"]]
            mat_remap[el["name"]] = el["name"]
        else:
            mat_remap[el["name"]] = typ["name"]

    print(f"materials:\t{len(mats)}\t{len(mat_types)}", file=sys.stderr)
    return mat_remap, mat_types

def consolidate(model, modify = False):
    mat_remap, mat_types = materials(model)
    sec_remap, sec_types = sections(model, mat_remap)
    sec_remap, sec_types = sections(model, mat_remap, sec_remap, sec_types)
    crd_remap, crd_types = transfms(model)

    elem_types = []
    elems = model["StructuralAnalysisModel"]["geometry"]["elements"]
    for el in elems:
        match = False
        verbose  = False
        #print(f"{el['name']}")

        # change references
        if "materials" in el:
            el["materials"] = [mat_remap[m] for m in el["materials"]]

        if "sections" in el:
            el["sections"]  = [sec_remap[m] for m in el["sections"]]

        if "crdTransformation" in el:
            el["crdTransformation"] = crd_remap[el["crdTransformation"]]

        for typ in elem_types:
            if el["type"] == typ["type"] and _dict_equal(el,typ,verbose)==True:
                match = True
                break

        if not match:
            elem_types.append(el)
            el["instances"] = [el["name"]]
        else:
            typ["instances"].append(el["name"])

    model["StructuralAnalysisModel"]["properties"]["element_types"] = elem_types

    print(f"elements:\t{len(elems)}\t{len(elem_types)}",file=sys.stderr)

    return model


if __name__=="__main__":
    import json,sys
    with open(sys.argv[-1],"r") as f:
        model = json.load(f)

    clean = consolidate(model)

    print(json.dumps(clean,indent=2))

