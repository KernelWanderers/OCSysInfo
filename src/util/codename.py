def codename(data, extf, family, extm, model, stepping=None):
    vals = []
    for arch in data:

        if extf.lower() == arch.get('ExtFamily', '').lower() and \
                family.lower() == arch.get('BaseFamily', '').lower() and \
                extm.lower() == arch.get('ExtModel', '').lower() and \
                model.lower() == arch.get('BaseModel', '').lower():

            if stepping and arch.get('Stepping', None):
                if stepping.lower() in arch.get('Stepping').lower():
                    vals.append(arch.get('Codename'))
            else:
                vals.append(arch.get('Codename'))

    return vals
