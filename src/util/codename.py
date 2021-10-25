def codename(data, extf, family, extm, model, stepping=None, laptop=False):
    """
    Extracts µarches matching the provided data,
    and takes care of validating which codename is
    the most accurate guess.
    """

    vals = []
    for arch in data:

        if extf.lower() == arch.get('ExtFamily', '').lower() and \
                family.lower() == arch.get('BaseFamily', '').lower() and \
                extm.lower() == arch.get('ExtModel', '').lower() and \
                model.lower() == arch.get('BaseModel', '').lower():

            valid_stepping = stepping and stepping.lower() in arch.get('Stepping', '').lower()

            if laptop and arch.get('Laptop', None) or \
                    stepping and arch.get('Stepping', None) and valid_stepping:
                vals = [arch.get('Codename')]
                break

            vals.append(arch.get('Codename'))

    return vals if vals else ["Unknown"]
