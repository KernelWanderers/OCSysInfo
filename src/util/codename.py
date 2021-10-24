def codename(data, extf, family, extm, model):
    vals = []
    for arch in data:

        if extf.lower() == arch.get('ExtFamily', '').lower() and \
           family.lower() == arch.get('BaseFamily', '').lower() and \
           extm.lower() == arch.get('ExtModel', '').lower() and \
           model.lower() == arch.get('BaseModel', '').lower():

            vals.append(arch.get('Codename'))

    return vals
