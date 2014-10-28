
def load_groups(request, groups, user):
        
    active_group = request.GET.get('group_name')
    if active_group:
        request.session['active_group'] = active_group
        active_group = {'name': active_group}
    elif request.session.get('active_group'):
        active_group = request.session.get('active_group')
        active_group = {'name': active_group}
    elif len(groups) > 0:
        active_group = groups[0]
    else:
        active_group = {'name': 'No Groups Yet'}
    
    return active_group