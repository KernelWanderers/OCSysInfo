def codename(data, extf, family, extm, model):
    val = None
    for arch in data:

        if arch.get('ExtFamily') == extf and \
           arch.get('BaseFamily') == family and \
           extm in arch.get('ExtModels', []) and \
           model in arch.get('BaseModels', []):

            val = arch.get('Codename')
            break

    return val
